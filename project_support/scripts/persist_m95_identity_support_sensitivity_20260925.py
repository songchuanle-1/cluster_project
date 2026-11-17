"""Persist the corrected M95 support-exclusion evidence on due candidates."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path


CANDIDATE_IDS = (
    "referent-supervision-axis",
    "referent-discrimination",
    "instance-identity-representation",
)
REPORT = {
    "path": "pipeline/reports/m95_identity_support_sensitivity_20260925-0248.json",
    "sha256": "baaba41beb319329e4262456b636344dd49f12bfa37a6154f1683fd12f549904",
}
CHECKER = {
    "path": "scripts/m95_identity_support_sensitivity_20260925.py",
    "sha256": "5d3f4da568f5d534b37e752a46db3925522d6e36f9f44afd4e8d43030ab99cf0",
}
TEST = {
    "path": "scripts/test_m95_identity_support_sensitivity_20260925.py",
    "sha256": "9c1f7cfc4c70afcd8155dee1b2ddb934dea3d72a99c1287d201210264364c48a",
}
DECISION = {
    "path": "pipeline/decisions/20260925-022629_route_change.md",
    "sha256": "c2a492afb3c079bc6d7a19ff74d7dc2674ddb6cb38f7fff6f5d415448b53cca8",
}
SUPERSEDED = {
    "path": "pipeline/reports/m95_identity_self_support_control_20260925-0200.json",
    "sha256": "028346febc84dafcbdc1cfae38729f93c27845f3b032ad4495e602a5c14943ad",
    "reason": (
        "Pair enumeration was order-biased: each peer was matched only against "
        "target queries already encountered in the loop."
    ),
}
EVIDENCE = (REPORT, CHECKER, TEST, DECISION)
SOURCE_CAPTURE_SHA256 = (
    "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025"
)
NEXT_ACTION = (
    "Monitor exact capture PID 3140840 to completion without launching a "
    "duplicate, then run the fail-closed postprocess runner. Treat the "
    "support-excluded identity advantage as restored under corrected full-pair "
    "and nearest-peer controls, but require exact native match-cause evidence "
    "before any mechanism or component-cause claim."
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", default=str(Path(__file__).resolve().parent.parent)
    )
    parser.add_argument(
        "--finalize-design-cycle",
        action="store_true",
        help="Record the scheduler-deadline disposition for this design tick.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    work_path = root / "pipeline" / "research_work.json"
    for item in EVIDENCE + (SUPERSEDED,):
        path = root / item["path"]
        if not path.is_file():
            raise ValueError("Evidence file does not exist: %s" % path)
        if file_sha256(path) != item["sha256"]:
            raise ValueError("Evidence hash differs: %s" % path)

    report = json.loads((root / REPORT["path"]).read_text(encoding="utf-8"))
    if report["source_capture"]["sha256"] != SOURCE_CAPTURE_SHA256:
        raise ValueError("Support-sensitivity capture identity differs")
    final = report["stages"]["final"]["common_population"]
    if final["queries"] != 6397 or final["score_matched_pairs"] != 1833:
        raise ValueError("Final common-population counts differ")
    if final["nearest_peer_score_matched_pairs"] != 134:
        raise ValueError("Final nearest-peer count differs")

    document = json.loads(work_path.read_text(encoding="utf-8"))
    candidates = {
        candidate["id"]: candidate for candidate in document["candidates"]
    }
    progress = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "stage": "validation",
        "report": REPORT,
        "checker": CHECKER,
        "test": TEST,
        "decision": DECISION,
        "supersedes": SUPERSEDED,
        "source_capture_sha256": SOURCE_CAPTURE_SHA256,
        "support_floors": [1, 2, 3],
        "common_final_queries": final["queries"],
        "common_final_full_pair_count": final["score_matched_pairs"],
        "common_final_nearest_peer_pair_count": final[
            "nearest_peer_score_matched_pairs"
        ],
        "floor1_full_pair_identity_minus_score": final[
            "score_matched_query_pairs"
        ]["1"]["identity_minus_score"],
        "floor3_full_pair_identity_minus_score": final[
            "score_matched_query_pairs"
        ]["3"]["identity_minus_score"],
        "floor3_full_pair_scene_bootstrap_95ci": final[
            "score_matched_query_pairs"
        ]["3"]["scene_bootstrap"]["difference"],
        "floor3_nearest_peer_identity_minus_score": final[
            "nearest_peer_matched"
        ]["3"]["identity_minus_score"],
        "floor3_nearest_peer_scene_bootstrap_95ci": final[
            "nearest_peer_matched"
        ]["3"]["scene_bootstrap"]["difference"],
        "stage_floor3_full_pair_identity_minus_score": {
            stage: report["stages"][stage]["common_population"][
                "score_matched_query_pairs"
            ]["3"]["identity_minus_score"]
            for stage in (
                "raw_2d",
                "projected_2d",
                "raw_3d",
                "projected_3d",
                "fused",
                "final",
            )
        },
        "conclusion": (
            "Correcting pair enumeration overturns the prior null result. "
            "After query-support exclusion, the final-stage identity-score "
            "advantage is positive on both the full common pair population "
            "and the nearest-score-peer control. This is oracle diagnostic "
            "evidence only and does not establish a mechanism or admission."
        ),
        "native_execution_completed": False,
        "admission": False,
    }
    for candidate_id in CANDIDATE_IDS:
        candidate = candidates.get(candidate_id)
        if candidate is None:
            raise ValueError("Missing due candidate: %s" % candidate_id)
        candidate["stage"] = "validation"
        candidate["next_action"] = NEXT_ACTION
        candidate["identity_support_sensitivity_20260925"] = progress
        existing = {
            (item.get("path"), item.get("sha256"))
            for item in candidate.setdefault("evidence", [])
        }
        for item in EVIDENCE:
            key = (item["path"], item["sha256"])
            if key not in existing:
                candidate["evidence"].append(item)

    document["updated_at"] = datetime.now().astimezone().isoformat()
    document["next_action"] = NEXT_ACTION
    if args.finalize_design_cycle:
        document["design_cycle"] = {
            "timestamp": document["updated_at"],
            "stop_reason": "tick_deadline_near",
            "deferred_reason": (
                "exact_full_scan_running_after_support_sensitivity_correction"
            ),
            "attempted_ids": list(CANDIDATE_IDS),
            "evidence": list(EVIDENCE),
            "resume_condition": (
                "Resume PID 3140840 at capture completion, run the fail-closed "
                "postprocess runner, and require exact native match-cause "
                "evidence before mechanism admission."
            ),
        }
    work_path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "updated_at": document["updated_at"],
                "candidate_ids": list(CANDIDATE_IDS),
                "report": REPORT,
            }
        )
    )


if __name__ == "__main__":
    main()
