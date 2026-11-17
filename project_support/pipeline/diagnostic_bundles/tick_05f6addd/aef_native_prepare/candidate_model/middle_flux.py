"""Fixed original-parent MST plus signed antisymmetric nonlinear middle-edge flux."""
import math
import torch
from torch import nn


def build_parent_mst(positions, parent_ids, supported):
    """Pure metadata plan; IDs are original middle rows, never renumbered.

    Prim edge order is (squared_distance, lower_original_ID, upper_original_ID).
    Root is the minimum supported original ID in each original parent group.
    Zero-distance distinct nodes are legal. Unsupported rows and batch padding
    never become nodes. This plan does not claim one-pass full-parent reception.
    """
    if not isinstance(positions, (list, tuple)) or not isinstance(parent_ids, (list, tuple)) or not isinstance(supported, (list, tuple)):
        raise ValueError('AEF metadata must be sequences')
    if len(positions) != len(parent_ids) or len(supported) != len(parent_ids):
        raise ValueError('AEF metadata lengths differ')
    coordinates = []
    grouped = {}
    for index, (position, parent, valid) in enumerate(zip(positions, parent_ids, supported)):
        if not isinstance(position, (list, tuple)) or len(position) != 3:
            raise ValueError('AEF positions must have exactly xyz')
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in position):
            raise ValueError('AEF coordinates must be finite numbers')
        if type(parent) is not int or parent < 0 or type(valid) is not bool:
            raise ValueError('AEF parent/support metadata is invalid')
        coordinates.append(tuple(float(v) for v in position))
        if valid:
            grouped.setdefault(parent, []).append(index)
    edges = []
    groups = []
    for parent in sorted(grouped):
        nodes = grouped[parent]
        selected = {nodes[0]}
        best = {}
        def edge_key(a, b):
            distance = sum((coordinates[a][axis] - coordinates[b][axis]) ** 2 for axis in range(3))
            if not math.isfinite(distance):
                raise ValueError('AEF squared distance is nonfinite')
            return (distance, min(a, b), max(a, b))
        for node in nodes[1:]:
            best[node] = (edge_key(nodes[0], node), nodes[0])
        group_edges = []
        while len(selected) < len(nodes):
            node = min(best, key=lambda n: best[n][0])
            key, previous = best.pop(node)
            group_edges.append((min(node, previous), max(node, previous)))
            selected.add(node)
            for other in best:
                key = edge_key(node, other)
                if key < best[other][0]:
                    best[other] = (key, node)
        groups.append({'parent_id': parent, 'node_ids': list(nodes), 'edges': group_edges})
        edges.extend(group_edges)
    return {'groups': groups, 'edges': edges}


class ParentAntisymmetricEdgeFlux(nn.Module):
    """One shared Linear2C->C/GELU call for both orientations of every MST edge."""
    def __init__(self, d_model, max_middle_tokens, max_parent_tokens):
        super().__init__()
        if type(d_model) is not int or d_model <= 0 or type(max_middle_tokens) is not int or max_middle_tokens <= 0 or type(max_parent_tokens) is not int or max_parent_tokens <= 0:
            raise ValueError('AEF model dimensions must be positive integers')
        self.d_model = d_model
        self.max_middle_tokens = max_middle_tokens
        self.max_parent_tokens = max_parent_tokens
        self.edge_map = nn.Linear(2 * d_model, d_model)
        self.activation = nn.GELU()

    def forward(self, features, positions, parent_ids, supported):
        if features.ndim != 3 or features.shape[-1] != self.d_model:
            raise ValueError('AEF expects [B,K,C] original middle normalized features')
        batch_size, width, channels = features.shape
        if width > self.max_middle_tokens:
            raise ValueError('AEF middle width exceeds unchanged native cluster capacity')
        if not all(isinstance(value, (list, tuple)) and len(value) == batch_size for value in (positions, parent_ids, supported)):
            raise ValueError('AEF geometry cache batch shape is invalid')
        left = []
        right = []
        for batch in range(batch_size):
            count = parent_ids[batch].numel()
            if parent_ids[batch].ndim != 1 or supported[batch].ndim != 1 or supported[batch].numel() != count or positions[batch].shape != (count, 3) or count > width:
                raise ValueError('AEF geometry cache does not match original middle rows')
            parents = parent_ids[batch].detach().cpu().tolist()
            if parents and max(parents) >= self.max_parent_tokens:
                raise ValueError('AEF original parent ID exceeds unchanged coarse capacity')
            plan = build_parent_mst(positions[batch].detach().cpu().tolist(),
                parents, supported[batch].detach().cpu().tolist())
            for a, b in plan['edges']:
                left.append(batch * width + a)
                right.append(batch * width + b)
        if not left:
            return features.new_zeros(features.shape)
        flat = features.reshape(batch_size * width, channels)
        left_index = torch.tensor(left, device=features.device, dtype=torch.long)
        right_index = torch.tensor(right, device=features.device, dtype=torch.long)
        left_values = flat.index_select(0, left_index)
        right_values = flat.index_select(0, right_index)
        oriented = torch.cat((torch.cat((left_values, right_values), dim=-1),
                              torch.cat((right_values, left_values), dim=-1)), dim=0)
        transformed = self.activation(self.edge_map(oriented))
        edge_count = len(left)
        flux = transformed[:edge_count] - transformed[edge_count:]
        delta = features.new_zeros((batch_size * width, channels))
        delta = delta.index_add(0, left_index, flux)
        delta = delta.index_add(0, right_index, -flux)
        return delta.reshape(batch_size, width, channels)
