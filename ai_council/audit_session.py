"""Audit-only retention and evidence reconciliation; no model or target execution.

The planning/sign-off evidence merger is intentionally unchanged.  A conflicting
observation in a read-only audit is preserved for diagnosis, then stops the audit
rather than allowing a final finding to cite an unrelated archived version.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from .audit_provenance import _verified_source_module, evidence_index


class AuditIntegrityError(ValueError):
    """The current audit can no longer support a consistent final report."""


def begin_audit_session(workflow_dir: Path) -> None:
    """Claim a workflow once, before any evidence or model output is written.

    No automatic resume is supported. An exclusive-create marker remains after
    success, interruption, cancellation or integrity failure. It is never removed
    or rewritten here. A new attempt must use a separate workflow directory.
    The marker is deliberately not parsed on re-entry: a torn/empty marker also
    fails closed. Legacy pre-marker artifacts block execution as well.
    """
    workflow_dir.mkdir(parents=True, exist_ok=True)
    marker = workflow_dir / "AUDIT_SESSION_STARTED.json"
    try:
        with marker.open("x", encoding="utf-8", newline="\n") as out:
            json.dump({"version": 1, "automatic_resume": False,
                       "policy": "ONE_ANALYSIS_INVOCATION_PER_WORKFLOW"}, out)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
    except FileExistsError as exc:
        raise AuditIntegrityError("AUDIT_SESSION_REENTRY_BLOCKED") from exc
    # Preparation writes base context; only audit-owned outputs are guarded.
    known = (
        "evidence/audit_evidence.json", "audit_project_facts.json",
        "audit_report.json", "audit_synthesis_input.json",
        "audit_synthesis_selection_raw.json", "audit_synthesis_selection.json",
        "analysis/audit_analyses.json", "analysis/audit_validated_findings.json",
        "analysis/audit_rejected_claims.json",
    )
    legacy = any((workflow_dir / relative).exists() for relative in known)
    analysis_dir = workflow_dir / "analysis"
    if analysis_dir.is_dir():
        legacy = legacy or any(analysis_dir.glob("*_audit_*.json"))
        legacy = legacy or any(analysis_dir.glob("*_validated_initial.json"))
    if legacy:
        raise AuditIntegrityError("AUDIT_EXISTING_ARTIFACTS_BLOCKED")


def _observation(row: dict[str, Any]) -> str:
    # A lookup's rationale is not evidence. Different requests for the identical
    # observation do not conflict just because their explanations differ.
    body = {k: v for k, v in row.items() if k != "reason"}
    return json.dumps(body, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def merge_audit_evidence(
    existing: list[dict[str, Any]], incoming: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Retain every distinct observation; collapse only identical observations.

    Do not collapse rows merely by kind/query or evidence ID. The caller writes
    this registry before asserting consistency so a STOP preserves both versions.
    Returned rows do not alias broker/model-owned mutable objects.
    """
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in [*existing, *incoming]:
        if not isinstance(row, dict):
            raise AuditIntegrityError("AUDIT_EVIDENCE_INVALID_RECORD")
        observation = _observation(row)
        if observation not in seen:
            out.append(deepcopy(row))
            seen.add(observation)
    return out


def assert_audit_evidence_consistent(evidence: list[dict[str, Any]]) -> None:
    """One ID cannot denote two observations, including found/not-found changes."""
    seen: dict[str, str] = {}
    for row in evidence:
        if not isinstance(row, dict):
            raise AuditIntegrityError("AUDIT_EVIDENCE_INVALID_RECORD")
        eid = row.get("evidence_id")
        if not isinstance(eid, str) or not eid or eid != eid.strip():
            raise AuditIntegrityError("AUDIT_EVIDENCE_INVALID_ID")
        observation = _observation(row)
        if eid in seen and seen[eid] != observation:
            raise AuditIntegrityError(f"AUDIT_EVIDENCE_CONFLICT:{eid}")
        seen[eid] = observation


