"""CPU-only source-label and final-head gradient audit; no training writes."""
import argparse
import json
import os
from pathlib import Path
import resource
import time

os.environ["CUDA_VISIBLE_DEVICES"] = ""
import numpy as np
import torch
import torch.nn.functional as F
import torch_scatter

from d1_assignment_20260911 import key, methods, sha, synthetic


def flat_grad(value, params):
    return torch.cat([g.flatten() for g in torch.autograd.grad(
        value, params, retain_graph=True)])


def logits(q, params):
    w0, b0, w2, b2, w3, b3 = params
    return F.linear(F.linear(F.relu(F.linear(q, w0, b0)), w2, b2), w3, b3)


def perturbed(params, direction, epsilon):
    result, offset = [], 0
    for param in params:
        size = param.numel()
        result.append(param.detach() + epsilon * direction[offset:offset + size].view_as(param))
        offset += size
    assert offset == direction.numel()
    return result


def project(a, delta):
    norm2 = a.dot(a)
    violation = a.dot(delta)
    if float(norm2) == 0 or float(violation) <= 0:
        return delta.clone()
    return delta - violation / norm2 * a


def projection_tests():
    a = torch.tensor([1., 2.], dtype=torch.double)
    delta = torch.tensor([2., 1.], dtype=torch.double)
    p = project(a, delta)
    assert abs(float(a.dot(p))) < 1e-12
    assert torch.equal(project(a, -a), -a)
    assert torch.equal(project(torch.zeros_like(a), delta), delta)
    assert torch.allclose(project(a, p), p)
    return 4


def derivatives(q, params, obj, y, selected, usable):
    z = logits(q, params)
    d = z[:, 1] - z[:, 0]
    pos = int(y.sum())
    # Source constructs eos weights as float32 even with double logits.
    weights = torch.where(y, 1., obj.eos_coef).float().double()
    terms = weights * F.binary_cross_entropy_with_logits(
        d, y.double(), reduction="none") / pos
    c = weights * (d.sigmoid() - y.double()) / pos
    independent_loss = terms.sum()
    native_z = z.detach().float().requires_grad_(True)
    indices = [(y.nonzero().flatten(), torch.zeros(pos, dtype=torch.long))]
    native_loss = obj.loss_indi(native_z[None], None, indices, pos)
    native_grad, = torch.autograd.grad(native_loss, native_z)
    gradient_error = float((native_grad[:, 1].double() - c.detach()).abs().max())
    entropy_constant = float(weights.sum() * np.log(1 + 1e-6) / pos)
    value_error = abs(float(native_loss) - float(independent_loss.detach()) - entropy_constant)
    assert gradient_error < 2e-7 and value_error < 2e-5
    record = dict(source_logit_gradient_max_error=gradient_error,
                  source_loss_value_error=value_error,
                  source_loss=float(native_loss.detach()))
    if not usable.any():
        return dict(**record, pair_status="no_usable_positive")
    h = int(d.detach().masked_fill(~usable, -torch.inf).argmax())
    a = flat_grad(d[selected] - d[h], params)
    g = flat_grad(independent_loss, params)
    pair = torch.zeros_like(y)
    pair[selected] = True
    pair[h] = True
    groups = (pair, ~pair & y, ~pair & ~y)
    gradients = [flat_grad(terms[group].sum(), params) for group in groups]
    velocities = [-float(a.dot(gg)) for gg in gradients]
    velocity = -float(a.dot(g))
    error = abs(velocity - sum(velocities))
    assert error < 1e-8 * (1 + abs(velocity))
    native_vjp = flat_grad((z * native_grad.double()).sum(), params)
    source_velocity = -float(a.dot(native_vjp))
    projected = project(a, -g)
    projected_velocity = float(a.dot(projected))
    assert projected_velocity <= 1e-9 * (1 + float(a.norm() * g.norm()))
    assert torch.allclose(project(a, projected), projected, atol=1e-9, rtol=1e-8)
    direction = -g / max(float(g.norm()), 1.)
    predicted = float(a.dot(direction))
    finite_differences = []
    for eps in (1e-4, 1e-5):
        with torch.no_grad():
            plus = logits(q, perturbed(params, direction, eps))
            minus = logits(q, perturbed(params, direction, -eps))
            def margin(v):
                return v[selected, 1] - v[selected, 0] - v[h, 1] + v[h, 0]
            fd = float((margin(plus) - margin(minus)) / (2 * eps))
            finite_differences.append(dict(epsilon=eps, observed=fd,
                                           abs_error=abs(fd - predicted)))
    # Reversing order must preserve the total objective and head gradient.
    perm_terms = weights.flip(0) * F.binary_cross_entropy_with_logits(
        d.flip(0), y.double().flip(0), reduction="none") / pos
    perm_g = flat_grad(perm_terms.sum(), params)
    assert torch.allclose(g, perm_g, atol=1e-10, rtol=1e-9)
    zero_a = flat_grad(d[selected] - d[selected], params)
    assert torch.count_nonzero(zero_a) == 0
    return dict(
        **record, pair_status="zero_pair" if selected == h else "informative",
        positive_index=h, margin=float((d[selected] - d[h]).detach()),
        v_head=velocity, v_source_float32_vjp=source_velocity,
        v_pair=velocities[0], v_other_positive=velocities[1],
        v_other_negative=velocities[2], decomposition_error=error,
        v_independent_two_logits=float((-2 * (c[selected] - c[h])).detach()),
        rest_bank_reversal=velocities[0] < -1e-9 and velocity > 1e-9,
        projected_velocity=projected_velocity, head_grad_norm=float(g.norm()),
        margin_grad_norm=float(a.norm()), finite_difference_predicted=predicted,
        finite_differences=finite_differences,
        finite_difference_flag=finite_differences[-1]["abs_error"] > 1e-5 * (1 + abs(predicted)))


