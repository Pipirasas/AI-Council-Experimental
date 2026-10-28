"""Test-first: audit provenance accepts only evidence-backed line locations.

Synthetic D01-analogue only.  No model calls, external input, or repair actions.
"""
from __future__ import annotations

import runpy
import tempfile
import unittest
from pathlib import Path

SOURCE = (
    Path(__file__).resolve().parents[1] /
    "ai_council/audit_provenance.py"
)
ns = runpy.run_path(str(SOURCE))
validate = ns["validate_specialist_analysis"]
collect_validated = ns["collect_validated"]
derive_contract = ns["derive_behavioral_contract_authority"]

# PR #28 introduces a separate trusted contract boundary; these legacy
# PR #25 tests must supply the contract they were already assuming.
with tempfile.TemporaryDirectory() as _fixture:
    _spec = "Requirement: total(a,b) must return the sum of the two arguments.\n"
    (Path(_fixture) / "SPEC.md").write_text(_spec, encoding="utf-8")
    SOURCE_CONTRACT = derive_contract(Path(_fixture), "AUTHORITATIVE SPECIFICATION:\n" + _spec)
assert SOURCE_CONTRACT["status"] == "USER_SPEC_MATCHED"


SRC_ID = "E-SRC"
TEST_ID = "E-TEST"
SOURCE_EVIDENCE = {
    "evidence_id": SRC_ID, "found": True, "query": "widget.py",
    "results": [{"file": "widget.py",
                 "snippet": "1: def total(a, b):\n2:     return a - b\n3: "}]
}
TEST_EVIDENCE = {
    "evidence_id": TEST_ID, "found": True, "query": "tests/test_widget.py",
    "results": [{"file": "tests/test_widget.py",
                 "snippet": "1: from widget import total\n2: import unittest\n"
                            "3: class TestWidget(unittest.TestCase):\n"
                            "4:     def test_total(self):\n"
                            "5:         self.assertEqual(total(2, 3), 5)"}]
}


def claim(location, ids, *, reason=None, recommendation=None):
    return {
        "type": "VERIFIED_BUG", "priority": "HIGH", "area": "Implementation",
        "location": location, "evidence_ids": list(ids),
        "reason": reason or "The source total computes subtraction; the contract requires the sum (addition).",
        "recommendation": recommendation or "Change the implementation to addition.",
        "confidence": "HIGH"
    }


def check(findings=None, strengths=None, evidence=None):
    raw = {
        "status": "READY", "summary": "synthetic",
        "findings": list(findings or []), "keep_as_is": list(strengths or []),
        "evidence_requests": [], "audit_limits": [],
    }
    # Full, exact source fixture binds this provenance test to a real source
    # snapshot instead of pretending a snippet alone proves runtime semantics.
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "SPEC.md").write_text(_spec, encoding="utf-8")
        (Path(tmp) / "widget.py").write_text(
            "def total(a, b):\n    return a - b\n\n", encoding="utf-8")
        return validate(
            role_name="LUA Programming GOD", raw=raw,
            valid_files={"widget.py", "tests/test_widget.py"},
            evidence=list(evidence if evidence is not None else [SOURCE_EVIDENCE, TEST_EVIDENCE]),
            project_facts={"has_automated_tests": True,
                           "behavioral_contract_authority": SOURCE_CONTRACT},
            project=Path(tmp),
        )


