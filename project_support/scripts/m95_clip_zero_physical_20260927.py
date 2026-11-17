"""Map CLIP zero rows onto native physical target superpoints."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ("data-root", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    import numpy as np
    import torch
    root = args.data_root
    annotation_path = root / "scanrefer/ScanRefer_train_new.json"
    chosen = {}
    for item in json.loads(annotation_path.read_text()):
        scene = item["scene_id"]
        if scene not in chosen or int(item["ann_id"]) < int(chosen[scene]["ann_id"]):
            chosen[scene] = item
    scenes = sorted(chosen)[:64]
    if len(scenes) != 64:
        raise ValueError("Insufficient scenes")
    totals = Counter()
    rows = []
    for scene in scenes:
        scene_path = root / "scannetv2/train" / (scene + "_refer.pth")
        clip_path = root / "clip_feat" / (scene + ".pth")
        xyz, rgb, superpoint, semantic, instance = torch.load(
            scene_path, map_location="cpu", weights_only=False)
        clip = torch.load(clip_path, map_location="cpu", weights_only=False)
        sp = np.asarray(superpoint)
        sem = np.asarray(semantic)
        ins = np.asarray(instance)
        if sp.shape != sem.shape or sp.shape != ins.shape or not np.array_equal(
                np.unique(sp), np.arange(clip.shape[0])):
            raise ValueError(f"Native superpoint/cache axis differs: {scene}")
        target = {int(x) for x in chosen[scene].get(
            "object_ids", [chosen[scene].get("object_id")])}
        zero = (clip == 0).all(dim=1).numpy()
        counts = np.bincount(sp, minlength=clip.shape[0])
        scene_counts = Counter()
        for sid in range(clip.shape[0]):
            if counts[sid] < 5:
                continue
            member = ins[sp == sid]
            is_target = sum(int(x) in target for x in member) * 2 > len(member)
            arm = "target" if is_target else "nontarget"
            scene_counts[arm + "_valid"] += 1
            scene_counts[arm + "_zero"] += int(zero[sid])
            if zero[sid]:
                scene_counts["zero_point_count"] += int(counts[sid])
                scene_counts["zero_semantic_unknown"] += int((sem[sp == sid] < 0).all())
        totals.update(scene_counts)
        rows.append({"scene": scene, "ann_id": int(chosen[scene]["ann_id"]),
                     "counts": dict(scene_counts), "scene_sha256": sha(scene_path),
                     "clip_sha256": sha(clip_path)})
    result = {"contract": "m95_clip_zero_physical_v1", "admission": False,
              "annotations_sha256": sha(annotation_path), "totals": dict(totals),
              "rows": rows, "limits": "Unaugmented physical TRAIN scene, not M95 prediction."}
    if args.output.exists():
        raise ValueError("Output exists")
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["totals"], sort_keys=True))


if __name__ == "__main__":
    main()
