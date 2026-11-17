"""Frozen native TRAIN capture; experimental joint operator, no model mutation."""
import argparse
import ast
import importlib
import json
import logging
import os
from pathlib import Path
import sys
import types


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--population", action="store_true")
    args = p.parse_args()
    root = args.root.resolve()
    assert os.environ["CUDA_VISIBLE_DEVICES"] == "7" and not args.output.exists()
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(root / "scripts"), str(root), str(root / "framework/lib")]
    import torch
    import gorilla
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader
    from m95_multiword_native_31_20260928 import (
        NAME, CHECKPOINT_SHA, DATASET_SHA, ANNOTATION_SHA, GRAPH_SHA,
        sha, frozen_rows, select_native_indices, selected_loader)
    from m95_final_seed_target_probe_20260927 import batch_fingerprint
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    assert sha(args.checkpoint) == CHECKPOINT_SHA
    if args.population:
        manifest_rows = json.loads(args.manifest.read_text())
        assert len(manifest_rows) == 32
        frozen = {(r["scene"], int(a["ann_id"])): {
            "target_instances": a["object_ids"]}
                  for r in manifest_rows for a in r["annotations"]}
        assert len(frozen) == 128 and len({s for s, _ in frozen}) == 32
    else:
        frozen = frozen_rows(args.manifest)
    data_root = Path("/data3/songcl/data/data_cluster")
    inputs = {"dataset": root / "framework/dataset/scannetv2.py",
              "annotations": data_root / "scanrefer/ScanRefer_train_new.json",
              "graphs": data_root / "scanrefer/scene_graphs_new_train.json"}
    expected = {"dataset": DATASET_SHA, "annotations": ANNOTATION_SHA, "graphs": GRAPH_SHA}
    assert {k: sha(v) for k, v in inputs.items()} == expected
    config = root / f"configs/Quard/ctf_hcg_csort/{NAME}.yaml"
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = str(data_root) + "/"
    gorilla.set_random_seed(1999)
    source = build_dataset(cfg.data.train, logging.getLogger("joint-selector-diagnostic"))
    if args.population:
        native_indices = [int(r["native_group"]) for r in manifest_rows]
        for r, index in zip(manifest_rows, native_indices):
            group = source.scene_inputs[index]
            for a in r["annotations"]:
                item = next(i for i in group if i["scene_id"] == r["scene"]
                            and int(i["ann_id"]) == int(a["ann_id"]))
                assert sorted(map(int, item["object_ids"])) == sorted(map(int, a["object_ids"]))
    else:
        native_indices = select_native_indices(source, frozen)
    loader = selected_loader(source, native_indices, DataLoader)
    model = importlib.import_module("framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    criterion = model.criterion
    pirs_source = root / f"framework/model/Quard_model/{NAME}_pirs/loss.py"
    pirs_tree = ast.parse(pirs_source.read_text())
    pirs_cls = next(n for n in pirs_tree.body if isinstance(n, ast.ClassDef) and n.name == "Criterion")
    pirs_fn = next(n for n in pirs_cls.body if isinstance(n, ast.FunctionDef) and n.name == "loss_indi")
    scope = {"torch": torch}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[pirs_fn], type_ignores=[])),
                 "<exact-existing-PIRS>", "exec"), scope)
    pirs = types.MethodType(scope["loss_indi"], criterion)
    held = {}
    handle = criterion.register_forward_pre_hook(lambda module, data: held.update(pred=data[0]))
    native = criterion.loss_indi
    last = {}

    def capture(self, logits, targets, indices, count):
        last.update(logits=logits, targets=targets, indices=indices, count=count)
        return native(logits, targets, indices, count)

    criterion.loss_indi = types.MethodType(capture, criterion)
    records = []

    def joint(logits, masks, target, detach_mask=False, detach_selector=False):
        indication = logits[:, 1] - logits[:, 0]
        if detach_selector:
            indication = indication.detach()
        likelihood = (-torch.nn.functional.binary_cross_entropy_with_logits(
            masks, target.expand_as(masks), reduction="none")).sum(-1)
        if detach_mask:
            likelihood = likelihood.detach()
        evidence = indication.log_softmax(0) + likelihood
        return -evidence.logsumexp(0) / target.numel(), evidence.softmax(0), likelihood

    def flat_cos(x, y):
        return float(torch.nn.functional.cosine_similarity(x.flatten(), y.flatten(), dim=0))

    try:
        with torch.no_grad():
            for step, batch in enumerate(loader):
                fingerprint = batch_fingerprint(torch, batch)
                held.clear()
                last.clear()
                gorilla.set_random_seed(1999)
                native_total, _ = model(batch, mode="loss")
                assert torch.isfinite(native_total).all()
                pred = held["pred"]
                scenes = [s for s, c in zip(batch["scan_ids"], batch["scenes_len"])
                          for _ in range(int(c))]
                for b, (scene, aid) in enumerate(zip(scenes, batch["ann_ids"])):
                    key = scene, int(aid)
                    if key not in frozen:
                        continue
                    assert sorted(map(int, batch["object_idss"][b])) == sorted(
                        map(int, frozen[key]["target_instances"]))
                    target = batch["gt_spmasks"][b].to(pred["masks"].device).flatten().bool()
                    assert target.any()
                    masks = pred["masks"][b, :, :len(target)].detach()
                    logits = pred["indis"][b].detach()
                    selected = int(logits.softmax(-1)[:, 1].argmax())
                    binary = masks > 0
                    ious = ((binary & target).sum(-1).float()
                            / (binary | target).sum(-1).clamp_min(1))
                    with torch.enable_grad():
                        z = logits.double().clone().requires_grad_(True)
                        m = masks.double().clone().requires_grad_(True)
                        y = target.double().unsqueeze(0)
                        value, posterior, likelihood = joint(z, m, y)
                        gz, gm = torch.autograd.grad(value, (z, m))
                        repeat, _, _ = joint(z, m, y)
                        rz, rm = torch.autograd.grad(repeat, (z, m))
                        torch.testing.assert_close(repeat, value, atol=1e-6, rtol=0)
                        torch.testing.assert_close(gz, rz, atol=1e-6, rtol=0)
                        torch.testing.assert_close(gm, rm, atol=1e-6, rtol=0)
                        no_mask, _, _ = joint(z, m, y, detach_mask=True)
                        az = torch.autograd.grad(no_mask, z)[0]
                        no_selector, _, _ = joint(z, m, y, detach_selector=True)
                        am = torch.autograd.grad(no_selector, m)[0]
                        torch.testing.assert_close(az, gz, atol=1e-6, rtol=0)
                        torch.testing.assert_close(am, gm, atol=1e-6, rtol=0)
                        order = torch.arange(len(z) - 1, -1, -1, device=z.device)
                        pv, _, _ = joint(z[order], m[order], y)
                        pgz, pgm = torch.autograd.grad(pv, (z, m))
                        torch.testing.assert_close(pv, value, atol=1e-6, rtol=0)
                        torch.testing.assert_close(pgz, gz, atol=1e-6, rtol=0)
                        torch.testing.assert_close(pgm, gm, atol=1e-6, rtol=0)
                        neutral = m.mean(0, keepdim=True).expand_as(m)
                        nv, _, _ = joint(z, neutral, y, detach_mask=True)
                        ng = torch.autograd.grad(nv, z)[0]
                        assert float(ng.abs().max()) < 1e-12
                        placebo, _, _ = joint(z, m, y.roll(1, dims=-1))
                        wrong_z, wrong_m = torch.autograd.grad(placebo, (z, m))
                        idx = last["indices"][b]
                        count = max(1, len(idx[0]))
                        targets = [last["targets"][b]]
                        native_z = logits.float().clone().requires_grad_(True)
                        native_m = masks.float()
                        nloss = native(native_z.unsqueeze(0), targets, [idx], count)
                        gn = torch.autograd.grad(nloss, native_z)[0].double()
                        ploss = pirs(native_z.unsqueeze(0), [native_m], targets, [idx], count)
                        gp = torch.autograd.grad(ploss, native_z)[0].double()
                        assert all(torch.isfinite(g).all() for g in (gz, gm, gn, gp))
                        mean_query_grad = gm.abs().sum(-1)
                        positive = torch.zeros(len(z), dtype=torch.bool, device=z.device)
                        positive[idx[0]] = True
                        row = {"scene": scene, "ann_id": int(aid), "batch": step,
                               "input_sha256": fingerprint, "selected_query": selected,
                               "selected_iou": float(ious[selected]), "oracle_iou": float(ious.max()),
                               "likelihood_best_query": int(likelihood.argmax()),
                               "likelihood_best_iou": float(ious[likelihood.argmax()]),
                               "posterior_best_iou": float(ious[posterior.argmax()]),
                               "posterior_max": float(posterior.max()),
                               "posterior_entropy": float(-(posterior * posterior.clamp_min(1e-300).log()).sum()),
                               "joint_selector_grad_l1": float(gz.abs().sum()),
                               "joint_mask_grad_l1": float(gm.abs().sum()),
                               "native_selector_grad_l1": float(gn.abs().sum()),
                               "pirs_selector_grad_l1": float(gp.abs().sum()),
                               "joint_native_selector_cosine": flat_cos(gz, gn),
                               "joint_pirs_selector_cosine": flat_cos(gz, gp),
                               "mask_placebo_gradient_cosine": flat_cos(gm, wrong_m),
                               "placebo_selector_gradient_max_delta": float((gz - wrong_z).abs().max()),
                               "posterior_iou_worse_than_selected": float(ious[posterior.argmax()]) < float(ious[selected]),
                               "mask_grad_outside_native_positive_l1": float(mean_query_grad[~positive].sum()),
                               "repeat_permutation_ablation_pass": True,
                               "neutral_selector_grad_max": float(ng.abs().max()),
                               "operator_dtype": "joint float64; native/PIRS controls and native forward float32"}
                    records.append(row)
                print(json.dumps({"batch": step, "captured": len(records)}), flush=True)
    finally:
        criterion.loss_indi = native
        handle.remove()
    assert len(records) == len(frozen) and {(r["scene"], r["ann_id"]) for r in records} == set(frozen)
    failures = [r for r in records if r["selected_iou"] < 0.5 and r["oracle_iou"] >= 0.5]
    summary = {
        "expressions": len(records), "scenes": len({r["scene"] for r in records}),
        "recoverable_selection_failures": len(failures),
        "likelihood_recovers_failures": sum(r["likelihood_best_iou"] >= 0.5 for r in failures),
        "posterior_recovers_failures": sum(r["posterior_best_iou"] >= 0.5 for r in failures),
        "likelihood_worse_than_selected": sum(r["likelihood_best_iou"] < r["selected_iou"] for r in records),
        "posterior_worse_than_selected": sum(r["posterior_iou_worse_than_selected"] for r in records),
        "recoverable_failure_scenes": len({r["scene"] for r in failures}),
        "posterior_saturated_gt_0999": sum(r["posterior_max"] > 0.999 for r in records),
        "nonzero_joint_mask_grad": sum(r["joint_mask_grad_l1"] > 0 for r in records),
        "nonzero_joint_selector_grad": sum(r["joint_selector_grad_l1"] > 0 for r in records)}
    result = {"contract": "joint_selector_native_diagnosis_v1", "admission": False,
              "checkpoint_sha256": CHECKPOINT_SHA, "manifest_sha256": sha(args.manifest),
              "config_sha256": sha(config), "native_inputs": expected,
              "pirs_source_sha256": sha(pirs_source), "script_sha256": sha(Path(__file__)),
              "seed": 1999, "summary": summary, "rows": records,
              "limits": "Frozen TRAIN only; detached native tensor backward; joint arithmetic float64, native/PIRS float32; not full model backward, resource admission, changed inference or trained efficacy."}
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
