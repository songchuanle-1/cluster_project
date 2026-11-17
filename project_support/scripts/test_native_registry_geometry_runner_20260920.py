import copy
import unittest

from frozen_capture_contract_20260916 import fingerprint
from native_registry_geometry_runner_20260920 import (
    RegistryDataset, capture_planned, require_expected, runner_manifest,
)
from native_geometry_runtime_20260919 import source_manifest
from referent_geometry_registry_20260919 import evaluate
from test_native_geometry_runtime_20260919 import Model
from test_referent_registry_binding_20260919 import binding_fixture


class NativeFixture:
    training = True

    def __init__(self):
        self.scene_inputs = [[dict(scene_id="unused", ann_id="99", object_id="7")],
                             [dict(scene_id="scene0", ann_id="10", object_id="1")]]
        self.accessed = []
        self.mutate_metadata = False
        self.mutate_collation = False

    def __len__(self):
        return len(self.scene_inputs)

    def transform_train(self):
        return None, None, None, [0, 1, 2, 3, 4, 5], None, None, [10, 20, 30, 40, 50, 60]

    def get_sp_label(self, *args):
        return [1.0, 1.0, 1.0, 2.0, 2.0, 2.0], {}

    def __getitem__(self, index):
        self.accessed.append(index)
        transform = self.transform_train()
        labels, _ = self.get_sp_label(transform[3], [1, 1, 1, 2, 2, 2], [4] * 6)
        metadata = self.scene_inputs[index]
        item = [None] * 16
        item[0], item[1] = [int(row["ann_id"]) for row in metadata], metadata[0]["scene_id"]
        item[5], item[6] = transform[3], [[int(row["object_id"])] for row in metadata]
        item[11], item[15] = labels, [[0.0]] * 6
        if self.mutate_metadata:
            metadata[0]["object_id"] = "88"
        return tuple(item)

    def collate_fn(self, items):
        if self.mutate_collation:
            items[0][6][0][0] = 88
        return dict(scan_ids=[x[1] for x in items],
                    ann_ids=[ann for x in items for ann in x[0]],
                    scenes_len=[len(x[0]) for x in items])


def setup():
    registry, digest, binding, *_ = binding_fixture()
    native = NativeFixture()
    wrapped = RegistryDataset(native, "synthetic-only", registry, digest, binding, "e" * 64)
    inputs = [None] * 10
    inputs[0] = {"sample_inds": [[0, 1]]}
    inputs[4], inputs[7] = [[1., 1., 1., 2., 2., 2.]], [[0, 3, 1]]
    inputs[8], inputs[9] = [[0, 0, 0], [1, 0, 0], [4, 0, 0],
                            [10, 0, 0], [11, 0, 0], [14, 0, 0]], [0, 6]
    return native, wrapped, Model(inputs), registry, digest, binding


