"""Descriptive common-support audit; does not change registered estimands."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from analyze_m95_manifest_identity_controls_20260922 import paired_summary


def audit(rows):
    common = []
    failures = Counter()
    missing = Counter()
    for row in rows:
        positive = row["target_positive_iou"]
        objectness = row["target_objectness_iou"]
        if positive is not None and objectness is not None:
            common.append({
                "scene_id": row["scene_id"],
                "positive_minus_target_objectness": positive - objectness,
            })
        if row["primary_pair_iou_uplift"] is None:
            if row["stratum"] == "class_unique":
                missing["class_unique_no_peer_by_design"] += 1
            elif row["class_matched_non_target_query"] is None:
                missing["ambiguous_no_peer_query"] += 1
            else:
                missing["ambiguous_no_score_matched_pair"] += 1
        if row["deployed_iou"] <= 0.5:
            failures["total"] += 1
            if max(row["ious"]) <= 0.5:
                failures["no_acceptable_candidate"] += 1
            else:
                failures["selection_with_acceptable_candidate"] += 1
            if positive is not None and positive > 0.5:
                failures["positive_repairs"] += 1
            if objectness is not None and objectness > 0.5:
                failures["target_objectness_repairs"] += 1
    by_scene = defaultdict(list)
    for row in rows:
        by_scene[row["scene_id"]].append(row)
    return {
        "common_support_positive_minus_target_objectness": paired_summary(
            common, "positive_minus_target_objectness"
        ),
        "common_support_expressions": len(common),
        "excluded_from_common_support": len(rows) - len(common),
        "primary_missingness": dict(missing),
        "failure_counts": dict(failures),
        "expressions": len(rows),
        "scenes": len(by_scene),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(args.analysis)
    document = json.loads(source.read_text(encoding="utf-8"))
    assert document["contract"] == "m95_manifest_identity_control_analysis_v1"
    assert len(document["rows"]) == 256
    result = {
        "contract": "m95_identity_descriptive_handoff_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "source": {
            "path": str(source),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        },
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "registered_primary": document["summary"]["primary_estimand"],
        "descriptive": audit(document["rows"]),
        "limitations": [
            "Common-support comparison is post-capture descriptive, not a new primary test.",
            "Target-objectness uses the true target union; it is not any-instance objectness.",
            "Positive-versus-known-wrong target IoU is an oracle contrast, not deployable efficacy.",
            "Only score-match-eligible ambiguous rows enter the primary estimand.",
            "Feature margins use a target-positive query and overlapping prototypes; not causal mediation.",
            "Cross-stage cosine differences alone cannot diagnose modality or identity destruction.",
            "No new mechanism, novelty, resource gate, native candidate backward, or admission is established.",
        ],
    }
    with Path(args.output).open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result["descriptive"], indent=2))


if __name__ == "__main__":
    main()
