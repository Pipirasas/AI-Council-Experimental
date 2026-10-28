"""Narrow, fail-closed checks against self-contradicting source-linked audit claims.

These tests use invented project paths and snippets; no live Council execution or
user-provided audit records are committed. Only the pure validator is imported.
"""
from __future__ import annotations

import runpy
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1]
          / "ai_council/audit_provenance.py")
module = runpy.run_path(str(SOURCE))
validate = module["validate_specialist_analysis"]
collect_validated = module["collect_validated"]


def evidence(eid, file, snippet):
    return {"evidence_id": eid, "kind": "path", "query": file, "found": True,
            "results": [{"file": file, "snippet": snippet}]}


TEST = evidence("E-TEST", "tests/test_widget.py",
                "1: import unittest\n2: class WidgetTests(unittest.TestCase):\n"
                "3:     def test_total(self):\n"
                "4:         self.assertEqual(total(2, 3), 5)")
SOURCE_CODE = evidence("E-SOURCE", "widget.py",
                       "1: def total(a, b):\n2:     return a - b")


def finding(*, reason, recommendation, location="tests/test_widget.py",
            ids=("E-TEST",)):
    return {
        "type": "IMPROVEMENT", "priority": "MEDIUM", "area": "Tests",
        "location": location, "evidence_ids": list(ids),
        "reason": reason, "recommendation": recommendation, "confidence": "HIGH",
    }


def strength(*, reason, ids=("E-TEST",)):
    return {"area": "Tests", "location": "tests/test_widget.py",
            "evidence_ids": list(ids), "reason": reason, "confidence": "HIGH"}


def check(*, findings=None, strengths=None, records=None):
    raw = {"status": "READY", "summary": "synthetic",
           "findings": list(findings or []), "keep_as_is": list(strengths or []),
           "evidence_requests": [], "audit_limits": []}
    return validate(
        role_name="LUA Programming GOD",
        raw=raw,
        valid_files={"tests/test_widget.py", "widget.py"},
        evidence=list(records if records is not None else [TEST, SOURCE_CODE]),
        project_facts={"has_automated_tests": True},
    )


