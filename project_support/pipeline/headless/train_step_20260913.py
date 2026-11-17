"""Isolated current-environment fixed TRAIN batch counterfactual, never a trainer."""
import argparse
import copy
import hashlib
import importlib
import inspect
import json
import logging
import os
from pathlib import Path
import random
import sys
import time

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024**2), b""):
            h.update(block)
    return h.hexdigest()


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, default=str), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    for name in ("code-root", "audit", "out"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--identity-followup", action="store_true")
    args = parser.parse_args()
    root, out = Path(args.code_root), Path(args.out)
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import numpy as np
    import torch
    import gorilla
    from framework.dataset import build_dataset
    from framework import resolve_network

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    audit = json.loads(Path(args.audit).read_text())
    assert sha(audit["checkpoint"]) == audit["checkpoint_sha256"]
    assert sha(audit["config"]) == audit["config_sha256"]
    cfg = gorilla.Config.fromfile(audit["config"])
    assert cfg.train.seed == 1999 and cfg.train.grad_clip == .1
    assert cfg.dataloader.train.batch_size == 2 and cfg.data.train.lang_num_max == 4
    assert cfg.data.train.training and cfg.data.train.prefix == "train"
    data = Path(cfg.data.train.data_root)
    source = data / "scanrefer/ScanRefer_train_new.json"
    graphs = data / "scanrefer/scene_graphs_new_train.json"
    assert graphs.exists(), "Do not generate new annotations"
    logger = logging.getLogger("fixed_train")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    gorilla.set_random_seed(1999)
    ds = build_dataset(cfg.data.train, logger)
    groups = {}
    # Preserve native groups; sort group identities only to choose deterministically.
    def identity(r):
        return (r["scene_id"], str(r["object_id"]), str(r["ann_id"]))
    for i, group in enumerate(ds.scene_inputs):
        groups.setdefault(group[0]["scene_id"], []).append((tuple(sorted(identity(r) for r in group)), i))
    chosen_scenes = sorted(groups)[:2]
    chosen = [min(groups[s])[1] for s in chosen_scenes]
    chosen_groups = [ds.scene_inputs[i] for i in chosen]
    records = [dict(scene_id=r["scene_id"], object_id=str(r["object_id"]), ann_id=str(r["ann_id"]))
               for group in chosen_groups for r in group]
    assert len(records) == 8
    module = importlib.import_module(audit["explicit_module"])
    package = Path(module.__file__).parent
    assert {p.name: sha(p) for p in package.glob("*.py")} == audit["package_sha256"]
    assert resolve_network(audit["config"]) is module.Network
    sources = {str(p.relative_to(root)): sha(p) for p in [
        root / "framework/dataset/__init__.py", root / "framework/dataset/scannetv2.py",
        root / "framework/__init__.py", root / "tools/train.py", root / "framework/utils/utils.py"]}
    inputs = {str(p): sha(p) for p in [source, graphs, data / "scannetv2-labels.combined.tsv"]}
    for scene in chosen_scenes:
        for p in (data / "scannetv2/train" / f"{scene}_refer.pth", data / "clip_feat" / f"{scene}.pth"):
            inputs[str(p)] = sha(p)
    for p in sorted((data / "roberta-base").glob("*")):
        if p.is_file():
            inputs[str(p)] = sha(p)
    model = module.Network(**cfg.model)
    checkpoint = torch.load(audit["checkpoint"], map_location="cpu", weights_only=False)
    initial = checkpoint["model"]
    extra = set(initial) - set(model.state_dict())
    assert extra == {"text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"}
    for name in extra:
        assert torch.equal(initial[name], getattr(model.text_encoder.embeddings, name.rsplit(".", 1)[1]))
    initial = {k: v for k, v in initial.items() if k not in extra}
    model.load_state_dict(initial, strict=True)
    optimizer = gorilla.build_optimizer(model, copy.deepcopy(cfg.optimizer))
    named = dict(model.named_parameters())
    reverse = {id(p): n for n, p in named.items()}
    mapping = []
    saved_opt = checkpoint["optimizer"]
    assert len(optimizer.param_groups) == len(saved_opt["param_groups"])
    seen = set()
    for gi, (current, saved) in enumerate(zip(optimizer.param_groups, saved_opt["param_groups"])):
        assert len(current["params"]) == len(saved["params"])
        for param, pid in zip(current["params"], saved["params"]):
            name = reverse[id(param)]
            assert name not in seen
            seen.add(name)
            state = saved_opt["state"].get(pid, {})
            for field in ("exp_avg", "exp_avg_sq"):
                if field in state:
                    assert state[field].shape == param.shape and state[field].dtype == param.dtype
            mapping.append(dict(group=gi, saved_id=pid, name=name, shape=list(param.shape),
                                requires_grad=param.requires_grad, has_state=bool(state)))
    # No shape-based assignment: pairing follows the actual deterministic builder order.
    assert sum(r["has_state"] for r in mapping) == 642
    single = gorilla.build_optimizer.__globals__["build_single_optimizer"]
    builder_text = inspect.getsource(gorilla.build_optimizer) + "\n" + inspect.getsource(single)
    manifest = dict(records=records, dataset_indices=chosen, scenes=chosen_scenes,
        inputs=inputs, source_hashes=sources, package_sha256=audit["package_sha256"],
        checkpoint_sha256=audit["checkpoint_sha256"], config_sha256=audit["config_sha256"],
        optimizer_mapping=mapping, optimizer_builder_source=builder_text,
        optimizer_type=str(type(optimizer)), torch_version=torch.__version__,
        worker_sha256=sha(__file__), created=time.strftime("%Y-%m-%d %H:%M:%S"),
        sampling="First two lexically sorted TRAIN scenes; choose native group with lexically smallest sorted identity tuple; preserve native within-group order.",
        mapping_limit="Current builder name/order/shape verification; checkpoint contains no historical param_names, so historical mapping identity remains unproved.")
    if args.prepare:
        out.mkdir(exist_ok=False)
        save_json(out / "manifest.json", manifest)
        assert not torch.cuda.is_initialized()
        print(json.dumps(dict(status="prepared", records=records, optimizer_groups=len(optimizer.param_groups),
            parameters=len(mapping), states=642, cuda=False, manifest_sha256=sha(out / "manifest.json"))))
        return
    frozen = json.loads((out / "manifest.json").read_text())
    for field in ("records", "dataset_indices", "inputs", "source_hashes", "package_sha256",
                  "checkpoint_sha256", "config_sha256", "optimizer_mapping", "optimizer_builder_source"):
        assert frozen[field] == manifest[field], field
    result_name = "identity_result.json" if args.identity_followup else "result.json"
    assert not (out / result_name).exists()
    acceptance = json.loads((out / "acceptance.json").read_text())
    assert acceptance["manifest_sha256"] == sha(out / "manifest.json")
    free, total = torch.cuda.mem_get_info()
    assert free > 27 * 1024**3
    torch.cuda.set_per_process_memory_fraction(26 * 1024**3 / total)
    model.cuda().train()
    trainable = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    params = [p for n, p in trainable]
    gorilla.set_random_seed(1999)
    if args.identity_followup:
        fixed = torch.load(out / "fixed_batch.pth", map_location="cpu", weights_only=False)
        assert fixed["manifest_sha256"] == sha(out / "manifest.json")
        batch = fixed["batch"]
    else:
        samples = [ds[i] for i in chosen]
        batch = ds.collate_fn(samples)
    assert batch["scan_ids"] == chosen_scenes
    def rng():
        return (random.getstate(), np.random.get_state(), torch.get_rng_state(), torch.cuda.get_rng_state_all())
    def set_rng(state):
        random.setstate(state[0]); np.random.set_state(state[1])
        torch.set_rng_state(state[2]); torch.cuda.set_rng_state_all(state[3])
    base_rng = fixed["rng"] if args.identity_followup else rng()
    # This file is diagnostic input/RNG evidence, not an updated checkpoint.
    if not args.identity_followup:
        torch.save(dict(batch=batch, rng=base_rng, manifest_sha256=sha(out / "manifest.json")),
                   out / "fixed_batch.pth")
    buffers = {n: b.detach().cpu().clone() for n, b in model.named_buffers()}
    capture = {}
    original_ce = model.criterion.loss_indi
    def ce_hook(pred, targets, indices, num_boxes):
        if "indices" not in capture:
            capture["indices"] = [(a.detach().clone(), b.detach().clone()) for a,b in indices]
        return original_ce(pred, targets, indices, num_boxes)
    model.criterion.loss_indi = ce_hook
    def criterion_pre(m, inputs):
        capture["pred"] = inputs[0]
    hook = model.criterion.register_forward_pre_hook(criterion_pre)
    def restore():
        model.load_state_dict(initial, strict=True)
        model.train()
        for n, b in model.named_buffers():
            b.copy_(buffers[n])
        optimizer.zero_grad(set_to_none=True)
        set_rng(base_rng)
        capture.clear()
    def forward(grad):
        with torch.set_grad_enabled(grad):
            loss, terms = model(batch, mode="loss")
        pred = capture["pred"]
        coefficients = {"mask_bce_loss": 1., "mask_dice_loss": 1., "score_loss": .5,
                        "sample_loss": 5., "indi_loss": .1, "sem_loss": .1, "orth_reg_loss": 1.}
        weighted = {}
        for name, term in terms.items():
            if name == "loss":
                continue
            base, factor = name, 1.
            if name.startswith("layer_"):
                _, index, base = name.split("_", 2)
                factor = (int(index) + 1) / (len(pred["aux_outputs"]) + 1)
            weighted[name] = term * coefficients[base] * factor
        reconstructed = sum(weighted.values())
        assert torch.allclose(loss, reconstructed, atol=1e-6, rtol=1e-5)
        assert torch.isfinite(loss).all()
        return loss, terms, weighted, pred
    restore()
    loss0, _, _, pred0 = forward(False)
    reference = {k: pred0[k].detach().cpu().clone() for k in ("indis", "sample_inds", "batch_mask")}
    indices0 = [(a.cpu(), b.cpu()) for a,b in capture["indices"]]
    get_iou = importlib.import_module(audit["explicit_module"] + ".loss").get_iou
    pairs = []
    for i, record in enumerate(records):
        mask = pred0["masks"][i][:, ~pred0["batch_mask"][i]]
        iou = get_iou(mask, batch["gt_spmasks"][i].cuda())
        z = pred0["indis"][i]
        s = int(z.softmax(-1)[:, 1].argmax())
        y = torch.zeros(len(z), dtype=torch.bool, device=z.device)
        y[indices0[i][0]] = True
        good = y & (iou > .5)
        h = int((z[:,1]-z[:,0]).masked_fill(~good, -torch.inf).argmax()) if good.any() else None
        pairs.append(dict(**record, selected=s, positive=h, selected_iou=float(iou[s]),
            oracle_iou=float(iou.max()), selected_positive=bool(y[s]),
            recoverable=bool(iou[s] <= .5 < iou.max()), informative=h is not None and h != s,
            margin=float(z[s,1]-z[s,0]-z[h,1]+z[h,0]) if h is not None else None))
    del pred0
    restore()
    _, _, _, repeat = forward(False)
    replay_error = float((repeat["indis"].cpu() - reference["indis"]).abs().max())
    assert torch.equal(repeat["sample_inds"].cpu(), reference["sample_inds"])
    assert replay_error <= acceptance["replay_logit_atol"], replay_error
    del repeat
    result = dict(status="replay_passed", manifest_sha256=sha(out / "manifest.json"),
        acceptance_sha256=sha(out / "acceptance.json"), worker_sha256=sha(__file__),
        replay_logit_error=replay_error, pairs=pairs,
        train_mode_flags={n:m.training for n,m in model.named_modules()},
        fixed_batch_sha256=sha(out / "fixed_batch.pth"))
    save_json(out / ("identity_replay.json" if args.identity_followup else "replay.json"), result)
    eligible = [(i,p) for i,p in enumerate(pairs) if p["informative"]]
    if not eligible:
        result["status"] = "inconclusive_empty_pairs"
        save_json(out / result_name, result)
        print("TRAIN_STEP_EMPTY_PAIRS", json.dumps(pairs), flush=True)
        return
    restore()
    loss, terms, weighted, pred = forward(True)
    gradients = torch.autograd.grad(loss, params, retain_graph=True, allow_unused=True)
    grads = [None if g is None else g.detach().cpu() for g in gradients]
    reconstructed_grad = torch.autograd.grad(sum(weighted.values()), params, retain_graph=True, allow_unused=True)
    grad_sum_error = max(float((g-h).abs().max()) for g,h in zip(gradients,reconstructed_grad) if g is not None)
    assert grad_sum_error <= acceptance["gradient_sum_atol"]
    margin_grads = {}
    final_head = [p for n,p in trainable if n.startswith("dec.decoder_layers.5.indi_embedding.")]
    for i, pair in eligible:
        z = pred["indis"][i]
        s,h = pair["selected"],pair["positive"]
        margin = z[s,1]-z[s,0]-z[h,1]+z[h,0]
        a = torch.autograd.grad(margin, params, retain_graph=True, allow_unused=True)
        margin_grads[i] = [None if g is None else g.detach().cpu() for g in a]
        pair["v_full_sgd"] = -sum(float((aa.double()*gg.double()).sum()) for aa,gg in zip(a,gradients) if aa is not None and gg is not None)
        ah = torch.autograd.grad(margin, final_head, retain_graph=True, allow_unused=True)
        gh = torch.autograd.grad(weighted["indi_loss"], final_head, retain_graph=True, allow_unused=True)
        pair["v_head_ce"] = -sum(float((aa.double()*gg.double()).sum()) for aa,gg in zip(ah,gh) if aa is not None and gg is not None)
    del gradients, reconstructed_grad, pred, loss, terms, weighted, a, ah, gh
    capture.clear()
    torch.cuda.empty_cache()
    def step_arm(zero):
        restore()
        optimizer.load_state_dict(copy.deepcopy(saved_opt))
        for p,g in zip(params,grads):
            p.grad = None if g is None else (torch.zeros_like(p) if zero else g.to(p.device).clone())
        pre_norm = float(torch.nn.utils.clip_grad_norm_(params, cfg.train.grad_clip))
        optimizer.step()
        linear = {}
        max_delta = 0.
        for i,_ in eligible:
            value = 0.
            for (name,p),a in zip(trainable,margin_grads[i]):
                if a is not None:
                    delta = p.detach().cpu() - initial[name]
                    max_delta = max(max_delta, float(delta.abs().max()))
                    value += float((a.double()*delta.double()).sum())
            linear[i] = value
        # Hold buffers/RNG/input fixed to isolate parameter response.
        for n,b in model.named_buffers():
            b.copy_(buffers[n])
        set_rng(base_rng)
        capture.clear()
        _, _, _, after = forward(False)
        identity_changed = not torch.equal(after["sample_inds"].cpu(), reference["sample_inds"])
        values = {}
        for i,pair in eligible:
            z = after["indis"][i]
            s,h = pair["selected"], pair["positive"]
            change = float(z[s,1]-z[s,0]-z[h,1]+z[h,0]) - pair["margin"]
            values[i] = dict(linear=linear[i], observed=change, remainder=change-linear[i])
        if args.identity_followup:
            identities = []
            for i, pair in enumerate(pairs):
                before_ids = reference["sample_inds"][i].long()
                after_ids = after["sample_inds"][i].detach().cpu().long()
                common = set(before_ids.tolist()) & set(after_ids.tolist())
                record = dict(expression=i, common_count=len(common),
                              before_count=len(before_ids), after_count=len(after_ids),
                              position_changes=int((before_ids != after_ids).sum()),
                              same_set=set(before_ids.tolist()) == set(after_ids.tolist()))
                if pair["informative"]:
                    sid, hid = int(before_ids[pair["selected"]]), int(before_ids[pair["positive"]])
                    si, hi = (after_ids == sid).nonzero().flatten(), (after_ids == hid).nonzero().flatten()
                    record.update(selected_seed=sid, positive_seed=hid,
                                  selected_retained=len(si) == 1, positive_retained=len(hi) == 1)
                    if len(si) == len(hi) == 1:
                        z = after["indis"][i]
                        aligned = float(z[si[0],1]-z[si[0],0]-z[hi[0],1]+z[hi[0],0])
                        record["aligned_change"] = aligned - pair["margin"]
                identities.append(record)
            del after
            capture.clear()
            original_sampling = model.dec.sampling_module.forward
            def fixed_sampling(*args, **kwargs):
                indices, scores = original_sampling(*args, **kwargs)
                return reference["sample_inds"].to(indices.device).to(indices.dtype), scores
            model.dec.sampling_module.forward = fixed_sampling
            try:
                for n,b in model.named_buffers():
                    b.copy_(buffers[n])
                set_rng(base_rng)
                _, _, _, fixed_after = forward(False)
                assert torch.equal(fixed_after["sample_inds"].cpu(), reference["sample_inds"])
                for i,pair in eligible:
                    z = fixed_after["indis"][i]
                    s,h = pair["selected"],pair["positive"]
                    fixed_change = float(z[s,1]-z[s,0]-z[h,1]+z[h,0]) - pair["margin"]
                    values[i]["fixed_seed_change"] = fixed_change
                    values[i]["fixed_seed_remainder"] = fixed_change-linear[i]
            finally:
                model.dec.sampling_module.forward = original_sampling
            return dict(preclip_norm=pre_norm, max_parameter_delta=max_delta,
                        query_identity_changed=identity_changed, values=values, identity=identities)
        return dict(preclip_norm=pre_norm, max_parameter_delta=max_delta,
                    query_identity_changed=identity_changed, values=values)
    result["gradient_sum_error"] = grad_sum_error
    result["full_adam"] = step_arm(False)
    result["zero_gradient_adam"] = step_arm(True)
    result["pairs"] = pairs
    result["peak_cuda_mib"] = torch.cuda.max_memory_allocated()/1024**2
    result["status"] = "complete"
    result["limit"] = "Current train-mode fixed batch, no historical mapping/trajectory guarantee; identity changes veto corresponding finite-step margin interpretation."
    assert sha(audit["checkpoint"]) == audit["checkpoint_sha256"]
    save_json(out / result_name, result)
    print("TRAIN_STEP_COMPLETE", json.dumps({k:v for k,v in result.items() if k != "train_mode_flags"}), flush=True)


if __name__ == "__main__":
    main()
