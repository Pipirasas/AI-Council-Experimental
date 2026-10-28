"""Fail-closed evidence ID regression tests, without importing Council runtime."""

from __future__ import annotations

import unittest
from pathlib import Path


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "ai_council/audit_provenance.py"
)
namespace = {"__name__": "_audit_id_collision_test", "__file__": str(SOURCE)}
exec(compile(SOURCE.read_bytes(), str(SOURCE), "exec"), namespace)
validate = namespace["validate_specialist_analysis"]
collect_validated = namespace["collect_validated"]
synthesis_input = namespace["synthesis_input"]

FILES = {"source/target.py", "source/other.py"}


def evidence(evidence_id: str, file: str) -> dict:
    return {
        "evidence_id": evidence_id,
        "kind": "path",
        "query": file,
        "found": True,
        "results": [{"file": file, "snippet": "1: x = 1"}],
    }


def analysis(records: list[dict], *, include_strength: bool = False) -> dict:
    raw = {
        "status": "READY",
        "summary": "synthetic audit",
        "findings": [{
            "type": "IMPROVEMENT",
            "priority": "HIGH",
            "area": "Evidence identity",
            "location": "source/target.py",
            "evidence_ids": ["ESHARED"],
            "reason": "A finding with one evidence reference.",
            "recommendation": "Retain validated evidence.",
            "confidence": "HIGH",
        }],
        "keep_as_is": [{
            "area": "Evidence identity",
            "location": "source/target.py",
            "evidence_ids": ["ESHARED"],
            "reason": "A supported source claim.",
            "confidence": "HIGH",
        }] if include_strength else [],
        "evidence_requests": [],
        "audit_limits": [],
    }
    return validate(
        role_name="LUA Programming GOD",
        raw=raw,
        valid_files=FILES,
        evidence=records,
        project_facts={},
    )


class EvidenceIdCollisionTests(unittest.TestCase):
    def test_conflicting_id_does_not_validate_when_matching_row_is_last(self):
        rows = [evidence("ESHARED", "source/other.py"),
                evidence("ESHARED", "source/target.py")]
        finding = analysis(rows)["findings"][0]
        self.assertEqual(finding["verification"], "UNVERIFIED")
        self.assertEqual(finding["evidence_ids"], [])
        self.assertIn("no_evidence_id_supports_location", finding["validation_notes"])

    def test_conflicting_id_is_order_independent(self):
        a = evidence("ESHARED", "source/other.py")
        b = evidence("ESHARED", "source/target.py")
        for rows in ([a, b], [b, a]):
            with self.subTest(order=[x["query"] for x in rows]):
                self.assertEqual(analysis(rows)["findings"][0]["verification"],
                                 "UNVERIFIED")

    def test_conflicting_id_cannot_validate_strength(self):
        rows = [evidence("ESHARED", "source/other.py"),
                evidence("ESHARED", "source/target.py")]
        value = analysis(rows, include_strength=True)
        self.assertEqual(value["keep_as_is"][0]["verification"], "UNVERIFIED")
        self.assertEqual(value["keep_as_is"][0]["evidence_ids"], [])

    def test_conflicting_id_not_fed_to_synthesizer(self):
        rows = [evidence("ESHARED", "source/other.py"),
                evidence("ESHARED", "source/target.py")]
        validated = collect_validated({"LUA Programming GOD": analysis(rows)})
        self.assertEqual(synthesis_input(validated)["validated_findings"], [])
        self.assertEqual(len(validated["rejected"]), 1)

    def test_identical_duplicate_rows_are_idempotent(self):
        one = evidence("ESHARED", "source/target.py")
        value = analysis([one, dict(one)])
        self.assertEqual(value["findings"][0]["verification"], "UNVERIFIED")
        self.assertEqual(value["findings"][0]["evidence_ids"], ["ESHARED"])
        self.assertNotIn("no_evidence_id_supports_location",
                         value["findings"][0]["validation_notes"])
        self.assertIn("nonbug_claim_lacks_deterministic_semantic_proof",
                      value["findings"][0]["validation_notes"])

    def test_distinct_ids_and_absent_ids_preserve_existing_contract(self):
        matching = evidence("ESHARED", "source/target.py")
        other = evidence("EOTHER", "source/other.py")
        valid = analysis([other, matching])
        self.assertEqual(valid["findings"][0]["verification"], "UNVERIFIED")
        self.assertEqual(valid["findings"][0]["evidence_ids"], ["ESHARED"])
        self.assertNotIn("no_evidence_id_supports_location",
                         valid["findings"][0]["validation_notes"])
        absent = analysis([other])
        self.assertEqual(absent["findings"][0]["verification"], "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
