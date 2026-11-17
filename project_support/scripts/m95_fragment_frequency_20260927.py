"""Join frozen M95 fragmentation and support-frequency diagnostics."""
import argparse
import hashlib
import json
from pathlib import Path

FRAGMENT_SHA = "dc9ce208a764bc2406f6093a089cdc65263f69b4ce23706d615a952194b2ea53"
FREQUENCY_SHA = "3822e7f7a682a6ee932b4efccbdcb7616e1b9738d0c025a16de5ad2c44cd008d"


def read(path, expected):
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError(f"Frozen input differs: {path}")
    return json.loads(content)


def analyze(fragment, frequency):
    if fragment["capture_sha256"] != frequency["capture_sha256"]:
        raise ValueError("Capture differs")
    native = {r["manifest_index"]: r for r in frequency["groups"]["limited"]["rows"]}
    if len(native) != 16:
        raise ValueError("Limited population differs")
    groups = {"fragmented": [], "other_limited": []}
    for r in fragment["groups"]["limited"]["rows"]:
        f = native[r["manifest_index"]]
        if (r["scene"], r["ann_id"]) != (f["scene"], f["ann_id"]):
            raise ValueError("Identity differs")
        groups["fragmented" if r["extra_recall"] > 0 else "other_limited"].append({
            "manifest_index": r["manifest_index"], "scene": r["scene"],
            "extra_recall": r["extra_recall"],
            "target_minus_competitor": f["target_minus_competitor"],
            "union_fp": r["union_fp"],
            "best_fp": r["best_fp"],
            "union_precision": r["union_precision"],
        })
    if len(groups["fragmented"]) != 4 or len(groups["other_limited"]) != 12:
        raise ValueError("Frozen split differs")
    return {
        "contract": "m95_fragment_frequency_v1", "admission": False,
        "fragment_sha256": FRAGMENT_SHA, "frequency_sha256": FREQUENCY_SHA,
        "groups": {
            key: {
                "expressions": len(rows),
                "scenes": len({r["scene"] for r in rows}),
                "mean_contrast": sum(r["target_minus_competitor"] for r in rows) / len(rows),
                "mean_union_precision": sum(r["union_precision"] for r in rows) / len(rows),
                "rows": rows,
            } for key, rows in groups.items()
        },
        "limits": "Frozen TRAIN retrospective join, no new causal mechanism or native candidate backward.",
    }


def main():
    p = argparse.ArgumentParser()
    for key in ("fragment", "frequency", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(read(args.fragment, FRAGMENT_SHA), read(args.frequency, FREQUENCY_SHA))
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: {n: v for n, v in g.items() if n != "rows"}
                      for k, g in report["groups"].items()}))


if __name__ == "__main__":
    main()
