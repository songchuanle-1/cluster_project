import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
from m95_same_forward_control_correction_20260922 import corrected_anyseed


class CorrectedAnyseedTest(unittest.TestCase):
    def test_available_success_is_preserved(self):
        result = corrected_anyseed({
            "anyseed_available": True,
            "anyseed_success": True,
            "anyseed_iou": 0.75,
            "anyseed_query": 3,
        })
        self.assertEqual(result, (True, 0.75, 3, False))

    def test_unavailable_does_not_fall_back(self):
        result = corrected_anyseed({
            "anyseed_available": False,
            "anyseed_success": True,
            "anyseed_iou": 1.0,
            "anyseed_query": 0,
        })
        self.assertEqual(result, (False, None, None, True))

    def test_unavailable_with_original_failure_still_marks_fallback(self):
        result = corrected_anyseed({
            "anyseed_available": False,
            "anyseed_success": False,
            "anyseed_iou": 0.1,
            "anyseed_query": 2,
        })
        self.assertEqual(result, (False, None, None, True))


if __name__ == "__main__":
    unittest.main()
