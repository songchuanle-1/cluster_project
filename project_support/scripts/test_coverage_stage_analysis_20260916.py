import copy
import unittest

from coverage_stage_analysis_20260916 import analyze, category


def fixture():
    row = dict(scene="synthetic", object_ids=[1], ann_id=1, batch=0,
               target_sp=1, fps_target=1, sampled_target=1,
               fps_instance_target=1, sampled_instance_target=1,
               layers=[dict(best=0.8, selected=0.5, success_queries=1)])
    return dict(rows=[row], summary=dict(expressions=1, scenes=1,
                no_fps_target=0, dropped_target=0, success=0,
                recoverable=1, mask_limited=0))


class CoverageTests(unittest.TestCase):
    def test_strict_threshold_and_scene_interval(self):
        result = analyze(fixture())
        self.assertEqual(result["scene_bootstrap_percentile_95"], [1.0, 1.0])
        self.assertEqual(category(fixture()["rows"][0]), "recoverable")

    def test_duplicate_rejected(self):
        data = fixture()
        data["rows"].append(copy.deepcopy(data["rows"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            analyze(data)

    def test_inconsistent_summary(self):
        data = fixture()
        data["summary"]["expressions"] = 2
        with self.assertRaisesRegex(ValueError, "summary"):
            analyze(data)

    def test_invalid_subset(self):
        data = fixture()
        data["rows"][0]["sampled_target"] = 2
        with self.assertRaisesRegex(ValueError, "subset"):
            analyze(data)

    def test_invalid_oracle(self):
        data = fixture()
        data["rows"][0]["layers"][0]["best"] = 0.4
        with self.assertRaisesRegex(ValueError, "ordering"):
            analyze(data)

    def test_empty_capture(self):
        with self.assertRaisesRegex(ValueError, "Empty"):
            analyze(dict(rows=[]))


if __name__ == "__main__":
    unittest.main()
