"""Record incompatible native producer as evidence on the stable diagnosis."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "pipeline/research_work.json"
EVIDENCE = [
    "pipeline/reports/m95_multiword_native_adapter_prereg_20260928.md",
    "scripts/m95_multiword_native_adapter_audit_20260928.py",
    "pipeline/reports/m95_multiword_native_adapter_audit_20260928.json",
    "pipeline/decisions/20260928-021329_route_change.md",
]


def bound(relative):
    return {"path": relative, "sha256": hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()}


def main():
    work = json.loads(LEDGER.read_text(encoding="utf-8"))
    item = next(row for row in work["candidates"] if row["id"] == "m95-sample-context-support")
    if item["stage"] != "diagnosis" or any(
            entry["path"] == EVIDENCE[2] for entry in item["evidence"]):
        raise ValueError("Unexpected diagnosis state or duplicate")
    report = json.loads((ROOT / EVIDENCE[2]).read_text(encoding="utf-8"))
    if (report["direct_compatibility"] is not False or report["manifest_rows"] != 31
            or report["producer_rows"] != 256):
        raise ValueError("Frozen adapter result differs")
    stamp = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    item["latest_progress"] = (
        stamp + ": Static frozen native capture compatibility check: new "
        "two-scene/31-expression manifest (11 phrase, 20 controls) is not "
        "accepted by the existing 256-row identity producer, which also "
        "expects stratum/target-class/peer metadata. No coercion or invented "
        "metadata. Live GPU7 still occupied by foreign PID 709354; no "
        "native model outcome, placebo or structural admission.")
    item["next_action"] = (
        "Diagnosis: review a separate manifest adapter preserving original "
        "utterance, physical target IDs, scene/annotation parity, M95 checkpoint, "
        "native loss, and seed 1999; do not rewrite the frozen 256-row producer. "
        "Then, only after live server-6 GPU7 vacancy and exclusive lease, "
        "capture fixed 31 expressions, compare same-forward fixed-text support "
        "change to placebo, and revisit independent structural mechanism. "
        "All six gates pending; no queue or training.")
    item["evidence"].extend(bound(path) for path in EVIDENCE)
    work["updated_at"] = stamp
    work["next_action"] = item["next_action"]
    cycle = work["design_cycle"]
    cycle.update(timestamp=stamp, attempted_ids=[item["id"]],
                 evidence=[bound(path) for path in EVIDENCE],
                 resume_condition=item["next_action"],
                 blocker="Live foreign GPU7 occupation; new native manifest adapter not reviewed.",
                 deferred_reason="Static adapter mismatch verified; native model evidence remains uncollected.")
    cycle.pop("stop_reason", None)
    LEDGER.write_text(json.dumps(work, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(item["id"], item["stage"], len(item["evidence"]))


if __name__ == "__main__":
    main()
