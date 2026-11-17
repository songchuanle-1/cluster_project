"""Frozen query-positive count and selected mask-source gradient audit."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path

INPUT_SHA = "33779b4305f84ed9e29f7a4d6049d84e5dc9eecc91d7885e28b3814b51a73a0a"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    content = args.input.read_bytes()
    if hashlib.sha256(content).hexdigest() != INPUT_SHA:
        raise ValueError("Frozen input differs")
    data = json.loads(content)
    groups = {}
    for key in ("fragmented", "other_limited"):
        rows = data["groups"][key]["rows"]
        if len(rows) != (4 if key == "fragmented" else 12):
            raise ValueError("Frozen stratum differs")
        groups[key] = {
            "expressions": len(rows),
            "scenes": len({r["scene"] for r in rows}),
            "median_positive_queries": statistics.median(
                r["matched_queries"] for r in rows),
            "median_raw_selected_query_gradient": statistics.median(
                r["query_grad_norm"] for r in rows),
            "median_count_corrected_selected_query_gradient": statistics.median(
                r["query_grad_norm"] * r["matched_queries"] for r in rows),
            "rows": [{"manifest_index": r["manifest_index"],
                      "scene": r["scene"],
                      "matched_queries": r["matched_queries"],
                      "raw": r["query_grad_norm"],
                      "count_corrected": r["query_grad_norm"] * r["matched_queries"]}
                     for r in rows],
        }
    report = {
        "contract": "m95_fragment_gradient_dilution_v1",
        "admission": False, "source_sha256": INPUT_SHA, "groups": groups,
        "limits": "Retrospective TRAIN observation, not a causal normalization intervention.",
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({k: {field: value for field, value in v.items()
                          if field != "rows"} for k, v in groups.items()}))


if __name__ == "__main__":
    main()
