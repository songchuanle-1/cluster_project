"""Frozen M95 BCE/Dice query gradient direction, diagnostic only."""
import argparse
import json
from pathlib import Path

from m95_native_positive_union_20260927 import sha
from m95_peer_pullback_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PEER_SHA, PRODUCER_SHA,
)


def analyze(capture_path, artifact_root, peer_path, checkpoint_path):
    import torch
    import torch.nn.functional as F

    for path, expected in ((capture_path, CAPTURE_SHA), (peer_path, PEER_SHA),
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
            best = int(peer["best_positive_index"])
            positive = [i for i, yes in enumerate(native["native_positive"]) if yes]
            if best not in positive or best != max(
                    positive, key=lambda i: (float(native["ious"][i]), -i)):
                raise ValueError("Positive identity differs")
            features = artifact["features"]["final"].float()
            query = artifact["identity_query"]["query_states"].float()[best]
            target = artifact["target_union"].bool()
            masks = artifact["query_masks"].bool()[best]
            physical = artifact["physical_instance_labels"].long()
            q = query.clone().requires_grad_(True)
            logits = F.layer_norm(q, (256,), weight, bias) @ features.T
            error = float((logits.detach() - artifact["query_mask_logits"].float()[best]).abs().max())
            if error > 1e-4 or not torch.equal(masks, logits.detach() > 0):
                raise ValueError(f"Logit replay differs: {idx}")
            missed = target & ~masks
            peer_axis = torch.zeros_like(target)
            for item in peer["peers"]:
                peer_axis |= physical == int(item["object_id"])
            if not missed.any() or not peer_axis.any():
                raise ValueError("Support differs")

            def grad(loss):
                return torch.autograd.grad(loss, q, retain_graph=True)[0].detach()

            target_grad = grad(F.binary_cross_entropy_with_logits(
                logits[missed], torch.ones_like(logits[missed])))
            peer_grad = grad(F.binary_cross_entropy_with_logits(
                logits[peer_axis], torch.zeros_like(logits[peer_axis])))
            bce = F.binary_cross_entropy_with_logits(logits, target.float())
            probs = logits.sigmoid()
            dice = 1 - (2 * (probs * target).sum() + 1) / (
                probs.sum() + target.sum() + 1)
            bce_grad, dice_grad = grad(bce), grad(dice)
            total_grad = bce_grad + dice_grad

            def cos(a, b):
                denom = float(a.norm() * b.norm())
                return float(torch.dot(a, b) / denom) if denom else None

            results[idx] = {
                "manifest_index": idx, "scene": native["scene"], "group": peer["group"],
                "reconstruction_error": error,
                "missed_target": int(missed.sum()),
                "peer_superpoints": int(peer_axis.sum()),
                "bce": float(bce), "dice": float(dice),
                "bce_dice_cosine": cos(bce_grad, dice_grad),
                "full_target_cosine": cos(total_grad, target_grad),
                "full_peer_cosine": cos(total_grad, peer_grad),
                "bce_target_cosine": cos(bce_grad, target_grad),
                "bce_peer_cosine": cos(bce_grad, peer_grad),
                "dice_target_cosine": cos(dice_grad, target_grad),
                "dice_peer_cosine": cos(dice_grad, peer_grad),
            }
    if set(results) != set(cohort):
        raise ValueError("Incomplete frozen cohort")
    groups = {}
    for name in ("fragmented", "other_limited", "covered_controls", "remainder"):
        rows = [r for r in results.values() if r["group"] == name]
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "full_helps_target": sum(r["full_target_cosine"] is not None
                                     and r["full_target_cosine"] > 0 for r in rows),
            "full_helps_peer": sum(r["full_peer_cosine"] is not None
                                   and r["full_peer_cosine"] > 0 for r in rows),
        }
    return {
        "contract": "m95_peer_dice_pullback_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "peer_sha256": PEER_SHA,
        "checkpoint_sha256": CHECKPOINT_SHA, "groups": groups,
        "rows": [results[i] for i in sorted(results)],
        "limits": "Matched final mask BCE/Dice query gradient only; excludes full decoder, optimizer and new-model native backward.",
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
