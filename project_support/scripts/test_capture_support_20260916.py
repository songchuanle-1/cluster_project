import unittest

from capture_support_20260916 import CaptureDataset, bind_queries, support_record


class FakeDataset:
    training = True

    def __len__(self):
        return 2

    def transform_train(self):
        return None, None, None, [1, 0, 1], None, None, [4, 9]

    def __getitem__(self, index):
        result = self.transform_train()
        item = [None] * 16
        item[0], item[1], item[5], item[15] = [11, 12], "scene", result[3], [[1], [2]]
        return tuple(item)

    def collate_fn(self, items):
        return dict(scan_ids=[x[1] for x in items],
                    ann_ids=[ann for x in items for ann in x[0]],
                    scenes_len=[len(x[0]) for x in items])


class Tests(unittest.TestCase):
    def setUp(self):
        self.native = FakeDataset()
        self.wrapper = CaptureDataset(self.native, "capture-1", "a" * 64)

    def test_preserves_native_item_and_restores_method(self):
        item, axes = self.wrapper[0]
        self.assertEqual(item, self.native[0])
        self.assertNotIn("transform_train", vars(self.native))
        self.assertEqual(axes[0]["original_superpoint_ids"], [4, 9])
        self.assertEqual(axes[0]["sample_inverse"], [1, 0, 1])

    def test_repeated_scene_occurrence_is_not_same_capture_row(self):
        _, axes = self.wrapper.collate_fn([self.wrapper[0], self.wrapper[0]])
        self.assertEqual([r["expression_slot"] for r in axes], [0, 1, 0, 1])
        self.assertEqual([r["scene_occurrence"] for r in axes], [0, 0, 1, 1])

    def test_restores_after_native_failure(self):
        def fail():
            raise RuntimeError("fixture")
        self.native.transform_train = fail
        with self.assertRaises(RuntimeError):
            self.wrapper[0]
        self.assertIs(self.native.transform_train, fail)

    def test_rejects_support_and_query_mismatch(self):
        for ids, inverse in (([4, 4], [0]), ([4, 9], [0, 2]), ([4, 9], [0])):
            with self.assertRaises(ValueError):
                support_record(ids, inverse)
        _, axes = self.wrapper[0]
        with self.assertRaises(ValueError):
            bind_queries(axes[0], [.9], [.6, .8], [1], [1], [3, 4])
        with self.assertRaises(ValueError):
            bind_queries(axes[0], [.9], [.6], [1], [1], [3])

    def test_all_acceptable_rank_and_endpoints(self):
        _, axes = self.wrapper[0]
        row = bind_queries(axes[0], [.9, .9, .1], [.1, .6, .99],
                           [1, 0, 0], [1, 0, 0], [3, 4])
        self.assertEqual(row["selected_query"], 0)
        self.assertEqual(row["best_acceptable_rank"], 2)
        self.assertEqual(row["instance_labels"], [3, 4])
        self.assertEqual(len(row["support_sha256"]), 64)

    def test_no_acceptable(self):
        _, axes = self.wrapper[0]
        row = bind_queries(axes[0], [.9], [.5], [1], [1], [3, 4])
        self.assertIsNone(row["best_acceptable_rank"])

    def test_rejects_collation_reordering(self):
        original = self.native.collate_fn
        def changed(items):
            batch = original(items)
            batch["ann_ids"].reverse()
            return batch
        self.native.collate_fn = changed
        with self.assertRaises(ValueError):
            self.wrapper.collate_fn([self.wrapper[0]])


if __name__ == "__main__":
    unittest.main()
