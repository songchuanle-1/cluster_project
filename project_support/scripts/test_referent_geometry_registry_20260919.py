import copy
import unittest

from frozen_capture_contract_20260916 import fingerprint
from referent_geometry_capture_20260919 import capture_batch
from referent_geometry_registry_20260919 import evaluate
from native_geometry_runtime_20260919 import capture_forward
from test_native_geometry_runtime_20260919 import setup as runtime_setup
from test_referent_geometry_capture_20260919 import fixture


def setup():
    inputs, axes, binding = fixture()
    capture = capture_batch(inputs, axes, binding)
    pairs = []
    for i in range(2):
        pairs.append(dict(
            pair_id="scene%d:0:%d" % (i, 10 + i), scene="scene%d" % i,
            expression_slot=0, ann_id=str(10 + i),
            target_object_id=str(1 if i == 0 else 3),
            observed_control_object_id=str(2 if i == 0 else 4),
            primary_same_class_pair_eligible=True,
            same_class_control_pool=[str(2 if i == 0 else 4)]))
    registry = dict(pairs=pairs)
    digest = fingerprint(registry)
    joins = dict(registry_sha256=digest, bindings=[
        dict(pair_id=p["pair_id"], identity=copy.deepcopy(r["identity"]))
        for p, r in zip(pairs, capture["rows"])])
    return registry, digest, [capture], binding, joins


class RegistryTest(unittest.TestCase):
    def test_valid_missing_and_scene_denominators(self):
        report = evaluate(*setup())
        self.assertEqual(report["overall"]["requested"], 2)
        self.assertEqual(report["overall"]["counts"]["valid"], 1)
        self.assertEqual(report["overall"]["counts"]["missing_geometry"], 1)
        self.assertEqual(report["scene_balanced_status_fractions"]["valid"], .5)
        self.assertFalse(report["native_execution_verified"])

    def test_no_bindings_never_guesses_scene_annotation_join(self):
        args = setup()
        args[4]["bindings"] = []
        report = evaluate(*args)
        self.assertEqual(report["overall"]["counts"]["missing_binding"], 2)
        self.assertEqual(report["unmatched_sidecar_rows"], 2)

    def test_no_capture_retains_registry_denominator(self):
        args = setup()
        args[2].clear()
        report = evaluate(*args)
        self.assertEqual(report["overall"]["counts"]["missing_capture"], 2)
        self.assertEqual(report["selection_sensitivity"]["captured_pairs"], 0)

    def test_absent_binding_allowed_only_without_captures(self):
        args = list(setup())
        args[3] = None
        with self.assertRaises(ValueError):
            evaluate(*args)
        args[2].clear()
        self.assertIsNone(evaluate(*args)["source_binding"])

    def test_physical_input_hash_mismatch_is_missing_not_weak_join(self):
        args = setup()
        args[4]["bindings"][0]["identity"]["native_input_sha256"] = "f" * 64
        report = evaluate(*args)
        self.assertEqual(report["overall"]["counts"]["missing_capture"], 1)

    def test_wrong_registry_or_source_rejected(self):
        for kind in ("registry", "source"):
            args = setup()
            if kind == "registry":
                args[4]["registry_sha256"] = "f" * 64
            else:
                args[3]["checkpoint_sha256"] = "f" * 64
            with self.assertRaises(ValueError):
                evaluate(*args)

    def test_duplicate_pair_binding_or_capture_rejected(self):
        for kind in ("pair", "binding", "capture"):
            args = setup()
            target = (args[0]["pairs"] if kind == "pair" else
                      args[4]["bindings"] if kind == "binding" else args[2])
            target.append(copy.deepcopy(target[0]))
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                evaluate(*args)

    def test_noncanonical_ids_rejected(self):
        for bad in (True, 1.0, "01", "-1", "1.0"):
            args = setup()
            args[0]["pairs"][0]["target_object_id"] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                evaluate(*args)

    def test_mismatched_join_identity_rejected(self):
        args = setup()
        args[4]["bindings"][0]["identity"]["ann_id"] = 50
        with self.assertRaises(ValueError):
            evaluate(*args)

    def test_excluded_cross_class_pair_not_in_primary(self):
        args = setup()
        args[0]["pairs"][1]["primary_same_class_pair_eligible"] = False
        args[4]["bindings"].pop()
        report = evaluate(*args)
        self.assertEqual(report["overall"]["requested"], 1)
        self.assertEqual(report["unmatched_sidecar_rows"], 1)

    def test_selection_sensitivity_retains_loss_of_coverage(self):
        args = setup()
        inputs, axes, binding = fixture()
        inputs[0]["sample_inds"][0] = [1, 1]
        args[2][0] = capture_batch(inputs, axes, binding)
        report = evaluate(*args)
        row = report["pairs"][0]
        self.assertEqual(row["status"], "missing_geometry")
        self.assertEqual(row["fps_reference"]["status"], "valid")
        self.assertTrue(row["selection_status_changed"])

    def test_exact_and_near_ties_are_separate(self):
        for delta, state in ((0., "tied"), (1e-10, "valid")):
            args = setup()
            inputs, axes, binding = fixture()
            inputs[8][:6] = [[0, 0, 0], [1, 0, 0], [4, 0, 0],
                              [10, 0, 0], [11, 0, 0], [14 + delta, 0, 0]]
            if delta == 0:
                inputs[8][:6] = [[i, 0, 0] for i in range(6)]
            inputs[0]["sample_inds"][0] = [1, 2]
            args[2][0] = capture_batch(inputs, axes, binding)
            row = evaluate(*args)["pairs"][0]
            self.assertEqual(row["status"], state)
            self.assertTrue(row["near_tie"])

    def test_selection_order_reversal_is_reported_not_independence(self):
        args = setup()
        inputs, axes, binding = fixture()
        inputs[8][3:6] = [[10, 0, 0], [12, 0, 0], [13, 0, 0]]
        inputs[7][0] = [1, 3, 4]
        inputs[0]["sample_inds"][0] = [0, 1]
        args[2][0] = capture_batch(inputs, axes, binding)
        report = evaluate(*args)
        self.assertTrue(report["pairs"][0]["selection_order_changed"])
        self.assertEqual(report["selection_sensitivity"]["order_changed"], 1)
        self.assertFalse(report["independent_objectness_resolved"])

    def test_per_scene_denominators_include_missing_bindings(self):
        args = setup()
        extra = dict(args[0]["pairs"][0], pair_id="scene0:1:12",
                     expression_slot=1, ann_id="12")
        args[0]["pairs"].append(extra)
        report = evaluate(*args)
        self.assertEqual(report["per_scene"]["scene0"]["requested"], 2)
        self.assertEqual(report["scene_balanced_status_fractions"]["valid"], .25)

    def test_inputs_unchanged(self):
        args = setup()
        before = copy.deepcopy(args)
        evaluate(*args)
        self.assertEqual(args, before)

    def test_runtime_envelope_joins_without_rewriting_sidecar(self):
        args = setup()
        args[2][0] = capture_forward(*runtime_setup())
        self.assertEqual(evaluate(*args)["overall"]["counts"]["valid"], 1)

    def test_tampered_runtime_envelope_rejected(self):
        args = setup()
        args[2][0] = capture_forward(*runtime_setup())
        args[2][0]["loss"] += 1
        with self.assertRaisesRegex(ValueError, "hash"):
            evaluate(*args)


if __name__ == "__main__":
    unittest.main()
