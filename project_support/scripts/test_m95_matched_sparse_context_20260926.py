import unittest

from m95_matched_sparse_context_20260926 import compare_tensors


class CompareTensorsTest(unittest.TestCase):
    def test_same_shape_reports_elementwise_difference(self):
        import numpy as np

        class Tensor:
            def __init__(self, array):
                self.array = np.asarray(array, dtype=float)
                self.shape = self.array.shape

            def float(self):
                return self

            def __sub__(self, other):
                return Tensor(self.array - other.array)

            def abs(self):
                return Tensor(abs(self.array))

            def max(self):
                return self.array.max()

            def mean(self):
                return self.array.mean()

            def __ne__(self, other):
                return Tensor(self.array != other)

            def sum(self):
                return self.array.sum()

        self.assertEqual(compare_tensors(Tensor([0, 1]), Tensor([0, 2])),
                         {"comparable": True, "max_abs": 1.0,
                          "mean_abs": 0.5, "changed_elements": 1})

    def test_shape_mismatch_is_not_compared(self):
        class Shape:
            def __init__(self, shape):
                self.shape = shape

        result = compare_tensors(Shape((2, 3)), Shape((3, 2)))
        self.assertEqual(result, {"comparable": False,
                                  "left_shape": [2, 3], "right_shape": [3, 2]})


if __name__ == "__main__":
    unittest.main()
