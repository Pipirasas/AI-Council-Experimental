"""Fail-closed contract-authority regressions for source/test mismatch audits.

Only synthetic local files and stored-format data. No model, network, or audit run.
"""
from __future__ import annotations

import hashlib
import runpy
import tempfile
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] /
          "ai_council/audit_provenance.py")
ns = runpy.run_path(str(SOURCE))
derive = ns["derive_behavioral_contract_authority"]
validate = ns["validate_specialist_analysis"]
collect = ns["collect_validated"]
build_report = ns["build_final_report"]

SUM_REQUEST = (
    "Read-only audit. AUTHORITATIVE SPECIFICATION:\n"
    "Requirement: add(a,b) must return the sum of the two arguments.\n"
    "Do not modify the project."
)
SUM_SPEC = "Requirement: add(a,b) must return the sum of the two arguments.\n"
NO_SPEC_REQUEST = (
    "Read-only audit. No authoritative behavior specification is supplied. "
    "Distinguish a source-test mismatch from a proven source defect."
)


def code_evidence(body="return a - b", name="add"):
    return {
        "evidence_id": "E-CODE", "found": True,
        "results": [{"file": "module.py",
                     "snippet": f"1: def {name}(a, b):\n2:     {body}"}],
    }


def test_evidence(name="add"):
    return {
        "evidence_id": "E-TEST", "found": True,
        "results": [{"file": "tests/test_module.py",
                     "snippet": ("1: import unittest\n2: class Tests(unittest.TestCase):\n"
                                 "3:     def test_example(self):\n"
                                 f"4:         self.assertEqual({name}(2, 3), 5)")}],
    }


def finding(reason, recommendation, *, location="module.py:2",
            evidence_ids=("E-CODE",), finding_type="VERIFIED_BUG"):
    return {
        "type": finding_type, "priority": "CRITICAL", "area": "Function semantics",
        "location": location, "evidence_ids": list(evidence_ids),
        "reason": reason, "recommendation": recommendation,
        "confidence": "HIGH",
    }


def validate_case(*, request, spec, records, findings, strengths=()):
    raw = {
        "status": "READY", "summary": "synthetic",
        "findings": list(findings), "keep_as_is": list(strengths),
        "evidence_requests": [], "audit_limits": [],
    }
    with tempfile.TemporaryDirectory() as temp:
        project = Path(temp)
        if spec is not None:
            (project / "SPEC.md").write_text(spec, encoding="utf-8")
        # Independently readable source fixture, identical to the cited
        # EvidenceBroker numbered lines. No target code gets executed.
        source_records = [
            hit for record in records for hit in (record.get("results") or [])
            if hit.get("file") == "module.py"
        ]
        if source_records:
            snippet = source_records[0]["snippet"]
            source = "\n".join(line.split(": ", 1)[1]
                               for line in snippet.splitlines()) + "\n"
            (project / "module.py").write_text(source, encoding="utf-8")
        authority = derive(project, request)
        analysis = validate(
            role_name="Universe Primer", raw=raw,
            valid_files={"module.py", "tests/test_module.py"},
            evidence=records, project_facts={
                "has_automated_tests": True,
                "behavioral_contract_authority": authority,
            },
            project=project,
        )
    return authority, analysis, collect({"Universe Primer": analysis})


