import copy
import unittest

from frozen_capture_contract_20260916 import fingerprint
from referent_geometry_capture_20260919 import capture_batch
from referent_geometry_registry_20260919 import evaluate
from referent_registry_binding_20260919 import BindingExporter, plan_bindings
from test_referent_geometry_capture_20260919 import fixture
from test_referent_geometry_registry_20260919 import setup


def binding_fixture():
    registry, digest, _, binding, _ = setup()
    inputs, axes, _ = fixture()
    metadata, items = [], []
    for index, axis in enumerate(axes):
        target = 1 if index == 0 else 3
        metadata.append([dict(scene_id=axis["scene"], ann_id=str(axis["ann_id"]),
                              object_id=str(target))])
        item = [None] * 16
        item[0], item[1] = [axis["ann_id"]], axis["scene"]
        item[5], item[6] = axis["sample_inverse"][:], [[target]]
        item[11] = [float(x) for x in axis["physical_instance_labels"]]
        item[15] = [[0.0] for _ in item[11]]
        item = tuple(item)
        axis["native_input_sha256"] = fingerprint(item)
        items.append(item)
    exporter = BindingExporter(registry, digest, metadata, binding, "e" * 64)
    return registry, digest, binding, inputs, axes, metadata, items, exporter


class BindingTest(unittest.TestCase):
    def test_roundtrip_into_geometry_registry(self):
        registry, digest, binding, inputs, axes, _, items, exporter = binding_fixture()
        for index, item in enumerate(items):
            exporter.export_item(index, item, [axes[index]])
        manifest = exporter.manifest()
        capture = capture_batch(inputs, axes, binding)
        report = evaluate(registry, digest, [capture], binding, manifest)
        self.assertEqual(manifest["counts"], {"bound": 2})
        self.assertEqual(report["overall"]["counts"]["valid"], 1)
        self.assertEqual(report["overall"]["counts"]["missing_geometry"], 1)
        self.assertEqual(manifest["bindings"][1]["control_support_count"], 0)
        self.assertFalse(manifest["native_execution_verified"])

    def test_metadata_target_prevents_scene_ann_only_match(self):
        registry, digest, _, _, _, metadata, _, _ = binding_fixture()
        metadata[0][0]["object_id"] = "55"
        plan = plan_bindings(registry, digest, metadata)
        self.assertEqual(plan["counts"]["missing_metadata"], 1)

    def test_duplicate_native_metadata_is_ambiguous_not_first_match(self):
        registry, digest, _, _, _, metadata, _, _ = binding_fixture()
        metadata.append(copy.deepcopy(metadata[0]))
        plan = plan_bindings(registry, digest, metadata)
        self.assertEqual(plan["rows"][0]["status"], "ambiguous_metadata")
        self.assertEqual(plan["rows"][0]["dataset_indices"], [0, 2])

    def test_missing_metadata_retains_every_pair(self):
        registry, digest, *_ = binding_fixture()
        self.assertEqual(plan_bindings(registry, digest, [])["counts"],
                         {"missing_metadata": 2})

    def test_metadata_plan_does_not_claim_physical_capture(self):
        *_, exporter = binding_fixture()
        manifest = exporter.manifest()
        self.assertEqual(manifest["counts"], {"missing_capture": 2})
        self.assertEqual(manifest["bindings"], [])

    def test_malformed_metadata_rejected(self):
        for change in (dict(ann_id=True), dict(object_id="01"),
                       dict(object_ids=[1, 2]), dict(object_ids=[7]),
                       dict(scene_id="")):
            registry, digest, _, _, _, metadata, _, _ = binding_fixture()
            metadata[0][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                plan_bindings(registry, digest, metadata)

    def test_mixed_scene_group_rejected(self):
        registry, digest, _, _, _, metadata, _, _ = binding_fixture()
        metadata[0].extend(metadata[1])
        with self.assertRaisesRegex(ValueError, "Mixed"):
            plan_bindings(registry, digest, metadata)

    def test_wrong_target_native_item_rejected_even_with_new_hash(self):
        _, _, _, _, axes, _, items, exporter = binding_fixture()
        items[0][6][0][0] = 9
        axes[0]["native_input_sha256"] = fingerprint(items[0])
        with self.assertRaisesRegex(ValueError, "target"):
            exporter.export_item(0, items[0], [axes[0]])

    def test_wrong_axis_identity_rejected(self):
        for field, value in (("dataset_index", 1), ("expression_slot", 1),
                             ("ann_id", 12), ("scene", "wrong"),
                             ("native_input_sha256", "f" * 64),
                             ("checkpoint_sha256", "f" * 64),
                             ("producer_sha256", "f" * 64)):
            _, _, _, _, axes, _, items, exporter = binding_fixture()
            axes[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                exporter.export_item(0, items[0], [axes[0]])
            self.assertEqual(exporter.manifest()["bindings"], [])

    def test_physical_support_mismatch_rejected(self):
        for field, value in (("sample_inverse", [0, 0, 1, 2, 3, 4, 5]),
                             ("physical_instance_labels", [1] * 6)):
            _, _, _, _, axes, _, items, exporter = binding_fixture()
            axes[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                exporter.export_item(0, items[0], [axes[0]])

    def test_lossy_native_labels_rejected(self):
        _, _, _, _, axes, _, items, exporter = binding_fixture()
        items[0][11][0] = 1.5
        axes[0]["native_input_sha256"] = fingerprint(items[0])
        with self.assertRaisesRegex(ValueError, "integral"):
            exporter.export_item(0, items[0], [axes[0]])

    def test_duplicate_observation_rejected(self):
        _, _, _, _, axes, _, items, exporter = binding_fixture()
        exporter.export_item(0, items[0], [axes[0]])
        with self.assertRaisesRegex(ValueError, "occurrence"):
            exporter.export_item(0, items[0], [axes[0]])
        axes[0]["scene_occurrence"] = 3
        with self.assertRaisesRegex(ValueError, "Repeated"):
            exporter.export_item(0, items[0], [axes[0]])

    def test_missing_axes_and_boolean_target_rejected(self):
        _, _, _, _, axes, _, items, exporter = binding_fixture()
        with self.assertRaises(ValueError):
            exporter.export_item(0, items[0], [])
        items[0][6][0][0] = True
        axes[0]["native_input_sha256"] = fingerprint(items[0])
        with self.assertRaises(ValueError):
            exporter.export_item(0, items[0], [axes[0]])

    def test_nonzero_slot_is_not_remapped(self):
        registry, digest, binding, inputs, axes, metadata, items, _ = binding_fixture()
        metadata[0].insert(0, dict(scene_id="scene0", ann_id="99", object_id="2"))
        plan = plan_bindings(registry, digest, metadata)
        self.assertEqual(plan["rows"][0]["status"], "missing_metadata")

    def test_inputs_and_return_values_do_not_alias_state(self):
        _, _, _, _, axes, metadata, items, exporter = binding_fixture()
        before = copy.deepcopy((axes, items))
        result = exporter.export_item(0, items[0], [axes[0]])
        self.assertEqual((axes, items), before)
        baseline = exporter.manifest()
        metadata[0][0]["object_id"] = "9"
        result[0]["identity"]["ann_id"] = 55
        baseline["bindings"][0]["physical_instance_labels"][0] = 55
        self.assertEqual(exporter.manifest()["bindings"][0]["identity"]["ann_id"], 10)
        self.assertEqual(exporter.manifest()["bindings"][0]["physical_instance_labels"][0], 1)

    def test_source_hash_and_index_fail_closed(self):
        registry, digest, binding, _, axes, metadata, items, exporter = binding_fixture()
        with self.assertRaises(ValueError):
            BindingExporter(registry, digest, metadata, binding, "invalid")
        for index in (True, -1, 0.0, 2):
            with self.subTest(index=index), self.assertRaises(ValueError):
                exporter.export_item(index, items[0], [axes[0]])

    def test_multiple_expressions_and_atomic_failure(self):
        registry, digest, binding, _, axes, metadata, items, _ = binding_fixture()
        pair = dict(registry["pairs"][0], pair_id="scene0:1:99",
                    expression_slot=1, ann_id="99")
        registry["pairs"].append(pair)
        metadata[0].append(dict(scene_id="scene0", ann_id="99", object_id="1"))
        items[0][0].append(99)
        items[0][6].append([1])
        axes[0]["native_input_sha256"] = fingerprint(items[0])
        second = dict(axes[0], expression_slot=1, ann_id=99)
        exporter = BindingExporter(registry, fingerprint(registry), metadata,
                                   binding, "e" * 64)
        second["scene_occurrence"] = 55
        with self.assertRaisesRegex(ValueError, "Inconsistent"):
            exporter.export_item(0, items[0], [axes[0], second])
        self.assertEqual(exporter.manifest()["bindings"], [])
        self.assertEqual(exporter.observations, set())
        second["scene_occurrence"] = axes[0]["scene_occurrence"]
        result = exporter.export_item(0, items[0], [axes[0], second])
        self.assertEqual([r["identity"]["expression_slot"] for r in result], [0, 1])

    def test_native_sentinel_and_real_199_remain_distinct(self):
        for actual in (-1, 199):
            _, _, _, _, axes, _, items, exporter = binding_fixture()
            items[0][11][0] = 199.0
            axes[0]["physical_instance_labels"][0] = actual
            axes[0]["native_input_sha256"] = fingerprint(items[0])
            row = exporter.export_item(0, items[0], [axes[0]])[0]
            self.assertEqual(row["physical_instance_labels"][0], actual)
            self.assertEqual(row["target_support_count"], 2)

    def test_scene_occurrence_collision_across_dataset_items(self):
        _, _, _, _, axes, _, items, exporter = binding_fixture()
        exporter.export_item(0, items[0], [axes[0]])
        axes[1]["scene_occurrence"] = axes[0]["scene_occurrence"]
        with self.assertRaisesRegex(ValueError, "occurrence"):
            exporter.export_item(1, items[1], [axes[1]])
        self.assertEqual(exporter.manifest()["counts"],
                         {"bound": 1, "missing_capture": 1})

    def test_ambiguous_plan_cannot_export_a_chosen_match(self):
        registry, digest, binding, _, axes, metadata, items, _ = binding_fixture()
        metadata.append(copy.deepcopy(metadata[0]))
        exporter = BindingExporter(registry, digest, metadata, binding, "e" * 64)
        self.assertEqual(exporter.export_item(0, items[0], [axes[0]]), [])
        self.assertEqual(exporter.manifest()["counts"]["ambiguous_metadata"], 1)


if __name__ == "__main__":
    unittest.main()
