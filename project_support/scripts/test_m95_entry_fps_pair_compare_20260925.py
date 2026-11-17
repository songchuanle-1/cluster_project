import unittest

from m95_entry_fps_pair_compare_20260925 import TARGET_ROWS, compare


class FakeScalar:
    def __init__(self, value):
        self.value = value

    def all(self):
        return self.value == 0

    def __eq__(self, other):
        return FakeScalar(self.value - other.value)

    def __sub__(self, other):
        return FakeScalar(self.value - other.value)

    def abs(self):
        return self

    def max(self):
        return self.value

    def __float__(self):
        return float(self.value)

    def __bool__(self):
        return self.all()


class EntryFpsComparisonTests(unittest.TestCase):
    def data(self):
        return {
            i: {
                "scene_id": str(i), "ann_id": i,
                "native_input_sha256": str(i), "shape": [1, 2, 3],
                "dtype": "torch.float32", "stride": [6, 3, 1],
                "coordinates": FakeScalar(0), "input_sha256": str(i),
                "indices": [0, 1],
            }
            for i in TARGET_ROWS
        }

    def test_equal(self):
        rows = compare(self.data(), self.data())
        self.assertTrue(all(r["coordinate_bytes_equal"] for r in rows))
        self.assertTrue(all(r["fps_changed_indices"] == 0 for r in rows))

    def test_input_mismatch_fails(self):
        a, b = self.data(), self.data()
        b[193]["native_input_sha256"] = "different"
        with self.assertRaisesRegex(ValueError, "identity differs"):
            compare(a, b)

    def test_missing_row_fails(self):
        a, b = self.data(), self.data()
        b.pop(193)
        with self.assertRaisesRegex(ValueError, "coverage differs"):
            compare(a, b)


if __name__ == "__main__":
    unittest.main()
