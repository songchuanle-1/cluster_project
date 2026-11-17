"""Frozen M95 LayerNorm pullback for target/peer BCE, diagnosis only."""
import argparse
import json
from collections import Counter
from pathlib import Path

from m95_native_positive_union_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)

PEER_SHA = "d400c26f9037ed1107e32113e27fec1de6cafaf6bafb183ba807b9f0ad651eaa"


def analyze(capture_path, artifact_root, peer_path, checkpoint_path):
    import torch
    import torch.nn.functional as F

    for path, expected in ((capture_path, CAPTURE_SHA),
                           (peer_path, PEER_SHA),
                           (checkpoint_path, CHECKPOINT_SHA)):
        if sha(path) != expected:
            raise ValueError(f"Frozen input differs: {path}")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    peers = json.loads(peer_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256
            or peers["capture_sha256"] != CAPTURE_SHA
            or len(peers["rows"]) != 26):
        raise ValueError("Frozen source contract differs")
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)["model"]
    prefix = "dec.decoder_layers.5.out_norm."
    weight, bias = state[prefix + "weight"].float(), state[prefix + "bias"].float()
    source = {int(r["manifest_index"]): r for r in capture["rows"]}
    cohort = {int(r["manifest_index"]): r for r in peers["rows"]}
    results = {}
    for entry in capture["feature_artifacts"]:
        if len(results) == len(cohort):
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Artifact differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            if idx not in cohort:
                continue
            native, peer = source[idx], cohort[idx]
            if (idx in results or artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["manifest_sha256"] != MANIFEST_SHA
                    or artifact["axis"]["scene"] != native["scene"]
                    or peer["scene"] != native["scene"]):
                raise ValueError("Native identity differs")
            features = artifact["features"]["final"].float()
            query = artifact["identity_query"]["query_states"].float()
            masks = artifact["query_masks"].bool()
            target = artifact["target_union"].bool()
            physical = artifact["physical_instance_labels"].long()
            semantic = torch.as_tensor(artifact["semantic_labels"]).long()
            best = int(peer["best_positive_index"])
            positive = [i for i, yes in enumerate(native["native_positive"]) if yes]
            if best not in positive or best != max(
                    positive, key=lambda i: (float(native["ious"][i]), -i)):
                raise ValueError("Best positive differs")
            q = query[best].clone().requires_grad_(True)
            logits = F.layer_norm(q, (256,), weight, bias) @ features.T
            saved = artifact["query_mask_logits"].float()[best]
            error = float((logits.detach() - saved).abs().max())
            if (error > 1e-4 or not torch.equal(masks[best], saved > 0)
                    or not torch.isfinite(logits).all()):
                raise ValueError(f"Logit replay differs: {idx}")
            missed = target & ~masks[best]
            peer_axis = torch.zeros_like(target)
            for item in peer["peers"]:
                peer_axis |= physical == int(item["object_id"])
            if (not missed.any() or not peer_axis.any()
                    or int(peer_axis.sum()) != sum(p["total"] for p in peer["peers"])):
                raise ValueError("Support differs")
            category = Counter(semantic[target].tolist()).most_common(1)[0][0]
            if category < 0:
                raise ValueError("Invalid category")
            different = (~target & ~peer_axis & (physical >= 0)
                         & (semantic >= 0) & (semantic != category))
            negative_ids = torch.nonzero(different).flatten()[:int(peer_axis.sum())]

            def gradient(axis, label):
                loss = F.binary_cross_entropy_with_logits(
                    logits[axis], torch.full_like(logits[axis], label))
                return torch.autograd.grad(loss, q, retain_graph=True)[0].detach()

            target_grad = gradient(missed, 1.)
            peer_grad = gradient(peer_axis, 0.)
            control_grad = gradient(
                torch.zeros_like(target).scatter_(0, negative_ids, True), 0.
            ) if negative_ids.numel() else None

            def cosine(g):
                denom = float(target_grad.norm() * g.norm())
                return float(torch.dot(target_grad, g) / denom) if denom else None

            results[idx] = {
                "manifest_index": idx, "scene": native["scene"],
                "group": peer["group"], "best_positive": best,
                "reconstruction_error": error,
                "missed_target": int(missed.sum()),
                "peer_superpoints": int(peer_axis.sum()),
                "peer_covered_by_best": int((peer_axis & masks[best]).sum()),
                "target_gradient_norm": float(target_grad.norm()),
                "peer_gradient_norm": float(peer_grad.norm()),
                "gradient_cosine": cosine(peer_grad),
                "different_class_control_cosine": cosine(control_grad) if control_grad is not None else None,
                "control_superpoints": int(negative_ids.numel()),
            }
    if set(results) != set(cohort):
        raise ValueError("Incomplete frozen cohort")
    groups = {}
    for group in ("fragmented", "other_limited", "covered_controls", "remainder"):
        rows = [r for r in results.values() if r["group"] == group]
        groups[group] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "defined": sum(r["gradient_cosine"] is not None for r in rows),
            "conflict": sum(r["gradient_cosine"] is not None and r["gradient_cosine"] < 0 for r in rows),
            "compatible": sum(r["gradient_cosine"] is not None and r["gradient_cosine"] > 0 for r in rows),
        }
    return {
        "contract": "m95_peer_pullback_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "peer_sha256": PEER_SHA,
        "checkpoint_sha256": CHECKPOINT_SHA,
        "groups": groups, "rows": [results[i] for i in sorted(results)],
        "limits": "Final-mask BCE query-state pullback, not native full backward, Dice or new-model admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "peer", "checkpoint", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.peer, args.checkpoint)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["groups"]))


if __name__ == "__main__":
    main()
