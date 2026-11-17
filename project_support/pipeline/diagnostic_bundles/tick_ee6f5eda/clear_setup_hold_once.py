"""Default NOP. Clear only M234's setup hold after reviewed actual production setup."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
TOKEN = "ee6f5eda28ef4b02a751c84d4c7df626"
SOURCE = "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
SHIM = "/data/songcl/Project/Cluster_project/pipeline/runtime/rvec_path_prod_ee6f5eda/conda_source.sh"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def guard():
    assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    full = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    owner = {k: full[k] for k in (
        "token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256"
    )}
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 180
    for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[key]
    return owner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--production-result")
    parser.add_argument("--production-review")
    parser.add_argument("--production-review-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SHARED_MUTATION"}))
        return
    assert all((args.production_result, args.production_review, args.production_review_sha256))
    owner = guard()
    production_path, review_path = map(Path, (args.production_result, args.production_review))
    assert all(p.resolve().is_relative_to(HERE.resolve()) for p in (production_path, review_path))
    assert sha(review_path) == args.production_review_sha256
    peer = read(review_path)
    assert peer["passed"] is True and peer["owner"] == owner and peer["material_concerns"] == []
    assert peer["source_commit"] == SOURCE and peer["production_result_sha256"] == sha(production_path)
    assert peer["reviewer_thread_id"] != owner["thread_id"]
    sys.path.insert(0, str(SKILL))
    import closure
    import pipeline_monitor as monitor
    import yaml
    assert yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]["server-4"]["conda_source"] == SHIM
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        intent, actual = HERE / "clear_hold_intent.json", HERE / "clear_hold_actual.json"
        assert not intent.exists() and not actual.exists(), "Existing or uncertain mutation; no replay."
        queue_path = ROOT / "pipeline/queue.json"
        before = queue_path.read_bytes()
        queue = json.loads(before.decode("utf-8-sig"))
        candidates = [t for tasks in queue["gpu_queues"].values() for t in tasks if t["id"] == "M234-RVE"]
        assert len(candidates) == 1
        task = candidates[0]
        assert task["status"] == "waiting" and task["gpu"] == "0" and task["code_commit"] == SOURCE
        assert task["dispatch_phase"] == "source_production_setup_pending"
        assert task["dispatch_hold"].startswith("Tested r1 technical admission; dispatch held for")
        closure.admission(ROOT, task)
        protected = copy.deepcopy({
            server: [t for t in tasks if t["id"] != "M234-RVE"]
            for server, tasks in queue["gpu_queues"].items()
        })
        save(intent, {"owner": owner, "queue_before_sha256": sha(queue_path),
                      "production_result_sha256": sha(production_path),
                      "production_review_sha256": sha(review_path),
                      "only_M234_setup_hold_change": True, "training_started": False, "no_replay": True})
        old_hold = task.pop("dispatch_hold")
        task["dispatch_phase"] = "production_ready"
        assert protected == {
            server: [t for t in tasks if t["id"] != "M234-RVE"]
            for server, tasks in queue["gpu_queues"].items()
        }
        temporary = queue_path.with_name("queue.ee6f5eda.clear_hold.tmp")
        assert not temporary.exists()
        save(temporary, queue)
        assert queue_path.read_bytes() == before
        guard()
        os.replace(temporary, queue_path)
        save(actual, {"owner": owner, "source_commit": SOURCE,
                      "queue_before_sha256": hashlib.sha256(before).hexdigest(),
                      "queue_after_sha256": sha(queue_path), "old_setup_hold": old_hold,
                      "only_M234_setup_hold_cleared": True, "protected_other_tasks_unchanged": True,
                      "training_started": False, "GPU_or_SSH": False})
        print(json.dumps({"path": str(actual), "sha256": sha(actual), "status": "READY_FOR_CANONICAL_DISPATCH"}))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
