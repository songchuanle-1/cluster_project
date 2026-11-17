"""Backfill the missing M183 registry entry without changing its queued task."""
from datetime import datetime
import importlib.util
from pathlib import Path


def main():
    root = Path("D:/project/cluster_project")
    source = root.parent / ".claude/skills/songcl_research_pipeline/pipeline_monitor.py"
    spec = importlib.util.spec_from_file_location("tick_monitor", source)
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    lock = monitor.acquire_lock(str(root))
    if lock is None:
        raise RuntimeError("Pipeline lock is busy; no files changed")
    try:
        exp_id = "M183-CTF-HCG-CSORT-HQI"
        if monitor.load_experiment(str(root), exp_id) is not None:
            print("M183 registry already exists; no changes")
            return
        queue = monitor.load_queue(str(root))
        matches = [
            task for task in queue["gpu_queues"]["server-4"]
            if task["id"] == exp_id
        ]
        assert len(matches) == 1 and matches[0]["status"] == "waiting"
        watched = ("queue.json", "running.json", "experiments.csv")
        before = {name: (root / "pipeline" / name).read_bytes() for name in watched}
        stamp = datetime.now().isoformat(timespec="seconds")
        record = dict(matches[0])
        record.update(server="server-4", registry_created_at=stamp, history=[{
            "ts": stamp,
            "action": "metadata_reconciled",
            "decision": "20260908-211039_other.md",
            "source": "queue.json; decisions/20260908-182949_next_batch.md",
        }])
        monitor.save_experiment(str(root), record)
        assert monitor.load_experiment(str(root), exp_id) == record
        assert all((root / "pipeline" / name).read_bytes() == data
                   for name, data in before.items())
        print(f"M183 registry backfilled at {stamp}; queue/running/CSV unchanged")
    finally:
        lock.close()


if __name__ == "__main__":
    main()
