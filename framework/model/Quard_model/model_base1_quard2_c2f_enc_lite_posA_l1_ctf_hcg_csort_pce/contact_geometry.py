"""Exact co-occupancy and six-face contacts using full membership joins."""
import numpy as np


def _unique_pairs(left, right, width):
    """Exact lexicographic pair deduplication with checked integer keys."""
    left = np.asarray(left, dtype=np.int64).ravel()
    right = np.asarray(right, dtype=np.int64).ravel()
    if not len(left):
        return np.empty((0, 2), dtype=np.int64)
    if width <= 0 or np.any(left < 0) or np.any(right < 0) or np.any(right >= width):
        raise ValueError('Invalid contact membership key')
    if int(left.max()) > (np.iinfo(np.int64).max - (width - 1)) // width:
        raise OverflowError('Contact integer key exceeds int64')
    keys = np.unique(left * width + right)
    return np.column_stack((keys // width, keys % width))


def contacts(voxel_coordinates, point_voxels, point_superpoints, offsets):
    voxels = np.asarray(voxel_coordinates, dtype=np.int64)
    offsets = np.asarray(offsets, dtype=np.int64)
    if not len(voxels):
        return [np.empty((0, 2), dtype=np.int64) for _ in offsets[:-1]]
    memberships = _unique_pairs(point_voxels, point_superpoints, int(offsets[-1]))
    starts = np.searchsorted(memberships[:, 0], np.arange(len(voxels) + 1))
    counts = np.diff(starts)
    assert np.all(counts > 0)
    record = np.dtype([(name, np.int64) for name in ('batch', 'x', 'y', 'z')])
    keys = np.ascontiguousarray(voxels).view(record).reshape(-1)
    order = np.argsort(keys, kind='stable')
    sorted_keys = keys[order]
    identifiers = np.arange(len(voxels), dtype=np.int64)
    pairs = [np.column_stack((identifiers, identifiers))]
    for axis in (1, 2, 3):
        neighbor = voxels.copy()
        neighbor[:, axis] += 1
        neighbor_keys = np.ascontiguousarray(neighbor).view(record).reshape(-1)
        index = np.searchsorted(sorted_keys, neighbor_keys)
        valid = index < len(voxels)
        valid &= sorted_keys[np.minimum(index, len(voxels) - 1)] == neighbor_keys
        pairs.append(np.column_stack((identifiers[valid], order[index[valid]])))
    pairs = np.concatenate(pairs, axis=0)
    left_counts, right_counts = counts[pairs[:, 0]], counts[pairs[:, 1]]
    products = left_counts * right_counts
    repeated = np.repeat(np.arange(len(pairs)), products)
    within = np.arange(int(products.sum())) - np.repeat(np.cumsum(products) - products, products)
    left = starts[pairs[repeated, 0]] + within // right_counts[repeated]
    right = starts[pairs[repeated, 1]] + within % right_counts[repeated]
    edges = np.column_stack((memberships[left, 1], memberships[right, 1]))
    edges = edges[edges[:, 0] != edges[:, 1]]
    edges = _unique_pairs(np.minimum(edges[:, 0], edges[:, 1]),
        np.maximum(edges[:, 0], edges[:, 1]), int(offsets[-1]))
    output = []
    for lo, hi in zip(offsets[:-1], offsets[1:]):
        selected = edges[(edges[:, 0] >= lo) & (edges[:, 0] < hi)]
        assert not len(selected) or np.all(selected[:, 1] < hi)
        output.append(selected - lo)
    return output
