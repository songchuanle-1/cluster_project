"""Expression-paired model comparison with scene bootstrap and explicit regressions."""
import hashlib
import json
import random
import statistics
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "pipeline/reports"
source = root / "baseline_matched_20260916.json"
data = json.loads(source.read_text())["results"]
names = {(r["scene"], r["ann_id"]): r for r in
         json.loads((root / "anchor_instance_names_20260916.json").read_text())["rows"]}
assert len(data["champion"]) == len(data["baseline"]) == 123
rows = []
for champion, baseline in zip(data["champion"], data["baseline"]):
    identity = (champion["scene"], champion["ann_id"])
    assert identity == (baseline["scene"], baseline["ann_id"])
    a, b = champion["layers"][-1], baseline["layers"][-1]
    transition = ("preserved" if b["selected"] > .5 else "repaired") if a["selected"] > .5 else (
        "regressed" if b["selected"] > .5 else "both_failed")
    rows.append(dict(scene=identity[0], ann_id=identity[1],
        utterance=names[identity]["utterance"], transition=transition,
        baseline_selected=b["selected"], champion_selected=a["selected"],
        baseline_oracle=b["best"], champion_oracle=a["best"],
        baseline_rank=baseline["language_rank"], champion_rank=champion["language_rank"],
        baseline_fps_target=baseline["fps_target"], champion_fps_target=champion["fps_target"],
        baseline_sampled_target=baseline["sampled_target"],
        champion_sampled_target=champion["sampled_target"],
        delta=a["selected"]-b["selected"]))
assert len({(r["scene"], r["ann_id"]) for r in rows}) == 123
scene_means = [statistics.mean(r["delta"] for r in rows if r["scene"] == scene)
               for scene in sorted({r["scene"] for r in rows})]
rng = random.Random(1999)
bootstrap = sorted(statistics.mean(rng.choices(scene_means, k=len(scene_means)))
                   for _ in range(10000))
summary = dict(expressions=123, scenes=len(scene_means),
    transitions={k: sum(r["transition"] == k for r in rows)
                 for k in ("preserved", "repaired", "regressed", "both_failed")},
    expression_mean_delta=statistics.mean(r["delta"] for r in rows),
    scene_mean_delta=statistics.mean(scene_means),
    scene_bootstrap95=[bootstrap[249], bootstrap[9749]],
    regression_recoverable=sum(r["transition"] == "regressed" and r["champion_oracle"] > .5
                              for r in rows),
    regression_mask_limited=sum(r["transition"] == "regressed" and r["champion_oracle"] <= .5
                               for r in rows))
report = dict(summary=summary, rows=rows,
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    limitations="Fixed TRAIN comparison,not overall validation ranking or isolated cluster "
    "causality. Same batch objects but native sampling and model/checkpoint differ. "
    "Oracle is diagnostic only. Regressions selected after outcomes;not independent test.")
(root / "baseline_matched_summary_20260916.json").write_text(json.dumps(report, indent=2))
print(json.dumps(summary, indent=2))
for row in rows:
    if row["transition"] == "regressed":
        print(json.dumps(row))
