"""Population extension of a frozen native matched-mask loss audit."""
import argparse
import json
from pathlib import Path

from m95_native_mask_backward_20260927 import (
    LOSS_SHA, evaluate,
)
from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)


def cohorts(rows):
    limited = [r for r in rows if max(r["ious"]) <= .5]
    covered = [r for r in rows if max(r["ious"]) > .5]
    if len(limited) != 16 or len(covered) != 240:
        raise ValueError("Frozen no-adequate-mask population differs")
    controls = set()
    for row in limited:
        eligible = [r for r in covered if r["manifest_index"] not in controls]
        match = min(eligible, key=lambda r: (
            abs(r["target_superpoints"] - row["target_superpoints"]),
            r["manifest_index"]))
        controls.add(match["manifest_index"])
    return {r["manifest_index"] for r in limited}, controls


def analyze(capture_path, artifact_root, loss_path):
    import importlib.util
    import torch

    if sha(capture_path) != CAPTURE_SHA or sha(loss_path) != LOSS_SHA:
        raise ValueError("Frozen source differs")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    rows = capture["rows"]
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(rows) != 256
            or sorted(r["manifest_index"] for r in rows) != list(range(256))):
        raise ValueError("Frozen population differs")
    limited, controls = cohorts(rows)
    spec = importlib.util.spec_from_file_location("m95_native_loss_full", loss_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    criterion = module.Criterion.__new__(module.Criterion)
    pending, result = limited | controls, {}
    by_index = {r["manifest_index"]: r for r in rows}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError("Artifact hash differs")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            if idx not in pending:
                continue
            if artifact["artifact_contract"] != capture["artifact_contract"]:
                raise ValueError("Artifact contract differs")
            row = by_index[idx]
            selected = row["selected_query"]
            if not row["native_positive"][selected]:
                result[idx] = {
                    "manifest_index": idx, "scene": row["scene"],
                    "ann_id": row["ann_id"], "selected_positive": False,
                    "selected_iou": row["ious"][selected],
                    "max_iou": max(row["ious"]),
                }
            else:
                result[idx] = {
                    **evaluate(row, artifact, criterion),
                    "selected_positive": True, "max_iou": max(row["ious"]),
                }
            pending.remove(idx)
    if pending:
        raise ValueError("Missing cohort artifacts")
    limited_rows = [result[i] for i in sorted(limited)]
    control_rows = [result[i] for i in sorted(controls)]

    def summary(group):
        eligible = [r for r in group if r["selected_positive"]]
        return {
            "expressions": len(group), "scenes": len({r["scene"] for r in group}),
            "selected_positive": len(eligible),
            "corrective": sum(
                r["all_finite"] and r["fn"] == r["fn_correct"]
                and r["fp"] == r["fp_correct"] for r in eligible),
            "zero_score_loss": sum(r["score_loss"] == 0 for r in eligible),
        }
    return {
        "contract": "m95_native_mask_population_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "loss_sha256": LOSS_SHA,
        "limited": summary(limited_rows), "controls": summary(control_rows),
        "limited_rows": limited_rows, "control_rows": control_rows,
        "limits": "TRAIN final-loss subgraph; no full-model candidate backward or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--loss", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.loss)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"limited": result["limited"], "controls": result["controls"]}))


if __name__ == "__main__":
    main()
