"""Join preregistered fragmented-mask rows to frozen native loss signs."""
import argparse
import hashlib
import json
from pathlib import Path

FRAGMENT_SHA = "dc9ce208a764bc2406f6093a089cdc65263f69b4ce23706d615a952194b2ea53"
LOSS_SHA = "a81b30f58c039cf52bc26c00e345408113c96a935fd0290a7502e799f5a0c7ce"


def read(path, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Frozen source differs: {path}")
    return json.loads(data)


def analyze(fragment, loss):
    if fragment["capture_sha256"] != loss["capture_sha256"]:
        raise ValueError("Capture identity differs")
    limited = fragment["groups"]["limited"]["rows"]
    native = {r["manifest_index"]: r for r in loss["rows"]}
    if len(limited) != 16 or len(native) != 16:
        raise ValueError("Limited population differs")
    groups = {}
    for name, selector in (("fragmented", lambda r: r["extra_recall"] > 0),
                           ("not_fragmented", lambda r: r["extra_recall"] == 0)):
        rows = []
        for row in limited:
            if not selector(row):
                continue
            n = native[row["manifest_index"]]
            if (row["scene"], row["ann_id"]) != (n["scene"], n["ann_id"]):
                raise ValueError("Expression identity differs")
            rows.append({
                "manifest_index": row["manifest_index"], "scene": row["scene"],
                "extra_recall": row["extra_recall"],
                "selected_positive": n["selected_positive"],
                "matched_queries": n["matched_queries"],
                "fn_corrective": n["all_finite"] and n["fn_correct"] == n["fn"],
                "fp_corrective": n["all_finite"] and n["fp_correct"] == n["fp"],
            })
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "selected_positive": sum(r["selected_positive"] for r in rows),
            "has_matched_positive": sum(r["matched_queries"] > 0 for r in rows),
            "both_signs_corrective": sum(
                r["fn_corrective"] and r["fp_corrective"] for r in rows),
            "rows": rows,
        }
    if groups["fragmented"]["expressions"] != 4:
        raise ValueError("Preselected fragment cohort differs")
    return {
        "contract": "m95_fragment_native_loss_v1",
        "admission": False,
        "fragment_sha256": FRAGMENT_SHA,
        "native_loss_sha256": LOSS_SHA,
        "groups": groups,
        "limits": "Original frozen TRAIN source gradients, not new-model backward or evidence of missing supervision.",
    }


def main():
    p = argparse.ArgumentParser()
    for key in ("fragment", "loss", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(read(args.fragment, FRAGMENT_SHA), read(args.loss, LOSS_SHA))
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: {n: v for n, v in g.items() if n != "rows"}
                      for k, g in report["groups"].items()}))


if __name__ == "__main__":
    main()
