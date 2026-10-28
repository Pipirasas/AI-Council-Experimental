"""Adversarial, deterministic semantic-authority controls (no model calls).

These fixtures deliberately use synthetic source snippets only. A cited code
location identifies WHAT was observed, not WHY an arbitrary behavioral claim
is true. The verifier must independently establish that particular defect.
"""
from __future__ import annotations

import runpy
import tempfile
import unittest
from pathlib import Path

PROVENANCE = (Path(__file__).resolve().parents[1] /
              "ai_council/audit_provenance.py")
ns = runpy.run_path(str(PROVENANCE))
derive = ns["derive_behavioral_contract_authority"]
validate = ns["validate_specialist_analysis"]
collect = ns["collect_validated"]
build_final = ns["build_final_report"]

REQUEST_SUM = (
    "Read-only audit. AUTHORITATIVE SPECIFICATION:\n"
    "Requirement: add(a,b) must return the sum of the two arguments.\n"
    "Do not modify the project."
)
SPEC_SUM = "Requirement: add(a,b) must return the sum of the two arguments.\n"
REQUEST_UNSPECIFIED = (
    "Read-only audit. No authoritative behavior specification is supplied. "
    "Distinguish a source-test mismatch from a source defect."
)


def case(*, body, reason, recommendation="Change source.", request=REQUEST_UNSPECIFIED,
         spec=None, symbol="combine", location="module.py:2", duplicates=None,
         cited_snippet=None, evidence_ids=("E-SRC",), mutate_spec_to=None):
    if duplicates is None:
        snippet = f"1: def {symbol}(a,b):\n2:     {body}"
    else:
        snippet = duplicates
    evidence = [{
        "evidence_id": "E-SRC", "found": True,
        "results": [{"file": "module.py",
                     "snippet": cited_snippet if cited_snippet is not None else snippet}],
    }]
    claim = {
        "type": "VERIFIED_BUG", "priority": "CRITICAL",
        "area": "Implementation", "location": location,
        "evidence_ids": list(evidence_ids),
        "reason": reason, "recommendation": recommendation, "confidence": "HIGH",
    }
    with tempfile.TemporaryDirectory() as folder:
        project = Path(folder)
        if spec is not None:
            (project / "SPEC.md").write_text(spec, encoding="utf-8")
        source = "\n".join(line.split(": ", 1)[1]
                           for line in snippet.splitlines()) + "\n"
        (project / "module.py").write_text(source, encoding="utf-8")
        authority = derive(project, request)
        if mutate_spec_to is not None:
            (project / "SPEC.md").write_text(mutate_spec_to, encoding="utf-8")
        return validate(role_name="Universe Primer", raw={
            "status": "READY", "summary": "synthetic",
            "findings": [claim], "keep_as_is": [],
            "evidence_requests": [], "audit_limits": [],
        }, valid_files={"module.py", "tests/test_module.py"},
            evidence=evidence,
            project_facts={"behavioral_contract_authority": authority},
            project=project)


