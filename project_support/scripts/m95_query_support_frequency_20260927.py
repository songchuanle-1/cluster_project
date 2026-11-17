"""Frozen M95 TRAIN query-mask incidence audit, no model or prediction change."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, MANIFEST_SHA, PRODUCER_SHA, CHECKPOINT_SHA, sha,
)


def evaluate(artifact, row):
    import torch

    if (artifact["artifact_contract"] != "m95_manifest_native_query_artifact_v1"
            or artifact["manifest_sha256"] != MANIFEST_SHA
            or artifact["axis"]["scene"] != row["scene"]
            or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
        raise ValueError("Artifact identity differs")
    masks = artifact["query_masks"].bool()
    target = artifact["target_union"].bool()
    physical = artifact["physical_instance_labels"].long()
    semantic = torch.tensor(artifact["semantic_labels"], dtype=torch.long)
    if (masks.ndim != 2 or masks.shape[0] != 128
            or masks.shape[1] != len(target)
            or len(target) != len(physical) or len(target) != len(semantic)
            or not target.any()):
        raise ValueError("Native axes differ")
    category = Counter(semantic[target].tolist()).most_common(1)[0][0]
    competitor = ~target & (semantic == category) & (physical >= 0)
    limited = max(row["ious"]) <= .5
    result = {
        "manifest_index": row["manifest_index"], "scene": row["scene"],
        "ann_id": row["ann_id"], "limited": limited,
        "target_superpoints": int(target.sum()),
        "competitor_superpoints": int(competitor.sum()),
    }
    if competitor.any():
        frequency = masks.float().mean(dim=0)
        result.update({
            "target_frequency": float(frequency[target].mean()),
            "competitor_frequency": float(frequency[competitor].mean()),
            "target_minus_competitor": float(
                frequency[target].mean() - frequency[competitor].mean()),
        })
    return result


def analyze(capture_path, artifact_root):
    import torch

    if sha(capture_path) != CAPTURE_SHA:
        raise ValueError("Frozen capture differs")
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
            raise ValueError(f"Artifact differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            if index in result:
                raise ValueError("Duplicate manifest index")
            result[index] = evaluate(artifact, rows[index])
    if sorted(result) != list(range(256)):
        raise ValueError("Incomplete population")
    groups = {}
    scenes = defaultdict(lambda: [[], []])
    for limited in (True, False):
        subset = [result[i] for i in sorted(result) if result[i]["limited"] == limited]
        eligible = [r for r in subset if "target_minus_competitor" in r]
        for r in eligible:
            scenes[r["scene"]][int(limited)].append(r["target_minus_competitor"])
        groups["limited" if limited else "covered"] = {
            "expressions": len(subset),
            "scenes": len({r["scene"] for r in subset}),
            "eligible": len(eligible),
            "eligible_scenes": len({r["scene"] for r in eligible}),
            "target_lower": sum(r["target_minus_competitor"] < 0 for r in eligible),
            "mean_contrast": (sum(r["target_minus_competitor"] for r in eligible)
                              / len(eligible) if eligible else None),
            "rows": subset,
        }
    paired = [
        {"scene": scene,
         "limited_minus_covered": (sum(values[1]) / len(values[1])
                                   - sum(values[0]) / len(values[0]))}
        for scene, values in sorted(scenes.items()) if values[0] and values[1]
    ]
    return {
        "contract": "m95_query_support_frequency_v1",
        "capture_sha256": CAPTURE_SHA,
        "admission": False,
        "groups": groups,
        "same_scene_pairs": paired,
        "limits": "Frozen TRAIN retrospective GT readout; frequency alone is a prior-art ranking/duplicate signal, not a new trainable method.",
    }


def main():
    p = argparse.ArgumentParser()
    for key in ("capture", "artifact-root", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(args.capture, args.artifact_root)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "groups": {k: {n: v for n, v in g.items() if n != "rows"}
                   for k, g in report["groups"].items()},
        "same_scene_pairs": report["same_scene_pairs"],
    }))


if __name__ == "__main__":
    main()
