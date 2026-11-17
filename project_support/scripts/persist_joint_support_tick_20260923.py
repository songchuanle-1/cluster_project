"""Persist event progress without changing the queue or training state."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_joint_support_20260923-0915.json"
SCREEN = "pipeline/reports/m95_supervision_unit_screen_20260923-0915.md"
DECISION = "pipeline/decisions/20260923-091759_route_change.md"
RESOLUTION = "pipeline/reports/m95_joint_support_resolution_20260923-0915.json"
NEXT = {
    "referent-supervision-axis": (
        "SET-MASS rejected as generic listwise relabeling. Next audit exact duplicate-mask "
        "equivalence classes and native-positive label discordance within existing40 "
        "failure shards; report query versus unique-mask denominators. Share implementation "
        "with identity axis. Diagnosis only: no capture, deduplication mechanism, selector, "
        "weighting, ranking or training."
    ),
    "modality-identity-preservation": (
        "Joint-disjoint support complete:16/40 scenes available. On these exact16 saved "
        "report rows, tabulate deployed/acceptable shared-prototype margin signs and "
        "paired changes raw_3d to fused to final, with scene denominators and uncertainty. "
        "Do not infer causal modality damage or create a modality-loss variant."
    ),
    "referent-discrimination": (
        "Object8 scene0245_00 remains unknown after physical-ID alignment and absent "
        "object-aligned annotations/graphs; do not repeat lookup or conflate graph node_id "
        "with object_id. In shared exact-mask audit stratify label discordance by "
        "target-dominant, registered-peer, outside-peer identity; retain unknown semantics."
    ),
    "instance-identity-representation": (
        "Joint-disjoint inventory complete; do not duplicate it. Share one exact-mask "
        "equivalence audit with supervision axis on existing40: identical masks with "
        "distinct seeds/native-positive labels, physical query axes, scene denominators "
        "and missingness. No deduplication selector or representation-collapse claim."
    ),
}


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def evidence(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    context, report = load("pipeline/headless/.tick_context.json"), load(REPORT)
    assert context["mode"] == "event"
    assert set(context["research_work"]["due_ids"]) == set(NEXT)
    assert report["host"] == "das" and report["cpu_only"] and not report["admission"]
    assert not report["native_backward_executed"] and not report["model_forward_executed"]
    assert report["summary"]["expressions"] == report["summary"]["scenes"] == 40
    assert report["summary"]["support_feasible"] == 16
    assert len(report["feature_shards"]) == 250
    assert evidence(REPORT)["sha256"] == "8e3a543a9064f9bdf394bef4e71ff7fe70d2b637e132381ca26f0b0999f14614"
    assert report["evidence"][-1]["sha256"] == evidence("scripts/m95_joint_support_20260923.py")["sha256"]
    assert report["semantic_resolution"]["wrong_annotation_count"] == 0
    sources = [REPORT, SCREEN, DECISION, "scripts/m95_joint_support_20260923.py",
               "scripts/test_m95_joint_support_20260923.py",
               "scripts/persist_joint_support_tick_20260923.py"]
    now = datetime.now().astimezone().isoformat()
    record = {
        "contract": "m95_joint_support_event_resolution_v1", "generated_at": now,
        "context_generated_at": context["generated_at"], "mode": "event",
        "gpu_observation": {
            "server": "server-6", "gpu": 7, "utilization_percent": 100,
            "memory_used_mib": 42025, "memory_total_mib": 81559,
            "foreign_jobs_touched": False, "ssh_code_environment_data_verified": True,
        },
        "tests": {"local_synthetic": 15, "server6_cpu_synthetic": 15, "failed": 0},
        "summary": report["summary"], "semantic_resolution": report["semantic_resolution"],
        "native_cpu_analysis_completed": True, "native_backward_executed": False,
        "model_forward_executed": False, "candidate_admission": False, "queue_mutation": False,
        "supervision_unit_screen": {
            "unit": "SET-MASS", "disposition": "rejected_before_implementation",
            "reason": "Generic listwise acceptable-mask relabeling; no new information flow.",
            "primary_supervision_axis_remains_open": True, "literature_novelty_claim": False,
        },
        "candidate_next_actions": NEXT,
        "pending_questions_24h": context["manifests"]["pending_questions_24h"],
        "limitations": report["limitations"], "evidence": [evidence(p) for p in sources],
    }
    work = load("pipeline/research_work.json")
    assert {c["id"] for c in work["candidates"] if c["id"] in NEXT} == set(NEXT)
    with (ROOT / RESOLUTION).open("x", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    refs = [evidence(p) for p in sources + [RESOLUTION]]
    for candidate in work["candidates"]:
        if candidate["id"] not in NEXT:
            continue
        candidate["stage"] = "diagnosis"
        candidate["next_action"] = NEXT[candidate["id"]]
        candidate["blocker"] = candidate["retry_after"] = candidate["unblock_condition"] = None
        candidate["joint_support_completed_20260923"] = {
            "timestamp": now, "report": evidence(REPORT), "screen": evidence(SCREEN),
            "resolution": evidence(RESOLUTION), "native_cpu_analysis_completed": True,
            "admission": False, "native_backward_executed": False,
        }
        existing = {e["path"]: e["sha256"] for e in candidate["evidence"]}
        for ref in refs:
            if ref["path"] in existing:
                assert ref["sha256"] == existing[ref["path"]], "Existing evidence changed"
            else:
                candidate["evidence"].append(ref)
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = (
        "Joint support and object-ID checks complete; SET-MASS rejected. Share bounded "
        "exact-mask label audit across supervision/identity/discrimination, and saved16 "
        "descriptive stage-sign audit. No candidate admission."
    )
    target = ROOT / "pipeline/research_work.json"
    temporary = target.with_suffix(".joint-support.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(target)
    print(json.dumps({"resolution": evidence(RESOLUTION), "updated_ids": list(NEXT)}))


if __name__ == "__main__":
    main()
