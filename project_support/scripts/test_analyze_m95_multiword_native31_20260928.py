"""CPU-only contracts for pre-registered grouped native outcome analysis."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "native31_analysis", ROOT / "scripts/analyze_m95_multiword_native31_20260928.py")
ANALYSIS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYSIS)
MANIFEST = json.loads(
    (ROOT / "pipeline/reports/m95_multiword_capture_manifest_20260928.json")
    .read_text(encoding="utf-8"))


class GroupedDiagnosisTest(unittest.TestCase):
    def fixture(self):
        capture = {
            "contract": "m95_multiword_native_31_v1",
            "manifest_sha256": ANALYSIS.MANIFEST_SHA,
            "checkpoint_sha256": ANALYSIS.CHECKPOINT_SHA,
            "rows": [
                {"scene": r["scene"], "ann_id": r["ann_id"], "arm": r["arm"],
                 "target_instances": r["target_instances"],
                 "selected_mask_iou": 0.75 if r["arm"] == "phrase" else 0.25,
                 "seed_majority_matches_target": r["arm"] == "phrase"}
                for r in MANIFEST["records"]],
        }
        return capture

    def test_grouping_does_not_treat_reused_controls_as_independent(self):
        result = ANALYSIS.summarize(MANIFEST, self.fixture())
        self.assertEqual((result["native_rows"], result["scene_target_units"]), (31, 7))
        self.assertEqual(sum(r["exposed_count"] for r in result["units"]), 11)
        self.assertEqual(len(result["scenes"]), 2)
        self.assertTrue(all(r["mask_iou_delta"] == 0.5 for r in result["units"]))
        self.assertTrue(all(r["seed_agreement_delta"] == 1 for r in result["units"]))

    def test_missing_or_duplicate_capture_rejected(self):
        capture = self.fixture()
        capture["rows"].pop()
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            ANALYSIS.summarize(MANIFEST, capture)
        capture = self.fixture()
        capture["rows"].append(dict(capture["rows"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            ANALYSIS.summarize(MANIFEST, capture)

    def test_wrong_target_checkpoint_or_nonfinite_rejected(self):
        capture = self.fixture()
        capture["checkpoint_sha256"] = "bad"
        with self.assertRaisesRegex(ValueError, "identity"):
            ANALYSIS.summarize(MANIFEST, capture)
        capture = self.fixture()
        capture["rows"][0]["target_instances"] = [-100]
        with self.assertRaisesRegex(ValueError, "target"):
            ANALYSIS.summarize(MANIFEST, capture)
        capture = self.fixture()
        capture["rows"][0]["selected_mask_iou"] = float("nan")
        with self.assertRaisesRegex(ValueError, "IoU"):
            ANALYSIS.summarize(MANIFEST, capture)


if __name__ == "__main__":
    unittest.main()
