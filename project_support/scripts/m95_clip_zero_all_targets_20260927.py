"""All-annotation zero-CLIP exposure in frozen native TRAIN scenes."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
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
    annotations_path = root / "scanrefer/ScanRefer_train_new.json"
    grouped = defaultdict(list)
    for row in json.loads(annotations_path.read_text()):
        grouped[row["scene_id"]].append(row)
    scenes = sorted(grouped)[:64]
    if len(scenes) != 64:
        raise ValueError("Insufficient scenes")
    total = Counter()
    rows = []
    for scene in scenes:
        data_path = root / "scannetv2/train" / (scene + "_refer.pth")
        clip_path = root / "clip_feat" / (scene + ".pth")
        _, _, sp, _, ins = torch.load(data_path, map_location="cpu", weights_only=False)
        clip = torch.load(clip_path, map_location="cpu", weights_only=False)
        sp = np.asarray(sp)
        ins = np.asarray(ins)
        if sp.shape != ins.shape or not np.array_equal(
                np.unique(sp), np.arange(clip.shape[0])):
            raise ValueError(f"Native axis differs: {scene}")
        zero = (clip == 0).all(dim=1).numpy()
        count = np.bincount(sp, minlength=clip.shape[0])
        owner = {}
        for sid in range(len(zero)):
            if count[sid] < 5:
                continue
            values = ins[sp == sid]
            ids, counts = np.unique(values, return_counts=True)
            best = int(counts.argmax())
            if ids[best] >= 0 and counts[best] * 2 > len(values):
                owner[sid] = int(ids[best])
        scene_count = Counter()
        exposed_objects = set()
        unexposed_objects = set()
        for ann in grouped[scene]:
            targets = {int(x) for x in ann.get("object_ids", [ann.get("object_id")])}
            rows_for_target = [sid for sid, iid in owner.items() if iid in targets]
            if not rows_for_target:
                scene_count["target_unsupported_annotations"] += 1
                continue
            nzero = sum(bool(zero[sid]) for sid in rows_for_target)
            scene_count["target_annotations"] += 1
            scene_count["target_rows"] += len(rows_for_target)
            scene_count["target_zero"] += nzero
            scene_count["exposed_annotations"] += int(nzero > 0)
            for iid in targets:
                if nzero:
                    exposed_objects.add(iid)
                else:
                    unexposed_objects.add(iid)
        target_ids = {int(x) for ann in grouped[scene] for x in ann.get(
            "object_ids", [ann.get("object_id")])}
        non_target = [sid for sid, iid in owner.items() if iid not in target_ids]
        scene_count["nontarget_rows"] = len(non_target)
        scene_count["nontarget_zero"] = sum(bool(zero[sid]) for sid in non_target)
        scene_count["unique_exposed_objects"] = len(exposed_objects)
        scene_count["unique_unexposed_objects"] = len(unexposed_objects)
        scene_count["mixed_exposure_scene"] = int(bool(exposed_objects) and bool(unexposed_objects))
        total.update(scene_count)
        rows.append({"scene": scene, "counts": dict(scene_count),
                     "data_sha256": sha(data_path), "clip_sha256": sha(clip_path)})
    result = {"contract": "m95_clip_zero_all_targets_v1", "admission": False,
              "annotations_sha256": sha(annotations_path), "totals": dict(total),
              "rows": rows, "limits": "Unaugmented physical TRAIN scenes; no M95 outcome or intervention."}
    if args.output.exists():
        raise ValueError("Output exists")
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["totals"], sort_keys=True))


if __name__ == "__main__":
    main()
