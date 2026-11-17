"""Persist the bounded same-forward control and external-resource blocker."""

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
    "scripts/m95_mask_component_counterfactual_20260924.py",
    "scripts/test_m95_mask_component_counterfactual_20260924.py",
    "pipeline/decisions/20260924-191018_route_change.md",
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
        raise ValueError("Unexpected design preflight")
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
            if ref not in candidate.setdefault("evidence", []):
                candidate["evidence"].append(ref)
        candidate["same_forward_component_control_20260924"] = {
            "timestamp": now.isoformat(),
            "checker": refs[0],
            "test": refs[1],
            "decision": refs[2],
            "tests_passed": 39,
            "native_execution_completed": False,
            "admission": False,
            "score_mse_unmeasured": True,
        }
        candidate["blocker"] = (
            "Read-only authorized GPU7 query during 2026-09-24 19:07 +08:00: "
            "external PID 3694608 uses 41,996 MiB; 42,023 MiB used, "
            "39,057 MiB free."
        )
        candidate["retry_after"] = (now + timedelta(minutes=20)).isoformat()
        candidate["unblock_condition"] = (
            "Authorized GPU7 clears; verify SSH, code/runtime/data, frozen "
            "checkpoint and producer provenance, and actual occupancy/memory."
        )
        candidate["alternatives_attempted"] = (
            "One read-only GPU7 query; same-forward offline component "
            "counterfactual and 39 focused synthetic tests. No native execution."
        )
        candidate["next_action"] = (
            "When GPU7 clears and provenance checks pass, run the ordered "
            "256-row native TRAIN capture with matcher causes and query states; "
            "audit all-row binding/collisions, six exclusion rows and four "
            "same-ID scenes. Replay matched mask-only, label-only and coupled "
            "controls; measure native backward and resources before admission."
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
            "verify provenance and run one ordered capture and component "
            "controls. Do not admit or dispatch before all hard gates pass."
        ),
    }
    work["updated_at"] = now.isoformat()
    work["last_event_tick"] = now.isoformat()
    if WORK.read_bytes() != original or reference("pipeline/queue.json")["sha256"] != queue_hash:
        raise ValueError("Concurrent research or queue change")
    temporary = WORK.with_suffix(".counterfactual.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    os.replace(temporary, WORK)
    print(json.dumps({"due_ids": sorted(found), "queue_sha256": queue_hash}))


if __name__ == "__main__":
    main()
