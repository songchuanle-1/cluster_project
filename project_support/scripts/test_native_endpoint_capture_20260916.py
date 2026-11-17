import unittest
from native_endpoint_capture_20260916 import semantic_binding, enrich_row, EndpointDataset


class Tests(unittest.TestCase):
    def test_majority_and_unresolved(self):
        result = semantic_binding([0, 0, 1, 1], [4, 4, 4, 8], [2, 2, 2, 3], [4., 199.])
        self.assertEqual(result["physical_instance_labels"], [4, -1])
        self.assertEqual(result["semantic_labels"], [2, -1])
        self.assertEqual(result["unresolved_superpoints"], 1)

    def test_real_instance_199_is_preserved(self):
        self.assertEqual(semantic_binding([0], [199], [5], [199])[
            "physical_instance_labels"], [199])

    def test_mixed_instance_fails_closed(self):
        result = semantic_binding([0, 1], [4, 4], [2, 3], [4, 4])
        self.assertEqual(result["semantic_labels"], [-1, -1])

    def test_unknown_semantic(self):
        self.assertEqual(semantic_binding([0], [4], [-100], [4])[
            "semantic_labels"], [-100])

    def test_background(self):
        self.assertEqual(semantic_binding([0], [-100], [2], [-100])[
            "semantic_labels"], [-1])

    def test_support_mismatch(self):
        for args in (([0], [4], [], [4]), ([1], [4], [2], [4]),
                     ([0], [4], [2], [8]), ([0], [True], [2], [1])):
            with self.subTest(args=args), self.assertRaises(ValueError):
                semantic_binding(*args)

    def test_enrichment(self):
        row = dict(original_superpoint_ids=[4, 8], sample_inverse=[0, 1],
                   physical_instance_labels=[1, 2], semantic_labels=[3, 3],
                   target_instances=[1], ious=[1., 0.], selected_query=1)
        enrich_row(row, [False, True])
        self.assertTrue(row["recoverable_same_class"])
        self.assertEqual(row["selected_mask_endpoints"]["best_overlap_instances"], [2])

    def test_hook_restored_on_error(self):
        class Dataset:
            training = True

            def get_sp_label(self, *args):
                return [4], {}

            def transform_train(self, *args):
                raise RuntimeError("fixture")

            def __getitem__(self, index):
                self.transform_train()

        dataset = Dataset()
        wrapper = EndpointDataset(dataset, "test", "a" * 64)
        with self.assertRaises(RuntimeError):
            wrapper[0]
        self.assertNotIn("get_sp_label", vars(dataset))
        self.assertNotIn("transform_train", vars(dataset))


if __name__ == "__main__":
    unittest.main()
