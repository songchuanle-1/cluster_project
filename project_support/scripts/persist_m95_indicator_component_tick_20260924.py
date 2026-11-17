"""Persist the indicator-control extension under the existing blocked IDs."""

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "pipeline/research_work.json"
DUE = {
    "referent-supervision-axis",
    "referent-discrimination",
    "instance-identity-representation",
}
PATHS = (
    "scripts/m95_score_component_control_20260924.py",
    "scripts/test_m95_score_component_control_20260924.py",
    "pipeline/reports/m95_indicator_component_control_20260924-2111.md",
    "pipeline/decisions/20260924-211303_route_change.md",
)


def reference(path):
    return {
        "path": path,
        "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
    }


def main():
    context = json.loads(
        (ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8")
    )
    if context["mode"] != "design" or set(context["research_work"]["due_ids"]) != DUE:
        raise ValueError("Unexpected preflight")

    original = WORK.read_bytes()
    queue_hash = reference("pipeline/queue.json")["sha256"]
    work = json.loads(original)
    refs = [reference(path) for path in PATHS]
    now = datetime.now().astimezone()
    found = set()

    for candidate in work["candidates"]:
        if candidate["id"] not in DUE:
            continue
        if candidate["stage"] != "blocked":
            raise ValueError("Unexpected due stage")
        found.add(candidate["id"])
        for ref in refs:
            matches = [
                item for item in candidate.setdefault("evidence", [])
                if item.get("path") == ref["path"]
            ]
            if matches:
                for item in matches:
                    item["sha256"] = ref["sha256"]
            else:
                candidate["evidence"].append(ref)
        candidate["indicator_component_control_20260924"] = {
            "timestamp": now.isoformat(),
            "checker": refs[0],
            "test": refs[1],
            "report": refs[2],
            "decision": refs[3],
            "focused_tests_passed": 22,
            "indicator_loss_available_from_frozen_probabilities": True,
            "native_capture_required": True,
            "native_execution_completed": False,
            "admission": False,
        }
        candidate["blocker"] = (
            "Read-only authorized GPU7 query at 2026-09-24 21:07 +08:00: "
            "external PID 3694608 uses 41,996 MiB; 42,023 MiB used, "
            "39,536 MiB free; 100% utilization."
        )
        candidate["retry_after"] = (now + timedelta(minutes=20)).isoformat()
        candidate["unblock_condition"] = (
            "Authorized GPU7 clears; verify SSH, code/runtime/data, frozen "
            "checkpoint and producer provenance, and actual occupancy/memory."
        )
        candidate["alternatives_attempted"] = (
            "One read-only authorized GPU7 query; exact offline score and "
            "indicator component controls with 22 focused synthetic tests. "
            "No native artifact or execution."
        )
        candidate["next_action"] = (
            "On GPU7 clearance and provenance checks, run one ordered 256-row "
            "native TRAIN capture including matcher causes, query states and "
            "frozen scores; audit binding/collisions and replay mask BCE/Dice, "
            "score MSE and indicator CE separately. Measure native backward and "
            "resources before admission."
        )

    if found != DUE:
        raise ValueError("Missing due IDs")
    work["design_cycle"] = {
        "timestamp": now.isoformat(),
        "stop_reason": "external_resource_blocked",
        "attempted_ids": sorted(DUE),
        "evidence": refs,
        "resume_condition": (
            "At or after retry_after, recheck authorized GPU7; on clearance "
            "verify provenance, run ordered capture and component controls, "
            "then evaluate every hard gate. No admission or dispatch before PASS."
        ),
    }
    work["updated_at"] = now.isoformat()
    work["last_event_tick"] = now.isoformat()
    work["next_action"] = (
        "Run the ordered 256-row native capture when GPU7 and runtime gates pass; "
        "evaluate mask, score and indicator controls before admission."
    )

    if WORK.read_bytes() != original or reference("pipeline/queue.json")["sha256"] != queue_hash:
        raise ValueError("Concurrent research or queue change")
    temporary = WORK.with_suffix(".indicator_component.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    os.replace(temporary, WORK)
    print(json.dumps({"due_ids": sorted(found), "queue_sha256": queue_hash}))


if __name__ == "__main__":
    main()
