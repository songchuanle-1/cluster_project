"""Isolated SCM draft checks. Does not import or modify a training model."""
import json
import numpy as np
import torch
import torch.nn.functional as F

from scm_math_check_20260914 import objective


def spatial_transport(masks, scores, xyz, target, valid=None, query_valid=None):
    """One expression; return loss and explicit exclusion status."""
    if masks.ndim != 2 or scores.shape != (masks.shape[0],):
        raise ValueError("Expected masks [Q,N] and score differences [Q]")
    if xyz.shape != (masks.shape[1], 3) or target.shape != (masks.shape[1],):
        raise ValueError("Coordinates and target must align with mask columns")
    if valid is None:
        valid = torch.ones_like(target, dtype=torch.bool)
    if query_valid is None:
        query_valid = torch.ones_like(scores, dtype=torch.bool)
    if valid.dtype != torch.bool or valid.shape != target.shape:
        raise ValueError("Invalid superpoint padding mask")
    if query_valid.dtype != torch.bool or query_valid.shape != scores.shape:
        raise ValueError("Invalid query padding mask")
    # Slice first: padded NaNs must never enter a normalization or zero anchor.
    masks = masks[query_valid][:, valid]
    scores = scores[query_valid]
    xyz = xyz[valid].detach()
    target = target[valid].detach()
    dtype = torch.float64 if masks.dtype == torch.float64 else torch.float32
    with torch.autocast(device_type=masks.device.type, enabled=False):
        masks, scores = masks.to(dtype), scores.to(dtype)
        xyz, target = xyz.to(dtype), target.to(dtype)
        if not all(torch.isfinite(v).all() for v in (masks, scores, xyz, target)):
            raise ValueError("Nonfinite valid inputs")
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
        losses = []
        for axis in range(3):
            order = torch.argsort(xyz[:, axis], stable=True)
            gaps = torch.diff(xyz[order, axis]) / diameter
            prefix = difference[order].cumsum(0)[:-1]
            losses.append((gaps * prefix.abs()).sum())
        return torch.stack(losses).mean(), "valid"


