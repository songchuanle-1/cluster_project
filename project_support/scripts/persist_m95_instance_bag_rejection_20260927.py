"""Record a rejected bag formulation without rejecting the broader diagnosis."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "pipeline/research_work.json"
EVIDENCE = (
    "pipeline/reports/m95_seed_mask_reachability_prereg_20260927.md",
    "pipeline/reports/m95_seed_mask_reachability_1999_20260927.json",
    "pipeline/reports/m95_seed_mask_reachability_summary_20260927.json",
    "pipeline/reports/m95_instance_bag_prereg_20260927.md",
    "pipeline/reports/m95_instance_bag_20260927.json",
    "pipeline/reports/m95_instance_bag_control_amendment_20260927.md",
    "pipeline/reports/m95_instance_bag_interleaved_20260927.json",
    "pipeline/reports/m95_instance_bag_population_prereg_20260927.md",
    "pipeline/reports/m95_instance_bag_population_20260927.json",
    "pipeline/reports/m95_instance_bag_population_summary_20260927.json",
    "pipeline/reports/m95_instance_bag_operating_regime_prereg_20260927.md",
    "pipeline/reports/m95_instance_bag_regime_20260927.json",
    "pipeline/reports/m95_instance_bag_regime_summary_20260927.json",
)
NEXT = (
    "Do not revive the noisy-OR context bag with target 0.25 or tune its "
    "target/scale: the preregistered native gradient sign gate rejected it. "
    "Keep physical seed-context exposure as an observational diagnosis. "
    "Seek a structurally independent supervision unit with a derived "
    "directional objective and same-forward native matched controls; "
    "compare whole mechanism against closed PIRS/ranking and mask-aware "
    "matching before implementation. On server-6 GPU7, run the next "
    "executable diagnosis/control; no admission without six hard gates."
)


def bound(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    regime = json.loads((ROOT / EVIDENCE[-1]).read_text(encoding="utf-8"))
    reach = json.loads((ROOT / EVIDENCE[2]).read_text(encoding="utf-8"))
    population = json.loads((ROOT / EVIDENCE[9]).read_text(encoding="utf-8"))
    if (not regime["rejection_gate_passed"]
            or regime["bags"] != 316
            or reach["selected_context_seed_in_selected_mask"] != 17
            or population["total_moved_seeds"] != 1232):
        raise ValueError("Native rejection evidence changed")
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    row = next(r for r in data["candidates"] if r["id"] == "m95-sample-context-support")
    if row["stage"] != "diagnosis" or any(
            item["path"] == EVIDENCE[-1] for item in row["evidence"]):
        raise ValueError("Unexpected candidate stage or duplicate evidence")
    stamp = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    row["latest_progress"] = (
        stamp + ": Same-input native selected seed is inside selected mask "
        "in 17/17 context-exposed cases (4/4 prespecified keys), so seed "
        "reachability is not falsified. Tested a physical-instance noisy-OR "
        "bag supervision unit with hard-zero and size-preserving shuffled "
        "controls; native two-tensor backward finite. Full 16-batch population "
        "moves 1232/2140 eligible seeds across shuffled bags; gradient "
        "specificity ratio <0.1 in 8/16 and >=0.5 in 8/16, mixed. "
        "Preregistered operating-regime gate rejects the formulation: all "
        "316 bag probabilities >0.25 (median .988), 289 bags have member "
        "gradient sign that suppresses logits and 27 are saturated at zero. "
        "No new model/config, resource gate, efficacy or admission; the "
        "underlying context-exposure diagnosis remains unresolved."
    )
    row["next_action"] = NEXT
    items = [bound(path) for path in EVIDENCE]
    row["evidence"].extend(items)
    data["next_action"] = NEXT
    data["updated_at"] = stamp
    cycle = data["design_cycle"]
    cycle.update(
        timestamp=stamp,
        attempted_ids=[row["id"]],
        evidence=cycle["evidence"] + items,
        stop_reason=(
            "No admission; noisy-OR formulation failed preregistered "
            "gradient-direction gate; broader diagnosis remains active."
        ),
        blocker="Internal structural/control design, not external resources.",
        resume_condition=NEXT,
        admissions=0,
    )
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(row["id"], row["stage"], len(row["evidence"]))


if __name__ == "__main__":
    main()
