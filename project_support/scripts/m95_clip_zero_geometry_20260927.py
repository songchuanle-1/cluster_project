"""Prediction-blind native TRAIN CLIP zero-row geometry audit."""
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
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    import numpy as np
    import torch

    root = args.data_root
    annotations = root / "scanrefer/ScanRefer_train_new.json"
    scenes = sorted({row["scene_id"] for row in json.loads(annotations.read_text())})[:64]
    if len(scenes) != 64 or args.output.exists():
        raise ValueError("Frozen cohort absent or output exists")
    result = {"contract": "m95_clip_zero_geometry_v1", "admission": False,
              "annotation_sha256": sha(annotations), "rows": [],
              "limits": "Unaugmented native TRAIN associations; no cache producer provenance or causal intervention."}
    for scene in scenes:
        physical = root / "scannetv2/train" / (scene + "_refer.pth")
        cache = root / "clip_feat" / (scene + ".pth")
        _, _, sp, semantic, _ = torch.load(physical, map_location="cpu", weights_only=False)
        clip = torch.load(cache, map_location="cpu", weights_only=False)
        sp = np.asarray(sp, dtype=np.int64)
        semantic = np.asarray(semantic, dtype=np.int64)
        if sp.shape != semantic.shape or not np.array_equal(np.unique(sp), np.arange(len(clip))):
            raise ValueError(f"Native axis mismatch: {scene}")
        zeros = (clip == 0).all(dim=1).numpy()
        counts = np.bincount(sp, minlength=len(clip))
        unknown = np.bincount(sp, weights=(semantic < 0), minlength=len(clip)) / counts
        purity = np.empty(len(clip))
        for sid in range(len(clip)):
            labels = semantic[sp == sid]
            purity[sid] = max(Counter(labels.tolist()).values()) / len(labels)
        zero_ids = np.flatnonzero(zeros)
        control_ids = set(np.flatnonzero(~zeros).tolist())
        pairs = []
        for sid in sorted(zero_ids, key=lambda i: (counts[i], i)):
            if not control_ids:
                break
            match = min(control_ids, key=lambda i: (abs(int(counts[sid]) - int(counts[i])), i))
            control_ids.remove(match)
            pairs.append([int(sid), int(match)])
        def stats(ids):
            return {"n": len(ids), "median_size": float(np.median(counts[ids])) if len(ids) else None,
                    "mean_unknown": float(np.mean(unknown[ids])) if len(ids) else None,
                    "mean_purity": float(np.mean(purity[ids])) if len(ids) else None}
        z = np.array([p[0] for p in pairs], dtype=int)
        c = np.array([p[1] for p in pairs], dtype=int)
        result["rows"].append({
            "scene": scene, "physical_sha256": sha(physical), "clip_sha256": sha(cache),
            "all_zero": stats(zero_ids), "all_nonzero": stats(np.flatnonzero(~zeros)),
            "matched_zero": stats(z), "matched_nonzero": stats(c),
            "pairs": len(pairs),
            "paired_mean_unknown_difference": float(np.mean(unknown[z] - unknown[c])) if len(pairs) else None,
            "paired_mean_purity_difference": float(np.mean(purity[z] - purity[c])) if len(pairs) else None,
        })
    rows = result["rows"]
    result["summary"] = {
        "scenes": len(rows),
        "zero_rows": sum(r["all_zero"]["n"] for r in rows),
        "matched_pairs": sum(r["pairs"] for r in rows),
        "scene_unknown_positive": sum((r["paired_mean_unknown_difference"] or 0) > 0 for r in rows),
        "scene_purity_negative": sum((r["paired_mean_purity_difference"] or 0) < 0 for r in rows),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
