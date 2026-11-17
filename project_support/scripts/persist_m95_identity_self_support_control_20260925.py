"""Persist the M95 identity self-support control on the three due IDs."""
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
EVIDENCE = (
    {
        "path": "pipeline/reports/m95_identity_self_support_control_20260925-0200.json",
        "sha256": "028346febc84dafcbdc1cfae38729f93c27845f3b032ad4495e602a5c14943ad",
    },
    {
        "path": "scripts/m95_identity_self_support_control_20260925.py",
        "sha256": "d7ee18afcbf3b1fa3ceffc7df5564b104e59a4055a1bad5056fc04f96f6d84ef",
    },
    {
        "path": "scripts/test_m95_identity_self_support_control_20260925.py",
        "sha256": "006dc9eec643d52ebe63e59e53512931c54d9724ef97114e16e99acfeac6a7d6",
    },
    {
        "path": "pipeline/decisions/20260925-020000_route_change.md",
        "sha256": "7cc33647cfdcedb01a6879a1fc8dd494126d77280c834fb1e65a84460b8aeb90",
    },
)
NEXT_ACTION = (
    "Monitor exact capture PID 3140840 to completion without launching a "
    "duplicate, then run the fail-closed postprocess runner. Do not rely on "
    "the earlier in-sample identity-minus-score advantage: the query-support "
    "control reduces it to -0.19pp on 515 identical final-stage pairs. Use "
    "exact match-cause evidence to distinguish score/supervision misalignment "
    "from geometry or component defects before any mechanism or representation "
    "deficiency claim."
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
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    work_path = root / "pipeline" / "research_work.json"
    for item in EVIDENCE:
        path = root / item["path"]
        if not path.is_file():
            raise ValueError("Evidence file does not exist: %s" % path)
        if file_sha256(path) != item["sha256"]:
            raise ValueError("Evidence hash differs: %s" % path)

    document = json.loads(work_path.read_text(encoding="utf-8"))
    candidates = {
        candidate["id"]: candidate for candidate in document["candidates"]
    }
    progress = {
        "timestamp": "2026-09-25T02:02:33+08:00",
        "stage": "validation",
        "report": EVIDENCE[0],
        "checker": EVIDENCE[1],
        "test": EVIDENCE[2],
        "decision": EVIDENCE[3],
        "source_capture_sha256": (
            "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025"
        ),
        "control": "subtract_each_query_support_from_target_and_peer_prototypes",
        "attempted_final_queries": 9649,
        "evaluated_final_queries": 6397,
        "coverage": 0.6629702559850762,
        "in_sample_final_balanced_accuracy": 0.9826166269721606,
        "self_support_excluded_final_balanced_accuracy": 0.9275216781237114,
        "self_support_excluded_final_scene_bootstrap": {
            "point_estimate": 0.928806850672277,
            "lo": 0.903924959117753,
            "hi": 0.9509838693958127,
        },
        "in_sample_identity_minus_score": 0.12427184466019417,
        "self_support_excluded_identity_minus_score": -0.001941747572815534,
        "matched_pairs": 515,
        "conclusion": (
            "The prior in-sample identity advantage was materially inflated by "
            "prototype self-inclusion. Identity information remains decodable "
            "after exclusion, but score-matched identity superiority is not "
            "established. This is oracle diagnostic evidence only."
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
        candidate["identity_self_support_control_20260925"] = progress
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
    document["design_cycle"] = {
        "timestamp": document["updated_at"],
        "stop_reason": "tick_deadline_near",
        "deferred_reason": "exact_full_scan_running_after_self_support_control",
        "attempted_ids": list(CANDIDATE_IDS),
        "evidence": list(EVIDENCE),
        "resume_condition": (
            "Resume PID 3140840 at capture completion, run the fail-closed "
            "postprocess runner, and use exact component causes with the "
            "query-support-excluded diagnostic before any mechanism admission."
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
                "evidence": list(EVIDENCE),
            }
        )
    )


if __name__ == "__main__":
    main()
