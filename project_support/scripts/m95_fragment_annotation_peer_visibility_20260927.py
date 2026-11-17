"""Audit annotation-class physical peers and their native query visibility."""
import argparse
import json
from collections import Counter
from pathlib import Path

from m95_native_positive_union_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, POPULATION_SHA, PRODUCER_SHA,
    FRAGMENT_SHA, sha,
)


def analyze(capture_path, artifact_root, manifest_path, population_path,
            fragment_path):
    import torch

    for path, expected in (
        (capture_path, CAPTURE_SHA),
        (manifest_path, MANIFEST_SHA),
        (population_path, POPULATION_SHA),
        (fragment_path, FRAGMENT_SHA),
    ):
        if sha(path) != expected:
            raise ValueError(f"Frozen input differs: {path}")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    population = json.loads(population_path.read_text(encoding="utf-8"))
    fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["capture_mode"] != "full_train_scan"
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or len(capture["rows"]) != 256
            or len(manifest["rows"]) != 256
            or population["capture_sha256"] != CAPTURE_SHA
            or fragment["capture_sha256"] != CAPTURE_SHA):
        raise ValueError("Frozen capture contract differs")

    limited = {r["manifest_index"] for r in population["limited_rows"]}
    controls = {r["manifest_index"] for r in population["control_rows"]}
    fragmented = {r["manifest_index"] for r in fragment["groups"]["limited"]["rows"]
                  if r["extra_recall"] > 0}
    if len(limited) != 16 or len(controls) != 16 or len(fragmented) != 4:
        raise ValueError("Frozen cohort differs")
    native = {int(r["manifest_index"]): r for r in capture["rows"]}
    frozen = {int(r["manifest_index"]): r for r in manifest["rows"]}
    rows = {}
    for entry in capture["feature_artifacts"]:
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Artifact bytes differ: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            if idx in rows or idx not in native or idx not in frozen:
                raise ValueError("Duplicate or unbound row")
            a, m = native[idx], frozen[idx]
            if (artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["manifest_sha256"] != MANIFEST_SHA
                    or artifact["axis"]["scene"] != a["scene"]
                    or str(m["scene_id"]) != a["scene"]
                    or int(m["ann_id"]) != int(a["ann_id"])
                    or str(m["target_object_id"]) != str(a["target_object_id"])):
                raise ValueError(f"Native identity differs: {idx}")
            masks = artifact["query_masks"].bool()
            logits = artifact["query_mask_logits"]
            target = artifact["target_union"].bool()
            semantic = torch.as_tensor(artifact["semantic_labels"]).long()
            physical = artifact["physical_instance_labels"].long()
            if (masks.shape != (128, target.numel()) or masks.shape != logits.shape
                    or semantic.shape != target.shape or physical.shape != target.shape
                    or not torch.isfinite(logits).all()
                    or not torch.equal(logits > 0, masks)
                    or not target.any()):
                raise ValueError(f"Native support axis differs: {idx}")
            support = masks.any(dim=0)
            category = Counter(semantic[target].tolist()).most_common(1)[0][0]
            missed = int((target & ~support).sum())
            peers = []
            for peer_id in m["same_class_peer_object_ids"]:
                peer = physical == int(peer_id)
                count = int(peer.sum())
                known = int((peer & (semantic >= 0)).sum())
                same = int((peer & (semantic == category)).sum()) if category >= 0 else 0
                peers.append({
                    "object_id": str(peer_id), "sampled_superpoints": count,
                    "known_semantic": known, "same_valid_category": same,
                    "unknown_semantic": int((peer & (semantic < 0)).sum()),
                    "covered": int((peer & support).sum()),
                    "uncovered": int((peer & ~support).sum()),
                })
            present = sum(p["sampled_superpoints"] > 0 for p in peers)
            group = ("fragmented" if idx in fragmented else
                     "other_limited" if idx in limited else
                     "covered_controls" if idx in controls else "remainder")
            rows[idx] = {
                "manifest_index": idx, "scene": a["scene"], "group": group,
                "target_category": category, "valid_category": category >= 0,
                "missed_target": missed, "declared_peers": len(peers),
                "present_peers": present, "peers": peers,
            }
    if sorted(rows) != list(range(256)):
        raise ValueError("Incomplete frozen capture")
    selected = [rows[i] for i in sorted(rows)
                if rows[i]["valid_category"] and rows[i]["missed_target"]]
    groups = {}
    for group in ("fragmented", "other_limited", "covered_controls", "remainder"):
        part = [r for r in selected if r["group"] == group]
        groups[group] = {
            "expressions": len(part), "scenes": len({r["scene"] for r in part}),
            "annotated_peer_rows": sum(r["declared_peers"] > 0 for r in part),
            "present_peer_rows": sum(r["present_peers"] > 0 for r in part),
            "absent_peer_rows": sum(r["declared_peers"] > 0 and not r["present_peers"] for r in part),
            "uncovered_peer_rows": sum(any(p["uncovered"] for p in r["peers"]) for r in part),
        }
    special = [rows[i] for i in sorted(fragmented)
               if rows[i]["missed_target"] and rows[i]["valid_category"]]
    if len(special) != 2 or {r["manifest_index"] for r in special} != {64, 104}:
        raise ValueError("Frozen fragmented failure rows differ")
    return {
        "contract": "m95_fragment_annotation_peer_visibility_v1",
        "admission": False, "capture_sha256": CAPTURE_SHA,
        "manifest_sha256": MANIFEST_SHA, "population_sha256": POPULATION_SHA,
        "fragment_sha256": FRAGMENT_SHA,
        "rows": [rows[i] for i in sorted(rows)],
        "groups": groups, "fragmented_missed_rows": special,
        "limits": "Retrospective TRAIN annotation-to-physical crosswalk, no causal intervention or admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "manifest", "population",
                 "fragment", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output already exists")
    result = analyze(args.capture, args.artifact_root, args.manifest,
                     args.population, args.fragment)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                           encoding="ascii")
    print(json.dumps({"groups": result["groups"],
                      "fragmented_missed_rows": result["fragmented_missed_rows"]}))


if __name__ == "__main__":
    main()