class RegistryRunnerTest(unittest.TestCase):
    def test_original_index_export_before_collation_and_evaluation(self):
        native, wrapped, model, registry, digest, binding = setup()
        seen = []
        records = capture_planned(model, wrapped, binding, 2,
                                  lambda step, index, row: seen.append((step, index)))
        joins = wrapped.exporter.manifest()
        report = evaluate(registry, digest, records, binding, joins)
        self.assertEqual(native.accessed, [1])
        self.assertEqual(seen, [(0, 1)])
        self.assertEqual(joins["bindings"][0]["identity"]["dataset_index"], 1)
        self.assertEqual(joins["counts"], {"bound": 1, "missing_metadata": 1})
        self.assertEqual(report["overall"]["requested"], 2)
        self.assertEqual(report["overall"]["counts"]["missing_binding"], 1)
        self.assertFalse(report["native_execution_verified"])
        self.assertEqual(len(model.criterion.hooks), 1)
        self.assertNotIn("transform_train", vars(native))
        self.assertNotIn("get_sp_label", vars(native))

    def test_export_happens_before_native_collation(self):
        native, wrapped, model, _, _, binding = setup()
        original = native.collate_fn
        def collate(items):
            self.assertEqual(len(wrapped.exporter.manifest()["bindings"]), 1)
            return original(items)
        native.collate_fn = collate
        capture_planned(model, wrapped, binding, 1)

    def test_nonzero_slot_preserves_full_original_group(self):
        native, _, model, registry, _, binding = setup()
        registry["pairs"][0].update(pair_id="scene0:1:10", expression_slot=1)
        native.scene_inputs[1].insert(
            0, dict(scene_id="scene0", ann_id="77", object_id="2"))
        wrapped = RegistryDataset(native, "synthetic", registry, fingerprint(registry),
                                  binding, "e" * 64)
        model.inputs[0]["sample_inds"] *= 2
        model.inputs[4] *= 2
        model.inputs[7] *= 2
        model.inputs[8] *= 2
        model.inputs[9] = [0, 6, 12]
        records = capture_planned(model, wrapped, binding, 1)
        axes = [row["identity"] for row in records[0]["geometry"]["rows"]]
        self.assertEqual([row["expression_slot"] for row in axes], [0, 1])
        self.assertEqual([row["ann_id"] for row in axes], [77, 10])
        self.assertEqual(wrapped.exporter.manifest()["bindings"][0]["identity"],
                         axes[1])

    def test_two_item_bound_and_unprocessed_pairs_remain_in_denominator(self):
        for limit in (1, 2):
            native, _, model, registry, digest, binding = setup()
            pair = registry["pairs"][1]
            native.scene_inputs.append([dict(scene_id=pair["scene"],
                ann_id=str(pair["ann_id"]), object_id=str(pair["target_object_id"]))])
            wrapped = RegistryDataset(native, "synthetic", registry, digest, binding, "e" * 64)
            steps = []
            records = capture_planned(model, wrapped, binding, limit,
                                      lambda step, index, row: steps.append((step, index)))
            self.assertEqual(steps, [(0, 1), (1, 2)][:limit])
            joins = wrapped.exporter.manifest()
            self.assertEqual(joins["counts"].get("missing_capture", 0), 2 - limit)
            report = evaluate(registry, digest, records, binding, joins)
            self.assertEqual(report["overall"]["requested"], 2)
            self.assertEqual(report["overall"]["counts"]["missing_binding"], 2 - limit)

    def test_reject_unplanned_bool_negative_and_repeat_indices(self):
        for index in (0, True, -1, 2):
            native, wrapped, *_ = setup()
            with self.subTest(index=index), self.assertRaises(ValueError):
                wrapped[index]
            self.assertEqual(native.accessed, [])
        _, wrapped, *_ = setup()
        wrapped[1]
        with self.assertRaises(ValueError):
            wrapped[1]

    def test_metadata_mutation_before_observation_prevents_dataset_call(self):
        native, wrapped, *_ = setup()
        native.scene_inputs[1][0]["object_id"] = "9"
        with self.assertRaisesRegex(ValueError, "before"):
            wrapped[1]
        self.assertEqual(native.accessed, [])
        self.assertTrue(wrapped.failed)

    def test_mutation_during_observation_fails_without_export_and_restores_hooks(self):
        native, wrapped, *_ = setup()
        native.mutate_metadata = True
        with self.assertRaisesRegex(ValueError, "during"):
            wrapped[1]
        self.assertEqual(wrapped.exporter.manifest()["bindings"], [])
        self.assertNotIn("transform_train", vars(native))
        self.assertNotIn("get_sp_label", vars(native))
        with self.assertRaisesRegex(ValueError, "cannot be resumed"):
            wrapped[1]

    def test_collation_mutation_prevents_model_capture(self):
        native, wrapped, model, _, _, binding = setup()
        native.mutate_collation = True
        with self.assertRaisesRegex(ValueError, "Collation mutated"):
            capture_planned(model, wrapped, binding, 1)
        self.assertTrue(wrapped.failed)
        self.assertEqual(len(model.criterion.hooks), 1)

    def test_empty_or_ambiguous_plan_does_not_access_native_items(self):
        for duplicate in (False, True):
            native, _, _, registry, digest, binding = setup()
            if duplicate:
                native.scene_inputs.append(copy.deepcopy(native.scene_inputs[1]))
            else:
                native.scene_inputs[1][0]["object_id"] = "9"
            wrapped = RegistryDataset(native, "synthetic", registry, digest, binding, "e" * 64)
            with self.assertRaisesRegex(ValueError, "unambiguous"):
                capture_planned(None, wrapped, binding, 1)
            self.assertEqual(native.accessed, [])
            self.assertEqual(wrapped.exporter.manifest()["requested"], 2)

    def test_limits_and_reuse_fail_closed(self):
        for limit in (0, 3, True, 1.0):
            native, wrapped, model, _, _, binding = setup()
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                capture_planned(model, wrapped, binding, limit)
            self.assertEqual(native.accessed, [])
        _, wrapped, model, _, _, binding = setup()
        capture_planned(model, wrapped, binding, 1)
        with self.assertRaisesRegex(ValueError, "fresh"):
            capture_planned(model, wrapped, binding, 1)

    def test_forward_and_sink_failure_poison_capture(self):
        for failure in ("forward", "sink"):
            _, wrapped, model, _, _, binding = setup()
            if failure == "forward":
                model.behavior = "raise"
            def sink(*args):
                raise RuntimeError("synthetic persistence failure")
            with self.subTest(failure=failure), self.assertRaises(RuntimeError):
                capture_planned(model, wrapped, binding, 1,
                                sink if failure == "sink" else None)
            self.assertTrue(wrapped.failed)
            self.assertEqual(len(model.criterion.hooks), 1)

    def test_sink_cannot_mutate_returned_capture(self):
        _, wrapped, model, _, _, binding = setup()
        records = capture_planned(model, wrapped, binding, 1,
                                  lambda step, index, row: row["geometry"]["rows"].clear())
        self.assertEqual(len(records[0]["geometry"]["rows"]), 1)

    def test_train_only(self):
        native, _, _, registry, digest, binding = setup()
        native.training = False
        with self.assertRaisesRegex(ValueError, "TRAIN"):
            RegistryDataset(native, "synthetic", registry, digest, binding, "e" * 64)

    def test_expected_binding_requires_exact_keys_and_values(self):
        require_expected({"a": "1"}, {"a": "1"})
        for actual in ({}, {"a": "2"}, {"a": "1", "b": "1"}):
            with self.assertRaises(ValueError):
                require_expected({"a": "1"}, actual)

    def test_separate_manifest_covers_binding_evaluator_and_frozen_producer(self):
        original = source_manifest()
        manifest = runner_manifest()
        names = {row["path"] for row in manifest["sources"]}
        self.assertTrue({row["path"] for row in original["sources"]}.issubset(names))
        self.assertTrue({"referent_registry_binding_20260919.py",
                         "referent_geometry_registry_20260919.py",
                         "native_registry_geometry_runner_20260920.py"}.issubset(names))
        self.assertEqual(manifest["producer_sha256"], fingerprint(manifest["sources"]))
        self.assertNotEqual(manifest["producer_sha256"], original["producer_sha256"])
        self.assertEqual(source_manifest(), original)


if __name__ == "__main__":
    unittest.main()
