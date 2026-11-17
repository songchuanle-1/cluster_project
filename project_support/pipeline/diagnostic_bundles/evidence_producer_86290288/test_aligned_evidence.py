"""CPU software controls only; these fixtures do not measure model efficacy."""
import copy
import json
from pathlib import Path
import unittest

import numpy as np

from aligned_evidence import EvidenceError, align_pairs, export_prediction, native_mean


def fixture():
    batch = {"scan_ids": ["scene0000_00"], "scenes_len": [3],
             "object_idss": [[5], [5], [6]], "ann_ids": [0, 1, 0]}
    prediction = {"scan_id": ["scene0000_00"] * 3, "object_ids": [[5], [5], [6]],
                  "ann_id": [0, 1, 0], "piou": list(np.asarray([0.1, 0.4, 0.8], dtype=np.float32))}
    return batch, prediction


class AlignmentTests(unittest.TestCase):
    def test_native_values_order_aggregation_and_readonly(self):
        batch, prediction = fixture()
        before = copy.deepcopy(prediction)
        records, aggregate = export_prediction(prediction, batch, "train")
        self.assertEqual(aggregate, float(np.asarray(prediction["piou"]).mean()))
        self.assertEqual([row["piou"] for row in records],
                         [float(value) for value in prediction["piou"]])
        self.assertEqual(prediction, before)
        self.assertEqual(len(records), 3)

    def test_reordered_pairs_use_full_identity(self):
        batch, prediction = fixture()
        records, _ = export_prediction(prediction, batch, "train")
        pairs = align_pairs(records, list(reversed(copy.deepcopy(records))))
        self.assertTrue(all(left == right for left, right in pairs))

    def test_json_round_trip_exact(self):
        batch, prediction = fixture()
        records, aggregate = export_prediction(prediction, batch, "train")
        restored = json.loads(json.dumps(records, allow_nan=False))
        self.assertEqual(align_pairs(records, restored), list(zip(records, records)))
        self.assertEqual(native_mean([row["piou"] for row in restored]), aggregate)

    def test_duplicate_input(self):
        batch, prediction = fixture()
        batch["ann_ids"][1] = 0
        with self.assertRaises(EvidenceError):
            export_prediction(prediction, batch, "train")

    def test_duplicate_persisted(self):
        batch, prediction = fixture()
        records, _ = export_prediction(prediction, batch, "train")
        with self.assertRaises(EvidenceError):
            align_pairs(records, records + [records[0]])

    def test_missing_member(self):
        batch, prediction = fixture()
        records, _ = export_prediction(prediction, batch, "train")
        with self.assertRaises(EvidenceError):
            align_pairs(records, records[:-1])

    def test_conflicting_object_scene_split_annotation(self):
        batch, prediction = fixture()
        records, _ = export_prediction(prediction, batch, "train")
        for field, value in (("object_ids", [99]), ("scene_id", "scene9999_00"),
                             ("split", "val"), ("ann_id", 999)):
            altered = copy.deepcopy(records)
            altered[0][field] = value
            with self.subTest(field=field), self.assertRaises(EvidenceError):
                align_pairs(records, altered)

    def test_prediction_input_mispair(self):
        batch, prediction = fixture()
        prediction["ann_id"] = [1, 0, 0]
        with self.assertRaises(EvidenceError):
            export_prediction(prediction, batch, "train")

    def test_lengths_fail(self):
        for field in ("scan_id", "object_ids", "ann_id", "piou"):
            batch, prediction = fixture()
            prediction[field].pop()
            with self.subTest(field=field), self.assertRaises(EvidenceError):
                export_prediction(prediction, batch, "train")

    def test_nonfinite_outofrange_and_precision_fail(self):
        for value in (float("nan"), float("inf"), -0.1, 1.1, 0.1):
            batch, prediction = fixture()
            prediction["piou"][0] = value
            with self.subTest(value=value), self.assertRaises(EvidenceError):
                export_prediction(prediction, batch, "train")

    def test_multiple_scene_batch_fail(self):
        batch, prediction = fixture()
        batch["scan_ids"] = ["scene0000_00", "scene0001_00"]
        batch["scenes_len"] = [2, 1]
        with self.assertRaises(EvidenceError):
            export_prediction(prediction, batch, "train")

    def test_empty_and_invalid_identity_fail(self):
        for field, value in (("object_ids", []), ("object_ids", [5, 5]),
                             ("ann_id", -1), ("ann_id", True), ("scene_id", "")):
            batch, prediction = fixture()
            records, _ = export_prediction(prediction, batch, "train")
            records[0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(EvidenceError):
                align_pairs(records, records)

    def test_float32_not_float64_aggregate(self):
        values = np.asarray([0.1, 0.4, 0.8], dtype=np.float32)
        self.assertEqual(native_mean(values), float(values.mean()))
        self.assertNotEqual(native_mean(values), float(values.astype(np.float64).mean()))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AlignmentTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    output = {"tests_run": result.testsRun, "passed": result.wasSuccessful(),
              "failures": [text for _, text in result.failures],
              "errors": [text for _, text in result.errors],
              "scope": "CPU identity/export controls; synthetic fixtures, not scientific efficacy"}
    Path(__file__).with_name("cpu_controls.json").write_text(
        json.dumps(output, indent=2, allow_nan=False), encoding="utf-8")
    raise SystemExit(not result.wasSuccessful())
