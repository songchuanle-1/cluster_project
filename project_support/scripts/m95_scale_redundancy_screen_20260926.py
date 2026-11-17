"""Fixed TRAIN cross-scale redundancy screen, read-only."""
import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

SOURCE_SHA = "fb330f24710a12b3aecb244c0a58246ec455b39495f95acaadb2cd6138c1b342"


def key(row):
    return int(row["step"]), str(row["scene"]), int(row["expression_slot"])


def unique(rows):
    result = {}
    for row in rows:
        identity = key(row)
        if identity in result:
            raise ValueError("Duplicate expression identity")
        result[identity] = row
    return result


def mean(values):
    return sum(values) / len(values) if values else None


def finite(value):
    if value is None:
        return None
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Nonfinite cosine")
    return value


def screen(source):
    records = {branch: unique(source["records"][branch])
               for branch in ("base", "drop_l0", "drop_l1", "drop_l2")}
    duplication = unique(source["duplication"])
    identities = set(records["base"])
    if len(identities) != 123 or any(
        set(rows) != identities for rows in (*records.values(), duplication)
    ):
        raise ValueError("Frozen branch identity differs")
    rows = []
    for identity in sorted(identities):
        base = records["base"][identity]
        duplicate = duplication[identity]
        failed = float(base["selected_iou"]) <= 0.5
        rows.append({
            "step": identity[0], "scene": identity[1],
            "expression_slot": identity[2], "failed": failed,
            "base_iou": float(base["selected_iou"]),
            "cos_l0_l1": finite(duplicate["cos_l0_l1"]),
            "cos_l0_l2": finite(duplicate["cos_l0_l2"]),
            "cos_l1_l2": finite(duplicate["cos_l1_l2"]),
            **{branch + "_delta": float(records[branch][identity]["selected_iou"])
               - float(base["selected_iou"])
               for branch in ("drop_l0", "drop_l1", "drop_l2")},
        })
    grouped = defaultdict(lambda: {True: [], False: []})
    for row in rows:
        grouped[row["scene"]][row["failed"]].append(row)
    metrics = ("cos_l0_l1", "cos_l0_l2", "cos_l1_l2")
    paired = {}
    for metric in metrics:
        paired[metric] = [
            mean([r[metric] for r in outcome[True] if r[metric] is not None])
            - mean([r[metric] for r in outcome[False] if r[metric] is not None])
            for outcome in grouped.values()
            if any(r[metric] is not None for r in outcome[True])
            and any(r[metric] is not None for r in outcome[False])
        ]
    summary = {
        "expressions": len(rows), "scenes": len(grouped),
        "failures": sum(r["failed"] for r in rows),
        "paired_scenes": {metric: len(paired[metric]) for metric in metrics},
        "observed": {
            metric: {
                label: sum(r[metric] is not None for r in rows
                           if r["failed"] == failed)
                for label, failed in (("failed", True), ("success", False))
            } for metric in metrics
        },
        "failure_minus_success": {
            metric: (
                mean([r[metric] for r in rows
                      if r["failed"] and r[metric] is not None])
                - mean([r[metric] for r in rows
                        if not r["failed"] and r[metric] is not None]))
            if all(any(r[metric] is not None for r in rows
                       if r["failed"] == failed) for failed in (True, False))
            else None
            for metric in metrics
        },
        "paired_failure_minus_success": {
            metric: mean(paired[metric]) for metric in metrics
        },
        "absolute_drop_delta": {
            branch: {
                label: mean([abs(r[branch + "_delta"]) for r in rows
                             if r["failed"] == failed])
                for label, failed in (("failed", True), ("success", False))
            } for branch in ("drop_l0", "drop_l1", "drop_l2")
        },
    }
    return {"contract": "m95_scale_redundancy_screen_v1",
            "admission": False, "source_sha256": SOURCE_SHA,
            "summary": summary, "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or hashlib.sha256(
        args.source.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError("Output exists or source hash differs")
    result = screen(json.loads(args.source.read_text(encoding="utf-8")))
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
