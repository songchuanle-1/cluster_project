import unittest
from pathlib import Path
from paired_metric_audit_20260916 import audit


class MetricAuditTest(unittest.TestCase):
    def test_archived_identity_and_denominators(self):
        report = audit(Path(__file__).resolve().parents[1])
        self.assertTrue(report["native_get_iou_ast_identical"])
        self.assertEqual(report["counts"]["baseline"]["expressions"], 123)
        self.assertEqual(report["counts"]["champion"]["selected_gt_half"], 85)
        self.assertEqual(report["counts"]["baseline"]["selected_gt_half"], 87)

    def test_epsilon_bound(self):
        for union in (1, 2, 10, 10000):
            for intersection in (0, union // 2, union):
                delta = intersection / union - intersection / (union + 1e-6)
                self.assertGreaterEqual(delta, 0)
                self.assertLessEqual(delta, 1e-6)

    def test_half_is_not_strict_success(self):
        self.assertFalse(.5 > .5)
        self.assertTrue(.5 >= .5)
        self.assertLess(1 / (2 + 1e-6), .5)


if __name__ == "__main__":
    unittest.main()
