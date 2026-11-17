"""Prediction-blind 2D/3D disagreement; frozen peer-cohort audit only."""
import argparse
import json
from pathlib import Path

from m95_native_positive_union_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)

PEER_SHA = "d400c26f9037ed1107e32113e27fec1de6cafaf6bafb183ba807b9f0ad651eaa"


def analyze(capture_path, artifact_root, peer_path):
    import torch
    import torch.nn.functional as F
    from collections import Counter

    if sha(capture_path) != CAPTURE_SHA or sha(peer_path) != PEER_SHA:
        raise ValueError("Frozen input differs")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    peers = json.loads(peer_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256
            or peers["capture_sha256"] != CAPTURE_SHA
            or len(peers["rows"]) != 26):
        raise ValueError("Frozen cohort differs")
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
            if (idx in results
                    or artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["manifest_sha256"] != MANIFEST_SHA
                    or artifact["axis"]["scene"] != native["scene"]
                    or peer["scene"] != native["scene"]):
                raise ValueError("Native identity differs")
            two = artifact["features"]["projected_2d"].float()
            three = artifact["features"]["projected_3d"].float()
            target = artifact["target_union"].bool()
            physical = artifact["physical_instance_labels"].long()
            semantic = torch.as_tensor(artifact["semantic_labels"]).long()
            best = int(peer["best_positive_index"])
            positive = [i for i, yes in enumerate(native["native_positive"]) if yes]
            if best not in positive or best != max(
                    positive, key=lambda i: (float(native["ious"][i]), -i)):
                raise ValueError("Best positive differs")
            masks = artifact["query_masks"].bool()
            if (two.shape != three.shape or two.shape[0] != target.numel()
                    or not torch.isfinite(two).all() or not torch.isfinite(three).all()
                    or not torch.equal(masks, artifact["query_mask_logits"] > 0)):
                raise ValueError("Feature or mask contract differs")
            disagreement = 1 - F.cosine_similarity(two, three, dim=1, eps=1e-12)
            missed = target & ~masks[best]
            covered = target & masks[best]
            peer_axis = torch.zeros_like(target)
            for item in peer["peers"]:
                peer_axis |= physical == int(item["object_id"])
            if (int(missed.sum()) == 0 or int(peer_axis.sum()) == 0
                    or int(peer_axis.sum()) != sum(p["total"] for p in peer["peers"])):
                raise ValueError("Physical support differs")
            category = Counter(semantic[target].tolist()).most_common(1)[0][0]
            if category < 0:
                raise ValueError("Invalid target category")
            different = (~target & ~peer_axis & (physical >= 0)
                         & (semantic >= 0) & (semantic != category))
            ids = torch.nonzero(different).flatten()[:int(peer_axis.sum())]

            def mean(axis):
                return float(disagreement[axis].mean()) if axis.any() else None

            different_axis = torch.zeros_like(target)
            different_axis[ids] = True
            a, b, c = mean(missed), mean(peer_axis), mean(different_axis)
            results[idx] = {
                "manifest_index": idx, "scene": native["scene"],
                "group": peer["group"], "best_positive": best,
                "missed_target": int(missed.sum()),
                "peer_superpoints": int(peer_axis.sum()),
                "different_class_superpoints": int(ids.numel()),
                "missed_mean": a, "peer_mean": b,
                "different_mean": c, "covered_mean": mean(covered),
                "missed_gt_peer": a > b,
                "missed_gt_different": a > c if c is not None else None,
            }
    if set(results) != set(cohort):
        raise ValueError("Incomplete frozen cohort")
    groups = {}
    for name in ("fragmented", "other_limited", "covered_controls", "remainder"):
        rows = [r for r in results.values() if r["group"] == name]
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "missed_gt_peer": sum(r["missed_gt_peer"] for r in rows),
            "different_defined": sum(r["different_mean"] is not None for r in rows),
            "missed_gt_different": sum(r["missed_gt_different"] is True for r in rows),
        }
    return {
        "contract": "m95_modal_disagreement_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "peer_sha256": PEER_SHA,
        "groups": groups, "rows": [results[i] for i in sorted(results)],
        "limits": "Retrospective TRAIN feature screen, not native new-model intervention/backward or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "peer", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.peer)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["groups"]))


if __name__ == "__main__":
    main()
