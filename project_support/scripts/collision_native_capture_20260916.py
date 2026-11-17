"""Fixed TRAIN collision pairs: native scores with repeat/shared-support controls."""
import copy
import hashlib
import json
from pathlib import Path

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
source = base.read_text().split("model.criterion.register_forward_pre_hook(capture)")[0]
ns = {"__file__": str(base)}
exec(compile(source, str(base), "exec"), ns)
torch, model, batches = ns["torch"], ns["model"], ns["batches"]
gorilla = ns["gorilla"]
pairs = {"scene0493_00": (11, 9), "scene0288_00": (28, 29),
         "scene0319_00": (34, 35), "scene0192_00": (6, 4),
         "scene0452_00": (56, 57)}
state, reports = {}, []
destination = ns["ROOT"].parent / "pipeline/collision_native_20260916"
destination.mkdir(exist_ok=True)


def sample_hook(module, args, output):
    inds, scores = output
    if state["branch"] == "shared":
        inds = inds.clone()
        offset = 0
        for scene, count in zip(state["batch"]["scan_ids"], state["batch"]["scenes_len"]):
            count = int(count)
            if scene in pairs:
                annotations = state["batch"]["ann_ids"][offset:offset+count]
                selected = [i for i, a in enumerate(annotations) if int(a) == pairs[scene][0]]
                assert len(selected) == 1
                inds[offset:offset+count] = state["base_samples"][offset+selected[0]]
            offset += count
    return inds, scores


def collector(module, args):
    pred, _, _, object_ids, labels = args[:5]
    fps = args[7].long()
    batch = state["batch"]
    scenes = [s for s, c in zip(batch["scan_ids"], batch["scenes_len"])
              for _ in range(int(c))]
    if state["branch"] == "base":
        state["base_samples"] = pred["sample_inds"].detach().clone()
    current = []
    for b, scene in enumerate(scenes):
        ann = int(batch["ann_ids"][b])
        if scene not in pairs or ann not in pairs[scene]:
            continue
        physical = fps[b][pred["sample_inds"][b].long()]
        d = pred["indis"][b, :, 1] - pred["indis"][b, :, 0]
        mask = pred["masks"][b, :, :len(labels[b])]
        chosen = int(d.argmax())
        n_tokens = int(batch["lang_masks"][b].sum())
        token_similarity = pred["proj_queries"][b] @ pred["proj_tokens"][b].T
        cell = []
        pair_targets = {int(obj) for i, ids in enumerate(object_ids)
                        if scenes[i] == scene and int(batch["ann_ids"][i]) in pairs[scene]
                        for obj in ids}
        for identity in sorted(pair_targets):
            target = labels[b] == identity
            qids = torch.where(target[physical])[0]
            masks = mask.sigmoid() >= .5
            overlaps = ((masks & target).sum(-1) /
                        (masks | target).sum(-1).clamp_min(1))
            cell.append(dict(instance=identity, queries=len(qids),
                mean_logit=float(d[qids].mean()) if len(qids) else None,
                best_mask_iou=float(overlaps.max()),
                chosen_mask_iou=float(overlaps[chosen]),
                mean_token_cosine=token_similarity[qids, :n_tokens].mean(0).cpu().tolist()
                                  if len(qids) else None))
        current.append(dict(scene=scene, ann_id=ann,
            targets=[int(o) for o in object_ids[b]],
            physical_seeds=physical.cpu().tolist(),
            seed_labels=labels[b][physical].cpu().tolist(),
            logits=d.cpu().tolist(), selected_query=chosen,
            tokens=ns["dataset"].tokenizer.convert_ids_to_tokens(
                batch["lang_tokenss"][b, :n_tokens].tolist()), cells=cell))
    state["result"] = current


model.dec.sampling_module.register_forward_hook(sample_hook)
model.criterion.register_forward_pre_hook(collector)
with torch.no_grad():
    for step, batch in enumerate(batches):
        if not set(batch["scan_ids"]).intersection(pairs):
            continue
        state["batch"] = batch
        branches = {}
        for branch in ("base", "repeat", "shared"):
            state["branch"] = branch
            gorilla.set_random_seed(1999)
            loss, _ = model(copy.deepcopy(batch), mode="loss")
            assert torch.isfinite(loss).all()
            branches[branch] = copy.deepcopy(state["result"])
        repeat_checks = []
        for a, b in zip(branches["base"], branches["repeat"]):
            repeat_checks.append(dict(scene=a["scene"], ann_id=a["ann_id"],
                same_physical_support=a["physical_seeds"] == b["physical_seeds"],
                max_logit_delta=max(abs(x-y) for x, y in zip(a["logits"], b["logits"])),
                same_selected_query=a["selected_query"] == b["selected_query"]))
        assert all(r["same_physical_support"] for r in repeat_checks)
        for scene in set(batch["scan_ids"]).intersection(pairs):
            shared = [r for r in branches["shared"] if r["scene"] == scene]
            assert len(shared) == 2
            assert shared[0]["physical_seeds"] == shared[1]["physical_seeds"]
        reports.append(dict(batch=step, branches=branches, repeat_checks=repeat_checks))
        print(json.dumps(dict(batch=step, pairs=len(branches["base"])//2,
                              repeat_checks=repeat_checks, shared_support_equal=True)), flush=True)
report = dict(batches=reports, pairs=pairs,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (base, Path(__file__), ns["config"], ns["checkpoint"])},
    scope="Preselected five TRAIN pairs,original descriptions,exact repeat and "
          "shared physical support. GT membership for diagnosis only;not ranking "
          "mechanism,causal relation truth or training admission.")
(destination / "result.json").write_text(json.dumps(report, indent=2))
