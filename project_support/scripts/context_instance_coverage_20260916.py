"""Native same-forward coverage of non-target instances, not anchor labels."""
import copy
import hashlib
import json
from pathlib import Path

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
ns = {"__file__": str(base)}
exec(compile(base.read_text().split(
    "model.criterion.register_forward_pre_hook(capture)")[0], str(base), "exec"), ns)
torch, model = ns["torch"], ns["model"]
raw_path = Path("/data3/songcl/data/data_cluster/scannetv2/train")
names, rows, state = {}, [], {}


def collect(module, args):
    pred, _, _, targets, labels = args[:5]
    batch = state["batch"]
    scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
              for _ in range(int(n))]
    for b, (scene, annotation, target_ids) in enumerate(
            zip(scenes, batch["ann_ids"], targets)):
        if scene not in names:
            source = raw_path / f"{scene}.aggregation.json"
            names[scene] = {int(g["id"]): g["label"]
                           for g in json.loads(source.read_text())["segGroups"]}
        graph = ns["dataset"].scene_graphs[scene][str(int(annotation))]
        nouns = {n["target"].lower() for n in graph["graph_node"]
                 if n["node_id"] != 0 and n["node_type"] == "Object"}
        instance = labels[b].long()
        hard = pred["masks"][b, :, :len(instance)].sigmoid() >= .5
        seed_ids = instance[args[7][b].long()][pred["sample_inds"][b].long()]
        entries = []
        for identity in instance.unique().tolist():
            if identity < 0 or identity == 199:
                continue
            truth = instance == identity
            iou = ((hard & truth).sum(-1).float()
                   / ((hard | truth).sum(-1).float() + 1e-6))
            best, query = iou.max(0)
            own_queries = seed_ids == identity
            entries.append(dict(instance=identity, name=names[scene].get(identity),
                target=identity in [int(v) for v in target_ids],
                exact_other_noun=names[scene].get(identity, "").lower() in nouns,
                support=int(truth.sum()), sampled_seeds=int(own_queries.sum()),
                oracle_iou=float(best), oracle_query=int(query),
                own_seed_best_iou=float(iou[own_queries].max()) if own_queries.any() else None))
        rows.append(dict(scene=scene, ann_id=int(annotation), instances=entries))


model.criterion.register_forward_pre_hook(collect)
with torch.no_grad():
    for step, batch in enumerate(ns["batches"]):
        state["batch"] = batch
        ns["gorilla"].set_random_seed(1999)
        loss, _ = model(copy.deepcopy(batch), mode="loss")
        assert torch.isfinite(loss).all()
        print(json.dumps(dict(batch=step, expressions=len(rows))), flush=True)
summary = {}
for group in ("target", "nontarget", "exact_other_noun"):
    entries = [e for r in rows for e in r["instances"]
               if (e["target"] if group == "target" else
                   not e["target"] if group == "nontarget" else
                   e["exact_other_noun"] and not e["target"])]
    summary[group] = dict(instance_expression_pairs=len(entries),
        covered=sum(e["oracle_iou"] > .5 for e in entries),
        seed_present=sum(e["sampled_seeds"] > 0 for e in entries),
        own_seed_covered=sum(e["own_seed_best_iou"] is not None and
                             e["own_seed_best_iou"] > .5 for e in entries))
out = ns["ROOT"].parent / "pipeline/context_instance_coverage_20260916"
out.mkdir(exist_ok=True)
result = dict(summary=summary, rows=rows,
    scope="Fixed123TRAIN expressions. Instance-expression pairs are repeated scene "
          "instances, not independent observations. Exact raw noun match is not "
          "anchor truth. Mask-bank oracle uses GT only for diagnosis.",
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), base, ns["checkpoint"])})
(out / "result.json").write_text(json.dumps(result, indent=2))
print(json.dumps(summary), flush=True)
