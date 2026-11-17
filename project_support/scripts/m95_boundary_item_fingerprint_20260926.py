"""Bind fixed diagnostic TRAIN items to frozen M95 full-scan inputs."""
import argparse
import hashlib
import json
import logging
from pathlib import Path
import sys


ROWS = (83, 174)
MANIFEST_SHA256 = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
CAPTURE_SHA256 = (
    "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025",
    "9271ea8e5202590e99e3d1e2da1a729ee87262bba8fecf96bd394c7f0abda1cd",
)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frozen_rows(paths):
    result = {}
    for path, expected in zip(paths, CAPTURE_SHA256):
        if sha256(path) != expected:
            raise ValueError("Capture hash differs")
        report = json.loads(Path(path).read_text(encoding="utf-8"))
        rows = {int(row["manifest_index"]): row for row in report["rows"]}
        if set(ROWS) - set(rows):
            raise ValueError("Frozen row missing")
        result[expected] = {i: rows[i]["native_input_sha256"] for i in ROWS}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeats", type=int, default=4)
    args = parser.parse_args()
    if args.repeats < 1 or args.repeats > 16:
        raise ValueError("Bounded repeat count required")
    root, bundle = Path(args.root).resolve(), Path(args.bundle).resolve()
    sys.path[:0] = [str(bundle), str(root), str(root / "framework/lib")]

    import gorilla
    from framework.dataset import build_dataset
    from frozen_capture_contract_20260916 import fingerprint
    from native_manifest_capture_20260922 import load_manifest, manifest_dataset_indices

    frozen = frozen_rows((args.reference, args.candidate))
    manifest = load_manifest(args.manifest, MANIFEST_SHA256)
    config = root / (
        "configs/Quard/ctf_hcg_csort/"
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml"
    )
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("boundary_item"))
    indices = manifest_dataset_indices(dataset, manifest)
    rows = []
    for row_index in ROWS:
        row = next(value for value in manifest.rows.values()
                   if value["manifest_index"] == row_index)
        dataset_index = next(
            i for i in indices
            if any(
                str(ann["scene_id"]) == row["scene_id"]
                and int(ann["ann_id"]) == int(row["ann_id"])
                for ann in dataset.scene_inputs[i]
            )
        )
        hashes = [fingerprint(dataset[dataset_index])
                  for _ in range(args.repeats)]
        rows.append({
            "manifest_index": row_index,
            "dataset_index": dataset_index,
            "item_sha256": hashes,
            "reference_item_sha256": frozen[CAPTURE_SHA256[0]][row_index],
            "candidate_item_sha256": frozen[CAPTURE_SHA256[1]][row_index],
            "matches_reference": [value == frozen[CAPTURE_SHA256[0]][row_index]
                                  for value in hashes],
            "matches_candidate": [value == frozen[CAPTURE_SHA256[1]][row_index]
                                  for value in hashes],
        })
    result = {
        "contract": "m95_boundary_item_fingerprint_v1",
        "manifest_sha256": MANIFEST_SHA256,
        "capture_sha256": list(CAPTURE_SHA256),
        "scope": "Standalone transformed TRAIN items; no full-forward causal attribution",
        "rows": rows,
        "admission": False,
    }
    output = Path(args.output)
    if output.exists():
        raise ValueError("Output already exists")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
