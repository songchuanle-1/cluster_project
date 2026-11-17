#!/usr/bin/env python
"""Render a six-section steady-state report without starting an LLM."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def clean(value: Any) -> str:
    if value is None or value == "":
        return "-"
    return str(value).replace("|", "\\|").replace("\n", " ")


def prune_reports(reports_dir: Path, now: datetime) -> int:
    removed = 0
    cutoff = now - timedelta(hours=24)
    for path in reports_dir.glob("summary_*.md"):
        stamp = path.name.removeprefix("summary_").split("_manual", 1)[0]
        stamp = stamp.removesuffix(".md")
        try:
            created = datetime.strptime(stamp, "%Y%m%d-%H%M%S")
        except ValueError:
            continue
        if created < cutoff:
            path.unlink()
            removed += 1
    return removed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    parser.add_argument("--context")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(os.environ.get("PROJECT_ROOT", "D:/project"))
    project_dir = root / args.project
    pipeline_dir = project_dir / "pipeline"
    context_path = (
        Path(args.context)
        if args.context
        else pipeline_dir / "headless" / ".tick_context.json"
    )
    context = load_json(context_path)
    if context.get("mode") != "steady":
        raise SystemExit(f"refusing non-steady context: {context.get('mode')}")

    now = datetime.now()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    reports_dir = pipeline_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    removed = prune_reports(reports_dir, now)
    output_path = reports_dir / f"summary_{stamp}.md"

    goal = context.get("goal", {})
    queue = context.get("queue", {})
    changes = context.get("changes", {})
    preflight = context.get("preflight", {})
    metric = goal.get("metric") or {}
    active = queue.get("active_tasks") or []
    running = [
        task
        for task in active
        if (task.get("status") or task.get("state")) == "running"
    ]
    waiting = [
        task
        for task in active
        if (task.get("status") or task.get("state")) == "waiting"
    ]
    pending = (
        context.get("manifests", {}).get("pending_questions_24h", [])
        or []
    )

    lines = [
        "=" * 80,
        f"  Research Pipeline Report - {args.project}",
        f"  {now.strftime('%Y-%m-%d %H:%M:%S')} Asia/Shanghai (steady, no LLM)",
        "=" * 80,
        "",
        "## 0. Goal Status",
        f"- Description: {clean(goal.get('description'))}",
        (
            f"- Target: {clean(metric.get('name'))} >= "
            f"{clean(metric.get('target'))} on {clean(metric.get('dataset'))}"
        ),
        f"- Goal preflight exit: {preflight.get('goal_rc', '-')}",
        "",
        "```text",
        str(preflight.get("goal_output") or "").strip(),
        "```",
        "",
        "## 1. GPU Overview",
        f"- Monitor preflight exit: {preflight.get('monitor_rc', '-')}",
        "- The monitor ran before this report and remains responsible for live GPU checks, early-stop, reconciliation, and FIFO dispatch.",
        "",
        "```text",
        str(preflight.get("monitor_output") or "").strip(),
        "```",
        "",
        "## 2. Running Experiments",
        "| ID | Config | Server | GPU | Status | Launched |",
        "|---|---|---|---|---|---|",
    ]
    if running:
        for task in running:
            lines.append(
                "| {id} | {config} | {server} | {gpu} | {status} | {launched} |".format(
                    id=clean(task.get("id") or task.get("exp_id")),
                    config=clean(task.get("config")),
                    server=clean(task.get("server")),
                    gpu=clean(task.get("gpu")),
                    status=clean(task.get("status") or task.get("state")),
                    launched=clean(task.get("launched")),
                )
            )
    else:
        lines.append("| - | - | - | - | none | - |")

    lines.extend(
        [
            "",
            "## 3. Queue Status",
            "| Position | ID | Config | Status | Depends On | Server |",
            "|---|---|---|---|---|---|",
        ]
    )
    if waiting:
        for index, task in enumerate(waiting, start=1):
            lines.append(
                "| {position} | {id} | {config} | waiting | {depends} | {server} |".format(
                    position=index,
                    id=clean(task.get("id") or task.get("exp_id")),
                    config=clean(task.get("config")),
                    depends=clean(",".join(task.get("depends_on") or [])),
                    server=clean(task.get("server")),
                )
            )
    else:
        lines.append("| - | - | - | no waiting tasks | - | - |")
    lines.extend(
        [
            (
                f"- Active capacity: {queue.get('active_count', 0)} active "
                f"({queue.get('running_count', 0)} running, "
                f"{queue.get('claiming_count', 0)} claiming, "
                f"{queue.get('waiting_count', 0)} waiting) / "
                f"{queue.get('target_active', queue.get('capacity', 0))} target; "
                f"next design budget {queue.get('candidate_budget', 0)}."
            ),
            f"- Consecutive steady ticks: {changes.get('steady_ticks', 0)}.",
            "",
            "## 4. This Tick's Actions",
            "- Ran pipeline monitor and goal check once outside Codex.",
            "- No structural state change was detected.",
            "- Generated this deterministic report without starting `codex exec`.",
            f"- Removed {removed} summary report(s) older than 24 hours.",
            "- No code, configuration, queue, scheduler, or research-policy change.",
            "",
            "## 5. Decisions Made",
            "- None. A steady monitoring result is not recorded as a new research decision.",
        ]
    )
    if pending:
        lines.extend(["", "## Pending User Decisions"])
        for item in pending:
            lines.append(f"- {item.get('path')}")
    lines.extend(["", "=" * 80, ""])

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Tick # steady {stamp}")
    print(f"steady_report={output_path.as_posix()}")
    print("codex_skipped=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
