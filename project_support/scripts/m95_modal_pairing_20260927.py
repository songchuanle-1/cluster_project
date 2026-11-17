"""Frozen native cross-modal alignment roll placebo."""
import argparse
import json
from pathlib import Path

from m95_modal_disagreement_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PEER_SHA, PRODUCER_SHA, sha,
)


def analyze(capture_path, artifact_root, peer_path, hardpeer_path):
    import torch
    import torch.nn.functional as F

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
            native, peer, old = source[idx], cohort[idx], hard_rows[idx]
            if (idx in results or artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["manifest_sha256"] != MANIFEST_SHA
                    or artifact["axis"]["scene"] != native["scene"]
                    or peer["scene"] != native["scene"] or old["scene"] != native["scene"]):
                raise ValueError("Axis differs")
            two = artifact["features"]["projected_2d"].float()
            three = artifact["features"]["projected_3d"].float()
            target = artifact["target_union"].bool()
            physical = artifact["physical_instance_labels"].long()
            best = int(peer["best_positive_index"])
            positives = [i for i, yes in enumerate(native["native_positive"]) if yes]
            if best not in positives or best != max(
                    positives, key=lambda i: (float(native["ious"][i]), -i)):
                raise ValueError("Positive differs")
            logits = artifact["query_mask_logits"].float()[best]
            masks = artifact["query_masks"].bool()[best]
            if (two.shape != three.shape or two.shape[0] != target.numel()
                    or not torch.equal(masks, logits > 0)):
                raise ValueError("Support differs")
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
            if len(pairs) != old["pairs"]:
                raise ValueError("Hard-peer pair count differs")
            original = 1 - F.cosine_similarity(two, three, dim=1, eps=1e-12)
            rolled = 1 - F.cosine_similarity(two.roll(1, dims=0), three, dim=1, eps=1e-12)

            def delta(signal):
                return sum(float(signal[t] - signal[p]) for t, p in pairs) / len(pairs)

            first, placebo = delta(original), delta(rolled)
            if abs(first - old["score_delta"]) > 1e-6:
                raise ValueError("Frozen hard-peer result differs")
            results[idx] = {
                "manifest_index": idx, "scene": native["scene"], "group": peer["group"],
                "pairs": len(pairs), "original_delta": first, "roll_delta": placebo,
                "alignment_advantage": first - placebo,
            }
    if set(results) != set(cohort):
        raise ValueError("Incomplete cohort")
    groups = {}
    for name in ("fragmented", "other_limited", "covered_controls", "remainder"):
        rows = [r for r in results.values() if r["group"] == name]
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "alignment_advantage_positive": sum(r["alignment_advantage"] > 0 for r in rows),
            "mean_advantage": sum(r["alignment_advantage"] for r in rows) / len(rows),
        }
    return {
        "contract": "m95_modal_pairing_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "peer_sha256": PEER_SHA,
        "hardpeer_sha256": sha(hardpeer_path), "groups": groups,
        "rows": [results[i] for i in sorted(results)],
        "limits": "Frozen TRAIN alignment placebo; not matched new-model forward, backward or efficacy.",
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
    print(json.dumps(report["groups"]))


if __name__ == "__main__":
    main()
