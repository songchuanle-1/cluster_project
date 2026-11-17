#!/usr/bin/env python
"""Build a compact, change-aware context manifest for one pipeline tick."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


TERMINAL_STATES = {
    "done_complete",
    "done_earlystop",
    "crashed",
    "stopped_unknown",
    "cancelled",
    "withdrawn",
}
ACTIVE_STATES = {"waiting", "claiming", "running"}
DEEP_DECISION_MARKERS = (
    "_manual",
    "_manual_batch",
    "_next_batch",
    "_route_change",
    "_question",
)


def read_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return default


def read_text(path: Path, limit: int = 16000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated by build_tick_context.py]..."


def hash_file(path: Path, tail_bytes: int | None = None) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            if tail_bytes is not None:
                handle.seek(0, os.SEEK_END)
                handle.seek(max(0, handle.tell() - tail_bytes))
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def iso_mtime(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    except OSError:
        return None


def latest_files(path: Path, limit: int, predicate=None) -> list[dict[str, Any]]:
    if not path.is_dir():
        return []
    files = [item for item in path.iterdir() if item.is_file()]
    if predicate is not None:
        files = [item for item in files if predicate(item)]
    files.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    result = []
    for item in files[:limit]:
        result.append(
            {
                "path": item.as_posix(),
                "mtime": iso_mtime(item),
                "bytes": item.stat().st_size,
            }
        )
    return result


def artifact_signature(pipeline_dir: Path) -> list[list[Any]]:
    """Track meaningful research artifacts without including per-tick reports."""
    signature = []
    for name in ("decisions", "analyses", "designs", "reviews", "bugfixes"):
        path = pipeline_dir / name
        latest = latest_files(
            path,
            1,
            (lambda item: item.name != "_index.md") if name == "decisions" else None,
        )
        if latest:
            item = latest[0]
            signature.append([name, item["path"], item["mtime"], item["bytes"]])
        else:
            signature.append([name, None, None, 0])
    return signature


def flatten_queue(queue: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    tasks: list[dict[str, Any]] = []
    states: dict[str, str] = {}
    gpu_queues = queue.get("gpu_queues", {})
    if not isinstance(gpu_queues, dict):
        return tasks, states
    for server, entries in gpu_queues.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            task = dict(entry)
            task["server"] = server
            task_id = str(task.get("id") or task.get("exp_id") or "")
            status = str(task.get("status") or task.get("state") or "unknown")
            if task_id:
                states[task_id] = status
            tasks.append(task)
    return tasks, states


def load_capacity(project_dir: Path) -> tuple[int, list[dict[str, Any]]]:
    path = project_dir / "SERVERS.yaml"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return 0, []
    capacity = 0
    servers = []
    for name, config in (data.get("servers") or {}).items():
        if not isinstance(config, dict) or config.get("role") != "gpu_server":
            continue
        allowed = config.get("allowed_gpus")
        if allowed is None:
            gpu_count = int((config.get("gpu") or {}).get("count") or 0)
            allowed = list(range(gpu_count))
        if not isinstance(allowed, list) or not allowed:
            continue
        max_tasks = max(1, int(config.get("max_tasks_per_gpu") or 1))
        server_capacity = len(allowed) * max_tasks
        capacity += server_capacity
        servers.append(
            {
                "name": name,
                "allowed_gpus": allowed,
                "max_tasks_per_gpu": max_tasks,
                "capacity": server_capacity,
            }
        )
    return capacity, servers


def recent_experiments(path: Path, limit: int = 12) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError:
        return []
    return rows[-limit:]


def compact_task(task: dict[str, Any]) -> dict[str, Any]:
    keep = (
        "id",
        "exp_id",
        "config",
        "status",
        "state",
        "server",
        "gpu",
        "label",
        "depends_on",
        "launched",
        "finished_at",
        "final_best",
        "best_epoch",
        "patience",
        "min_epochs",
        "dispatch_hold",
    )
    return {key: task[key] for key in keep if key in task}


def research_gate_summary(path: Path) -> list[dict[str, Any]]:
    data = read_json(path, {})
    result = []
    for item in data.get("items", []) if isinstance(data, dict) else []:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "id": item.get("id"),
                "status": item.get("status"),
                "gate_passed": item.get("gate_passed"),
                "depends_on": item.get("depends_on", []),
                "next_action": item.get("next_action"),
            }
        )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    parser.add_argument("--monitor-file")
    parser.add_argument("--goal-file")
    parser.add_argument("--monitor-rc", type=int, default=0)
    parser.add_argument("--goal-rc", type=int, default=0)
    parser.add_argument(
        "--design-interval-hours",
        type=float,
        default=float(os.environ.get("CODEX_DESIGN_INTERVAL_HOURS", "6")),
    )
    parser.add_argument(
        "--force-design",
        action="store_true",
        default=os.environ.get("CODEX_FORCE_DESIGN", "0") == "1",
        help="Enter design mode immediately when candidate capacity is available.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(os.environ.get("PROJECT_ROOT", "D:/project"))
    project_dir = root / args.project
    pipeline_dir = project_dir / "pipeline"
    headless_dir = pipeline_dir / "headless"
    context_path = headless_dir / ".tick_context.json"
    state_path = headless_dir / ".tick_context_state.json"
    next_state_path = headless_dir / ".tick_context_state.next.json"
    headless_dir.mkdir(parents=True, exist_ok=True)

    queue_path = pipeline_dir / "queue.json"
    goal_path = pipeline_dir / "goal.json"
    ledger_path = pipeline_dir / "experiments.csv"
    research_queue_path = pipeline_dir / "research_queue.json"
    queue = read_json(queue_path, {})
    goal = read_json(goal_path, {})
    running = read_json(pipeline_dir / "running.json", {})
    tasks, task_states = flatten_queue(queue)
    active_tasks = [compact_task(task) for task in tasks if task_states.get(str(task.get("id") or task.get("exp_id") or "")) in ACTIVE_STATES]
    waiting = [task for task in active_tasks if (task.get("status") or task.get("state")) == "waiting"]
    claiming = [task for task in active_tasks if (task.get("status") or task.get("state")) == "claiming"]
    running_tasks = [task for task in active_tasks if (task.get("status") or task.get("state")) == "running"]
    capacity, servers = load_capacity(project_dir)

    previous = read_json(state_path, {})
    previous_states = previous.get("task_states", {}) if isinstance(previous, dict) else {}
    new_terminal = [
        task_id
        for task_id, status in task_states.items()
        if status in TERMINAL_STATES and previous_states.get(task_id) != status
    ]
    active_signature = sorted(
        [task_id, status]
        for task_id, status in task_states.items()
        if status in ACTIVE_STATES
    )
    goal_hash = hash_file(goal_path)
    ledger_hash = hash_file(ledger_path, tail_bytes=65536)
    gate_summary = research_gate_summary(research_queue_path)
    gate_signature = [
        [item.get("id"), item.get("status"), item.get("gate_passed")]
        for item in gate_summary
    ]
    current_artifact_signature = artifact_signature(pipeline_dir)

    previous_exists = bool(previous)
    change_reasons = []
    if args.monitor_rc != 0:
        change_reasons.append(f"monitor_rc={args.monitor_rc}")
    if args.goal_rc != 0:
        change_reasons.append(f"goal_rc={args.goal_rc}")
    if (headless_dir / ".tick_unhealthy").exists():
        change_reasons.append("previous_tick_unhealthy")
    if new_terminal and previous_exists:
        change_reasons.append("new_terminal:" + ",".join(new_terminal))
    if previous_exists and active_signature != previous.get("active_signature", []):
        change_reasons.append("active_queue_changed")
    if previous_exists and goal_hash != previous.get("goal_hash"):
        change_reasons.append("goal_changed")
    if previous_exists and ledger_hash != previous.get("ledger_hash"):
        change_reasons.append("ledger_changed")
    if previous_exists and gate_signature != previous.get("gate_signature", []):
        change_reasons.append("research_gate_changed")
    if previous_exists and current_artifact_signature != previous.get(
        "artifact_signature", []
    ):
        change_reasons.append("research_artifact_changed")
    if not previous_exists:
        change_reasons.append("context_bootstrap")

    meaningful_change = bool(change_reasons)
    steady_ticks = 0 if meaningful_change else int(previous.get("steady_ticks", 0)) + 1
    now = datetime.now(timezone.utc)
    last_deep_at = previous.get("last_deep_at")
    deep_age_hours = None
    if last_deep_at:
        try:
            deep_age_hours = (now - datetime.fromisoformat(last_deep_at)).total_seconds() / 3600
        except ValueError:
            deep_age_hours = None

    pipeline_policy = goal.get("pipeline_policy") or {}
    steady_ticks_before_design = max(
        1, int(pipeline_policy.get("steady_ticks_before_design") or 2)
    )
    fill_to_capacity = bool(pipeline_policy.get("fill_to_capacity", True))
    design_buffer = max(0, int(pipeline_policy.get("design_buffer") or 0))
    max_candidates_per_design_tick = max(
        0,
        int(
            pipeline_policy.get("max_candidates_per_design_tick")
            if pipeline_policy.get("max_candidates_per_design_tick") is not None
            else capacity
        ),
    )
    active_count = len(waiting) + len(claiming) + len(running_tasks)
    target_active = capacity + design_buffer if fill_to_capacity else 0
    open_slots = max(0, target_active - active_count)
    candidate_budget = min(max_candidates_per_design_tick, open_slots)
    shallow_queue = candidate_budget > 0
    cooldown_ready = deep_age_hours is None or deep_age_hours >= args.design_interval_hours
    design_due = (
        candidate_budget > 0
        and (
            args.force_design
            or (
                steady_ticks >= steady_ticks_before_design
                and cooldown_ready
            )
        )
    )
    if design_due:
        mode = "design"
        if args.force_design:
            mode_reason = (
                f"user-forced design; active={active_count} below "
                f"target={target_active}; candidate_budget={candidate_budget}"
            )
        else:
            mode_reason = (
                f"active={active_count} below target={target_active}; "
                f"candidate_budget={candidate_budget}; "
                f"{steady_ticks} steady ticks; deep-review cooldown ready"
            )
        last_deep_at = now.isoformat()
    elif meaningful_change:
        mode = "event"
        mode_reason = "; ".join(change_reasons)
    else:
        mode = "steady"
        mode_reason = (
            f"no structural state change; active={active_count}/{target_active}; "
            f"candidate_budget={candidate_budget}; "
            f"steady_ticks={steady_ticks}"
        )

    recent_decisions = latest_files(
        pipeline_dir / "decisions",
        6,
        lambda item: item.name != "_index.md"
        and any(marker in item.stem for marker in DEEP_DECISION_MARKERS),
    )
    pending_questions = latest_files(
        pipeline_dir / "decisions",
        5,
        lambda item: "_question" in item.stem
        and (now.timestamp() - item.stat().st_mtime) <= 86400,
    )
    recent_analyses = latest_files(pipeline_dir / "analyses", 8)
    recent_designs = latest_files(pipeline_dir / "designs", 4)
    recent_reviews = latest_files(pipeline_dir / "reviews", 4)
    recent_bugfixes = latest_files(pipeline_dir / "bugfixes", 3)
    recent_reports = latest_files(
        pipeline_dir / "reports",
        1,
        lambda item: item.name.startswith("summary_"),
    )

    if mode == "steady":
        suggested_reads = [
            str(pipeline_dir / "codex_memory.md"),
            *(entry["path"] for entry in recent_reports),
        ]
    elif mode == "event":
        suggested_reads = [
            str(pipeline_dir / "codex_memory.md"),
            str(goal_path),
            *(entry["path"] for entry in recent_decisions[:3]),
            *(entry["path"] for entry in recent_analyses[:3]),
            *(entry["path"] for entry in recent_reports),
        ]
    else:
        suggested_reads = [
            str(pipeline_dir / "codex_memory.md"),
            str(goal_path),
            str(ledger_path),
            *(entry["path"] for entry in recent_decisions),
            *(entry["path"] for entry in recent_analyses),
            *(entry["path"] for entry in recent_designs),
            *(entry["path"] for entry in recent_reviews),
        ]
    suggested_reads = list(dict.fromkeys(suggested_reads))

    monitor_output = read_text(Path(args.monitor_file)) if args.monitor_file else ""
    goal_output = read_text(Path(args.goal_file)) if args.goal_file else ""
    context = {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "project": args.project,
        "mode": mode,
        "mode_reason": mode_reason,
        "rules": {
            "steady": "Use snapshot plus targeted live evidence. Do not scan history.",
            "event": "Inspect only files tied to listed changes.",
            "design": "Use manifest first; expand older evidence only by explicit ID/reference.",
            "never_read_normally": [
                "pipeline/headless/tick_*.log",
                "entire decisions/ directory",
                "entire analyses/ directory",
                "entire reports/ directory",
            ],
        },
        "preflight": {
            "monitor_rc": args.monitor_rc,
            "goal_rc": args.goal_rc,
            "monitor_output": monitor_output,
            "goal_output": goal_output,
        },
        "goal": {
            "description": goal.get("description"),
            "metric": goal.get("metric"),
            "baseline_experiment_id": goal.get("baseline_experiment_id"),
            "constraint_count": len(goal.get("constraints") or []),
            "banned_count": len(goal.get("banned") or []),
            "path": goal_path.as_posix(),
        },
        "queue": {
            "capacity": capacity,
            "target_active": target_active,
            "active_count": active_count,
            "candidate_budget": candidate_budget,
            "waiting_count": len(waiting),
            "claiming_count": len(claiming),
            "running_count": len(running_tasks),
            "active_tasks": active_tasks,
            "status_counts": {
                status: sum(1 for value in task_states.values() if value == status)
                for status in sorted(set(task_states.values()))
            },
            "running_map": running,
            "servers": servers,
        },
        "changes": {
            "reasons": change_reasons,
            "new_terminal_ids": new_terminal if previous_exists else [],
            "steady_ticks": steady_ticks,
            "shallow_queue": shallow_queue,
            "design_due": design_due,
            "force_design": args.force_design,
            "design_interval_hours": args.design_interval_hours,
            "steady_ticks_before_design": steady_ticks_before_design,
            "fill_to_capacity": fill_to_capacity,
            "design_buffer": design_buffer,
            "max_candidates_per_design_tick": max_candidates_per_design_tick,
        },
        "research_gates": gate_summary,
        "recent_experiments": recent_experiments(ledger_path),
        "manifests": {
            "decisions": recent_decisions,
            "pending_questions_24h": pending_questions,
            "analyses": recent_analyses,
            "designs": recent_designs,
            "reviews": recent_reviews,
            "bugfixes": recent_bugfixes,
            "latest_report": recent_reports,
            "suggested_reads": suggested_reads,
        },
    }
    context_path.write_text(
        json.dumps(context, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    state = {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "mode": mode,
        "steady_ticks": steady_ticks,
        "last_deep_at": last_deep_at,
        "task_states": task_states,
        "active_signature": active_signature,
        "goal_hash": goal_hash,
        "ledger_hash": ledger_hash,
        "gate_signature": gate_signature,
        "artifact_signature": current_artifact_signature,
    }
    next_state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"mode={mode}")
    print(f"reason={mode_reason}")
    print(f"context={context_path.as_posix()}")
    print(f"pending_state={next_state_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
