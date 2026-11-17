"""Frozen M95 all-query support intervention, prediction-blind."""
import argparse
import json
from pathlib import Path

from m95_native_mask_population_20260927 import cohorts
from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)

POPULATION_SHA = "71159f4e74fcc19a72bdf13dd478d6ffe2a30b80823efeb41d6f59b3597800ea"


def evaluate(artifact, row, weight, bias):
    import torch
    import torch.nn.functional as F

    if (artifact["artifact_contract"] != "m95_manifest_native_query_artifact_v1"
            or artifact["manifest_sha256"] != MANIFEST_SHA
            or artifact["axis"]["scene"] != row["scene"]
            or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
        raise ValueError("Frozen binding differs")
    final, fused = artifact["features"]["final"].float(), artifact["features"]["fused"].float()
    query = artifact["identity_query"]["query_states"].float()
    if final.shape != fused.shape or query.shape != (128, 256):
        raise ValueError("Feature/query axes differ")
    normalized = F.layer_norm(query, (256,), weight, bias)
    original_logits = normalized @ final.T
    max_error = float((original_logits - artifact["query_mask_logits"].float()).abs().max())
    if max_error > 1e-4:
        raise ValueError(f"Saved logits differ: {max_error}")
    support = (original_logits > 0).any(dim=0)
    if not torch.equal(support, artifact["query_masks"].bool().any(dim=0)):
        raise ValueError("Union native mask differs")
    shifted = torch.roll(support, max(1, len(support) // 2), dims=0)
    selected = int(row["selected_query"])
    target = artifact["target_union"].bool()
    if target.shape != support.shape:
        raise ValueError("Target axis differs")

    def outcome(features):
        mask = normalized[selected] @ features.T > 0
        return float((mask & target).sum() / (mask | target).sum().clamp_min(1))

    original = outcome(final)
    if abs(original - float(row["ious"][selected])) > 1e-6:
        raise ValueError("Deployed IoU differs")

    def swapped(region):
        value = final.clone()
        value[region] = fused[region]
        return outcome(value)

    union, control = swapped(support), swapped(shifted)
    return {
        "manifest_index": row["manifest_index"], "scene": row["scene"],
        "ann_id": row["ann_id"], "selected_query": selected,
        "logit_max_abs_error": max_error, "original_iou": original,
        "union_iou": union, "shifted_iou": control,
        "union_delta": union - original, "shifted_delta": control - original,
        "union_superpoints": int(support.sum()), "total_superpoints": len(support),
        "union_target_overlap": int((support & target).sum()),
        "shifted_target_overlap": int((shifted & target).sum()),
    }


def analyze(capture_path, artifact_root, checkpoint_path, population_path):
    import torch

    for path, expected in ((capture_path, CAPTURE_SHA), (checkpoint_path, CHECKPOINT_SHA),
                           (population_path, POPULATION_SHA)):
        if sha(path) != expected:
            raise ValueError(f"Frozen hash differs: {path}")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256):
        raise ValueError("Frozen capture differs")
    limited, controls = cohorts(capture["rows"])
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)["model"]
    prefix = "dec.decoder_layers.5.out_norm."
    weight, bias = state[prefix + "weight"].float(), state[prefix + "bias"].float()
    rows = {r["manifest_index"]: r for r in capture["rows"]}
    pending, result = limited | controls, {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Artifact differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            if index in pending:
                result[index] = evaluate(artifact, rows[index], weight, bias)
                pending.remove(index)
    if pending:
        raise ValueError(f"Missing {len(pending)} cohort artifacts")

    def group(ids):
        group_rows = [result[i] for i in sorted(ids)]
        return {
            "expressions": len(group_rows), "scenes": len({r["scene"] for r in group_rows}),
            "mean_union_fraction": sum(
                r["union_superpoints"] / r["total_superpoints"] for r in group_rows
            ) / len(group_rows),
            "union_improved": sum(r["union_delta"] > 0 for r in group_rows),
            "union_harmed": sum(r["union_delta"] < 0 for r in group_rows),
            "union_fixed": sum(r["original_iou"] <= .5 < r["union_iou"] for r in group_rows),
            "union_broken": sum(r["original_iou"] > .5 >= r["union_iou"] for r in group_rows),
            "shifted_improved": sum(r["shifted_delta"] > 0 for r in group_rows),
            "shifted_harmed": sum(r["shifted_delta"] < 0 for r in group_rows),
            "rows": group_rows,
        }
    return {
        "contract": "m95_query_union_support_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "checkpoint_sha256": CHECKPOINT_SHA,
        "limited": group(limited), "size_matched_controls": group(controls),
        "limits": "All-query support is prediction-blind but may saturate; frozen M95 subgraph only, not an admitted mechanism.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "checkpoint", "population", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.checkpoint, args.population)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: {j: v for j, v in result[k].items() if j != "rows"}
                      for k in ("limited", "size_matched_controls")}))


if __name__ == "__main__":
    main()
