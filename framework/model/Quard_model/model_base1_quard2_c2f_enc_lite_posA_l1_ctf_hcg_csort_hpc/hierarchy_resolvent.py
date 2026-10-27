"""M218 HPC: exact two-level tree Schur elimination for (I + L) solves.

Only original point-supported IDs define edges. No dense inverse, feature
round-trip through Python, data-dependent weights, or trainable parameters.
"""
import torch


def _checked_ids(values, limit, label):
    result = list(values)
    if any(type(v) is not int or v < 0 or v >= limit for v in result):
        raise ValueError(label + " must contain in-range integer IDs")
    return result


def build_resolvent_plan(point_ids, fine_to_middle, middle_to_coarse,
                         bank_sizes):
    """Pure stdlib metadata for one batch's ORIGINAL three-level forest.

    Active means reachable from a real point via ids0 -> ids1 -> ids2.
    Unsupported and batch-pad rows are absent from this forest, not attached
    to a sentinel. All returned IDs retain their original bank row identity.
    """
    if len(bank_sizes) != 3 or any(type(k) is not int or k < 0 for k in bank_sizes):
        raise ValueError("exactly three nonnegative integer bank sizes required")
    k0, k1, k2 = bank_sizes
    p = _checked_ids(point_ids, k0, "point_ids")
    f2m = _checked_ids(fine_to_middle, k1, "fine_to_middle")
    m2c = _checked_ids(middle_to_coarse, k2, "middle_to_coarse")
    if len(f2m) > k0 or len(m2c) > k1:
        raise ValueError("membership arrays exceed their child banks")
    fine = sorted(set(p))
    if any(i >= len(f2m) for i in fine):
        raise ValueError("a supported fine row has no original middle parent")
    middle = sorted({f2m[i] for i in fine})
    if any(j >= len(m2c) for j in middle):
        raise ValueError("a supported middle row has no original coarse parent")
    coarse = sorted({m2c[j] for j in middle})
    mpos = {j: q for q, j in enumerate(middle)}
    cpos = {k: q for q, k in enumerate(coarse)}
    fine_parent = [mpos[f2m[i]] for i in fine]
    middle_parent = [cpos[m2c[j]] for j in middle]
    fine_counts = [0] * len(middle)
    middle_counts = [0] * len(coarse)
    for j in fine_parent:
        fine_counts[j] += 1
    for k in middle_parent:
        middle_counts[k] += 1
    # Eliminate fine leaves of A=I+L. Each active fine node has diagonal 2.
    middle_diagonal = [2.0 + n / 2.0 for n in fine_counts]
    coarse_diagonal = [1.0 + n for n in middle_counts]
    for j, k in enumerate(middle_parent):
        coarse_diagonal[k] -= 1.0 / middle_diagonal[j]
    if any(a <= 0 for a in middle_diagonal + coarse_diagonal):
        raise ValueError("nonpositive Schur diagonal")
    return {
        "fine_ids": fine, "middle_ids": middle, "coarse_ids": coarse,
        "fine_parent_positions": fine_parent,
        "middle_parent_positions": middle_parent,
        "fine_child_counts": fine_counts, "middle_child_counts": middle_counts,
        "middle_diagonal": middle_diagonal,
        "coarse_diagonal": coarse_diagonal,
        "point_count": len(p),
        "edge_count": len(fine) + len(middle),
        "active_node_count": len(fine) + len(middle) + len(coarse),
    }


def prepare_resolvent_plans(levels, cluster_ids_list):
    if len(levels) != 3 or len(cluster_ids_list) != 3:
        raise ValueError("HPC requires the original three levels")
    batch = levels[0].shape[0]
    if any(x.ndim != 3 or x.shape[0] != batch or
           x.shape[2] != levels[0].shape[2] for x in levels):
        raise ValueError("inconsistent original bank shapes")
    if any(len(ids) != batch for ids in cluster_ids_list):
        raise ValueError("membership batch count mismatch")
    sizes = [int(x.shape[1]) for x in levels]
    return [build_resolvent_plan(
        cluster_ids_list[0][b].detach().cpu().tolist(),
        cluster_ids_list[1][b].detach().cpu().tolist(),
        cluster_ids_list[2][b].detach().cpu().tolist(), sizes)
        for b in range(batch)]


def solve_resolvent_levels(levels, plans):
    """Apply (I+L)^-1 in O(active nodes * channels), without dense matrices.

    Functional index_add/index_copy retain the feature autograd graph. Only
    integer membership metadata went to CPU. Unsupported/pad rows use identity,
    retaining the original per-row LN/FFN behavior outside the active forest.
    """
    if len(levels) != 3 or len(plans) != levels[0].shape[0]:
        raise ValueError("three banks and one forest plan per batch required")
    if not plans:
        return list(levels)
    result = [[], [], []]
    for b, plan in enumerate(plans):
        if not plan["fine_ids"]:
            for level in range(3):
                result[level].append(levels[level][b])
            continue
        device = levels[0].device
        ids = [torch.tensor(plan[key], device=device, dtype=torch.long)
               for key in ("fine_ids", "middle_ids", "coarse_ids")]
        fparent = torch.tensor(plan["fine_parent_positions"], device=device,
                               dtype=torch.long)
        mparent = torch.tensor(plan["middle_parent_positions"], device=device,
                               dtype=torch.long)
        x0, x1, x2 = [levels[l][b].index_select(0, ids[l]) for l in range(3)]
        a1 = x1.new_tensor(plan["middle_diagonal"]).unsqueeze(-1)
        a2 = x2.new_tensor(plan["coarse_diagonal"]).unsqueeze(-1)
        r1 = x1.index_add(0, fparent, x0 * 0.5)
        r2 = x2.index_add(0, mparent, r1 / a1)
        z2 = r2 / a2
        z1 = (r1 + z2.index_select(0, mparent)) / a1
        z0 = (x0 + z1.index_select(0, fparent)) * 0.5
        for level, solved in enumerate((z0, z1, z2)):
            result[level].append(levels[level][b].index_copy(0, ids[level], solved))
    return [torch.stack(rows, dim=0) for rows in result]
