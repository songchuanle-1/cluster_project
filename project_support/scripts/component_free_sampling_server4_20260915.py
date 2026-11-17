"""Native free-sampling capture; raw query-index comparisons are NOT valid metrics."""
import ast
from pathlib import Path

# Existing verified full-loss worker; execute this only on server4.
source = Path("/tmp/component_parameter_step_20260915.py")
tree = ast.parse(source.read_text())
setup = '''
physical_trace = []
def record_seeds(module, args, result):
    seeds = args[1].detach().gather(1, result["sample_inds"].detach().long())
    physical_trace.append(seeds.cpu().clone())
model.dec.register_forward_hook(record_seeds)
'''
for node in list(tree.body):
    if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "out" for t in node.targets):
        node.value = ast.parse('Path("/tmp/component_free_sampling_server4_20260915")', mode="eval").body
    if isinstance(node, ast.For) and isinstance(node.target, ast.Tuple):
        if any(isinstance(t, ast.Name) and t.id == "step" for t in node.target.elts):
            index = tree.body.index(node)
            tree.body[index:index] = ast.parse(setup).body
            node.body.insert(0, ast.parse("physical_trace.clear()").body[0])
            node.body.extend(ast.parse('''
assert len(physical_trace) == 4
torch.save(dict(before=physical_trace[0],global_seeds=physical_trace[1],
                component=physical_trace[2],global_repeat=physical_trace[3]),
           out / f"batch_{step}_physical_seeds.pth")
''').body)
ast.fix_missing_locations(tree)
exec(compile(tree, str(source), "exec"), {"__name__": "__main__", "__file__": __file__})
# Persist aligned metrics separately; never interpret inherited raw query comparisons.
import json
import torch
from component_seed_alignment import alignment_plan, support_bounds

out = Path("/tmp/component_free_sampling_server4_20260915")
aligned = []
for batch_id in (0, 1):
    seeds = torch.load(out / f"batch_{batch_id}_physical_seeds.pth", weights_only=True)
    runs = {name: torch.load(out / f"batch_{batch_id}_{name}.pth", weights_only=False)
            for name in ("global", "component", "global_repeat")}
    rows, coverage = [], []
    for expression in range(len(seeds["before"])):
        plans = alignment_plan(seeds["before"][expression].tolist(), {
            name: seeds["global_seeds" if name == "global" else name][expression].tolist()
            for name in runs})
        coverage.append(dict(expression=expression, **plans))
        for record in runs["global"]["records"]:
            if record["expression"] != expression:
                continue
            seed = int(seeds["before"][expression, record["query"]])
            if seed not in plans["common"]:
                continue
            y = runs["global"]["targets"][expression][record["target"]].bool()
            metrics = {}
            for name, run in runs.items():
                # One physical seed may be repeated by native FPS; aggregate logits.
                logits = run["after"][expression][plans["indices"][name][seed]].mean(0)
                probability = logits.sigmoid()
                hard = probability > .5
                metrics[name] = dict(
                    hard_iou=float((hard & y).sum() / (hard | y).sum().clamp_min(1)),
                    soft_iou=float((probability*y).sum() /
                                   (probability+y-probability*y).sum().clamp_min(1e-8)))
            rows.append(dict(expression=expression, seed=seed, target=record["target"],
                             components=len(record["groups"]), metrics=metrics))
    bounds = {}
    for subset in ("all", "connected", "disconnected"):
        def included(record):
            size = record["components"] if "components" in record else len(record["groups"])
            return subset == "all" or (size == 1 if subset == "connected" else size > 1)
        total = sum(included(r) for r in runs["global"]["records"])
        deltas = [r["metrics"]["component"]["hard_iou"] -
                  r["metrics"]["global"]["hard_iou"] for r in rows if included(r)]
        bounds[subset] = support_bounds(total, deltas)
    aligned.append(dict(batch=batch_id, coverage=coverage, rows=rows,
                        full_support_hard_iou_bounds=bounds))
(out / "aligned.json").write_text(json.dumps(dict(
    results=aligned,
    scope="Common-support matched-query estimand; excluded support explicitly reported. "
          "Duplicate seeds averaged, original matched-query multiplicity retained. "
          "Not deployable selected-output performance or validation mIoU."), indent=2))
