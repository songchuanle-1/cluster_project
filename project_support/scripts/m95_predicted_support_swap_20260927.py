"""Prediction-blind fixed-query feature swaps on frozen M95 TRAIN inputs."""
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
        raise ValueError("Frozen identity differs")
    final = artifact["features"]["final"].float()
    fused = artifact["features"]["fused"].float()
    query = artifact["identity_query"]["query_states"].float()
    if final.shape != fused.shape or query.shape != (128, 256):
        raise ValueError("Frozen feature/query axes differ")
    normalized = F.layer_norm(query, (256,), weight, bias)
    logits = normalized @ final.T
    max_error = float((logits - artifact["query_mask_logits"].float()).abs().max())
    if max_error > 1e-4:
        raise ValueError(f"Frozen logits do not reconstruct: {max_error}")
    selected = int(row["selected_query"])
    support = logits[selected] > 0
    if not torch.equal(support, artifact["query_masks"][selected].bool()):
        raise ValueError("Deployed support differs")
    shifted = torch.roll(support, shifts=max(1, len(support) // 2), dims=0)
    target = artifact["target_union"].bool()
    if target.shape != support.shape:
        raise ValueError("Target axis differs")

    def outcome(features):
        mask = (normalized[selected] @ features.T) > 0
        return float((mask & target).sum() / (mask | target).sum().clamp_min(1))

    original = outcome(final)
    if abs(original - float(row["ious"][selected])) > 1e-6:
        raise ValueError("Deployed IoU differs")

    def intervene(mask):
        changed = final.clone()
        changed[mask] = fused[mask]
        return outcome(changed)

    predicted = intervene(support)
    negative = intervene(shifted)
    return {
        "manifest_index": row["manifest_index"], "scene": row["scene"],
        "ann_id": row["ann_id"], "selected_query": selected,
        "logit_max_abs_error": max_error, "original_iou": original,
        "predicted_iou": predicted, "shifted_iou": negative,
        "predicted_delta": predicted - original,
        "shifted_delta": negative - original,
        "support_superpoints": int(support.sum()),
        "shifted_superpoints": int(shifted.sum()),
        "support_target_overlap": int((support & target).sum()),
        "shifted_target_overlap": int((shifted & target).sum()),
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
    weight, bias = state[prefix + "weight"].float(), state[prefix + "bias"].float()
    rows = {r["manifest_index"]: r for r in capture["rows"]}
    pending, result = limited | controls, {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Frozen artifact SHA256 differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            if index in pending:
                result[index] = evaluate(artifact, rows[index], weight, bias)
                pending.remove(index)
    if pending:
        raise ValueError(f"Missing {len(pending)} cohort artifacts")

    def group(indices):
        selected = [result[i] for i in sorted(indices)]
        return {
            "expressions": len(selected), "scenes": len({r["scene"] for r in selected}),
            "empty_support": sum(not r["support_superpoints"] for r in selected),
            "predicted_improved": sum(r["predicted_delta"] > 0 for r in selected),
            "predicted_harmed": sum(r["predicted_delta"] < 0 for r in selected),
            "predicted_fixed": sum(r["original_iou"] <= .5 < r["predicted_iou"] for r in selected),
            "predicted_broken": sum(r["original_iou"] > .5 >= r["predicted_iou"] for r in selected),
            "shifted_improved": sum(r["shifted_delta"] > 0 for r in selected),
            "shifted_harmed": sum(r["shifted_delta"] < 0 for r in selected),
            "predicted_better_than_shifted": sum(
                r["predicted_delta"] > r["shifted_delta"] for r in selected),
            "rows": selected,
        }
    return {
        "contract": "m95_predicted_support_swap_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "checkpoint_sha256": CHECKPOINT_SHA,
        "limited": group(limited), "size_matched_controls": group(controls),
        "limits": "Frozen same-query intervention only, no new model/training; physical target labels used solely for evaluation.",
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
