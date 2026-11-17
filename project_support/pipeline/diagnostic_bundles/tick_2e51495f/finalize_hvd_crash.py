"""Archive the confirmed exact failed run; no monitor, dispatch or restart."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import pipeline_monitor as mon


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def guard():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == "2e51495f07244023946fc53eec6e6d98"
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    return owner


owner = guard()
assert not (HERE / "hvd_crash_archive_result.json").exists()
death = read(HERE / "hvd_death_confirmation_cpu_checkpoint.json")
assert death["returncode"] == 0
confirmed = json.loads(death["stdout"])
assert len(confirmed["process_absence_observations"]) == 3
assert all(not item["exists"] for item in confirmed["process_absence_observations"])
exit_observation = read(HERE / "hvd_exit_observation.json")["observation"]
assert exit_observation["guardian"]["state"]["status"] == "RELEASED"
assert all(not item["kernel_entries"] for item in exit_observation["locks"])
assert any("TypeError: argument of type 'MultiheadAttention' is not iterable" in line for line in exit_observation["markers"])
best = confirmed["saved_checkpoints"][0]["meta"]["best_miou"]
assert best == 0.4264346659183502
queue = mon.load_queue(str(ROOT))
task = next(item for item in queue["gpu_queues"]["server-4"] if item["id"] == "M230-HVD")
assert task["pid"] == 2829477 and task["status"] == "running" and task["launch_verified"] is True
before_paused = [item for item in queue["gpu_queues"]["server-4"] if item["id"] in ("M206-CGCA", "M227-LFT")]
lock = mon.acquire_lock(str(ROOT))
assert lock is not None
original_pull = mon.pull_log


def pull_exact(project_dir, host, user, remote_log, cfg_name, state, srv_name=""):
    guard()
    assert (project_dir, host, user, remote_log, state, srv_name) == (
        str(ROOT), "192.168.1.115", "songcl", task["log"], "crashed", "server-4")
    directory = ROOT / "Checkpoints/server_4/hvd_crashed_2e51495f"
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / Path(remote_log).name
    assert not destination.exists()
    subprocess.run(
        ["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8",
         "songcl@192.168.1.115:" + remote_log, str(destination)],
        check=True, capture_output=True, timeout=35,
    )
    assert destination.stat().st_size == exit_observation["log_size"]
    return str(destination)


try:
    guard()
    mon.pull_log = pull_exact
    events = []
    basename = Path(task["config"]).stem
    local_log = mon.finalize_task(str(ROOT), queue, "server-4", "192.168.1.115", "songcl",
                                  task, basename, "crashed", best, "5/50 (partial1449/4686)", "0",
                                  task["log"], events)
    experiment = mon.load_experiment(str(ROOT), "M230-HVD")
    assert experiment["status"] == "crashed"
    experiment.update({
        "training_status": "crashed_runtime_implementation_inconclusive",
        "exact_saved_best": best, "exact_saved_best_epoch": 4,
        "last_complete_checkpoint_epoch": 4, "partial_failed_epoch": 5,
        "partial_failed_step": 1449, "partial_failed_epoch_saved": False,
        "failure_scope": "implementation", "hypothesis_falsified": False,
        "root_cause": "UNKNOWN",
        "error": "TypeError: argument of type 'MultiheadAttention' is not iterable",
        "automatic_restart_or_resume_authorized": False,
        "process_death_confirmation_evidence": {
            "path": (HERE / "hvd_death_confirmation_cpu_checkpoint.json").relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256((HERE / "hvd_death_confirmation_cpu_checkpoint.json").read_bytes()).hexdigest()},
    })
    mon.save_experiment(str(ROOT), experiment)
    after = mon.load_queue(str(ROOT))
    assert not any(item["id"] == "M230-HVD" for item in after["gpu_queues"]["server-4"])
    assert [item for item in after["gpu_queues"]["server-4"] if item["id"] in ("M206-CGCA", "M227-LFT")] == before_paused
    record = {
        "recorded_at": datetime.now(timezone.utc).isoformat(), "status": "crashed",
        "archive_id": experiment["archive_id"], "exact_saved_best": best,
        "last_complete_epoch": 4, "failed_partial_epoch": 5, "failed_partial_step": 1449,
        "original_log_local": local_log, "original_log_sha256": hashlib.sha256(Path(local_log).read_bytes()).hexdigest(),
        "canonical_finalizer": "pipeline_monitor.finalize_task",
        "three_fresh_absence_checks": True, "death_threshold_changed": False,
        "GPU_operations": False, "restart_resume_dispatch_or_crashfix_called": False,
        "events": events,
    }
    with (HERE / "hvd_crash_archive_result.json").open("x", encoding="utf8") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(record, ensure_ascii=False))
finally:
    mon.pull_log = original_pull
    lock.close()
