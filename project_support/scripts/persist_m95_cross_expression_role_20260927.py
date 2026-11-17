"""Add the native identity-matched observational contrast to the stable ID."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "pipeline/research_work.json"
EVIDENCE = (
    "pipeline/reports/m95_cross_expression_role_prereg_20260927.md",
    "pipeline/reports/m95_cross_expression_role_1999_20260927.json",
    "pipeline/reports/m95_cross_expression_role_summary_20260927.json",
)
NEXT = (
    "On server-6 GPU7, preregister an instance-grouped seed-supervision "
    "mechanism and its same-forward seed-wise hard-zero and group-size/score "
    "controls, preserving native matcher, indicator and mask losses. Explicitly "
    "treat the cross-expression same-instance contrast as confounded by language "
    "and target identity; do not claim it is a causal placebo. First review "
    "whether the proposed group-level loss is substantively distinct from closed "
    "PIRS/ranking and generic mask-aware matching; reject if it is only a "
    "reparameterization. If distinct, implement and run native parameter "
    "backward, resource/Pareto, independent package/config and goal-constraint "
    "checks. Admission, sync and training require all six hard gates."
)


def bound(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    summary = json.loads((ROOT / EVIDENCE[-1]).read_text(encoding="utf-8"))
    if (summary["native_expressions"] != 128 or summary["scenes"] != 32
            or summary["mixed_role_instances"] != 180
            or summary["selected_context_with_cross_expression_zero"] != 12
            or summary["fractional_unprotected_seeds_excluded"] != 15):
        raise ValueError("Native role contrast changed")
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    row = next(x for x in data["candidates"]
               if x["id"] == "m95-sample-context-support")
    if row["stage"] != "diagnosis" or any(
            item["path"] == EVIDENCE[-1] for item in row["evidence"]):
        raise ValueError("Unexpected stage or duplicate evidence")
    stamp = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    row["latest_progress"] = (
        stamp + ": Exact native role census on 128 expressions/32 scenes "
        "(the preregistration's '16-scene' wording incorrectly counted 16 "
        "batches as scenes): 180 physical instances in 31 scenes have both "
        "unprotected context 0.25 and zero targets across expressions. "
        "Twelve of 17 selected-context failures have a same-instance "
        "zero-target counterpart in another expression; 15 fractional "
        "superpoint targets excluded. Same-input fingerprints and selected "
        "outcomes match the earlier seed-1999 capture. This contrast changes "
        "language and often referent identity; it is observational, not a "
        "causal placebo. Within-expression exact instance-matched zero "
        "controls remain 0/2140. No admitted mechanism or resource gate."
    )
    row["next_action"] = NEXT
    items = [bound(path) for path in EVIDENCE]
    row["evidence"].extend(items)
    data["next_action"] = NEXT
    data["updated_at"] = stamp
    cycle = data["design_cycle"]
    cycle.update(
        timestamp=stamp,
        stop_reason=(
            "No admission: cross-expression identity control is confounded; "
            "remaining structurally independent routes lack diagnosis/gates."
        ),
        attempted_ids=[row["id"]],
        evidence=cycle["evidence"] + items,
        blocker=(
            "Internal mechanism-distinction/control implementation; no "
            "external resource block."
        ),
        resume_condition=NEXT,
        admissions=0,
    )
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(row["id"], row["stage"], len(row["evidence"]))


if __name__ == "__main__":
    main()
