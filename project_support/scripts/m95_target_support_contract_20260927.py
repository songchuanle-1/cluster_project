"""Audit native mask target against physical instance support on one axis."""
import argparse
import json
from pathlib import Path

from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)

RESIDUAL_SHA = "915e1d7e9385392a4f30da35a50b2698b54e005394caeb1d6d6a5ed2d3ca6bd5"


def evaluate(row, artifact):
    import numpy as np

    if (artifact["manifest_index"] != row["manifest_index"]
            or artifact["manifest_sha256"] != MANIFEST_SHA
            or artifact["axis"]["scene"] != row["scene"]
            or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
        raise ValueError("Artifact identity differs")
    query = row["selected_query"]
    if not 0 <= query < 128 or len(row["ious"]) != 128:
        raise ValueError("Native query axis differs")
    mask = artifact["query_masks"][query].bool().numpy()
    native = artifact["target_union"].bool().numpy()
    labels = artifact["physical_instance_labels"].numpy()
    if (len(mask) != len(native) or len(native) != len(labels)
            or list(map(int, labels)) != list(map(int, row["physical_instance_labels"]))):
        raise ValueError("Physical support axis differs")
    physical = np.isin(labels, row["target_instances"])
    def iou(target):
        return float(np.count_nonzero(mask & target) /
                     max(1, np.count_nonzero(mask | target)))
    native_iou = iou(native)
    if abs(native_iou - row["ious"][query]) > 1e-6:
        raise ValueError("Native selected IoU differs")
    return {
        "manifest_index": row["manifest_index"], "scene": row["scene"],
        "ann_id": row["ann_id"], "native_target_size": int(native.sum()),
        "physical_target_size": int(physical.sum()),
        "support_disagreement": int(np.count_nonzero(native != physical)),
        "native_selected_iou": native_iou,
        "physical_selected_iou": iou(physical),
        "selected_native_positive": bool(row["native_positive"][query]),
    }


def analyze(capture_path, residual_path, artifact_root):
    import torch

    if sha(capture_path) != CAPTURE_SHA or sha(residual_path) != RESIDUAL_SHA:
        raise ValueError("Frozen source differs")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    residual = json.loads(residual_path.read_text(encoding="utf-8"))
    rows = capture["rows"]
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(rows) != 256
            or sorted(r["manifest_index"] for r in rows) != list(range(256))
            or residual["capture_sha256"] != CAPTURE_SHA
            or residual["residual_expressions"] != 4):
        raise ValueError("Frozen capture population differs")
    failures = {r["manifest_index"] for r in residual["rows"]}
    if len(failures) != 4:
        raise ValueError("Frozen residual differs")
    successes = [
        r for r in rows if r["manifest_index"] not in failures
        and r["ious"][r["selected_query"]] > .5
        and r["native_positive"][r["selected_query"]]
        and r["seed_inside"][r["selected_query"]]
    ]
    # Fixed nearest-size controls, without looking at support disagreements.
    controls = {
        min(successes, key=lambda s: (
            abs(s["target_superpoints"] - r["target_superpoints"]),
            s["manifest_index"]))["manifest_index"]
        for r in rows if r["manifest_index"] in failures
    }
    wanted = failures | controls
    by_index = {r["manifest_index"]: r for r in rows}
    result = {}
    for entry in capture["feature_artifacts"]:
        if not wanted:
            break
        # Historical artifact metadata only records step; verify the file
        # before opening, and inspect its identity after deserialization.
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError("Artifact hash differs")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            if index in wanted:
                if artifact["artifact_contract"] != capture["artifact_contract"]:
                    raise ValueError("Artifact contract differs")
                result[index] = evaluate(by_index[index], artifact)
                wanted.remove(index)
    if wanted:
        raise ValueError("Missing artifact rows: " + str(sorted(wanted)))
    failure_rows = [result[i] for i in sorted(failures)]
    control_rows = [result[i] for i in sorted(controls)]
    return {
        "contract": "m95_target_support_contract_v1",
        "admission": False, "capture_sha256": CAPTURE_SHA,
        "residual_sha256": RESIDUAL_SHA,
        "failure_rows": failure_rows, "control_rows": control_rows,
        "failure_disagreement": sum(r["support_disagreement"] > 0 for r in failure_rows),
        "control_disagreement": sum(r["support_disagreement"] > 0 for r in control_rows),
        "limits": "Frozen TRAIN support audit only; no causal intervention or admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--residual", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(analyze(args.capture, args.residual, args.artifact_root),
                        indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            raise ValueError("Output exists")
        args.output.write_text(result, encoding="utf-8")
    print(result)


if __name__ == "__main__":
    main()
