"""Full frozen TRAIN population extension of post-hoc feature contrast."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from m95_feature_separability_20260927 import evaluate
from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)


def analyze(capture_path, artifact_root):
    import torch

    if sha(capture_path) != CAPTURE_SHA:
        raise ValueError("Frozen capture SHA256 differs")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256):
        raise ValueError("Frozen provenance differs")
    rows = {r["manifest_index"]: r for r in capture["rows"]}
    result = {}
    for entry in capture["feature_artifacts"]:
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Frozen artifact SHA256 differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            if index in result:
                raise ValueError("Duplicate manifest index")
            result[index] = evaluate(artifact, rows[index])
            result[index]["limited"] = max(rows[index]["ious"]) <= .5
    if sorted(result) != list(range(256)):
        raise ValueError("Incomplete full manifest")

    def group(limited):
        subset = [result[i] for i in sorted(result) if result[i]["limited"] == limited]
        paired = [r for r in subset if r["status"] == "paired"]
        def mean(key):
            return sum(r[key] for r in paired) / len(paired) if paired else None
        return {
            "expressions": len(subset), "scenes": len({r["scene"] for r in subset}),
            "paired": len(paired), "paired_scenes": len({r["scene"] for r in paired}),
            "missing_competitor": len(subset) - len(paired),
            "mean_fused_margin": mean("fused_margin"),
            "mean_final_margin": mean("final_margin"),
            "final_le_fused": sum(r["final_margin"] <= r["fused_margin"] for r in paired),
            "rows": subset,
        }
    scenes = defaultdict(lambda: [[], []])
    for item in result.values():
        if item["status"] == "paired":
            scenes[item["scene"]][int(item["limited"])].append(
                item["final_margin"] - item["fused_margin"])
    paired_scenes = [
        {"scene": name, "limited_final_minus_fused": sum(groups[1]) / len(groups[1]),
         "covered_final_minus_fused": sum(groups[0]) / len(groups[0])}
        for name, groups in sorted(scenes.items()) if groups[0] and groups[1]
    ]
    return {
        "contract": "m95_full_feature_separability_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "limited": group(True), "covered": group(False),
        "within_scene_paired": len(paired_scenes), "within_scene": paired_scenes,
        "limits": "Post-hoc physical target oracle on TRAIN; observational, not prediction-blind or an admissible candidate.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(args.capture, args.artifact_root)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: {j: v for j, v in report[k].items() if j != "rows"}
                      for k in ("limited", "covered")}))
    print(json.dumps({"within_scene_paired": report["within_scene_paired"]}))


if __name__ == "__main__":
    main()
