import unittest
from types import SimpleNamespace

from native_partition_boundary_capture_20260925 import observe_partition


class Tensor:
    def __init__(self, values):
        self.values = values

    def __len__(self):
        return len(self.values)

    def __getitem__(self, index):
        return Tensor(self.values[index])

    def detach(self):
        return self

    def cpu(self):
        return self

    def tolist(self):
        return self.values


def distance(left, right):
    return Tensor([
        [abs(point[0] - center[0]) for center in right.values]
        for point in left.values
    ])


class NativePartitionObservationTest(unittest.TestCase):
    def setUp(self):
        self.torch = SimpleNamespace(cdist=distance)
        self.points = Tensor([[0.25], [0.8]])
        self.centers = Tensor([[0.0], [1.0]])

    def partition(self, points, centers):
        rows = self.torch.cdist(points, centers).tolist()
        return [
            Tensor([i for i, row in enumerate(rows)
                    if row.index(min(row)) == center])
            for center in range(len(centers))
        ]

    def test_records_native_row_and_preserves_partition(self):
        original = self.partition(self.points, self.centers)
        subsets, observed = observe_partition(
            self.torch, self.partition, self.points, self.centers, 0
        )
        self.assertEqual([x.tolist() for x in subsets],
                         [x.tolist() for x in original])
        self.assertEqual(observed["native_distance_row"], [0.25, 0.75])
        self.assertEqual(observed["distance_margin"], 0.5)
        self.assertIs(self.torch.cdist, distance)

    def test_invalid_point_index_fails(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            observe_partition(
                self.torch, self.partition, self.points, self.centers, 344
            )

    def test_missing_native_cdist_fails_closed(self):
        def unrelated(points, centers):
            return [Tensor([0]), Tensor([1])]

        with self.assertRaisesRegex(ValueError, "cdist"):
            observe_partition(
                self.torch, unrelated, self.points, self.centers, 0
            )

    def test_duplicate_membership_fails_closed(self):
        def duplicate(points, centers):
            self.torch.cdist(points, centers)
            return [Tensor([0]), Tensor([0, 1])]

        with self.assertRaisesRegex(ValueError, "membership"):
            observe_partition(
                self.torch, duplicate, self.points, self.centers, 0
            )

    def test_changed_distance_is_rejected_and_cdist_restored(self):
        def inconsistent(points, centers):
            self.torch.cdist(points, centers)
            return [Tensor([1]), Tensor([0])]

        with self.assertRaisesRegex(ValueError, "assignment"):
            observe_partition(
                self.torch, inconsistent, self.points, self.centers, 0
            )
        self.assertIs(self.torch.cdist, distance)
