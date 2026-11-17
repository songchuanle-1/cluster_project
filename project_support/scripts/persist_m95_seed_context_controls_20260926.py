"""Persist completed controls and the next native test on the same stable ID."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "pipeline/research_work.json"
FILES = (
    "pipeline/reports/m95_wrong_seed_context_control_prereg_20260926-2354.md",
    "pipeline/reports/m95_wrong_seed_context_control_20260926-2354.json",
    "pipeline/reports/m95_seed_context_score_control_prereg_20260926-2357.md",
    "pipeline/reports/m95_seed_context_score_control_20260926-2357.json",
)


def evidence(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    row = next(x for x in data["candidates"] if x["id"] == "m95-sample-context-support")
    if row["stage"] != "diagnosis":
        raise ValueError("Unexpected candidate stage")
    stamp = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    row["latest_progress"] = (
        stamp + ": Native-negative endpoint control: 18/49 exposed "
        "(17 failures, one already-successful target-IoU endpoint), "
        "0/207 outside native-negative; 21/49 native-negative selected "
        "seeds unresolved. In the all-query within-expression control, "
        "context-class native-negative seeds score +0.11387 higher on "
        "average in 160 paired expressions/145 scenes (114 positive "
        "deltas); ambiguous +0.16886 over 92 pairs, class-unique "
        "+0.03946 over 68. Observational association; no causal "
        "sample-loss attribution or training admission."
    )
    row["next_action"] = (
        "On server-6 GPU7, first verify live occupancy/headroom, native "
        "M95 checkpoint/config/model hashes, conda and data roots. In one "
        "frozen TRAIN batch containing a preregistered exposed ambiguous "
        "row and a non-exposed matched row, hook the unmodified criterion "
        "to capture ref_padding_seed_ (pre-overwrite), final "
        "ref_padding_seed, FPS seed indices, native topk_seed_inds, "
        "matched_seed_inds, ref_scores and per-component losses. Repeat "
        "unmodified forward for noise; then intervene on class-context "
        "support only for unmatched non-target FPS seeds and compare "
        "with a count-/class-/instance-matched placebo while preserving "
        "masks, matcher pairs, indicator and other losses. Check sample "
        "gradient and any effect on referent decision; only then assess "
        "diagnosis/controls and subsequent native backward/resources/"
        "independence/goal constraints. Do not treat a score association "
        "or source-only change as a PASS."
    )
    row["evidence"].extend(evidence(path) for path in FILES)
    data["updated_at"] = stamp
    data["next_action"] = row["next_action"]
    cycle = data["design_cycle"]
    cycle["timestamp"] = stamp
    cycle["attempted_ids"] = [
        "m95-physical-target-semantic-conflict",
        "m95-multigt-mask-index",
        "m95-sample-context-support",
    ]
    cycle["evidence"] = [evidence(path) for path in FILES]
    cycle["resume_condition"] = row["next_action"]
    cycle["blocker"] = (
        "Exact final seed target and matched native intervention are unmeasured; "
        "the route is actionable, not externally blocked. No admission receipt."
    )
    cycle["deferred_reason"] = (
        "Three diagnostic routes progressed; two rejected, one actionable. "
        "Continue the native test while scheduler time remains."
    )
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("persisted", row["id"], row["stage"])


if __name__ == "__main__":
    main()
