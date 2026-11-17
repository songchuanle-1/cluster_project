"""Matched native feature decomposition; no changed model or inference path."""
import hashlib
import json
from pathlib import Path

parent = Path(__file__).with_name("coverage_stage_capture_20260916.py")
source = parent.read_text().split("\nmodel.criterion.register_forward_pre_hook(capture)")[0]
ns = {"__file__": str(parent)}
exec(compile(source, str(parent), "exec"), ns)
torch, model = ns["torch"], ns["model"]
pipeline = ns["ROOT"].parent / "pipeline"
inventory_path = pipeline / "instance_feature_audit_20260916/result.json"
inventory = json.loads(inventory_path.read_text())
lookup = {(r["scene"], int(r["ann_id"])): r for r in inventory["rows"]}
parts, rows = {}, []


def save_part(name):
    def hook(module, args, output):
        parts[name] = output.detach()
    return hook


model.dec.input_proj.register_forward_hook(save_part("three_d"))
model.dec.input_proj_2d.register_forward_hook(save_part("two_d"))
model.dec.sum_norm.register_forward_hook(save_part("fused"))


def norm(x):
    return float(x.double().square().sum().sqrt())


def record(module, args):
    ns["rows"].clear()
    ns["capture"](module, args)
    labels, offsets = args[4], args[9]
    for b, observed in enumerate(ns["rows"]):
        identity = (observed["scene"], observed["ann_id"])
        old = lookup[identity]
        lo, hi = int(offsets[b]), int(offsets[b + 1])
        assert hi - lo == len(labels[b])
        target = int(old["target"])
        neighbors = old["nearest_clip"]
        assert neighbors, identity
        # Neighbor selected by raw cached feature distance, never outcome.
        neighbor = int(neighbors[0][0])
        target_mask, neighbor_mask = labels[b] == target, labels[b] == neighbor
        row = dict(scene=identity[0], ann_id=identity[1], target=target,
                   neighbor=neighbor, original_iou=old["before"],
                   native_iou=observed["layers"][-1]["selected"],
                   original_winner=old["winner"],
                   original_winner_overlap=old["winner_overlap"],
                   missing=not bool(target_mask.any() and neighbor_mask.any()))
        if not row["missing"]:
            diffs = {}
            for name, part in parts.items():
                feat = part[lo:hi].double()
                diffs[name] = feat[target_mask].mean(0) - feat[neighbor_mask].mean(0)
            a, v = diffs["three_d"], diffs["two_d"]
            denominator = float(a.square().sum() + v.square().sum())
            dot = float((a * v).sum())
            # Signed interference, invariant to a shared orthogonal basis change.
            row.update(
                norms={name: norm(diff) for name, diff in diffs.items()},
                sum_norm=norm(a + v), energy=denominator,
                cross_term=2 * dot,
                cancellation_ratio=(2 * dot / denominator if denominator else None),
                cosine=(dot / (norm(a) * norm(v)) if norm(a) * norm(v) else None),
                target_sps=int(target_mask.sum()), neighbor_sps=int(neighbor_mask.sum()),
            )
            assert abs(norm(a + v) ** 2 - denominator - 2 * dot) < 1e-7 * max(denominator, 1)
        rows.append(row)


model.criterion.register_forward_pre_hook(record)
with torch.no_grad():
    for step, batch in enumerate(ns["batches"]):
        ns["current"].update(step=step, batch=batch)
        ns["gorilla"].set_random_seed(1999)
        loss, _ = model(batch, mode="loss")
        assert torch.isfinite(loss).all()
        print(json.dumps(dict(batch=step, rows=len(rows))), flush=True)
assert len(rows) == 123
output = pipeline / "modality_cancellation_20260916"
output.mkdir(exist_ok=True)
report = dict(rows=rows, scope="Same original16TRAIN batches;M95weights/eval unchanged. "
              "Nearest raw2D neighbor selected without outcomes. Descriptive signed "
              "interference in projected instance centroids,not causal efficacy. "
              "Augmented majority SP labels;missing neighbors explicit. No new model.",
              sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (parent, Path(__file__), inventory_path, ns["checkpoint"])})
(output / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
