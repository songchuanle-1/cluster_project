"""CPU full-source criterion, padding identity and projected-gradient checks."""
import argparse
import ast
import copy
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

from d1_assignment_20260911 import methods
from d1_candidate_bank_20260911 import key, sha
from d1_ordering_20260911 import criterion, semantic_tests

FIELDS = ("positive_map", "modify_positive_map", "pron_positive_map",
          "other_entity_map", "rel_positive_map")


def logit_criterion(path, temperature, eos_coef):
    tree = ast.parse(Path(path).read_text())
    nodes = [copy.deepcopy(n) for c in tree.body if isinstance(c, ast.ClassDef)
             for n in c.body if isinstance(n, ast.FunctionDef)
             and n.name in {"loss_sem_align", "_get_src_permutation_idx"}]
    method = next(n for n in nodes if n.name == "loss_sem_align")
    matches = [n for n in method.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "logits" for t in n.targets)]
    assert len(matches) == 1
    matches[0].value = ast.Name(id="proj_queries", ctx=ast.Load())
    ast.fix_missing_locations(tree := ast.Module(body=nodes, type_ignores=[]))
    scope = dict(torch=torch)
    exec(compile(tree, str(path), "exec"), scope)
    obj = SimpleNamespace(temperature=temperature, eos_coef=eos_coef)
    for name in ("loss_sem_align", "_get_src_permutation_idx"):
        setattr(obj, name, scope[name].__get__(obj))
    return obj


def audit_case(obj, logit_obj, b, positives):
    valid = b["lang_masks"].bool()
    length, total = int(valid.sum()), len(valid)
    assert length >= 2 and torch.equal(valid, torch.arange(total) < length)
    v, t = b["proj_queries"][None].double(), b["proj_tokens"][None].double()
    assert all(torch.isfinite(x).all() for x in (v, t))
    assert torch.allclose(v.norm(dim=-1), torch.ones_like(v[..., 0]), atol=1e-5)
    assert torch.allclose(t.norm(dim=-1), torch.ones_like(t[..., 0]), atol=1e-5)
    target = {f: b["dense_maps"][f][:1] for f in FIELDS}
    # All maps are retained, including fractional overlapping annotation weights.
    support = {f: int((x[..., length:total] != 0).sum()) for f, x in target.items()}
    assert not any(support.values()), support
    ids = torch.tensor(positives, dtype=torch.long)
    indices = [(ids, torch.zeros(len(ids), dtype=torch.long))]
    m = len(ids)
    assert m > 0
    losses, gradients = [], []
    for n in (total, length):
        vv, tt = v.clone().requires_grad_(), t[:, :n].clone().requires_grad_()
        loss = obj.loss_sem_align(tt, vv, b["lang_masks"][None, :n], [target], indices, m)
        gv, gt = torch.autograd.grad(loss, (vv, tt))
        assert torch.isfinite(loss) and torch.isfinite(gv).all() and torch.isfinite(gt).all()
        losses.append(float(loss))
        gradients.append((gv, gt))
    s = (v @ t.transpose(-1, -2) / obj.temperature).detach().requires_grad_()
    sloss = logit_obj.loss_sem_align(None, s, b["lang_masks"][None], [target], indices, m)
    gs, = torch.autograd.grad(sloss, s)
    gv, gt = gradients[0]
    chain_v, chain_t = gs @ t / obj.temperature, gs.transpose(-1, -2) @ v / obj.temperature
    assert abs(float(sloss) - losses[0]) < 1e-8
    assert torch.allclose(gv, chain_v, atol=1e-8, rtol=1e-7)
    assert torch.allclose(gt, chain_t, atol=1e-8, rtol=1e-7)
    active = torch.ones(v.shape[1], dtype=torch.bool)
    active[ids] = bool(target["positive_map"][0, :total].any())
    w = torch.full((v.shape[1],), obj.eos_coef, dtype=torch.float32).double()
    w[ids] = 1
    other = torch.zeros_like(s)
    other[0, ids] = (target["other_entity_map"][0, :total] > 0).double()
    logits = (1 + other) * s.detach()
    mass = logits.softmax(-1)[0, :, length:].sum(-1)
    weighted = w * active
    delta = (weighted * (logits.logsumexp(-1)[0] -
                        logits[..., :length].logsumexp(-1)[0])).sum() / (2 * m)
    padding_expected = weighted[:, None] * logits.softmax(-1)[0, :, length:] / (2 * m)
    pg = gs[0, :, length:]
    error = float((pg - padding_expected).abs().max()) if pg.numel() else 0.
    assert error < 1e-8
    assert abs((losses[0] - losses[1]) - float(delta)) < 1e-7
    assert losses[0] - losses[1] >= -1e-7
    full_q, crop_q = float(gv.norm()), float(gradients[1][0].norm())
    change_q = float((gv - gradients[1][0]).norm())
    full_t, pad_t = float(gt.norm()), float(gt[:, length:].norm())
    valid_change = float((gt[:, :length] - gradients[1][1]).norm())
    ratio = lambda n, d: n / d if d else None
    return dict(valid_length=length, padded_length=total, padding_count=total-length,
                annotation_padding_support=support, positive_count=m, normalization="per-description M",
                full_loss=losses[0], valid_prefix_loss=losses[1], loss_delta=losses[0]-losses[1],
                analytic_loss_delta=float(delta),
                padding_mass_sum=float(mass.sum()), query_count=len(mass),
                padding_mass_mean=float(mass.mean()), weighted_mass_numerator=float((weighted*mass).sum()),
                weighted_mass_denominator=float(weighted.sum()),
                weighted_padding_mass=ratio(float((weighted*mass).sum()), float(weighted.sum())),
                full_query_gradient_norm=full_q, valid_query_gradient_norm=crop_q,
                query_gradient_change_norm=change_q, query_gradient_change_ratio=ratio(change_q, full_q),
                full_token_gradient_norm=full_t, padded_token_gradient_norm=pad_t,
                padded_token_gradient_ratio=ratio(pad_t, full_t),
                valid_token_gradient_change_norm=valid_change,
                padding_logit_gradient_max_error=error,
                loss_delta_error=abs(losses[0]-losses[1]-float(delta)),
                chain_gradient_max_error=float(max((gv-chain_v).abs().max(), (gt-chain_t).abs().max())))


