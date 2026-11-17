"""Static score-direction audit of the frozen discordance provenance report."""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = "pipeline/reports/m95_discordance_provenance_20260923-1107.json"
SOURCE_SHA256 = "6ed69abe4d26a2bd20283bb59119c2ebf30d4c0e73e2252903c210925292e372"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(rows):
    if len(rows) != 32 or len({(r["manifest_index"], r["mask_sha256"]) for r in rows}) != 32:
        raise ValueError("Frozen discordant-class cohort differs")
    if len({r["scene_id"] for r in rows}) != 24 or sum(r["acceptable"] for r in rows) != 23:
        raise ValueError("Frozen scene or acceptable denominator differs")
    groups = {}
    for name, selected in (
        ("all", rows),
        ("acceptable", [r for r in rows if r["acceptable"]]),
        ("seed_label_aligned", [r for r in rows if r["seed_membership_equals_label"]]),
        ("positive_outside_seed", [r for r in rows if r["positive_outside_seed_count"]]),
    ):
        margins = [r["mean_positive_minus_negative_score"] for r in selected]
        groups[name] = {
            "classes": len(selected),
            "scenes": len({r["scene_id"] for r in selected}),
            "positive_higher": sum(m > 0 for m in margins),
            "positive_lower": sum(m < 0 for m in margins),
            "ties": sum(m == 0 for m in margins),
            "identity": dict(Counter(r["identity"] for r in selected)),
            "lower_rows": [
                {"manifest_index": r["manifest_index"], "scene_id": r["scene_id"],
                 "margin": r["mean_positive_minus_negative_score"]}
                for r in selected if r["mean_positive_minus_negative_score"] < 0
            ],
        }
    if groups["all"]["classes"] != groups["seed_label_aligned"]["classes"] + groups["positive_outside_seed"]["classes"]:
        raise ValueError("Seed provenance strata do not partition the cohort")
    return groups


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = ROOT / SOURCE
    if sha256(source) != SOURCE_SHA256:
        raise ValueError("Frozen provenance report changed")
    doc = json.loads(source.read_text(encoding="utf-8"))
    if doc["contract"] != "m95_saved_discordance_provenance_v1" or doc["admission"]:
        raise ValueError("Wrong provenance contract")
    result = {
        "contract": "m95_static_discordance_score_audit_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "scope": "Static analysis of one already verified frozen TRAIN failure report; no native data or model execution.",
        "groups": audit(doc["rows"]),
        "interpretation": (
            "Equal thresholded masks can have distinct indicator scores and different "
            "native labels. Positive-higher is descriptive, not proof that the labels "
            "are correct or that a new supervision unit improves held-out mIoU."
        ),
        "limitations": [
            "Forty outcome-selected TRAIN failures; classes within a scene are dependent.",
            "Mean positive-minus-negative score is a class-level pair mean, not a scene-balanced effect.",
            "Six outside-seed positives have no saved nearest-GT cause tag.",
            "No independent query-state capture, causal training intervention, native backward or resource gate.",
        ],
        "admission": False,
        "queue_mutation": False,
        "evidence": [{"path": SOURCE, "sha256": SOURCE_SHA256}],
    }
    output = Path(args.output)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps(result["groups"], indent=2))


if __name__ == "__main__":
    main()
