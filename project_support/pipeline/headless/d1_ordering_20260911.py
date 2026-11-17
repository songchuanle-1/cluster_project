"""CPU ranking diagnostics and source-extracted semantic-loss invariance tests."""
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


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024**2), b""):
            h.update(block)
    return h.hexdigest()


def key(r):
    return r["scene_id"], str(r["object_id"]), str(r["ann_id"])


def criterion(path):
    names = {"loss_sem_align", "_get_src_permutation_idx"}
    tree = ast.parse(Path(path).read_text())
    nodes = [n for c in tree.body if isinstance(c, ast.ClassDef)
             for n in c.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == names
    scope = dict(torch=torch)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), scope)
    obj = SimpleNamespace(temperature=.07, eos_coef=.1)
    for name in names:
        setattr(obj, name, scope[name].__get__(obj))
    return obj


def semantic_case(obj, padded=0, alternate=False, permutation=None):
    v = torch.eye(3, dtype=torch.float64)
    t = torch.tensor([[.6, .8, 0], [0, .6, .8], [.8, 0, .6], [1., 0, 0]],
                     dtype=torch.float64)
    if padded:
        extra = torch.tensor([[0., 1, 0], [0., 0, 1]], dtype=torch.float64)
        if alternate:
            extra = -extra
        t = torch.cat((t, extra))
    assert padded in (0, 2)
    assert torch.allclose(torch.linalg.vector_norm(t, dim=1), torch.ones(len(t), dtype=t.dtype))
    matched = 0
    if permutation is not None:
        v = v[permutation]
        matched = permutation.index(0)
    v, t = v[None].requires_grad_(True), t[None].requires_grad_(True)
    lang = torch.tensor([[1, 1, 1, 1] + [0] * padded])
    fields = ["positive_map", "modify_positive_map", "pron_positive_map", "other_entity_map", "rel_positive_map"]
    target = {f: torch.zeros(1, len(t[0])) for f in fields}
    target["positive_map"][0, 0] = 1
    indices = [(torch.tensor([matched]), torch.tensor([0]))]
    loss = obj.loss_sem_align(t, v, lang, [target], indices, 1)
    gv, gt = torch.autograd.grad(loss, (v, t))
    s = (v @ t.transpose(-1, -2) / obj.temperature).detach()
    a = torch.zeros_like(s, dtype=torch.float32)
    a[:, :, 2:4] = 1
    a[:, matched] = 0
    a[:, matched, 0] = 1
    w = torch.full((1, 3), obj.eos_coef)
    w[:, matched] = 1
    tw = torch.full((1, len(t[0])), obj.eos_coef)
    active = a.any(1)
    tw[active] = 1
    tw[:, 2] = .1
    nq = a.sum(2) + 1e-6
    ml = a.sum(1) + 1e-6
    entropy = -torch.log(ml + 1e-6) / ml
    independent_loss = (((-(a * s).sum(2) / nq + s.logsumexp(2)) * w).sum()
                        + ((entropy - (a * s).sum(1) / ml + s.logsumexp(1))
                           * tw * active).sum()) / 2
    g = (w[:, :, None] * (s.softmax(2) - a / nq[:, :, None])
         + (tw * active)[:, None] * (s.softmax(1) - a / ml[:, None])) / 2
    expected_v = g @ t.detach() / obj.temperature
    expected_t = g.transpose(-1, -2) @ v.detach() / obj.temperature
    assert torch.allclose(loss.detach(), independent_loss, atol=1e-6, rtol=1e-6)
    assert torch.allclose(gv, expected_v, atol=1e-6, rtol=1e-6)
    assert torch.allclose(gt, expected_t, atol=1e-6, rtol=1e-6)
    eps = 1e-5
    vp, vm = v.detach().clone(), v.detach().clone()
    vp[0, 1, 0] += eps
    vm[0, 1, 0] -= eps
    fd = (obj.loss_sem_align(t.detach(), vp, lang, [target], indices, 1)
          - obj.loss_sem_align(t.detach(), vm, lang, [target], indices, 1)) / (2 * eps)
    assert abs(float(fd) - float(gv[0, 1, 0])) < 1e-5
    if padded:
        assert (g[:, :, 4:] > 0).all()
    return dict(loss=float(loss.detach()), independent_loss=float(independent_loss),
                valid_embedding_grad=gt[0, :4].tolist(), query_grad=gv[0].tolist(),
                padded_logit_gradient=g[0, :, 4:].tolist(),
                max_gradient_error=float(max((gv - expected_v).abs().max(),
                                             (gt - expected_t).abs().max())),
                finite_difference_error=abs(float(fd) - float(gv[0, 1, 0])))


