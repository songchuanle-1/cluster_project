"""M219 APF: simultaneous three-level ancestry-path factors, original IDs only."""
import torch
import torch.nn as nn


def _ids(values, limit, label):
    out = list(values)
    if any(type(i) is not int or i < 0 or i >= limit for i in out):
        raise ValueError(label + " must be integer original bank IDs in range")
    return out


def build_ancestry_path_plan(point_ids, fine_to_middle, middle_to_coarse, bank_sizes):
    """Pure metadata. One factor per truly point-supported original fine row.

    The two upper groups index these factors, not points, centroids, padding or
    recomputed raw banks. Coarse means weight fine paths equally, without an
    intermediate mean over middle groups. External original IDs never change.
    """
    if len(bank_sizes) != 3 or any(type(k) is not int or k < 0 for k in bank_sizes):
        raise ValueError("three nonnegative integer original bank widths required")
    k0, k1, k2 = bank_sizes
    p = _ids(point_ids, k0, "point_ids")
    f2m = _ids(fine_to_middle, k1, "fine_to_middle")
    m2c = _ids(middle_to_coarse, k2, "middle_to_coarse")
    if len(f2m) > k0 or len(m2c) > k1:
        raise ValueError("membership exceeds original child bank")
    fine = sorted(set(p))
    if any(i >= len(f2m) for i in fine):
        raise ValueError("supported fine ID has no original middle parent")
    middle_for_paths = [f2m[i] for i in fine]
    if any(j >= len(m2c) for j in middle_for_paths):
        raise ValueError("supported middle ID has no original coarse parent")
    coarse_for_paths = [m2c[j] for j in middle_for_paths]
    middle = sorted(set(middle_for_paths)); coarse = sorted(set(coarse_for_paths))
    mid_positions = {j: q for q, j in enumerate(middle)}
    coarse_positions = {k: q for q, k in enumerate(coarse)}
    mp = [mid_positions[j] for j in middle_for_paths]
    cp = [coarse_positions[k] for k in coarse_for_paths]
    mc = [0] * len(middle); cc = [0] * len(coarse)
    for j in mp: mc[j] += 1
    for k in cp: cc[k] += 1
    return {"fine_ids": fine, "middle_for_paths": middle_for_paths,
            "coarse_for_paths": coarse_for_paths,
            "middle_ids": middle, "coarse_ids": coarse,
            "middle_parent_positions": mp, "coarse_parent_positions": cp,
            "middle_path_counts": mc, "coarse_path_counts": cc,
            "path_count": len(fine), "point_count": len(p)}


def prepare_ancestry_path_plans(levels, cluster_ids_list):
    if len(levels) != 3 or len(cluster_ids_list) != 3:
        raise ValueError("APF requires the original three banks and ID lists")
    batch = int(levels[0].shape[0])
    channels = int(levels[0].shape[2])
    if any(x.ndim != 3 or int(x.shape[0]) != batch or int(x.shape[2]) != channels
           or x.device != levels[0].device or x.dtype != levels[0].dtype for x in levels):
        raise ValueError("inconsistent original bank batch/channel/device/dtype")
    if any(len(ids) != batch for ids in cluster_ids_list):
        raise ValueError("original membership batch count mismatch")
    widths = [int(x.shape[1]) for x in levels]
    return [build_ancestry_path_plan(
        cluster_ids_list[0][b].detach().cpu().tolist(),
        cluster_ids_list[1][b].detach().cpu().tolist(),
        cluster_ids_list[2][b].detach().cpu().tolist(), widths)
        for b in range(batch)]


def mean_path_messages(messages, parent_positions, counts):
    """Fixed equal mean of actual vector factor outputs; no learned score."""
    index = torch.tensor(parent_positions, device=messages.device, dtype=torch.long)
    summed = messages.new_zeros((len(counts), messages.shape[1])).index_add(0, index, messages)
    divisor = messages.new_tensor(counts).unsqueeze(-1)
    return summed / divisor


class AncestryPathFactorComposition(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.channels = channels
        self.path_map = nn.Linear(3 * channels, 3 * channels)
        self.activation = nn.GELU()

    def forward(self, normalized, cluster_ids_list):
        plans = prepare_ancestry_path_plans(normalized, cluster_ids_list)
        if any(int(x.shape[2]) != self.channels for x in normalized):
            raise ValueError("APF channel count changed")
        batch = int(normalized[0].shape[0])
        widths = [int(x.shape[1]) for x in normalized]
        flat = [x.reshape(batch * widths[l], self.channels) for l, x in enumerate(normalized)]
        fine_index=[]; middle_input=[]; coarse_input=[]
        middle_index=[]; coarse_index=[]; mp=[]; cp=[]; mc=[]; cc=[]
        for b, plan in enumerate(plans):
            mo, co = len(middle_index), len(coarse_index)
            fine_index.extend(b * widths[0] + i for i in plan["fine_ids"])
            middle_input.extend(b * widths[1] + j for j in plan["middle_for_paths"])
            coarse_input.extend(b * widths[2] + k for k in plan["coarse_for_paths"])
            middle_index.extend(b * widths[1] + j for j in plan["middle_ids"])
            coarse_index.extend(b * widths[2] + k for k in plan["coarse_ids"])
            mp.extend(mo + j for j in plan["middle_parent_positions"])
            cp.extend(co + k for k in plan["coarse_parent_positions"])
            mc.extend(plan["middle_path_counts"]); cc.extend(plan["coarse_path_counts"])
        delta = [x.new_zeros(x.shape) for x in flat]
        if not fine_index:
            return [x.reshape(normalized[l].shape) for l, x in enumerate(delta)]
        device = normalized[0].device
        fi = torch.tensor(fine_index, device=device, dtype=torch.long)
        mi = torch.tensor(middle_input, device=device, dtype=torch.long)
        ci = torch.tensor(coarse_input, device=device, dtype=torch.long)
        triplets = torch.cat([flat[0].index_select(0, fi), flat[1].index_select(0, mi),
                              flat[2].index_select(0, ci)], dim=-1)
        factors = self.activation(self.path_map(triplets))
        c = self.channels
        fine_delta, middle_messages, coarse_messages = factors[:, :c], factors[:, c:2*c], factors[:, 2*c:]
        middle_delta = mean_path_messages(middle_messages, mp, mc)
        coarse_delta = mean_path_messages(coarse_messages, cp, cc)
        delta[0] = delta[0].index_copy(0, fi, fine_delta)
        delta[1] = delta[1].index_copy(0, torch.tensor(middle_index, device=device, dtype=torch.long), middle_delta)
        delta[2] = delta[2].index_copy(0, torch.tensor(coarse_index, device=device, dtype=torch.long), coarse_delta)
        return [x.reshape(normalized[l].shape) for l, x in enumerate(delta)]
