"""Join frozen native outcomes to physical target-minority superpoints."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--dataset-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import numpy as np
    import torch

    if args.output.exists():
        raise ValueError("Output exists")
    source = args.dataset_source.read_text()
    if "gt_spmask = (gt_spmask > 0.5).float()" not in source:
        raise ValueError("Native majority target contract differs")
    capture = json.loads(args.capture.read_text())
    if (capture["contract"] != "m95_final_seed_target_diagnostic_v1"
            or capture["transform_seed"] != 1999 or len(capture["rows"]) != 128
            or capture["checkpoint_sha256"] !=
            "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"):
        raise ValueError("Frozen capture differs")
    grouped = defaultdict(list)
    for row in capture["rows"]:
        grouped[row["scene"]].append(row)
    if len(grouped) != 32 or any(len(v) != 4 for v in grouped.values()):
        raise ValueError("Frozen scene grouping differs")
    output = []
    physical_hashes = {}
    for scene, rows in sorted(grouped.items()):
        path = args.data_root / "scannetv2/train" / (scene + "_refer.pth")
        data = torch.load(path, map_location="cpu", weights_only=False)
        if len(data) != 5:
            raise ValueError("Physical scene schema differs")
        sp = np.asarray(data[2], dtype=np.int64)
        ins = np.asarray(data[4], dtype=np.int64)
        ids = np.unique(sp)
        if not np.array_equal(ids, np.arange(len(ids))):
            raise ValueError("Superpoints noncontiguous")
        counts = np.bincount(sp)
        physical_hashes[scene] = sha(path)
        for row in rows:
            target = [int(x) for x in row["target_instances"]]
            if not target or any((ins == t).sum() == 0 for t in target):
                raise ValueError("Target instance unavailable")
            physical_target = np.isin(ins, target)
            part = np.bincount(sp, weights=physical_target, minlength=len(counts))
            fraction = part / counts
            minority = (part > 0) & (fraction <= 0.5)
            majority = fraction > 0.5
            output.append({
                "scene": scene, "ann_id": int(row["ann_id"]),
                "target_instances": target,
                "target_points": int(physical_target.sum()),
                "target_bearing_rows": int((part > 0).sum()),
                "minority_rows": int(minority.sum()),
                "minority_target_points": int(part[minority].sum()),
                "majority_rows": int(majority.sum()),
                "physical_target_superpoints_capture": int(
                    capture["target_seed_direction_rows"][
                        next(i for i, x in enumerate(capture["rows"])
                             if x["scene"] == scene and
                             int(x["ann_id"]) == int(row["ann_id"]))
                    ]["physical_target_superpoints"]),
                "failed": bool(float(row["selected_mask_iou"]) <= 0.5),
                "selected_iou": float(row["selected_mask_iou"]),
            })
    if len({(r["scene"], r["ann_id"]) for r in output}) != 128:
        raise ValueError("Duplicate identities")
    exposed = [r for r in output if r["minority_rows"]]
    control = [r for r in output if not r["minority_rows"]]
    discordant = []
    for scene, rows in sorted(grouped.items()):
        bound = [r for r in output if r["scene"] == scene]
        a = [r for r in bound if r["minority_rows"]]
        b = [r for r in bound if not r["minority_rows"]]
        if a and b:
            discordant.append({
                "scene": scene, "exposed": len(a), "unexposed": len(b),
                "failure_exposed": sum(r["failed"] for r in a),
                "failure_unexposed": sum(r["failed"] for r in b),
            })
    summary = {
        "expressions": len(output), "scenes": len(grouped),
        "exposed_expressions": len(exposed),
        "exposed_scenes": len({r["scene"] for r in exposed}),
        "exposed_physical_targets": len({
            (r["scene"], tuple(r["target_instances"])) for r in exposed}),
        "minority_rows_repeated": sum(r["minority_rows"] for r in output),
        "minority_target_points_repeated": sum(
            r["minority_target_points"] for r in output),
        "exposed_failures": sum(r["failed"] for r in exposed),
        "unexposed_expressions": len(control),
        "unexposed_failures": sum(r["failed"] for r in control),
        "discordant_scenes": len(discordant),
    }
    result = {
        "contract": "m95_target_minority_outcome_v1", "admission": False,
        "capture_sha256": sha(args.capture),
        "dataset_source_sha256": sha(args.dataset_source),
        "physical_sha256": physical_hashes,
        "summary": summary, "discordant_scenes": discordant, "rows": output,
        "limits": "Frozen TRAIN source diagnostic; no native loss intervention or model efficacy.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
