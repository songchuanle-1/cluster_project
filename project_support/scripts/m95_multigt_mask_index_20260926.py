"""Count actual frozen ScanRefer exposures to repeated-GT mask indexing."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

CAPTURE_SHA = "9271ea8e5202590e99e3d1e2da1a729ee87262bba8fecf96bd394c7f0abda1cd"
PRODUCER_SHA = "206c594d8c5219c6e249d89f7cb91815467bd443a030bc8bbd76d457de0b485a"


def audit(capture):
    if (capture.get("producer_sha256") != PRODUCER_SHA
            or capture.get("capture_mode") != "full_train_scan"
            or not capture.get("native_match_cause_completed")):
        raise ValueError("Native capture contract differs")
    rows = []
    for item in capture["rows"]:
        cause = item["native_match_cause"]
        object_ids = list(map(int, cause["object_ids"]))
        pairs = [tuple(map(int, pair)) for pair in cause["matched_query_gt_pairs"]]
        if (not object_ids or object_ids != list(map(int, item["target_instances"]))
                or len({q for q, _ in pairs}) != len(pairs)
                or any(gt < 0 or gt >= len(object_ids) for _, gt in pairs)):
            raise ValueError("Matcher GT axis differs")
        matched = {q for q, _ in pairs}
        positives = {q for q, value in enumerate(cause["native_positive"]) if value}
        if matched != positives:
            raise ValueError("Matcher positive axis differs")
        counts = Counter(gt for _, gt in pairs)
        expanded = [gt for gt in range(len(object_ids))
                    for _ in range(counts[gt])]
        affected = [q for q, gt in pairs if expanded[gt] != gt]
        rows.append({
            "manifest_index": int(item["manifest_index"]),
            "scene": item["scene"], "ann_id": int(item["ann_id"]),
            "stratum": item["stratum"],
            "failed": float(item["ious"][int(item["selected_query"])]) <= 0.5,
            "gt_count": len(object_ids), "match_counts": [counts[gt] for gt in range(len(object_ids))],
            "affected_queries": affected, "exposed": bool(affected),
        })
    rows.sort(key=lambda x: x["manifest_index"])
    if len(rows) != 256 or [r["manifest_index"] for r in rows] != list(range(256)):
        raise ValueError("Frozen manifest incomplete")

    def tally(group):
        return {
            "rows": len(group), "scenes": len({r["scene"] for r in group}),
            "failures": sum(r["failed"] for r in group),
            "multi_gt": sum(r["gt_count"] > 1 for r in group),
            "affected": sum(r["exposed"] for r in group),
            "affected_failures": sum(r["failed"] and r["exposed"] for r in group),
            "affected_queries": sum(len(r["affected_queries"]) for r in group),
        }
    pairs = [(a, b) for i, a in enumerate(rows) for b in rows[i + 1:]
             if a["scene"] == b["scene"] and a["stratum"] == b["stratum"]
             and a["exposed"] != b["exposed"]]
    return {
        "contract": "m95_multigt_mask_index_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA,
        "summary": {
            "all": tally(rows),
            "ambiguous": tally([r for r in rows if r["stratum"] == "ambiguous"]),
            "class_unique": tally([r for r in rows if r["stratum"] == "class_unique"]),
            "same_scene_discordant_pairs": len(pairs),
        },
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or hashlib.sha256(args.capture.read_bytes()).hexdigest() != CAPTURE_SHA:
        raise ValueError("Output exists or native capture differs")
    result = audit(json.loads(args.capture.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