def semantic_tests(obj):
    base = semantic_case(obj)
    pad = semantic_case(obj, 2)
    alternate = semantic_case(obj, 2, alternate=True)
    perm = semantic_case(obj, permutation=[2, 0, 1])
    assert abs(base["loss"] - perm["loss"]) < 1e-6
    assert abs(base["loss"] - pad["loss"]) > 1e-4
    assert abs(pad["loss"] - alternate["loss"]) > 1e-4
    delta = np.asarray(pad["valid_embedding_grad"]) - np.asarray(base["valid_embedding_grad"])
    assert np.max(np.abs(delta)) > 1e-4
    return dict(status="passed", configurations=4,
                base=base, padded=pad, alternate_padding=alternate, query_permuted=perm,
                padded_minus_base=pad["loss"] - base["loss"],
                alternate_minus_base=alternate["loss"] - base["loss"],
                max_valid_gradient_change=float(np.abs(delta).max()),
                conclusion="Source loss is not padding invariant on these fixed unit-embedding controls; real training impact unknown.")


def ranking(z, usable, positives, selected):
    z = np.asarray(z, dtype=np.float64)
    d = z[:, 1] - z[:, 0]
    assert z.shape == (128, 2) and np.isfinite(z).all()
    scores = 1 / (1 + np.exp(-d))
    eligible = dict(usable=np.asarray(usable, bool), positive_usable=np.asarray(usable, bool) & positives)
    record = dict(logit_differences=d.tolist(), selected_index=selected,
                  float64_selected=int(d.argmax()), selected_probability=float(scores[selected]),
                  selected_score_ties=int((d == d[selected]).sum()))
    for name, mask in eligible.items():
        ids = np.flatnonzero(mask)
        if not len(ids):
            record[name] = None
            continue
        best = int(ids[np.argmax(d[ids])])
        best_score = d[best]
        record[name] = dict(best_index=best, count=len(ids), rank=1 + int((d > best_score).sum()),
                            tied_count=int((d == best_score).sum()),
                            best_probability=float(scores[best]),
                            selected_margin=float(d[selected] - best_score))
    return record


def main():
    ap = argparse.ArgumentParser()
    for k in ("protocol", "assignment", "code-root", "banks", "out"):
        ap.add_argument("--" + k, required=True)
    args = ap.parse_args()
    protocol = json.loads(Path(args.protocol).read_text())
    root, banks, out = map(Path, (args.code_root, args.banks, args.out))
    assert not out.exists()
    assert sha(args.assignment) == protocol["assignment_sha256"]
    for rel, digest in protocol["source_hashes"].items():
        assert sha(root / rel) == digest
    a = json.loads(Path(args.assignment).read_text())
    assignments = {(r["model"], *key(r)): r for r in a["rows"]}
    torch.set_num_threads(1)
    started = time.monotonic()
    tests = {}
    for name, m in protocol["models"].items():
        obj = criterion(root / m["loss_path"])
        tests[name] = semantic_tests(obj)
    rows = []
    for name in ("baseline", "m95"):
        summary_path = banks / name / "summary.json"
        assert sha(summary_path) == protocol["summary_hashes"][name]
        summary = json.loads(summary_path.read_text())
        assert {key(r) for r in summary["rows"]} == {tuple(v) for v in protocol["ids"]}
        for r in summary["rows"]:
            assert time.monotonic() - started < 600
            path = banks / name / r["artifact"]
            assert sha(path) == r["artifact_sha256"]
            b = torch.load(path, map_location="cpu", weights_only=False)
            ar = assignments[(name, *key(r))]
            assert ar["bank_sha256"] == r["artifact_sha256"] and key(b["identity"]) == key(r)
            positive = np.zeros(128, bool)
            positive[ar["positive_indices"]] = True
            usable = np.asarray(r["candidate_ious"]) > .5
            z = b["score_logits"]
            assert int(z.softmax(-1)[:, 1].argmax()) == r["selected_index"]
            values = ranking(z.numpy(), usable, positive, r["selected_index"])
            rows.append(dict(model=name, **b["identity"], bank_sha256=r["artifact_sha256"],
                             status="complete", selected_iou=r["selected_iou"],
                             oracle_iou=r["oracle_iou"],
                             stratum="success" if r["selected_iou"] > .5 else
                             "recoverable" if r["oracle_iou"] > .5 else "bank_failure",
                             positive_indices=ar["positive_indices"], **values))
    assert len(rows) == 568 and not torch.cuda.is_initialized()
    result = dict(status="complete", protocol_sha256=sha(args.protocol),
                  worker_sha256=sha(__file__), rows=rows, semantic_tests=tests,
                  elapsed_seconds=time.monotonic() - started,
                  peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                  cuda_initialized=False,
                  limitation="Rank/GT diagnostics plus synthetic semantic tests; no real semantic projection/gradient measurements, no training modification.")
    out.mkdir()
    (out / "ordering.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ("rows", "semantic_tests")}, indent=2))
    print({n: (v["padded_minus_base"], v["alternate_minus_base"]) for n, v in tests.items()})


if __name__ == "__main__":
    main()
