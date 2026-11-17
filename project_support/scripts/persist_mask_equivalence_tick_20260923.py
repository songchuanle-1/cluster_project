"""Persist verified event evidence without touching training or queue state."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_mask_equivalence_20260923-1010.json"
DECISION = "pipeline/decisions/20260923-101523_route_change.md"
RESOLUTION = "pipeline/reports/m95_mask_equivalence_resolution_20260923-1010.json"
NEXT = {
    "referent-supervision-axis": (
        "On saved32 exact-mask label-discordant classes, compare captured mask logits "
        "and indicator scores within class and audit native-positive seed membership. "
        "Report all32 and acceptable23 class denominators with scene uncertainty. Bind "
        "the label rule to frozen criterion source before calling labels erroneous. "
        "Share one audit with identity/discrimination; no new capture, ranking or deduplication."
    ),
    "modality-identity-preservation": (
        "Bounded saved-support modality diagnostic complete: acceptable final margins "
        "positive16/16 and raw3D-to-final paired CI includes zero. No modality-damage or "
        "preservation-mechanism claim. Do not repeat stage-sign audits or create a modality "
        "loss; reopen only on new independently controlled causal evidence."
    ),
    "referent-discrimination": (
        "In shared saved32-class provenance audit retain target26/peer5/outside1 strata, "
        "physical IDs and unknown semantics. Determine whether label discordance coincides "
        "with seed target membership, without assuming outside-peer is cross-class. "
        "Do not repeat object8 lookup or propose a selector."
    ),
    "instance-identity-representation": (
        "Share supervision's saved32-class logit/provenance audit. Identical thresholded "
        "masks are not identical logits or decoder states: quantify captured mask-logit "
        "differences and mark uncaptured query-state comparisons unavailable. "
        "No collapse claim, deduplication mechanism, new capture or identity loss."
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
    assert evidence(REPORT)["sha256"] == "6a219bd48f5cc28bd56e437280fc6336e9834253c8d9fa6848502e8ab66b6790"
    assert report["host"] == "das" and report["cpu_only"] and not report["admission"]
    assert not report["native_backward_executed"] and not report["model_forward_executed"]
    assert report["summary"]["expressions"] == report["summary"]["scenes"] == 40
    assert report["summary"]["discordant_class_count"] == 32
    assert report["stage_transitions"]["available"] == report["stage_transitions"]["scenes"] == 16
    assert len(report["feature_shards"]) == 250
    assert report["evidence"][-1]["sha256"] == evidence("scripts/m95_mask_equivalence_20260923.py")["sha256"]
    assert evidence("scripts/test_m95_mask_equivalence_20260923.py")["sha256"] == "8aa8ca45eacb2eb45728a2d0a09b9fa4f94af9b9bbf4e362723d11591b41a8bc"
    sources = [REPORT, DECISION, "scripts/m95_mask_equivalence_20260923.py",
               "scripts/test_m95_mask_equivalence_20260923.py",
               "scripts/persist_mask_equivalence_tick_20260923.py"]
    now = datetime.now().astimezone().isoformat()
    stages = {cid: "complete" if cid == "modality-identity-preservation" else "diagnosis"
              for cid in NEXT}
    record = {
        "contract": "m95_mask_equivalence_event_resolution_v1",
        "generated_at": now, "context_generated_at": context["generated_at"], "mode": "event",
        "gpu_observation": {
            "server": "server-6", "gpu": 7, "utilization_percent": 0,
            "memory_used_mib": 42025, "memory_total_mib": 81559,
            "foreign_jobs_touched": False, "ssh_code_environment_data_verified": True,
        },
        "tests": {"local_synthetic": 16, "server6_cpu_synthetic": 16,
                  "local_prior_joint_support_regression": 15, "failed": 0},
        "summary": report["summary"],
        "stage_transitions": {k: v for k, v in report["stage_transitions"].items() if k != "rows"},
        "native_cpu_analysis_completed": True, "native_backward_executed": False,
        "model_forward_executed": False, "candidate_admission": False, "queue_mutation": False,
        "candidate_stages": stages, "candidate_next_actions": NEXT,
        "pending_questions_24h": context["manifests"]["pending_questions_24h"],
        "new_research_question": "Does binary-mask label discordance persist at logits, or follow native seed ownership?",
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
        candidate["stage"] = stages[candidate["id"]]
        candidate["next_action"] = NEXT[candidate["id"]]
        candidate["blocker"] = candidate["retry_after"] = candidate["unblock_condition"] = None
        candidate["mask_equivalence_completed_20260923"] = {
            "timestamp": now, "report": evidence(REPORT), "resolution": evidence(RESOLUTION),
            "native_cpu_analysis_completed": True, "admission": False,
            "native_backward_executed": False,
        }
        existing = {e["path"]: e["sha256"] for e in candidate["evidence"]}
        for ref in refs:
            if ref["path"] in existing:
                assert ref["sha256"] == existing[ref["path"]], "Existing evidence changed"
            else:
                candidate["evidence"].append(ref)
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = (
        "Modality diagnostic complete without a mechanism. Three diagnosis IDs share one "
        "saved32-class logit/label provenance audit; preserve goal gates and empty queue."
    )
    target = ROOT / "pipeline/research_work.json"
    temporary = target.with_suffix(".mask-equivalence.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(target)
    print(json.dumps({"resolution": evidence(RESOLUTION), "candidate_stages": stages}))


if __name__ == "__main__":
    main()
