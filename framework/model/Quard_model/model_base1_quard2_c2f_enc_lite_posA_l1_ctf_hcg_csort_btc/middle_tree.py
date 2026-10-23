"""M211: within-parent binary-tree inside/outside complement composition.

The detached geometry defines a work tree only. Original hierarchy IDs, raw
banks, CSORT and HCG are never rewritten. No point-pair matrix is constructed.
"""
import math

import torch
from torch import nn


def build_parent_forest(centers, parent_ids, supported, max_middle_tokens):
    """Build the actual production topology using only Python scalar geometry.

    Leaves retain original middle IDs. Negative IDs name private internal nodes.
    Longest extent ties use x/y/z; ordering ties use xyz then original token ID.
    Each nonempty original coarse parent owns a separate balanced binary tree.
    """
    k = len(parent_ids)
    if not (len(centers) == len(supported) == k <= max_middle_tokens):
        raise ValueError('BTC geometry/support/parent prefix mismatch or oversized hierarchy')
    for point, parent, active in zip(centers, parent_ids, supported):
        if len(point) != 3 or not all(math.isfinite(v) for v in point):
            raise ValueError('BTC requires finite 3D original middle centers')
        if type(parent) is not int or parent < 0 or type(active) is not bool:
            raise ValueError('BTC invalid original parent IDs or true-support mask')
    groups = {}
    for token, (parent, active) in enumerate(zip(parent_ids, supported)):
        if active:
            groups.setdefault(parent, []).append(token)
    forest = []
    for parent in sorted(groups):
        children, postorder = {}, []
        next_internal = -1

        def split(rows):
            nonlocal next_internal
            if len(rows) == 1:
                return rows[0]
            extents = [max(centers[i][a] for i in rows) -
                       min(centers[i][a] for i in rows) for a in range(3)]
            axis = max(range(3), key=lambda a: (extents[a], -a))
            ordered = sorted(rows, key=lambda i: (centers[i][axis],
                                                  *centers[i], i))
            cut = len(ordered) // 2
            left, right = split(ordered[:cut]), split(ordered[cut:])
            node = next_internal
            next_internal -= 1
            children[node] = (left, right)
            postorder.append(node)
            return node

        root = split(groups[parent])
        forest.append((parent, root, children, postorder, tuple(groups[parent])))
    return forest


class ParentBinaryTreeComplement(nn.Module):
    """Three shared 2C->C maps, two GELU compositions, no new residual or gate."""

    def __init__(self, channels, max_middle_tokens):
        super().__init__()
        self.channels = channels
        self.max_middle_tokens = max_middle_tokens
        self.inside = nn.Linear(2 * channels, channels)
        self.outside = nn.Linear(2 * channels, channels)
        self.leaf = nn.Linear(2 * channels, channels)
        self.activation = nn.GELU()

    def forward(self, features, positions, parent_ids, supported):
        if features.ndim != 3 or features.shape[-1] != self.channels:
            raise ValueError('BTC expects [batch, middle_slots, channels]')
        batch, slots, _ = features.shape
        if (positions is None or supported is None or parent_ids is None or
                not (len(positions) == len(parent_ids) == len(supported) == batch)):
            raise RuntimeError('BTC current-forward geometry/support cache missing')
        output = torch.zeros_like(features)
        for b in range(batch):
            parents, valid, coords = parent_ids[b], supported[b], positions[b]
            k = parents.numel()
            if (parents.ndim != 1 or parents.dtype != torch.long or
                    valid.shape != (k,) or valid.dtype != torch.bool or
                    coords.shape != (k, 3) or k > slots or
                    parents.device != features.device or
                    valid.device != features.device or coords.device != features.device):
                raise RuntimeError('BTC shape/device/ID domain mismatch')
            forest = build_parent_forest(coords.detach().cpu().tolist(),
                                         parents.detach().cpu().tolist(),
                                         valid.detach().cpu().tolist(),
                                         self.max_middle_tokens)
            leaves, values = [], []
            for _, root, children, postorder, tokens in forest:
                # Every dictionary is local to one parent and one batch item.
                inside = {token: features[b, token] for token in tokens}
                for node in postorder:
                    # Root inside is unused by a strict complement pass.
                    if node != root:
                        left, right = children[node]
                        inside[node] = self.activation(self.inside(
                            torch.cat((inside[left], inside[right]), dim=-1)))
                outside = {root: features.new_zeros(self.channels)}
                # Reverse postorder visits each parent before its children.
                for node in reversed(postorder):
                    left, right = children[node]
                    outside[left] = self.activation(self.outside(
                        torch.cat((outside[node], inside[right]), dim=-1)))
                    outside[right] = self.activation(self.outside(
                        torch.cat((outside[node], inside[left]), dim=-1)))
                for token in tokens:
                    leaves.append(token)
                    values.append(self.leaf(torch.cat(
                        (inside[token], outside[token]), dim=-1)))
            if leaves:
                indices = torch.tensor(leaves, dtype=torch.long, device=features.device)
                output[b] = output[b].index_copy(0, indices, torch.stack(values))
        # Internal empty slots and batch padding stay zero and enter no tree.
        # HCG can only read truly point-supported middle slots.
        return output
