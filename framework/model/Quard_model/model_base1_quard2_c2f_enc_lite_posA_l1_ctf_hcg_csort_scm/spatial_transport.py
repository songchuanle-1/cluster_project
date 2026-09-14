"""Selection-conditioned transport; no inference parameters or fitted scale."""
import torch
import torch.distributed as dist
import torch.nn.functional as F


def spatial_transport(masks, scores, xyz, target):
    if masks.ndim != 2 or scores.shape != (masks.shape[0],):
        raise ValueError("Expected masks [Q,N] and score differences [Q]")
    if xyz.shape != (masks.shape[1], 3) or target.shape != (masks.shape[1],):
        raise ValueError("Coordinates and binary target must align with masks")
    dtype = torch.float64 if masks.dtype == torch.float64 else torch.float32
    with torch.autocast(device_type=masks.device.type, enabled=False):
        masks, scores = masks.to(dtype), scores.to(dtype)
        xyz, target = xyz.detach().to(dtype), target.detach().to(dtype)
        if not all(torch.isfinite(v).all() for v in (masks, scores, xyz, target)):
            raise ValueError("Nonfinite valid SCM inputs")
        if ((target != 0) & (target != 1)).any():
            raise ValueError("Expected binary target union")
        zero = masks.sum() * 0 + scores.sum() * 0
        if not len(scores):
            return zero, "no_queries"
        if not len(target):
            return zero, "no_superpoints"
        if target.sum() == 0:
            return zero, "no_target"
        diameter = torch.linalg.vector_norm(xyz.amax(0) - xyz.amin(0))
        if diameter == 0:
            return zero, "zero_extent"
        b = F.logsigmoid(masks).softmax(-1)
        alpha = F.logsigmoid(scores).softmax(0)
        difference = alpha @ b - target / target.sum()
        costs = []
        for axis in range(3):
            order = torch.argsort(xyz[:, axis], stable=True)
            gaps = torch.diff(xyz[order, axis]) / diameter
            costs.append((gaps * difference[order].cumsum(0)[:-1].abs()).sum())
        return torch.stack(costs).mean(), "valid"


def parent_reduction(local_sum, global_matches, local_valid):
    """Preserve parent's local numerator/global matches, including DDP averaging."""
    valid = local_sum.new_tensor(float(local_valid))
    if dist.is_available() and dist.is_initialized():
        dist.all_reduce(valid)
    # No world-size multiplier: the unchanged parent also omits that multiplier.
    loss = local_sum / global_matches.clamp_min(1)
    return loss, valid.detach()
