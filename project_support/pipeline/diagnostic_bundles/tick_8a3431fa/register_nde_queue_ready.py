"""Register only the genuinely admitted M233 task, preserving every prior row."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import sys

ROOT = Path("D:/project/cluster_project")
TICK = Path(__file__).resolve().parent
TOKEN = '8a3431facc69449d9cbb681e512733aa'
CID = "hierarchy-native-distribution-embedding-composition"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import closure
import pipeline_monitor as monitor


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def ref(p):
    p = Path(p).resolve()
    return {"path": p.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployment-hold")
    args = parser.parse_args()
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    validation = read(TICK / "canonical_admission_validation.json")
    task = copy.deepcopy(validation["task"])
    closure.admission(ROOT, task)
    now = datetime.now(timezone.utc).isoformat()
    task.update(status="waiting", server="server-4", gpu="0",
                required_server="server-4", required_physical_gpu=0,
                resume_authorized=False, created_at=now, admitted_at=now)
    proof_paths = [TICK / "canonical_admission_validation.json"]
    if args.deployment_hold:
        task["dispatch_hold"] = args.deployment_hold
    else:
        pointer = TICK / "nde_pointer_active/switch_result.json"
        production = TICK / "nde_actual_production_result.json"
        review = TICK / "nde_actual_production_independent_review.json"
        p, v, a = read(pointer), read(production), read(review)
        assert p["owner"]["token"] == TOKEN
        assert p["only_runtime_and_conda_source_changed"] is True
        assert v["owner"]["token"] == TOKEN and v["one_shot_consumed"] is False
        assert a["passed"] is True and a["production_result_sha256"] == ref(production)["sha256"]
        assert hashlib.sha256((ROOT / "SERVERS.yaml").read_bytes()).hexdigest() == p["SERVERS_sha256"]
        proof_paths += [pointer, production, review, TICK / "nde_runtime_deployment.json",
                        ROOT / "pipeline/diagnostic_bundles/tick_2218a502/nde_deployment_execute/ff_result.json"]
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        proof_refs = []
        for path in proof_paths:
            assert path.is_file(), "Missing registration evidence; no queue mutation: " + str(path)
            proof_refs.append(ref(path))
        before = monitor.load_queue(str(ROOT))
        assert not any(t["id"] == "M233-NDE" for ts in before["gpu_queues"].values() for t in ts)
        after = copy.deepcopy(before)
        after["gpu_queues"].setdefault("server-4", []).append(task)
        for name, rows in before["gpu_queues"].items():
            assert after["gpu_queues"][name][:len(rows)] == rows
        monitor.save_queue(str(ROOT), after)
        assert monitor.load_queue(str(ROOT)) == after
        work_path = ROOT / "pipeline/research_work.json"
        work = read(work_path)
        candidate = next(c for c in work["candidates"] if c["id"] == CID)
        candidate.update(queued=True, updated_at=now)
        if args.deployment_hold:
            candidate["next_action"] = args.deployment_hold
        else:
            candidate.update(stage="deployment", deployed=True, source_only=False,
                             runtime_root=read(TICK / "nde_runtime_deployment.json")["runtime_root"])
            candidate["next_action"] = "Use the canonical gated dispatcher on server4 physicalGPU0; verify increasing native training steps. Keep all resource safeguards and manual pauses."
        for entry in proof_refs:
            if entry not in candidate["evidence"]:
                candidate["evidence"].append(entry)
        work["updated_at"] = now
        monitor._save_json(str(work_path), work)
        result = {"recorded_at": now, "owner_token": TOKEN, "task": task,
                  "existing_rows_preserved": True, "queue": ref(ROOT / "pipeline/queue.json"),
                  "deployment_hold": args.deployment_hold, "training_started": False}
        with (TICK / "nde_queue_registration.json").open("x", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(json.dumps({"id": task["id"], "status": task["status"],
                          "held": bool(args.deployment_hold), "existing_rows_preserved": True}))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
