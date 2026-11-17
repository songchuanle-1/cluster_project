"""Bind physical minority exposure to unchanged M95 selected seed."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--minority", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    m = json.loads(args.minority.read_text())
    c = json.loads(args.capture.read_text())
    if (m["contract"] != "m95_target_minority_outcome_v1"
            or m["capture_sha256"] != sha(args.capture)
            or c["contract"] != "m95_final_seed_target_diagnostic_v1"
            or len(m["rows"]) != 128 or len(c["rows"]) != 128):
        raise ValueError("Frozen source mismatch")
    by_key = {(r["scene"], int(r["ann_id"])): r for r in c["rows"]}
    if len(by_key) != 128:
        raise ValueError("Duplicate native identities")
    rows = []
    for r in m["rows"]:
        key = (r["scene"], int(r["ann_id"]))
        original = by_key.pop(key)
        if (list(map(int, original["target_instances"])) != r["target_instances"]
                or abs(float(original["selected_mask_iou"]) -
                       r["selected_iou"]) > 1e-7):
            raise ValueError("Identity/outcome mismatch")
        rows.append({
            "scene": key[0], "ann_id": key[1],
            "target_instances": r["target_instances"],
            "minority_rows": r["minority_rows"],
            "minority_target_points": r["minority_target_points"],
            "target_bearing_rows": r["target_bearing_rows"],
            "failed": r["failed"],
            "selected_seed_instance": original["selected_seed_instance"],
            "selected_seed_matches_target": original[
                "selected_seed_matches_target_instance"],
            "target_seed_count": next(
                c["target_seed_direction_rows"][i]["target_seed_count"]
                for i, x in enumerate(c["rows"])
                if x["scene"] == key[0] and int(x["ann_id"]) == key[1]),
        })
    if by_key:
        raise ValueError("Missing native identities")
    groups = {}
    for name, subset in (
            ("exposed_failure", [r for r in rows if r["minority_rows"] and r["failed"]]),
            ("exposed_success", [r for r in rows if r["minority_rows"] and not r["failed"]]),
            ("unexposed_failure", [r for r in rows if not r["minority_rows"] and r["failed"]])):
        groups[name] = {
            "expressions": len(subset),
            "scenes": len({r["scene"] for r in subset}),
            "physical_targets": len({(r["scene"], tuple(r["target_instances"]))
                                     for r in subset}),
            "selected_target_seed": sum(bool(r["selected_seed_matches_target"])
                                        for r in subset),
            "zero_target_seed": sum(r["target_seed_count"] == 0 for r in subset),
        }
    result = {
        "contract": "m95_minority_seed_path_v1", "admission": False,
        "minority_sha256": sha(args.minority),
        "capture_sha256": sha(args.capture),
        "groups": groups, "exposed_rows": [r for r in rows if r["minority_rows"]],
        "limits": "Selected TRAIN cohort only; physical seed identity is retrospective and no same-forward causal correction was tested.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(groups, sort_keys=True))


if __name__ == "__main__":
    main()
