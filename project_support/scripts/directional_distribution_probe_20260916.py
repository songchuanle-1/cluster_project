"""Native differentiable sorted relation primitive; no production model edit."""
import hashlib
import json
from pathlib import Path
import numpy as np
import torch


def ordered_mass(z, target, anchor):
    """P(Z_target < Z_anchor), with strict ties and normalized positive masses."""
    if z.ndim != 1 or target.shape != z.shape or anchor.shape != z.shape:
        raise ValueError("Expected aligned one-dimensional support and masses")
    if not torch.isfinite(z).all() or not torch.isfinite(target).all() or not torch.isfinite(anchor).all():
        raise ValueError("Nonfinite support/mass")
    if (target < 0).any() or (anchor < 0).any():
        raise ValueError("Negative mass")
    if not len(z) or target.sum() == 0 or anchor.sum() == 0:
        return (target.sum() + anchor.sum()) * 0
    order = torch.argsort(z)
    heights, t, a = z[order], target[order], anchor[order]
    # Equal coordinates share the prefix BEFORE the whole tie group.
    first = torch.searchsorted(heights, heights, right=False)
    prefix = torch.cat((a.new_zeros(1), a.cumsum(0)))
    after = a.sum() - prefix[torch.searchsorted(heights, heights, right=True)]
    assert first.shape == after.shape
    return (t * after).sum() / (t.sum() * a.sum())


def main():
    torch.set_num_threads(1)
    torch.manual_seed(1999)
    device = "cuda"
    z = torch.tensor([2., 0., 1., 1., 3.], dtype=torch.float64, device=device)
    t = torch.rand(5, dtype=torch.float64, device=device, requires_grad=True) + .1
    a = torch.rand(5, dtype=torch.float64, device=device, requires_grad=True) + .1
    slow = (t[:, None]*a[None, :]*(z[:, None] < z[None, :])).sum()/(t.sum()*a.sum())
    fast = ordered_mass(z, t, a)
    assert torch.allclose(slow, fast, atol=1e-12)
    gs = torch.autograd.grad(slow, (t, a), retain_graph=True)
    gf = torch.autograd.grad(fast, (t, a), retain_graph=True)
    error = max(float((x-y).abs().max()) for x, y in zip(gs, gf))
    assert error < 1e-12
    assert torch.autograd.gradcheck(lambda x,y: ordered_mass(z,x,y), (t,a))
    permutation = torch.tensor([4, 2, 0, 3, 1], device=device)
    assert torch.allclose(fast, ordered_mass(z[permutation], t[permutation], a[permutation]))
    assert torch.allclose(fast, ordered_mass(z*3+11, t, a))
    assert torch.allclose(fast, ordered_mass(z, t*7, a*2))
    reverse = ordered_mass(z, a, t)
    tie = (t[:, None]*a[None, :]*(z[:, None] == z[None, :])).sum()/(t.sum()*a.sum())
    assert torch.allclose(fast+reverse+tie, fast.new_tensor(1.))
    empty = ordered_mass(z, t*0, a)
    assert empty == 0 and torch.isfinite(torch.autograd.grad(empty, (t,a))[0]).all()
    # Same centroid, different distributions; not proof of semantic superiority.
    zz = torch.tensor([-2., 0., 1., 2.], dtype=torch.float64, device=device)
    aa = torch.tensor([0., 0., 1., 0.], dtype=torch.float64, device=device)
    t1 = torch.tensor([.5, 0., 0., .5], dtype=torch.float64, device=device)
    t2 = torch.tensor([0., 1., 0., 0.], dtype=torch.float64, device=device)
    assert (zz*t1).sum() == (zz*t2).sum()
    assert ordered_mass(zz,t1,aa) != ordered_mass(zz,t2,aa)

    root = Path("/data3/songcl/Project/Cluster_project")
    source = root / "pipeline/vertical_relation_bounds_20260916/result.json"
    results = []
    for row in json.loads(source.read_text())["rows"]:
        if not row.get("anchors"):
            continue
        raw = Path("/data3/songcl/data/data_cluster/scannetv2/train")/(row["scene"]+"_refer.pth")
        xyz, _, _, _, ids = torch.load(raw, weights_only=False, map_location="cpu")
        xyz, ids = np.asarray(xyz), np.asarray(ids)
        # Identity lookup, not outcome-specific anchor selection.
        binding = json.loads((root/"pipeline/entity_binding_20260916/result.json").read_text())["rows"]
        meta = next(r for r in binding if r["scene"]==row["scene"] and r["ann_id"]==row["ann_id"])
        direction = -1 if row["relation"]=="above" else 1
        if not row["target_first"]:
            direction *= -1
        pairs = []
        for anchor in row["anchors"]:
            pair = dict(anchor=anchor)
            for role in ("target", "winner"):
                identity = meta[role]
                if identity == anchor:
                    pair[role] = None
                    continue
                hz = torch.as_tensor(xyz[ids==identity,2]*direction, device=device).double()
                az = torch.as_tensor(xyz[ids==anchor,2]*direction, device=device).double()
                support = torch.cat((hz, az))
                tw = torch.cat((torch.ones_like(hz), torch.zeros_like(az)))
                aw = 1-tw
                pair[role] = float(ordered_mass(support, tw, aw))
            pairs.append(pair)
        results.append(dict(scene=row["scene"], ann_id=row["ann_id"],
                            confident_wrong=row["confident_wrong"], pairs=pairs))
    output = root/"pipeline/directional_distribution_20260916"
    output.mkdir(exist_ok=True)
    report = dict(
        controls=dict(value_and_gradient_equivalence=True, gradcheck=True,
                      permutation=True, monotone_affine=True, mass_scale=True,
                      strict_ties=True, empty_connected_zero=True,
                      equal_centroid_distinction=True, gradient_max_error=error),
        rows=results, device=torch.cuda.get_device_name(),
        sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__),source)},
        complexity="O(NlogN) sorting,O(N) memory; small dense oracle only in test.",
        limitations="Ordered pair probability is a standard distribution statistic, "
        "not claimed novelty. No horizontal proximity,anchor identity or relational "
        "semantic truth. Raw point density weights surfaces nonuniformly. No fullmodel "
        "resources/backward or admission;synthetic gradients only.")
    (output/"result.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(controls=report["controls"],edges=len(results),
                         wrong=[r for r in results if r["confident_wrong"]])),flush=True)


if __name__ == "__main__":
    main()