class AuditLineLocationEvidenceTests(unittest.TestCase):
    def test_01_cited_source_path_line_is_bound_and_canonical(self):
        f = check([claim("widget.py:2", [SRC_ID])])["findings"][0]
        self.assertEqual(f["verification"], "VERIFIED")
        self.assertEqual(f["location"], "widget.py")
        self.assertEqual(f["evidence_ids"], [SRC_ID])

    def test_02_line_only_with_unique_cited_file_is_bound(self):
        f = check([claim("line 2", [SRC_ID],
                         reason="The implementation of total in widget.py at line 2 subtracts rather than adds.")])["findings"][0]
        self.assertEqual(f["verification"], "VERIFIED")
        self.assertEqual(f["location"], "widget.py")
        self.assertEqual(f["evidence_ids"], [SRC_ID])

    def test_03_do_not_guess_file_when_line_only_has_two_citations(self):
        f = check([claim("line 2", [SRC_ID, TEST_ID])])["findings"][0]
        self.assertEqual(f["verification"], "UNVERIFIED")
        self.assertIn("location_not_in_project", f["validation_notes"])

    def test_04_wrong_id_does_not_validate_other_file_line(self):
        f = check([claim("widget.py:2", [TEST_ID])])["findings"][0]
        self.assertEqual(f["verification"], "UNVERIFIED")
        self.assertEqual(f["evidence_ids"], [])

    def test_05_nonexistent_line_does_not_bypass_evidence_check(self):
        f = check([claim("widget.py:99", [SRC_ID])])["findings"][0]
        self.assertEqual(f["verification"], "UNVERIFIED")
        self.assertEqual(f["evidence_ids"], [])

    def test_06_nonexistent_path_line_does_not_become_valid(self):
        f = check([claim("ghost.py:2", [SRC_ID])])["findings"][0]
        self.assertEqual(f["verification"], "UNVERIFIED")

    def test_07_fabricated_evidence_id_cannot_resolve_line_only(self):
        f = check([claim("line 2", ["NOT_A_REAL_ID"])])["findings"][0]
        self.assertEqual(f["verification"], "UNVERIFIED")
        self.assertEqual(f["evidence_ids"], [])

    def test_08_conflicting_duplicate_id_cannot_validate_line(self):
        forged = {
            "evidence_id": SRC_ID, "found": True,
            "results": [{"file": "tests/test_widget.py", "snippet": "2: assert True"}],
        }
        f = check([claim("widget.py:2", [SRC_ID])],
                  evidence=[SOURCE_EVIDENCE, forged])["findings"][0]
        self.assertEqual(f["verification"], "UNVERIFIED")

    def test_09_bare_existing_path_remains_valid(self):
        f = check([claim("widget.py", [SRC_ID])])["findings"][0]
        self.assertEqual(f["verification"], "VERIFIED")
        self.assertEqual(f["location"], "widget.py")

    def test_10_range_location_only_accepts_lines_in_cited_snippet(self):
        f = check([claim("widget.py:1-2", [SRC_ID])])["findings"][0]
        self.assertEqual(f["verification"], "VERIFIED")
        self.assertEqual(f["location"], "widget.py")
        rejected = check([claim("widget.py:2-99", [SRC_ID])])["findings"][0]
        self.assertEqual(rejected["verification"], "UNVERIFIED")

    def test_11_preserve_test_expectation_change_guard(self):
        f = check([claim(
            "tests/test_widget.py:5", [TEST_ID],
            reason="The test expects 5 for total(2,3) but source returns -1.",
            recommendation="Update the expected output in the test to -1."
        )])["findings"][0]
        self.assertEqual(f["location"], "tests/test_widget.py")
        self.assertEqual(f["verification"], "UNVERIFIED")
        self.assertIn("test_expectation_change_needs_semantic_authority", f["validation_notes"])

    def test_12_valid_source_findings_survive_but_invalid_test_edit_does_not(self):
        out = check([
            claim("widget.py:2", [SRC_ID]),
            claim("line 2", [SRC_ID],
                  reason="total in widget.py:2 returns subtraction, violating the written sum requirement."),
            claim("tests/test_widget.py:5", [TEST_ID],
                  reason="Current source returns subtraction.",
                  recommendation="Change the expected output in tests/test_widget.py to -1."),
        ])
        validated = collect_validated({"LUA Programming GOD": out})
        self.assertEqual(len(validated["findings"]), 2)
        self.assertEqual(len(validated["rejected"]), 1)
        self.assertEqual([x["location"] for x in validated["findings"]], ["widget.py", "widget.py"])

    def test_13_line_only_unknown_extra_id_cannot_infer(self):
        f = check([claim("line 2", [SRC_ID, "BOGUS_ID"])])["findings"][0]
        self.assertEqual(f["verification"], "UNVERIFIED")

    def test_14_unsupported_line_like_text_is_not_interpreted(self):
        f = check([claim("widget.py:line two", [SRC_ID])])["findings"][0]
        self.assertEqual(f["verification"], "UNVERIFIED")

    def test_15_strength_location_uses_same_grounding(self):
        strength = {"area": "Source", "location": "widget.py:2",
                    "evidence_ids": [SRC_ID],
                    "reason": "The current source has a concrete return statement.",
                    "confidence": "MEDIUM"}
        s = check(strengths=[strength])["keep_as_is"][0]
        self.assertEqual(s["location"], "widget.py")
        self.assertEqual(s["evidence_ids"], [SRC_ID])
        # Correct line/location binding is not semantic endorsement of an
        # arbitrary KEEP_AS_IS reason.
        self.assertEqual(s["verification"], "UNVERIFIED")
        self.assertIn("nonbug_claim_lacks_deterministic_semantic_proof",
                      s["validation_notes"])


if __name__ == "__main__":
    unittest.main()
