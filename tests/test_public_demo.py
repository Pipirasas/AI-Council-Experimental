"""Public-only smoke test for offline read-only demonstration."""
from __future__ import annotations

import unittest
from examples.offline_demo import run_demo


class PublicDemoTests(unittest.TestCase):
    def test_example_is_offline_and_bounded(self):
        result = run_demo()
        self.assertEqual(result["demo"], "synthetic_offline_only")
        self.assertEqual(result["verified_with_authority"], 1)
        self.assertEqual(result["verified_without_authority"], 0)
        self.assertEqual(result["model_calls"], 0)
        self.assertFalse(result["target_code_executed"])


if __name__ == "__main__":
    unittest.main()
