"""Read-only native M95 TRAIN seed-target audit on server-6 GPU7."""
import argparse
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys


NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CHECKPOINT_SHA = "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def batch_fingerprint(torch, batch):
    h = hashlib.sha256()
    for key in ("voxel_coords", "p2v_map", "v2p_map", "feats",
                "superpoints", "coords_float", "sp_ins_labels",
                "lang_tokenss", "lang_masks", "gt_spmasks", "sp_ref_masks"):
        values = batch[key]
        if not isinstance(values, (list, tuple)):
            values = [values]
        h.update(key.encode("ascii"))
        for value in values:
            tensor = torch.as_tensor(value).detach().cpu().contiguous()
            h.update(str((tuple(tensor.shape), str(tensor.dtype))).encode("ascii"))
            h.update(tensor.numpy().tobytes())
    return h.hexdigest()


def role_gradients(torch, batch, pred, fps, labels, match_calls, focal_calls,
                   sampler_input, triples):
    loss_module = importlib.import_module(
        "framework.model.Quard_model." + NAME + ".loss")
    calls = [c for c in focal_calls
             if tuple(c["logits"].shape[:2]) == tuple(pred["ref_scores"].shape)]
    if len(calls) != 1 or not torch.equal(
            calls[0]["logits"].squeeze(-1), pred["ref_scores"].detach()):
        raise ValueError("Native sample focal capture differs")
    if sampler_input.shape[:2] != fps.shape:
        raise ValueError("Sampler/FPS axes differ")
    target = calls[0]["target"].squeeze(-1)
    valid = (~pred["batch_mask"]).gather(1, fps.long())
    focal = loss_module.SigmoidFocalClassificationLoss()
    native = (focal(pred["ref_scores"].unsqueeze(-1),
                    target.unsqueeze(-1), calls[0]["weights"])
              .squeeze(-1) * valid)
    scenes = [scene for scene, count in zip(batch["scan_ids"], batch["scenes_len"])
              for _ in range(int(count))]
    keys = {(scene, int(batch["ann_ids"][i])): i
            for i, scene in enumerate(scenes)}
    if len(keys) != len(scenes):
        raise ValueError("Duplicate expression identity")
    involved = set()
    selected = []
    for triple in triples:
        scene = triple["scene"]
        ids = [keys.get((scene, int(triple[role + "_ann"])))
               for role in ("target", "context", "zero")]
        if any(i is None for i in ids):
            continue
        selected.append((triple, ids))
        involved.update(ids)
    grads = {}
    score_grads = {}
    for i in sorted(involved):
        grad, score_grad = torch.autograd.grad(
            native[i].sum(), (sampler_input, pred["ref_scores"]),
            retain_graph=True)
        if not bool(torch.isfinite(grad).all()):
            raise ValueError("Nonfinite native focal sampler gradient")
        grads[i] = grad[i].detach()
        score_grads[i] = score_grad[i].detach()
    output = []
    for triple, (a, b, c) in selected:
        instance = int(triple["target_instance"])
        if set(map(int, batch["object_idss"][a])) != {instance}:
            raise ValueError("Target instance differs")
        protected = []
        for i in (a, b, c):
            topk, _, matched, _ = match_calls[2 * i]
            protected.append(set(topk.tolist()) | set(matched[0].tolist()))
        for seed in triple["shared_fps_positions"]:
            i = int(seed)
            if len({int(fps[j, i]) for j in (a, b, c)}) != 1:
                raise ValueError("FPS physical superpoint mismatch")
            if any(int(labels[j][fps[j, i].long()]) != instance
                   for j in (a, b, c)):
                raise ValueError("Physical instance mismatch")
            if not (torch.equal(sampler_input[a, i], sampler_input[b, i])
                    and torch.equal(sampler_input[a, i], sampler_input[c, i])):
                raise ValueError("Sampler feature differs across expressions")
            if (i in protected[1] or i in protected[2]
                    or float(target[b, i]) != .25
                    or float(target[c, i]) != 0.):
                raise ValueError("Non-target role differs from preregistration")
            g = [grads[j][i] for j in (a, b, c)]
            norms = [float(x.norm()) for x in g]
            dots = [float(torch.dot(g[0], x)) for x in g[1:]]
            output.append({
                "scene": triple["scene"], "target_ann": triple["target_ann"],
                "context_ann": triple["context_ann"],
                "zero_ann": triple["zero_ann"], "instance": instance,
                "fps_position": i, "superpoint": int(fps[a, i]),
                "target_final_label": float(target[a, i]),
                "target_protected": i in protected[0],
                "logits": [float(pred["ref_scores"][j, i].detach())
                           for j in (a, b, c)],
                "scalar_gradients": [float(score_grads[j][i])
                                     for j in (a, b, c)],
                "norms": norms, "dots": dots,
                "cosines": [dot / (norms[0] * norms[k + 1])
                            if norms[0] and norms[k + 1] else None
                            for k, dot in enumerate(dots)],
            })
    return output


