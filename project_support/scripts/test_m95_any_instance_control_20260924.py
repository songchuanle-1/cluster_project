import unittest

from m95_any_instance_control_20260924 import analyze_document, analyze_rows


def row(manifest_index=0, scene_id="scene0000_00", scores=None, ious=None,
        dominant=None, deployed=0, positive=None):
    return {
        "manifest_index": manifest_index,
        "scene_id": scene_id,
        "scores": scores or [0.9, 0.8, 0.7],
        "ious": ious or [0.1, 0.9, 0.8],
        "dominant_instance": dominant or [0, 1, None],
        "deployed_query": deployed,
        "target_positive_query": positive,
    }


class AnyInstanceControlTests(unittest.TestCase):
    def test_filters_queries_without_a_dominant_instance(self):
        rows = [
            row(
                scores=[0.99, 0.8, 0.7],
                dominant=[None, 1, None],
                deployed=0,
                positive=1,
            )
        ]
        result = analyze_rows(rows, draws=100)
        self.assertEqual(result["selectors"]["any_instance"]["success_rate"], 1.0)
        self.assertEqual(result["selector_changed_rows"], 1)

    def test_detects_when_control_equals_deployed(self):
        rows = [
            row(manifest_index=0, scene_id="scene0000_00", deployed=0, positive=0),
            row(manifest_index=1, scene_id="scene0001_00", deployed=0, positive=0),
        ]
        result = analyze_rows(rows, draws=100)
        self.assertEqual(result["selector_changed_rows"], 0)
        self.assertEqual(
            result["paired_controls"]["any_instance_minus_deployed"][
                "scene_bootstrap_95ci"
            ]["point_estimate"],
            0.0,
        )

    def test_target_positive_gain_is_scene_balanced(self):
        rows = [
            row(
                manifest_index=0,
                scene_id="scene0000_00",
                scores=[0.9, 0.8],
                ious=[0.2, 0.8],
                dominant=[0, 1],
                deployed=0,
                positive=1,
            ),
            row(
                manifest_index=1,
                scene_id="scene0001_00",
                scores=[0.9, 0.7],
                ious=[0.3, 0.6],
                dominant=[0, 1],
                deployed=0,
                positive=1,
            ),
        ]
        result = analyze_rows(rows, draws=100)
        control = result["paired_controls"]["target_positive_minus_any_instance"]
        self.assertAlmostEqual(control["pooled_mean"], 0.45)
        self.assertEqual(control["scene_bootstrap_95ci"]["scene_count"], 2)
        self.assertEqual(control["scene_bootstrap_95ci"]["lo"], 0.3)

    def test_axes_must_match(self):
        bad = row()
        bad["dominant_instance"] = [0, 1]
        with self.assertRaisesRegex(ValueError, "axes differ"):
            analyze_rows([bad], draws=100)

    def test_wrong_contract_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "contract"):
            analyze_document({"contract": "wrong", "rows": [row()]}, draws=100)


if __name__ == "__main__":
    unittest.main()
