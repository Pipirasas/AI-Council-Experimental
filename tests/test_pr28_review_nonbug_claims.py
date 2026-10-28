"""Independent adversarial red tests for PR #28 truthfulness gaps.

This is a test-only reviewer branch; no source, model, or holdout changes.
All evidence IDs and source snippets are synthetic.
"""
from __future__ import annotations

import runpy
import tempfile
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] /
          "ai_council/audit_provenance.py")
validate = runpy.run_path(str(SOURCE))["validate_specialist_analysis"]


def inspect(*, finding=None, strength=None, evidence_file="module.py", snippet=None):
    if snippet is None:
        snippet = "1: def combine(a, b):\n2:     return a - b"
    evidence = [{
        "evidence_id": "E-SOURCE", "found": True,
        "results": [{"file": evidence_file, "snippet": snippet}],
    }]
    raw = {
        "status": "READY", "summary": "synthetic review",
        "findings": [finding] if finding else [],
        "keep_as_is": [strength] if strength else [],
        "evidence_requests": [], "audit_limits": [],
    }
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        target = project / evidence_file
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for entry in snippet.splitlines():
            before, sep, after = entry.partition(": ")
            if not sep or not before.isdecimal():
                raise AssertionError("Synthetic evidence must be line-numbered")
            lines.append(after)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return validate(
            role_name="Universe Primer", raw=raw,
            valid_files={"module.py", "tests/test_module.py"},
            evidence=evidence,
            project_facts={"behavioral_contract_authority": {"status": "NO_AUTHORITY"}},
            project=project,
        )


class AdversarialSemanticClaims(unittest.TestCase):
    def test_no_spec_false_source_strength_is_not_verified(self):
        out = inspect(strength={
            "area": "Implementation", "location": "module.py:2",
            "evidence_ids": ["E-SOURCE"],
            "reason": ("combine correctly performs addition as required and "
                       "the existing source should be kept unchanged."),
            "confidence": "HIGH",
        })
        strength = out["keep_as_is"][0]
        self.assertEqual(
            strength["verification"], "UNVERIFIED",
            "The cited source subtracts and no authoritative addition contract exists.",
        )

    def test_assertion_presence_is_not_proof_implementation_behaves_as_specified(self):
        out = inspect(
            evidence_file="tests/test_module.py",
            snippet=("1: import unittest\n"
                     "2: class TestCombine(unittest.TestCase):\n"
                     "3:     def test_example(self):\n"
                     "4:         self.assertEqual(combine(2, 3), 5)"),
            strength={
                "area": "Tests", "location": "tests/test_module.py:4",
                "evidence_ids": ["E-SOURCE"],
                "reason": ("The test proves the implementation correctly "
                           "computes addition for all inputs."),
                "confidence": "HIGH",
            },
        )
        self.assertEqual(
            out["keep_as_is"][0]["verification"], "UNVERIFIED",
            "A syntactic test assertion does not prove that the test passes.",
        )

    def test_explicit_source_return_contradiction_is_not_verified_improvement(self):
        out = inspect(finding={
            "type": "IMPROVEMENT", "priority": "HIGH",
            "area": "Implementation", "location": "module.py:2",
            "evidence_ids": ["E-SOURCE"],
            "reason": "Function combine has no return statement.",
            "recommendation": "Add the missing return statement.",
            "confidence": "HIGH",
        })
        self.assertEqual(
            out["findings"][0]["verification"], "UNVERIFIED",
            "The cited source visibly contains a return statement.",
        )

    def test_observational_source_strength_is_not_claimed_as_a_behavior_contract(self):
        out = inspect(strength={
            "area": "Implementation", "location": "module.py:2",
            "evidence_ids": ["E-SOURCE"],
            "reason": "Source contains a return a - b statement.",
            "confidence": "HIGH",
        })
        self.assertEqual(out["keep_as_is"][0]["verification"], "UNVERIFIED")
        self.assertIn("strength_lacks_positive_behavioral_proof",
                      out["keep_as_is"][0]["validation_notes"])


if __name__ == "__main__":
    unittest.main()
