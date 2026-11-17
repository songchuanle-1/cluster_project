"""Native, prediction-blind physical support incidence on the frozen TRAIN cohort."""
import argparse
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys

from m95_multiword_native_31_20260928 import (
    NAME, CHECKPOINT_SHA, DATASET_SHA, ANNOTATION_SHA, GRAPH_SHA,
    frozen_rows, select_native_indices, selected_loader, sha,
)
from m95_native31_physical_support_20260928 import physical_support
from m95_native31_support_contract_20260928 import (
    check_final_targets, check_non_sample_losses,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--parameter-backward", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    if (os.environ.get("CUDA_VISIBLE_DEVICES") != "7" or output.exists()
            or not output.is_relative_to(root.parent / "pipeline")
            or sha(args.checkpoint) != CHECKPOINT_SHA):
        raise ValueError("GPU7, fresh project output and frozen checkpoint required")
    if args.parameter_backward and not args.replay:
        raise ValueError("Parameter backward needs same-forward replay")
    frozen = frozen_rows(args.manifest)
    data_root = Path("/data3/songcl/data/data_cluster")
    inputs = {
        "dataset": root / "framework/dataset/scannetv2.py",
        "annotations": data_root / "scanrefer/ScanRefer_train_new.json",
        "graphs": data_root / "scanrefer/scene_graphs_new_train.json",
    }
    expected = {"dataset": DATASET_SHA, "annotations": ANNOTATION_SHA,
                "graphs": GRAPH_SHA}
    if {name: sha(path) for name, path in inputs.items()} != expected:
        raise ValueError("Frozen native source hashes differ")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import torch
    import gorilla
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader

    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    config = root / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = str(data_root) + "/"
    gorilla.set_random_seed(1999)
    source = build_dataset(cfg.data.train, logging.getLogger("m95_support_incidence"))
    indices = select_native_indices(source, frozen)
    transformed = {}
    original_transform = source.transform_train

    def capture_transform(*scene):
        result = original_transform(*scene)
        transformed["axes"] = result[3:6]
        return result

    source.transform_train = capture_transform
    loader = selected_loader(source, indices, DataLoader)
    model = importlib.import_module(
        "framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    held = {}
    matches = []
    focal_targets = []
    native_match = model.criterion.match_sampled_ins
    loss_module = importlib.import_module(
        "framework.model.Quard_model." + NAME + ".loss")
    native_focal = loss_module.SigmoidFocalClassificationLoss.forward

    def capture_focal(module, logits, targets, weights):
        focal_targets.append(targets.detach().cpu().clone())
        return native_focal(module, logits, targets, weights)

    def capture_match(*args):
        result = native_match(*args)
        matches.append(result)
        return result

    model.criterion.match_sampled_ins = capture_match
    if args.replay:
        loss_module.SigmoidFocalClassificationLoss.forward = capture_focal
    handle = model.criterion.register_forward_pre_hook(
        lambda module, inputs: held.update(fps=inputs[7], args=inputs))
    results = []
    backward_scenes = set()
    try:
        with torch.set_grad_enabled(args.parameter_backward):
            for batch in loader:
                superpoints, semantics, instances = transformed.pop("axes")
                sp = [int(x) for x in superpoints]
                inst = [int(x) for x in instances]
                sem = [int(x) for x in semantics]
                first = {}
                for i, instance in enumerate(inst):
                    first.setdefault(instance, sem[i])
                classes = {}
                for instance, label in first.items():
                    nyu = int(source.sem2nyu[label]) if label >= 0 else -1
                    classes[instance] = source.nyu40id2class.get(nyu, -1)
                point_classes = [classes[instance] for instance in inst]
                held.clear()
                matches.clear()
                focal_targets.clear()
                gorilla.set_random_seed(1999)
                loss, _ = model(batch, mode="loss")
                if not bool(torch.isfinite(loss).all()):
                    raise ValueError("Nonfinite native loss")
                fps = held["fps"]
                if len(matches) != 2 * len(batch["object_idss"]):
                    raise ValueError("Native seed/query matching call count differs")
                scenes = [scene for scene, count in zip(
                    batch["scan_ids"], batch["scenes_len"])
                    for _ in range(int(count))]
                for b, (scene, ann_id) in enumerate(zip(scenes, batch["ann_ids"])):
                    key = scene, int(ann_id)
                    if key not in frozen or frozen[key]["arm"] != "phrase":
                        continue
                    text = (" ".join(source.scene_graphs[scene][str(ann_id)]
                                     ["utterance"].replace(",", " ,").split())
                            + " . not mentioned")
                    if text != frozen[key]["text"]:
                        raise ValueError("Frozen native utterance differs")
                    context = {source.type2class[word] for word in text.split()
                               if word in source.type2class and word != "others"}
                    result = physical_support(
                        sp, inst, point_classes, batch["object_idss"][b],
                        context, frozen[key]["nontarget_curtain_instances"],
                        batch["sp_ref_masks"][b])
                    changed = set(result["changed_superpoints"])
                    topk, _, matched, _ = matches[2 * b]
                    protected = {int(i) for i in topk} | {int(i) for i in matched[0]}
                    treatment_seeds = {
                        i for i, index in enumerate(fps[b])
                        if int(index) in changed and i not in protected
                    }
                    placebo_seeds = {
                        i for i, index in enumerate(fps[b])
                        if int(index) in result["placebo_pool"]
                        and i not in protected
                    }
                    if any(
                        result["baseline"][int(fps[b][i])] != 0
                        or abs(result["treated"][int(fps[b][i])] - 0.5) > 1e-6
                        for i in treatment_seeds
                    ):
                        raise ValueError("Nonuniform eligible treatment magnitude")
                    row = {
                        "scene": scene, "ann_id": int(ann_id),
                        "target_instances": frozen[key]["target_instances"],
                        "changed_superpoints": len(changed),
                        "changed_fps_seeds_before_overwrite": sum(
                            int(i) in changed for i in fps[b]),
                        "mixed_changed_superpoints": len(result["mixed_changed"]),
                        "zero_support_placebo_pool": len(result["placebo_pool"]),
                        "placebo_fps_seeds_before_overwrite": sum(
                            int(i) in result["placebo_pool"] for i in fps[b]),
                        "protected_seed_count": len(protected),
                        "eligible_final_treatment_seeds": len(treatment_seeds),
                        "eligible_final_placebo_seeds": len(placebo_seeds),
                    }
                    if args.replay:
                        if not treatment_seeds or len(placebo_seeds) < len(treatment_seeds):
                            row["replay_exclusion"] = "No equal-count final seed placebo"
                        else:
                            instance_by_sp = {}
                            for sp_index, instance in zip(sp, inst):
                                instance_by_sp.setdefault(sp_index, set()).add(instance)
                            chosen = sorted(
                                placebo_seeds,
                                key=lambda i: (
                                    min(instance_by_sp[int(fps[b][i])]),
                                    int(fps[b][i]), i),
                            )[:len(treatment_seeds)]
                            placebo = list(result["baseline"])
                            for i in chosen:
                                placebo[int(fps[b][i])] = 0.5
                            native_references = held["args"][2]
                            references = list(native_references)
                            references[b] = torch.as_tensor(
                                result["treated"], dtype=references[b].dtype,
                                device=references[b].device)
                            placebo_references = list(native_references)
                            placebo_references[b] = torch.as_tensor(
                                placebo, dtype=placebo_references[b].dtype,
                                device=placebo_references[b].device)

                            def replay(refs):
                                ref_score = held["args"][0]["ref_scores"].detach().requires_grad_()
                                pred = dict(held["args"][0], ref_scores=ref_score)
                                replay_args = list(held["args"])
                                replay_args[0] = pred
                                replay_args[2] = refs
                                focal_targets.clear()
                                with torch.enable_grad():
                                    _, components = model.criterion(*replay_args)
                                    grad = torch.autograd.grad(
                                        components["sample_loss"].sum(), ref_score)[0]
                                if len(focal_targets) != 1:
                                    raise ValueError("Sample focal target count differs")
                                return (
                                    focal_targets[0][b].flatten().tolist(),
                                    {key: float(value.detach().mean())
                                     for key, value in components.items() if key != "loss"},
                                    grad[b].detach().cpu().flatten(),
                                )

                            baseline = replay(native_references)
                            repeat = replay(native_references)
                            if (any(abs(a - b) > 1e-6 for a, b in zip(
                                    baseline[0], repeat[0])) or any(
                                    abs(value - repeat[1][key]) > 1e-6
                                    for key, value in baseline[1].items())):
                                target_diffs = sum(
                                    abs(a - b) > 1e-6
                                    for a, b in zip(baseline[0], repeat[0]))
                                loss_diffs = {
                                    key: (value, repeat[1][key])
                                    for key, value in baseline[1].items()
                                    if abs(value - repeat[1][key]) > 1e-6
                                }
                                raise ValueError(
                                    "Same-forward baseline replay differs: "
                                    f"scene={scene} ann={ann_id} "
                                    f"target_diffs={target_diffs} "
                                    f"loss_diffs={loss_diffs}")
                            treated = replay(references)
                            control = replay(placebo_references)
                            final = check_final_targets(
                                baseline[0], treated[0], control[0], protected,
                                treatment_seeds, set(chosen))
                            check_non_sample_losses(
                                baseline[1], treated[1], control[1])
                            if any(not torch.isfinite(g).all() for g in (
                                    baseline[2], treated[2], control[2])):
                                raise ValueError("Nonfinite sample gradient")
                            row["replay"] = {
                                **final,
                                "baseline_sample_loss": baseline[1]["sample_loss"],
                                "treated_sample_loss": treated[1]["sample_loss"],
                                "placebo_sample_loss": control[1]["sample_loss"],
                                "treated_gradient_delta_l1": float(
                                    (treated[2] - baseline[2]).abs().sum()),
                                "placebo_gradient_delta_l1": float(
                                    (control[2] - baseline[2]).abs().sum()),
                                "baseline_replay_equal": True,
                                "non_sample_losses_equal": True,
                            }
                            if args.parameter_backward and scene not in backward_scenes:
                                params = [p for p in model.dec.sampling_module.parameters()
                                          if p.requires_grad]
                                if not params:
                                    raise ValueError("No trainable sampler parameters")

                                def parameter_grad(refs):
                                    pred = dict(held["args"][0])
                                    replay_args = list(held["args"])
                                    replay_args[0] = pred
                                    replay_args[2] = refs
                                    _, components = model.criterion(*replay_args)
                                    grads = torch.autograd.grad(
                                        components["sample_loss"].sum(), params,
                                        retain_graph=True, allow_unused=True)
                                    if any(g is None or not bool(torch.isfinite(g).all())
                                           for g in grads):
                                        raise ValueError("Missing or nonfinite sampler gradient")
                                    return [g.detach() for g in grads]

                                bg = parameter_grad(native_references)
                                tg = parameter_grad(references)
                                pg = parameter_grad(placebo_references)
                                delta = lambda a, b: sum(
                                    float((x - y).abs().sum())
                                    for x, y in zip(a, b))
                                row["sampler_parameter_backward"] = {
                                    "trainable_tensors": len(params),
                                    "baseline_grad_l1": sum(float(g.abs().sum()) for g in bg),
                                    "treated_delta_l1": delta(bg, tg),
                                    "placebo_delta_l1": delta(bg, pg),
                                }
                                if row["sampler_parameter_backward"]["treated_delta_l1"] <= 0:
                                    raise ValueError("No sampler-parameter treatment effect")
                                backward_scenes.add(scene)
                    results.append(row)
    finally:
        handle.remove()
        model.criterion.match_sampled_ins = native_match
        if args.replay:
            loss_module.SigmoidFocalClassificationLoss.forward = native_focal
    if len(results) != 11:
        raise ValueError("Incomplete frozen phrase cohort")
    output.write_text(json.dumps({
        "contract": ("m95_native31_same_forward_replay_v1" if args.replay
                     else "m95_native31_support_incidence_v2"), "admission": False,
        "manifest_sha256": sha(args.manifest),
        "checkpoint_sha256": CHECKPOINT_SHA, "inputs": expected,
        "rows": results,
        "limits": ("Same-forward frozen TRAIN loss replay, no model-weight update or "
                   "inference/efficacy claim; sampler-parameter backward, resource "
                   "and independent mechanism gates remain pending."
                   if args.replay else
                   "Native matcher-protected seed eligibility only; final focal "
                   "target replay, matched placebo and gradients still untested."),
    }, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "rows": len(results),
        "with_changed_fps": sum(r["changed_fps_seeds_before_overwrite"] > 0 for r in results),
        "with_placebo_fps": sum(r["placebo_fps_seeds_before_overwrite"] > 0 for r in results),
        "eligible_rows": sum(r["eligible_final_treatment_seeds"] > 0 and
                             r["eligible_final_placebo_seeds"] >=
                             r["eligible_final_treatment_seeds"] for r in results),
        "replayed_rows": sum("replay" in r for r in results),
        "parameter_backward_scenes": len(backward_scenes),
    }))


if __name__ == "__main__":
    main()
