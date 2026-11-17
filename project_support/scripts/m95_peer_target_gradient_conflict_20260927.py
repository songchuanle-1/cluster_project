"""Final-layer BCE query-gradient direction on frozen M95 physical peer cohort."""
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
    weight = state[prefix + "weight"].float()
    bias = state[prefix + "bias"].float()
    source = {int(r["manifest_index"]): r for r in capture["rows"]}
    cohort = {int(r["manifest_index"]): r for r in peers["rows"]}
    results = {}
    for entry in capture["feature_artifacts"]:
        if len(results) == len(cohort):
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Artifact bytes differ: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            if idx not in cohort:
                continue
            native, peer = source[idx], cohort[idx]
            if (idx in results
                    or artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["manifest_sha256"] != MANIFEST_SHA
                    or artifact["axis"]["scene"] != native["scene"]
                    or peer["scene"] != native["scene"]):
                raise ValueError("Native identity differs")
            query = artifact["identity_query"]["query_states"].float()
            features = artifact["features"]["final"].float()
            masks = artifact["query_masks"].bool()
            target = artifact["target_union"].bool()
            physical = artifact["physical_instance_labels"].long()
            semantic = torch.as_tensor(artifact["semantic_labels"]).long()
            normalized = F.layer_norm(query, (256,), weight, bias)
            logits = normalized @ features.T
            saved = artifact["query_mask_logits"].float()
            error = float((logits - saved).abs().max())
            if (error > 1e-4 or query.shape != (128, 256)
                    or features.shape != (target.numel(), 256)
                    or masks.shape != (128, target.numel())
                    or not torch.equal(masks, saved > 0)
                    or not torch.isfinite(logits).all()):
                raise ValueError(f"Native logit reconstruction differs: {idx}")
            best = int(peer["best_positive_index"])
            positive = [i for i, yes in enumerate(native["native_positive"]) if yes]
            if (best not in positive or best != max(
                    positive, key=lambda i: (float(native["ious"][i]), -i))):
                raise ValueError("Best positive selection differs")
            missed = target & ~masks[best]
            peer_axis = torch.zeros_like(target)
            for item in peer["peers"]:
                peer_axis |= physical == int(item["object_id"])
            if (int(missed.sum()) == 0 or int(peer_axis.sum()) == 0
                    or int(missed.sum()) < peer["target_missed"]["total"]
                    or int(peer_axis.sum()) != sum(p["total"] for p in peer["peers"])):
                raise ValueError("Frozen target/peer support differs")
            category = Counter(semantic[target].tolist()).most_common(1)[0][0]
            if category < 0:
                raise ValueError("Invalid target semantic class")
            different = (~target & ~peer_axis & (physical >= 0)
                         & (semantic >= 0) & (semantic != category))
            negative_ids = torch.nonzero(different).flatten()[:int(peer_axis.sum())]
            point_logits = logits[best]
            def direction(axis, positive_label):
                values = point_logits[axis]
                residual = values.sigmoid() - float(positive_label)
                gradient = (residual[:, None] * features[axis]).mean(dim=0)
                return gradient, float(values.mean())
            target_grad, target_logit = direction(missed, True)
            peer_grad, peer_logit = direction(peer_axis, False)
            def alignment(other):
                denom = float(target_grad.norm() * other.norm())
                return (float(torch.dot(target_grad, other) / denom)
                        if denom > 0 else None)
            control_cosine = None
            if negative_ids.numel():
                control_axis = torch.zeros_like(target)
                control_axis[negative_ids] = True
                control_grad, _ = direction(control_axis, False)
                control_cosine = alignment(control_grad)
            results[idx] = {
                "manifest_index": idx, "scene": native["scene"],
                "group": peer["group"], "best_positive": best,
                "reconstruction_error": error,
                "missed_target": int(missed.sum()),
                "peer_superpoints": int(peer_axis.sum()),
                "peer_covered_by_best": int((peer_axis & masks[best]).sum()),
                "target_mean_logit": target_logit,
                "peer_mean_logit": peer_logit,
                "gradient_cosine": alignment(peer_grad),
                "different_class_control_cosine": control_cosine,
                "control_superpoints": int(negative_ids.numel()),
            }
    if set(results) != set(cohort):
        raise ValueError("Incomplete frozen cohort")
    groups = {}
    for group in ("fragmented", "other_limited", "covered_controls", "remainder"):
        rows = [r for r in results.values() if r["group"] == group]
        groups[group] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "gradient_defined": sum(r["gradient_cosine"] is not None for r in rows),
            "conflict": sum(r["gradient_cosine"] is not None and
                            r["gradient_cosine"] < 0 for r in rows),
            "compatible": sum(r["gradient_cosine"] is not None and
                              r["gradient_cosine"] > 0 for r in rows),
            "control_defined": sum(r["different_class_control_cosine"] is not None
                                   for r in rows),
        }
    return {
        "contract": "m95_peer_target_gradient_conflict_v1",
        "admission": False, "capture_sha256": CAPTURE_SHA,
        "peer_sha256": PEER_SHA, "checkpoint_sha256": CHECKPOINT_SHA,
        "groups": groups, "rows": [results[i] for i in sorted(results)],
        "limits": "Final-layer BCE diagnostic excludes Dice and full decoder Jacobian; not a new-model backward or admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "peer", "checkpoint", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.peer,
                     args.checkpoint)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["groups"]))


if __name__ == "__main__":
    main()