def target_seed_direction(torch, batch, pred, fps, labels, focal_calls,
                          original_focal_forward):
    loss_module = importlib.import_module(
        "framework.model.Quard_model." + NAME + ".loss")
    call = next(c for c in focal_calls
                if tuple(c["logits"].shape[:2]) == tuple(pred["ref_scores"].shape))
    target = call["target"].squeeze(-1)
    valid = (~pred["batch_mask"]).gather(1, fps.long())
    focal = loss_module.SigmoidFocalClassificationLoss()
    old_forward = loss_module.SigmoidFocalClassificationLoss.forward
    loss_module.SigmoidFocalClassificationLoss.forward = original_focal_forward
    try:
        values = (focal(pred["ref_scores"].unsqueeze(-1),
                        call["target"], call["weights"])
                  .squeeze(-1) * valid)
    finally:
        loss_module.SigmoidFocalClassificationLoss.forward = old_forward
    gradient, = torch.autograd.grad(values.sum(), pred["ref_scores"],
                                    retain_graph=True)
    output = []
    for b, ids in enumerate(batch["object_idss"]):
        if len(ids) != 1:
            raise ValueError("Expected unique target instance")
        physical = labels[b][fps[b].long()]
        target_id = int(ids[0])
        indices = [i for i in range(fps.shape[1])
                   if bool(valid[b, i]) and int(physical[i]) == target_id]
        output.append({
            "ann_id": int(batch["ann_ids"][b]),
            "instance": target_id,
            "physical_target_superpoints": int((labels[b] == target_id).sum()),
            "scene_superpoints": len(labels[b]),
            "valid_fps_count": int(valid[b].sum()),
            "target_seed_count": len(indices),
            "seeds": [
                [int(i), float(target[b, i]), float(pred["ref_scores"][b, i].detach()),
                 float(gradient[b, i])]
                for i in indices
            ],
        })
    return output


