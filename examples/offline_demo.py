"""AI Council R0: synthetic source-level certificate demo. Never run target code."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ai_council.audit_provenance import (
    derive_behavioral_contract_authority,
    validate_specialist_analysis,
    collect_validated,
)

SPEC = "Requirement: add(a,b) must return the sum of the two arguments.\n"
REQUEST = "Read-only audit. AUTHORITATIVE SPECIFICATION:\n" + SPEC
SOURCE = "def add(a, b):\n    return a - b\n"


def run_demo() -> dict:
    """Demonstrate one narrowly proven mismatch and one source-only abstention."""
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        (project / "SPEC.md").write_bytes(SPEC.encode("utf-8"))
        (project / "module.py").write_bytes(SOURCE.encode("utf-8"))
        evidence = [{
            "evidence_id": "E-SYNTHETIC", "kind": "path", "query": "module.py",
            "found": True, "results": [{"file": "module.py", "snippet":
                "1: def add(a, b):\n2:     return a - b"}],
        }]
        raw = {
            "status": "READY", "summary": "synthetic only",
            "findings": [{
                "type": "VERIFIED_BUG", "priority": "HIGH", "area": "Arithmetic contract",
                "location": "module.py:2", "evidence_ids": ["E-SYNTHETIC"],
                "reason": "add uses subtraction although the sum is required by the specification.",
                "recommendation": "Change the return expression from subtraction to addition.",
                "confidence": "HIGH",
            }],
            "keep_as_is": [], "evidence_requests": [], "audit_limits": [],
        }
        authority = derive_behavioral_contract_authority(project, REQUEST)
        approved = validate_specialist_analysis(
            role_name="Synthetic Reviewer", raw=raw, valid_files={"module.py"},
            evidence=evidence, project_facts={"behavioral_contract_authority": authority},
            project=project,
        )
        missing = validate_specialist_analysis(
            role_name="Synthetic Reviewer", raw=raw, valid_files={"module.py"},
            evidence=evidence, project_facts={"behavioral_contract_authority": {"status": "NO_AUTHORITY"}},
            project=project,
        )
        verified = collect_validated({"Synthetic Reviewer": approved})
        withheld = collect_validated({"Synthetic Reviewer": missing})
    return {
        "demo": "synthetic_offline_only",
        "target_code_executed": False,
        "model_calls": 0,
        "verified_with_authority": len(verified["findings"]),
        "verified_without_authority": len(withheld["findings"]),
        "claim": "Supported only for the explicitly parsed arithmetic subset",
    }


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2, sort_keys=True))
