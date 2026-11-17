#!/usr/bin/env python
"""Build a compact, change-aware context manifest for one pipeline tick."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml
import closure
import tick_efficiency
import experiment_first


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
RESOURCE_BLOCKERS = tick_efficiency.RESOURCE_BLOCKERS
HUMAN_BLOCKERS = tick_efficiency.HUMAN_BLOCKERS
RESEARCH_BLOCKERS = tick_efficiency.RESEARCH_BLOCKERS


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


def ledger_states(path: Path) -> dict[str, str]:
    """Return the latest recorded state for each experiment in the CSV ledger."""
    states: dict[str, str] = {}
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                experiment_id = str(row.get("id") or "").strip()
                state = str(row.get("state") or row.get("status") or "").strip()
                if experiment_id and state:
                    states[experiment_id] = state
    except OSError:
        pass
    return states


def experiment_file_states(path: Path) -> dict[str, str]:
    """Return lifecycle states persisted in pipeline/experiments/*.json."""
    states: dict[str, str] = {}
    if not path.is_dir():
        return states
    for item in path.glob("*.json"):
        data = read_json(item, {})
        if not isinstance(data, dict):
            continue
        experiment_id = str(data.get("id") or item.stem).strip()
        state = str(data.get("status") or data.get("state") or "").strip()
        if experiment_id and state:
            states[experiment_id] = state
    return states


def lifecycle_states(
    queue_states: dict[str, str],
    ledger: dict[str, str],
    experiment_files: dict[str, str],
) -> dict[str, str]:
    """Merge durable lifecycle sources, preferring live queue state."""
    states = dict(ledger)
    states.update(experiment_files)
    states.update(queue_states)
    return states


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
        if config.get("dispatch_enabled", True) is False:
            continue
        max_tasks = max(1, int(config.get("max_tasks_per_gpu") or 1))
        server_capacity = len(allowed) * max_tasks
        global_task_cap = config.get("max_tasks")
        if global_task_cap is not None:
            server_capacity = min(server_capacity, max(1, int(global_task_cap)))
        capacity += server_capacity
        servers.append(
            {
                "name": name,
                "allowed_gpus": allowed,
                "max_tasks_per_gpu": max_tasks,
                "max_tasks": global_task_cap,
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
        "admission_error",
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


def blocked_recheck(
    project: Path, candidate: dict, previous: dict, signals: dict, now: datetime
) -> tuple[bool, dict]:
    """Back off scoped holds; a wakeup never grants permission or scientific PASS."""
    kind = candidate.get("blocker_kind")
    try:
        retry = datetime.fromisoformat(candidate["retry_after"])
        if retry.tzinfo is None:
            raise ValueError("Naive retry")
    except (KeyError, TypeError, ValueError):
        return True, {}
    if kind not in RESOURCE_BLOCKERS | HUMAN_BLOCKERS | RESEARCH_BLOCKERS:
        return retry <= now, {}
    watched = {}
    if kind in RESEARCH_BLOCKERS:
        if not tick_efficiency.parkable_block(candidate):
            return True, {}
        try:
            for entry in candidate["evidence"]:
                closure.artifact(project, entry)
                watched[entry["path"]] = entry["sha256"]
        except (KeyError, TypeError, ValueError, OSError):
            return True, {}
    base = project.resolve()
    paths = candidate.get("wake_paths", [])
    if not isinstance(paths, list):
        return True, {}
    for relative in paths:
        if not isinstance(relative, str):
            return True, {}
        path = (base / relative).resolve()
        if not path.is_relative_to(base):
            return True, {}
        watched[relative] = hash_file(path) if path.is_file() else None
    signature = hashlib.sha256(json.dumps({
        "kind": kind,
        "server": candidate.get("required_server"),
        "condition": candidate.get("unblock_condition"),
        "goal": signals["goal"],
        "servers": signals["servers"],
        "queue": signals.get("queue") if kind in RESOURCE_BLOCKERS else None,
        "watched": watched,
    }, sort_keys=True).encode()).hexdigest()
    changed = bool(previous) and previous.get("signature") != signature
    interval = timedelta(hours=1 if kind in RESOURCE_BLOCKERS else 4)
    try:
        last = datetime.fromisoformat(previous["last_check_at"])
        next_check = max(retry, last + interval) if last.tzinfo else retry
    except (KeyError, TypeError, ValueError):
        next_check = retry
    due = changed or now >= next_check
    state = {
        "signature": signature,
        "last_check_at": now.isoformat() if due else previous.get("last_check_at"),
        "next_check_at": (now + interval if due else next_check).isoformat(),
    }
    return due, state


def research_funnel(project: Path, candidates: list, observed: bool) -> dict:
    """Cumulative bookkeeping, not a scientific acceptance or success rate."""
    if not observed:
        return {"observed": False}
    scopes = Counter(
        c.get("failure_scope") if c.get("failure_scope") in
        ("implementation", "inconclusive", "hypothesis") else "unclassified"
        for c in candidates if c.get("stage") == "rejected")
    receipts = project / "pipeline/admissions"
    return {
        "observed": True,
        "candidate_records": len(candidates),
        "stages": dict(Counter(c.get("stage") if c.get("stage") in
                              closure.STAGES + ("closed",) else "unknown"
                              for c in candidates)),
        "rejected_scopes": dict(scopes),
        "implementation_revisions": sum(len(c.get("revision_history", []))
                                        for c in candidates),
        "receipt_files": len(list(receipts.glob("*.json"))) if receipts.is_dir() else 0,
        "note": "Cumulative records; receipts may include revisions/retries, not success rates.",
    }


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
    durable_states = lifecycle_states(
        task_states,
        ledger_states(ledger_path),
        experiment_file_states(pipeline_dir / "experiments"),
    )
    all_active_tasks = [compact_task(task) for task in tasks if task_states.get(str(task.get("id") or task.get("exp_id") or "")) in ACTIVE_STATES]
    capacity, servers = load_capacity(project_dir)
    dispatch_servers = {server["name"] for server in servers}
    active_tasks = [
        task for task in all_active_tasks
        if task.get("server") in dispatch_servers
    ]
    waiting = [task for task in active_tasks if (task.get("status") or task.get("state")) == "waiting"]
    claiming = [task for task in active_tasks if (task.get("status") or task.get("state")) == "claiming"]
    running_tasks = [task for task in active_tasks if (task.get("status") or task.get("state")) == "running"]

    previous = read_json(state_path, {})
    previous_states = (
        previous.get("lifecycle_states", previous.get("task_states", {}))
        if isinstance(previous, dict)
        else {}
    )
    new_terminal = [
        task_id
        for task_id, status in durable_states.items()
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
    closure_enabled = closure.enabled(project_dir)
    simple_policy = experiment_first.effective(project_dir) if closure_enabled else {}
    simple = bool(simple_policy)
    work_path = pipeline_dir / "research_work.json"
    work_ledger = read_json(work_path, {})
    work_candidates = work_ledger.get("candidates", [])
    work_pending = [c for c in work_candidates
                    if c.get("stage") not in ("training", "complete", "rejected", "closed")
                    ] if closure_enabled else []
    work_due = []
    blocked_rechecks = {}
    now = datetime.now(timezone.utc)
    wake_signals = {
        "goal": goal_hash,
        "servers": hash_file(project_dir / "SERVERS.yaml"),
        "queue": active_signature,
    }
    for candidate in work_pending:
        if candidate.get("stage") == "blocked":
            if candidate.get("blocker_kind") == "exclusive_gpu_slot":
                if not closure.exclusive_gpu_slot_available(candidate, servers, active_tasks):
                    continue
                work_due.append(candidate)
                continue
            due, retry_state = blocked_recheck(
                project_dir, candidate,
                previous.get("blocked_rechecks", {}).get(candidate["id"], {}),
                wake_signals, now)
            if retry_state:
                blocked_rechecks[candidate["id"]] = retry_state
            if not due:
                continue
        work_due.append(candidate)
    stages = ("deployment", "admission", "validation", "implementation", "design", "diagnosis")
    work_due.sort(key=lambda c: stages.index(c["stage"]) if c["stage"] in stages else len(stages))
    monitor_output = read_text(Path(args.monitor_file)) if args.monitor_file else ""
    goal_output = read_text(Path(args.goal_file)) if args.goal_file else ""
    operational_issues = tick_efficiency.monitor_issues(monitor_output)
    change_reasons = []
    if previous_exists and operational_issues != previous.get("operational_issues", []):
        change_reasons.append("operational_issues_changed")
    if args.monitor_rc != 0:
        change_reasons.append(f"monitor_rc={args.monitor_rc}")
    if args.goal_rc not in (0, 1, 4):
        change_reasons.append(f"goal_rc={args.goal_rc}")
    if previous_exists and args.goal_rc != previous.get("goal_rc", 0):
        change_reasons.append("goal_phase_changed")
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
    work_hash = hash_file(pipeline_dir / "research_work.json")
    if previous_exists and work_hash != previous.get("work_hash"):
        change_reasons.append("research_work_changed")
    if not previous_exists:
        change_reasons.append("context_bootstrap")

    meaningful_change = bool(change_reasons)
    steady_ticks = 0 if meaningful_change else int(previous.get("steady_ticks", 0)) + 1
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
    design_interval_hours = max(
        0.0,
        float(
            pipeline_policy.get("design_interval_hours")
            if pipeline_policy.get("design_interval_hours") is not None
            else args.design_interval_hours
        ),
    )
    fill_to_capacity = bool(pipeline_policy.get("fill_to_capacity", True))
    design_buffer = max(0, int(pipeline_policy.get("design_buffer") or 0))
    max_candidates_per_design_tick = max(
        0,
        int(
            pipeline_policy.get("max_candidates_per_design_tick")
            if pipeline_policy.get("max_candidates_per_design_tick") is not None
            else simple_policy["max_new_candidates"] if simple else capacity
        ),
    )
    active_count = len(waiting) + len(claiming) + len(running_tasks)
    ready_waiting = [t for t in waiting if tick_efficiency.ready_waiting(t, durable_states)]
    if simple and fill_to_capacity:
        design_buffer = simple_policy["waiting_target"]
        max_candidates_per_design_tick = min(
            max_candidates_per_design_tick, simple_policy["max_new_candidates"])
        active_count = len(ready_waiting) + len(claiming) + len(running_tasks)
    target_active = capacity + design_buffer if fill_to_capacity else 0
    open_slots = max(0, target_active - active_count)
    candidate_budget = min(max_candidates_per_design_tick, open_slots)
    reserve_enabled = (closure_enabled and args.monitor_rc == 0 and args.goal_rc == 0
                       and capacity > 0 and fill_to_capacity
                       and (simple or pipeline_policy.get("research_on_capacity_gap") is True))
    reserve_target = max(0, int(pipeline_policy.get("research_reserve_target", 2))
                         ) if reserve_enabled else 0
    parked = [c for c in work_pending if tick_efficiency.parkable_block(c)
              and c["id"] in blocked_rechecks]
    parked_ids = {c["id"] for c in parked}
    actionable = [c for c in work_pending if c["id"] not in parked_ids]
    all_pending_ids = tick_efficiency.pending_ids(work_pending, all_active_tasks)
    total_pending_count = len(all_pending_ids)
    reserve_ids = tick_efficiency.pending_ids(actionable, waiting + claiming)
    reserve_count = len(reserve_ids)
    pending_limit = None
    if reserve_enabled and reserve_target > 0:
        pending_limit = pipeline_policy.get("research_pending_limit", max(8, reserve_target * 2))
        if (not isinstance(pending_limit, int) or isinstance(pending_limit, bool)
                or pending_limit < 0):
            raise ValueError("research_pending_limit must be a nonnegative integer")
    reserve_budget = min(max_candidates_per_design_tick,
                         max(0, reserve_target - reserve_count))
    if pending_limit is not None:
        reserve_budget = min(reserve_budget, max(0, pending_limit - len(all_pending_ids)))
    if simple:
        parked = [c for c in work_pending if c.get("stage") == "blocked"]
        parked_ids = {c["id"] for c in parked}
        actionable = [c for c in work_pending if c["id"] not in parked_ids]
        all_pending_ids = tick_efficiency.pending_ids(
            work_pending, all_active_tasks, actionable_only=True, states=durable_states)
        reserve_ids = tick_efficiency.pending_ids(
            actionable, waiting + claiming, actionable_only=True, states=durable_states)
        reserve_count = len(reserve_ids)
        pending_limit = simple_policy["actionable_limit"]
        reserve_target = max(0, target_active - len(running_tasks)) if reserve_enabled else 0
        reserve_budget = min(
            max_candidates_per_design_tick, max(0, reserve_target - reserve_count),
            max(0, pending_limit - len(all_pending_ids)))
        if not reserve_enabled:
            candidate_budget = 0
    limit_reached = pending_limit is not None and len(all_pending_ids) >= pending_limit
    reserve_only = not simple and candidate_budget == 0 and reserve_budget > 0
    shallow_queue = candidate_budget > 0
    cooldown_ready = deep_age_hours is None or deep_age_hours >= design_interval_hours
    design_due = (
        candidate_budget > 0
        and (
            simple or pipeline_policy.get("research_on_capacity_gap") is True
            or
            args.force_design
            or (
                steady_ticks >= steady_ticks_before_design
                and cooldown_ready
            )
        )
    )
    design_due = design_due or reserve_only
    # Rechecking a blocked candidate is an event, not proof of research progress.
    if pending_limit is not None and reserve_budget == 0 and work_pending and not actionable:
        design_due = False
    if pending_limit == 0 and not work_pending:
        design_due = False
    if args.monitor_rc != 0 or args.goal_rc != 0:
        design_due = False
    hold = (not simple and not args.force_design and not work_due and args.monitor_rc == 0 and args.goal_rc in (0, 1, 4)
            and not (headless_dir / ".tick_unhealthy").exists()
            and "goal_phase_changed" not in change_reasons
            and tick_efficiency.cooldown_active(
                project_dir, now, candidate_backfill=bool(parked and reserve_budget > 0)))
    if hold:
        work_due = []
        design_due = False
        # Research output from the preceding completed tick is not a new trigger.
        change_reasons = [r for r in change_reasons
                          if r not in ("research_artifact_changed", "research_work_changed")]
        meaningful_change = bool(change_reasons)
        steady_ticks = 0 if meaningful_change else int(previous.get("steady_ticks", 0)) + 1
    blocked_wait = bool(
        (not args.force_design or limit_reached) and reserve_enabled and reserve_target > 0
        and reserve_budget == 0 and work_pending and not work_due
        and len(parked) == len(work_pending))
    blocked_wait_signature = None
    deferred_until = None
    if blocked_wait:
        design_due = False
        blocked_wait_signature = tick_efficiency.research_signature(project_dir)
        deferred_until = min(datetime.fromisoformat(
            blocked_rechecks.get(c["id"], {}).get("next_check_at") or c["retry_after"])
            for c in work_pending).isoformat()
        # A new or changed wait still receives event validation before quiet polling.
        if not hold and blocked_wait_signature != previous.get("blocked_wait_signature"):
            change_reasons.append("blocked_wait_changed")
            meaningful_change = True
            steady_ticks = 0
    if work_due and design_due:
        mode = "design"
        mode_reason = (
            "resume unfinished candidate stages, then continue capacity-gap "
            f"or reserve design in this tick; candidate_budget={candidate_budget}; "
            f"research_reserve_budget={reserve_budget}"
        )
        last_deep_at = now.isoformat()
    elif work_due:
        mode = "event"
        mode_reason = "resume unfinished candidate stages before new design"
    elif design_due:
        mode = "design"
        if reserve_only:
            mode_reason = (
                f"prepare bounded research reserve {reserve_count}/{reserve_target}; "
                "candidate_budget=0, no new queue entries or launches"
            )
        elif args.force_design:
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
    elif blocked_wait:
        mode = "steady"
        mode_reason = (
            "pending limit or queued work awaits unchanged evidenced holds; "
            "monitoring and goal checks continue without new candidate bootstrap"
        )
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
    terminal_experiments = [
        {
            "id": task_id,
            "state": durable_states[task_id],
            "path": (pipeline_dir / "experiments" / f"{task_id}.json").as_posix(),
        }
        for task_id in new_terminal
        if (pipeline_dir / "experiments" / f"{task_id}.json").is_file()
    ]
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
            *(entry["path"] for entry in terminal_experiments),
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

    context = {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "deadline_at": (now + timedelta(seconds=3600)).isoformat(),
        "project": args.project,
        "mode": mode,
        "mode_reason": mode_reason,
        "experiment_first": simple_policy,
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
            "operational_issues": operational_issues,
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
            "ready_waiting_count": len(ready_waiting),
            "claiming_count": len(claiming),
            "running_count": len(running_tasks),
            "active_tasks": active_tasks,
            "monitored_active_tasks": all_active_tasks,
            "status_counts": {
                status: sum(1 for value in task_states.values() if value == status)
                for status in sorted(set(task_states.values()))
            },
            "recorded_ids": sorted(task_states),
            "known_experiment_ids": sorted(durable_states),
            "dependency_states": {d: durable_states.get(d) for t in tasks
                                  for d in (t.get("depends_on") or [])},
            "running_map": running,
            "servers": servers,
        },
        "changes": {
            "reasons": change_reasons,
            "new_terminal_ids": new_terminal if previous_exists else [],
            "steady_ticks": steady_ticks,
            "shallow_queue": shallow_queue,
            "design_due": design_due,
            "research_cooldown": hold,
            "force_design": args.force_design,
            "design_interval_hours": design_interval_hours,
            "steady_ticks_before_design": steady_ticks_before_design,
            "fill_to_capacity": fill_to_capacity,
            "design_buffer": design_buffer,
            "max_candidates_per_design_tick": max_candidates_per_design_tick,
        },
        "research_gates": gate_summary,
        "research_work": {
            "path": str(pipeline_dir / "research_work.json"),
            "candidates": work_pending,
            "due_ids": [c["id"] for c in work_due],
            "blocked_rechecks": blocked_rechecks,
            "reserve_target": reserve_target,
            "reserve_count": reserve_count,
            "reserve_budget": reserve_budget,
            "reserve_only": reserve_only,
            "pending_ids": sorted(all_pending_ids),
            "pending_scope": "actionable" if simple else "all",
            "total_pending_count": total_pending_count,
            "creation_budget": reserve_budget if simple else None,
            "pending_count": len(all_pending_ids),
            "pending_limit": pending_limit,
            "parked_count": total_pending_count - len(all_pending_ids) if simple
                            else len(all_pending_ids - reserve_ids),
            "parked_ids": sorted(parked_ids),
            "human_wait_count": sum(c.get("blocker_kind") in HUMAN_BLOCKERS for c in parked),
            "resource_wait_count": sum(c.get("blocker_kind") in RESOURCE_BLOCKERS for c in parked),
            "research_wait_count": sum(c.get("blocker_kind") in RESEARCH_BLOCKERS for c in parked),
            "unclassified_block_count": sum(c.get("stage") == "blocked" for c in actionable),
            "deferred": blocked_wait,
            "deferred_until": deferred_until,
            "deferred_reason": ("pending_limit" if limit_reached else "queued_work")
                               if blocked_wait else None,
            "human_actions": [
                {"id": c["id"], "next_action": c.get("next_action"),
                 "retry_after": c.get("retry_after")}
                for c in work_pending
                if c.get("stage") == "blocked" and c.get("blocker_kind") in HUMAN_BLOCKERS],
            "progress_baselines": {c["id"]: closure.candidate_progress(c)
                                   for c in work_candidates},
            "revision_baselines": {
                c["id"]: {k: c[k] for k in ("id", "stage", "hypothesis", "hypothesis_id",
                                           "failure_scope", "revision_history",
                                           "implementation_revision_authorization") if k in c}
                for c in work_candidates},
            "instruction": (
                "Follow references/experiment_first.md. Reuse scoped authorization. "
                "Prefer a runnable variant and native smoke this tick, within creation/admission "
                "budgets. Park holds without reopening them; one real test outcome may finish."
            ) if simple else (
                "Resume the most advanced executable due candidate first and keep advancing "
                "it through its remaining gates within this tick. A blocked retry only rechecks evidence, "
                "never grants permission. Parked candidates do not consume actionable reserve; "
                "prepare independent authorized work within reserve_budget and pending_limit. "
                "Do not reopen held routes or duplicate reviews. Goal phase and admission "
                "constraints still apply."
            ),
        },
        "research_funnel": research_funnel(project_dir, work_candidates, work_path.is_file()),
        "recent_experiments": recent_experiments(ledger_path),
        "manifests": {
            "decisions": recent_decisions,
            "pending_questions_24h": pending_questions,
            "analyses": recent_analyses,
            "designs": recent_designs,
            "reviews": recent_reviews,
            "bugfixes": recent_bugfixes,
            "terminal_experiments": terminal_experiments,
            "latest_report": recent_reports,
            "suggested_reads": suggested_reads,
        },
    }
    context_path.write_text(
        json.dumps(context, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (headless_dir / ".tick_model_view.json").write_text(
        json.dumps(tick_efficiency.compact_view(context), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    state = {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "mode": mode,
        "steady_ticks": steady_ticks,
        "last_deep_at": last_deep_at,
        "task_states": task_states,
        "lifecycle_states": durable_states,
        "active_signature": active_signature,
        "goal_hash": goal_hash,
        "goal_rc": args.goal_rc,
        "operational_issues": operational_issues,
        "work_hash": work_hash,
        "ledger_hash": ledger_hash,
        "gate_signature": gate_signature,
        "artifact_signature": current_artifact_signature,
        "blocked_rechecks": blocked_rechecks,
        "blocked_wait_signature": blocked_wait_signature,
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
