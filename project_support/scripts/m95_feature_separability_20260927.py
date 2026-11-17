"""Frozen target/same-category feature separation, post hoc only."""
import argparse
import json
from collections import Counter
from pathlib import Path

from m95_native_mask_population_20260927 import cohorts
from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)

POPULATION_SHA = "71159f4e74fcc19a72bdf13dd478d6ffe2a30b80823efeb41d6f59b3597800ea"


def contrast(artifact, name, target, competitor):
    import torch
    import torch.nn.functional as F

    features = artifact["features"][name].float()
    if features.shape[0] != len(target) or not torch.isfinite(features).all():
        raise ValueError("Feature support/finite contract differs")
    vectors = F.normalize(features, p=2, dim=1)
    prototype = F.normalize(vectors[target].mean(dim=0), p=2, dim=0)
    scores = vectors @ prototype
    return float(scores[target].mean() - scores[competitor].mean())


def evaluate(artifact, row):
    import torch

    if (artifact["artifact_contract"] != "m95_manifest_native_query_artifact_v1"
            or artifact["manifest_sha256"] != MANIFEST_SHA
            or artifact["axis"]["scene"] != row["scene"]
            or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
        raise ValueError("Manifest/axis differs")
    labels = artifact["physical_instance_labels"].long()
    semantic = torch.tensor(artifact["semantic_labels"], dtype=torch.long)
    target = artifact["target_union"].bool()
    if labels.shape != semantic.shape or target.shape != labels.shape or not target.any():
        raise ValueError("Physical support differs")
    category = Counter(semantic[target].tolist()).most_common(1)[0][0]
    matched_target = target & (semantic == category)
    other = ~target & (semantic == category) & (labels >= 0)
    if not matched_target.any() or not other.any():
        return {
            "manifest_index": row["manifest_index"], "scene": row["scene"],
            "ann_id": row["ann_id"], "status": "no_same_category_competitor",
            "category": category,
        }
    return {
        "manifest_index": row["manifest_index"], "scene": row["scene"],
        "ann_id": row["ann_id"], "status": "paired",
        "category": category, "target_superpoints": int(matched_target.sum()),
        "competing_superpoints": int(other.sum()),
        "competing_instances": len(set(labels[other].tolist())),
        "fused_margin": contrast(artifact, "fused", matched_target, other),
        "final_margin": contrast(artifact, "final", matched_target, other),
    }


def analyze(capture_path, artifact_root, population_path):
    import torch

    if sha(capture_path) != CAPTURE_SHA or sha(population_path) != POPULATION_SHA:
        raise ValueError("Frozen input hashes differ")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or len(capture["rows"]) != 256
            or capture["capture_mode"] != "full_train_scan"):
        raise ValueError("Frozen capture contract differs")
    limited, controls = cohorts(capture["rows"])
    pending = limited | controls
    rows = {r["manifest_index"]: r for r in capture["rows"]}
    results = {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Artifact hash differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            if index in pending:
                results[index] = evaluate(artifact, rows[index])
                pending.remove(index)
    if pending:
        raise ValueError(f"Missing artifacts: {len(pending)}")

    def group(ids):
        selected = [results[i] for i in sorted(ids)]
        paired = [r for r in selected if r["status"] == "paired"]
        return {
            "expressions": len(selected),
            "scenes": len({r["scene"] for r in selected}),
            "paired": len(paired),
            "paired_scenes": len({r["scene"] for r in paired}),
            "missing_competitor": len(selected) - len(paired),
            "fused_positive": sum(r["fused_margin"] > 0 for r in paired),
            "final_positive": sum(r["final_margin"] > 0 for r in paired),
            "final_le_fused": sum(r["final_margin"] <= r["fused_margin"] for r in paired),
            "rows": selected,
        }

    return {
        "contract": "m95_feature_separability_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "population_sha256": POPULATION_SHA,
        "limited": group(limited), "size_matched_controls": group(controls),
        "limits": "Physical-instance labels used post hoc only. Prototype includes target superpoints and is an oracle readout, not an inference-time mechanism or causal intervention.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "population", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(args.capture, args.artifact_root, args.population)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: {j: v for j, v in report[k].items() if j != "rows"}
                      for k in ("limited", "size_matched_controls")}))


if __name__ == "__main__":
    main()
