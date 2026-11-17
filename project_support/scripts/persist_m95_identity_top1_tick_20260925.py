"""Persist the expression-level identity top-1 control on due candidates."""
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
    "path": "pipeline/reports/m95_identity_top1_counterfactual_20260925-0406.json",
    "sha256": "82fc1cc2485ee0f4a4d7b604927989efcfaffd2af4a8d7be69be3b962ffc122e",
}
CHECKER = {
    "path": "scripts/m95_identity_top1_counterfactual_20260925.py",
    "sha256": "cb7b8851361f7655a65c5ec17a5dbb0a0fb0d4bfc3284c2df916b0b2c2c99727",
}
TEST = {
    "path": "scripts/test_m95_identity_top1_counterfactual_20260925.py",
    "sha256": "4a3cac304771556c00922485bccca2e5f0b72be290a936c37ad1439107dce041",
}
DECISION = {
    "path": "pipeline/decisions/20260925-040536_route_change.md",
    "sha256": "a0b4f12d699bf668ef453c9463579f2f409b23d474442ea40497ec7599e01c31",
}
ANALYSIS = {
    "path": "pipeline/analyses/M95-identity-top1-counterfactual_20260925-0406.md",
    "sha256": None,
}
SOURCE_CAPTURE_SHA256 = (
    "f90286842d9d82d835652a29048100a10b6286ee563e0d7c296363e95880025"
)
NEXT_ACTION = (
    "Do not create an identity-margin selector. Monitor exact capture PID "
    "3140840 without launching a duplicate; when capture.json exists, run "
    "scripts/m95_exact_capture_postprocess_20260925.py and use exact native "
    "match causes to attribute score, supervision, geometry, and mask-"
    "component effects."
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
    analysis = dict(ANALYSIS)
    analysis["sha256"] = file_sha256(root / analysis["path"]).lower()
    evidence = [
        REPORT,
        CHECKER,
        TEST,
        DECISION,
        analysis,
    ]
    for item in evidence:
        if file_sha256(root / item["path"]).lower() != item["sha256"].lower():
            raise ValueError("Evidence hash differs: %s" % item["path"])

    report = json.loads((root / REPORT["path"]).read_text(encoding="utf-8"))
    if report["source_capture"]["sha256"] != SOURCE_CAPTURE_SHA256:
        raise ValueError("Source capture identity differs")
    summary = report["summary"]
    if summary["expressions"] != 121 or summary["scenes"] != 121:
        raise ValueError("Top-1 expression coverage differs")
    if summary["same_query"] != 2 or summary["identity_changed_query"] != 119:
        raise ValueError("Top-1 selector agreement differs")
    if summary["success"]["score"]["success_rate"] >= summary["success"][
        "identity"
    ]["success_rate"]:
        raise ValueError("Expected disconfirming top-1 success result")
    if report["counts"]["identity_eligible_queries"] != 9362:
        raise ValueError("Identity-eligible query count differs")

    work_path = root / "pipeline" / "research_work.json"
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
        "analysis": analysis,
        "source_capture_sha256": SOURCE_CAPTURE_SHA256,
        "attempted_queries": report["counts"]["attempted_queries"],
        "identity_eligible_queries": report["counts"][
            "identity_eligible_queries"
        ],
        "expressions": summary["expressions"],
        "same_query": summary["same_query"],
        "identity_changed_query": summary["identity_changed_query"],
        "identity_minus_score": summary["paired_effects"][
            "identity_minus_score"
        ],
        "oracle_minus_score": summary["paired_effects"][
            "oracle_minus_score"
        ],
        "identity_success": summary["success"]["identity"][
            "success_rate"
        ],
        "score_success": summary["success"]["score"]["success_rate"],
        "permutation_null": summary["permutation_null"],
        "conclusion": (
            "Identity-margin top-1 selection is disconfirmed on the oracle "
            "diagnostic: it changed 119 of 121 choices, reduced success above "
            "0.5 IoU from 20.66% to 9.92%, and had a scene-clustered IoU "
            "difference whose interval includes zero. Do not create a "
            "selector or renamed variant; exact native causes remain required."
        ),
        "native_execution_completed": False,
        "admission": False,
    }
    for candidate_id in CANDIDATE_IDS:
        candidate = candidates.get(candidate_id)
        if candidate is None:
            raise ValueError("Missing due candidate: %s" % candidate_id)
        candidate["stage"] = "validation"
        candidate["status"] = "waiting_exact_capture_after_top1_disconfirmation"
        candidate["next_action"] = NEXT_ACTION
        candidate["identity_top1_counterfactual_20260925"] = progress
        existing = {
            (item.get("path"), item.get("sha256"))
            for item in candidate.setdefault("evidence", [])
        }
        for item in evidence:
            normalized = {
                "path": item["path"],
                "sha256": item["sha256"].lower(),
            }
            key = (normalized["path"], normalized["sha256"])
            if key not in existing:
                candidate["evidence"].append(normalized)

    updated_at = datetime.now().astimezone().isoformat()
    document["updated_at"] = updated_at
    document["next_action"] = NEXT_ACTION
    document["design_cycle"] = {
        "timestamp": updated_at,
        "stop_reason": "native_capture_in_progress",
        "deferred_reason": (
            "identity_top1_control_completed_exact_full_scan_running"
        ),
        "attempted_ids": list(CANDIDATE_IDS),
        "evidence": [
            {"path": item["path"], "sha256": item["sha256"].lower()}
            for item in evidence
        ],
        "resume_condition": NEXT_ACTION,
        "blocker": (
            "Exact capture PID 3140840 remains active and capture.json is "
            "absent; launching a duplicate is forbidden."
        ),
    }
    work_path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "updated_at": updated_at,
                "candidate_ids": list(CANDIDATE_IDS),
                "report": REPORT,
            }
        )
    )


if __name__ == "__main__":
    main()
