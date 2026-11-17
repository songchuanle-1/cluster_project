"""Native physical-support parameter-backward diagnosis over full TRAIN exposure."""
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
    select_native_indices, selected_loader, sha,
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
    parser.add_argument("--population", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--parameter-backward", action="store_true")
    parser.add_argument("--score-matched-placebo", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    if (os.environ.get("CUDA_VISIBLE_DEVICES") != "7" or output.exists()
            or not output.is_relative_to(root.parent / "pipeline")
            or sha(args.checkpoint) != CHECKPOINT_SHA):
        raise ValueError("GPU7, fresh project output and frozen checkpoint required")
    if args.parameter_backward and not args.replay:
        raise ValueError("Parameter backward needs same-forward replay")
    if sha(args.population) != "325626925578df183ef3f8ffdce2b7cb7f010ccefa87de70db0b4b1353f0d664":
        raise ValueError("Full TRAIN population hash differs")
    population = json.loads(args.population.read_text(encoding="utf-8"))
    if (population["contract"] != "m95_multiword_population_v1"
            or population["summary"]["qualifying_expressions"] != 102):
        raise ValueError("Full TRAIN cohort differs")
    frozen = {
        (row["scene"], int(row["ann_id"])): {
            "scene": row["scene"], "ann_id": int(row["ann_id"]),
            "target_instances": row["target_instances"],
            "nontarget_curtain_instances": row["other_curtain_instances"],
            "arm": "phrase",
        } for row in population["rows"] if row["other_curtain_instances"]
    }
    if len(frozen) != 102 or len({s for s, _ in frozen}) != 28:
        raise ValueError("Full TRAIN identities differ")
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
    for (scene, ann_id), row in frozen.items():
        row["text"] = (" ".join(source.scene_graphs[scene][str(ann_id)]
                                 ["utterance"].replace(",", " ,").split())
                       + " . not mentioned")
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
                native_args = held["args"]
                fps = native_args[7]
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
                    try:
                        result = physical_support(
                            sp, inst, point_classes, batch["object_idss"][b],
                            context, frozen[key]["nontarget_curtain_instances"],
                            batch["sp_ref_masks"][b])
                    except ValueError as error:
                        if str(error) not in ("Curtain cropped or noncontiguous superpoints",
                                              "No physical phrase support changed"):
                            raise
                        results.append({
                            "scene": scene, "ann_id": int(ann_id),
                            "target_instances": frozen[key]["target_instances"],
                            "replay_exclusion": str(error),
                        })
                        continue
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
                        results.append({
                            "scene": scene, "ann_id": int(ann_id),
                            "target_instances": frozen[key]["target_instances"],
                            "replay_exclusion": "Nonuniform eligible treatment magnitude",
                        })
                        continue
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
                            if args.score_matched_placebo:
                                score = native_args[0]["ref_scores"][b].detach()
                                pool = set(placebo_seeds)
                                chosen = []
                                for treatment in sorted(treatment_seeds):
                                    candidate = min(
                                        pool, key=lambda i: (
                                            abs(float(score[i] - score[treatment])), i))
                                    chosen.append(candidate)
                                    pool.remove(candidate)
                                row["baseline_score_pair_abs_mean"] = sum(
                                    abs(float(score[t] - score[c]))
                                    for t, c in zip(sorted(treatment_seeds), chosen)
                                ) / len(chosen)
                            else:
                                chosen = sorted(
                                    placebo_seeds,
                                    key=lambda i: (
                                        min(instance_by_sp[int(fps[b][i])]),
                                        int(fps[b][i]), i),
                                )[:len(treatment_seeds)]
                            placebo = list(result["baseline"])
                            for i in chosen:
                                placebo[int(fps[b][i])] = 0.5
                            native_references = native_args[2]
                            references = list(native_references)
                            references[b] = torch.as_tensor(
                                result["treated"], dtype=references[b].dtype,
                                device=references[b].device)
                            placebo_references = list(native_references)
                            placebo_references[b] = torch.as_tensor(
                                placebo, dtype=placebo_references[b].dtype,
                                device=placebo_references[b].device)

                            def replay(refs):
                                ref_score = native_args[0]["ref_scores"].detach().requires_grad_()
                                pred = dict(native_args[0], ref_scores=ref_score)
                                replay_args = list(native_args)
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
                                row["replay_exclusion"] = (
                                    "Same-forward baseline replay differs: "
                                    f"target_diffs={target_diffs} "
                                    f"loss_diffs={loss_diffs}")
                                results.append(row)
                                continue
                            treated = replay(references)
                            control = replay(placebo_references)
                            try:
                                final = check_final_targets(
                                    baseline[0], treated[0], control[0],
                                    protected, treatment_seeds, set(chosen))
                            except ValueError as error:
                                row["replay_exclusion"] = (
                                    "Final target parity failed: " + str(error))
                                results.append(row)
                                continue
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
                            if args.parameter_backward:
                                named_params = [
                                    (name, p) for name, p in
                                    model.dec.sampling_module.named_parameters()
                                    if p.requires_grad
                                ]
                                params = [p for _, p in named_params]
                                if not params:
                                    raise ValueError("No trainable sampler parameters")

                                def parameter_grad(refs):
                                    pred = dict(native_args[0])
                                    replay_args = list(native_args)
                                    replay_args[0] = pred
                                    replay_args[2] = refs
                                    _, components = model.criterion(*replay_args)
                                    grads = torch.autograd.grad(
                                        components["sample_loss"].sum(), params,
                                        retain_graph=True, allow_unused=True)
                                    if any(g is not None and
                                           not bool(torch.isfinite(g).all())
                                           for g in grads):
                                        raise ValueError("Nonfinite sampler gradient")
                                    return [g.detach() if g is not None else None
                                            for g in grads]

                                bg = parameter_grad(native_references)
                                tg = parameter_grad(references)
                                pg = parameter_grad(placebo_references)
                                patterns = [[g is not None for g in arm]
                                            for arm in (bg, tg, pg)]
                                if patterns[0] != patterns[1] or patterns[0] != patterns[2]:
                                    raise ValueError("Sampler gradient connectivity changed")
                                active = [i for i, used in enumerate(patterns[0]) if used]
                                if not active:
                                    raise ValueError("No connected sampler parameters")
                                delta = lambda a, b: sum(
                                    float((a[i] - b[i]).abs().sum()) for i in active)
                                row["sampler_parameter_backward"] = {
                                    "trainable_tensors": len(params),
                                    "connected_tensors": len(active),
                                    "disconnected_names": [
                                        name for (name, _), used in
                                        zip(named_params, patterns[0]) if not used
                                    ],
                                    "baseline_grad_l1": sum(
                                        float(bg[i].abs().sum()) for i in active),
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
    if len(results) != 102 or len({(r["scene"], r["ann_id"]) for r in results}) != 102:
        raise ValueError("Incomplete full TRAIN phrase cohort")
    replayed = [row for row in results if "replay" in row]
    output.write_text(json.dumps({
        "contract": ("m95_full_train_score_matched_placebo_v1"
                     if args.score_matched_placebo
                     else "m95_full_train_support_backward_v1"),
        "admission": False,
        "population_sha256": sha(args.population),
        "checkpoint_sha256": CHECKPOINT_SHA, "inputs": expected,
        "rows": results,
        "summary": {
            "cohort": len(results), "replayed": len(replayed),
            "replay_excluded": len(results) - len(replayed),
            "replayed_scenes": len({r["scene"] for r in replayed}),
            "excluded_reasons": {
                reason: sum(r.get("replay_exclusion") == reason for r in results)
                for reason in sorted({r["replay_exclusion"] for r in results
                                      if "replay_exclusion" in r})
            },
        },
        "limits": ("Same-forward frozen TRAIN loss replay, no model-weight update or "
                   "inference/efficacy claim; old sampler-parameter connectivity "
                   "is diagnostic only, candidate native-backward, resource and "
                   "independent mechanism gates remain pending."
                   if args.replay else
                   "Native matcher-protected seed eligibility only; final focal "
                   "target replay, matched placebo and gradients still untested."),
    }, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "rows": len(results),
        "replayed_rows": len(replayed),
        "replay_excluded": len(results) - len(replayed),
        "parameter_backward_scenes": len(backward_scenes),
        "parameter_backward_rows": sum(
            "sampler_parameter_backward" in row for row in results),
    }))


if __name__ == "__main__":
    main()
