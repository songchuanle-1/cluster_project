"""Attribute frozen target-blind predicted peers after native capture."""
import argparse
import hashlib
import json
from pathlib import Path

from m95_group_predicted_peer_20260926 import pair_geometry


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyze(capture):
    import numpy as np

    if capture.get("contract") != "m95_group_predicted_peer_v1":
        raise ValueError("Wrong native capture contract")
    rows, units = [], set()
    for row in capture["rows"]:
        unit = row["cohort"], row["scene"], str(row["target"])
        if unit in units:
            raise ValueError("Repeated scene-target unit")
        units.add(unit)
        masks = np.asarray(row["masks"], dtype=bool)
        target = np.asarray(row["target_mask"], dtype=bool)
        if masks.ndim != 2 or target.shape != (masks.shape[1],):
            raise ValueError("Native mask support differs")
        geometry = pair_geometry(masks, row["xyz"])
        if (geometry["true"] != {int(k): v for k, v in row["true_peer"].items()}
                or geometry["shuffled"] != {
                    int(k): v for k, v in row["shuffled_peer"].items()}):
            raise ValueError("Target-blind pair replay differs")
        if len(row["physical_labels"]) != len(target):
            raise ValueError("Physical-label support differs")
        labels = np.asarray(row["physical_labels"], dtype=int)
        target_id = int(row["target"])
        if not np.any(labels == target_id):
            raise ValueError("Target instance absent from native support")
        if not row["same_name_peer_ids"] or target_id in row["same_name_peer_ids"]:
            raise ValueError("Same-name peer identity differs")
        true, shuffled = geometry["true"], geometry["shuffled"]
        covered = []
        for i, mask in enumerate(masks):
            intersection = np.logical_and(mask, target).sum()
            union = np.logical_or(mask, target).sum()
            if union and intersection * 2 > union:
                covered.append(i)
        votes = []
        for i in covered:
            if i not in true:
                continue
            center = geometry["centers"][i]
            expected = row["cohort"] == "lower"
            true_z = geometry["centers"][true[i]][2]
            shuffled_z = geometry["centers"][shuffled[i]][2]

            def physical_peer(query):
                members = labels[masks[query]]
                if not len(members):
                    raise ValueError("Empty attributed peer mask")
                ids, counts = np.unique(members[members >= 0],
                                        return_counts=True)
                if not len(ids):
                    return None
                winner = int(ids[np.argmax(counts)])
                return winner if counts.max() * 2 > len(members) else None

            true_instance = physical_peer(true[i])
            shuffled_instance = physical_peer(shuffled[i])
            votes.append({
                "query": i, "true_peer": true[i],
                "shuffled_peer": shuffled[i],
                "true_sign": center[2] < true_z if expected else center[2] > true_z,
                "shuffled_sign": center[2] < shuffled_z if expected
                else center[2] > shuffled_z,
                "control_changed": true[i] != shuffled[i],
                "true_peer_instance": true_instance,
                "shuffled_peer_instance": shuffled_instance,
                "true_distinct_same_name": true_instance in row["same_name_peer_ids"],
                "shuffled_distinct_same_name": shuffled_instance in row["same_name_peer_ids"],
            })
        rows.append({
            "cohort": row["cohort"], "scene": row["scene"],
            "ann_id": row["ann_id"], "target": row["target"],
            "target_covered_queries": covered, "eligible_votes": votes,
            "true_positive_votes": sum(v["true_sign"] for v in votes),
            "shuffled_positive_votes": sum(v["shuffled_sign"] for v in votes),
            "mixed_true": bool(votes) and 0 < sum(
                v["true_sign"] for v in votes) < len(votes),
            "control_changed_votes": sum(v["control_changed"] for v in votes),
            "true_same_name_votes": sum(
                v["true_distinct_same_name"] for v in votes),
            "shuffled_same_name_votes": sum(
                v["shuffled_distinct_same_name"] for v in votes),
            "true_bound_sign_votes": sum(
                v["true_sign"] and v["true_distinct_same_name"] for v in votes),
            "shuffled_bound_sign_votes": sum(
                v["shuffled_sign"] and v["shuffled_distinct_same_name"]
                for v in votes),
        })
    summary = {}
    for cohort in ("lower", "upper"):
        selected = [r for r in rows if r["cohort"] == cohort]
        summary[cohort] = {
            "units": len(selected),
            "target_covered": sum(bool(r["target_covered_queries"]) for r in selected),
            "pair_covered": sum(bool(r["eligible_votes"]) for r in selected),
            "true_positive_units": sum(
                r["true_positive_votes"] * 2 > len(r["eligible_votes"])
                for r in selected if r["eligible_votes"]),
            "shuffled_positive_units": sum(
                r["shuffled_positive_votes"] * 2 > len(r["eligible_votes"])
                for r in selected if r["eligible_votes"]),
            "mixed_true_units": sum(r["mixed_true"] for r in selected),
            "true_positive_votes": sum(r["true_positive_votes"] for r in selected),
            "shuffled_positive_votes": sum(
                r["shuffled_positive_votes"] for r in selected),
            "eligible_votes": sum(len(r["eligible_votes"]) for r in selected),
            "control_changed_votes": sum(
                r["control_changed_votes"] for r in selected),
            "true_same_name_votes": sum(
                r["true_same_name_votes"] for r in selected),
            "shuffled_same_name_votes": sum(
                r["shuffled_same_name_votes"] for r in selected),
            "true_bound_sign_votes": sum(
                r["true_bound_sign_votes"] for r in selected),
            "shuffled_bound_sign_votes": sum(
                r["shuffled_bound_sign_votes"] for r in selected),
        }
    return {"contract": "m95_group_predicted_peer_analysis_v1",
            "admission": False, "summary": summary, "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or digest(args.capture) != args.expected_sha256:
        raise ValueError("Output exists or frozen capture hash differs")
    result = analyze(json.loads(args.capture.read_text(encoding="ascii")))
    result["capture_sha256"] = args.expected_sha256
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
