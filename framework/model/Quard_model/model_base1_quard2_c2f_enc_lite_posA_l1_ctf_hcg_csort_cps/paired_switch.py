"""Conditional assignment supervision on shared physical seed identities."""
import itertools

import torch
import torch.nn.functional as F


def paired_switch(indis, seed_ids, instance_labels, object_ids, scene_lengths):
    if indis.ndim != 3 or indis.shape[-1] != 2:
        raise ValueError("Expected [expressions, queries, 2] logits")
    lengths = [int(v) for v in scene_lengths]
    if any(v < 0 for v in lengths) or sum(lengths) != len(indis):
        raise ValueError("Scene grouping does not match expression count")
    if seed_ids.shape != indis.shape[:2]:
        raise ValueError("Seed/logit shapes differ")
    if len(instance_labels) != len(indis) or len(object_ids) != len(indis):
        raise ValueError("Target metadata length differs")
    # Float32 loss island preserves AMP stability; float64 supports gradcheck.
    with torch.autocast(device_type=indis.device.type, enabled=False):
        z = indis if indis.dtype == torch.float64 else indis.float()
        if not torch.isfinite(z).all():
            raise ValueError("Nonfinite valid selector logits")
        d = z[..., 1] - z[..., 0]
        total = d.sum() * 0
        counters = dict(eligible_pairs=0, eligible_scenes=0, same_target=0,
                        multi_target=0, missing_shared_target=0, duplicate_queries=0)
        physical = []
        # FPS may repeat seeds when a scene has fewer points than fps_num.
        # Average observations per physical seed before forming the shared set.
        for row, ids in zip(d, seed_ids):
            unique, inverse, counts = torch.unique(
                ids.long(), sorted=True, return_inverse=True, return_counts=True)
            means = row.new_zeros(len(unique)).scatter_add(0, inverse, row) / counts
            physical.append((unique, means))
            counters["duplicate_queries"] += ids.numel() - unique.numel()
        offset = 0
        for size in lengths:
            pair_losses = []
            for a, b in itertools.combinations(range(offset, offset + size), 2):
                if len(object_ids[a]) != 1 or len(object_ids[b]) != 1:
                    counters["multi_target"] += 1
                    continue
                ta, tb = int(object_ids[a][0]), int(object_ids[b][0])
                if ta == tb:
                    counters["same_target"] += 1
                    continue
                if ta < 0 or tb < 0 or ta == 199 or tb == 199:
                    counters["missing_shared_target"] += 1
                    continue
                sa, da = physical[a]
                sb, db = physical[b]
                if sa.numel() == 0 or sb.numel() == 0:
                    counters["missing_shared_target"] += 1
                    continue
                where = torch.searchsorted(sb, sa)
                safe = where.clamp(max=sb.numel() - 1)
                common = (where < sb.numel()) & (sb[safe] == sa)
                ids = sa[common]
                la = instance_labels[a].to(ids.device)
                lb = instance_labels[b].to(ids.device)
                if ids.numel() and (ids.min() < 0 or ids.max() >= min(len(la), len(lb))):
                    raise ValueError("Physical seed outside scene label array")
                if not torch.equal(la[ids], lb[ids]):
                    raise ValueError("Paired scene instance maps disagree")
                ma, mb = la[ids] == ta, la[ids] == tb
                if not ma.any() or not mb.any():
                    counters["missing_shared_target"] += 1
                    continue
                change = da[common] - db[safe[common]]
                delta = change[ma].mean() - change[mb].mean()
                pair_losses.append(F.softplus(-delta))
                counters["eligible_pairs"] += 1
            if pair_losses:
                total = total + torch.stack(pair_losses).mean()
                counters["eligible_scenes"] += 1
            offset += size
        return total, counters
