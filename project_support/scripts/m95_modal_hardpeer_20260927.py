"""Frozen same-class, query-logit-matched peer control."""
import argparse
import json
from pathlib import Path

from m95_modal_disagreement_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PEER_SHA, PRODUCER_SHA, sha,
)

def analyze(capture_path, artifact_root, peer_path, previous_path):
    import torch
    import torch.nn.functional as F

    if sha(capture_path) != CAPTURE_SHA or sha(peer_path) != PEER_SHA:
        raise ValueError("Frozen source differs")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    peers = json.loads(peer_path.read_text(encoding="utf-8"))
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256
            or peers["capture_sha256"] != CAPTURE_SHA
            or len(peers["rows"]) != 26
            or previous["contract"] != "m95_modal_disagreement_v1"
            or previous["peer_sha256"] != PEER_SHA):
        raise ValueError("Frozen contract differs")
    source = {int(r["manifest_index"]): r for r in capture["rows"]}
    cohort = {int(r["manifest_index"]): r for r in peers["rows"]}
    prior = {int(r["manifest_index"]): r for r in previous["rows"]}
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
            native, peer, old = source[idx], cohort[idx], prior[idx]
            if (idx in results or artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["manifest_sha256"] != MANIFEST_SHA
                    or artifact["axis"]["scene"] != native["scene"]
                    or peer["scene"] != native["scene"]
                    or old["scene"] != native["scene"]):
                raise ValueError("Axis differs")
            two = artifact["features"]["projected_2d"].float()
            three = artifact["features"]["projected_3d"].float()
            score = 1 - F.cosine_similarity(two, three, dim=1, eps=1e-12)
            target = artifact["target_union"].bool()
            physical = artifact["physical_instance_labels"].long()
            best = int(peer["best_positive_index"])
            positive = [i for i, yes in enumerate(native["native_positive"]) if yes]
            if best not in positive or best != max(
                    positive, key=lambda i: (float(native["ious"][i]), -i)):
                raise ValueError("Best query differs")
            logits = artifact["query_mask_logits"].float()[best]
            masks = artifact["query_masks"].bool()[best]
            if not torch.equal(masks, logits > 0) or score.shape != target.shape:
                raise ValueError("Support differs")
            missed = torch.nonzero(target & ~masks).flatten().tolist()
            peer_axis = torch.zeros_like(target)
            for item in peer["peers"]:
                peer_axis |= physical == int(item["object_id"])
            eligible = torch.nonzero(peer_axis).flatten().tolist()
            if (not missed or not eligible or len(eligible) != old["peer_superpoints"]
                    or len(missed) != old["missed_target"]):
                raise ValueError("Frozen support differs")
            selected = []
            for t in missed:
                if not eligible:
                    break
                p = min(eligible, key=lambda x: (abs(float(logits[t] - logits[x])), x))
                eligible.remove(p)
                selected.append((t, p))
            target_score = [float(score[t]) for t, _ in selected]
            peer_score = [float(score[p]) for _, p in selected]
            target_logit = [float(logits[t]) for t, _ in selected]
            peer_logit = [float(logits[p]) for _, p in selected]
            delta = sum(a - b for a, b in zip(target_score, peer_score)) / len(selected)
            results[idx] = {
                "manifest_index": idx, "scene": native["scene"], "group": peer["group"],
                "pairs": len(selected), "score_delta": delta,
                "positive": delta > 0,
                "mean_abs_logit_distance": sum(
                    abs(a - b) for a, b in zip(target_logit, peer_logit)
                ) / len(selected),
                "unmatched_target": len(missed) - len(selected),
                "unmatched_peer": len(eligible),
                "target_mean": sum(target_score) / len(selected),
                "peer_mean": sum(peer_score) / len(selected),
            }
    if set(results) != set(cohort):
        raise ValueError("Incomplete cohort")
    groups = {}
    for name in ("fragmented", "other_limited", "covered_controls", "remainder"):
        rows = [r for r in results.values() if r["group"] == name]
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "positive": sum(r["positive"] for r in rows),
            "mean_delta": sum(r["score_delta"] for r in rows) / len(rows),
        }
    return {
        "contract": "m95_modal_hardpeer_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "peer_sha256": PEER_SHA,
        "previous_sha256": sha(previous_path), "groups": groups,
        "rows": [results[i] for i in sorted(results)],
        "limits": "Retrospective GT-bound hard-peer control, no new-model forward or training efficacy.",
    }

def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "peer", "previous", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.peer, args.previous)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["groups"]))

if __name__ == "__main__":
    main()
