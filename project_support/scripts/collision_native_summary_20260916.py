"""Paired native collision evidence; no optimized rule or training claim."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "pipeline/reports/collision_native_20260916.json"
data = json.loads(source.read_text())
rows = []
repeat = []
for batch in data["batches"]:
    repeat.extend(batch["repeat_checks"])
    shared = batch["branches"]["shared"]
    assert len(shared) == 2
    assert shared[0]["physical_seeds"] == shared[1]["physical_seeds"]
    scene = shared[0]["scene"]
    bad_ann, control_ann = data["pairs"][scene]
    a = next(r for r in shared if r["ann_id"] == bad_ann)
    b = next(r for r in shared if r["ann_id"] == control_ann)
    target, wrong = a["targets"][0], b["targets"][0]
    cells_a = {c["instance"]: c for c in a["cells"]}
    cells_b = {c["instance"]: c for c in b["cells"]}
    complete = all(c["queries"] for c in [*cells_a.values(), *cells_b.values()])
    row = dict(scene=scene, wrong_ann=bad_ann, control_ann=control_ann,
               target=target, winner=wrong, complete_seed_support=bool(complete),
               target_chosen_iou=cells_a[target]["chosen_mask_iou"],
               wrong_chosen_iou=cells_a[wrong]["chosen_mask_iou"],
               control_chosen_iou=cells_b[wrong]["chosen_mask_iou"])
    if complete:
        margin_a = cells_a[target]["mean_logit"] - cells_a[wrong]["mean_logit"]
        margin_b = cells_b[target]["mean_logit"] - cells_b[wrong]["mean_logit"]
        row.update(target_margin_under_target_description=margin_a,
                   target_margin_under_winner_description=margin_b,
                   description_margin_change=margin_a-margin_b)
        token_rows = []
        for label, expression, cells in [("target", a, cells_a), ("control", b, cells_b)]:
            token_rows.append(dict(description=label, ann_id=expression["ann_id"],
                values=[dict(token=token, target_minus_winner_cosine=x-y)
                        for token, x, y in zip(expression["tokens"],
                            cells[target]["mean_token_cosine"],
                            cells[wrong]["mean_token_cosine"])]))
        row["token_evidence"] = token_rows
    rows.append(row)
assert len(rows) == 5
assert all(r["same_physical_support"] for r in repeat)
summary = dict(pairs=5, complete_seed_pairs=sum(r["complete_seed_support"] for r in rows),
    missing_seed_pairs=sum(not r["complete_seed_support"] for r in rows),
    wrong_preserved=sum(r["wrong_chosen_iou"] > .5 and r["target_chosen_iou"] <= .5 for r in rows),
    control_success_preserved=sum(r["control_chosen_iou"] > .5 for r in rows),
    positive_description_margin_change=sum(r.get("description_margin_change", 0) > 0 for r in rows),
    negative_description_margin_change=sum(r.get("description_margin_change", 0) < 0 for r in rows),
    repeat_max_logit_delta=max(r["max_logit_delta"] for r in repeat),
    repeat_selected_changes=sum(not r["same_selected_query"] for r in repeat))
report = dict(summary=summary, rows=rows, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    interpretation="Shared-support collisions survive. Language changes soft scores, not uniformly "
    "in the desired direction;do not claim complete language insensitivity. Missing seed pair "
    "cannot support seed-level comparison. Four-cell margin is diagnostic, not renewed CPS loss. "
    "Token cosines are contextual and not causal attribution. Five outcome-selected scenes "
    "are not population estimates or new-model efficacy.")
(root / "pipeline/reports/collision_native_summary_20260916.json").write_text(
    json.dumps(report, indent=2))
print(json.dumps(summary, indent=2))
for row in rows:
    print({k: v for k, v in row.items() if k != "token_evidence"})