def bag_intervention(torch, batch, pred, fps, labels, match_calls, focal_calls,
                     params):
    loss_module = importlib.import_module(
        "framework.model.Quard_model." + NAME + ".loss")
    focal = loss_module.SigmoidFocalClassificationLoss()
    call = next(c for c in focal_calls
                if tuple(c["logits"].shape[:2]) == tuple(pred["ref_scores"].shape))
    target = call["target"].squeeze(-1).detach()
    logits = pred["ref_scores"]
    valid = (~pred["batch_mask"]).gather(1, fps.long())
    weights = call["weights"].detach()
    hard = target.clone()
    physical, shuffled, coverage, bag_regimes = [], [], [], []
    for b, ids in enumerate(batch["object_idss"]):
        topk, _, matched, _ = match_calls[2 * b]
        protected = set(topk.tolist()) | set(matched[0].tolist())
        instances = labels[b][fps[b].long()]
        groups = {}
        for i, instance in enumerate(instances.tolist()):
            if (i not in protected and instance >= 0 and instance not in ids
                    and bool(valid[b, i]) and float(target[b, i]) == .25):
                groups.setdefault(int(instance), []).append(i)
                hard[b, i] = 0
        bags = [indices for _, indices in sorted(groups.items())
                if len(indices) >= 2]
        flat = [i for indices in bags for i in indices]
        sizes = [len(indices) for indices in bags]
        interleaved = [
            indices[position]
            for position in range(max(sizes, default=0))
            for indices in bags if position < len(indices)
        ]
        offsets = [0]
        for size in sizes:
            offsets.append(offsets[-1] + size)
        controls = [interleaved[offsets[j]:offsets[j + 1]]
                    for j in range(len(sizes))]
        physical.append(bags)
        shuffled.append(controls)
        regimes = []
        for indices in bags:
            values = logits[b, indices].detach().clone().requires_grad_(True)
            probability = -torch.expm1(
                torch.nn.functional.logsigmoid(-values).sum())
            clipped = probability.clamp(1e-6, 1 - 1e-6)
            bag_logit = torch.logit(clipped)
            objective = focal(
                bag_logit.reshape(1, 1),
                torch.full_like(bag_logit.reshape(1, 1), .25),
                torch.ones(1, device=values.device)).sum()
            gradient, = torch.autograd.grad(objective, values)
            regimes.append({
                "size": len(indices),
                "probability": float(probability.detach()),
                "clipped": float(clipped.detach()),
                "member_grad_positive": int((gradient > 0).sum()),
                "member_grad_negative": int((gradient < 0).sum()),
                "member_grad_abs_sum": float(gradient.abs().sum()),
            })
        bag_regimes.append(regimes)
        coverage.append({
            "eligible_seeds": sum(len(x) for x in groups.values()),
            "groups_at_least_two": len(bags),
            "grouped_seeds": len(flat),
            "singleton_groups": sum(len(x) == 1 for x in groups.values()),
            "shuffled_membership_changed": any(
                set(x) != set(y) for x, y in zip(bags, controls)),
            "seeds_moved_to_other_bags": sum(
                len(set(x) - set(y)) for x, y in zip(bags, controls)),
        })

    def base_loss(tgt):
        return (focal(logits.unsqueeze(-1), tgt.unsqueeze(-1), weights)
                .squeeze(-1) * valid).sum(-1).mean()

    def group_loss(bags):
        per_expression = []
        for b, groups in enumerate(bags):
            if not groups:
                per_expression.append(logits[b].sum() * 0)
                continue
            bag_logits = []
            for indices in groups:
                z = logits[b, indices]
                probability = -torch.expm1(torch.nn.functional.logsigmoid(-z).sum())
                probability = probability.clamp(1e-6, 1 - 1e-6)
                bag_logits.append(torch.logit(probability))
            stacked = torch.stack(bag_logits)
            bag_target = torch.full_like(stacked, .25)
            bag_weight = torch.ones_like(stacked) / len(groups)
            value = focal(stacked[:, None], bag_target[:, None], bag_weight).sum()
            per_expression.append(
                value * sum(map(len, groups)) / valid[b].sum().clamp_min(1))
        return torch.stack(per_expression).mean()

    values = {
        "original": base_loss(target),
        "hard_zero": base_loss(hard),
        "physical_bag": base_loss(hard) + group_loss(physical),
        "shuffled_bag": base_loss(hard) + group_loss(shuffled),
    }
    trainable = [p for p in params if p.requires_grad]
    gradients = {}
    for name, value in values.items():
        grads = torch.autograd.grad(value, trainable, retain_graph=True,
                                    allow_unused=True)
        if any(g is None or not bool(torch.isfinite(g).all()) for g in grads):
            raise ValueError("Missing or nonfinite bag-intervention gradient")
        gradients[name] = [g.detach() for g in grads]
    def delta(left, right):
        return sum(float((x - y).abs().sum())
                   for x, y in zip(gradients[left], gradients[right]))
    return {
        "coverage": coverage,
        "bag_regimes": bag_regimes,
        "losses": {name: float(value.detach()) for name, value in values.items()},
        "parameter_tensors": len(trainable),
        "gradient_l1": {name: sum(float(g.abs().sum()) for g in grad)
                        for name, grad in gradients.items()},
        "gradient_delta_l1": {
            "physical_vs_original": delta("physical_bag", "original"),
            "physical_vs_hard_zero": delta("physical_bag", "hard_zero"),
            "physical_vs_shuffled": delta("physical_bag", "shuffled_bag"),
        },
        "unchanged_inference_forward": True,
    }