def main():
    parser = argparse.ArgumentParser()
    for name in ("protocol", "code-root", "data-root", "capture", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    start = time.monotonic()
    resource.setrlimit(resource.RLIMIT_AS, (16 * 1024**3, 16 * 1024**3))
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    output, root, data, capture = map(Path, (args.output, args.code_root, args.data_root, args.capture))
    assert not output.exists()
    protocol = json.loads(Path(args.protocol).read_text())
    for rel, digest in protocol["source_hashes"].items():
        assert sha(root / rel) == digest, rel
    assert sha(capture / "summary.json") == protocol["capture_summary_sha256"]
    summary = json.loads((capture / "summary.json").read_text())
    assert summary["manifest_sha256"] == protocol["manifest_sha256"]
    assert len(summary["rows"]) == len({key(r) for r in summary["rows"]}) == 284
    assert {key(r) for r in summary["rows"]} == {tuple(k) for k in protocol["ids"]}
    checkpoint = protocol["checkpoint"]
    assert sha(checkpoint) == protocol["checkpoint_sha256"]
    assert sha(protocol["checkpoint_config"]) == protocol["checkpoint_config_sha256"]
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    prefix = "dec.decoder_layers.5.indi_embedding."
    names = ["0.weight", "0.bias", "2.weight", "2.bias", "3.weight", "3.bias"]
    params = [state[prefix + n].double().clone().requires_grad_(True) for n in names]
    del state
    ds = methods(root / "framework/dataset/scannetv2.py", ["get_sp_label"])
    obj = methods(root / protocol["loss_path"],
                  ["loss_indi", "_get_src_permutation_idx", "match_sampled_ins"])
    obj.eos_coef = protocol["eos_coef"]
    tests = dict(source_assignment=synthetic(ds, obj), projection=projection_tests())
    rows, scenes = [], []
    for scene in sorted({r["scene_id"] for r in summary["rows"]}):
        assert time.monotonic() - start < 840
        raw = data / "scannetv2/val" / f"{scene}_refer.pth"
        digest = sha(raw)
        assert digest == protocol["input_hashes"][str(raw.relative_to(data))]
        xyz, _, sp, sem, ins = torch.load(raw, map_location="cpu", weights_only=False)
        _, mapping = np.unique(sp, return_inverse=True)
        mapping = torch.tensor(mapping)
        ins, sem = torch.as_tensor(ins), torch.as_tensor(sem)
        labels, _ = ds.get_sp_label(mapping, ins, sem)
        counts = np.bincount(mapping.numpy())
        independent = np.full(len(counts), 199)
        for inst in np.unique(ins.numpy()):
            votes = np.bincount(mapping[ins == inst].numpy(), minlength=len(counts))
            independent[2 * votes > counts] = inst
        assert np.array_equal(labels.numpy(), independent)
        centroids = torch_scatter.scatter_mean(torch.as_tensor(xyz).float(), mapping, dim=0)
        scenes.append(dict(scene_id=scene, raw_sha256=digest))
        for r in summary["rows"]:
            if r["scene_id"] != scene:
                continue
            artifact = capture / r["artifact"]
            assert sha(artifact) == r["artifact_sha256"]
            saved = torch.load(artifact, map_location="cpu", weights_only=False)
            assert key(saved["identity"]) == key(r)
            t = saved["tensors"]
            gt = t["gt_spmask"].bool().flatten()
            target = int(r["object_id"])
            assert torch.equal(t["superpoints"].flatten().long(), mapping)
            assert torch.equal(gt, labels == target)
            row = dict(**saved["identity"], artifact_sha256=r["artifact_sha256"])
            if not gt.any():
                rows.append(dict(**row, status="missing_target_majority_centroid"))
                continue
            query_sp = t["seed_indices"].long().flatten()[t["sample_indices"].long().flatten()]
            mu = torch_scatter.scatter_mean(centroids, gt.long(), dim=0)[1:2]
            nearest, _, matched, _ = obj.match_sampled_ins(
                labels[query_sp], [target], centroids[query_sp], mu)
            y = torch.zeros(len(query_sp), dtype=torch.bool)
            y[matched[0]] = True
            expected = labels[query_sp] == target
            expected[nearest] = True
            assert torch.equal(y, expected)
            q = t["query"].double()
            with torch.no_grad():
                z = logits(q, params)
                z32 = logits(q.float(), [v.float() for v in params])
                stored = t["indis_logits"].float()
                forward_error = float((z - stored).abs().max())
                assert forward_error < .03
                masks = t["mask_logits"].float()
                pred = masks.sigmoid() >= .5
                intersection = (pred & gt[None]).sum(1)
                union = (pred | gt[None]).sum(1)
                iou = intersection.float() / (union.float() + 1e-6)
                selected = int(r["indis_index"])
                # Preserve deployed selection; report numerical argmax discrepancies.
                si64 = int((z[:, 1] - z[:, 0]).argmax())
                si32 = int(z32.softmax(-1)[:, 1].argmax())
                usable = y & (iou > .5)
            info = derivatives(q, params, obj, y, selected, usable)
            rows.append(dict(
                **row, status="complete", **info, selected_index=selected,
                selected_positive=bool(y[selected]), positive_indices=y.nonzero().flatten().tolist(),
                query_sp=query_sp.tolist(), selected_iou=float(iou[selected]),
                oracle_iou=float(iou.max()), positive_usable=int(usable.sum()),
                recoverable=bool(iou[selected] <= .5 < iou.max()),
                success=bool(iou[selected] > .5), forward_max_error=forward_error,
                reconstructed_margin_argmax=si64, reconstructed_float32_argmax=si32,
                stored_float32_argmax=int(stored.softmax(-1)[:, 1].argmax()),
                reconstructed_margin_ties=int(((z[:, 1] - z[:, 0]) == (z[:, 1] - z[:, 0]).max()).sum()),
                mask_zero_entries=int((masks == 0).sum()),
                threshold_comparison_flips=int((pred != (masks > 0)).sum()),
                selected_iou_capture_error=abs(float(iou[selected]) - r["indis_iou"]),
                oracle_iou_capture_error=abs(float(iou.max()) - r["oracle_iou"])))
        print("SCENE", scene, "ROWS", len(rows), flush=True)
    assert len(rows) == 284 and not torch.cuda.is_initialized()
    assert sha(checkpoint) == protocol["checkpoint_sha256"]
    complete = [r for r in rows if r["status"] == "complete"]
    informative = [r for r in complete if r["pair_status"] == "informative"]
    rec = [r for r in complete if r["recoverable"]]
    def aggregate(rs):
        eligible = [r for r in rs if r["pair_status"] == "informative"]
        return dict(banks=len(rs), informative=len(eligible),
                    no_usable_positive=sum(r["pair_status"] == "no_usable_positive" for r in rs),
                    zero_pair=sum(r["pair_status"] == "zero_pair" for r in rs),
                    pair_correcting=sum(r["v_pair"] < -1e-9 for r in eligible),
                    head_correcting=sum(r["v_head"] < -1e-9 for r in eligible),
                    head_worsening=sum(r["v_head"] > 1e-9 for r in eligible),
                    rest_bank_reversals=sum(r["rest_bank_reversal"] for r in eligible),
                    independent_correcting=sum(r["v_independent_two_logits"] < -1e-9 for r in eligible))
    result = dict(
        status="complete", protocol_sha256=sha(args.protocol), worker_sha256=sha(__file__),
        tests=tests, rows=rows, scenes=scenes, aggregate=dict(all=aggregate(complete),
            recoverable=aggregate(rec), success=aggregate([r for r in complete if r["success"]])),
        finite_difference_flags=sum(r["finite_difference_flag"] for r in informative),
        selector_disagreements=sum(r["selected_index"] != r["reconstructed_float32_argmax"] for r in complete),
        float64_margin_selector_disagreements=sum(r["selected_index"] != r["reconstructed_margin_argmax"] for r in complete),
        elapsed_seconds=time.monotonic() - start,
        peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        cuda_initialized=torch.cuda.is_initialized(), outer_loss_weight=protocol["outer_loss_weight"],
        limit="Frozen eval query final head, source multi-positive CE smooth double extension with native float32 VJP check; not full training, auxiliary loss, Adam, efficacy or novelty.")
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ("rows", "scenes")}, indent=2))


if __name__ == "__main__":
    main()
