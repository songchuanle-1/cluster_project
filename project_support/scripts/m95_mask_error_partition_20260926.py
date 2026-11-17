"""Read-only partition of frozen M95 mask errors on the same support."""
import argparse
import hashlib
import json
from pathlib import Path

CAPTURE_SHA256 = "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"
MANIFEST_SHA256 = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mask_partition(masks, target):
    import torch

    masks = masks.bool()
    target = target.bool()
    intersection = (masks & target).sum(1)
    fp = (masks & ~target).sum(1)
    fn = (~masks & target).sum(1)
    union = intersection + fp + fn
    iou = intersection.float() / union.clamp_min(1)
    best, index = iou.max(0)
    index = int(index)
    common = int(intersection[index])
    false_positive = int(fp[index])
    false_negative = int(fn[index])
    return {
        "query": index,
        "iou": float(best),
        "target_size": int(target.sum()),
        "mask_size": common + false_positive,
        "tp": common,
        "fp": false_positive,
        "fn": false_negative,
        "precision": common / max(1, common + false_positive),
        "recall": common / max(1, common + false_negative),
        "fn_dominant": false_negative > false_positive,
        "fp_dominant": false_positive > false_negative,
    }


def analyze(capture, root):
    import torch

    if (sha256(capture) != CAPTURE_SHA256):
        raise ValueError("Frozen capture hash differs")
    source = json.loads(Path(capture).read_text(encoding="utf-8"))
    rows = source["rows"]
    if (not source["native_capture_completed"] or len(rows) != 256
            or source["manifest"]["sha256"] != MANIFEST_SHA256):
        raise ValueError("Frozen capture contract differs")
    by_index = {int(row["manifest_index"]): row for row in rows}
    if len(by_index) != len(rows):
        raise ValueError("Duplicate manifest index")
    observed = {}
    for entry in source["feature_artifacts"]:
        path = root / entry["path"]
        if sha256(path) != entry["sha256"]:
            raise ValueError("Feature artifact hash differs: " + str(path))
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            row = by_index[index]
            if (index in observed or artifact["manifest_sha256"] != MANIFEST_SHA256
                    or artifact["artifact_contract"] != source["artifact_contract"]
                    or artifact["axis"]["scene"] != row["scene"]
                    or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
                raise ValueError("Artifact identity differs")
            masks, target = artifact["query_masks"], artifact["target_union"]
            if len(masks) != len(row["ious"]) or masks.shape[1] != len(target):
                raise ValueError("Mask support differs")
            part = mask_partition(masks, target)
            if abs(part["iou"] - max(row["ious"])) > 1e-6:
                raise ValueError("Native IoU differs")
            observed[index] = dict(
                manifest_index=index, scene=row["scene"], ann_id=row["ann_id"],
                stratum=row["stratum"], no_acceptable=part["iou"] <= 0.5,
                **part,
            )
    if set(observed) != set(by_index):
        raise ValueError("Incomplete capture coverage")
    limited = [value for value in observed.values() if value["no_acceptable"]]
    covered = [value for value in observed.values() if not value["no_acceptable"]]

    def summary(group):
        return {
            "rows": len(group), "scenes": len({row["scene"] for row in group}),
            "fn_dominant": sum(row["fn_dominant"] for row in group),
            "fp_dominant": sum(row["fp_dominant"] for row in group),
            "tie": sum(row["fp"] == row["fn"] for row in group),
            "zero_overlap": sum(row["tp"] == 0 for row in group),
            "mean_precision": sum(row["precision"] for row in group) / len(group),
            "mean_recall": sum(row["recall"] for row in group) / len(group),
        }

    return {
        "contract": "m95_mask_error_partition_v1",
        "capture_sha256": CAPTURE_SHA256, "manifest_sha256": MANIFEST_SHA256,
        "limited": summary(limited), "covered": summary(covered),
        "limited_rows": limited, "admission": False,
        "interpretation": "Outcome-stratified description only; no causal or deployable mechanism.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output already exists")
    result = analyze(args.capture, args.artifact_root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({"limited": result["limited"], "covered": result["covered"]}))


if __name__ == "__main__":
    main()