def analyze(torch, batch, pred, fps, labels, match_calls, focal_calls, *,
            intervention=False, backward_params=None, role_census=False,
            mask_reachability=False):
    if len(match_calls) != 2 * len(batch["object_idss"]):
        raise ValueError("Native matcher call count differs")
    seed_call = [call for call in focal_calls
                 if tuple(call["logits"].shape[:2]) == tuple(pred["ref_scores"].shape)]
    if len(seed_call) != 1:
        raise ValueError("Native sample focal call not unique")
    call = seed_call[0]
    if not torch.equal(call["logits"].squeeze(-1), pred["ref_scores"].detach()):
        raise ValueError("Sample focal logits differ from native ref_scores")
    target = call["target"].squeeze(-1)
    pre = torch.nn.utils.rnn.pad_sequence(
        [x.to(fps.device) for x in batch["sp_ref_masks"]],
        batch_first=True, padding_value=0).gather(1, fps.long())
    if tuple(pre.shape) != tuple(target.shape):
        raise ValueError("Seed supervision axes differ")
    rows = []
    selections = []
    for b, ids in enumerate(batch["object_idss"]):
        topk, _, matched, _ = match_calls[2 * b]
        protected = set(topk.tolist()) | set(matched[0].tolist())
        sp_ids = fps[b].long()
        if sp_ids.min() < 0 or sp_ids.max() >= len(labels[b]):
            raise ValueError("Native FPS index outside criterion label axis")
        instances = labels[b][sp_ids]
        targets = set(map(int, ids))
        context = ((pre[b] == 0.5) & ~torch.tensor(
            [int(x) in targets for x in instances], device=pre.device))
        eligible = [i for i in range(len(sp_ids))
                    if bool(context[i]) and i not in protected]
        controls = [i for i in range(len(sp_ids))
                    if i not in protected and int(instances[i]) not in targets
                    and float(target[b, i]) == 0.0]
        controls.sort(key=lambda i: (
            min((abs(float(score_value) - float(pred["ref_scores"][b, i]))
                 for score_value in pred["ref_scores"][b, eligible]), default=float("inf")),
            i))
        controls = controls[:len(eligible)]
        same_instance_controls = {}
        for i in eligible:
            instance_id = int(instances[i])
            same_instance_controls[i] = [
                j for j in range(len(sp_ids))
                if j not in protected and j != i
                and int(instances[j]) == instance_id
                and float(target[b, j]) == 0.0
            ]
        if intervention and len(controls) < len(eligible):
            raise ValueError("Insufficient unprotected non-target placebo seeds")
        selections.append((eligible, controls))
        changed = [i for i in range(len(sp_ids))
                   if not torch.isclose(target[b, i], pre[b, i] * 0.5, atol=1e-6)]
        score = pred["ref_scores"][b]
        selected = int(pred["indis"][b].softmax(-1)[:, 1].argmax())
        selected_seed = int(pred["sample_inds"][b, selected])
        gt = batch["gt_spmasks"][b].to(score.device).flatten().bool()
        mask = pred["masks"][b, selected, :len(gt)] > 0
        selected_iou = float(
            (mask & gt).sum().float() / (mask | gt).sum().clamp_min(1))
        rows.append({
            "ann_id": int(batch["ann_ids"][b]),
            "fps_count": len(sp_ids), "topk": topk.tolist(),
            "matched": matched[0].tolist(),
            "pre_context_count": int(context.sum()),
            "unmatched_non_target_context": len(eligible),
            "eligible_final_values": sorted(set(float(target[b, i]) for i in eligible)),
            "eligible_logits_mean": float(score[eligible].mean()) if eligible else None,
            "changed_from_half_pre_count": len(changed),
            "changed_outside_protected": sorted(set(changed) - protected),
            "placebo_count": len(controls),
            "same_instance_zero_control_eligible": sum(
                bool(pool) for pool in same_instance_controls.values()),
            "same_instance_zero_control_total": sum(
                len(pool) for pool in same_instance_controls.values()),
            "selected_context_same_instance_zero_controls": (
                len(same_instance_controls[selected_seed])
                if selected_seed in same_instance_controls else None),
            "selected_query": selected,
            "selected_seed": selected_seed,
            "selected_seed_instance": int(instances[selected_seed]),
            "target_instances": sorted(targets),
            "selected_seed_matches_target_instance": int(instances[selected_seed]) in targets,
            "selected_seed_pre_context": float(pre[b, selected_seed]),
            "selected_seed_final_target": float(target[b, selected_seed]),
            "selected_seed_is_context": selected_seed in eligible,
            "selected_mask_iou": selected_iou,
        })
        if role_census:
            rows[-1]["unprotected_seed_roles"] = [
                [i, int(instances[i]), float(target[b, i])]
                for i in range(len(sp_ids))
                if i not in protected and int(instances[i]) >= 0
                and int(instances[i]) not in targets
            ]
        if mask_reachability:
            seed_sp = int(sp_ids[selected_seed])
            instance_mask = labels[b][:len(gt)] == instances[selected_seed]
            if seed_sp >= len(gt) or not bool(instance_mask[seed_sp]):
                raise ValueError("Selected seed/instance superpoint axis differs")
            rows[-1]["selected_seed_in_selected_mask"] = bool(mask[seed_sp])
            rows[-1]["selected_mask_seed_instance_iou"] = float(
                (mask & instance_mask).sum().float()
                / (mask | instance_mask).sum().clamp_min(1))
        if any(not torch.isclose(target[b, i], pre[b, i] * 0.5, atol=1e-6)
               for i in eligible):
            raise ValueError("Unexpected overwrite outside matched/topk")
    if intervention:
        replay = importlib.import_module(
            "framework.model.Quard_model." + NAME + ".loss"
        ).SigmoidFocalClassificationLoss()
        raw = pred["ref_scores"].detach().clone().requires_grad_(True)
        base = target.detach().clone()
        treated, placebo = base.clone(), base.clone()
        for b, (eligible, controls) in enumerate(selections):
            treated[b, eligible] = 0
            placebo[b, controls] = 0.25
        valid = (~pred["batch_mask"]).gather(1, fps.long())
        weights = call["weights"].detach()

        def loss_gradient(tgt):
            value = (replay(raw.unsqueeze(-1), tgt.unsqueeze(-1), weights)
                     .squeeze(-1) * valid).sum(-1).mean()
            grad, = torch.autograd.grad(value, raw)
            return float(value.detach()), grad.detach()

        base_loss, base_grad = loss_gradient(base)
        treated_loss, treated_grad = loss_gradient(treated)
        placebo_loss, placebo_grad = loss_gradient(placebo)
        for b, (eligible, controls) in enumerate(selections):
            untouched = [i for i in range(raw.shape[1])
                         if i not in set(eligible) | set(controls)]
            rows[b]["intervention"] = {
                "baseline_loss": base_loss, "treated_loss": treated_loss,
                "placebo_loss": placebo_loss,
                "treated_grad_change_l1": float(
                    (treated_grad[b, eligible] - base_grad[b, eligible]).abs().sum()),
                "placebo_grad_change_l1": float(
                    (placebo_grad[b, controls] - base_grad[b, controls]).abs().sum()),
                "untouched_grad_change_max": float(
                    (treated_grad[b, untouched] - base_grad[b, untouched]).abs().max()),
                "immediate_referent_argmax_tested": False,
            }
        if backward_params is not None:
            trainable = [p for p in backward_params if p.requires_grad]
            if not trainable:
                raise ValueError("No trainable sampling parameters")
            def parameter_gradient(tgt, retain):
                loss = (replay(pred["ref_scores"].unsqueeze(-1),
                               tgt.unsqueeze(-1), weights)
                        .squeeze(-1) * valid).sum(-1).mean()
                grads = torch.autograd.grad(
                    loss, trainable, retain_graph=retain, allow_unused=True)
                return [g.detach() if g is not None else None for g in grads]
            bg = parameter_gradient(base, True)
            tg = parameter_gradient(treated, True)
            pg = parameter_gradient(placebo, False)
            def difference(left, right):
                return sum(float((a - b).abs().sum()) for a, b in zip(left, right)
                           if a is not None and b is not None)
            if any(g is None or not bool(torch.isfinite(g).all())
                   for g in bg + tg + pg):
                raise ValueError("Missing or nonfinite native sampling gradient")
            rows[0]["parameter_backward"] = {
                "trainable_tensors": len(trainable),
                "baseline_grad_l1": sum(float(g.abs().sum()) for g in bg),
                "treated_delta_l1": difference(bg, tg),
                "placebo_delta_l1": difference(bg, pg),
            }
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--batches", type=int, default=2)
    p.add_argument("--intervention", action="store_true")
    p.add_argument("--parameter-backward", action="store_true")
    p.add_argument("--targeted-indices", action="store_true")
    p.add_argument("--manifest-population", type=Path)
    p.add_argument("--transform-seed", type=int, default=1999)
    p.add_argument("--fingerprint-input", action="store_true")
    p.add_argument("--role-census", action="store_true")
    p.add_argument("--mask-reachability", action="store_true")
    p.add_argument("--instance-bag", action="store_true")
    p.add_argument("--role-gradient-triples", type=Path)
    p.add_argument("--target-seed-direction", action="store_true")
    args = p.parse_args()
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "7" or args.batches < 1:
        raise ValueError("Authorized GPU7 and positive batch count required")
    if args.parameter_backward and not args.intervention:
        raise ValueError("Parameter backward requires registered intervention")
    if args.instance_bag and (args.intervention or args.batches > 16):
        raise ValueError("Instance bag requires at most 16 batches without other intervention")
    if args.role_gradient_triples and (
            args.intervention or args.instance_bag or args.batches != 16
            or not args.manifest_population or args.transform_seed != 1999):
        raise ValueError("Role-gradient capture requires frozen 16-batch population")
    if args.target_seed_direction and (
            args.intervention or args.instance_bag or args.role_gradient_triples
            or args.batches != 16 or not args.manifest_population
            or args.transform_seed != 1999 or not args.fingerprint_input):
        raise ValueError("Target seed direction requires frozen 16-batch population")
    if args.manifest_population and args.targeted_indices:
        raise ValueError("Choose one cohort")
    if args.output.exists() or not args.output.parent.is_dir():
        raise ValueError("Fresh output and existing parent required")
    root = args.root.resolve()
    triples = None
    if args.role_gradient_triples:
        expected = "m95_role_triple_screen_v1"
        triples = json.loads(args.role_gradient_triples.read_text(encoding="utf-8"))
        if triples.get("contract") != expected or triples.get("role_triples") != 38:
            raise ValueError("Role triple manifest changed")
    if digest(args.checkpoint) != CHECKPOINT_SHA:
        raise ValueError("M95 checkpoint hash differs")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import torch
    import gorilla
    from framework.dataset import build_dataset, build_dataloader
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    config = root / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(args.transform_seed)
    dataset = build_dataset(cfg.data.train, logging.getLogger("seed-target-probe"))
    population_keys = None
    if args.manifest_population:
        expected = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
        if digest(args.manifest_population) != expected:
            raise ValueError("Manifest identity differs")
        manifest = json.loads(args.manifest_population.read_text(encoding="ascii"))
        if (manifest.get("contract") != "m95_preregistered_identity_controls_v1"
                or len(manifest.get("rows", [])) != 256
                or any(int(r["manifest_index"]) != i
                       for i, r in enumerate(manifest["rows"]))):
            raise ValueError("Frozen manifest structure differs")
        selected = [manifest["rows"][i] for i in
                    (*range(16), *range(128, 144))]
        population_keys = {(r["scene_id"], int(r["ann_id"])) for r in selected}
        source_inputs = dataset.scene_inputs
        indices = []
        seen = set()
        for idx, expressions in enumerate(source_inputs):
            matched = {(r.get("scene_id"), int(r.get("ann_id")))
                       for r in expressions if (r.get("scene_id"),
                                                  int(r.get("ann_id"))) in population_keys}
            if matched:
                indices.append(idx)
                seen.update(matched)
        if seen != population_keys:
            raise ValueError("Frozen expression identities absent from native dataset")
        source_dataset = dataset
        class PopulationDataset:
            def __len__(self):
                return len(indices)
            def __getitem__(self, index):
                return source_dataset[indices[index]]
            def collate_fn(self, items):
                return source_dataset.collate_fn(items)
        dataset = PopulationDataset()
    if args.targeted_indices:
        source_dataset = dataset
        class SelectedDataset:
            indices = (8096, 8815)
            def __len__(self):
                return len(self.indices)
            def __getitem__(self, index):
                return source_dataset[self.indices[index]]
            def collate_fn(self, items):
                return source_dataset.collate_fn(items)
        dataset = SelectedDataset()
    loader = build_dataloader(dataset, batch_size=2, num_workers=0,
                              persistent_workers=False)
    model = importlib.import_module("framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    loss_module = importlib.import_module("framework.model.Quard_model." + NAME + ".loss")
    original_focal = loss_module.SigmoidFocalClassificationLoss.forward
    original_match = model.criterion.match_sampled_ins
    held, matches, focals, rows, bag_results, gradient_rows, target_seed_rows = (
        {}, [], [], [], [], [], [])

    def prehook(module, inputs):
        held["pred"], held["labels"], held["fps"] = inputs[0], inputs[4], inputs[7]

    def match(*inputs, **kwargs):
        result = original_match(*inputs, **kwargs)
        matches.append(result)
        return result

    def focal(self, logits, target, weights):
        if logits.ndim == 3:
            focals.append({"logits": logits.detach().clone(),
                           "target": target.detach().clone(),
                           "weights": weights.detach().clone()})
        return original_focal(self, logits, target, weights)

    def sampler_prehook(module, inputs):
        held["sampler_input"] = inputs[0]

    handle = model.criterion.register_forward_pre_hook(prehook)
    sampler_handle = model.dec.sampling_module.register_forward_pre_hook(
        sampler_prehook) if triples else None
    model.criterion.match_sampled_ins = match
    loss_module.SigmoidFocalClassificationLoss.forward = focal
    try:
        for step, batch in enumerate(loader):
            fingerprint = batch_fingerprint(torch, batch) if args.fingerprint_input else None
            held.clear()
            matches.clear()
            focals.clear()
            gorilla.set_random_seed(1999)
            with torch.set_grad_enabled(
                    args.parameter_backward or args.instance_bag or bool(triples)
                    or args.target_seed_direction):
                loss, components = model(batch, mode="loss")
            if args.target_seed_direction:
                target_seed_rows.extend(target_seed_direction(
                    torch, batch, held["pred"], held["fps"], held["labels"],
                    focals, original_focal))
            if triples:
                sample_call = next(c for c in focals
                    if tuple(c["logits"].shape[:2]) ==
                    tuple(held["pred"]["ref_scores"].shape))
                valid = (~held["pred"]["batch_mask"]).gather(
                    1, held["fps"].long())
                replay = loss_module.SigmoidFocalClassificationLoss()
                original_forward = loss_module.SigmoidFocalClassificationLoss.forward
                loss_module.SigmoidFocalClassificationLoss.forward = original_focal
                try:
                    reconstructed = (replay(
                    held["pred"]["ref_scores"].unsqueeze(-1),
                    sample_call["target"], sample_call["weights"])
                    .squeeze(-1) * valid).sum(-1).mean()
                finally:
                    loss_module.SigmoidFocalClassificationLoss.forward = original_forward
                if not torch.allclose(reconstructed, components["sample_loss"],
                                      atol=1e-6, rtol=1e-5):
                    raise ValueError("Native sample loss replay mismatch")
                gradient_rows.extend(role_gradients(
                    torch, batch, held["pred"], held["fps"], held["labels"],
                    matches, focals, held["sampler_input"], triples["triples"]))
                del focals[1:]
            current = analyze(torch, batch, held["pred"], held["fps"], held["labels"],
                              matches, focals, intervention=args.intervention,
                              backward_params=(model.dec.sampling_module.parameters()
                                               if args.parameter_backward else None),
                              role_census=args.role_census,
                              mask_reachability=args.mask_reachability)
            scenes = [scene for scene, count in zip(batch["scan_ids"], batch["scenes_len"])
                      for _ in range(int(count))]
            for row, scene in zip(current, scenes):
                row["scene"] = scene
                row["batch"] = step
                if fingerprint:
                    row["batch_input_sha256"] = fingerprint
            rows.extend(current)
            if args.instance_bag:
                bag_results.append(bag_intervention(
                    torch, batch, held["pred"], held["fps"], held["labels"],
                    matches, focals, model.dec.sampling_module.parameters()))
            print(json.dumps({"batch": step, "rows": len(rows),
                              "sample_loss": float(components["sample_loss"])}), flush=True)
            if step + 1 >= args.batches:
                break
    finally:
        loss_module.SigmoidFocalClassificationLoss.forward = original_focal
        model.criterion.match_sampled_ins = original_match
        handle.remove()
        if sampler_handle:
            sampler_handle.remove()
    if triples and len(gradient_rows) != sum(
            len(x["shared_fps_positions"]) for x in triples["triples"]):
        raise ValueError("Frozen triple positions not fully covered")
    if args.target_seed_direction and len(target_seed_rows) != 128:
        raise ValueError("Frozen target-seed expression count differs")
    args.output.write_text(json.dumps({
        "contract": "m95_seed_loss_intervention_v1" if args.intervention
                    else "m95_final_seed_target_diagnostic_v1",
        "admission": False, "checkpoint_sha256": CHECKPOINT_SHA,
        "config_sha256": digest(config),
        "loss_source_sha256": digest(root / "framework/model/Quard_model" / NAME / "loss.py"),
        "targeted_indices": [8096, 8815] if args.targeted_indices else None,
        "population_manifest_sha256": (
            digest(args.manifest_population) if args.manifest_population else None),
        "transform_seed": args.transform_seed,
        "exact_input_fingerprints": args.fingerprint_input,
        "role_census": args.role_census,
        "mask_reachability": args.mask_reachability,
        "bag_intervention": bag_results if args.instance_bag else None,
        "role_gradient_rows": gradient_rows if triples else None,
        "target_seed_direction_rows": target_seed_rows if args.target_seed_direction else None,
        "role_triples_sha256": (
            digest(args.role_gradient_triples) if triples else None),
        "population_selected": (
            [{"scene": r["scene"], "ann_id": r["ann_id"],
              "context": r["unmatched_non_target_context"],
              "selected_context": r["selected_seed_is_context"],
              "selected_iou": r["selected_mask_iou"]}
             for r in rows if (r["scene"], r["ann_id"]) in population_keys]
            if population_keys else None),
        "rows": rows,
        "limits": ("Same-forward focal-logit gradients only; placebo is count/logit-matched "
                   "but not class/instance-matched; no parameter backward, optimizer, or efficacy claim."
                   if args.intervention else
                   "Passive native loss-target census; no paired intervention, backward, or efficacy claim.")
    }, indent=2) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