def assert_audit_records_current(
    *, analyses: dict[str, dict[str, Any]], evidence: list[dict[str, Any]],
    project: Path, project_facts: dict[str, Any],
) -> None:
    """Rebind all accepted certificates to the ONE archived evidence registry.

    A source or contract change is a deterministic STOP, not a model-authorized
    retraction. No target file is imported or executed. Unsupported strengths
    cannot acquire authority by entering through persisted intermediate state.
    """
    assert_audit_evidence_consistent(evidence)
    by_id = evidence_index(evidence)
    for analysis in analyses.values():
        for row in [*(analysis.get("findings") or []),
                    *(analysis.get("keep_as_is") or [])]:
            if row.get("verification") != "VERIFIED":
                continue
            proof = row.get("semantic_proof")
            if not isinstance(proof, dict):
                raise AuditIntegrityError("AUDIT_CERTIFICATE_MISSING")
            kind = proof.get("kind")
            allowed = {
                "UNCONDITIONAL_ZERO_DIVISION": "VERIFIED_BUG",
                "DECLARED_ARITHMETIC_CONTRACT_MISMATCH": "VERIFIED_BUG",
                "MODULE_DOCSTRING_ABSENT": "OPTIONAL_IDEA",
            }
            if kind not in allowed or row.get("type") != allowed[kind]:
                raise AuditIntegrityError("AUDIT_CERTIFICATE_KIND_MISMATCH")
            ids = row.get("evidence_ids")
            if (not isinstance(ids, list) or not ids or len(ids) > 6
                    or any(not isinstance(eid, str) or eid not in by_id for eid in ids)):
                raise AuditIntegrityError("AUDIT_ARCHIVED_REFERENCE_MISSING")
            verified = _verified_source_module(
                project=project, location=str(row.get("location", "")),
                evidence_ids=ids, evidence_by_id=by_id,
            )
            if verified is None or verified[1] != proof.get("source_sha256"):
                raise AuditIntegrityError("AUDIT_SOURCE_CERTIFICATE_CHANGED")
            if kind == "DECLARED_ARITHMETIC_CONTRACT_MISMATCH":
                authority = project_facts.get("behavioral_contract_authority")
                if (not isinstance(authority, dict)
                        or authority.get("status") != "USER_SPEC_MATCHED"
                        or authority.get("sha256") != proof.get("authority_sha256")):
                    raise AuditIntegrityError("AUDIT_CONTRACT_CERTIFICATE_CHANGED")
                spec = project / "SPEC.md"
                try:
                    if spec.is_symlink() or not spec.is_file() or spec.stat().st_size > 32768:
                        raise AuditIntegrityError("AUDIT_CONTRACT_UNREADABLE")
                    spec_hash = hashlib.sha256(spec.read_bytes()).hexdigest()
                except OSError as exc:
                    raise AuditIntegrityError("AUDIT_CONTRACT_UNREADABLE") from exc
                if spec_hash != proof.get("authority_sha256"):
                    raise AuditIntegrityError("AUDIT_CONTRACT_CERTIFICATE_CHANGED")


def _certified_issue(row: dict[str, Any]) -> str | None:
    if row.get("verification") != "VERIFIED":
        return None
    return json.dumps(
        [row.get("type"), row.get("location"), row.get("semantic_proof")],
        sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False,
    )


def retain_audit_findings(
    initial: dict[str, Any], followup: dict[str, Any]
) -> dict[str, Any]:
    """Keep initial IDs; assign new, non-reused IDs to genuinely new records.

    The orchestrator rechecks both analyses against archived evidence before
    calling this function. An empty follow-up cannot silently retract a proved
    issue. Repeated certificates retain the original ID and supporting citation.
    Rejected records are retained too; a correction receives a fresh ID.
    """
    out = deepcopy(followup)
    for collection, key in (("findings", "finding_id"),
                            ("keep_as_is", "strength_id")):
        retained = deepcopy(initial.get(collection) or [])
        seen_issues = {_certified_issue(row) for row in retained}
        seen_issues.discard(None)
        existing_ids = {str(row[key]) for row in retained}
        for row in followup.get(collection) or []:
            issue = _certified_issue(row)
            if issue is not None and issue in seen_issues:
                continue
            new = deepcopy(row)
            match = re.fullmatch(r"(.+)-(\d+)", str(new.get(key, "")))
            if match is None:
                raise AuditIntegrityError("AUDIT_INTERNAL_FINDING_ID_INVALID")
            prefix = match.group(1)
            numbers = [int(m.group(1)) for ident in existing_ids
                       if (m := re.fullmatch(re.escape(prefix) + r"-(\d+)", ident))]
            new[key] = f"{prefix}-{max(numbers, default=0) + 1:03d}"
            existing_ids.add(new[key])
            retained.append(new)
            if issue is not None:
                seen_issues.add(issue)
        out[collection] = retained
    for field in ("audit_limits", "unverified_model_limits"):
        out[field] = list(dict.fromkeys(
            [*(initial.get(field) or []), *(followup.get(field) or [])]
        ))[:8]
    return out
