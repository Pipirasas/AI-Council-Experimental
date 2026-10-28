from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any, Iterable

from .project_files import is_text_candidate, project_files, safe_project_path


class EvidenceBroker:
    """Read-only evidence broker for local specialist agents.

    Agents never receive shell access. They may ask for a path, symbol or literal text;
    the broker resolves those requests using Git-tracked files when available or a safe bounded read-only filesystem scan otherwise.
    """

    def __init__(self, git_executable: str = "git"):
        self.git_executable = git_executable

    def _git(self, project: Path, *args: str) -> str:
        cp = subprocess.run(
            [self.git_executable, *args],
            cwd=project,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return cp.stdout if cp.returncode == 0 else ""

    def tracked_files(self, project: Path) -> list[str]:
        # Historical method name kept for compatibility. In READ-ONLY audit mode,
        # non-Git folders fall back to a safe bounded filesystem scan.
        _mode, files = project_files(project, max_files=5000)
        return files

    def source_mode(self, project: Path) -> str:
        mode, _files = project_files(project, max_files=5000)
        return mode

    @staticmethod
    def _safe_rel(project: Path, rel: str) -> Path | None:
        try:
            candidate = (project / rel).resolve()
            candidate.relative_to(project.resolve())
            return candidate
        except Exception:
            return None

    @staticmethod
    def _read_lines_status(
        path: Path, center: int | None = None, radius: int = 8, cap: int = 2500,
    ) -> tuple[str, bool]:
        """Only an actual successful strict UTF-8 read grants broker read_ok.

        Error/omission strings are diagnostic observations, never proof that a
        requested file was inspected. An empty file is a *successful* read.
        """
        try:
            raw = path.read_bytes()
            if b"\x00" in raw[:4096]:
                return "[binary/non-text file omitted]", False
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return "[non-UTF-8 file omitted]", False
        except OSError as exc:
            return f"[read failed: {exc}]", False
        lines = text.splitlines()
        if center is None:
            selected = list(enumerate(lines[:120], 1))
        else:
            start = max(0, center - 1 - radius)
            stop = min(len(lines), center - 1 + radius + 1)
            selected = [(i + 1, lines[i]) for i in range(start, stop)]
        out = "\n".join(f"{number}: {line}" for number, line in selected)
        excerpt = out[:max(0, cap)]
        if not raw:
            return excerpt, True
        # Do not count broker-generated numeric prefixes or partial indentation
        # as inspected source. Check the actual source characters emitted, even
        # when a centered excerpt begins with blank lines.
        pos = 0
        for number, line in selected:
            prefix_size = len(f"{number}: ")
            visible = max(0, min(len(line), len(excerpt) - pos - prefix_size))
            if visible and line[:visible].strip():
                return excerpt, True
            pos += prefix_size + len(line) + 1  # newline separator
        # A wholly blank source is valid evidence only if the entire bounded
        # selected excerpt is visible (never a clipped numeric prefix).
        return excerpt, bool(selected) and len(excerpt) == len(out) and all(
            not line.strip() for line in lines
        )

    @staticmethod
    def _read_lines(path: Path, center: int | None = None, radius: int = 8, cap: int = 2500) -> str:
        # Preserve the existing human-readable broker interface for callers
        # which do not need the audit-specific successful-read certificate.
        return EvidenceBroker._read_lines_status(path, center, radius, cap)[0]

    @staticmethod
    def _normalize_request(req: dict[str, Any]) -> dict[str, str] | None:
        kind = str(req.get("kind", "")).strip().lower()
        raw_query = req.get("query")
        if not isinstance(raw_query, str):
            return None
        query = raw_query.strip()
        reason = str(req.get("reason", "")).strip()[:240]
        # Broker must reject invalid identities rather than execute a search
        # for a silently truncated query. Model and curated requests share it.
        if (kind not in {"path", "symbol", "text"} or not query
                or len(query) > 160 or any(c in query for c in "\x00\r\n")):
            return None
        return {"kind": kind, "query": query, "reason": reason}

    def _path_evidence(self, project: Path, query: str, tracked: list[str], cap: int) -> list[dict[str, Any]]:
        q = query.replace("\\", "/").strip("/").lower()
        matches = [r for r in tracked if r.replace("\\", "/").lower() == q]
        if not matches:
            matches = [r for r in tracked if Path(r).name.lower() == Path(q).name.lower()]
        if not matches:
            matches = [r for r in tracked if q in r.replace("\\", "/").lower()]
        out: list[dict[str, Any]] = []
        for rel in matches[:3]:
            path = safe_project_path(project, rel)
            if path and path.is_file():
                snippet, read_ok = self._read_lines_status(path, cap=cap)
                out.append({"file": rel, "snippet": snippet, "read_ok": read_ok})
        return out

    def _grep_evidence(self, project: Path, query: str, tracked: list[str], cap: int) -> list[dict[str, Any]]:
        if len(query) > 160 or "\n" in query or "\r" in query:
            return []
        needle = query.lower()
        out: list[dict[str, Any]] = []
        # Python search works for both Git tracked files and safe non-Git filesystem scans.
        for rel in tracked[:5000]:
            if not is_text_candidate(rel):
                continue
            path = safe_project_path(project, rel)
            if path is None or not path.is_file():
                continue
            try:
                if path.stat().st_size > 500_000:
                    continue
                raw = path.read_bytes()
                if b"\x00" in raw[:4096]:
                    continue
                lines = raw.decode("utf-8").splitlines()
            except Exception:
                continue
            for idx, line in enumerate(lines, start=1):
                if needle in line.lower():
                    snippet, read_ok = self._read_lines_status(path, idx, cap=cap)
                    out.append({"file": rel, "line": idx, "snippet": snippet, "read_ok": read_ok})
                    if len(out) >= 8:
                        return out
        return out

    def fulfill_many(
        self,
        project: Path,
        requests: Iterable[dict[str, Any]],
        *,
        max_requests: int = 6,
        per_result_chars: int = 2500,
    ) -> list[dict[str, Any]]:
        project = project.resolve()
        tracked = self.tracked_files(project)
        seen: set[str] = set()
        results: list[dict[str, Any]] = []
        for raw in requests:
            req = self._normalize_request(raw)
            if req is None:
                continue
            key = hashlib.sha1(f"{req['kind']}\0{req['query'].lower()}".encode("utf-8")).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            if len(results) >= max_requests:
                break
            if req["kind"] == "path":
                hits = self._path_evidence(project, req["query"], tracked, per_result_chars)
            else:
                hits = self._grep_evidence(project, req["query"], tracked, per_result_chars)
            evidence_id = "E" + hashlib.sha256(
                f"{req['kind']}\0{req['query'].lower()}".encode("utf-8")
            ).hexdigest()[:10].upper()
            results.append({"evidence_id": evidence_id, **req, "found": bool(hits), "results": hits})
        return results
