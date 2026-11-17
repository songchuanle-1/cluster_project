"""Persist the complete M95 identity-control tick under all due IDs."""

import hashlib
import json
import os
from copy import deepcopy
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
    "pipeline/reports/m95_identity_control_analysis_20260924-231333.json",
    "pipeline/reports/m95_any_instance_control_20260924-231840.json",
    "pipeline/reports/m95_native_component_counterfactual_attempt_20260924-2311.json",
    "pipeline/reports/m95_identity_control_full_20260924-2318.md",
    "scripts/m95_any_instance_control_20260924.py",
    "scripts/test_m95_any_instance_control_20260924.py",
    "pipeline/decisions/20260924-231953_route_change.md",
)


def reference(path):
    return {
        "path": path,
        "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
    }


def main():
    context = json.loads(
        (ROOT / "pipeline/headless/.tick_context.json").read_text(
            encoding="utf-8"
        )
    )
    if context["mode"] != "design" or set(context["research_work"]["due_ids"]) != DUE:
        raise ValueError("Unexpected preflight")

    original = WORK.read_bytes()
    queue_hash = reference("pipeline/queue.json")["sha256"]
    work = json.loads(original)
    refs = [reference(path) for path in PATHS]
    now = datetime.now().astimezone()
    retry_after = (now + timedelta(minutes=20)).isoformat()
    found = set()

    for candidate in work["candidates"]:
        if candidate["id"] not in DUE:
            continue
        found.add(candidate["id"])
        evidence = candidate.setdefault("evidence", [])
        for ref in refs:
            matches = [
                item for item in evidence if item.get("path") == ref["path"]
            ]
            if matches:
                for item in matches:
                    item["sha256"] = ref["sha256"]
            else:
                evidence.append(deepcopy(ref))

        candidate["m95_identity_control_full_20260924"] = {
            "timestamp": now.isoformat(),
            "source_capture": {
                "host": "server-6",
                "path": (
                    "/data3/songcl/Project/Cluster_project/pipeline/"
                    "diagnostic_runs/m95_identity_capture_20260922-1813/"
                    "capture.json"
                ),
                "sha256": (
                    "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296"
                    "363e95880025"
                ),
                "rows": 256,
                "artifact_rows": 256,
                "artifact_files": 250,
                "native_match_cause_rows": 0,
            },
            "identity_analysis": refs[0],
            "any_instance_control": refs[1],
            "component_attempt": refs[2],
            "report": refs[3],
            "checker": refs[4],
            "test": refs[5],
            "decision": refs[6],
            "new_focused_tests_passed": 5,
            "identity_control_completed": True,
            "target_positive_scene_uplift": 0.10228510977421706,
            "target_positive_scene_ci": [0.06869772261073165, 0.13806120463301377],
            "class_matched_scene_uplift": 0.002823094668489405,
            "class_matched_scene_ci": [-0.0025454545454545456, 0.011638115174299383],
            "any_instance_minus_deployed": 0.0,
            "native_match_cause_capture_required": True,
            "native_component_counterfactual_completed": False,
            "native_backward_measured": False,
            "resources_measured": False,
            "admission": False,
        }
        candidate["blocker"] = (
            "Read-only authorized GPU7 query at 2026-09-24 23:12 +08:00: "
            "external PID 3694608 uses 41,996 MiB; 42,023 MiB used, "
            "39,057 MiB free, 0% utilization."
        )
        candidate["retry_after"] = retry_after
        candidate["unblock_condition"] = (
            "Authorized GPU7 clears; verify SSH, code/runtime/data, frozen "
            "checkpoint and producer provenance, and actual occupancy/memory."
        )
        candidate["alternatives_attempted"] = (
            "Ran the complete 256-row identity-control analyzer and a "
            "scene-balanced any-instance control on server-6 CPU. Attempted "
            "the four-arm component replay and captured its fail-closed "
            "native_match_cause error. No GPU execution."
        )

        if candidate["id"] == "referent-supervision-axis":
            candidate["stage"] = "blocked"
            candidate["next_action"] = (
                "On GPU7 clearance and provenance checks, run a new ordered "
                "256-row native TRAIN capture with --capture-match-causes; run "
                "scripts/native_component_counterfactual_20260924.py on the "
                "new capture, then measure native backward and resources "
                "before admission."
            )
        elif candidate["id"] == "referent-discrimination":
            candidate["stage"] = "diagnosis"
            candidate["next_action"] = (
                "Derive a deployable target-specific query-score supervision "
                "candidate from the full-cohort controls, with explicit "
                "whole-mechanism novelty against DETR/RefMask3D and matched "
                "controls for generic objectness, class membership, and the "
                "already rejected listwise/ranking/selector families. Do not "
                "reopen an oracle selector or a renamed rejected loss."
            )
        else:
            candidate["stage"] = "diagnosis"
            candidate["next_action"] = (
                "Use the full-cohort identity margins only as diagnostic "
                "context. Do not create another stage audit or identity-loss "
                "variant; require a distinct representational causal unit with "
                "a native backward and resource plan before admission."
            )

    if found != DUE:
        raise ValueError("Missing due IDs")

    work["design_cycle"] = {
        "timestamp": now.isoformat(),
        "stop_reason": "no_admissible_candidate_after_full_identity_control",
        "attempted_ids": sorted(DUE),
        "evidence": refs,
        "resume_condition": (
            "At or after retry_after, recheck authorized GPU7. On clearance, "
            "run a new capture with native matcher causes and resume the "
            "component replay. Independently derive a deployable target-score "
            "mechanism without reopening rejected selector, listwise, ranking "
            "or identity-loss families."
        ),
    }
    work["updated_at"] = now.isoformat()
    work["last_event_tick"] = now.isoformat()
    work["next_action"] = (
        "Run the matcher-cause capture when GPU7 clears; derive a deployable "
        "target-specific query-score mechanism from the full identity-control "
        "evidence without creating a renamed rejected route."
    )

    if WORK.read_bytes() != original or reference("pipeline/queue.json")[
        "sha256"
    ] != queue_hash:
        raise ValueError("Concurrent research or queue change")
    temporary = WORK.with_suffix(".identity_control.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    os.replace(temporary, WORK)
    print(
        json.dumps(
            {
                "due_ids": sorted(found),
                "queue_sha256": queue_hash,
                "retry_after": retry_after,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
