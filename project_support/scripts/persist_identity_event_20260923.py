"""Persist completed shared validation without touching training state."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATHS = [
    "pipeline/reports/m95_capture_provenance_20260923-0012.json",
    "pipeline/reports/m95_manifest_identity_analysis_20260923-0012.json",
    "pipeline/reports/m95_identity_handoff_20260923-0020.json",
    "scripts/m95_identity_handoff_20260923.py",
    "scripts/test_m95_identity_handoff_20260923.py",
    "pipeline/decisions/20260923-001844_route_change.md",
]
ACTIONS = {
    "referent-supervision-axis": (
        "Using the completed 256-row analysis, enumerate the 40 deployed failures "
        "with an acceptable query and partition native-positive eligibility versus "
        "score rank. Test whether a distinct supervision unit is evidenced without "
        "reopening PIRS, generic ranking, or mask-aware matching. Remain diagnosis "
        "until a nonduplicate mechanism is specified; no admission from oracle uplift."
    ),
    "referent-causality-audit": (
        "Audit registered pair membership against target-positive and dominant-peer "
        "overlap in the existing 65 pairs, then compare the 243 common-support rows "
        "by exact selected query ID. Quantify target-informed control overlap and "
        "eligibility selection; do not call oracle contrast deployable causality "
        "or native-positive-specific benefit."
    ),
    "modality-identity-preservation": (
        "Use existing 250 hash-bound feature shards on server-6 CPU to compare "
        "stage margins for deployed wrong versus acceptable target queries in the "
        "40 selection failures, with self-overlap explicitly reported. No new "
        "capture or modality-fusion mechanism; current target-positive margins "
        "do not establish modality identity destruction."
    ),
    "referent-discrimination": (
        "On the existing 40 recoverable selection failures, use frozen manifest "
        "target/peer IDs and deployed dominant-instance IDs to tabulate same-class, "
        "cross-class, no-instance and mixed-support errors with denominators. "
        "Keep 16 no-acceptable cases separate; do not propose a class selector."
    ),
    "instance-identity-representation": (
        "Audit existing frozen query masks and feature shards for whether deployed "
        "wrong-query identity margins differ from acceptable-query margins on "
        "matched scenes. Report prototype-mask self-overlap and missingness before "
        "any identity-representation mechanism; no new GPU capture is needed."
    ),
}


def main():
    now = datetime.now().astimezone().isoformat()
    evidence = [
        {"path": p, "sha256": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
        for p in PATHS
    ]
    analysis = json.loads((ROOT / PATHS[1]).read_text(encoding="utf-8"))
    handoff = json.loads((ROOT / PATHS[2]).read_text(encoding="utf-8"))
    progress = {
        "contract": "m95_identity_event_resolution_v1",
        "generated_at": now,
        "mode": "event",
        "native_capture_completed": True,
        "registered_analysis_completed": True,
        "candidate_admission": False,
        "queue_mutation": False,
        "new_gpu_launch": False,
        "tests": {"frozen_analyzer_passed": 7, "descriptive_handoff_passed": 3},
        "gpu_observation": {
            "server": "server-6", "gpu": 7, "utilization_percent": 100,
            "memory_used_mib": 42025, "memory_total_mib": 81559,
            "capture_pid_1578754_present": False, "foreign_jobs_touched": False,
        },
        "registered_primary": analysis["summary"]["primary_estimand"],
        "descriptive": handoff["descriptive"],
        "limitations": handoff["limitations"],
        "provenance_note": (
            "Initial orchestration assertion compared entry and composite producer "
            "hashes. Source inspection resolved field semantics; all eight "
            "local/remote dependencies match, and unchanged analyzer succeeded."
        ),
        "pending_questions_24h": [],
        "candidate_next_actions": ACTIONS,
        "evidence": evidence,
    }
    report = ROOT / "pipeline/reports/m95_identity_event_resolution_20260923-0020.json"
    with report.open("x", encoding="utf-8") as handle:
        json.dump(progress, handle, indent=2)
        handle.write("\n")
    evidence.append({
        "path": report.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
    })
    work_path = ROOT / "pipeline/research_work.json"
    work = json.loads(work_path.read_text(encoding="utf-8"))
    changed = []
    for candidate in work["candidates"]:
        if candidate["id"] not in ACTIONS:
            continue
        candidate.update(
            stage="diagnosis", next_action=ACTIONS[candidate["id"]],
            blocker=None, retry_after=None, unblock_condition=None,
            latest_progress=report.relative_to(ROOT).as_posix(),
        )
        candidate["identity_validation_completed_20260923"] = {
            "report": evidence[-1]["path"], "report_sha256": evidence[-1]["sha256"],
            "timestamp": now, "registered_primary_passed": True,
            "admission": False, "stage": "diagnosis",
        }
        candidate["identity_capture_progress"].update(
            state="completed", capture_json_present=True, last_step=4663,
            last_expressions=256, native_capture_completed=True,
        )
        existing = {item["path"] for item in candidate["evidence"]}
        candidate["evidence"].extend(item for item in evidence if item["path"] not in existing)
        changed.append(candidate["id"])
    assert set(changed) == set(ACTIONS)
    work["updated_at"] = now
    work["last_event_tick"] = {
        "timestamp": now, "report": evidence[-1]["path"],
        "sha256": evidence[-1]["sha256"], "candidate_ids": changed,
    }
    work["next_action"] = (
        "Resume five bounded diagnosis actions from the completed frozen capture. "
        "No repeat capture, automatic training, or admission; retain registered "
        "oracle gate and common-support confound together."
    )
    work_path.write_text(json.dumps(work, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"updated_candidates": changed, "evidence": evidence}, indent=2))


if __name__ == "__main__":
    main()
