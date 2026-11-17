"""Read-only upper bound for composing two native M95 query masks."""
import argparse
import hashlib
import json
from pathlib import Path


CAPTURE_SHA256 = "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"
MANIFEST_SHA256 = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pair_bound(masks, target):
    import torch

    masks = masks.bool()
    target = target.bool()
    intersections = (masks & target).sum(1)
    unions = (masks | target).sum(1).clamp_min(1)
    single = intersections.float() / unions
    best_single, single_index = single.max(0)
    best_pair = best_single
    pair = None
    for i in range(len(masks)):
        combined = masks | masks[i]
        iou = (combined & target).sum(1).float() / (
            combined | target
        ).sum(1).clamp_min(1)
        if i + 1 == len(masks):
            continue
        value, j = iou[i + 1:].max(0)
        if value > best_pair:
            best_pair = value
            pair = [i, i + 1 + int(j)]
    return float(best_single), int(single_index), float(best_pair), pair


def analyze(capture, artifact_root):
    import torch

    rows = capture["rows"]
    if (len(rows) != 256 or not capture["native_capture_completed"]
            or capture["manifest"]["sha256"] != MANIFEST_SHA256):
        raise ValueError("Frozen full-capture contract differs")
    expected = {int(r["manifest_index"]): r for r in rows}
    if len(expected) != 256:
        raise ValueError("Duplicate or missing manifest rows")
    results = {}
    for entry in capture["feature_artifacts"]:
        path = artifact_root / entry["path"]
        if sha256(path) != entry["sha256"]:
            raise ValueError("Artifact hash differs: " + str(path))
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            row = expected[index]
            if (index in results or artifact["manifest_sha256"] != MANIFEST_SHA256
                    or artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["axis"]["scene"] != row["scene"]
                    or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
                raise ValueError("Artifact/row binding differs")
            masks, target = artifact["query_masks"], artifact["target_union"]
            if len(masks) != len(row["ious"]) or masks.shape[1] != len(target):
                raise ValueError("Mask axis differs")
            best, single, pair_best, pair = pair_bound(masks, target)
            if abs(best - max(row["ious"])) > 1e-6:
                raise ValueError("Native single-query IoU differs")
            results[index] = {
                "scene": row["scene"], "ann_id": row["ann_id"],
                "stratum": row["stratum"], "best_single": best,
                "best_single_query": single, "best_pair": pair_best,
                "pair": pair, "delta": pair_best - best,
                "no_acceptable": best <= 0.5,
                "pair_rescue": best <= 0.5 and pair_best > 0.5,
            }
    if set(results) != set(expected):
        raise ValueError("Incomplete artifact coverage")
    limited = [r for r in results.values() if r["no_acceptable"]]
    covered = [r for r in results.values() if not r["no_acceptable"]]
    return {
        "contract": "m95_pair_union_oracle_bound_v1",
        "source_capture_sha256": CAPTURE_SHA256,
        "manifest_sha256": MANIFEST_SHA256,
        "rows": len(results), "no_acceptable": len(limited),
        "pair_rescues": sum(r["pair_rescue"] for r in limited),
        "covered_rows": len(covered),
        "covered_pair_improved": sum(r["delta"] > 1e-6 for r in covered),
        "limited_pair_improved": sum(r["delta"] > 1e-6 for r in limited),
        "limited_rows": [
            dict(manifest_index=i, **r) for i, r in sorted(results.items())
            if r["no_acceptable"]
        ],
        "admission": False,
        "interpretation": "Oracle pair upper bound only; no deployable selector or causal mechanism.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if sha256(args.capture) != CAPTURE_SHA256:
        raise ValueError("Frozen capture SHA256 differs")
    if args.output.exists():
        raise ValueError("Output already exists")
    capture = json.loads(args.capture.read_text(encoding="utf-8"))
    result = analyze(capture, args.artifact_root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({key: result[key] for key in
                      ("rows", "no_acceptable", "pair_rescues", "admission")}))


if __name__ == "__main__":
    main()
