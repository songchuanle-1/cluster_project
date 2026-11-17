"""Observe one native partition cdist row without replacing partition outputs."""
from unittest.mock import patch

from m95_partition_boundary_probe_20260925 import boundary_observation


def observe_partition(torch_module, partition, points, centers, point_index):
    if not 0 <= point_index < len(points):
        raise ValueError("Point index outside partition support")
    native_cdist = torch_module.cdist
    observed = []

    def capture_cdist(left, right, *args, **kwargs):
        distances = native_cdist(left, right, *args, **kwargs)
        if left is points and right is centers:
            observed.append(distances[point_index].detach().cpu().tolist())
        return distances

    with patch.object(torch_module, "cdist", capture_cdist):
        subsets = partition(points, centers)
    if len(observed) != 1 or len(subsets) != len(centers):
        raise ValueError("Native partition cdist call structure differs")
    membership = [
        center_id for center_id, subset in enumerate(subsets)
        if point_index in subset.detach().cpu().tolist()
    ]
    if len(membership) != 1:
        raise ValueError("Native partition membership is not unique")
    point = points[point_index].detach().cpu().tolist()
    center_positions = centers.detach().cpu().tolist()
    boundary = boundary_observation(
        point, center_positions, membership[0], observed[0]
    )
    boundary.update(
        point_index=point_index,
        native_distance_row=observed[0],
        center_positions=center_positions,
    )
    return subsets, boundary
