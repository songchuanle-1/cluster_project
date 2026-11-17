"""Summarize existing exact query axes; no resampling or model execution."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    source = root / "pipeline/reports/native_support_capture_20260916-1517.json"
    capture = json.loads(source.read_text(encoding="utf-8"))
    scenes = defaultdict(list)
    groups = defaultdict(list)
    cells = defaultdict(lambda: dict(n=0, score_sum=0., positive=0))
    for row in capture["rows"]:
        scenes[row["scene"]].append(row)
        groups[(row["scene"], tuple(row["target_instances"]))].append(row)
        for score, iou, seed, positive in zip(row["scores"], row["ious"],
                                             row["seed_inside"], row["native_positive"]):
            cell = cells["seed%d_mask%d" % (seed, iou > .5)]
            cell["n"] += 1
            cell["score_sum"] += score
            cell["positive"] += positive
    for cell in cells.values():
        cell["mean_score"] = cell.pop("score_sum") / cell["n"]
        cell["positive_fraction"] = cell["positive"] / cell["n"]
    summary = {}
    for scene, rows in scenes.items():
        summary[scene] = dict(
            expressions=len(rows),
            selected_success=sum(r["ious"][r["selected_query"]] > .5 for r in rows) / len(rows),
            no_acceptable=sum(r["best_acceptable_rank"] is None for r in rows),
            acceptable_top5=sum(r["best_acceptable_rank"] is not None
                                and r["best_acceptable_rank"] <= 5 for r in rows) / len(rows))
    repeated = []
    for (scene, targets), rows in groups.items():
        if len(rows) > 1:
            repeated.append(dict(scene=scene, targets=targets,
                                 annotations=[r["ann_id"] for r in rows],
                                 same_support=len({r["support_sha256"] for r in rows}) == 1,
                                 note="support_sha256 includes expression identity; verify physical axes separately",
                                 physical_axes_equal=all(
                                     r["original_superpoint_ids"] == rows[0]["original_superpoint_ids"]
                                     and r["sample_inverse"] == rows[0]["sample_inverse"]
                                     and r["scene_occurrence"] == rows[0]["scene_occurrence"]
                                     for r in rows)))
    report = dict(scope="Descriptive query contingency and repeated-target inventory, same 16-expression capture",
                  source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  scene_summary=summary, query_contingency=dict(cells),
                  repeated_target_groups=repeated,
                  limitations=["Not an expanded predefined sample or PIRS terminal comparison.",
                               "Repeated target groups are not the seven preregistered connected controls.",
                               "Four scenes do not support a population-level confidence claim.",
                               "All acceptable masks use superpoint IoU > .5, not goal mIoU."])
    output = root / "pipeline/reports/native_query_summary_20260916-1615.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
