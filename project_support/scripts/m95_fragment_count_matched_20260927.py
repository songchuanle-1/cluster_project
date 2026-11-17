"""Control frozen fragmented gradient comparison at fixed positive count."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path

INPUT_SHA = "33779b4305f84ed9e29f7a4d6049d84e5dc9eecc91d7885e28b3814b51a73a0a"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    source = args.input.read_bytes()
    if hashlib.sha256(source).hexdigest() != INPUT_SHA:
        raise ValueError("Frozen source differs")
    data = json.loads(source)
    groups = {}
    for key in ("fragmented", "other_limited"):
        rows = [r for r in data["groups"][key]["rows"] if r["matched_queries"] == 2]
        if len(rows) < 2:
            raise ValueError("Not enough matched positives")
        groups[key] = {
            "expressions": len(rows),
            "scenes": len({r["scene"] for r in rows}),
            "median_query_grad_norm": statistics.median(r["query_grad_norm"] for r in rows),
            "median_target_feature_grad_norm": statistics.median(
                r["target_feature_grad_norm"] for r in rows),
            "median_native_loss": statistics.median(r["loss"] for r in rows),
            "rows": [{"manifest_index": r["manifest_index"], "scene": r["scene"],
                      "query_grad_norm": r["query_grad_norm"],
                      "target_feature_grad_norm": r["target_feature_grad_norm"],
                      "loss": r["loss"]} for r in rows],
        }
    report = {
        "contract": "m95_fragment_count_matched_v1", "admission": False,
        "source_sha256": INPUT_SHA, "matched_positive_queries": 2,
        "groups": groups,
        "limits": "Sparse retrospective TRAIN control; not a native intervention or candidate gate.",
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({k: {field: value for field, value in v.items()
                          if field != "rows"} for k, v in groups.items()}))


if __name__ == "__main__":
    main()
