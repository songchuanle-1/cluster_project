"""Frozen projected-modality norm integrity on hard-peer pairs."""
import argparse
import json
from pathlib import Path

from m95_modal_disagreement_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PEER_SHA, PRODUCER_SHA, sha,
)

def analyze(capture_path, artifact_root, peer_path, hardpeer_path):
    import torch

    if sha(capture_path) != CAPTURE_SHA or sha(peer_path) != PEER_SHA:
        raise ValueError("Frozen source differs")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    peers = json.loads(peer_path.read_text(encoding="utf-8"))
    hard = json.loads(hardpeer_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256 or peers["capture_sha256"] != CAPTURE_SHA
            or len(peers["rows"]) != 26 or hard["contract"] != "m95_modal_hardpeer_v1"
            or hard["peer_sha256"] != PEER_SHA):
        raise ValueError("Frozen contract differs")
    source = {int(r["manifest_index"]): r for r in capture["rows"]}
    cohort = {int(r["manifest_index"]): r for r in peers["rows"]}
    hard_rows = {int(r["manifest_index"]): r for r in hard["rows"]}
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
            native, peer, matched = source[idx], cohort[idx], hard_rows[idx]
            if (idx in results or artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["manifest_sha256"] != MANIFEST_SHA
                    or artifact["axis"]["scene"] != native["scene"]
                    or peer["scene"] != native["scene"]
                    or matched["scene"] != native["scene"]):
                raise ValueError("Axis differs")
            best = int(peer["best_positive_index"])
            positive = [i for i, yes in enumerate(native["native_positive"]) if yes]
            if best not in positive or best != max(
                    positive, key=lambda i: (float(native["ious"][i]), -i)):
                raise ValueError("Best query differs")
            target = artifact["target_union"].bool()
            physical = artifact["physical_instance_labels"].long()
            logits = artifact["query_mask_logits"].float()[best]
            masks = artifact["query_masks"].bool()[best]
            if not torch.equal(masks, logits > 0):
                raise ValueError("Mask differs")
            missed = torch.nonzero(target & ~masks).flatten().tolist()
            peer_axis = torch.zeros_like(target)
            for item in peer["peers"]:
                peer_axis |= physical == int(item["object_id"])
            eligible = torch.nonzero(peer_axis).flatten().tolist()
            pairs = []
            for t in missed:
                if not eligible:
                    break
                p = min(eligible, key=lambda x: (abs(float(logits[t] - logits[x])), x))
                eligible.remove(p)
                pairs.append((t, p))
            if len(pairs) != matched["pairs"]:
                raise ValueError("Hard-peer pairing differs")
            record = {"manifest_index": idx, "scene": native["scene"],
                      "group": peer["group"], "pairs": len(pairs), "stages": {}}
            for stage in ("projected_2d", "projected_3d"):
                vectors = artifact["features"][stage].float()
                norm = vectors.norm(dim=1)
                if norm.shape != target.shape or not torch.isfinite(norm).all():
                    raise ValueError("Norm support differs")
                a = norm[[t for t, _ in pairs]]
                b = norm[[p for _, p in pairs]]
                record["stages"][stage] = {
                    "target_zero": int((a == 0).sum()), "peer_zero": int((b == 0).sum()),
                    "target_min": float(a.min()), "peer_min": float(b.min()),
                    "target_median": float(a.median()), "peer_median": float(b.median()),
                    "target_mean": float(a.mean()), "peer_mean": float(b.mean()),
                }
            results[idx] = record
    if set(results) != set(cohort):
        raise ValueError("Incomplete cohort")
    return {
        "contract": "m95_modal_support_integrity_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "peer_sha256": PEER_SHA,
        "hardpeer_sha256": sha(hardpeer_path),
        "rows": [results[i] for i in sorted(results)],
        "limits": "Frozen TRAIN norm audit, not causal mechanism or efficacy.",
    }

def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "peer", "hardpeer", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(args.capture, args.artifact_root, args.peer, args.hardpeer)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps([r for r in report["rows"] if r["group"] == "fragmented"]))

if __name__ == "__main__":
    main()
