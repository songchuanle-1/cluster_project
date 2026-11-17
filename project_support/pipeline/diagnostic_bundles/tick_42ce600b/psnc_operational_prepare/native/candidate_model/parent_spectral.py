"""Parent-segmented spectral nonlinear middle-token refinement.

The original middle f=FFN o LayerNorm is called once. Only true-supported
middle siblings mix. A private zero work row supplies differentiable f(0);
it is never a hierarchy token. No parameters, buffers, caches, routing or gates.
"""
import math
import torch

_MAX_MIDDLE_TOKENS = 64  # exact unchanged original native hierarchy bound


def _require(condition, message):
    if not condition:
        raise RuntimeError('PSNC: ' + message)


def _dct_ii(n, reference):
    # Real orthonormal DCT-II, rows=modes and columns=sorted original IDs.
    modes = torch.arange(n, device=reference.device, dtype=reference.dtype).unsqueeze(1)
    samples = torch.arange(n, device=reference.device, dtype=reference.dtype).unsqueeze(0)
    q = torch.cos((math.pi / n) * modes * (samples + 0.5)) * math.sqrt(2.0 / n)
    q[0] = 1.0 / math.sqrt(n)
    return q


def parent_spectral_delta(cf, cluster_ids_list, middle_positions,
                          geometry_ids, coarse_width, norm, ffn):
    """Return replacement middle FFN delta; the caller retains original cf+.

    For a real supported sibling group: delta=Q.T@(f(QX)-f(0))+f(0).
    For singleton, empty internal slot and batch pad: original per-row f.
    Zero/affine identities are deterministic real-arithmetic statements,
    not FP32 bitwise claims. No feature or f(0) is detached.
    """
    _require(cf.ndim == 3 and cf.shape[2] == 256, 'expected [B,K,256] middle bank')
    B, Kpad, C = cf.shape
    _require(0 <= Kpad <= _MAX_MIDDLE_TOKENS, 'middle bank exceeds original fixed64 bound')
    _require(geometry_ids is cluster_ids_list, 'stale geometry/ID cache identity')
    _require(isinstance(cluster_ids_list, (list, tuple)) and len(cluster_ids_list) == 3,
             'expected original three-level IDs')
    _require(all(len(level) == B for level in cluster_ids_list), 'ID batch mismatch')
    _require(isinstance(middle_positions, (list, tuple)) and len(middle_positions) == B,
             'missing current middle geometry')
    _require(type(coarse_width) is int and coarse_width > 0, 'invalid original coarse width')
    for module in ffn.modules():
        if isinstance(module, torch.nn.Dropout):
            _require(module.p == 0.0, 'original native dropout0 required; do not change stochastic protocol')
    groups = []
    has_mixed_group = False
    for b in range(B):
        ids0, ids1, ids2 = (level[b] for level in cluster_ids_list)
        for ids in (ids0, ids1, ids2):
            _require(ids.ndim == 1 and ids.dtype == torch.long and ids.device == cf.device,
                     'original IDs must be same-device long vectors')
            if ids.numel():
                _require(int(ids.min().item()) >= 0, 'negative original ID')
        K = ids2.numel()
        _require(K <= Kpad, 'middle prefix exceeds padded bank')
        positions = middle_positions[b]
        _require(positions.ndim == 2 and tuple(positions.shape) == (K, 3)
                 and positions.device == cf.device, 'geometry must match exact middle prefix')
        _require(bool(torch.isfinite(positions).all().item()), 'nonfinite current centroid')
        if ids0.numel():
            _require(ids1.numel() > 0 and int(ids0.max().item()) < ids1.numel(), 'point-to-fine ID range')
        if ids1.numel():
            _require(K > 0 and int(ids1.max().item()) < K, 'fine-to-middle ID range')
        if ids2.numel():
            _require(int(ids2.max().item()) < coarse_width, 'middle-to-coarse ID range')
        # True original point support, never feature magnitude or ids2 occupancy.
        actual_middle = ids1.index_select(0, ids0)
        counts = torch.bincount(actual_middle, minlength=K)
        occupied = torch.nonzero(counts > 0, as_tuple=False).flatten().tolist()
        parent_ids = ids2.detach().cpu().tolist()
        coords = positions.detach().cpu().tolist()
        by_parent = {}
        for original_id in occupied:
            by_parent.setdefault(parent_ids[original_id], []).append(original_id)
        batch_groups = []
        for parent in sorted(by_parent):
            order = sorted(by_parent[parent], key=lambda j: (coords[j][0], coords[j][1], coords[j][2], j))
            indices = torch.tensor(order, device=cf.device, dtype=torch.long)
            n = len(order)
            q = _dct_ii(n, cf) if n > 1 else None
            batch_groups.append((indices, q))
            has_mixed_group = has_mixed_group or n > 1
        groups.append(batch_groups)
    # Preserve the original [B,K,C] FFN layout when there is no genuine mixing.
    if not has_mixed_group:
        return ffn(norm(cf))
    work_batches = []
    for b, batch_groups in enumerate(groups):
        work_b = cf[b]
        for indices, q in batch_groups:
            if q is not None:
                work_b = work_b.index_copy(0, indices, q @ cf[b].index_select(0, indices))
        work_batches.append(work_b)
    work = torch.stack(work_batches, dim=0)
    sentinel = cf.new_zeros((B, 1, C))
    # Exactly one original norm/FFN call. f(0) remains on its real autograd graph.
    refined_work = ffn(norm(torch.cat((work, sentinel), dim=1)))
    base = refined_work[:, -1:, :]
    deltas = []
    for b, batch_groups in enumerate(groups):
        delta_b = refined_work[b, :Kpad]
        for indices, q in batch_groups:
            if q is not None:
                values = refined_work[b, :Kpad].index_select(0, indices)
                reconstructed = q.transpose(0, 1) @ (values - base[b]) + base[b]
                delta_b = delta_b.index_copy(0, indices, reconstructed)
        deltas.append(delta_b)
    return torch.stack(deltas, dim=0)
