"""Isolated CUDA prototype for proposed distributional instance read."""
import hashlib
import json
from pathlib import Path
import torch
import torch.nn.functional as F


def relations(z, target, instances):
    """QxKx2 strict ordered mass, with no SxS tensor."""
    order = z.argsort(stable=True)
    heights = z[order]
    t = target[:, order]
    p = instances[:, order]
    t = t / t.sum(-1, keepdim=True).clamp_min(torch.finfo(t.dtype).tiny)
    p = p / p.sum(-1, keepdim=True).clamp_min(torch.finfo(p.dtype).tiny)
    prefix = F.pad(p.cumsum(-1), (1, 0))
    lo = prefix[:, torch.searchsorted(heights, heights, right=False)]
    hi = p.sum(-1, keepdim=True) - prefix[:, torch.searchsorted(heights, heights, right=True)]
    return torch.stack((t @ hi.T, t @ lo.T), -1)


def read(q, features, instance_logits, target_logits, z, relation_projection):
    p, t = instance_logits.sigmoid(), target_logits.sigmoid()
    p = p / p.sum(-1, keepdim=True)
    values = p @ features
    rel = relations(z, t, p)
    affinity = q @ values.T / q.shape[-1] ** .5
    affinity = affinity + torch.einsum("qr,qkr->qk", q @ relation_projection, rel)
    return affinity.softmax(-1) @ values, rel


def main():
    torch.set_num_threads(1)
    torch.manual_seed(1999)
    device, dtype = "cuda", torch.float64
    z = torch.tensor([0., 1., 1., 2., 3.], device=device, dtype=dtype)
    a = torch.randn(3, 5, device=device, dtype=dtype, requires_grad=True)
    b = torch.randn(2, 5, device=device, dtype=dtype, requires_grad=True)
    features = torch.randn(5, 4, device=device, dtype=dtype, requires_grad=True)
    q = torch.randn(2, 4, device=device, dtype=dtype, requires_grad=True)
    w = torch.randn(4, 2, device=device, dtype=dtype, requires_grad=True)
    output, rel = read(q, features, a, b, z, w)
    p, t = a.sigmoid(), b.sigmoid()
    p, t = p / p.sum(-1, keepdim=True), t / t.sum(-1, keepdim=True)
    dense = torch.stack((t @ (z[:, None] < z[None, :]).to(dtype) @ p.T,
                         t @ (z[:, None] > z[None, :]).to(dtype) @ p.T), -1)
    torch.testing.assert_close(rel, dense, atol=1e-12, rtol=1e-12)
    grads = torch.autograd.grad(output.square().sum(), (q, features, a, b, w),
                                retain_graph=True)
    assert all(torch.isfinite(g).all() and g.abs().sum() > 0 for g in grads)
    assert torch.autograd.gradcheck(
        lambda aa, bb: read(q.detach(), features.detach(), aa, bb, z, w.detach())[0],
        (a, b))
    permutation = torch.tensor([3, 0, 4, 1, 2], device=device)
    out2, _ = read(q, features[permutation], a[:, permutation], b[:, permutation],
                   z[permutation], w)
    torch.testing.assert_close(output, out2, atol=1e-12, rtol=1e-12)
    ip = torch.tensor([2, 0, 1], device=device)
    out3, _ = read(q, features, a[ip], b, z, w)
    torch.testing.assert_close(output, out3, atol=1e-12, rtol=1e-12)
    owner_truth = F.one_hot(torch.tensor([0, 0, 1, 1, 2], device=device), 3).T.to(dtype)
    owner_loss = F.binary_cross_entropy_with_logits(a, owner_truth)
    owner_grads = torch.autograd.grad(owner_loss, (a, b), allow_unused=True)
    assert owner_grads[1] is None and owner_grads[0].abs().sum() > 0
    target_truth = torch.tensor([[0., 0., 1., 1., 0.], [1., 1., 0., 0., 0.]],
                                device=device, dtype=dtype)
    target_loss = F.binary_cross_entropy_with_logits(b, target_truth)
    target_grads = torch.autograd.grad(target_loss, (a, b), allow_unused=True)
    assert target_grads[0] is None and target_grads[1].abs().sum() > 0
    # Repeated physical instances are not neutral under ordinary softmax reads.
    duplicate_a = torch.cat((a, a[:1]), 0)
    duplicated, _ = read(q, features, duplicate_a, b, z, w)
    duplicate_delta = float((duplicated-output).abs().max())
    assert duplicate_delta > 1e-8
    empty_rel = relations(z, torch.zeros_like(b), a.sigmoid())
    assert torch.count_nonzero(empty_rel) == 0
    result = dict(
        checks=dict(dense_relation_equivalence=True, nonzero_finite_gradients=True,
                    cuda_gradcheck=True, point_permutation=True, instance_permutation=True,
                    direct_mask_loss_separation=True, empty_target_mass=True),
        dense_max_error=float((rel-dense).abs().max()),
        gradient_l1={name: float(g.abs().sum()) for name, g in zip(
            ("query", "features", "instance_mask", "target_mask", "relation_projection"), grads)},
        duplicate_instance_read_max_delta=duplicate_delta,
        limitation="Synthetic CUDA computation only. Ordinary softmax read changes under "
                   "duplicate instance proposals. This is unresolved for native seed multiplicity, "
                   "not evidence of actual accuracy loss. Shared backbone gradients can conflict. "
                   "No complete model, resource clearance or novelty admission.",
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out = Path("/data3/songcl/Project/Cluster_project/pipeline/instance_distribution_prototype_20260916")
    out.mkdir(exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
