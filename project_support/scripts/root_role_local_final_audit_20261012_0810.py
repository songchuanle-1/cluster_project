"""Bound current-candidate identity before foreground postflight."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
TOKEN = "612af628c2f046f4acf6414e49f6f18a"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    owner = load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    work = load(ROOT / "pipeline/research_work.json")
    candidate = next(row for row in work["candidates"] if row["id"] == "m95-native-target-mention-role")
    for ref in candidate["evidence"]:
        assert sha(ROOT / ref["path"]) == ref["sha256"]
    sys.path.insert(0, str(SKILL))
    import closure
    queue = load(ROOT / "pipeline/queue.json")
    task = next(row for row in queue["gpu_queues"]["server-6"] if row["id"] == "M200-TMR")
    assert task["status"] == "running" and task["launch_verified"] is True
    receipt = closure.admission(ROOT, task)
    assert closure.git(ROOT / "Cluster", "rev-parse", "HEAD") == task["code_commit"]
    population = load(ROOT / "pipeline/reports/root_role_population_contract_20261012_0810.json")
    assert population["script_sha256"] == sha(ROOT / "scripts/root_role_population_contract_20261012_0810.py")
    assert population["expressions"] == 128 and population["native_groups"] == 32
    assert len(population["changed"]) == 1 and population["unchanged_exact"] == 127
    assert len((ROOT / "pipeline/codex_memory.md").read_text(encoding="utf-8").splitlines()) < 120
    result = {
        "local_verified_at": datetime.now(timezone.utc).isoformat(),
        "candidate_evidence_hashes_verified": len(candidate["evidence"]),
        "current_commit": task["code_commit"], "six_gate_receipt_hash": sha(ROOT / task["admission_receipt"]),
        "training_progress_verified": True, "native_population_contract_verified": True,
        "original_deadline_at": owner["deadline_at"], "no_goal_gate_or_deadline_change": True,
        "limits": "Local integrity and recorded native observations; finish is not yet executed.",
    }
    path = ROOT / "pipeline/reports/root_role_local_final_audit_20261012_0810.json"
    assert not path.exists()
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