def main():
    ap = argparse.ArgumentParser()
    for name in ("protocol", "code-root", "data-root", "banks", "capture", "assignment", "out"):
        ap.add_argument("--" + name, required=True)
    args = ap.parse_args()
    root, data, banks, cap, out = map(Path, (args.code_root, args.data_root, args.banks, args.capture, args.out))
    assert not out.exists()
    protocol = json.loads(Path(args.protocol).read_text())
    for rel, digest in protocol["source_hashes"].items():
        assert sha(root / rel) == digest
    assert sha(args.assignment) == protocol["assignment_sha256"]
    assignments = {(r["model"], *key(r)): r for r in json.loads(Path(args.assignment).read_text())["rows"]}
    torch.set_num_threads(1)
    started = time.monotonic()
    ds = methods(root / "framework/dataset/scannetv2.py", ["get_sp_label"])
    scene_cache, rows, tests = {}, [], {}
    for name in ("baseline", "m95"):
        old_summary = json.loads((banks / name / "summary.json").read_text())
        assert sha(banks / name / "summary.json") == protocol["summary_hashes"][name]
        old_rows = {key(r): r for r in old_summary["rows"]}
        summary = json.loads((cap / name / "summary.json").read_text())
        assert summary["protocol_sha256"] == sha(args.protocol)
        assert summary["checkpoint_sha256"] == protocol["models"][name]["checkpoint_sha256"]
        assert summary["scene_graph_sha256"] == old_summary["scene_graph_sha256"]
        assert all(old_summary["input_hashes"][k] == v for k, v in summary["input_hashes"].items())
        path = root / protocol["models"][name]["loss_path"]
        obj = criterion(path)
        obj.temperature, obj.eos_coef = summary["temperature"], summary["eos_coef"]
        lo = logit_criterion(path, obj.temperature, obj.eos_coef)
        matcher = methods(path, ["match_sampled_ins"])
        tests[name] = semantic_tests(obj)
        for r in summary["rows"]:
            assert time.monotonic() - started < 300
            old = old_rows[key(r)]
            p, op = cap / name / r["artifact"], banks / name / old["artifact"]
            assert sha(p) == r["artifact_sha256"] and sha(op) == old["artifact_sha256"]
            b, previous = [torch.load(x, map_location="cpu", weights_only=False) for x in (p, op)]
            assert key(b["identity"]) == key(r) == key(previous["identity"])
            group = summary["groups"][r["group_index"]]["members"]
            assert group == old_summary["groups"][old["group_index"]]["members"]
            for field in ("seed_indices", "sample_indices", "superpoints", "gt_pmask", "gt_spmask"):
                assert torch.equal(b[field], previous[field]), (name, key(r), field)
            drift, logit_equal = {}, {}
            for field in ("mask_logits", "score_logits"):
                drift[field] = float((b[field] - previous[field]).abs().max())
                logit_equal[field] = torch.allclose(b[field], previous[field], atol=1e-5, rtol=1e-5)
            binary_equal = torch.equal(b["mask_logits"] >= 0, previous["mask_logits"] >= 0)
            iou_equal = b["selected_iou"] == old["selected_iou"]
            selected_equal = int(b["score_logits"].softmax(-1)[:, 1].argmax()) == old["selected_index"]
            linked = all(logit_equal.values()) and binary_equal and iou_equal and selected_equal
            ar = assignments[(name, *key(r))]
            assert ar["bank_sha256"] == old["artifact_sha256"]
            scene = r["scene_id"]
            if scene not in scene_cache:
                raw = data / "scannetv2/val" / f"{scene}_refer.pth"
                assert sha(raw) == summary["input_hashes"][str(raw.relative_to(data))]
                xyz, _, sp, sem, ins = torch.load(raw, map_location="cpu", weights_only=False)
                _, mapping = np.unique(sp, return_inverse=True)
                mapping = torch.tensor(mapping)
                labels, _ = ds.get_sp_label(mapping, torch.tensor(ins), torch.tensor(sem))
                xyz = torch_scatter.scatter_mean(torch.tensor(xyz).float(), mapping, dim=0)
                scene_cache[scene] = (labels, xyz, mapping)
            labels, xyz, mapping = scene_cache[scene]
            assert torch.equal(mapping, b["superpoints"])
            target = int(r["object_id"])
            qsp = b["seed_indices"].long()[b["sample_indices"].long()]
            mu = torch_scatter.scatter_mean(xyz, (labels == target).long(), dim=0)[1:2]
            positive = matcher.match_sampled_ins(labels[qsp], [target], xyz[qsp], mu)[2][0].tolist()
            assert sorted(positive) == sorted(ar["positive_indices"])
            values = audit_case(obj, lo, b, positive)
            rows.append(dict(model=name, **b["identity"], bank_sha256=r["artifact_sha256"],
                             previous_bank_sha256=old["artifact_sha256"], bank_max_abs_drift=drift,
                             prior_logit_tolerance_pass=logit_equal, prior_binary_equal=binary_equal,
                             prior_selected_iou_equal=iou_equal, prior_selected_index_equal=selected_equal,
                             prior_bank_linked_claims_accepted=linked,
                             selected_iou=b["selected_iou"], positive_indices=positive,
                             role="error" if list(key(r)) in [p["error"] for p in protocol["pairs"]] else "control",
                             **values))
    assert not torch.cuda.is_initialized()
    result = dict(status="complete" if len(rows) == 42 else "partial", rows=rows, tests=tests,
                  protocol_sha256=sha(args.protocol), worker_sha256=sha(__file__),
                  elapsed_seconds=time.monotonic()-started,
                  peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                  cuda_initialized=False,
                  limits="Final evaluation projections, per-description normalizer, outcome-selected 21 IDs; not historical training gradients, causal efficacy, population prevalence or novelty.")
    out.mkdir()
    (out / "padding.json").write_text(json.dumps(result, indent=2))
    print("AUDIT", result["status"], len(rows), "rows", flush=True)
    for name in ("baseline", "m95"):
        rr = [r for r in rows if r["model"] == name]
        print(name, {f: float(np.mean([r[f] for r in rr])) for f in (
            "padding_mass_mean", "weighted_padding_mass", "loss_delta",
            "query_gradient_change_ratio", "padded_token_gradient_ratio")}, flush=True)


if __name__ == "__main__":
    main()
