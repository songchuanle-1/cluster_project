"""Bound physical seed-context upper bound to native-negative endpoint classes."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

SCREEN_SHA = "ffb8a804824f200f745e8835685aac9f5a469c3758bc430df4aa637d5ad888bf"
PARTITION_SHA = "5a277d507c27208e6703152af914f6b0e16d6ea40c4f6be6f03323d1181bff18"


def analyze(screen, partition):
    if (screen.get("contract") != "m95_wrong_seed_context_v1"
            or partition.get("contract") != "m95_negative_intrusion_partition_v1"):
        raise ValueError("Source contracts differ")
    rows = {int(row["manifest_index"]): row for row in screen["rows"]}
    if len(rows) != 256 or sorted(rows) != list(range(256)):
        raise ValueError("Physical screen incomplete")
    seen = set()
    joined = []
    for item in partition["summary"]["mismatch_rows"]:
        index = int(item["manifest_index"])
        if index in seen or index not in rows or item["scene_id"] != rows[index]["scene"]:
            raise ValueError("Endpoint/seed identity differs")
        seen.add(index)
        row = rows[index]
        joined.append({
            "manifest_index": index, "scene": row["scene"],
            "stratum": row["stratum"], "category": item["category"],
            "failed": row["failed"], "exposed": row["selected_exposed"],
            "unresolved": row["selected_unresolved"],
        })
    if len(seen) != 49:
        raise ValueError("Native-negative mismatch denominator differs")
    def tally(group):
        return {"rows": len(group), "scenes": len({r["scene"] for r in group}),
                "failures": sum(r["failed"] for r in group),
                "exposed": sum(r["exposed"] for r in group),
                "exposed_failures": sum(r["exposed"] and r["failed"] for r in group),
                "unresolved": sum(r["unresolved"] for r in group)}
    groups = {key: tally([r for r in joined if r["category"] == key])
              for key in ("wrong_instance", "neither_target_nor_wrong_instance",
                          "target_false_negative")}
    groups["all_native_negative"] = tally(joined)
    groups["outside_native_negative"] = tally([
        {"scene": row["scene"], "failed": row["failed"],
         "exposed": row["selected_exposed"],
         "unresolved": row["selected_unresolved"]}
        for index, row in rows.items() if index not in seen])
    return {"contract": "m95_wrong_seed_context_control_v1",
            "admission": False, "screen_sha256": SCREEN_SHA,
            "partition_sha256": PARTITION_SHA,
            "summary": groups, "rows": sorted(joined, key=lambda r: r["manifest_index"])}


def main():
    p = argparse.ArgumentParser()
    for key in ("screen", "partition", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or any(
        hashlib.sha256(path.read_bytes()).hexdigest() != expected
        for path, expected in ((args.screen, SCREEN_SHA),
                               (args.partition, PARTITION_SHA))
    ):
        raise ValueError("Input hash differs or output exists")
    result = analyze(json.loads(args.screen.read_text(encoding="utf-8")),
                     json.loads(args.partition.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
