import unittest

from native_manifest_capture_20260922 import identity_query_binding


class IdentityQueryBindingTest(unittest.TestCase):
    def bind(self, **kwargs):
        return identity_query_binding(
            kwargs.get("query_shape", (1, 2, 256)),
            kwargs.get("indicator_shape", (1, 2, 2)),
            kwargs.get("batch_index", 0),
            kwargs.get("seed_indices", [2, 0]),
            [10, 11, 12],
            kwargs.get("score_count", 2),
        )

    def test_physical_seed_binding(self):
        self.assertEqual(self.bind(), [12, 10])

    def test_rejects_query_axis_mismatch(self):
        with self.assertRaisesRegex(ValueError, "indicator axis"):
            self.bind(query_shape=(1, 1, 256))

    def test_rejects_missing_score(self):
        with self.assertRaisesRegex(ValueError, "score axis"):
            self.bind(score_count=1)

    def test_rejects_invalid_seed_index(self):
        with self.assertRaisesRegex(ValueError, "Invalid sampled seed"):
            self.bind(seed_indices=[2, 3])

    def test_rejects_unbatched_query(self):
        with self.assertRaisesRegex(ValueError, "must be batched"):
            self.bind(query_shape=(2, 256))

    def test_rejects_invalid_batch_index(self):
        with self.assertRaisesRegex(ValueError, "batch index"):
            self.bind(batch_index=1)

    def test_rejects_negative_seed_index(self):
        with self.assertRaisesRegex(ValueError, "Invalid sampled seed"):
            self.bind(seed_indices=[-1, 0])

    def test_rejects_boolean_seed_index(self):
        with self.assertRaisesRegex(ValueError, "Invalid sampled seed"):
            self.bind(seed_indices=[True, 0])


if __name__ == "__main__":
    unittest.main()
