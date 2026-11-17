import unittest

import m95_negative_intrusion_partition_20260925 as diagnostic


def endpoint(instance, iou):
    return {"instance": instance, "iou": iou}


def row(
        scores,
        ious,
        positive,
        selected=0,
        seed_inside=None,
        endpoints=None,
        target_instances=(1,),
        scene="scene1",
        manifest_index=0,
):
    if seed_inside is None:
        seed_inside = [False] * len(scores)
    if endpoints is None:
        endpoints = []
    return {
        "scores": scores,
        "ious": ious,
        "native_positive": positive,
        "selected_query": selected,
        "seed_inside": seed_inside,
        "selected_mask_endpoints": {"overlaps": endpoints},
        "target_instances": list(target_instances),
        "scene": scene,
        "manifest_index": manifest_index,
    }


class NegativeIntrusionPartitionTest(unittest.TestCase):
    def test_selects_exact_native_negative_mismatch(self):
        rows = [
            row([0.9, 0.2], [0.0, 1.0], [False, True]),
            row([0.8, 0.1], [1.0, 0.0], [True, False]),
        ]
        summary = diagnostic.analyze_rows(rows, draws=20)
        self.assertEqual(summary["rows"]["native_negative_deployed_mismatches"], 1)
        self.assertEqual(summary["mismatch_rows"][0]["selected_query"], 0)

    def test_classifies_target_false_negative_before_wrong_instance(self):
        selected = row(
            [0.9, 0.2],
            [0.7, 0.0],
            [False, True],
            endpoints=[endpoint(1, 0.7), endpoint(2, 0.8)],
        )
        self.assertEqual(
            diagnostic.classify_selected(selected)["category"],
            "target_false_negative",
        )

    def test_classifies_wrong_instance_only(self):
        selected = row(
            [0.9, 0.2],
            [0.1, 0.8],
            [False, True],
            endpoints=[endpoint(1, 0.1), endpoint(2, 0.8)],
        )
        self.assertEqual(
            diagnostic.classify_selected(selected)["category"],
            "wrong_instance",
        )

    def test_classifies_neither(self):
        selected = row(
            [0.9, 0.2],
            [0.1, 0.8],
            [False, True],
            endpoints=[endpoint(1, 0.1), endpoint(2, 0.2)],
        )
        self.assertEqual(
            diagnostic.classify_selected(selected)["category"],
            "neither_target_nor_wrong_instance",
        )

    def test_score_rank_uses_deterministic_tie_convention(self):
        rows = [row([0.9, 0.9, 0.1], [0.0, 1.0, 0.0], [False, True, False])]
        summary = diagnostic.analyze_rows(rows, draws=20)
        self.assertEqual(summary["score_rank"]["median_best_positive_rank"], 2)

    def test_seed_counts_are_separate(self):
        rows = [
            row(
                [0.9, 0.2],
                [0.0, 1.0],
                [False, True],
                seed_inside=[False, True],
            )
        ]
        summary = diagnostic.analyze_rows(rows, draws=20)
        self.assertEqual(summary["seed_location"]["selected_seed_inside_target"], 0)
        self.assertEqual(
            summary["seed_location"]["best_positive_seed_inside_target"], 1
        )
        self.assertEqual(
            summary["seed_location"]["any_positive_seed_inside_target"], 1
        )

    def test_rejects_selected_query_not_score_argmax(self):
        rows = [row([0.9, 0.2], [0.0, 1.0], [False, True], selected=1)]
        with self.assertRaisesRegex(ValueError, "score argmax"):
            diagnostic.analyze_rows(rows, draws=20)

    def test_rejects_missing_positive_query(self):
        rows = [row([0.9, 0.2], [0.0, 0.0], [False, False])]
        with self.assertRaisesRegex(ValueError, "lacks a native-positive"):
            diagnostic.analyze_rows(rows, draws=20)

    def test_rejects_axis_mismatch(self):
        rows = [row([0.9, 0.2], [0.0], [False, True])]
        with self.assertRaisesRegex(ValueError, "axes differ"):
            diagnostic.analyze_rows(rows, draws=20)

    def test_bootstrap_is_deterministic(self):
        values = {"b": [1.0], "a": [0.0]}
        first = diagnostic.bootstrap_scene(values, draws=50, seed=7)
        second = diagnostic.bootstrap_scene(values, draws=50, seed=7)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
