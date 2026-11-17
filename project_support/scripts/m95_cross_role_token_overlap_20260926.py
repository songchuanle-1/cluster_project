"""Audit contradictory target-positive/other-negative token supports."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

TOKEN_SHA = "f149aa2c4f0c64ff8ef6f8d8f18782a16493aa5a9f48bec097e4caa01cbdee21"


def support(spans, role, kind):
    positions = set()
    for span in spans:
        if span["role"] == role and span["kind"] == kind and span["mapped"]:
            start, end = span["token_positions"]
            positions.update(range(start, end + 1))
    return positions


def analyze(receipt):
    rows = []
    for item in receipt["rows"]:
        spans = item["spans"]
        other = support(spans, "other", "target_char_span")
        noun = support(spans, "target", "target_char_span")
        fields = {
            "noun": noun,
            "modifier": support(spans, "target", "mod_char_span"),
            "pronoun": support(spans, "target", "pron_char_span"),
            "relation": support(spans, "target", "rel_char_span"),
        }
        overlaps = {key: sorted(other & value) for key, value in fields.items()}
        rows.append({
            "manifest_index": item["manifest_index"], "scene": item["scene"],
            "ann_id": item["ann_id"], "stratum": item["stratum"],
            "failed": item["failed"], "unresolved": not noun,
            "other_span_count": sum(s["role"] == "other" for s in spans),
            "other_token_count": len(other),
            "noun_token_count": len(noun),
            "overlaps": overlaps,
            "exposed": bool(overlaps["noun"]),
            "target_role_overlap": sorted(
                (fields["noun"] & fields["modifier"]) |
                (fields["noun"] & fields["pronoun"]) |
                (fields["noun"] & fields["relation"])),
        })
    rows.sort(key=lambda row: row["manifest_index"])
    if len(rows) != 256 or [r["manifest_index"] for r in rows] != list(range(256)):
        raise ValueError("Frozen tokenizer receipt incomplete")

    def tally(items):
        return {"rows": len(items), "scenes": len({r["scene"] for r in items}),
                "failures": sum(r["failed"] for r in items),
                "unresolved": sum(r["unresolved"] for r in items),
                "has_other": sum(bool(r["other_token_count"]) for r in items),
                "primary_overlap": sum(r["exposed"] for r in items),
                "primary_overlap_failures": sum(r["exposed"] and r["failed"] for r in items),
                "modifier_overlap": sum(bool(r["overlaps"]["modifier"]) for r in items),
                "pronoun_overlap": sum(bool(r["overlaps"]["pronoun"]) for r in items),
                "relation_overlap": sum(bool(r["overlaps"]["relation"]) for r in items),
                "target_role_overlap": sum(bool(r["target_role_overlap"]) for r in items)}

    scenes = defaultdict(list)
    for row in rows:
        if not row["unresolved"]:
            scenes[(row["scene"], row["stratum"])].append(row)
    pairs = [(a, b) for group in scenes.values() for i, a in enumerate(group)
             for b in group[i + 1:] if a["exposed"] != b["exposed"]]
    return {
        "contract": "m95_cross_role_token_overlap_v1", "admission": False,
        "token_receipt_sha256": TOKEN_SHA,
        "source_sha256": receipt["source_sha256"],
        "graph_sha256": receipt["graph_sha256"],
        "capture_sha256": receipt["capture_sha256"],
        "summary": {
            "all": tally(rows),
            "ambiguous": tally([r for r in rows if r["stratum"] == "ambiguous"]),
            "class_unique": tally([r for r in rows if r["stratum"] == "class_unique"]),
            "same_scene_discordant_pairs": len(pairs),
            "same_scene_exposed_failures": sum(
                a["failed"] if a["exposed"] else b["failed"] for a, b in pairs),
            "same_scene_control_failures": sum(
                b["failed"] if a["exposed"] else a["failed"] for a, b in pairs),
        }, "rows": rows,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or hashlib.sha256(args.receipt.read_bytes()).hexdigest() != TOKEN_SHA:
        raise ValueError("Output exists or native tokenizer receipt hash differs")
    result = analyze(json.loads(args.receipt.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
