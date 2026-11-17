"""Fixed-child mean composition for HRC; the original IDs define every row.

Only the per-batch child prefix participates, exactly as in SharedClusterBank.
Internal empty-ID child rows remain ordinary fixed child slots, including any
FFN bias they acquire. No point-mass/occupancy weighting is introduced.
"""

import torch
from torch_scatter import scatter_mean


def refined_parent_mean(child_feats, parent_ids_list, parent_template):
    """Pool refined child slots into the original padded parent shape.

    child_feats: [B, K_child_max, C]; IDs for batch b have K_child_b entries.
    parent_template supplies shape only; its raw values are never overwritten.
    Feature gradients pass through the fixed scatter mean without detaching.
    """
    if child_feats.ndim != 3 or parent_template.ndim != 3:
        raise ValueError("HRC expects batched token tensors")
    batch_size, _, channels = child_feats.shape
    if parent_template.shape[0] != batch_size or parent_template.shape[2] != channels:
        raise ValueError("HRC child/parent batch and channel dimensions must agree")
    if len(parent_ids_list) != batch_size:
        raise ValueError("HRC needs one original parent-ID tensor per batch")
    parent_count = parent_template.shape[1]
    pooled = []
    for batch_index, parent_ids in enumerate(parent_ids_list):
        child_count = parent_ids.numel()
        if parent_ids.ndim != 1 or child_count > child_feats.shape[1]:
            raise ValueError("HRC parent IDs exceed the original child prefix")
        child = child_feats[batch_index, :child_count]
        pooled.append(scatter_mean(child, parent_ids, dim=0, dim_size=parent_count))
    return torch.stack(pooled, dim=0)
