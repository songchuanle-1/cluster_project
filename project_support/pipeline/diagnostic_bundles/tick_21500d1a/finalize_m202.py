"""Evidence-bound exact-run terminal archival through the canonical finalizer."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

from audit_terminal import guard, save, ROOT, OUT, BASE, tick
import pipeline_monitor as monitor

guard()
audit = tick.load(OUT / "terminal_observation.json")
assert not audit["pid_exists"] and not audit["exact_training_pids"]
assert audit["explicit_earlystop_matches"] and all(row == ["29", "10"] for row in audit["explicit_earlystop_matches"])
assert not audit["stdout"]["tail_crash_markers"] and audit["frozen_sources_match"]
assert all(value == "acquired_and_released" for value in audit["locks"].values())
assert audit["gpu0"]["compute_contexts"] == ""
name = BASE + "_hds_canon_r1"
queue = monitor.load_queue(str(ROOT))
matches = [task for task in queue["gpu_queues"]["server-4"] if task.get("id") == "M202-HDS"]
assert len(matches) == 1 and matches[0]["status"] == "running"
task = matches[0]
before = monitor.load_experiment(str(ROOT), "M202-HDS")
assert before["pid"] == 1592337 and before["status"] == "running"
save("experiment_before_finalization.json", before)
save("queue_before_finalization.json", queue)
remote_log = audit["native_scalar_log"]["path"]
local_log = OUT / "m202_resumed_native.log"
response = subprocess.run(["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10",
                           "songcl@192.168.1.115:" + remote_log, str(local_log)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
assert response.returncode == 0, response.stderr
assert tick.digest(local_log) == audit["native_scalar_log"]["sha256"]
best = max(audit["native_scalar_log"]["miou"])
events = []
original_pull = monitor.pull_log
def exact_pull(project_dir, host, user, path, cfg, state, srv):
    assert Path(project_dir) == ROOT and host == "192.168.1.115" and user == "songcl"
    assert path == remote_log and cfg == name and state == "done_earlystop" and srv == "server-4"
    return str(local_log)
monitor.pull_log = exact_pull
try:
    guard()
    archived = monitor.finalize_task(str(ROOT), queue, "server-4", "192.168.1.115", "songcl", task,
                                    name, "done_earlystop", best, "29/50", 0, remote_log, events)
finally:
    monitor.pull_log = original_pull
after = monitor.load_experiment(str(ROOT), "M202-HDS")
assert after["status"] == "done_earlystop" and after["final_best"] == "0.4947"
assert not any(t.get("id") == "M202-HDS" for group in monitor.load_queue(str(ROOT))["gpu_queues"].values() for t in group)
running = monitor.load_running(str(ROOT))
assert "M202-HDS" not in json.dumps(running)
def ev(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": tick.digest(path)}
result = {"observed_at": datetime.now(timezone.utc).isoformat(), "state": "done_earlystop", "epoch": 29,
          "native_stopped_at": "2026-10-17T13:12:28+08:00", "no_improvement": 10,
          "best_miou": best, "best_epoch": 8 + audit["native_scalar_log"]["miou"].index(best),
          "baseline": .4894, "historical_champion": .5020, "target": .51,
          "vs_baseline": best - .4894, "vs_champion": best - .5020,
          "events": events, "native_log": ev(local_log), "all_frozen_sources_match": True,
          "transport_override": "Verified exact current native scalar log only; canonical finalize_task/queue/running/ledger/analysis unchanged. No broad log pull or repeated preflight.",
          "scientific_scope": "This trained HDS realization did not improve the historical champion; not falsification of all hierarchical point-feature mechanisms. Scene-paired uncertainty/subgroup harm and whole-run peak remain unmeasured.",
          "new_training_launches": 0, "signals": 0, "resumes": 0}
save("terminal_finalization.json", result)
work = tick.load(ROOT / "pipeline/research_work.json")
primary = next(c for c in work["candidates"] if c["id"] == "m95-hierarchical-mask-feature-path-audit")
assert primary["stage"] == "training" and len(primary["revision_history"]) == 2
primary.update(stage="complete", outcome="trained_realization_not_improved_over_historical_champion",
               scientific_status="Trained HDS best.4946560264<champion.5020 and target.5100; native earlystop29/patience10, not a crash. General hierarchical-point-feature hypothesis and scene-paired uncertainty remain unresolved.",
               next_action="Preserve this terminal realization and frozen post-training evaluation. Complete aligned native evidence validation/paired evaluation where exact references exist; no blind restart, revision3, VAL-selected mechanism or M201 recovery. A future distinct mainline mechanism needs fresh TRAIN-only error evidence and all original gates.")
primary["evidence"].extend([ev(OUT / "terminal_observation.json"), ev(OUT / "terminal_finalization.json")])
guard()
tick.save(ROOT / "pipeline/research_work.json", work)
print(json.dumps({key: result[key] for key in ("state", "epoch", "best_miou", "best_epoch", "vs_baseline", "vs_champion", "new_training_launches")}, indent=2))
