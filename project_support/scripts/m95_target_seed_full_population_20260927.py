"""Screen full native M95 capture for same-target seed/mask error controls."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


CAPTURE_SHA = "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"
PRODUCER_SHA = "206c594d8c5219c6e249d89f7cb91815467bd443a030bc8bbd76d457de0b485a"
CHECKPOINT_SHA = "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"


def analyze(capture):
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"):
        raise ValueError("Frozen native capture provenance differs")
    rows = capture["rows"]
    if (len(rows) != 256
            or sorted(r["manifest_index"] for r in rows) != list(range(256))):
        raise ValueError("Frozen manifest population differs")
    groups = defaultdict(list)
    for row in rows:
        selected = row["selected_query"]
        if (not 0 <= selected < 128 or len(row["sampled_seed_indices"]) != 128
                or len(row["ious"]) != 128):
            raise ValueError("Selected query/IoU axis differs")
        seed_index = row["sampled_seed_indices"][selected]
        fps = row["fps_superpoints"]
        labels = row["physical_instance_labels"]
        if not 0 <= seed_index < len(fps) or not 0 <= fps[seed_index] < len(labels):
            raise ValueError("Selected seed superpoint axis differs")
        physical_seed = labels[fps[seed_index]]
        target = tuple(sorted(row["target_instances"]))
        if not target or not 0 <= row["ious"][selected] <= 1:
            raise ValueError("Target or native mask IoU differs")
        groups[row["scene"]].append({
            "scene": row["scene"], "manifest_index": row["manifest_index"],
            "ann_id": row["ann_id"],
            "target_instances": target, "physical_seed_instance": physical_seed,
            "target_seed": physical_seed in target,
            "selected_iou": row["ious"][selected],
        })
    failures = []
    for scene, scene_rows in groups.items():
        for row in scene_rows:
            if not row["target_seed"] or row["selected_iou"] > 0.5:
                continue
            controls = [other for other in scene_rows
                        if other["target_seed"] and other["selected_iou"] > 0.5]
            matched = [other for other in controls
                       if other["target_instances"] == row["target_instances"]]
            failures.append({
                **row,
                "same_scene_success_controls": len(controls),
                "same_target_success_controls": [
                    {"manifest_index": c["manifest_index"], "ann_id": c["ann_id"],
                     "selected_iou": c["selected_iou"]}
                    for c in matched],
            })
    return {
        "contract": "m95_target_seed_full_population_v1",
        "admission": False,
        "capture_sha256": CAPTURE_SHA,
        "population": {"expressions": 256, "scenes": len(groups)},
        "target_seed_failures": len(failures),
        "failure_scenes": len({r["scene"] for r in failures}),
        "failures_with_same_scene_control": sum(
            r["same_scene_success_controls"] > 0 for r in failures),
        "failures_with_same_target_control": sum(
            bool(r["same_target_success_controls"]) for r in failures),
        "same_target_paired_scenes": len({
            r["scene"] for r in failures if r["same_target_success_controls"]}),
        "failure_rows": sorted(failures, key=lambda r: r["manifest_index"]),
        "limits": "Frozen TRAIN observational screen; not an intervention, independence or efficacy gate.",
    }


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or sha(args.capture) != CAPTURE_SHA:
        raise ValueError("Output exists or frozen capture differs")
    result = analyze(json.loads(args.capture.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "failure_rows"}))


if __name__ == "__main__":
    main()