class AuditBehavioralAuthorityTests(unittest.TestCase):
    def test_explicit_user_and_exact_spec_match_is_hash_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "SPEC.md").write_bytes(SUM_SPEC.encode("utf-8"))
            fact = derive(Path(tmp), SUM_REQUEST)
        self.assertEqual(fact["status"], "USER_SPEC_MATCHED")
        self.assertEqual(fact["path"], "SPEC.md")
        self.assertEqual(fact["sha256"], hashlib.sha256(SUM_SPEC.encode()).hexdigest())
        self.assertEqual(fact["symbol"], "add")
        self.assertEqual(fact["semantic_terms"], ["sum"])

    def test_explicit_no_spec_is_not_a_test_based_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            fact = derive(Path(tmp), NO_SPEC_REQUEST)
        self.assertEqual(fact["status"], "NO_AUTHORITY")
        self.assertNotIn("symbol", fact)

    def test_spec_file_alone_is_not_user_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "SPEC.md").write_text(SUM_SPEC, encoding="utf-8")
            fact = derive(Path(tmp), "Please audit the code.")
        self.assertNotEqual(fact["status"], "USER_SPEC_MATCHED")

    def test_conflicting_spec_and_request_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "SPEC.md").write_text(
                "Requirement: add(a,b) must return the difference.\n", encoding="utf-8")
            fact = derive(Path(tmp), SUM_REQUEST)
        self.assertNotEqual(fact["status"], "USER_SPEC_MATCHED")

    def test_explicit_user_requirement_without_independent_spec_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            fact = derive(Path(tmp), SUM_REQUEST)
        self.assertNotEqual(fact["status"], "USER_SPEC_MATCHED")

    def test_d01_true_source_bug_survives_with_bound_requirement(self):
        source = code_evidence()
        r = finding(
            "The implementation of add in module.py returns subtraction, while the "
            "test expects 5; the authoritative requirement says add returns the sum.",
            "Fix module.py to return a + b.")
        _, analysis, accepted = validate_case(
            request=SUM_REQUEST, spec=SUM_SPEC,
            records=[source, test_evidence()], findings=[r])
        self.assertEqual(len(accepted["findings"]), 1)
        self.assertEqual(analysis["findings"][0]["location"], "module.py")
        self.assertEqual(analysis["findings"][0]["verification"], "VERIFIED")

    def test_d01_wrong_test_expectation_rewrite_is_still_rejected(self):
        wrong = finding(
            "The source does not match the test expectation.",
            "Change the expected output in tests/test_module.py to -1.",
            location="tests/test_module.py:4", evidence_ids=("E-TEST",))
        _, analysis, accepted = validate_case(
            request=SUM_REQUEST, spec=SUM_SPEC,
            records=[code_evidence(), test_evidence()], findings=[wrong])
        self.assertEqual(accepted["findings"], [])
        self.assertIn("test_expectation_change_needs_semantic_authority",
                      analysis["findings"][0]["validation_notes"])

    def test_d02_correct_behavior_keeps_no_bugs_and_valid_strength(self):
        strength = {
            "area": "Implementation", "location": "module.py:2",
            "evidence_ids": ["E-CODE"],
            "reason": "The source uses return a + b.", "confidence": "HIGH",
        }
        _, analysis, accepted = validate_case(
            request=SUM_REQUEST, spec=SUM_SPEC,
            records=[code_evidence("return a + b"), test_evidence()],
            findings=[], strengths=[strength])
        self.assertEqual(accepted["findings"], [])
        # Source syntax alone is not a KEEP_AS_IS correctness certificate.
        self.assertEqual(accepted["strengths"], [])
        self.assertEqual(len(accepted["rejected"]), 1)
        self.assertIn("strength_lacks_positive_behavioral_proof",
                      analysis["keep_as_is"][0]["validation_notes"])

    def test_d03_three_specialists_cannot_promote_test_as_source_contract(self):
        claims = [
            finding("combine returns subtraction but tests/test_module.py expects "
                    "addition; it is a contract violation defined by the test.",
                    "Modify module.py to satisfy the test.", evidence_ids=("E-CODE",)),
            finding("The test asserts combine(2,3) == 5, while source subtracts. "
                    "The implementation violates the expected behavior.",
                    "Correct module.py to match the test."),
            finding("The code and test contradict. The test represents the "
                    "required behavior for combine.", "Fix source to match test."),
        ]
        _, analysis, accepted = validate_case(
            request=NO_SPEC_REQUEST, spec=None,
            records=[code_evidence(name="combine"), test_evidence(name="combine")],
            findings=claims)
        self.assertEqual(accepted["findings"], [])
        self.assertEqual(len(accepted["rejected"]), 3)
        for row in analysis["findings"]:
            self.assertEqual(row["verification"], "UNVERIFIED")
            self.assertIn("source_test_mismatch_no_independent_contract",
                          row["validation_notes"])
        self.assertTrue(any("SOURCE_TEST_MISMATCH_UNRESOLVED" in l
                            for l in analysis["audit_limits"]))
        report = build_report(synthesis={"finding_groups": [],
                                         "strength_ids": [],
                                         "disagreement_groups": [],
                                         "ranked_action_groups": []},
                              validated=accepted, project_facts={})
        self.assertEqual(report["findings"], [])
        self.assertIn("INCONCLUSIVE SOURCE/TEST CONTRACT",
                      report["overall_assessment"])
        self.assertTrue(any("SOURCE_TEST_MISMATCH_UNRESOLVED" in limit
                            for limit in report["audit_limits"]))

    def test_d03_fabricated_specification_in_model_text_does_not_approve(self):
        claim = finding(
            "According to SPEC.md combine should return a sum; "
            "tests/test_module.py expects 5, so this violates the contract.",
            "Change the source to addition.")
        _, analysis, accepted = validate_case(
            request=NO_SPEC_REQUEST, spec=None,
            records=[code_evidence(name="combine"), test_evidence(name="combine")],
            findings=[claim])
        self.assertEqual(accepted["findings"], [])
        self.assertEqual(analysis["findings"][0]["verification"], "UNVERIFIED")

    def test_unrelated_improvement_does_not_become_test_mismatch(self):
        r = finding("This short source has no module-level docstring.",
                    "Add a module docstring.", finding_type="IMPROVEMENT")
        _, analysis, accepted = validate_case(
            request=NO_SPEC_REQUEST, spec=None,
            records=[code_evidence("return a - b"), test_evidence()],
            findings=[r])
        # The narrow guard does not add an invented test-based contract for a
        # genuine, source-observable documentation opportunity.
        self.assertEqual(analysis["findings"][0]["verification"], "VERIFIED")
        self.assertEqual(len(accepted["findings"]), 1)

    def test_fabricated_contract_source_defect_without_test_is_not_verified(self):
        claim = finding(
            "The supposed specification requires combine to return a sum; "
            "the source violates its behavioral contract.",
            "Change module.py to return addition.")
        _, analysis, accepted = validate_case(
            request=NO_SPEC_REQUEST, spec=None,
            records=[code_evidence(name="combine"), test_evidence(name="combine")],
            findings=[claim])
        self.assertEqual(accepted["findings"], [])
        self.assertIn("source_defect_no_independent_behavior_contract",
                      analysis["findings"][0]["validation_notes"])

    def test_unrelated_regression_test_recommendation_does_not_trigger_guard(self):
        claim = finding(
            "The function add unconditionally divides by numeric zero, causing "
            "ZeroDivisionError for any call.",
            "Fix the division-by-zero bug, then add regression tests.")
        _, analysis, accepted = validate_case(
            request=NO_SPEC_REQUEST, spec=None,
            records=[code_evidence("return 1 / 0"), test_evidence()],
            findings=[claim])
        # An intrinsic runtime failure is not a source-vs-test mismatch.
        # Mentioning regression tests in the recommendation is not evidence.
        self.assertEqual(analysis["findings"][0]["verification"], "VERIFIED")

    def test_matched_but_unrelated_authoritative_spec_does_not_authorize_other_symbol(self):
        r = finding("combine violates the test's expected sum.",
                    "Fix combine to pass the test.")
        _, analysis, accepted = validate_case(
            request=SUM_REQUEST, spec=SUM_SPEC,
            records=[code_evidence(name="combine"), test_evidence(name="combine")],
            findings=[r])
        self.assertEqual(accepted["findings"], [])
        self.assertIn("source_test_claim_not_bound_to_contract",
                      analysis["findings"][0]["validation_notes"])

    def test_matched_spec_requires_semantic_term_in_claim(self):
        r = finding("The test asserts the function add returns 5, whereas module.py differs.",
                    "Change source to meet the test.")
        _, analysis, accepted = validate_case(
            request=SUM_REQUEST, spec=SUM_SPEC,
            records=[code_evidence(), test_evidence()],
            findings=[r])
        self.assertEqual(accepted["findings"], [])
        self.assertIn("source_test_claim_not_bound_to_contract",
                      analysis["findings"][0]["validation_notes"])


if __name__ == "__main__":
    unittest.main()
