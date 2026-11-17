"""Validate and summarize same-forward coverage captures without model execution."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import statistics


def category(row):
    final = row["layers"][-1]
    if final["selected"] > 0.5:
        return "success"
    return "recoverable" if final["best"] > 0.5 else "mask_limited"


def analyze(report):
    rows = report["rows"]
    if not rows:
        raise ValueError("Empty capture")
    identities = set()
    scene_rows = defaultdict(list)
    depths = {len(row["layers"]) for row in rows}
    if len(depths) != 1 or 0 in depths:
        raise ValueError("Inconsistent decoder depth")
    for row in rows:
        identity = (row["scene"], tuple(row["object_ids"]), row["ann_id"])
        if identity in identities:
            raise ValueError("Duplicate expression identity")
        identities.add(identity)
        scene_rows[row["scene"]].append(row)
        if row["target_sp"] <= 0:
            raise ValueError("Empty target requires a separate diagnostic")
        if not 0 <= row["sampled_target"] <= row["fps_target"]:
            raise ValueError("Invalid subset counts")
        for layer in row["layers"]:
            if not 0 <= layer["selected"] <= layer["best"] <= 1:
                raise ValueError("Invalid IoU ordering")
            if (layer["success_queries"] > 0) != (layer["best"] > 0.5):
                raise ValueError("Oracle/query count mismatch")
    counts = Counter(category(row) for row in rows)
    summary = {
        "expressions": len(rows), "scenes": len(scene_rows),
        "no_fps_target": sum(row["fps_target"] == 0 for row in rows),
        "dropped_target": sum(row["fps_target"] > 0 and row["sampled_target"] == 0
                              for row in rows),
        **{key: counts[key] for key in ("success", "recoverable", "mask_limited")},
    }
    if summary != report["summary"]:
        raise ValueError("Reported summary does not match capture")
    strata = {}
    for label, subset in (
        ("no_fps_target", [r for r in rows if r["fps_target"] == 0]),
        ("has_fps_target", [r for r in rows if r["fps_target"] > 0]),
        ("instance_sp_disagreement", [r for r in rows
          if r["fps_target"] != r["fps_instance_target"]
          or r["sampled_target"] != r["sampled_instance_target"]]),
    ):
        strata[label] = {"n": len(subset), "outcomes": dict(Counter(map(category, subset)))}
    per_scene = []
    for scene, subset in sorted(scene_rows.items()):
        c = Counter(map(category, subset))
        per_scene.append({
            "scene": scene, "n": len(subset), "outcomes": dict(c),
            "recoverable_rate": c["recoverable"] / len(subset),
            "oracle_gap": statistics.mean(r["layers"][-1]["best"]
                                          - r["layers"][-1]["selected"] for r in subset),
        })
    rng = random.Random(1999)
    boot = sorted(statistics.mean(rng.choice(per_scene)["recoverable_rate"]
                                 for _ in per_scene) for _ in range(10000))
    layer_summary = []
    for layer_index in range(next(iter(depths))):
        layer_summary.append({
            "layer": layer_index,
            "selected_success": sum(r["layers"][layer_index]["selected"] > 0.5 for r in rows),
            "oracle_success": sum(r["layers"][layer_index]["best"] > 0.5 for r in rows),
            "mean_selected_sp_iou": statistics.mean(r["layers"][layer_index]["selected"] for r in rows),
        })
    transitions = Counter()
    for row in rows:
        first, final = row["layers"][0], row["layers"][-1]
        transitions[f'{first["selected"] > .5}->{final["selected"] > .5}'] += 1
    return {
        "summary": summary,
        "strata": strata,
        "per_scene": per_scene,
        "layers": layer_summary,
        "first_final_selected_transitions": dict(transitions),
        "scene_balanced_recoverable_rate": statistics.mean(s["recoverable_rate"] for s in per_scene),
        "scene_bootstrap_percentile_95": [boot[249], boot[9749]],
        "missing_rows": 0,
        "batch_ids": sorted({r["batch"] for r in rows}),
        "sample_manifest": [{"scene": r["scene"], "object_ids": r["object_ids"],
                             "ann_id": r["ann_id"], "outcome": category(r)} for r in rows],
        "limitations": [
            "Fixed augmented TRAIN sample; no population generalization or causal claim.",
            "SP IoU threshold strictly >0.5; not point mIoU or validation metric.",
            "Bootstrap is descriptive post-capture, scene-balanced, 10000 draws, seed1999.",
            "No missing rows within supplied capture; external dataset completeness not established.",
            "Best-query oracle is not a deployable result; no reranker admission.",
            "No same-class, relation or language-token evidence in this capture.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = analyze(json.loads(args.capture.read_text(encoding="utf-8")))
    result["evidence"] = [
        {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in (args.capture, Path(__file__))
    ]
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "summary", "strata", "layers", "first_final_selected_transitions",
        "scene_balanced_recoverable_rate", "scene_bootstrap_percentile_95")}, indent=2))
