"""Frozen-report audit of all-query support reachability and specificity."""
import argparse
import hashlib
import json
from pathlib import Path

UNION_SHA = "e8749bd8fa89dfcae3f842766f76b1fb89d1e2fa271f39ae9f733489f5e5b48c"
FEATURE_SHA = "7537ade52ef41ea73582fe1452bfa410f0a17e5485634ef572769ba300fc4c81"


def read(path, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Frozen report differs: {path}")
    return json.loads(data)


def analyze(union, feature):
    if union["capture_sha256"] != feature["capture_sha256"]:
        raise ValueError("Capture differs")
    features = {
        row["manifest_index"]: row
        for group in ("limited", "covered")
        for row in feature[group]["rows"]
    }
    if len(features) != 256:
        raise ValueError("Feature population differs")
    groups = {}
    seen = set()
    for cohort in ("limited", "covered"):
        for row in union[cohort]["rows"]:
            key = row["manifest_index"]
            f = features[key]
            if key in seen or (row["scene"], row["ann_id"]) != (f["scene"], f["ann_id"]):
                raise ValueError("Identity differs")
            seen.add(key)
            if row["limited"] != (cohort == "limited"):
                raise ValueError("Cohort differs")
            if not 0 <= row["union_target_overlap"] <= row["union_superpoints"]:
                raise ValueError("Support count invalid")
            group = f"{cohort}/" + ("overlap" if row["union_target_overlap"] else "none")
            groups.setdefault(group, []).append({
                "manifest_index": key, "scene": row["scene"],
                "target_superpoints": f.get("target_superpoints"),
                "union_target_overlap": row["union_target_overlap"],
                "original_iou": row["original_iou"], "union_iou": row["union_iou"],
                "union_delta": row["union_delta"], "feature_status": f["status"],
                "final_margin": f.get("final_margin"),
            })
    if seen != set(range(256)):
        raise ValueError("Union population incomplete")
    summaries = {}
    for group in ("limited/none", "limited/overlap", "covered/none", "covered/overlap"):
        rows = groups.get(group, [])
        summaries[group] = {
            "expressions": len(rows),
            "scenes": len({r["scene"] for r in rows}),
            "union_fixed": sum(r["original_iou"] <= .5 < r["union_iou"] for r in rows),
            "union_broken": sum(r["original_iou"] > .5 >= r["union_iou"] for r in rows),
            "union_harmed": sum(r["union_delta"] < 0 for r in rows),
            "mean_union_delta": sum(r["union_delta"] for r in rows) / len(rows) if rows else None,
            "margin_paired": sum(r["final_margin"] is not None for r in rows),
            "rows": rows,
        }
    return {
        "contract": "m95_support_identifiability_v1",
        "admission": False,
        "union_sha256": UNION_SHA,
        "feature_sha256": FEATURE_SHA,
        "groups": summaries,
        "limits": "TRAIN frozen retrospective overlap; not an inference-time rule, native new-model backward, or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    for key in ("union", "feature", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(read(args.union, UNION_SHA), read(args.feature, FEATURE_SHA))
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: {n: v for n, v in g.items() if n != "rows"}
                      for k, g in report["groups"].items()}))


if __name__ == "__main__":
    main()
