"""Exact count-conditioned occupancy likelihood on physical contact boundaries."""
import numpy as np
import torch


def conditional_assignment(logits, target):
    """Per-variable negative log likelihood; leading axes are independent masks."""
    if logits.shape[-1] != target.numel():
        raise ValueError("Boundary logits/target sizes differ")
    target = target.to(device=logits.device, dtype=torch.bool)
    n = target.numel()
    k = int(target.sum())
    with torch.autocast(device_type=logits.device.type, enabled=False):
        z = logits if logits.dtype == torch.float64 else logits.float()
        if not torch.isfinite(z).all():
            raise ValueError("Nonfinite boundary logits")
        if n == 0 or k == 0 or k == n:
            return z.sum(-1) * 0
        if k > n // 2:
            z, target, k = -z, ~target, n - k
        # A detached common shift cancels analytically and reduces cancellation.
        z = z - z.mean(-1, keepdim=True).detach()
        states = z.new_zeros((*z.shape[:-1], 1))
        for i in range(n):
            value = z[..., i:i + 1]
            width = min(i + 1, k)
            interior = torch.logaddexp(
                states[..., 1:width], states[..., :width - 1] + value)
            if i + 1 <= k:
                last = states[..., -1:] + value
            else:
                last = torch.logaddexp(states[..., k:k + 1],
                                       states[..., k - 1:k] + value)
            states = torch.cat((states[..., :1], interior, last), dim=-1)
        return (states[..., k] - z[..., target].sum(-1)) / n


def scene_contacts(voxel_coords, p2v_map, superpoints, batch_offsets):
    """Detached six-face contacts from the actual augmented occupied voxels."""
    voxels = voxel_coords.detach().cpu().numpy().astype(np.int64)
    point_voxels = p2v_map.detach().cpu().numpy().ravel().astype(np.int64)
    sp = superpoints.detach().cpu().numpy().ravel().astype(np.int64)
    offsets = batch_offsets.detach().cpu().numpy().astype(np.int64)
    pairs, counts = np.unique(np.stack((point_voxels, sp), axis=1),
                              axis=0, return_counts=True)
    rank = np.lexsort((pairs[:, 1], -counts, pairs[:, 0]))
    ranked = pairs[rank]
    _, first = np.unique(ranked[:, 0], return_index=True)
    owner = np.empty(len(voxels), dtype=np.int64)
    owner[ranked[first, 0]] = ranked[first, 1]
    result = []
    for scene, (lo, hi) in enumerate(zip(offsets[:-1], offsets[1:])):
        take = voxels[:, 0] == scene
        xyz, labels = voxels[take, 1:], owner[take] - lo
        if len(xyz) == 0:
            result.append(np.empty((0, 2), dtype=np.int64))
            continue
        if (labels < 0).any() or (labels >= hi - lo).any():
            raise ValueError("Voxel superpoint owner outside scene")
        xyz = xyz - xyz.min(0)
        dims = xyz.max(0) + 2
        encode = lambda a: (a[:, 0] * dims[1] + a[:, 1]) * dims[2] + a[:, 2]
        keys = encode(xyz)
        order = np.argsort(keys)
        keys, xyz, labels = keys[order], xyz[order], labels[order]
        edges = []
        for axis in range(3):
            shifted = xyz.copy()
            shifted[:, axis] += 1
            wanted = encode(shifted)
            index = np.searchsorted(keys, wanted)
            safe = index.clip(max=len(keys) - 1)
            valid = (index < len(keys)) & (keys[safe] == wanted)
            a, b = labels[valid], labels[safe[valid]]
            different = a != b
            edges.append(np.sort(np.stack((a[different], b[different]), axis=1), axis=1))
        result.append(np.unique(np.concatenate(edges), axis=0))
    return result


def boundary_components(edges, target):
    """Connected components of the induced boundary graph, including same-label edges."""
    labels = target.detach().cpu().numpy().astype(bool)
    edges = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    if len(edges) and ((edges < 0).any() or (edges >= len(labels)).any()):
        raise ValueError("Contact endpoint outside target")
    crossing = edges[labels[edges[:, 0]] != labels[edges[:, 1]]]
    boundary = np.unique(crossing)
    adjacency = {int(v): set() for v in boundary}
    for a, b in edges:
        if int(a) in adjacency and int(b) in adjacency:
            adjacency[int(a)].add(int(b))
            adjacency[int(b)].add(int(a))
    remaining = set(adjacency)
    groups = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        stack, members = [first], []
        while stack:
            vertex = stack.pop()
            members.append(vertex)
            neighbors = adjacency[vertex] & remaining
            remaining.difference_update(neighbors)
            stack.extend(sorted(neighbors))
        groups.append(sorted(members))
    return groups


def boundary_loss(pred_masks, targets, indices, contacts, scene_lengths, num_matches):
    lengths = [int(v) for v in scene_lengths]
    if sum(lengths) != len(pred_masks) or len(lengths) != len(contacts):
        raise ValueError("Scene grouping does not match masks")
    total = pred_masks[0].sum() * 0
    stats = dict(valid_masks=0, empty_interfaces=0, boundary_variables=0)
    offset = 0
    for edge_array, size in zip(contacts, lengths):
        for b in range(offset, offset + size):
            qs, ts = indices[b]
            if targets[b]["masks"] is None or not len(qs):
                continue
            masks = targets[b]["masks"][ts].bool()
            # Targets repeat across matched queries. Evaluate each target in one DP batch.
            unique, inverse = torch.unique(masks, dim=0, return_inverse=True)
            per_expression = pred_masks[b].sum() * 0
            for j, gt in enumerate(unique):
                selected = qs[inverse == j]
                groups = boundary_components(edge_array, gt)
                n = sum(len(group) for group in groups)
                if not n:
                    stats["empty_interfaces"] += len(selected)
                    continue
                loss = pred_masks[b][selected].sum(-1) * 0
                for group in groups:
                    loss = loss + conditional_assignment(
                        pred_masks[b][selected][:, group], gt[group]) * (len(group) / n)
                per_expression = per_expression + loss.sum()
                stats["valid_masks"] += len(selected)
                stats["boundary_variables"] += n * len(selected)
            total = total + per_expression / len(qs)
        offset += size
    return total / num_matches.clamp_min(1), stats
