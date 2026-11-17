import copy
import inspect
import itertools
import unittest

from referent_geometry_control_20260919 import geometry_control, validate_contrast
from referent_object_rank_capture_20260919 import build_capture
from test_referent_native_expression_producer_20260919 import (
    binding_fixture, capture_fixture, registry_fixture,
)
from referent_native_expression_producer_20260919 import produce_expression_inputs


def fixture():
    return (
        [[0., 0., 0.], [1., 0., 0.], [4., 0., 0.],
         [10., 0., 0.], [11., 0., 0.], [12., 0., 0.]],
        [1, 1, 1, 2, 2, 2],
        [0, 4],
    )


class GeometryControlTest(unittest.TestCase):
    def test_closed_form(self):
        result = geometry_control(*fixture())
        self.assertAlmostEqual(result["query_costs"][0], 25 / 26)
        self.assertEqual(result["query_costs"][1], 0)
        self.assertEqual(validate_contrast(result, [1, 2]), result["query_costs"])

    def test_full_support_field_has_mean_one_per_nondegenerate_object(self):
        result = geometry_control(*fixture())
        for indices in ([0, 1, 2], [3, 4, 5]):
            self.assertAlmostEqual(sum(result["support_costs"][i] for i in indices), 3)

    def test_target_swap_preserves_physical_scores(self):
        inputs = fixture()
        before = geometry_control(*inputs)
        original = copy.deepcopy(before)
        a = validate_contrast(before, [1, 2])
        b = validate_contrast(before, [2, 1])
        self.assertEqual(a, b[::-1])
        self.assertEqual(before, original)
        self.assertEqual(geometry_control(*inputs), original)
        self.assertEqual(
            list(inspect.signature(geometry_control).parameters),
            ["coordinates", "instance_labels", "query_seed_indices"],
        )
        with self.assertRaises(TypeError):
            geometry_control(*inputs, target=1)

    def test_support_permutations(self):
        coordinates, labels, seeds = fixture()
        reference = geometry_control(*fixture())["object_costs"]
        for permutation in itertools.permutations(range(6)):
            inverse = {old: new for new, old in enumerate(permutation)}
            result = geometry_control(
                [coordinates[i] for i in permutation],
                [labels[i] for i in permutation],
                [inverse[i] for i in seeds],
            )
            for key, value in reference.items():
                self.assertAlmostEqual(result["object_costs"][key], value)

    def test_seed_order_and_duplicates(self):
        coordinates, labels, seeds = fixture()
        reference = geometry_control(coordinates, labels, seeds)
        result = geometry_control(coordinates, labels, [4, 0, 4])
        self.assertEqual(result["object_costs"], reference["object_costs"])
        self.assertEqual(result["query_costs"],
                         [reference["query_costs"][1], reference["query_costs"][0],
                          reference["query_costs"][1]])

    def test_similarity_transform(self):
        coordinates, labels, seeds = fixture()
        transformed = [[7 - 3*y, -5 + 3*x, 2 + 3*z] for x, y, z in coordinates]
        result = geometry_control(transformed, labels, seeds)
        reference = geometry_control(coordinates, labels, seeds)
        for key, value in reference["object_costs"].items():
            self.assertAlmostEqual(result["object_costs"][key], value)

    def test_instance_id_renaming(self):
        coordinates, labels, seeds = fixture()
        result = geometry_control(coordinates, [11 if x == 1 else 20 for x in labels], seeds)
        self.assertEqual(result["query_costs"], geometry_control(*fixture())["query_costs"])

    def test_background_is_missing_not_zero(self):
        coordinates, labels, seeds = fixture()
        result = geometry_control(coordinates + [[50, 0, 0]], labels + [-100], seeds + [6])
        self.assertIsNone(result["query_costs"][-1])
        self.assertNotIn("-100", result["object_costs"])

    def test_zero_radius_and_singleton_are_rejected(self):
        result = geometry_control([[0, 0, 0], [0, 0, 0], [4, 0, 0]], [1, 1, 2], [0, 2])
        self.assertEqual(result["degenerate_object_ids"], [1, 2])
        self.assertEqual(result["query_costs"], [None, None])
        with self.assertRaisesRegex(ValueError, "degenerate"):
            validate_contrast(result, [1, 2])

    def test_uncovered_object_is_not_imputed(self):
        coordinates, labels, _ = fixture()
        result = geometry_control(coordinates, labels, [0])
        with self.assertRaisesRegex(ValueError, "Missing"):
            validate_contrast(result, [1, 2])

    def test_equal_geometry_rejected(self):
        result = geometry_control(
            [[0, 0, 0], [2, 0, 0], [4, 0, 0], [6, 0, 0]], [1, 1, 2, 2], [0, 2]
        )
        with self.assertRaisesRegex(ValueError, "Tied"):
            validate_contrast(result, [1, 2])

    def test_seed_membership_control_is_object_rank_degenerate(self):
        native = capture_fixture()
        for row in native["rows"]:
            row["objectness_scores"] = [
                float(row["instance_labels"][row["fps_superpoints"][i]] >= 0)
                for i in row["sampled_seed_indices"]
            ]
        registry = registry_fixture()
        capture = build_capture(
            registry, produce_expression_inputs(native, registry), binding_fixture()
        )
        self.assertEqual(capture["rows"][0]["scores"]["objectness"],
                         {"1": 0.0, "2": 0.0, "3": 0.0})

    def test_query_selection_can_change_contrast(self):
        coordinates, labels, seeds = fixture()
        before = geometry_control(coordinates, labels, seeds)
        after = geometry_control(coordinates, labels, [1, 3])
        self.assertNotEqual(before["object_costs"], after["object_costs"])
        self.assertEqual(before["support_costs"], after["support_costs"])

    def test_invalid_axes_fail_closed(self):
        for slot, value in (
            (0, []), (0, [[1, 2]]), (0, [[float("nan"), 0, 0]] * 6),
            (0, [[True, 0, 0]] * 6), (1, [1]), (1, [True] * 6),
            (1, [1.0] * 6), (2, []), (2, [True]), (2, [-1]), (2, [6]),
        ):
            with self.subTest(slot=slot, value=value):
                args = list(fixture())
                args[slot] = value
                with self.assertRaises(ValueError):
                    geometry_control(*args)

    def test_invalid_contrast_fails_closed(self):
        result = geometry_control(*fixture())
        for ids in ([1], [1, 1], [True, 2], ["1", "2"], [1, -1]):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                validate_contrast(result, ids)

    def test_geometry_cannot_be_relabelled_as_objectness(self):
        result = geometry_control(*fixture())
        native = capture_fixture()
        native["rows"][0]["objectness_score_semantics"] = result["semantics"]
        with self.assertRaisesRegex(ValueError, "objectness"):
            produce_expression_inputs(native, registry_fixture())


if __name__ == "__main__":
    unittest.main()
