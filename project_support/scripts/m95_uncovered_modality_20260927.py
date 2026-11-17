"""Compare native missed-target modality features to same-scene unseen background."""
import argparse
import json
from pathlib import Path

from m95_native_positive_union_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, FRAGMENT_SHA, MANIFEST_SHA, POPULATION_SHA,
    PRODUCER_SHA, sha,
)


def analyze(capture_path, artifact_root, fragment_path, population_path):
    import torch
    import torch.nn.functional as F

    for path, expected in ((capture_path, CAPTURE_SHA), (fragment_path, FRAGMENT_SHA),
                           (population_path, POPULATION_SHA)):
        if sha(path) != expected:
            raise ValueError(f"Frozen source differs: {path}")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
    population = json.loads(population_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256
            or fragment["capture_sha256"] != CAPTURE_SHA
            or population["capture_sha256"] != CAPTURE_SHA):
        raise ValueError("Frozen provenance differs")
    limited = {r["manifest_index"] for r in population["limited_rows"]}
    controls = {r["manifest_index"] for r in population["control_rows"]}
    fragmented = {r["manifest_index"] for r in fragment["groups"]["limited"]["rows"]
                  if r["extra_recall"] > 0}
    if len(limited) != 16 or len(controls) != 16 or len(fragmented) != 4:
        raise ValueError("Frozen cohorts differ")
    source = {r["manifest_index"]: r for r in capture["rows"]}
    pending = limited | controls
    results = {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Frozen artifact differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            if idx not in pending:
                continue
            row = source[idx]
            if (artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["manifest_sha256"] != MANIFEST_SHA
                    or artifact["axis"]["scene"] != row["scene"]
                    or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
                raise ValueError(f"Native identity differs: {idx}")
            masks = artifact["query_masks"].bool()
            logits = artifact["query_mask_logits"]
            target = artifact["target_union"].bool()
            if (masks.shape != logits.shape or masks.shape != (128, target.numel())
                    or not torch.equal(masks, logits > 0)
                    or not bool(target.any())):
                raise ValueError(f"Native mask differs: {idx}")
            seen = masks.any(dim=0)
            covered_target = seen & target
            missing_target = ~seen & target
            missing_background = ~seen & ~target
            out = {
                "manifest_index": idx, "scene": row["scene"], "ann_id": row["ann_id"],
                "covered_target": int(covered_target.sum()),
                "uncovered_target": int(missing_target.sum()),
                "uncovered_background": int(missing_background.sum()),
            }
            if covered_target.any() and missing_target.any() and missing_background.any():
                out["status"] = "paired"
                out["stages"] = {}
                for stage in ("projected_3d", "projected_2d", "fused", "final"):
                    features = artifact["features"][stage].float()
                    if (features.shape[0] != target.numel()
                            or not bool(torch.isfinite(features).all())):
                        raise ValueError(f"Feature support differs: {idx}/{stage}")
                    vectors = F.normalize(features, dim=1)
                    prototype = F.normalize(vectors[covered_target].mean(0), dim=0)
                    scores = vectors @ prototype
                    target_mean = float(scores[missing_target].mean())
                    background_mean = float(scores[missing_background].mean())
                    out["stages"][stage] = {
                        "missed_target": target_mean,
                        "unseen_background": background_mean,
                        "margin": target_mean - background_mean,
                    }
            else:
                out["status"] = "insufficient_parts"
            results[idx] = out
            pending.remove(idx)
    if pending:
        raise ValueError(f"Missing rows: {sorted(pending)}")
    groups = {}
    for name, ids in (("fragmented", fragmented),
                      ("other_limited", limited - fragmented),
                      ("covered_controls", controls)):
        rows = [results[i] for i in sorted(ids)]
        paired = [r for r in rows if r["status"] == "paired"]
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "paired_expressions": len(paired),
            "mean_margins": {
                stage: sum(r["stages"][stage]["margin"] for r in paired) / len(paired)
                if paired else None
                for stage in ("projected_3d", "projected_2d", "fused", "final")
            },
            "final_below_fused": sum(
                r["stages"]["final"]["margin"] < r["stages"]["fused"]["margin"]
                for r in paired),
            "rows": rows,
        }
    return {
        "contract": "m95_uncovered_modality_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "fragment_sha256": FRAGMENT_SHA,
        "population_sha256": POPULATION_SHA, "groups": groups,
        "limits": "TRAIN oracle-localized observational feature contrast; no causal intervention, inference signal or admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "fragment", "population", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.fragment, args.population)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({key: {k: v for k, v in value.items() if k != "rows"}
                      for key, value in result["groups"].items()}))


if __name__ == "__main__":
    main()
