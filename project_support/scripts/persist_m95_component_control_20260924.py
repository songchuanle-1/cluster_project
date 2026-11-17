"""Persist the bounded component-control diagnosis on the three due IDs."""

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
REPORT = "pipeline/reports/m95_mask_component_control_20260924-1810.md"
DECISION = "pipeline/decisions/20260924-181102_route_change.md"
SOURCE = (
    "Cluster/framework/model/Quard_model/"
    "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/loss.py"
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
    refs = [
        reference(path)
        for path in (
            SOURCE,
            "scripts/native_manifest_capture_20260922.py",
            "scripts/m95_repeated_gt_mask_contract_20260924.py",
            "scripts/m95_exclusion_cause_audit_20260924.py",
            REPORT,
            DECISION,
        )
    ]
    now = datetime.now().astimezone()
    found = set()
    for candidate in work["candidates"]:
        if candidate["id"] not in DUE:
            continue
        if candidate["stage"] != "blocked":
            raise ValueError("Unexpected due stage")
        found.add(candidate["id"])
        evidence = candidate.setdefault("evidence", [])
        for ref in refs:
            if ref not in evidence:
                evidence.append(ref)
        candidate["component_control_20260924"] = {
            "timestamp": now.isoformat(),
            "report": reference(REPORT),
            "decision": reference(DECISION),
            "source": reference(SOURCE),
            "tests_passed": 24,
            "native_execution_completed": False,
            "admission": False,
        }
        candidate["blocker"] = (
            "External PID 3694608 occupies 41,996 MiB on authorized GPU7 "
            "at 2026-09-24T18:07:48+08:00"
        )
        candidate["retry_after"] = (now + timedelta(minutes=20)).isoformat()
        candidate["unblock_condition"] = (
            "Authorized GPU7 clears; SSH, code/runtime/data, frozen checkpoint "
            "and producer provenance, and actual memory/occupancy are verified."
        )
        candidate["alternatives_attempted"] = (
            "One read-only authorized GPU7 query; source-bound component "
            "contract and 24 focused synthetic tests. No native execution."
        )
        candidate["next_action"] = (
            "After GPU7 clears and provenance checks pass, run one ordered "
            "256-row native TRAIN capture with matcher causes and query states; "
            "audit all-row binding/collisions, six exclusion rows and four "
            "same-ID scenes. Then run matched mask-only, label-only and "
            "coupled controls before mechanism admission."
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
            "verify provenance and run the single ordered capture and controls. "
            "Do not admit or dispatch before all hard gates pass."
        ),
    }
    work["updated_at"] = now.isoformat()
    work["last_event_tick"] = now.isoformat()
    if WORK.read_bytes() != original or reference("pipeline/queue.json")["sha256"] != queue_hash:
        raise ValueError("Concurrent research or queue change")
    temporary = WORK.with_suffix(".component_control.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    os.replace(temporary, WORK)
    print(json.dumps({"due_ids": sorted(found), "queue_sha256": queue_hash}))


if __name__ == "__main__":
    main()
