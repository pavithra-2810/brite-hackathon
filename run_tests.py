#!/usr/bin/env python3
"""
Zero-Dependency Unit Test Runner using Python's standard unittest framework.
"""

import unittest
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from tests.test_ingestion import test_parse_manual, test_parse_amendment
from tests.test_reasoning import (
    test_calculation_award,
    test_refusal_gap,
    test_conflict_detection,
    test_day2_amendment_disregard
)


class TestPolicyEngine(unittest.TestCase):
    def test_ingestion_manual(self):
        test_parse_manual()

    def test_ingestion_amendment(self):
        test_parse_amendment()

    def test_award_calculation(self):
        test_calculation_award()

    def test_gap_refusal(self):
        test_refusal_gap()

    def test_contradiction(self):
        test_conflict_detection()

    def test_day2_amendment(self):
        test_day2_amendment_disregard()


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPolicyEngine)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
