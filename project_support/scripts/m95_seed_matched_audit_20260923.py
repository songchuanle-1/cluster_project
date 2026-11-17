"""Bounded within-seed-identity audit of saved discordant mask classes."""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = "pipeline/reports/m95_discordance_provenance_20260923-1107.json"
SOURCE_SHA256 = "6ed69abe4d26a2bd20283bb59119c2ebf30d4c0e73e2252903c210925292e372"


def audit(rows):
    if len(rows) != 32 or len({(r["manifest_index"], r["mask_sha256"]) for r in rows}) != 32:
        raise ValueError("Frozen discordant-class cohort differs")
    if len({r["scene_id"] for r in rows}) != 24 or sum(r["acceptable"] for r in rows) != 23:
        raise ValueError("Frozen scene or acceptable denominator differs")
    matched = []
    for row in rows:
        seeds = row["seeds"]
        if len(seeds) != row["query_count"] or len({s["query"] for s in seeds}) != len(seeds):
            raise ValueError("Query binding differs")
        if sum(bool(s["positive"]) for s in seeds) != row["positive_count"]:
            raise ValueError("Positive binding differs")
        ids = {s["seed_physical_id"] for s in seeds if s["positive"]} & {
            s["seed_physical_id"] for s in seeds if not s["positive"]
        }
        for physical_id in sorted(ids):
            pos = [s["score"] for s in seeds if s["positive"] and s["seed_physical_id"] == physical_id]
            neg = [s["score"] for s in seeds if not s["positive"] and s["seed_physical_id"] == physical_id]
            if not pos or not neg:
                raise ValueError("Incomplete matched group")
            matched.append({
                "manifest_index": row["manifest_index"],
                "scene_id": row["scene_id"],
                "mask_sha256": row["mask_sha256"],
                "identity": row["identity"],
                "acceptable": row["acceptable"],
                "seed_physical_id": physical_id,
                "positive_queries": len(pos),
                "negative_queries": len(neg),
                "positive_minus_negative_mean_score": sum(pos) / len(pos) - sum(neg) / len(neg),
                "same_exact_seed_index_pairs": sum(
                    p["physical_seed_index"] == n["physical_seed_index"]
                    for p in seeds if p["positive"] and p["seed_physical_id"] == physical_id
                    for n in seeds if not n["positive"] and n["seed_physical_id"] == physical_id
                ),
            })
    return {
        "total_discordant_classes": len(rows),
        "total_scenes": len({r["scene_id"] for r in rows}),
        "matched_classes": len({(r["manifest_index"], r["mask_sha256"]) for r in matched}),
        "matched_scenes": len({r["scene_id"] for r in matched}),
        "matched_groups": len(matched),
        "identity": dict(Counter(r["identity"] for r in matched)),
        "positive_higher_groups": sum(r["positive_minus_negative_mean_score"] > 0 for r in matched),
        "positive_lower_groups": sum(r["positive_minus_negative_mean_score"] < 0 for r in matched),
        "exact_seed_index_pairs": sum(r["same_exact_seed_index_pairs"] for r in matched),
        "rows": matched,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = ROOT / SOURCE
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Frozen provenance report changed")
    doc = json.loads(source.read_text(encoding="utf-8"))
    if doc["contract"] != "m95_saved_discordance_provenance_v1" or doc["admission"]:
        raise ValueError("Wrong provenance contract")
    result = {
        "contract": "m95_static_seed_matched_audit_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "scope": "Saved TRAIN failure report only; physical instance ID of query seed matched within exact binary-mask class.",
        "summary": audit(doc["rows"]),
        "limitations": [
            "Outcome-selected 40 TRAIN failures; no population or causal benefit estimate.",
            "A shared physical instance ID does not match seed coordinate, query state, object assignment cause, or target label.",
            "Native nearest-GT match cause remains unavailable from this saved capture.",
            "No native backward, candidate resource check, or admission.",
        ],
        "admission": False,
        "queue_mutation": False,
        "evidence": [{"path": SOURCE, "sha256": SOURCE_SHA256}],
    }
    output = Path(args.output)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps({k: v for k, v in result["summary"].items() if k != "rows"}))


if __name__ == "__main__":
    main()
