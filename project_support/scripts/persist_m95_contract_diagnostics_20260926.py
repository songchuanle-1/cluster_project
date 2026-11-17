"""Persist bounded negative M95 contract diagnoses under stable IDs."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "pipeline/research_work.json"
ROUTES = (
    (
        "m95-physical-target-semantic-conflict",
        "Native annotation/dataset/TSV/capture-bound 256-row audit: 80 exact-class "
        "eligible target instances, 2 semantic-class conflicts, both deployed "
        "successes; zero same-scene class-matched exposure-discordant pairs. "
        "No failure-linked physical target class contradiction.",
        "Do not relabel this as class-label repair or lexical supervision correction. "
        "Reconsider only on independent failure-linked physical identity conflict "
        "and a matched native loss-path intervention.",
        ("pipeline/reports/m95_physical_semantic_contract_prereg_20260926-2326.md",
         "pipeline/reports/m95_physical_semantic_contract_20260926-2326.json",
         "pipeline/decisions/20260926-233955_route_change.md"),
    ),
    (
        "m95-multigt-mask-index",
        "All 256 frozen native ScanRefer expressions, including 56 failures, "
        "have one GT object. The conditional repeated-GT mask-indexing bug "
        "has zero affected queries and no failure exposure here.",
        "Do not create a bugfix model candidate from this synthetic multi-GT "
        "source contract for the current task; only revisit under independently "
        "observed multi-GT native ScanRefer rows and matched loss-path control.",
        ("pipeline/reports/m95_multigt_mask_index_prereg_20260926-2336.md",
         "pipeline/reports/m95_multigt_mask_index_20260926-2336.json",
         "pipeline/decisions/20260926-234005_route_change.md"),
    ),
)


def receipt(path):
    full = ROOT / path
    return {"path": path, "sha256": hashlib.sha256(full.read_bytes()).hexdigest()}


def main():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    existing = {row["id"] for row in data["candidates"]}
    stamp = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    evidence = []
    for route_id, result, next_action, files in ROUTES:
        if route_id in existing:
            raise ValueError("Stable ID already exists: " + route_id)
        bound = [receipt(path) for path in files]
        data["candidates"].append({
            "id": route_id, "stage": "rejected",
            "latest_progress": stamp + ": " + result + " No admission or training.",
            "next_action": next_action, "evidence": bound,
        })
        evidence.extend(bound)
    data["updated_at"] = stamp
    data["next_action"] = (
        "Continue distinct prediction-blind task mechanism diagnosis; exact "
        "physical semantic conflicts and repeated-GT mask-index prerequisites "
        "were absent on frozen M95. Do not enqueue without six hard gates."
    )
    data["design_cycle"] = {
        "timestamp": stamp, "stop_reason": "independent_routes_exhausted",
        "deferred_reason": "Provisional only; continue research before deadline.",
        "attempted_ids": [row[0] for row in ROUTES],
        "evidence": evidence,
        "resume_condition": "Continue independent prediction-blind native task information diagnostic, then matched control and remaining gates on server-6 GPU7.",
        "blocker": "Neither route exposes a failure-linked causal deficit; candidate budget 2 remains open.",
    }
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("persisted", len(ROUTES), "negative routes")


if __name__ == "__main__":
    main()
