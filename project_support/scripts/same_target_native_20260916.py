"""Preregistered same-target TRAIN description audit on existing fixed scenes."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
source = base.read_text().split("model.criterion.register_forward_pre_hook(capture)")[0]
ns = {"__file__": str(base)}
exec(compile(source, str(base), "exec"), ns)
torch, model, dataset = ns["torch"], ns["model"], ns["dataset"]
root = ns["ROOT"].parent / "pipeline"
inventory = root / "anchor_identity_20260916/instance_names.json"
scenes = {r["scene"] for r in json.loads(inventory.read_text())["rows"]}
annotation_file = Path(dataset.data_root) / "scanrefer/ScanRefer_train_new.json"
annotations = json.loads(annotation_file.read_text())
by_scene = defaultdict(lambda: defaultdict(list))
for r in annotations:
    if r["scene_id"] in scenes:
        by_scene[r["scene_id"]][int(r["object_id"])].append(r)
groups, manifest = [], []
for scene in sorted(scenes):
    eligible = [(obj, sorted(rs, key=lambda r: int(r["ann_id"])))
                for obj, rs in sorted(by_scene[scene].items()) if len(rs) >= 2]
    selected = [r for _, rs in eligible[:2] for r in rs[:2]]
    manifest.append(dict(scene=scene, eligible_objects=len(eligible),
        selected=[dict(object_id=r["object_id"], ann_id=r["ann_id"],
                       description=r["description"]) for r in selected]))
    if selected:
        groups.append(selected)
dataset.scene_inputs = groups
loader = ns["build_dataloader"](dataset, batch_size=1, num_workers=0,
                               persistent_workers=False)
state, results = {}, []
native_expand = model.expand_and_fps


def expand(*args, **kwargs):
    out = native_expand(*args, **kwargs)
    fps = out[2]
    # Each batch is exactly one physical scene repeated for its descriptions.
    return (*out[:2], fps[:1].expand_as(fps).clone(), *out[3:])


def collect(module, args):
    ns["rows"].clear()
    ns["capture"](module, args)
    pred, _, _, targets, labels = args[:5]
    for b, row in enumerate(ns["rows"]):
        n = len(labels[b])
        chosen = int(pred["indis"][b].softmax(-1)[:, 1].argmax())
        mask = pred["masks"][b, chosen, :n].sigmoid() >= .5
        ids = labels[b].unique()
        ids = ids[ids >= 0]
        overlaps = []
        for obj in ids:
            target = labels[b] == obj
            overlaps.append(float((mask & target).sum() /
                                  (mask | target).sum().clamp_min(1)))
        winner = max(range(len(ids)), key=lambda j: overlaps[j]) if len(ids) else None
        row.update(winner_id=int(ids[winner]) if winner is not None else None,
            winner_overlap=overlaps[winner] if winner is not None else 0,
            target_ids=[int(o) for o in targets[b]],
            before=row["layers"][-1]["selected"],
            utterance=groups[state["step"]][b]["description"])
        results.append(dict(row))
    assert all(torch.equal(args[7][0], x) for x in args[7])


model.expand_and_fps = expand
model.criterion.register_forward_pre_hook(collect)
ns["gorilla"].set_random_seed(1999)
with torch.no_grad():
    for step, batch in enumerate(loader):
        state["step"] = step
        ns["current"].update(step=step, batch=batch)
        loss, _ = model(batch, mode="loss")
        assert torch.isfinite(loss).all()
        print(json.dumps(dict(batch=step, expressions=len(results))), flush=True)
output = root / "same_target_native_20260916"
output.mkdir(exist_ok=True)
report = dict(rows=results, manifest=manifest,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (base, Path(__file__), inventory, annotation_file, ns["checkpoint"])},
    scope="Existing32TRAINscenes;first2eligible objectIDs,first2annIDs each. "
    "Shared augmented scene/FPS,independent language-conditioned sampling. "
    "No cross-forward query joins,no model edits,no efficacy/admission claim.")
(output / "result.json").write_text(json.dumps(report, indent=2))
