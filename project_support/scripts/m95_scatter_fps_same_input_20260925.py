"""Repeat native scatter_mean and entry FPS on one fixed TRAIN item."""
import argparse
import hashlib
import json
import logging
from pathlib import Path
import sys


EXPECTED_MANIFEST = (
    "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
)
TARGET_ROWS = (95, 193)


def digest(tensor):
    return hashlib.sha256(
        tensor.detach().cpu().contiguous().numpy().tobytes()
    ).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeats", type=int, default=32)
    parser.add_argument("--cpu-control", action="store_true")
    args = parser.parse_args()
    if args.repeats < 2:
        raise ValueError("At least two repeats required")
    if __import__("os").environ.get("CUDA_VISIBLE_DEVICES") != "7":
        raise ValueError("Only authorized physical GPU7")
    root, bundle = Path(args.root).resolve(), Path(args.bundle).resolve()
    sys.path[:0] = [str(bundle), str(root), str(root / "framework/lib")]

    import torch
    from torch_scatter import scatter_mean
    from pointnet2.pointnet2_utils import FurthestPointSampling
    import pointnet2._ext as extension
    import gorilla
    from framework.dataset import build_dataset
    from native_manifest_capture_20260922 import (
        load_manifest, manifest_dataset_indices,
    )

    manifest = load_manifest(args.manifest, EXPECTED_MANIFEST)
    binary = Path(extension.__file__).resolve()
    config = root / (
        "configs/Quard/ctf_hcg_csort/"
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml"
    )
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("scatter_fps"))
    indices = manifest_dataset_indices(dataset, manifest)
    targets = {
        index: next(row for row in manifest.rows.values()
                    if row["manifest_index"] == index)
        for index in TARGET_ROWS
    }
    result = {
        "contract": "m95_scatter_fps_same_input_v1",
        "scope": "Repeated native operators on one fixed TRAIN item per scene",
        "manifest_sha256": EXPECTED_MANIFEST,
        "extension_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "repeats": args.repeats,
        "rows": [],
        "admission": False,
    }
    torch.set_num_threads(1)
    for index, row in targets.items():
        dataset_index = next(
            i for i in indices
            if any(
                str(ann["scene_id"]) == row["scene_id"]
                and int(ann["ann_id"]) == int(row["ann_id"])
                for ann in dataset.scene_inputs[i]
            )
        )
        item = dataset[dataset_index]
        batch = dataset.collate_fn([item])
        coords = batch["coords_float"].cuda()
        labels = batch["superpoints"].cuda()
        start, end = int(batch["batch_offsets"][0]), int(batch["batch_offsets"][1])
        observations = []
        with torch.no_grad():
            for _ in range(args.repeats):
                mean = scatter_mean(coords, labels, dim=0)[start:end]
                fps = FurthestPointSampling.apply(mean.unsqueeze(0), 256)
                observations.append((digest(mean), mean.cpu(), fps.cpu().reshape(-1)))
        first = observations[0]
        result["rows"].append({
            "manifest_index": index,
            "scene_id": row["scene_id"],
            "dataset_index": dataset_index,
            "coords_sha256": digest(coords),
            "superpoints_sha256": digest(labels),
            "scatter_unique_hashes": len(set(x[0] for x in observations)),
            "scatter_max_abs_delta": max(
                float((first[1] - x[1]).abs().max()) for x in observations
            ),
            "fps_unique_outputs": len(set(
                tuple(x[2].tolist()) for x in observations
            )),
            "fps_changed_indices_from_first": [
                int((first[2] != x[2]).sum()) for x in observations[1:]
            ],
        })
        if args.cpu_control:
            cpu_coords = batch["coords_float"].contiguous()
            cpu_labels = batch["superpoints"].contiguous()
            cpu_outputs = [
                scatter_mean(cpu_coords, cpu_labels, dim=0)[start:end]
                for _ in range(args.repeats)
            ]
            result["rows"][-1]["cpu_scatter_unique_hashes"] = len({
                digest(value) for value in cpu_outputs
            })
            result["rows"][-1]["cpu_scatter_max_abs_delta"] = max(
                float((cpu_outputs[0] - value).abs().max())
                for value in cpu_outputs
            )
            result["rows"][-1]["cpu_gpu_first_max_abs_delta"] = float(
                (cpu_outputs[0] - first[1]).abs().max()
            )
    output = Path(args.output)
    if output.exists():
        raise ValueError("Require a new report")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
