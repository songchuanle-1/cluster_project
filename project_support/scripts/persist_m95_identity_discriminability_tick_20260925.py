"""Persist the frozen identity-vs-score diagnostic on the three due IDs."""
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
        "path": "pipeline/reports/m95_instance_identity_discriminability_20260925-0146.json",
        "sha256": "dd53fb3919cd50df9851bbbf400f64ec1248befcd58dc43a7c2e9e0c1cb363ac",
    },
    {
        "path": "scripts/m95_instance_identity_discriminability_20260925.py",
        "sha256": "d606ec5345fcc16bacb56317e44c2f7638364d3400b07abc4960cd0e6da698a5",
    },
    {
        "path": "scripts/test_m95_instance_identity_discriminability_20260925.py",
        "sha256": "c983d589730a4e1ccdfe149e1fb8ab2deee1ac0dd86ec07688ad37ba2196b76a",
    },
)
NEXT_ACTION = (
    "Monitor exact capture PID 3140840 to completion without launching a "
    "duplicate. Then run the fail-closed postprocess runner. Interpret a "
    "match-cause defect as score/supervision misalignment unless the exact "
    "capture contradicts the frozen identity discriminability result; no "
    "representation-deficiency claim is supported by the current diagnostic."
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--decision", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    work_path = root / "pipeline" / "research_work.json"
    decision_path = Path(args.decision).resolve()
    if not decision_path.is_file():
        raise ValueError("Decision record does not exist")
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
    evidence = list(EVIDENCE)
    evidence.append(
        {
            "path": decision_path.relative_to(root).as_posix(),
            "sha256": file_sha256(decision_path),
        }
    )
    progress = {
        "timestamp": "2026-09-25T01:50:18+08:00",
        "report": evidence[0],
        "checker": evidence[1],
        "test": evidence[2],
        "decision": evidence[3],
        "source_capture_sha256": (
            "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025"
        ),
        "eligible_expressions": 121,
        "target_peer_queries": 9197,
        "final_balanced_accuracy": 0.9846460668274143,
        "final_scene_bootstrap_accuracy": {
            "point_estimate": 0.98031474074695,
            "lo": 0.9660270982707033,
            "hi": 0.9902222572307436,
        },
        "score_matched_pairs": 1161,
        "identity_pair_accuracy": 0.9569336778639104,
        "score_pair_accuracy": 0.6950904392764858,
        "identity_minus_score": 0.26184323858742464,
        "identity_minus_score_scene_bootstrap": {
            "point_estimate": 0.28935601096999675,
            "lo": 0.19441024377422958,
            "hi": 0.3878546287691764,
        },
        "conclusion": (
            "Target-versus-peer identity is strongly decodable from all "
            "captured feature stages, while query scores are materially less "
            "aligned with target IoU on score-matched pairs. This is oracle "
            "diagnostic evidence and does not admit a mechanism."
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
        candidate["identity_discriminability_20260925"] = progress
        existing = {
            (item.get("path"), item.get("sha256"))
            for item in candidate.setdefault("evidence", [])
        }
        for item in evidence:
            key = (item["path"], item["sha256"])
            if key not in existing:
                candidate["evidence"].append(item)

    document["updated_at"] = datetime.now().astimezone().isoformat()
    document["design_cycle"] = {
        "timestamp": document["updated_at"],
        "stop_reason": "exact_full_scan_running_after_identity_discriminability",
        "attempted_ids": list(CANDIDATE_IDS),
        "evidence": evidence,
        "resume_condition": (
            "Resume PID 3140840 at capture completion, run the fail-closed "
            "postprocess runner, and combine exact match-cause evidence with "
            "the identity-versus-score diagnostic before mechanism derivation "
            "or admission."
        ),
    }
    work_path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"updated_at": document["updated_at"], "evidence": evidence}))


if __name__ == "__main__":
    main()
