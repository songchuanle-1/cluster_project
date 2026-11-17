"""Persist expression and target-query dependence controls on due candidates."""
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
    "path": "pipeline/reports/m95_identity_expression_dependence_20260925-0340.json",
    "sha256": "1EA570086DE89A00D393F3AF68F210560032D84D1306D5532AC01F22AD0FE8D9",
}
CHECKER = {
    "path": "scripts/m95_identity_expression_dependence_20260925.py",
    "sha256": "EC6E33EAD0DECE70001171432FEC41473D305D45F24BF3B90D2BC0B8A1B3677F",
}
TEST = {
    "path": "scripts/test_m95_identity_expression_dependence_20260925.py",
    "sha256": "199041500DA8D4250CC46CA268346E04B33F1C242B6BDF01F1F2114B5449926B",
}
DECISION = {
    "path": "pipeline/decisions/20260925-034133_route_change.md",
    "sha256": "086BDDFA7AF2CC0CDF0BA09783A2FAA0517DDBD2CDEF9C602264E182F52024B7",
}
SUPERSEDED_REPORT = {
    "path": "pipeline/reports/m95_identity_expression_dependence_20260925-0322.json",
    "sha256": "623DBB889DFDEF8D7DD225D80C0EBC241E8E17D299AB11B0579D54F4C1B463CB",
    "reason": (
        "Expression-only sensitivity was extended with a stricter target-query "
        "cluster bootstrap and leave-one-target-query-out control."
    ),
}
SOURCE_CAPTURE_SHA256 = (
    "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025"
)
EVIDENCE = (REPORT, CHECKER, TEST, DECISION)
NEXT_ACTION = (
    "Monitor exact capture PID 3140840 to completion without launching a "
    "duplicate, then run the fail-closed postprocess runner. Preserve the "
    "target-query-clustered support-excluded identity evidence, but require "
    "exact native match-cause evidence before any mechanism or component-cause "
    "claim."
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
        "--root",
        default=str(Path(__file__).resolve().parent.parent),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    work_path = root / "pipeline" / "research_work.json"
    for item in EVIDENCE + (SUPERSEDED_REPORT,):
        path = root / item["path"]
        if file_sha256(path).lower() != item["sha256"].lower():
            raise ValueError("Evidence hash differs: %s" % path)

    report = json.loads((root / REPORT["path"]).read_text(encoding="utf-8"))
    if report["source_capture"]["sha256"] != SOURCE_CAPTURE_SHA256:
        raise ValueError("Source capture identity differs")
    if report["common_support_queries"] != 6397:
        raise ValueError("Common query count differs")
    if report["full_pairs"]["pairs"] != 1833:
        raise ValueError("Registered full-pair count differs")
    if report["full_pairs"]["expressions"] != 18:
        raise ValueError("Registered expression count differs")
    if report["target_query_cluster_bootstrap"]["target_query_count"] != 135:
        raise ValueError("Target-query cluster count differs")

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
        "supersedes": SUPERSEDED_REPORT,
        "source_capture_sha256": SOURCE_CAPTURE_SHA256,
        "common_support_queries": report["common_support_queries"],
        "common_support_pairs": report["full_pairs"]["pairs"],
        "common_support_expressions": report["full_pairs"]["expressions"],
        "pooled_identity_minus_score": report["full_pairs"][
            "identity_minus_score"
        ],
        "expression_balanced_identity_minus_score": report[
            "expression_balanced"
        ]["expression_balanced_identity_minus_score"],
        "expression_cluster_bootstrap_95ci": report[
            "expression_cluster_bootstrap"
        ],
        "target_query_cluster_bootstrap_95ci": report[
            "target_query_cluster_bootstrap"
        ],
        "leave_one_expression_out": report["leave_one_expression_out"],
        "leave_one_target_query_out": report[
            "leave_one_target_query_out"
        ],
        "deterministic_one_pair_per_expression": report[
            "deterministic_one_pair_per_expression"
        ]["summary"],
        "conclusion": (
            "After clustering matched peers by target query, the "
            "support-excluded final-stage identity-score advantage remains "
            "positive (13.15pp; 95% CI +8.46pp to +18.30pp across 135 target "
            "queries). This is stronger dependence-control evidence, not a "
            "mechanism, deployable result, or admission."
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
        candidate["identity_expression_dependence_20260925"] = progress
        for item in candidate.setdefault("evidence", []):
            item["sha256"] = item["sha256"].lower()
        existing = {
            (item.get("path"), item.get("sha256"))
            for item in candidate.setdefault("evidence", [])
        }
        for item in EVIDENCE:
            normalized = {
                "path": item["path"],
                "sha256": item["sha256"].lower(),
            }
            key = (normalized["path"], normalized["sha256"])
            if key not in existing:
                candidate["evidence"].append(normalized)

    document["updated_at"] = datetime.now().astimezone().isoformat()
    document["next_action"] = NEXT_ACTION
    document["design_cycle"] = {
        "timestamp": document["updated_at"],
        "stop_reason": "external_blocker",
        "deferred_reason": (
            "exact_full_scan_running_after_target_query_dependence_control"
        ),
        "attempted_ids": list(CANDIDATE_IDS),
        "evidence": [
            {"path": item["path"], "sha256": item["sha256"].lower()}
            for item in EVIDENCE
        ],
        "resume_condition": NEXT_ACTION,
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
