"""Native per-positive gradient coherence on retrospectively missed target support."""
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
REFERENCE_SHA = "c88bdc19dc74255940c8da90ff3b6de9a343c7fcc4d81c48a1b6c16c2ef2e3ef"


def evaluate(row, artifact, weight, bias, reference):
    import torch
    import torch.nn.functional as F

    if (artifact["manifest_sha256"] != MANIFEST_SHA
            or artifact["manifest_index"] != row["manifest_index"]
            or artifact["axis"]["scene"] != row["scene"]
            or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
        raise ValueError("Artifact identity mismatch")
    q = artifact["identity_query"]["query_states"].detach().float()
    features = artifact["features"]["final"].detach().float().requires_grad_(True)
    logits = F.layer_norm(q, (256,), weight, bias) @ features.T
    error = float((logits.detach() - artifact["query_mask_logits"].float()).abs().max())
    if error > LOGIT_ATOL:
        raise ValueError("Native logits differ")
    target = artifact["target_union"].bool()
    positive = [i for i, yes in enumerate(row["native_positive"]) if yes]
    if (len(positive) != reference["matched_queries"]
            or any(bool(artifact["native_positive"][i]) != (i in positive)
                   for i in range(128))):
        raise ValueError("Matcher positives differ")
    best = max(positive, key=lambda i: (row["ious"][i], -i))
    missed = target & ~artifact["query_masks"][best].bool()
    gradients = []
    losses = []
    for i in positive:
        prob = logits[i].sigmoid()
        component = (F.binary_cross_entropy_with_logits(logits[i], target.float())
                     + 1 - (2 * (prob * target).sum() + 1)
                     / (prob.sum() + target.sum() + 1))
        gradients.append(torch.autograd.grad(component, features, retain_graph=True)[0].detach())
        losses.append(float(component.detach()))
    all_target_aggregate = torch.stack(gradients).mean(0)[target] / len(positive)
    if (abs(sum(losses) / len(positive) ** 2 - reference["loss"]) > 1e-4
            or abs(float(all_target_aggregate.norm())
                   - reference["target_feature_grad_norm"]) > 1e-4):
        raise ValueError("Native aggregate reconstruction differs")
    coherence = None
    if len(positive) >= 2 and missed.any():
        subset = torch.stack([g[missed] for g in gradients])
        individual_norm = subset.flatten(1).norm(dim=1).mean()
        if individual_norm > 0:
            coherence = float(subset.mean(0).norm() / individual_norm)
    return {
        "manifest_index": row["manifest_index"], "scene": row["scene"],
        "best_native_positive": best, "positive_queries": len(positive),
        "target_superpoints": int(target.sum()), "missed_superpoints": int(missed.sum()),
        "missed_coherence": coherence, "logit_error": error,
    }


def analyze(capture_path, artifact_root, checkpoint_path, loss_path,
            population_path, positive_path, fragment_path, reference_path):
    import torch

    for path, expected in (
        (capture_path, CAPTURE_SHA), (checkpoint_path, CHECKPOINT_SHA),
        (loss_path, LOSS_SHA), (population_path, POPULATION_SHA),
        (positive_path, POSITIVE_SHA), (fragment_path, FRAGMENT_SHA),
        (reference_path, REFERENCE_SHA),
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
            or len(capture["rows"]) != 256
            or fragment["capture_sha256"] != CAPTURE_SHA
            or reference["capture_sha256"] != CAPTURE_SHA):
        raise ValueError("Frozen provenance differs")
    limited, controls = cohorts(capture["rows"])
    fragmented = {r["manifest_index"] for r in fragment["groups"]["limited"]["rows"]
                  if r["extra_recall"] > 0}
    if len(fragmented) != 4:
        raise ValueError("Fragmented cohort differs")
    original = {}
    for key in ("limited", "size_matched_controls"):
        original.update({r["manifest_index"]: r for r in reference[key]["rows"]})
    if set(original) != limited | controls:
        raise ValueError("Reference cohort differs")
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)["model"]
    prefix = "dec.decoder_layers.5.out_norm."
    weight, bias = (state[prefix + tag].detach().float() for tag in ("weight", "bias"))
    norm_sha = hashlib.sha256(weight.numpy().tobytes() + bias.numpy().tobytes()).hexdigest()
    if norm_sha != reference["out_norm_state_sha256"]:
        raise ValueError("Normalization state differs")
    rows = {r["manifest_index"]: r for r in capture["rows"]}
    pending = set(original)
    result = {}
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
        raise ValueError("Missing frozen rows")
    groups = {}
    for name, ids in (
        ("fragmented", fragmented),
        ("other_limited", limited - fragmented),
        ("covered_controls", controls),
    ):
        subset = [result[i] for i in sorted(ids)]
        eligible = [r["missed_coherence"] for r in subset
                    if r["missed_coherence"] is not None]
        two = [r["missed_coherence"] for r in subset
               if r["positive_queries"] == 2 and r["missed_coherence"] is not None]
        groups[name] = {
            "expressions": len(subset), "scenes": len({r["scene"] for r in subset}),
            "missed_support_rows": sum(r["missed_superpoints"] > 0 for r in subset),
            "coherence_defined": len(eligible),
            "median_missed_coherence": statistics.median(eligible) if eligible else None,
            "two_positive": len(two),
            "median_two_positive_missed_coherence": statistics.median(two) if two else None,
            "rows": subset,
        }
    return {
        "contract": "m95_missed_support_gradient_coherence_v1",
        "admission": False, "capture_sha256": CAPTURE_SHA,
        "fragment_sha256": FRAGMENT_SHA, "reference_sha256": REFERENCE_SHA,
        "norm_sha256": norm_sha, "groups": groups,
        "limits": "Frozen TRAIN oracle-localized native mask-source replay, not deployable mechanism or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    for key in ("capture", "artifact-root", "checkpoint", "loss",
                "population", "positive", "fragment", "reference", "output"):
        parser.add_argument("--" + key, required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(args.capture, args.artifact_root, args.checkpoint,
                     args.loss, args.population, args.positive, args.fragment,
                     args.reference)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({k: {field: value for field, value in group.items()
                          if field != "rows"} for k, group in report["groups"].items()}))


if __name__ == "__main__":
    main()
