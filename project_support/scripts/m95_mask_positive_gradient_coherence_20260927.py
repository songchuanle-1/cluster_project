"""Native frozen M95 positive-query feature-gradient coherence audit."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path

from m95_mask_feature_path_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, LOGIT_ATOL, LOSS_SHA, MANIFEST_SHA,
    POPULATION_SHA, POSITIVE_SHA, PRODUCER_SHA, sha,
)
from m95_native_mask_population_20260927 import cohorts

FRAGMENT_SHA = "dc9ce208a764bc2406f6093a089cdc65263f69b4ce23706d615a952194b2ea53"
GRADIENT_SHA = "c88bdc19dc74255940c8da90ff3b6de9a343c7fcc4d81c48a1b6c16c2ef2e3ef"


def evaluate(row, artifact, weight, bias, reference):
    import torch
    import torch.nn.functional as F

    if (artifact["manifest_sha256"] != MANIFEST_SHA
            or artifact["manifest_index"] != row["manifest_index"]
            or artifact["axis"]["scene"] != row["scene"]
            or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
        raise ValueError("Axis identity mismatch")
    q = artifact["identity_query"]["query_states"].detach().float()
    f = artifact["features"]["final"].detach().float().requires_grad_(True)
    if q.shape != (128, 256) or f.ndim != 2 or f.shape[1] != 256:
        raise ValueError("Feature dimensions differ")
    logits = F.layer_norm(q, (256,), weight, bias) @ f.T
    error = float((logits.detach() - artifact["query_mask_logits"].float()).abs().max())
    if error > LOGIT_ATOL:
        raise ValueError(f"Logit reconstruction error: {error}")
    target = artifact["target_union"].bool()
    if target.shape != (len(f),) or not target.any():
        raise ValueError("Target dimensions differ")
    positive = [i for i, yes in enumerate(row["native_positive"]) if yes]
    if (len(positive) != reference["matched_queries"]
            or any(bool(artifact["native_positive"][i]) != (i in positive)
                   for i in range(128))):
        raise ValueError("Native matching differs")
    individual = []
    for i in positive:
        component = (F.binary_cross_entropy_with_logits(logits[i], target.float())
                     + 1 - (2 * (logits[i].sigmoid() * target).sum() + 1)
                     / (logits[i].sigmoid().sum() + target.sum() + 1))
        grad = torch.autograd.grad(component, f, retain_graph=True)[0][target]
        individual.append((float(component.detach()), grad.detach()))
    if not individual:
        raise ValueError("Missing positive")
    # Native loss_masks first averages BCE/Dice over positives, then divides
    # by num_boxes, which the reference replay sets to len(positive).
    unscaled_mean_grad = torch.stack([r[1] for r in individual]).mean(0)
    mean_grad = unscaled_mean_grad / len(individual)
    mean_loss = sum(r[0] for r in individual) / len(individual) ** 2
    mean_norm = sum(float(r[1].norm()) for r in individual) / len(individual)
    if (abs(mean_loss - reference["loss"]) > 1e-4
            or abs(float(mean_grad.norm()) - reference["target_feature_grad_norm"]) > 1e-4):
        raise ValueError(
            f"Aggregate native loss/feature gradient mismatch at {row['manifest_index']}: "
            f"loss={mean_loss}/{reference['loss']}, "
            f"feature_grad={float(mean_grad.norm())}/{reference['target_feature_grad_norm']}")
    ratio = (float(unscaled_mean_grad.norm()) / mean_norm
             if len(individual) >= 2 and mean_norm > 0 else None)
    return {"manifest_index": row["manifest_index"], "scene": row["scene"],
            "positives": len(individual), "coherence": ratio,
            "mean_individual_norm": mean_norm, "mean_grad_norm": float(mean_grad.norm()),
            "mean_loss": mean_loss, "logit_error": error}


def analyze(capture_path, artifact_root, checkpoint_path, loss_path,
            population_path, positive_path, fragment_path, reference_path):
    import torch

    for path, expected in (
        (capture_path, CAPTURE_SHA), (checkpoint_path, CHECKPOINT_SHA),
        (loss_path, LOSS_SHA), (population_path, POPULATION_SHA),
        (positive_path, POSITIVE_SHA), (fragment_path, FRAGMENT_SHA),
        (reference_path, GRADIENT_SHA),
    ):
        if sha(path) != expected:
            raise ValueError(f"Frozen source differs: {path}")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or fragment["capture_sha256"] != CAPTURE_SHA
            or reference["capture_sha256"] != CAPTURE_SHA
            or len(capture["rows"]) != 256):
        raise ValueError("Provenance differs")
    limited, controls = cohorts(capture["rows"])
    fragmented = {r["manifest_index"] for r in fragment["groups"]["limited"]["rows"]
                  if r["extra_recall"] > 0}
    if len(fragmented) != 4:
        raise ValueError("Fragmentation group differs")
    original = {}
    for key in ("limited", "size_matched_controls"):
        original.update({r["manifest_index"]: r for r in reference[key]["rows"]})
    if set(original) != limited | controls:
        raise ValueError("Reference cohort differs")
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)["model"]
    prefix = "dec.decoder_layers.5.out_norm."
    weight = state[prefix + "weight"].detach().float()
    bias = state[prefix + "bias"].detach().float()
    norm_sha = hashlib.sha256(weight.numpy().tobytes() + bias.numpy().tobytes()).hexdigest()
    if norm_sha != reference["out_norm_state_sha256"]:
        raise ValueError("Output normalization differs")
    pending = set(original)
    result = {}
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
                result[index] = evaluate(rows[index], artifact, weight, bias, original[index])
                pending.remove(index)
    if pending:
        raise ValueError(f"Missing {len(pending)} rows")
    groups = {}
    for name, ids in (
        ("fragmented", fragmented),
        ("other_limited", limited - fragmented),
        ("covered_controls", controls),
    ):
        subset = [result[i] for i in sorted(ids)]
        eligible = [r["coherence"] for r in subset if r["coherence"] is not None]
        two = [r["coherence"] for r in subset if r["positives"] == 2]
        groups[name] = {
            "expressions": len(subset), "scenes": len({r["scene"] for r in subset}),
            "coherence_defined": len(eligible),
            "median_coherence": statistics.median(eligible) if eligible else None,
            "two_positive": len(two),
            "median_two_positive_coherence": statistics.median(two) if two else None,
            "rows": subset,
        }
    return {
        "contract": "m95_mask_positive_gradient_coherence_v1",
        "admission": False, "capture_sha256": CAPTURE_SHA,
        "fragment_sha256": FRAGMENT_SHA, "reference_sha256": GRADIENT_SHA,
        "norm_sha256": norm_sha, "groups": groups,
        "limits": "Frozen TRAIN native mask-source replay, not full-model candidate backward, causal intervention, or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "checkpoint", "loss",
                 "population", "positive", "fragment", "reference", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(args.capture, args.artifact_root, args.checkpoint,
                     args.loss, args.population, args.positive, args.fragment,
                     args.reference)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({k: {field: v for field, v in group.items() if field != "rows"}
                      for k, group in report["groups"].items()}))


if __name__ == "__main__":
    main()