def main():
    torch.set_num_threads(1)
    torch.manual_seed(1999)
    rng = np.random.default_rng(1999)
    xyz = torch.tensor(rng.normal(size=(9, 3)), dtype=torch.float64)
    masks = torch.tensor(rng.normal(size=(4, 9)), requires_grad=True)
    scores = torch.tensor(rng.normal(size=4), requires_grad=True)
    target = torch.tensor([1., 1, 0, 0, 0, 0, 0, 0, 0], dtype=torch.float64)
    reference = objective(masks.detach().numpy(), scores.detach().numpy(),
                          xyz.numpy(), target.numpy())
    loss, status = spatial_transport(masks, scores, xyz, target)
    assert status == "valid"
    torch.testing.assert_close(loss, torch.tensor(reference[0]), rtol=1e-10, atol=1e-12)
    grads = torch.autograd.grad(loss, (masks, scores))
    for got, expected in zip(grads, reference[1:]):
        torch.testing.assert_close(got, torch.tensor(expected), rtol=1e-9, atol=1e-12)
    checks = ["float64_reference_and_autograd"]

    padded_m = F.pad(masks.detach(), (0, 3, 0, 2), value=float("nan")).requires_grad_()
    padded_s = F.pad(scores.detach(), (0, 2), value=float("nan")).requires_grad_()
    padded_x = F.pad(xyz, (0, 0, 0, 3), value=float("nan"))
    padded_y = F.pad(target, (0, 3), value=float("nan"))
    valid = torch.arange(12) < 9
    query_valid = torch.arange(6) < 4
    padded_loss, _ = spatial_transport(
        padded_m, padded_s, padded_x, padded_y, valid, query_valid)
    torch.testing.assert_close(padded_loss, loss)
    padded_loss.backward()
    assert torch.isfinite(padded_m.grad).all() and torch.isfinite(padded_s.grad).all()
    assert (padded_m.grad[4:] == 0).all() and (padded_m.grad[:, 9:] == 0).all()
    assert (padded_s.grad[4:] == 0).all()
    checks.append("nan_padding_excluded_before_normalization_zero_padding_grad")

    for label, m, s, x, y in [
        ("no_queries", masks[:0], scores[:0], xyz, target),
        ("no_superpoints", masks[:, :0], scores, xyz[:0], target[:0]),
        ("no_target", masks, scores, xyz, target * 0),
        ("zero_extent", masks, scores, xyz * 0, target),
    ]:
        val, why = spatial_transport(m, s, x, y)
        assert why == label and val.item() == 0 and val.requires_grad
        gs = torch.autograd.grad(val, (masks, scores), allow_unused=True)
        assert all(g is None or torch.equal(g, torch.zeros_like(g)) for g in gs)
    checks.append("empty_inputs_and_target_zero_extent_connected_zero")

    perm = torch.randperm(9)
    for m, s, x, y in [
        (masks[:, perm], scores, xyz[perm], target[perm]),
        (masks, scores, xyz * 7 + 12, target),
        (masks, scores, -xyz[:, [2, 0, 1]], target),
        (masks.repeat(2, 1), scores.repeat(2), xyz, target),
    ]:
        torch.testing.assert_close(spatial_transport(m, s, x, y)[0], loss)
    checks.append("permutation_similarity_reflection_whole_bank_replication")

    identical = masks[:1].detach().repeat(4, 1).requires_grad_()
    iloss, _ = spatial_transport(identical, scores, xyz, target)
    igrad = torch.autograd.grad(iloss, scores)[0]
    assert igrad.abs().max() < 1e-14
    checks.append("identical_mask_selector_gradient_null")
    for offset in (-1000, 1000):
        eloss, _ = spatial_transport(masks + offset, scores + offset, xyz, target)
        egrads = torch.autograd.grad(eloss, (masks, scores))
        assert torch.isfinite(eloss) and all(torch.isfinite(g).all() for g in egrads)
    checks.append("extreme_logits_finite_loss_and_backward")

    fm, fs = masks.detach().float().requires_grad_(), scores.detach().float().requires_grad_()
    with torch.autocast("cpu", dtype=torch.bfloat16):
        aloss, _ = spatial_transport(fm, fs, xyz.float(), target.float())
    aloss.backward()
    assert aloss.dtype == torch.float32
    torch.testing.assert_close(aloss.double(), loss, rtol=1e-5, atol=1e-7)
    assert torch.isfinite(fm.grad).all() and torch.isfinite(fs.grad).all()
    checks.append("cpu_bfloat16_autocast_fp32_loss_island")

    invalid = xyz.clone()
    invalid[0, 0] = float("nan")
    try:
        spatial_transport(masks, scores, invalid, target)
    except ValueError:
        pass
    else:
        raise AssertionError("Valid nonfinite inputs silently accepted")
    checks.append("valid_nan_rejected")

    # Two disjoint joint supports have equal marginals, including at hard inference.
    square = torch.tensor([[0., 0, 0], [1, 1, 0], [0, 1, 0], [1, 0, 0]])
    wrong = torch.tensor([[80., 80, -80, -80]])
    square_target = torch.tensor([0., 0, 1, 1])
    null, _ = spatial_transport(wrong, torch.zeros(1), square, square_target)
    assert null.abs() < 1e-10
    hard = wrong[0] > 0
    hard_iou = ((hard & square_target.bool()).sum()
                / (hard | square_target.bool()).sum())
    assert hard_iou == 0
    checks.append("zero_transport_disjoint_hard_mask_counterexample")
    print(json.dumps({
        "status": "PASS", "torch": torch.__version__, "device": "cpu",
        "checks": checks, "count": len(checks), "reference_loss": loss.item(),
        "max_autograd_error": max(float((g - torch.tensor(r)).abs().max())
                                  for g, r in zip(grads, reference[1:])),
        "marginal_null_loss": null.item(), "marginal_null_hard_iou": hard_iou.item(),
        "not_tested": ["CUDA AMP", "production integration", "real data batch",
                       "DDP global valid-count reduction", "full-model FLOPs",
                       "bs1 warmup20 repeat100 latency and peak memory",
                       "training efficacy", "application novelty"],
    }, indent=2))


if __name__ == "__main__":
    main()
