"""Native TRAIN sampling threshold screen for the frozen 64 scenes."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dataset-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import torch

    annotation = args.data_root / "scanrefer/ScanRefer_train_new.json"
    scenes = sorted({row["scene_id"] for row in json.loads(annotation.read_text())})[:64]
    config = args.config.read_text()
    source = args.dataset_source.read_text()
    if len(scenes) != 64 or args.output.exists():
        raise ValueError("Frozen cohort or output mismatch")
    if "max_npoint: 2500000" not in config or "def sample_rdn(" not in source:
        raise ValueError("Source contract differs; inspect manually")
    rows = []
    for scene in scenes:
        path = args.data_root / "scannetv2/train" / (scene + "_refer.pth")
        data = torch.load(path, map_location="cpu", weights_only=False)
        n = len(data[0])
        if any(len(x) != n for x in data):
            raise ValueError(f"Point schema mismatch: {scene}")
        rows.append({"scene": scene, "points": n, "sha256": sha(path),
                     "below_sampling_threshold": n <= 2500000})
    result = {
        "contract": "m95_first_point_train_order_v1", "admission": False,
        "input_sha256": {"annotation": sha(annotation), "config": sha(args.config),
                         "dataset_source": sha(args.dataset_source)},
        "threshold": 2500000, "rows": rows,
        "summary": {"scenes": len(rows), "all_below": all(r["below_sampling_threshold"] for r in rows),
                    "max_points": max(r["points"] for r in rows),
                    "above_threshold": sum(not r["below_sampling_threshold"] for r in rows)},
        "limits": "Source/manual ordering contract plus physical counts, not live augmented model execution.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
