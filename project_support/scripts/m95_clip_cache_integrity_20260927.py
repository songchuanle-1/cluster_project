"""Physical CLIP cache integrity, CPU-only and prediction-blind."""
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
    import torch
    root = args.data_root
    annotation_path = root / "scanrefer/ScanRefer_train_new.json"
    scenes = sorted({row["scene_id"] for row in json.loads(annotation_path.read_text())})[:64]
    if len(scenes) != 64:
        raise ValueError("Insufficient scenes")
    totals = Counter()
    rows = []
    hashes = {}
    sampled_rows = []
    for scene in scenes:
        path = root / "clip_feat" / (scene + ".pth")
        feature = torch.load(path, map_location="cpu", weights_only=False)
        if not isinstance(feature, torch.Tensor) or feature.ndim != 2 or feature.shape[1] != 1024:
            raise ValueError(f"Feature schema differs: {scene}")
        if not torch.is_floating_point(feature):
            raise ValueError(f"Feature dtype differs: {scene}")
        finite = torch.isfinite(feature).all(dim=1)
        zero = (feature == 0).all(dim=1)
        distinct = torch.unique(feature, dim=0).shape[0]
        digest = sha(path)
        hashes.setdefault(digest, []).append(scene)
        sampled_rows.append(feature[0].clone())
        result = {"scene": scene, "sha256": digest, "rows": feature.shape[0],
                  "nonfinite": int((~finite).sum()), "zero": int(zero.sum()),
                  "duplicate_rows": feature.shape[0] - distinct}
        rows.append(result)
        totals["rows"] += feature.shape[0]
        totals["nonfinite"] += result["nonfinite"]
        totals["zero"] += result["zero"]
        totals["duplicate_rows"] += result["duplicate_rows"]
    totals["identical_scene_pairs"] = sum(n * (n - 1) // 2 for n in map(len, hashes.values()))
    totals["different_scene_control_pairs"] = len(sampled_rows) * (len(sampled_rows) - 1) // 2
    totals["different_scene_control_equal"] = sum(
        bool(torch.equal(sampled_rows[i], sampled_rows[j]))
        for i in range(len(sampled_rows)) for j in range(i + 1, len(sampled_rows)))
    if args.output.exists():
        raise ValueError("Output exists")
    result = {"contract": "m95_clip_cache_integrity_v1", "admission": False,
              "annotation_sha256": sha(annotation_path), "totals": dict(totals),
              "rows": rows, "limits": "Exact-content integrity only, not physical semantic provenance."}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["totals"], sort_keys=True))


if __name__ == "__main__":
    main()
