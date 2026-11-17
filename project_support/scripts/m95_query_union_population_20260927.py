"""Extend frozen M95 prediction-blind query union to all TRAIN expressions."""
import argparse
import json
from pathlib import Path

from m95_query_union_support_20260927 import evaluate
from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)


def analyze(capture_path, artifact_root, checkpoint_path):
    import torch

    if sha(capture_path) != CAPTURE_SHA or sha(checkpoint_path) != CHECKPOINT_SHA:
        raise ValueError("Frozen capture/checkpoint SHA256 differs")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256):
        raise ValueError("Frozen capture provenance differs")
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)["model"]
    prefix = "dec.decoder_layers.5.out_norm."
    weight, bias = state[prefix + "weight"].float(), state[prefix + "bias"].float()
    rows = {r["manifest_index"]: r for r in capture["rows"]}
    result = {}
    for entry in capture["feature_artifacts"]:
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Artifact SHA256 differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            if index in result:
                raise ValueError("Duplicate manifest index")
            result[index] = evaluate(artifact, rows[index], weight, bias)
            result[index]["limited"] = max(rows[index]["ious"]) <= .5
    if sorted(result) != list(range(256)):
        raise ValueError("Incomplete manifest")

    def group(limited):
        selected = [result[i] for i in sorted(result) if result[i]["limited"] == limited]
        return {
            "expressions": len(selected), "scenes": len({r["scene"] for r in selected}),
            "mean_union_delta": sum(r["union_delta"] for r in selected) / len(selected),
            "mean_shifted_delta": sum(r["shifted_delta"] for r in selected) / len(selected),
            "mean_union_fraction": sum(
                r["union_superpoints"] / r["total_superpoints"] for r in selected
            ) / len(selected),
            "union_improved": sum(r["union_delta"] > 0 for r in selected),
            "union_harmed": sum(r["union_delta"] < 0 for r in selected),
            "union_fixed": sum(r["original_iou"] <= .5 < r["union_iou"] for r in selected),
            "union_broken": sum(r["original_iou"] > .5 >= r["union_iou"] for r in selected),
            "shifted_improved": sum(r["shifted_delta"] > 0 for r in selected),
            "shifted_harmed": sum(r["shifted_delta"] < 0 for r in selected),
            "rows": selected,
        }

    return {
        "contract": "m95_query_union_population_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "checkpoint_sha256": CHECKPOINT_SHA,
        "limited": group(True), "covered": group(False),
        "limits": "Prediction-blind support from unchanged M95, but frozen same-query feature swap is not a trained mechanism or efficacy estimate.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "checkpoint", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(args.capture, args.artifact_root, args.checkpoint)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: {j: v for j, v in report[k].items() if j != "rows"}
                      for k in ("limited", "covered")}))


if __name__ == "__main__":
    main()
