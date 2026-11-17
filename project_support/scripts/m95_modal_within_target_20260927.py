"""Frozen within-target modality contrast, retrospective only."""
import argparse
import json
from pathlib import Path

from m95_modal_disagreement_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PEER_SHA, PRODUCER_SHA, sha,
)


def analyze(capture_path, artifact_root, peer_path):
    import torch
    import torch.nn.functional as F

    if sha(capture_path) != CAPTURE_SHA or sha(peer_path) != PEER_SHA:
        raise ValueError("Frozen source differs")
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
            best = int(peer["best_positive_index"])
            positive = [i for i, yes in enumerate(native["native_positive"]) if yes]
            if best not in positive or best != max(
                    positive, key=lambda i: (float(native["ious"][i]), -i)):
                raise ValueError("Best positive differs")
            two = artifact["features"]["projected_2d"].float()
            three = artifact["features"]["projected_3d"].float()
            target = artifact["target_union"].bool()
            logits = artifact["query_mask_logits"].float()[best]
            masks = artifact["query_masks"].bool()[best]
            if (two.shape != three.shape or two.shape[0] != target.numel()
                    or not torch.equal(masks, logits > 0)):
                raise ValueError("Support differs")
            score = 1 - F.cosine_similarity(two, three, dim=1, eps=1e-12)
            missed = torch.nonzero(target & ~masks).flatten().tolist()
            covered = torch.nonzero(target & masks).flatten().tolist()
            if not missed:
                raise ValueError("Frozen missed support differs")
            pairs = []
            for t in missed:
                if not covered:
                    break
                c = min(covered, key=lambda x: (abs(float(logits[t] - logits[x])), x))
                covered.remove(c)
                pairs.append((t, c))
            delta = (sum(float(score[t] - score[c]) for t, c in pairs) / len(pairs)
                     if pairs else None)
            results[idx] = {
                "manifest_index": idx, "scene": native["scene"], "group": peer["group"],
                "missed": len(missed), "covered": int((target & masks).sum()),
                "pairs": len(pairs), "difference": delta,
                "positive": delta > 0 if delta is not None else None,
                "mean_abs_logit_distance": (
                    sum(abs(float(logits[t] - logits[c])) for t, c in pairs) / len(pairs)
                    if pairs else None),
            }
    if set(results) != set(cohort):
        raise ValueError("Incomplete frozen cohort")
    groups = {}
    for name in ("fragmented", "other_limited", "covered_controls", "remainder"):
        rows = [r for r in results.values() if r["group"] == name]
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "defined": sum(r["difference"] is not None for r in rows),
            "positive": sum(r["positive"] is True for r in rows),
        }
    return {
        "contract": "m95_modal_within_target_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "peer_sha256": PEER_SHA,
        "groups": groups, "rows": [results[i] for i in sorted(results)],
        "limits": "Frozen TRAIN post hoc mask-stratified control; not causal new-model intervention.",
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