class SemanticAuthorityProofTests(unittest.TestCase):
    def test_adversarial_desired_output_bypasses_prior_regex_but_not_proof(self):
        a = case(
            body="return a - b",
            reason=("The function combine(2,3) returns -1, but the desired "
                    "output is 5. The implementation is incorrect."),
            recommendation="Replace subtraction with addition.")
        self.assertEqual(a["findings"][0]["verification"], "UNVERIFIED")

    def test_adversarial_intended_behavior_avoids_prior_regex(self):
        a = case(body="return a - b",
                 reason="The algorithm performs subtraction, whereas the intended output is addition.")
        self.assertEqual(a["findings"][0]["verification"], "UNVERIFIED")

    def test_no_spec_plain_claim_without_trigger_word_fails_closed(self):
        a = case(body="return a - b", reason="The module has a critical flaw.",
                 recommendation="Fix it.")
        self.assertEqual(a["findings"][0]["verification"], "UNVERIFIED")

    def test_no_spec_test_based_claim_still_fails_closed(self):
        a = case(body="return a - b",
                 reason="The test expects combine(2,3)==5, so code is broken.")
        self.assertEqual(a["findings"][0]["verification"], "UNVERIFIED")

    def test_real_spec_and_source_operator_mismatch_has_independent_certificate(self):
        a = case(body="return a - b", symbol="add",
                 request=REQUEST_SUM, spec=SPEC_SUM,
                 reason="add uses subtraction, but it must return the sum of its two arguments.")
        row = a["findings"][0]
        self.assertEqual(row["verification"], "VERIFIED")
        self.assertEqual(row["semantic_proof"]["kind"], "DECLARED_ARITHMETIC_CONTRACT_MISMATCH")
        self.assertEqual(row["semantic_proof"]["observed_operator"], "SUB")
        self.assertEqual(row["semantic_proof"]["expected_operator"], "ADD")
        self.assertEqual(row["priority"], "MEDIUM")

    def test_real_spec_correct_source_cannot_be_called_broken(self):
        a = case(body="return a + b", symbol="add",
                 request=REQUEST_SUM, spec=SPEC_SUM,
                 reason="add uses subtraction and violates the sum requirement.")
        self.assertEqual(a["findings"][0]["verification"], "UNVERIFIED")

    def test_spec_changed_after_authority_identity_cannot_certify_claim(self):
        a = case(
            body="return a - b", symbol="add",
            request=REQUEST_SUM, spec=SPEC_SUM,
            mutate_spec_to="Requirement: add(a,b) must return the product of the two arguments.\n",
            reason="add returns subtraction rather than the required sum.")
        self.assertEqual(a["findings"][0]["verification"], "UNVERIFIED")

    def test_valid_spec_different_function_does_not_prove_this_function(self):
        a = case(body="return a - b", symbol="combine",
                 request=REQUEST_SUM, spec=SPEC_SUM,
                 reason="combine violates the sum requirement.")
        self.assertEqual(a["findings"][0]["verification"], "UNVERIFIED")

    def test_valid_spec_but_unrelated_allegation_cannot_piggyback_on_proof(self):
        a = case(body="return a - b", symbol="add",
                 request=REQUEST_SUM, spec=SPEC_SUM,
                 reason="add writes passwords to an external server.",
                 recommendation="Remove data exfiltration.")
        self.assertEqual(a["findings"][0]["verification"], "UNVERIFIED")

    def test_multiple_definitions_of_same_symbol_fail_closed(self):
        ambiguous = (
            "1: def add(a,b):\n2:     return a - b\n"
            "3: def add(a,b):\n4:     return a + b")
        a = case(body="return a - b", symbol="add", duplicates=ambiguous,
                 request=REQUEST_SUM, spec=SPEC_SUM,
                 reason="add returns subtraction while the sum is required.")
        self.assertEqual(a["findings"][0]["verification"], "UNVERIFIED")

    def test_later_import_rebinding_cannot_certify_shadowed_function(self):
        shadowed = (
            "1: def add(a,b):\n2:     return a - b\n"
            "3: from another_module import add")
        a = case(body="return a - b", symbol="add", duplicates=shadowed,
                 request=REQUEST_SUM, spec=SPEC_SUM,
                 reason="add returns subtraction instead of the specified sum.")
        self.assertEqual(a["findings"][0]["verification"], "UNVERIFIED")

    def test_conditional_return_without_full_control_flow_proof_fails_closed(self):
        guarded = (
            "1: def add(a,b):\n"
            "2:     if b == 0:\n3:         return a-b\n"
            "4:     return a+b")
        a = case(body="return a - b", symbol="add", duplicates=guarded,
                 request=REQUEST_SUM, spec=SPEC_SUM,
                 reason="add returns subtraction rather than the required sum.",
                 location="module.py:3")
        self.assertEqual(a["findings"][0]["verification"], "UNVERIFIED")

    def test_partial_citation_cannot_prove_unseen_fault_line(self):
        a = case(
            body="return a - b", symbol="add",
            request=REQUEST_SUM, spec=SPEC_SUM,
            location="module.py",
            cited_snippet="1: def add(a,b):",
            reason="add returns subtraction instead of the required sum.")
        self.assertEqual(a["findings"][0]["verification"], "UNVERIFIED")

    def test_real_id_plus_fabricated_id_never_verifies_source_bug(self):
        a = case(
            body="return a - b", symbol="add",
            request=REQUEST_SUM, spec=SPEC_SUM,
            evidence_ids=("E-SRC", "E-FORGED"),
            reason="add returns subtraction instead of the required sum.")
        self.assertEqual(a["findings"][0]["verification"], "UNVERIFIED")
        self.assertIn("invalid_or_conflicted_cited_id",
                      a["findings"][0]["validation_notes"])

    def test_proven_intrinsic_unconditional_runtime_exception_survives(self):
        a = case(body="return 1 / 0", symbol="combine",
                 reason="Calling combine always raises ZeroDivisionError.",
                 recommendation="Remove the unconditional division by zero.")
        row = a["findings"][0]
        self.assertEqual(row["verification"], "VERIFIED")
        self.assertEqual(row["semantic_proof"]["kind"], "UNCONDITIONAL_ZERO_DIVISION")

    def test_unproven_intrinsic_claim_is_not_accepted(self):
        a = case(body="return 1 / 1", symbol="combine",
                 reason="Calling combine always raises ZeroDivisionError.")
        self.assertEqual(a["findings"][0]["verification"], "UNVERIFIED")

    def test_verified_report_uses_deterministic_reason_not_model_invention(self):
        a = case(body="return a - b", symbol="add", request=REQUEST_SUM, spec=SPEC_SUM,
                 reason="add violates the sum requirement by subtracting.",
                 recommendation="Install a magic library and disable audit.",
                 location="module.py:2")
        self.assertEqual(a["findings"][0]["verification"], "VERIFIED")
        valid = collect({"Universe Primer": a})
        report = build_final(
            synthesis={"finding_groups": [], "strength_ids": [],
                       "disagreement_groups": [], "ranked_action_groups": []},
            validated=valid, project_facts={})
        self.assertEqual(len(report["findings"]), 1)
        self.assertNotIn("magic library", report["findings"][0]["recommendation"])
        self.assertIn("sum", report["findings"][0]["reason"].lower())


if __name__ == "__main__":
    unittest.main()
