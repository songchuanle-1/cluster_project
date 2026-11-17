"""Oracle-only, fixed-deployed-query feature replacement on frozen M95."""
import argparse
import json
from collections import Counter
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
        raise ValueError("Artifact/row identity differs")
    query = artifact["identity_query"]["query_states"].float()
    final = artifact["features"]["final"].float()
    fused = artifact["features"]["fused"].float()
    if query.shape != (128, 256) or final.shape != fused.shape:
        raise ValueError("Feature shape differs")
    normalized = F.layer_norm(query, (256,), weight, bias)
    saved = artifact["query_mask_logits"].float()
    logits = normalized @ final.T
    max_error = float((logits - saved).abs().max())
    if max_error > 1e-4:
        raise ValueError(f"Saved logit reconstruction differs: {max_error}")
    target = artifact["target_union"].bool()
    labels = artifact["physical_instance_labels"].long()
    semantic = torch.tensor(artifact["semantic_labels"], dtype=torch.long)
    if target.shape != labels.shape or target.shape != semantic.shape:
        raise ValueError("Support differs")
    category = Counter(semantic[target].tolist()).most_common(1)[0][0]
    negative = ~target & (semantic == category) & (labels >= 0)
    match = torch.nonzero(negative, as_tuple=False).flatten()[:int(target.sum())]
    selected = int(row["selected_query"])

    def outcome(features):
        mask = (normalized[selected] @ features.T) > 0
        iou = float((mask & target).sum() / (mask | target).sum().clamp_min(1))
        return {
            "iou": iou, "tp": int((mask & target).sum()),
            "fp": int((mask & ~target).sum()),
            "fn": int((~mask & target).sum()),
        }

    original = outcome(final)
    if abs(original["iou"] - float(row["ious"][selected])) > 1e-6:
        raise ValueError("Frozen deployed selection/IoU differs")
    target_features = final.clone()
    target_features[target] = fused[target]
    target_swap = outcome(target_features)
    negative_swap = None
    if match.numel():
        other_features = final.clone()
        other_features[match] = fused[match]
        negative_swap = outcome(other_features)
    return {
        "manifest_index": row["manifest_index"], "scene": row["scene"],
        "ann_id": row["ann_id"], "selected_query": selected,
        "target_superpoints": int(target.sum()),
        "negative_replaced": len(match), "logit_max_abs_error": max_error,
        "original": original, "target_swap": target_swap,
        "negative_swap": negative_swap,
        "target_delta": target_swap["iou"] - original["iou"],
        "negative_delta": (
            negative_swap["iou"] - original["iou"] if negative_swap else None),
    }


def analyze(capture_path, artifact_root, checkpoint_path, population_path):
    import torch

    for path, expected in ((capture_path, CAPTURE_SHA),
                           (checkpoint_path, CHECKPOINT_SHA),
                           (population_path, POPULATION_SHA)):
        if sha(path) != expected:
            raise ValueError(f"Frozen source SHA256 differs: {path}")
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
    weight = state[prefix + "weight"].float()
    bias = state[prefix + "bias"].float()
    rows = {r["manifest_index"]: r for r in capture["rows"]}
    pending, result = limited | controls, {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Artifact SHA256 differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            if index in pending:
                result[index] = evaluate(artifact, rows[index], weight, bias)
                pending.remove(index)
    if pending:
        raise ValueError(f"Missing {len(pending)} cohort artifacts")

    def group(indices):
        selected = [result[i] for i in sorted(indices)]
        negatives = [r for r in selected if r["negative_swap"]]
        return {
            "expressions": len(selected), "scenes": len({r["scene"] for r in selected}),
            "target_improved": sum(r["target_delta"] > 0 for r in selected),
            "target_harmed": sum(r["target_delta"] < 0 for r in selected),
            "target_fixed": sum(r["original"]["iou"] <= .5 < r["target_swap"]["iou"] for r in selected),
            "target_broken": sum(r["original"]["iou"] > .5 >= r["target_swap"]["iou"] for r in selected),
            "negative_available": len(negatives),
            "negative_improved": sum(r["negative_delta"] > 0 for r in negatives),
            "negative_harmed": sum(r["negative_delta"] < 0 for r in negatives),
            "target_better_than_negative": sum(r["target_delta"] > r["negative_delta"] for r in negatives),
            "rows": selected,
        }
    return {
        "contract": "m95_fixed_query_feature_intervention_v1",
        "admission": False, "capture_sha256": CAPTURE_SHA,
        "checkpoint_sha256": CHECKPOINT_SHA,
        "limited": group(limited), "size_matched_controls": group(controls),
        "limits": "Target-support oracle feature swap, labels unavailable at inference; no learned mechanism, new-model backward, or training efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "checkpoint", "population", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(args.capture, args.artifact_root, args.checkpoint, args.population)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: {j: v for j, v in report[k].items() if j != "rows"}
                      for k in ("limited", "size_matched_controls")}))


if __name__ == "__main__":
    main()
