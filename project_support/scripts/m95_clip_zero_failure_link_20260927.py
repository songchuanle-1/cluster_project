"""Frozen native M95 outcome joined to physical zero CLIP rows, CPU-only."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

CAPTURE_SHA = "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "data-root", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    import numpy as np
    import torch
    if sha(args.capture) != CAPTURE_SHA or args.output.exists():
        raise ValueError("Frozen capture differs or output exists")
    capture = json.loads(args.capture.read_text())
    if capture.get("capture_mode") != "full_train_scan" or len(capture["rows"]) != 256:
        raise ValueError("Native capture schema differs")
    by_scene = defaultdict(list)
    for row in capture["rows"]:
        by_scene[row["scene"]].append(row)
    totals = Counter()
    results = []
    cache_hashes = {}
    for scene, source_rows in sorted(by_scene.items()):
        path = args.data_root / "clip_feat" / (scene + ".pth")
        clip = torch.load(path, map_location="cpu", weights_only=False)
        if clip.ndim != 2 or clip.shape[1] != 1024:
            raise ValueError(f"Cache schema differs: {scene}")
        cache_hashes[scene] = sha(path)
        zero = (clip == 0).all(dim=1).numpy()
        for row in source_rows:
            ids = np.asarray(row["original_superpoint_ids"], dtype=int)
            labels = np.asarray(row["physical_instance_labels"], dtype=int)
            if len(ids) != len(labels) or np.unique(ids).size != len(ids):
                raise ValueError(f"Physical binding differs: {scene}")
            if ids.min() < 0 or ids.max() >= len(zero):
                raise ValueError(f"Cache row out of bounds: {scene}")
            target_ids = {int(x) for x in row["target_instances"]}
            target = np.isin(labels, list(target_ids))
            if not target.any():
                raise ValueError(f"No target support: {scene}")
            selected = int(row["selected_query"])
            ious = row["ious"]
            if selected < 0 or selected >= len(ious):
                raise ValueError(f"Selected query differs: {scene}")
            failure = float(ious[selected]) <= 0.5
            target_zero = int(zero[ids[target]].sum())
            other_zero = int(zero[ids[~target]].sum())
            exposed = target_zero > 0
            totals["expressions"] += 1
            totals["exposed"] += int(exposed)
            totals["exposed_fail"] += int(exposed and failure)
            totals["unexposed_fail"] += int(not exposed and failure)
            results.append({
                "scene": scene, "ann_id": int(row["ann_id"]),
                "manifest_index": int(row["manifest_index"]),
                "selected_iou": float(ious[selected]), "failure": failure,
                "target_superpoints": int(target.sum()), "target_zero": target_zero,
                "other_superpoints": int((~target).sum()), "other_zero": other_zero,
                "exposed": exposed,
            })
    pairs = []
    for scene in sorted(by_scene):
        rows = [r for r in results if r["scene"] == scene]
        yes = [r for r in rows if r["exposed"]]
        no = [r for r in rows if not r["exposed"]]
        if yes and no:
            pairs.append({"scene": scene, "exposed": len(yes), "unexposed": len(no),
                          "exposed_fail": sum(r["failure"] for r in yes),
                          "unexposed_fail": sum(r["failure"] for r in no)})
    result = {"contract": "m95_clip_zero_failure_link_v1", "admission": False,
              "capture_sha256": CAPTURE_SHA, "cache_hashes": cache_hashes,
              "totals": dict(totals), "same_scene_pairs": pairs,
              "rows": results, "limits": "TRAIN observational association; no mechanism or admission."}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"totals": result["totals"],
                      "discordant_scenes": len(pairs)}, sort_keys=True))


if __name__ == "__main__":
    main()
