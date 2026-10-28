from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterable

TEXT_EXTS = {
    '.py', '.pyi', '.js', '.jsx', '.ts', '.tsx', '.java', '.kt', '.kts', '.cs', '.cpp', '.cc',
    '.c', '.h', '.hpp', '.rs', '.go', '.rb', '.php', '.lua', '.luau', '.swift', '.sql', '.sh',
    '.ps1', '.bat', '.cmd', '.json', '.toml', '.yaml', '.yml', '.xml', '.gradle', '.properties',
    '.md', '.txt', '.ini', '.cfg', '.conf', '.html', '.css', '.scss', '.vue', '.svelte', '.csv',
}

KEY_FILES = {
    'readme', 'readme.md', 'readme.txt', 'pyproject.toml', 'requirements.txt', 'package.json',
    'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 'cargo.toml', 'go.mod', 'pom.xml',
    'build.gradle', 'build.gradle.kts', 'settings.gradle', 'settings.gradle.kts', 'gradle.properties',
    'dockerfile', 'docker-compose.yml', 'docker-compose.yaml', 'agents.md', 'claude.md', '.gitignore',
}

IGNORE_DIRS = {
    '.git', '.hg', '.svn', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.tox',
    '.venv', 'venv', 'env', 'node_modules', 'dist', 'build', 'target', '.gradle', '.idea',
    '.vs', '.next', '.nuxt', 'coverage', '.coverage', 'tmp', 'temp',
}

SENSITIVE_NAMES = {
    '.env', '.env.local', '.env.production', '.env.development', 'id_rsa', 'id_ed25519',
    'credentials.json', 'service-account.json', 'secrets.json', 'secret.json',
}
SENSITIVE_SUFFIXES = {'.pem', '.key', '.pfx', '.p12', '.jks', '.keystore'}


def _run_git(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ['git', *args], cwd=project, capture_output=True, text=True,
        encoding='utf-8', errors='replace', timeout=120,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    )


def is_git_repo(project: Path) -> bool:
    try:
        cp = _run_git(project, 'rev-parse', '--is-inside-work-tree')
        return cp.returncode == 0 and cp.stdout.strip() == 'true'
    except Exception:
        return False


def git_tracked_files(project: Path) -> list[str]:
    try:
        cp = _run_git(project, 'ls-files')
        if cp.returncode != 0:
            return []
        return [x.strip() for x in cp.stdout.splitlines() if x.strip()]
    except Exception:
        return []


def _is_sensitive(path: Path) -> bool:
    low = path.name.lower()
    if low in SENSITIVE_NAMES:
        return True
    if path.suffix.lower() in SENSITIVE_SUFFIXES:
        return True
    if low.startswith('.env.'):
        return True
    if 'credential' in low or 'secret' in low:
        return True
    return False


def filesystem_files(project: Path, *, max_files: int = 5000, max_depth: int = 12) -> list[str]:
    """Safe bounded file listing for READ-ONLY analysis when no Git index exists.

    Never follows symlink directories, ignores build/cache/dependency trees, and omits
    common credential/secret files. Returned paths are project-relative POSIX strings.
    """
    root = project.resolve()
    out: list[str] = []
    for current, dirs, files in os.walk(root, followlinks=False):
        cur = Path(current)
        try:
            rel_dir = cur.relative_to(root)
        except Exception:
            continue
        depth = len(rel_dir.parts)
        dirs[:] = [
            d for d in dirs
            if d.lower() not in IGNORE_DIRS
            and not (cur / d).is_symlink()
            and depth < max_depth
        ]
        for name in files:
            p = cur / name
            if p.is_symlink() or _is_sensitive(p):
                continue
            try:
                rel = p.relative_to(root)
            except Exception:
                continue
            out.append(rel.as_posix())
            if len(out) >= max_files:
                return sorted(out)
    return sorted(out)


def project_files(project: Path, *, max_files: int = 5000) -> tuple[str, list[str]]:
    project = project.resolve()
    if is_git_repo(project):
        tracked = git_tracked_files(project)
        if tracked:
            return 'GIT_TRACKED', tracked[:max_files]
    return 'FILESYSTEM_READ_ONLY', filesystem_files(project, max_files=max_files)


def is_text_candidate(rel: str) -> bool:
    p = Path(rel)
    return p.suffix.lower() in TEXT_EXTS or p.name.lower() in KEY_FILES


def safe_project_path(project: Path, rel: str) -> Path | None:
    try:
        root = project.resolve()
        candidate = (root / rel).resolve()
        candidate.relative_to(root)
        if candidate.is_symlink() or _is_sensitive(candidate):
            return None
        return candidate
    except Exception:
        return None


def iter_text_files(project: Path, rels: Iterable[str], *, max_size: int = 500_000):
    for rel in rels:
        if not is_text_candidate(rel):
            continue
        path = safe_project_path(project, rel)
        if path is None or not path.is_file():
            continue
        try:
            if path.stat().st_size > max_size:
                continue
        except Exception:
            continue
        yield rel, path
