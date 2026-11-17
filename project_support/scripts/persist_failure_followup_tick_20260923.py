"""Recover completed follow-up and persist bounded evidence, without queue edits."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLLOWUP = "pipeline/reports/m95_failure_followup_20260923-0540.json"
DIRECTION = "pipeline/reports/m95_supervision_direction_20260923-0815.json"
DECISION = "pipeline/decisions/20260923-081158_route_change.md"
RESOLUTION = "pipeline/reports/m95_followup_event_resolution_20260923-0815.json"
NEXT = {
    "referent-supervision-axis": (
        "Use six exclusion and seven within-positive scenes to specify one supervision "
        "unit distinct from generic mask-aware matching, ranking, PIRS and rejected "
        "referent-supervision-unit. State input/target/gradient ownership and matched "
        "control; reject before implementation if equivalent to closed routes. "
        "Current analytic derivatives do not satisfy native backward."
    ),
    "referent-causality-audit": (
        "Bounded audit complete: preserve original 65-pair endpoint and descriptive "
        "subgroups, two discordant selectors and 13 missing controls. No repeated "
        "audit or causal-specificity claim; reopen only for an explicitly new "
        "estimand or changed source evidence, not queue capacity."
    ),
    "modality-identity-preservation": (
        "Statically specify shared target/peer prototype support excluding BOTH "
        "compared query masks, including empty-support and zero-norm rejection. "
        "Test synthetic masks before auditing the existing 40-row shard inventory. "
        "Do not repeat individual-query exclusion or claim modality damage."
    ),
    "referent-discrimination": (
        "Resolve only scene0245_00 object8 using already-hashed native scene graph "
        "and physical-label metadata on server-6 CPU; ScanRefer descriptions lack "
        "its class. Require object-ID alignment; retain unknown if absent. "
        "Couch/sofachair string differences are not an ontology result."
    ),
    "instance-identity-representation": (
        "Share the modality axis's single disjoint-support feasibility contract, "
        "not a duplicate implementation. Quantify target/peer support remaining "
        "after the union of deployed and acceptable masks on 40 saved failures, "
        "with structural missingness and scene denominators. No new capture."
    ),
}


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def evidence(relative):
    return {"path": relative, "sha256": hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()}


def main():
    context = load("pipeline/headless/.tick_context.json")
    followup, direction = load(FOLLOWUP), load(DIRECTION)
    assert context["mode"] == "event"
    assert set(context["research_work"]["due_ids"]) == set(NEXT)
    assert evidence(FOLLOWUP)["sha256"] == "444aa9c8af032709010e8f4f148ce42ec5020eb9b94d7a2663f857e4d7418132"
    assert followup["host"] == direction["host"] == "das"
    assert followup["cpu_only"] and direction["cpu_only"]
    assert followup["admission"] is direction["admission"] is False
    assert len(followup["feature_shards"]) == 250
    assert direction["expressions"] == direction["scenes"] == 13
    assert followup["summary"]["registered_pairs"]["original_unchanged"]["available"] == 65
    assert direction["analytic_contract"]["native_backward_executed"] is False
    assert direction["evidence"][-1]["sha256"] == evidence("scripts/m95_supervision_direction_20260923.py")["sha256"]
    sources = [
        FOLLOWUP, DIRECTION, DECISION,
        "pipeline/decisions/20260923-053555_route_change.md",
        "scripts/m95_failure_followup_20260923.py",
        "scripts/test_m95_failure_followup_20260923.py",
        "scripts/m95_supervision_direction_20260923.py",
        "scripts/test_m95_supervision_direction_20260923.py",
        "scripts/persist_failure_followup_tick_20260923.py",
    ]
    now = datetime.now().astimezone().isoformat()
    record = {
        "contract": "m95_followup_event_resolution_v1", "generated_at": now,
        "context_generated_at": context["generated_at"], "mode": "event",
        "recovered_previous_tick_artifact": FOLLOWUP, "new_native_cpu_analysis": DIRECTION,
        "gpu_observation": {
            "server": "server-6", "gpu": 7, "utilization_percent": 0,
            "memory_used_mib": 42025, "memory_total_mib": 81559,
            "observation_scope": "one read-only observation this tick",
            "foreign_jobs_touched": False,
        },
        "tests": {"local": 28, "server6_cpu": 28, "failed": 0},
        "summary": followup["summary"],
        "supervision_direction_groups": direction["groups"],
        "limitations": followup["limitations"] + direction["limitations"],
        "candidate_next_actions": NEXT, "completed_ids": ["referent-causality-audit"],
        "pending_questions_24h": context["manifests"]["pending_questions_24h"],
        "candidate_admission": False, "queue_mutation": False,
        "model_forward_executed": False, "native_backward_executed": False,
        "evidence": [evidence(path) for path in sources],
    }
    work = load("pipeline/research_work.json")
    assert {c["id"] for c in work["candidates"] if c["id"] in NEXT} == set(NEXT)
    with (ROOT / RESOLUTION).open("x", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    refs = [evidence(path) for path in sources + [RESOLUTION]]
    for candidate in work["candidates"]:
        if candidate["id"] not in NEXT:
            continue
        candidate["stage"] = "complete" if candidate["id"] == "referent-causality-audit" else "diagnosis"
        candidate["next_action"] = NEXT[candidate["id"]]
        candidate["blocker"] = candidate["retry_after"] = candidate["unblock_condition"] = None
        candidate["failure_followup_completed_20260923"] = {
            "timestamp": now, "report": evidence(FOLLOWUP),
            "direction": evidence(DIRECTION), "resolution": evidence(RESOLUTION),
            "admission": False, "native_cpu_analysis_completed": True,
            "native_backward_executed": False,
        }
        existing = {item["path"]: item["sha256"] for item in candidate["evidence"]}
        for ref in refs:
            if ref["path"] in existing:
                assert existing[ref["path"]] == ref["sha256"], "Existing evidence changed"
            else:
                candidate["evidence"].append(ref)
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = (
        "Bounded pair audit complete; four diagnosis axes have finite distinct "
        "next actions. No training candidate admitted; capacity remains empty."
    )
    target = ROOT / "pipeline/research_work.json"
    temporary = target.with_suffix(".recovery.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(target)
    print(json.dumps({"resolution": evidence(RESOLUTION), "updated_ids": list(NEXT)}))


if __name__ == "__main__":
    main()
