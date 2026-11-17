"""Persist one shared bounded diagnosis without changing queue or training."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_discordance_provenance_20260923-1107.json"
RESOLUTION = "pipeline/reports/m95_discordance_resolution_20260923-1107.json"
DECISION = "pipeline/decisions/20260923-111459_route_change.md"
IDS = (
    "referent-supervision-axis",
    "referent-discrimination",
    "instance-identity-representation",
)
NEXT = {
    IDS[0]: (
        "Check whether saved native geometry and target centroid permit exact replay of "
        "the criterion's nearest-GT assignment for six positive-outside-target-seed "
        "classes (three acceptable). If unavailable, record the missing cause tag and "
        "test a distinct supervision unit only after matched controls and admission gates."
    ),
    IDS[1]: (
        "Use the same six class IDs to separate nearest-GT from sampled-instance "
        "membership if frozen coordinates permit; retain target26/peer5/outside1 "
        "physical strata. Do not infer outside-peer class or add a selector."
    ),
    IDS[2]: (
        "Saved32 classes all have different mask logits despite identical binary masks. "
        "Keep diagnosis open only for a falsifiable representation-level mechanism "
        "with an independently captured query-state control; do not infer collapse, "
        "deduplicate queries or launch a new capture from this descriptive audit."
    ),
}


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def ref(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    context, report, work = (
        load("pipeline/headless/.tick_context.json"), load(REPORT),
        load("pipeline/research_work.json"),
    )
    assert context["mode"] == "event" and set(context["research_work"]["due_ids"]) == set(IDS)
    assert ref(REPORT)["sha256"] == "6ed69abe4d26a2bd20283bb59119c2ebf30d4c0e73e2252903c210925292e372"
    assert report["host"] == "das" and report["cpu_only"] and not report["admission"]
    assert not report["model_forward_executed"] and not report["native_backward_executed"]
    assert report["summary"]["all"]["classes"] == 32
    assert report["summary"]["acceptable"]["classes"] == 23
    assert report["summary"]["all"]["metrics"]["logits_differ"]["classes"] == 32
    assert report["summary"]["all"]["metrics"]["positive_outside_seed"]["classes"] == 6
    assert report["summary"]["acceptable"]["metrics"]["positive_outside_seed"]["classes"] == 3
    assert report["evidence"][-1]["sha256"] == ref(
        "scripts/m95_discordance_provenance_20260923.py"
    )["sha256"]
    assert {c["id"] for c in work["candidates"] if c["id"] in IDS} == set(IDS)
    now = datetime.now().astimezone().isoformat()
    sources = [REPORT, DECISION, "scripts/m95_discordance_provenance_20260923.py",
               "scripts/test_m95_discordance_provenance_20260923.py",
               "scripts/persist_discordance_tick_20260923.py"]
    resolution = {
        "contract": "m95_saved_discordance_event_resolution_v1",
        "generated_at": now,
        "context_generated_at": context["generated_at"],
        "mode": "event",
        "summary": report["summary"],
        "tests": {"local_synthetic": 7, "server6_cpu_synthetic": 7, "failed": 0},
        "candidate_stages": dict.fromkeys(IDS, "diagnosis"),
        "candidate_next_actions": NEXT,
        "native_cpu_analysis_completed": True,
        "native_backward_executed": False,
        "model_forward_executed": False,
        "candidate_admission": False,
        "queue_mutation": False,
        "pending_questions_24h": context["manifests"]["pending_questions_24h"],
        "new_research_question": (
            "Can the six positive-outside-target-seed classes be attributed to "
            "nearest-GT assignment with saved geometry?"
        ),
        "limitations": report["limitations"],
        "evidence": [ref(p) for p in sources],
    }
    with (ROOT / RESOLUTION).open("x", encoding="utf-8") as handle:
        json.dump(resolution, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    refs = [ref(p) for p in sources + [RESOLUTION]]
    for candidate in work["candidates"]:
        if candidate["id"] not in IDS:
            continue
        candidate["stage"] = "diagnosis"
        candidate["next_action"] = NEXT[candidate["id"]]
        candidate["blocker"] = candidate["retry_after"] = candidate["unblock_condition"] = None
        candidate["discordance_provenance_completed_20260923"] = {
            "timestamp": now, "report": ref(REPORT), "resolution": ref(RESOLUTION),
            "native_cpu_analysis_completed": True, "admission": False,
            "native_backward_executed": False,
        }
        existing = {e["path"]: e["sha256"] for e in candidate["evidence"]}
        for item in refs:
            if item["path"] in existing:
                assert item["sha256"] == existing[item["path"]]
            else:
                candidate["evidence"].append(item)
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = (
        "Three diagnosis IDs share a bounded six-class nearest-GT provenance check "
        "only if saved geometry suffices; no new capture or admission from binary masks."
    )
    target = ROOT / "pipeline/research_work.json"
    temporary = target.with_suffix(".discordance.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(target)
    print(json.dumps({"resolution": ref(RESOLUTION), "stages": resolution["candidate_stages"]}))


if __name__ == "__main__":
    main()
