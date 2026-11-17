"""Read-only proposal-seed coverage audit for the frozen M95 group screen."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect(capture, screen):
    native = {int(r["manifest_index"]): r for r in capture["rows"]}
    if len(native) != 256 or len(capture["rows"]) != 256:
        raise ValueError("Expected exactly 256 native rows")
    rows = []
    for item in screen["exposed_descriptions"]:
        index = int(item["manifest_index"])
        row = native[index]
        if row["scene"] != item["scene"] or int(row["ann_id"]) != int(
            item.get("ann_id", row["ann_id"])
        ):
            raise ValueError("Manifest identity mismatch")
        contract = row["native_match_cause"]
        pos = contract["sampled_pos"]
        labels = contract["sampled_instance_labels"]
        if len(pos) != 128 or len(labels) != 128:
            raise ValueError("Expected 128 query seeds")
        target = int(row["target_object_id"])
        on_target = [i for i, label in enumerate(labels) if int(label) == target]
        other = [i for i, label in enumerate(labels) if int(label) >= 0
                 and int(label) != target]
        description = item["description"].lower()
        # Only the explicit referent-bound lower examples of the first screen
        # are assessed; other uses remain visible without assigning a sign.
        lower = index in (38, 88, 108)
        neighbors = []
        for i in on_target:
            if not other:
                break
            j = min(other, key=lambda n: (
                (pos[i][0] - pos[n][0]) ** 2 +
                (pos[i][1] - pos[n][1]) ** 2, n))
            neighbors.append({
                "query": i, "neighbor_query": j,
                "neighbor_instance": int(labels[j]),
                "lower": bool(pos[i][2] < pos[j][2]),
                "upper": bool(pos[i][2] > pos[j][2]),
            })
        rows.append({
            "manifest_index": index, "scene": row["scene"],
            "ann_id": int(row["ann_id"]), "target": target,
            "description": description,
            "target_bound_lower": lower, "target_seeds": len(on_target),
            "other_instance_seeds": len(other),
            "lower_votes": sum(n["lower"] for n in neighbors),
            "upper_votes": sum(n["upper"] for n in neighbors),
            "neighbors": neighbors,
            "selected_query": int(row["selected_query"]),
            "selected_seed_on_target": int(row["selected_query"]) in on_target,
        })
    return {
        "rows": rows,
        "summary": {
            "group_rows": len(rows),
            "target_covered": sum(r["target_seeds"] > 0 for r in rows),
            "lower_bound_rows": sum(r["target_bound_lower"] for r in rows),
            "lower_bound_covered": sum(
                r["target_bound_lower"] and r["target_seeds"] > 0 for r in rows),
            "lower_unanimous": sum(
                r["target_bound_lower"] and r["target_seeds"] > 0
                and r["lower_votes"] == r["target_seeds"] for r in rows),
            "lower_mixed": sum(
                r["target_bound_lower"] and 0 < r["lower_votes"] <
                r["target_seeds"] for r in rows),
        },
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--capture", type=Path, required=True)
    p.add_argument("--screen", type=Path, required=True)
    p.add_argument("--capture-sha", required=True)
    p.add_argument("--screen-sha", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    if sha(a.capture) != a.capture_sha or sha(a.screen) != a.screen_sha:
        raise ValueError("Frozen input differs")
    result = inspect(json.loads(a.capture.read_text(encoding="utf-8")),
                     json.loads(a.screen.read_text(encoding="utf-8")))
    result.update({"contract": "m95_group_query_seed_v1", "admission": False,
                   "capture_sha256": a.capture_sha,
                   "screen_sha256": a.screen_sha})
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
