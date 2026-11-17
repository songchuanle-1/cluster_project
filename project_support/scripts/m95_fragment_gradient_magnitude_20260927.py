"""Join frozen support fragmentation with native mask source gradients."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path

FRAGMENT_SHA = "dc9ce208a764bc2406f6093a089cdc65263f69b4ce23706d615a952194b2ea53"
GRADIENT_SHA = "c88bdc19dc74255940c8da90ff3b6de9a343c7fcc4d81c48a1b6c16c2ef2e3ef"


def read_bound(path, expected):
    content = path.read_bytes()
    actual = hashlib.sha256(content).hexdigest()
    if actual != expected:
        raise ValueError(f"Source hash mismatch: {path}: {actual}")
    return json.loads(content)


def summarize(rows):
    if not rows:
        raise ValueError("Empty cohort")
    return {
        "expressions": len(rows),
        "scenes": len({r["scene"] for r in rows}),
        "median_target_feature_grad_norm": statistics.median(
            r["target_feature_grad_norm"] for r in rows),
        "median_query_grad_norm": statistics.median(
            r["query_grad_norm"] for r in rows),
        "median_native_loss": statistics.median(r["loss"] for r in rows),
        "rows": rows,
    }


def analyze(fragment, gradients):
    if fragment["capture_sha256"] != gradients["capture_sha256"]:
        raise ValueError("Capture identity mismatch")
    native = {}
    for key in ("limited", "size_matched_controls"):
        for row in gradients[key]["rows"]:
            idx = row["manifest_index"]
            if idx in native:
                raise ValueError("Duplicate index")
            native[idx] = row
    limited = fragment["groups"]["limited"]["rows"]
    if len(limited) != 16 or len(native) != 32:
        raise ValueError("Frozen cohort size mismatch")
    groups = {"fragmented": [], "other_limited": [], "covered_controls": []}
    for row in limited:
        n = native.pop(row["manifest_index"])
        if n["scene"] != row["scene"]:
            raise ValueError("Scene mismatch")
        key = "fragmented" if row["extra_recall"] > 0 else "other_limited"
        groups[key].append(n)
    groups["covered_controls"] = list(native.values())
    if [len(groups[k]) for k in groups] != [4, 12, 16]:
        raise ValueError("Frozen strata changed")
    return {
        "contract": "m95_fragment_gradient_magnitude_v1",
        "admission": False,
        "capture_sha256": fragment["capture_sha256"],
        "fragment_sha256": FRAGMENT_SHA,
        "gradient_sha256": GRADIENT_SHA,
        "groups": {key: summarize(rows) for key, rows in groups.items()},
        "limits": "TRAIN retrospective source gradients, not causal candidate backward, optimizer effect, or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("fragment", "gradients", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(read_bound(args.fragment, FRAGMENT_SHA),
                     read_bound(args.gradients, GRADIENT_SHA))
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({k: {n: v for n, v in g.items() if n != "rows"}
                      for k, g in report["groups"].items()}))


if __name__ == "__main__":
    main()
