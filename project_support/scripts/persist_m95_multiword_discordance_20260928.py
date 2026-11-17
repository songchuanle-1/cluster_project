"""Bind the frozen source-data discordance test to the existing diagnosis."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "pipeline/research_work.json"
EVIDENCE = [
    "pipeline/reports/m95_multiword_role_target_discordance_prereg_20260928.md",
    "scripts/m95_multiword_role_target_discordance_20260928.py",
    "pipeline/reports/m95_multiword_role_target_discordance_20260928.json",
]


def bound(relative):
    return {"path": relative, "sha256": hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()}


def main():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    row = next(x for x in data["candidates"] if x["id"] == "m95-sample-context-support")
    if row["stage"] != "diagnosis" or any(
            x["path"] == EVIDENCE[-1] for x in row["evidence"]):
        raise ValueError("Unexpected stage or duplicate evidence")
    report = json.loads((ROOT / EVIDENCE[-1]).read_text(encoding="utf-8"))
    counts = report["summary"]
    if (counts["physical_nontarget_expressions"] != 102
            or counts["graph_target_span_expressions"] != 36
            or counts["graph_target_span_physical_noncurtain_expressions"] != 7
            or counts["graph_other_only_expressions"] != 65):
        raise ValueError("Frozen join changed")
    stamp = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    row["latest_progress"] = (
        stamp + ": Outcome-blind frozen TRAIN join: 102 expressions with a "
        "physical non-target curtain; 36 graph target-span expressions, "
        "including 7 whose physical target is not a curtain (3 scenes), "
        "and 65 graph other-Object-only expressions. Thus graph target span "
        "does not uniquely bind the phrase to the physical curtain. "
        "No native M95 outcomes, same-input intervention or structural mechanism; "
        "server-6 GPU7 remains occupied by a foreign process.")
    row["next_action"] = (
        "Diagnosis only. Frozen 31-expression/2-scene manifest native capture "
        "requires live GPU7 vacancy plus exclusive lease. Evaluate original "
        "M95 outcomes, fixed-text same-forward context-support change and "
        "placebo; distinguish physical target and graph-role discordance. "
        "Do not admit a lexical fix or relabel a closed selector route. "
        "All six gates and independent structural mechanism remain pending.")
    row["evidence"].extend(bound(path) for path in EVIDENCE)
    data["next_action"] = row["next_action"]
    data["updated_at"] = stamp
    cycle = data["design_cycle"]
    cycle.update(timestamp=stamp, attempted_ids=[row["id"]],
                 evidence=[bound(path) for path in EVIDENCE],
                 resume_condition=row["next_action"],
                 blocker="Native capture awaits confirmed exclusive GPU7 vacancy; no GPU job was started.",
                 deferred_reason="Source-data role binding disconfirmed; native same-forward diagnosis pending.")
    cycle.pop("stop_reason", None)
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(row["id"], row["stage"], len(row["evidence"]))


if __name__ == "__main__":
    main()
