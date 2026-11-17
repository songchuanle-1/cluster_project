"""CPU replay of current seed assignment on immutable evaluation banks."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import resource
import time
from types import SimpleNamespace

os.environ["CUDA_VISIBLE_DEVICES"] = ""
import numpy as np
import torch
import torch_scatter


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024**2), b""):
            h.update(block)
    return h.hexdigest()


def key(row):
    return row["scene_id"], str(row["object_id"]), str(row["ann_id"])


def methods(path, names):
    tree = ast.parse(Path(path).read_text())
    nodes = [n for c in tree.body if isinstance(c, ast.ClassDef)
             for n in c.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    scope = dict(torch=torch, np=np, torch_scatter=torch_scatter)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), scope)
    obj = SimpleNamespace(eos_coef=.1)
    for n in names:
        setattr(obj, n, scope[n].__get__(obj))
    return obj


def gradient_check(obj, scores, labels):
    scores = scores.float().clone().requires_grad_(True)
    indices = [(labels.nonzero().flatten(), torch.zeros(int(labels.sum()), dtype=torch.long))]
    loss = obj.loss_indi(scores[None], None, indices, int(labels.sum()))
    grad, = torch.autograd.grad(loss, scores)
    p = scores.softmax(-1)[:, 1]
    w = torch.where(labels, 1., obj.eos_coef).float()
    expected = w * (p - labels.float()) / labels.sum()
    assert torch.allclose(grad[:, 1], expected, atol=1e-7, rtol=1e-5)
    assert torch.allclose(grad[:, 0], -expected, atol=1e-7, rtol=1e-5)
    assert (grad[~labels, 1] >= 0).all() and (grad[labels, 1] <= 0).all()
    return float((grad[:, 1] - expected).abs().max()), grad.detach(), float(loss)


def synthetic(ds, obj):
    sp = torch.tensor([0, 0, 1, 1, 2, 2, 3, 3])
    ins = torch.tensor([3, 3, 3, 4, -1, -1, 4, 4])
    label, _ = ds.get_sp_label(sp, ins, torch.zeros_like(ins))
    assert label.tolist() == [3, 199, -1, 4]
    coords = torch.tensor([[0., 0, 0], [1., 0, 0], [2., 0, 0], [3., 0, 0]])
    def assignment(lbl, x, mu):
        return obj.match_sampled_ins(lbl, [3], x, mu)[2][0]
    ids = assignment(label, coords, torch.tensor([[1.1, 0, 0]]))
    assert set(ids.tolist()) == {0, 1} and len(ids) == 2
    assert assignment(label, coords, torch.zeros(1, 3)).tolist() == [0]
    perm = torch.tensor([2, 0, 3, 1])
    assert set(perm[assignment(label[perm], coords[perm], torch.tensor([[1.1, 0, 0]]))].tolist()) == {0, 1}
    y = torch.tensor([True, True, False, False])
    z = torch.tensor([[.2, -.1], [.5, .7], [-.2, .8], [1., -1.]])
    error, grad, _ = gradient_check(obj, z, y)
    eps = 1e-2
    ix = [(y.nonzero().flatten(), torch.zeros(2, dtype=torch.long))]
    plus, minus = z.clone(), z.clone()
    plus[2, 1] += eps
    minus[2, 1] -= eps
    fd = (obj.loss_indi(plus[None], None, ix, 2) -
          obj.loss_indi(minus[None], None, ix, 2)) / (2 * eps)
    assert abs(float(fd) - float(grad[2, 1])) < 1e-5
    quality = torch.tensor([0., 0., .9, .8])
    assert not ((quality > .5) & y).any() and (grad[quality > .5, 1] > 0).all()
    return dict(checks=8, status="passed", max_gradient_error=error)


def main():
    parser = argparse.ArgumentParser()
    for name in ("protocol", "code-root", "banks", "data-root", "out"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    output, root, data, banks = map(Path, (args.out, args.code_root, args.data_root, args.banks))
    assert not output.exists()
    protocol = json.loads(Path(args.protocol).read_text())
    for rel, digest in protocol["source_hashes"].items():
        assert sha(root / rel) == digest
    torch.set_num_threads(1)
    ds = methods(root / "framework/dataset/scannetv2.py", ["get_sp_label"])
    criteria = {name: methods(root / m["loss_path"],
                            ["match_sampled_ins", "_get_src_permutation_idx", "loss_indi"])
                for name, m in protocol["models"].items()}
    for name, obj in criteria.items():
        obj.eos_coef = protocol["models"][name]["eos_coef"]
    tests = {n: synthetic(ds, obj) for n, obj in criteria.items()}
    summaries = {n: json.loads((banks / n / "summary.json").read_text()) for n in criteria}
    for n, s in summaries.items():
        assert sha(banks / n / "summary.json") == protocol["summary_hashes"][n]
        assert s["manifest_sha256"] == protocol["manifest_sha256"]
    selected = {tuple(v) for v in protocol["ids"]}
    assert len(selected) == 284
    assert all({key(r) for r in s["rows"]} == selected for s in summaries.values())
    rows, scenes = [], []
    start = time.monotonic()
    for scene in sorted({k[0] for k in selected}):
        assert time.monotonic() - start < 600
        raw = data / "scannetv2/val" / f"{scene}_refer.pth"
        digest = sha(raw)
        assert all(s["input_hashes"][str(raw.relative_to(data))] == digest for s in summaries.values())
        xyz, _, sp, sem, ins = torch.load(raw, map_location="cpu", weights_only=False)
        _, mapping = np.unique(sp, return_inverse=True)
        mapping, ins, sem = torch.tensor(mapping), torch.tensor(ins), torch.tensor(sem)
        labels, _ = ds.get_sp_label(mapping, ins, sem)
        # Independent per-superpoint majority via counts, including ignored instance IDs.
        counts = np.bincount(mapping.numpy())
        independent = np.full(len(counts), 199)
        for inst in np.unique(ins.numpy()):
            votes = np.bincount(mapping[ins == inst].numpy(), minlength=len(counts))
            independent[2 * votes > counts] = inst
        assert np.array_equal(labels.numpy(), independent)
        centroids = torch_scatter.scatter_mean(torch.tensor(xyz).float(), mapping, dim=0)
        scenes.append(dict(scene_id=scene, raw_sha256=digest, points=len(ins), superpoints=len(labels)))
        for name, summary in summaries.items():
            obj = criteria[name]
            for r in summary["rows"]:
                if r["scene_id"] != scene:
                    continue
                file = banks / name / r["artifact"]
                assert sha(file) == r["artifact_sha256"]
                b = torch.load(file, map_location="cpu", weights_only=False)
                assert key(b["identity"]) == key(r)
                target = int(r["object_id"])
                assert torch.equal(b["superpoints"], mapping)
                assert torch.equal(b["gt_pmask"] > .5, ins == target)
                assert torch.equal(b["gt_spmask"] > .5, labels == target)
                record = dict(model=name, **b["identity"], bank_sha256=r["artifact_sha256"])
                if not (labels == target).any():
                    rows.append(dict(**record, status="missing_target_majority_centroid"))
                    continue
                seed, sample = b["seed_indices"].long(), b["sample_indices"].long()
                query_sp = seed[sample]
                qlabels, qpos = labels[query_sp], centroids[query_sp]
                mu = torch_scatter.scatter_mean(centroids, (labels == target).long(), dim=0)[1:2]
                nearest, _, matched, _ = obj.match_sampled_ins(qlabels, [target], qpos, mu)
                y = torch.zeros(len(sample), dtype=torch.bool)
                y[matched[0]] = True
                d64 = torch.linalg.vector_norm(qpos.double() - mu.double(), dim=1)
                d32 = torch.cdist(qpos, mu).flatten()
                expected = qlabels == target
                expected[nearest] = True
                assert torch.equal(y, expected) and len(matched[0]) == int(y.sum())
                gradient_error, grad, loss = gradient_check(obj, b["score_logits"], y)
                u = np.asarray(r["candidate_ious"])
                assert len(u) == 128 == len(y)
                good = u > .5
                pos = y.numpy()
                si, oi = r["selected_index"], r["oracle_index"]
                assert int(b["score_logits"].softmax(-1)[:, 1].argmax()) == si
                assert oi == int(u.argmax())
                rec = r["selected_iou"] <= .5 < r["oracle_iou"]
                rows.append(dict(
                    **record, status="complete", positive_indices=y.nonzero().flatten().tolist(),
                    query_sp=query_sp.tolist(), query_instance_labels=qlabels.tolist(),
                    nearest=int(nearest[0]), nearest_in_target=bool(qlabels[nearest[0]] == target),
                    nearest_tie_count=int((d32 == d32.min()).sum()),
                    nearest_float64_agrees=int(d64.argmin()) == int(nearest[0]),
                    nearest_float64_margin=float(d64.sort().values[1] - d64.min()),
                    positive_usable=int((pos & good).sum()), negative_usable=int((~pos & good).sum()),
                    positive_unusable=int((pos & ~good).sum()), negative_unusable=int((~pos & ~good).sum()),
                    selected_positive=bool(pos[si]), oracle_positive=bool(pos[oi]),
                    selected_iou=float(u[si]), oracle_iou=float(u[oi]),
                    positive_oracle=float(u[pos].max()),
                    negative_oracle=float(u[~pos].max()) if (~pos).any() else None,
                    recoverable=bool(rec), no_usable_positive=bool(good.any() and not (good & pos).any()),
                    all_usable_oracles_negative=bool(not (pos & (u == u.max())).any()),
                    gradients_z1=grad[:, 1].tolist(), gradient_error=gradient_error,
                    discriminator_loss=loss))
    assert len(rows) == 568
    assert not torch.cuda.is_initialized()
    result = dict(status="complete", protocol_sha256=sha(args.protocol),
                  worker_sha256=sha(__file__), tests=tests, scenes=scenes, rows=rows,
                  elapsed_seconds=time.monotonic() - start,
                  peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                  cuda_initialized=torch.cuda.is_initialized(),
                  limit="Current CPU assignment applied to evaluation candidates; not historical training targets or causal evidence.")
    output.mkdir()
    (output / "assignment.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ("rows", "scenes")}, indent=2))


if __name__ == "__main__":
    main()
