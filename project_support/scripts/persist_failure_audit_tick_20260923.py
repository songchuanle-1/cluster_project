"""Persist completed descriptive audit without changing queue or admission."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_failure_partition_20260923-0318.json"
DECISION = "pipeline/decisions/20260923-032233_route_change.md"
RESOLUTION = "pipeline/reports/m95_failure_audit_resolution_20260923-0323.json"
NEXT = {
    "referent-supervision-axis": (
        "Use six positive-set exclusion rows and seven within-positive score failures "
        "from the partition report. Cross-tabulate eligibility, dominant identity and "
        "target-mask support against the frozen supervision contract; distinguish "
        "target-seed sampling from mask-support mismatch. No ranking successor, "
        "positive-set relabeling or admission without a distinct supervision unit."
    ),
    "referent-causality-audit": (
        "Decompose registered contrast by nine peer-dominant positives and one "
        "also-positive negative, keeping the original 65-pair primary unchanged. "
        "Enumerate two discordant selectors and 13 missing seed controls. Report "
        "scene denominators and selection; filtered contrasts are descriptive."
    ),
    "modality-identity-preservation": (
        "Compare overlapping and query-excluded margins on the SAME 16 complete "
        "rows; tabulate reasons for 24 missing rows using existing masks and peers. "
        "Do not compare unmatched 36-row and 16-row means as self-overlap effects "
        "or infer modality damage from cross-stage cosine differences. No new capture."
    ),
    "referent-discrimination": (
        "Resolve three recoverable outside-target-and-peer dominant IDs using "
        "existing native scene annotations on server-6 CPU. Cross-tabulate 30 "
        "peer-dominant and seven target-dominant errors with 24 mixed-support masks "
        "and failure partitions. Keep 16 coverage failures separate; no class selector."
    ),
    "instance-identity-representation": (
        "Tabulate prototype-mask overlap for the 40 recoverable failures, including "
        "seven exact target-union masks. Audit identity separation on the 16 complete "
        "query-excluded pairs with same-support comparisons, missingness and scene "
        "uncertainty. Existing shards only; no identity-loss or causality claim."
    ),
}


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def evidence(relative):
    return {"path": relative, "sha256": hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()}


def main():
    context = load("pipeline/headless/.tick_context.json")
    result = load(REPORT)
    assert context["mode"] == "event"
    assert set(context["research_work"]["due_ids"]) == set(NEXT)
    assert result["cpu_only"] and result["admission"] is False
    assert result["summary"]["expressions"] == 256
    assert len(result["feature_shards"]) == 250
    assert result["summary"]["features"]["rows"] == 40
    sources = [
        REPORT, DECISION, "scripts/m95_failure_partition_20260923.py",
        "scripts/test_m95_failure_partition_20260923.py",
        "scripts/analyze_m95_manifest_identity_controls_20260922.py",
        "scripts/persist_failure_audit_tick_20260923.py",
    ]
    now = datetime.now().astimezone().isoformat()
    resolution = {
        "contract": "m95_failure_audit_event_resolution_v1", "generated_at": now,
        "mode": "event", "recovered_previous_tick_implementation": True,
        "native_cpu_analysis_completed": True, "new_gpu_capture": False,
        "candidate_admission": False, "queue_mutation": False,
        "gpu_observation": {
            "server": "server-6", "gpu": 7, "utilization_percent": 0,
            "memory_used_mib": 42025, "memory_total_mib": 81559,
            "foreign_jobs_touched": False,
        },
        "tests": {"local_audit": 8, "remote_audit": 8, "local_regression": 10},
        "summary": result["summary"], "limitations": result["limitations"],
        "candidate_next_actions": NEXT,
        "pending_questions_24h": context["manifests"]["pending_questions_24h"],
        "evidence": [evidence(path) for path in sources],
    }
    with (ROOT / RESOLUTION).open("x", encoding="utf-8") as handle:
        json.dump(resolution, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    work = load("pipeline/research_work.json")
    for candidate in work["candidates"]:
        if candidate["id"] not in NEXT:
            continue
        candidate["stage"] = "diagnosis"
        candidate["next_action"] = NEXT[candidate["id"]]
        candidate["blocker"] = None
        candidate["retry_after"] = None
        candidate["unblock_condition"] = None
        candidate["failure_partition_completed_20260923"] = {
            "report": REPORT, "report_sha256": evidence(REPORT)["sha256"],
            "resolution": RESOLUTION, "timestamp": now, "admission": False,
            "native_cpu_analysis_completed": True,
        }
        existing = {item["path"] for item in candidate["evidence"]}
        candidate["evidence"].extend(
            evidence(path) for path in sources + [RESOLUTION] if path not in existing
        )
    work["updated_at"] = now
    work["last_event_tick"] = now
    work["next_action"] = (
        "Resume per-ID follow-ups from completed failure audit; no admission, "
        "new capture, or duplicate review."
    )
    (ROOT / "pipeline/research_work.json").write_text(
        json.dumps(work, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"resolution": evidence(RESOLUTION), "updated_ids": list(NEXT)}))


if __name__ == "__main__":
    main()
