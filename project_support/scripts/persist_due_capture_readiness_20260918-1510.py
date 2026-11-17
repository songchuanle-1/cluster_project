from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "pipeline/reports/due_capture_readiness_20260918-1510.json"
WORK_PATH = ROOT / "pipeline/research_work.json"
CANDIDATE_IDS = [
    "referent-causality-audit",
    "modality-identity-preservation",
    "referent-discrimination",
    "instance-identity-representation",
    "referent-query-selection",
    "input-modality-distinguishability",
    "same-target-description-grounding",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    report_hash = sha256(REPORT_PATH)
    with WORK_PATH.open("r", encoding="utf-8") as handle:
        work = json.load(handle)

    by_id = {candidate["id"]: candidate for candidate in work["candidates"]}
    missing = [candidate_id for candidate_id in CANDIDATE_IDS if candidate_id not in by_id]
    if missing:
        raise SystemExit(f"missing candidates: {missing}")

    observation = report["remote_observation"]
    progress = report["m197_live_progress"]
    latest = (
        f"{report['timestamp']}: the due retry again found M197-PIRS pid"
        f"{observation['processes'][0]['pid']} "
        f"({observation['processes'][0]['used_mib']} MiB) plus foreign pid"
        f"{observation['processes'][1]['pid']} "
        f"({observation['processes'][1]['used_mib']} MiB) on server-6 GPU7. "
        "The two-process cap remained closed, so no native capture or training launched. "
        f"M197 native progress advanced from step {progress['previous_observed_step']} to "
        f"step {progress['native_step']}; preflight reported best 0.4803 and "
        "no_improve 1/10. The previously skipped remote CPU-only contrast suite passed "
        "5/5 tests. Fresh evidence: "
        f"pipeline/reports/{REPORT_PATH.name} sha256={report_hash}."
    )
    evidence_entry = {
        "path": f"pipeline/reports/{REPORT_PATH.name}",
        "sha256": report_hash,
    }
    capacity_progress = {
        "timestamp": report["timestamp"],
        "report": evidence_entry["path"],
        "report_sha256": report_hash,
        "gpu_process_count": len(observation["processes"]),
        "gpu_free_mib": observation["free_mib"],
        "native_step": progress["native_step"],
        "cpu_contrast_tests_passed": report["cpu_validation"]["tests_passed"],
        "native_execution_completed": False,
        "finding": (
            "Due retry remained gated by M197-PIRS and foreign pid3827570; M197 "
            "advanced to step 3760/4686, and the previously skipped CPU-only "
            "native-feature-contrast suite passed 5/5."
        ),
        "retry_after": report["blocker"]["retry_after"],
    }

    for candidate_id in CANDIDATE_IDS:
        candidate = by_id[candidate_id]
        if candidate.get("stage") != "blocked":
            raise SystemExit(
                f"{candidate_id}: expected blocked, found {candidate.get('stage')!r}"
            )
        candidate["blocker"] = report["blocker"]["blocker"]
        candidate["retry_after"] = report["blocker"]["retry_after"]
        candidate["unblock_condition"] = report["blocker"]["unblock_condition"]
        candidate["latest_progress"] = latest
        candidate["capacity_retry_progress"] = capacity_progress
        evidence = candidate.setdefault("evidence", [])
        if evidence_entry not in evidence:
            evidence.append(evidence_entry)

    temp_path = WORK_PATH.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(work, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temp_path, WORK_PATH)

    with WORK_PATH.open("r", encoding="utf-8") as handle:
        verified = json.load(handle)
    verified_ids = {candidate["id"] for candidate in verified["candidates"]}
    if not set(CANDIDATE_IDS).issubset(verified_ids):
        raise SystemExit("post-write validation did not find every due candidate")

    print(
        json.dumps(
            {
                "report": evidence_entry,
                "updated_candidates": CANDIDATE_IDS,
                "work_candidates": len(verified["candidates"]),
                "post_write_validation": "ok",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
