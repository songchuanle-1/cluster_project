"""Bind tested native-capture readiness to the existing diagnosis, not admission."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "pipeline/research_work.json"
EVIDENCE = [
    "pipeline/reports/m95_multiword_native_31_prereg_20260928.md",
    "scripts/m95_multiword_native_31_20260928.py",
    "scripts/test_m95_multiword_native_31_20260928.py",
    "pipeline/decisions/20260928-022043_route_change.md",
]


def bind(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    candidate = next(item for item in data["candidates"]
                     if item["id"] == "m95-sample-context-support")
    if candidate["stage"] != "diagnosis" or any(
            item["path"] == EVIDENCE[1] for item in candidate["evidence"]):
        raise ValueError("Unexpected state or duplicate evidence")
    stamp = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    candidate["latest_progress"] = (
        stamp + ": Frozen 31-expression/2-scene native M95 capture adapter "
        "prepared as independent read-only script; six CPU contract tests "
        "pass (identity, original text, physical target, duplicate/missing "
        "identities, unrelated scene), AST pass. Binds original TRAIN "
        "dataset/annotation/graph hashes, original M95 checkpoint, seed 1999. "
        "Never run on GPU or claim model outcome: live GPU7 foreign PID "
        "709354 occupied ~13.2GB at 02:19. No structural mechanism or "
        "six-gate admission.")
    candidate["next_action"] = (
        "Diagnosis: verify server-6 GPU7 is live-idle, acquire an exclusive "
        "native-diagnostic lease and confirm remote code/data/checkpoint hashes "
        "before staging the frozen 31-expression capture. Review its native "
        "outcomes by scene/physical target; then preregister and test a "
        "same-forward fixed-text support intervention with a matched placebo. "
        "If source-only lexical repair or unrelated losses remain, do not admit. "
        "All six gates remain pending.")
    candidate["evidence"].extend(bind(path) for path in EVIDENCE)
    data["next_action"] = candidate["next_action"]
    data["updated_at"] = stamp
    data["design_cycle"].update(
        timestamp=stamp, attempted_ids=[candidate["id"]],
        evidence=[bind(path) for path in EVIDENCE],
        resume_condition=candidate["next_action"],
        blocker="Foreign GPU7 process occupied the only authorized card; native run unexecuted.",
        deferred_reason="Native capture adapter passed CPU contracts but not GPU/runtime or causal validation.")
    data["design_cycle"].pop("stop_reason", None)
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(candidate["id"], candidate["stage"], len(candidate["evidence"]))


if __name__ == "__main__":
    main()
