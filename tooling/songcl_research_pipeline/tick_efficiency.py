"""Bounded model views and evidence-sensitive research cooldowns."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


VIEW_LIMIT = 12000
MAX_DUE = 4
HUMAN_BLOCKERS = {
    "independent_grounded_counterfactual_annotations",
    "human_review",
    "human_authorization",
    "human_revision_authorization",
}
RESOURCE_BLOCKERS = {
    "live_external_gpu_occupation",
    "gpu_context_or_lock_not_released",
    "external_resource",
}
RESEARCH_BLOCKERS = {"numerical_control_failure"}
TERMINAL_RESEARCH = {"training", "complete", "rejected", "closed"}


def ready_waiting(task, states=None):
    return (not task.get("dispatch_hold") and not task.get("admission_error")
            and all((states or {}).get(d) in ("done_complete", "done_earlystop")
                    for d in (task.get("depends_on") or [])))


def pending_ids(candidates, queued=(), *, actionable_only=False, states=None):
    """Count a stable candidate and its waiting task only once."""
    queued = list(queued)
    held = {t.get("id") or t.get("exp_id") for t in queued
            if (t.get("status") or t.get("state")) == "waiting"
            and not ready_waiting(t, states)} if actionable_only else set()
    ids = {c.get("experiment_id") or c["id"] for c in candidates
           if c.get("stage") not in TERMINAL_RESEARCH
           and (not actionable_only or c.get("stage") != "blocked")}
    ids.update(t.get("id") or t.get("exp_id") for t in queued
               if (t.get("status") or t.get("state")) in ("waiting", "claiming"))
    return ids - {None, ""} - held


def external_block(candidate):
    """An evidenced candidate hold is not permission or usable research stock."""
    return (candidate.get("blocker_kind") in HUMAN_BLOCKERS | RESOURCE_BLOCKERS
            and parkable_block(candidate))


def parkable_block(candidate):
    """Recognize scoped holds without treating them as executable reserve."""
    if (candidate.get("stage") != "blocked"
            or candidate.get("blocker_kind") not in
            HUMAN_BLOCKERS | RESOURCE_BLOCKERS | RESEARCH_BLOCKERS
            or not all(candidate.get(k) for k in
                       ("blocker", "unblock_condition", "next_action", "evidence"))):
        return False
    if (candidate["blocker_kind"] in RESEARCH_BLOCKERS
            and candidate.get("failure_scope") not in ("implementation", "inconclusive")):
        return False
    try:
        return datetime.fromisoformat(candidate["retry_after"]).tzinfo is not None
    except (ValueError, TypeError, KeyError):
        return False


def monitor_issues(text):
    """Extract known monitor failure markers, not conclusions from exit code 0."""
    issues, seen = [], set()
    server, task = None, None
    for line in text.splitlines():
        heading = re.match(r"--- ([\w.-]+) \(", line.strip())
        dispatch = re.search(
            ">>> \u961f\u5217\u63a8\u9001: \\[([^\\]]+)\\] on ([\\w.-]+)", line)
        if heading:
            server, task = heading[1], None
        if dispatch:
            task, server = dispatch[1][:100], dispatch[2]
        tagged = re.search(r"\[(?:认领待核验|依赖阻止|停止待核验|归档待恢复)\]\s*\[([^\]]+)\]", line)
        admission = re.search(r"\[准入阻止\]\s*(.+?):", line)
        if tagged or admission:
            task = (tagged or admission)[1][:100]
        if "[跳过]" in line and ".pipeline.lock" in line:
            server, task = None, None
            kind, reason = "observation", "monitor_busy"
        elif "[停止待核验]" in line:
            kind, reason = "stop", "stop_unconfirmed"
        elif "[归档待恢复]" in line:
            kind, reason = "archive", "archive_pending"
        elif "[\u4e0d\u53ef\u8fbe]" in line:
            kind, reason = "connectivity", "unreachable"
        elif "[进程观测不可用]" in line:
            kind, reason = "observation", "process_unknown"
        elif "[准入阻止]" in line:
            kind, reason = "admission", "admission_blocked"
        elif "[认领待核验]" in line:
            kind, reason = "claim", "claim_uncertain"
        elif "[依赖阻止]" in line:
            kind, reason = "dependency", "dependency_blocked"
        elif "[\u540c\u6b65\u963b\u6b62]" in line or "\u4ee3\u7801\u540c\u6b65\u5931\u8d25" in line:
            kind = "deployment"
            reason = ("source_marker" if "Remote source marker unavailable" in line
                      else "source_integrity" if "Source integrity" in line
                      else "sync_failed")
        elif "[\u542f\u52a8\u5931\u8d25]" in line or "推送失败" in line:
            kind, reason = "launch", "launch_failed"
        else:
            continue
        key = (server, task, kind)
        if key not in seen:
            seen.add(key)
            issues.append({"kind": kind, "server": server, "task": task, "reason": reason})
    return issues


def encoded_size(value):
    return len((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def read(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def research_signature(project):
    """Exclude routine reports and memory; include external and research changes."""
    pipeline = Path(project) / "pipeline"
    files = ["goal.json", "queue.json", "research_queue.json", "research_work.json",
             "experiments.csv", "closure_policy.json"]
    values = {name: file_hash(pipeline / name) for name in files}
    values["SERVERS.yaml"] = file_hash(Path(project) / "SERVERS.yaml")
    for folder in ("analyses", "designs", "reviews", "decisions", "experiments"):
        directory = pipeline / folder
        values[folder] = sorted(
            (p.name, p.stat().st_size, p.stat().st_mtime_ns)
            for p in directory.iterdir() if p.is_file()
        ) if directory.is_dir() else []
    work = read(pipeline / "research_work.json", {}) or {}
    # Changing an artifact in place must wake work even if the ledger is unchanged.
    values["evidence"] = []
    base = Path(project).resolve()
    for item in work.get("candidates", []):
        for entry in item.get("evidence", []):
            path = (base / entry.get("path", "")).resolve()
            if path.is_relative_to(base):
                values["evidence"].append((entry.get("path"), file_hash(path)))
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def cooldown_active(project, now=None, candidate_backfill=False):
    pipeline = Path(project) / "pipeline"
    try:
        hold = read(pipeline / "headless/.research_cooldown.json", {}) or {}
        if candidate_backfill:
            reason = hold.get("stop_reason")
            if reason is None:
                reason = (read(pipeline / "research_work.json", {}) or {}).get(
                    "design_cycle", {}).get("stop_reason")
            if reason == "external_resource_blocked":
                return False
        until = datetime.fromisoformat(hold["retry_after"])
        now = now or datetime.now(timezone.utc)
        return (until.tzinfo is not None and until > now
                and hold["signature"] == research_signature(project))
    except (ValueError, KeyError, TypeError, OSError):
        return False


def compact_view(context, limit=VIEW_LIMIT):
    """The full snapshot remains untouched; overflow is explicit and queryable."""
    due = context.get("research_work", {}).get("due_ids", [])
    candidates = context.get("research_work", {}).get("candidates", [])
    by_id = {c["id"]: c for c in candidates}
    selected = []
    for id in due[:MAX_DUE]:
        c = by_id.get(id, {})
        selected.append({
            "id": id, "stage": c.get("stage"),
            "next_action": str(c.get("next_action", ""))[:400],
            "blocker": str(c.get("blocker", ""))[:200],
            "retry_after": c.get("retry_after"),
            "evidence_count": len(c.get("evidence", [])),
            "failure_scope": c.get("failure_scope"),
            "implementation_revisions": len(c.get("revision_history", [])),
            "detail": "foreground_tick.py <project> candidate --id <id>",
        })
    q = context.get("queue", {})
    research = context.get("research_work", {})
    human_actions = research.get("human_actions", [])
    view = {
        "schema_version": 1,
        **{k: context.get(k) for k in ("project", "generated_at", "deadline_at", "mode", "mode_reason")},
        "full_snapshot_for_validator_only": "pipeline/headless/.tick_context.json",
        "goal": {k: context.get("goal", {}).get(k)
                 for k in ("path", "metric", "constraint_count", "banned_count")},
        "preflight": {
            **{k: context.get("preflight", {}).get(k) for k in ("monitor_rc", "goal_rc")},
            "operational_issues": context.get("preflight", {}).get("operational_issues", [])[:6],
            "omitted_issue_count": max(
                0, len(context.get("preflight", {}).get("operational_issues", [])) - 6),
        },
        "experiment_first": context.get("experiment_first", {}),
        "queue": {k: q.get(k) for k in
                  ("capacity", "target_active", "active_count", "candidate_budget",
                   "running_count", "claiming_count", "waiting_count", "ready_waiting_count")},
        "changes": {
            "reasons": context.get("changes", {}).get("reasons", [])[:8],
            "new_terminal_ids": context.get("changes", {}).get("new_terminal_ids", [])[:8],
            "terminal_count": len(context.get("changes", {}).get("new_terminal_ids", [])),
        },
        "research": {
            "due_count": len(due), "shown": selected, "omitted_due_count": max(0, len(due) - len(selected)),
            "blocked_not_due_count": sum(c.get("stage") == "blocked" and c["id"] not in due for c in candidates),
            "page_command": "foreground_tick.py <project> candidates --offset <n>",
            "deferred": bool(research.get("deferred")),
            "deferred_until": research.get("deferred_until"),
            "deferred_reason": research.get("deferred_reason"),
            "human_actions": [
                {"id": item.get("id"),
                 "next_action": str(item.get("next_action") or "")[:400],
                 "retry_after": item.get("retry_after")}
                for item in human_actions[:MAX_DUE]],
            "omitted_human_action_count": max(0, len(human_actions) - MAX_DUE),
            **{k: context.get("research_work", {}).get(k) for k in
               ("reserve_target", "reserve_count", "reserve_budget", "reserve_only",
                "pending_count", "pending_limit", "parked_count", "human_wait_count",
                "resource_wait_count", "research_wait_count", "unclassified_block_count",
                "pending_scope", "total_pending_count", "creation_budget")},
        },
        "research_funnel": context.get("research_funnel", {"observed": False}),
        "read_policy": "Read only listed IDs as needed; do not dump full snapshot, history or all references.",
    }
    if context["mode"] != "steady":
        view["relevant_files"] = context.get("manifests", {}).get("suggested_reads", [])[:5]
    reserve = context.get("research_work", {})
    # Due held IDs need an evidence check, not a repeat of the blocked experiment.
    actionable_due = set(due) - set(reserve.get("parked_ids", []))
    if (context["mode"] == "design" and not actionable_due
            and (reserve.get("pending_limit") is None or reserve.get("reserve_budget", 0) > 0)
            and (q.get("candidate_budget", 0) > 0 or reserve.get("reserve_only"))):
        view["design_bootstrap"] = {
            "required": True,
            "candidate_budget": q.get("candidate_budget"),
            "reserve_only": bool(reserve.get("reserve_only")),
            "research_reserve_budget": reserve.get("reserve_budget", 0),
            "rule": (
                "Create at least one stable diagnosis candidate before broad route "
                "review or any abort. Conceptual overlap is not a rejection; run the "
                "cheapest discriminating test in this tick, persist hashed evidence, "
                "then reject, advance, or create the next independent candidate."
            ),
            "required_fields": [
                "id", "stage=diagnosis", "hypothesis", "matched_control",
                "next_action", "evidence(path,sha256)",
            ],
            "continue_until": (
                "admission, disconfirming evidence for each attempted route, or "
                "the real tick deadline; reserve-only work stops at its bounded "
                "preparation target and never adds queue entries or launches"
            ),
        }
    if context.get("experiment_first", {}).get("enabled"):
        view.pop("design_bootstrap", None)
        view["workflow"] = {
            "reference": "references/experiment_first.md",
            "steps": ["Observe and dispatch existing ready work",
                      "Implement independent variants when ready backlog is short",
                      "Check native data/backward, resources and constraints",
                      "Admit and dispatch this tick, or preserve actual failed/blocked test"],
            "authorization": "Scoped experiment operations are approved; resource/data bans remain.",
            "stop": "One real evidenced attempt may finish; no quota-forcing or exhaustive route review.",
        }
    # Limit UTF-8 bytes, including pathological goal/reason strings.
    while encoded_size(view) > limit:
        if view.get("relevant_files"):
            view["relevant_files"].pop()
        elif view["preflight"]["operational_issues"]:
            view["preflight"]["operational_issues"].pop()
            view["preflight"]["omitted_issue_count"] += 1
        elif view["research"]["human_actions"]:
            view["research"]["human_actions"].pop()
            view["research"]["omitted_human_action_count"] += 1
        elif view["research"]["shown"]:
            view["research"]["shown"].pop()
            view["research"]["omitted_due_count"] += 1
        elif view["changes"]["reasons"]:
            view["changes"]["reasons"].pop()
        else:
            view["mode_reason"] = "See targeted context detail; oversized fields omitted."
            view["goal"] = {"path": "pipeline/goal.json", "read_constraints_in_full": True}
            view["changes"]["new_terminal_ids"] = []
            if encoded_size(view) > limit:
                raise ValueError("Compact view cannot fit the requested bound")
    return view


def candidate_page(context, offset=0):
    if offset < 0:
        raise ValueError("Offset must be nonnegative")
    due = context.get("research_work", {}).get("due_ids", [])
    ids = due[offset:offset + MAX_DUE]
    return {"due_count": len(due), "offset": offset, "ids": ids,
            "next_offset": offset + len(ids) if offset + len(ids) < len(due) else None}
