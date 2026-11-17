"""Oracle-only target feature prototype screen on frozen M95 TRAIN capture."""
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
        raise ValueError("Frozen manifest/scene/annotation binding differs")
    features = artifact["features"]["final"].float()
    query = artifact["identity_query"]["query_states"].float()
    if query.shape != (128, 256) or features.shape[1] != 256:
        raise ValueError("Source shape differs")
    normalized = F.layer_norm(query, (256,), weight, bias)
    logits = normalized @ features.T
    max_error = float((logits - artifact["query_mask_logits"].float()).abs().max())
    if max_error > 1e-4:
        raise ValueError(f"Logits do not reconstruct: {max_error}")
    target = artifact["target_union"].bool()
    labels = artifact["physical_instance_labels"].long()
    semantic = torch.tensor(artifact["semantic_labels"], dtype=torch.long)
    if target.shape != labels.shape or target.shape != semantic.shape:
        raise ValueError("Target/physical support differs")
    target_category = Counter(semantic[target].tolist()).most_common(1)[0][0]
    non_target = ~target & (semantic == target_category) & (labels >= 0)
    candidates = sorted(set(labels[non_target].tolist()))
    masks = artifact["query_masks"].bool()
    union = (masks | target).sum(dim=1).clamp_min(1)
    ious = (masks & target).sum(dim=1).float() / union
    if max(abs(float(ious[i]) - float(row["ious"][i])) for i in range(128)) > 1e-6:
        raise ValueError("Mask/IoU binding differs")
    vectors = F.normalize(features, p=2, dim=1)
    queries = F.normalize(normalized, p=2, dim=1)

    def pick(support):
        proto = F.normalize(vectors[support].mean(dim=0), p=2, dim=0)
        return int(torch.argmax(queries @ proto))

    selected = pick(target)
    negatives = [pick((labels == label) & non_target) for label in candidates]
    deployed = int(row["selected_query"])
    return {
        "manifest_index": row["manifest_index"], "scene": row["scene"],
        "ann_id": row["ann_id"], "deployed_query": deployed,
        "deployed_iou": float(ious[deployed]),
        "target_oracle_query": selected,
        "target_oracle_iou": float(ious[selected]),
        "target_oracle_delta": float(ious[selected] - ious[deployed]),
        "same_category_instances": len(candidates),
        "negative_oracle_queries": negatives,
        "negative_oracle_ious": [float(ious[i]) for i in negatives],
        "logit_max_abs_error": max_error,
    }


def analyze(capture_path, artifact_root, checkpoint_path, population_path):
    import torch

    for path, expected in ((capture_path, CAPTURE_SHA),
                           (checkpoint_path, CHECKPOINT_SHA),
                           (population_path, POPULATION_SHA)):
        if sha(path) != expected:
            raise ValueError(f"Source SHA256 differs: {path}")
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
    pending, results = limited | controls, {}
    rows = {r["manifest_index"]: r for r in capture["rows"]}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Artifact hash differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            if index in pending:
                results[index] = evaluate(artifact, rows[index], weight, bias)
                pending.remove(index)
    if pending:
        raise ValueError(f"Missing {len(pending)} frozen artifacts")

    def group(indices):
        group_rows = [results[i] for i in sorted(indices)]
        with_competitor = [r for r in group_rows if r["same_category_instances"]]
        return {
            "expressions": len(group_rows), "scenes": len({r["scene"] for r in group_rows}),
            "with_competitor": len(with_competitor),
            "oracle_fixed": sum(r["deployed_iou"] <= .5 < r["target_oracle_iou"] for r in group_rows),
            "oracle_broken": sum(r["deployed_iou"] > .5 >= r["target_oracle_iou"] for r in group_rows),
            "mean_delta": sum(r["target_oracle_delta"] for r in group_rows) / len(group_rows),
            "negative_best_gt_target": sum(
                max(r["negative_oracle_ious"]) > r["target_oracle_iou"] for r in with_competitor),
            "rows": group_rows,
        }
    return {
        "contract": "m95_feature_prototype_oracle_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "checkpoint_sha256": CHECKPOINT_SHA,
        "limited": group(limited), "size_matched_controls": group(controls),
        "limits": "Ground-truth target-feature prototype is oracle-only, forbidden in deployment; this does not establish a prediction-blind mechanism, matched causal control or trained benefit.",
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
