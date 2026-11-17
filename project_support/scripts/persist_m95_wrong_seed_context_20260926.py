"""Resume the existing seed-context ID after its physical seed screen."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "pipeline/research_work.json"
FILES = (
    "pipeline/reports/m95_wrong_seed_context_prereg_20260926-2346.md",
    "pipeline/reports/m95_wrong_seed_context_20260926-2346.json",
    "pipeline/decisions/20260926-235141_route_change.md",
)


def evidence(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    row = next(x for x in data["candidates"] if x["id"] == "m95-sample-context-support")
    if row["stage"] != "rejected":
        raise ValueError("Unexpected prior stage")
    stamp = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    row["stage"] = "diagnosis"
    row["latest_progress"] = (
        stamp + ": A distinct physical-query-seed extension of the completed "
        "lexical screen found 17/17 exposed selected ambiguous failures versus "
        "14/65 resolved non-exposed, on 256 frozen expressions. All 17 overlap "
        "native-negative wrong/partial-mask selections; 92 selected seeds "
        "unresolved and no same-scene discordant control. This is an upper "
        "bound before native matched/top-k overwrite, not a final loss target."
    )
    row["next_action"] = (
        "Run an outcome-independent control within native-negative "
        "wrong/partial-mask selections, then capture exact final ref_padding_seed "
        "and top-k/matcher overwrite on frozen M95 rows with a same-forward "
        "context removal versus matched placebo. Verify the change reaches "
        "sample_loss and query/backward paths before resources, independent "
        "implementation, constraints, receipt or training. Reject only on "
        "disconfirming native controls, not on missing capture."
    )
    row["evidence"].extend(evidence(path) for path in FILES)
    data["updated_at"] = stamp
    data["next_action"] = row["next_action"]
    data["design_cycle"] = {
        "timestamp": stamp, "stop_reason": "independent_routes_exhausted",
        "deferred_reason": "Provisional: continue executable seed-context control and native capture this tick.",
        "attempted_ids": ["m95-physical-target-semantic-conflict",
                          "m95-multigt-mask-index", "m95-sample-context-support"],
        "evidence": [evidence(path) for path in FILES],
        "resume_condition": row["next_action"],
        "blocker": "Diagnosis is incomplete; no six-gate admission receipt.",
    }
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("resumed", row["id"], row["stage"])


if __name__ == "__main__":
    main()
