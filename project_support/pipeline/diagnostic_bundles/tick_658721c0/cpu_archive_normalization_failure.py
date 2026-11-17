"""Geometry-only physical contact graph and a cross-leaf feature path."""
import math
import numpy as np
import torch


def contacts(voxel_coordinates, point_voxels, point_superpoints, offsets):
    voxels = np.asarray(voxel_coordinates, dtype=np.int64)
    memberships = np.unique(np.column_stack((np.asarray(point_voxels).ravel(),
        np.asarray(point_superpoints).ravel())), axis=0)
    owners = {}
    for voxel, owner in memberships:
        owners.setdefault(int(voxel), []).append(int(owner))
    result = []
    for scene, (lo, hi) in enumerate(zip(offsets[:-1], offsets[1:])):
        lookup = {tuple(row[1:]): index for index, row in enumerate(voxels) if row[0] == scene}
        edges = set()
        for coordinate, index in lookup.items():
            here = owners[index]
            assert all(lo <= owner < hi for owner in here)
            for a in here:
                for b in here:
                    if a < b:
                        edges.add((a - lo, b - lo))
            for axis in range(3):
                neighbor = list(coordinate)
                neighbor[axis] += 1
                other = lookup.get(tuple(neighbor))
                if other is not None:
                    for a in here:
                        for b in owners[other]:
                            if a != b:
                                edges.add(tuple(sorted((a - lo, b - lo))))
        array = np.asarray(sorted(edges), dtype=np.int64).reshape(-1, 2)
        if len(array):
            assert array.min() >= 0 and array.max() < hi - lo
        result.append(array)
    return result


def exchange(features, positions, leaves, edge_array, fallback, heads=8, rotate_values=False):
    n, channels = features.shape
    assert channels % heads == 0 and fallback.shape == features.shape
    leaves = np.asarray(leaves, dtype=np.int64)
    positions = np.asarray(positions)
    edges = np.asarray(edge_array, dtype=np.int64).reshape(-1, 2)
    adjacency = [set() for _ in range(n)]
    for a, b in edges:
        if leaves[a] != leaves[b]:
            adjacency[a].add(int(b))
            adjacency[b].add(int(a))
    dimension = channels // heads
    rows, degrees = [], []
    for i, donors in enumerate(adjacency):
        degrees.append(len(donors))
        if not donors:
            rows.append(fallback[i])
            continue
        # Geometry fixes reduction order, independently of superpoint numbering.
        donors = sorted(donors, key=lambda j: tuple(positions[j]))
        coordinates = [tuple(positions[j]) for j in donors]
        if len(coordinates) != len(set(coordinates)):
            raise ValueError('Coincident contact donors: geometric ordering undefined')
        indices = torch.tensor(donors, device=features.device)
        keys = features[indices].reshape(len(donors), heads, dimension)
        values = features[(indices + 1) % n] if rotate_values else features[indices]
        values = values.reshape(len(donors), heads, dimension)
        query = features[i].reshape(1, heads, dimension)
        weights = ((query * keys).sum(-1) / math.sqrt(dimension)).softmax(0)
        rows.append((weights.unsqueeze(-1) * values).sum(0).reshape(channels))
    return torch.stack(rows), degrees