class AuditClaimEvidenceGuardTests(unittest.TestCase):
    def test_literal_expected_value_refutes_missing_expected_output(self):
        out = check(findings=[finding(
            reason="The expected output is not provided for this test.",
            recommendation="Add the missing expected result.")])
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")
        self.assertIn("expected_result_present_in_cited_test",
                      out["findings"][0]["validation_notes"])

    def test_pytest_literal_assertion_also_refutes_absence(self):
        record = evidence("E-TEST", "tests/test_widget.py",
                          "8: def test_total():\n9:     assert total(2, 3) == 5")
        out = check(findings=[finding(
            reason="There is no expected result in the test.",
            recommendation="Add an expected result.")], records=[record])
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")

    def test_test_expected_value_rewrite_requires_independent_evidence(self):
        out = check(findings=[finding(
            reason="The test is incorrect and should match the implementation.",
            recommendation="Update the test case to match the expected output.",
            ids=("E-TEST",))])
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")
        self.assertIn("test_expectation_change_missing_independent_evidence",
                      out["findings"][0]["validation_notes"])

    def test_mirrored_false_strength_cannot_be_verified(self):
        out = check(strengths=[
            strength(reason="The expected output is not provided in this test."),
            strength(reason="Correct this test by changing its expected output to match implementation."),
        ])
        self.assertEqual([x["verification"] for x in out["keep_as_is"]],
                         ["UNVERIFIED", "UNVERIFIED"])

    def test_rejected_claims_do_not_become_synthesis_findings(self):
        out = check(findings=[
            finding(reason="The expected output is not provided.",
                    recommendation="Add the expected result."),
            finding(reason="The test is incorrect; the current code differs.",
                    recommendation="Update the test case to match the expected output.",
                    ids=("E-TEST",)),
        ], strengths=[strength(reason="The expected output is not provided.")])
        valid = collect_validated({"LUA Programming GOD": out})
        self.assertEqual(valid["findings"], [])
        self.assertEqual(valid["strengths"], [])
        self.assertEqual(len(valid["rejected"]), 3)

    def test_legitimate_source_finding_is_not_discarded(self):
        out = check(findings=[finding(
            reason="The current source subtracts instead of adding.",
            recommendation="Correct the source implementation.",
            location="widget.py", ids=("E-SOURCE",))])
        # Provenance and PR23 scope are preserved; semantic truth is not
        # inferred from the presence of a cited file alone.
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")
        self.assertIn("nonbug_claim_lacks_deterministic_semantic_proof",
                      out["findings"][0]["validation_notes"])
        self.assertTrue(out["findings"][0]["evidence_ids"])

    def test_source_current_behavior_is_not_authority_to_rewrite_a_test(self):
        # Source implementation alone does not establish the intended
        # behavior, even when both source and test are cited. A contract or
        # independent semantic oracle must authorize changing the expectation.
        out = check(findings=[finding(
            reason="The source and expected test value must be compared.",
            recommendation="Update the test case to match the expected output.",
            ids=("E-TEST", "E-SOURCE"))])
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")
        self.assertIn("test_expectation_change_needs_semantic_authority",
                      out["findings"][0]["validation_notes"])

    def test_do_not_change_existing_expectation_is_not_an_edit(self):
        out = check(findings=[finding(
            reason="The test already documents the expected value.",
            recommendation="Do not change the test's expected output.",
            ids=("E-TEST",))])
        # Provenance and PR23 scope are preserved; semantic truth is not
        # inferred from the presence of a cited file alone.
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")
        self.assertIn("nonbug_claim_lacks_deterministic_semantic_proof",
                      out["findings"][0]["validation_notes"])
        self.assertTrue(out["findings"][0]["evidence_ids"])
        self.assertNotIn("test_expectation_change_needs_semantic_authority",
                         out["findings"][0]["validation_notes"])

    def test_sibling_test_assertion_does_not_refute_missing_expected_result(self):
        # One file contains two cases, but only the first has an expected
        # literal. A finding about the second case is not disproven by it.
        record = evidence(
            "E-TEST", "tests/test_widget.py",
            "1: def test_total(self):\n"
            "2:     self.assertEqual(total(2, 3), 5)\n"
            "3: def test_difference(self):\n"
            "4:     actual = difference(3, 2)")
        out = check(findings=[finding(
            reason="In test_difference the expected output is not provided.",
            recommendation="Add an expected result for test_difference.")],
            records=[record])
        # Provenance and PR23 scope are preserved; semantic truth is not
        # inferred from the presence of a cited file alone.
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")
        self.assertIn("nonbug_claim_lacks_deterministic_semantic_proof",
                      out["findings"][0]["validation_notes"])
        self.assertTrue(out["findings"][0]["evidence_ids"])
        self.assertNotIn("expected_result_present_in_cited_test",
                         out["findings"][0]["validation_notes"])

    def test_named_case_with_an_expected_value_remains_refuted(self):
        record = evidence(
            "E-TEST", "tests/test_widget.py",
            "1: def test_total(self):\n"
            "2:     self.assertEqual(total(2, 3), 5)\n"
            "3: def test_difference(self):\n"
            "4:     actual = difference(3, 2)")
        out = check(findings=[finding(
            reason="In test_total the expected result is not provided.",
            recommendation="Add an expected result for test_total.")],
            records=[record])
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")

    def test_comment_does_not_create_an_expected_result(self):
        record = evidence(
            "E-TEST", "tests/test_widget.py",
            "1: def test_total():\n"
            "2:     assert total(2, 3)  # TODO: expected result == 5")
        out = check(findings=[finding(
            reason="The expected output is not provided in this test.",
            recommendation="Add an expected value.")], records=[record])
        # Provenance and PR23 scope are preserved; semantic truth is not
        # inferred from the presence of a cited file alone.
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")
        self.assertIn("nonbug_claim_lacks_deterministic_semantic_proof",
                      out["findings"][0]["validation_notes"])
        self.assertTrue(out["findings"][0]["evidence_ids"])
        self.assertNotIn("expected_result_present_in_cited_test",
                         out["findings"][0]["validation_notes"])

    def test_multiline_docstring_is_not_executable_assertion(self):
        record = evidence(
            "E-TEST", "tests/test_widget.py",
            "1: def test_total():\n"
            "2:     '''Example:\n"
            "3:     assert total(2, 3) == 5\n"
            "4:     '''\n"
            "5:     assert total(2, 3)")
        out = check(findings=[finding(
            reason="The expected output is not provided in this test.",
            recommendation="Add a concrete expected value.")], records=[record])
        # Provenance and PR23 scope are preserved; semantic truth is not
        # inferred from the presence of a cited file alone.
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")
        self.assertIn("nonbug_claim_lacks_deterministic_semantic_proof",
                      out["findings"][0]["validation_notes"])
        self.assertTrue(out["findings"][0]["evidence_ids"])
        self.assertNotIn("expected_result_present_in_cited_test",
                         out["findings"][0]["validation_notes"])

    def test_pytest_quoted_expected_value_is_explicit(self):
        record = evidence(
            "E-TEST", "tests/test_widget.py",
            "1: def test_name():\n"
            "2:     assert name() == 'widget'")
        out = check(findings=[finding(
            reason="The expected output is not provided in this test.",
            recommendation="Add an expected string.")], records=[record])
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")

    def test_negating_source_edit_does_not_authorize_test_expected_rewrite(self):
        out = check(findings=[finding(
            reason="The implementation returns -1.",
            recommendation="Do not change the source. Update the expected output to -1.",
            ids=("E-TEST",))])
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")
        self.assertIn("test_expectation_change_needs_semantic_authority",
                      out["findings"][0]["validation_notes"])

    def test_rewrite_in_reason_cannot_hide_behind_generic_recommendation(self):
        out = check(findings=[finding(
            reason="Change the expected output to -1 to match the implementation.",
            recommendation="Apply this correction.",
            ids=("E-TEST",))])
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")

    def test_source_implementation_fix_is_not_test_expectation_rewrite(self):
        out = check(findings=[finding(
            reason="The assertion exposes a source bug; keep the expected output unchanged.",
            recommendation="Fix the implementation to return the expected output.",
            ids=("E-TEST",))])
        # Provenance and PR23 scope are preserved; semantic truth is not
        # inferred from the presence of a cited file alone.
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")
        self.assertIn("nonbug_claim_lacks_deterministic_semantic_proof",
                      out["findings"][0]["validation_notes"])
        self.assertTrue(out["findings"][0]["evidence_ids"])
        self.assertNotIn("test_expectation_change_needs_semantic_authority",
                         out["findings"][0]["validation_notes"])

    def test_class_qualified_same_method_names_cannot_cross_contaminate(self):
        record = evidence(
            "E-TEST", "tests/test_widget.py",
            "1: class TestTotal:\n"
            "2:     def test_result(self):\n"
            "3:         assert total(2, 3) == 5\n"
            "4: class TestDifference:\n"
            "5:     def test_result(self):\n"
            "6:         actual = difference(3, 2)")
        out = check(findings=[finding(
            reason="In TestDifference.test_result the expected output is not provided.",
            recommendation="Add an expected output.")], records=[record])
        # Provenance and PR23 scope are preserved; semantic truth is not
        # inferred from the presence of a cited file alone.
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")
        self.assertIn("nonbug_claim_lacks_deterministic_semantic_proof",
                      out["findings"][0]["validation_notes"])
        self.assertTrue(out["findings"][0]["evidence_ids"])
        self.assertNotIn("expected_result_present_in_cited_test",
                         out["findings"][0]["validation_notes"])

    def test_class_qualified_matching_assertion_still_refutes_absence(self):
        record = evidence(
            "E-TEST", "tests/test_widget.py",
            "1: class TestTotal:\n"
            "2:     def test_result(self):\n"
            "3:         assert total(2, 3) == 5\n"
            "4: class TestDifference:\n"
            "5:     def test_result(self):\n"
            "6:         actual = difference(3, 2)")
        out = check(findings=[finding(
            reason="In TestTotal.test_result the expected output is not provided.",
            recommendation="Add the expected value.")], records=[record])
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")

    def test_ambiguous_unqualified_method_name_does_not_imply_all_tests(self):
        record = evidence(
            "E-TEST", "tests/test_widget.py",
            "1: class TestTotal:\n"
            "2:     def test_result(self):\n"
            "3:         assert total(2, 3) == 5\n"
            "4: class TestDifference:\n"
            "5:     def test_result(self):\n"
            "6:         actual = difference(3, 2)")
        out = check(findings=[finding(
            reason="In test_result the expected output is not provided.",
            recommendation="Add a literal expected value.")], records=[record])
        # Provenance and PR23 scope are preserved; semantic truth is not
        # inferred from the presence of a cited file alone.
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")
        self.assertIn("nonbug_claim_lacks_deterministic_semantic_proof",
                      out["findings"][0]["validation_notes"])
        self.assertTrue(out["findings"][0]["evidence_ids"])
        self.assertNotIn("expected_result_present_in_cited_test",
                         out["findings"][0]["validation_notes"])

    def test_assertion_in_uncited_file_does_not_refute_claim(self):
        without_assertion = evidence(
            "E-TEST", "tests/test_widget.py",
            "1: def test_total():\n2:     check_total()")
        out = check(findings=[finding(
            reason="The expected output is not provided in this test.",
            recommendation="Add a concrete expected output.")],
            records=[without_assertion, TEST | {"evidence_id": "E-OTHER",
                                                "results": [{"file": "tests/other.py",
                                                             "snippet": "assert total(2, 3) == 5"}]}])
        # Provenance and PR23 scope are preserved; semantic truth is not
        # inferred from the presence of a cited file alone.
        self.assertEqual(out["findings"][0]["verification"], "UNVERIFIED")
        self.assertIn("nonbug_claim_lacks_deterministic_semantic_proof",
                      out["findings"][0]["validation_notes"])
        self.assertTrue(out["findings"][0]["evidence_ids"])
        self.assertNotIn("expected_result_present_in_cited_test",
                         out["findings"][0]["validation_notes"])


if __name__ == "__main__":
    unittest.main()
