"""Preflight and postflight for research performed in an existing Codex task."""

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

import closure
import tick_efficiency
import tick_usage
import render_tick_report

SKILL = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipt(headless, owner, status, **details):
    token = owner["token"]
    if not isinstance(token, str) or not token.isalnum():
        raise ValueError("Invalid receipt token")
    directory = headless.parent / "tick_receipts"
    directory.mkdir(exist_ok=True)
    path = directory / (token + ".json")
    save(path, {
        "schema_version": 1, "token": token,
        "thread_id": owner["thread_id"], "started_at": owner["started_at"],
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": status, **details,
        "usage": tick_usage.collect(owner.get("usage_cursor")),
        "outcomes": tick_usage.outcomes(headless.parent, owner.get("work_before")),
    })
    return path


def paths(project):
    root = Path(os.environ.get("PROJECT_ROOT", "D:/project")).resolve()
    project_dir = (root / project).resolve()
    if project_dir.parent != root or not (project_dir / "pipeline").is_dir():
        raise ValueError("Expected an existing direct-child pipeline project")
    return project_dir / "pipeline", project_dir / "pipeline" / "headless"


def run(script, *args):
    result = subprocess.run(
        [sys.executable, "-B", str(SKILL / script), *map(str, args)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=900,
    )
    text = result.stdout + result.stderr
    if script == "closure.py" or result.returncode not in (
            (0, 1, 4) if script == "check_goal.py" else (0,)):
        print(text, end="", flush=True)
    return result.returncode, text


def release(headless):
    lock = headless / ".foreground.lockdir"
    (lock / "owner.json").unlink()
    lock.rmdir()


class LeaseReleaseError(OSError):
    """Release or its receipt failed; do not repeat cleanup on a newer lease."""


def owns_lease(headless, owner):
    try:
        current = load(headless / ".foreground.lockdir/owner.json")
        return isinstance(current, dict) and current.get("token") == owner["token"]
    except (OSError, ValueError):
        return False


def release_recorded(headless, owner, record):
    data = load(record)
    if any(data.get(k) != owner.get(k) for k in ("token", "thread_id", "started_at")):
        raise ValueError("Release receipt does not match the owned lease")
    if not owns_lease(headless, owner):
        raise ValueError("Lease ownership changed; refusing release")
    try:
        release(headless)
    except Exception as exc:
        data.update(
            lease_release="retained" if owns_lease(headless, owner) else "unknown",
            lease_release_checked_at=datetime.now(timezone.utc).isoformat(),
            lease_release_error=type(exc).__name__,
        )
        try:
            save(record, data)
        except OSError as audit_error:
            raise LeaseReleaseError("Lease release and receipt update failed") from audit_error
        raise LeaseReleaseError("Lease release failed; inspect its receipt before recovery") from exc
    # Only this immutable token's receipt is updated, never shared tick state.
    data.update(lease_release="released",
                lease_released_at=datetime.now(timezone.utc).isoformat())
    data.pop("lease_release_error", None)
    try:
        save(record, data)
    except OSError as exc:
        raise LeaseReleaseError("Lease released but receipt update failed; do not replay tick") from exc


def committed_state(headless, owner):
    state = headless / ".tick_context_state.json"
    return bool(owner.get("pending_sha256") and state.is_file()
                and digest(state) == owner["pending_sha256"])


def fail(headless, reason, owner=None):
    owner = owner or load(headless / ".foreground.lockdir" / "owner.json")
    if not owns_lease(headless, owner):
        raise ValueError("Lease ownership changed; refusing abort")
    record = receipt(headless, owner, "INCOMPLETE", reason=reason,
                     context_committed=committed_state(headless, owner), lease_release="pending")
    (headless / ".tick_context_state.next.json").unlink(missing_ok=True)
    (headless / ".tick_unhealthy").write_text(reason + "\n", encoding="utf-8")
    release_recorded(headless, owner, record)


def begin(project, thread_id, auto_steady=False):
    pipeline, headless = paths(project)
    mode = load(pipeline / "execution_mode.json")
    if mode.get("mode") != "foreground" or mode.get("target_thread_id") != thread_id:
        raise ValueError("Foreground project ownership does not match this task")
    if not closure.enabled(pipeline.parent):
        print("CLOSURE_NOT_ENABLED: no preflight performed; enable policy only after project review")
        return 2
    headless.mkdir(exist_ok=True)
    # Never infer that an old background lock is stale from its age alone.
    if (headless / ".tick.lockdir").exists():
        print("BUSY: background tick owns the project; no preflight performed")
        return 75
    lock = headless / ".foreground.lockdir"
    try:
        lock.mkdir()
    except FileExistsError:
        print("BUSY: foreground lease exists; inspect its owner, do not delete or replay")
        return 75
    token = uuid.uuid4().hex
    owner = {
        "token": token, "thread_id": thread_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "usage_cursor": tick_usage.cursor(thread_id),
        "work_before": tick_usage.work_snapshot(pipeline),
    }
    save(lock / "owner.json", owner)
    try:
        if (headless / ".tick.lockdir").exists():
            record = receipt(headless, owner, "SKIPPED_BUSY", reason="Background tick appeared",
                             context_committed=False, lease_release="pending")
            release_recorded(headless, owner, record)
            print("BUSY: background tick appeared; no preflight performed")
            return 75
        monitor_rc, monitor = run("pipeline_monitor.py", project)
        if monitor_rc == 75:
            record = receipt(headless, owner, "SKIPPED_BUSY", reason="Monitor lock is held",
                             context_committed=False, lease_release="pending")
            release_recorded(headless, owner, record)
            print("BUSY: monitor lease held; no snapshot committed; foreground lease released")
            return 75
        goal_rc, goal = run("check_goal.py", project)
        if monitor_rc != 0 or goal_rc not in (0, 1, 4):
            fail(headless, f"foreground preflight failed: monitor={monitor_rc}, goal={goal_rc}", owner)
            return 1
        monitor_path = headless / ".foreground_monitor.txt"
        goal_path = headless / ".foreground_goal.txt"
        monitor_path.write_text(monitor, encoding="utf-8")
        goal_path.write_text(goal, encoding="utf-8")
        rc, _ = run(
            "build_tick_context.py", project,
            "--monitor-file", monitor_path, "--goal-file", goal_path,
            "--monitor-rc", monitor_rc, "--goal-rc", goal_rc,
        )
        if rc:
            fail(headless, "foreground context builder failed", owner)
            return rc
        context = load(headless / ".tick_context.json")
        pending = load(headless / ".tick_context_state.next.json")
        if (not context.get("generated_at") or pending.get("generated_at") != context["generated_at"]
                or pending.get("mode") != context["mode"]):
            raise ValueError("Context and pending state do not identify the same tick")
        owner.update({
            "context_sha256": digest(headless / ".tick_context.json"),
            "pending_sha256": digest(headless / ".tick_context_state.next.json"),
            "generated_at": context["generated_at"], "mode": context["mode"],
            "deadline_at": context["deadline_at"],
        })
        save(lock / "owner.json", owner)
        save(headless / ".tick_model_view.json", tick_efficiency.compact_view(context))
        report_path = report(project, token)
        print(json.dumps({
            "token": token, "mode": context["mode"],
            "deadline_at": context["deadline_at"],
            "context": str(headless / ".tick_model_view.json"),
            "report": str(report_path),
        }, ensure_ascii=False), flush=True)
        if auto_steady and context["mode"] == "steady":
            return complete(project, token)
        return 0
    except LeaseReleaseError:
        raise
    except Exception:
        if owns_lease(headless, owner):
            fail(headless, "foreground preflight interrupted or failed; reconcile before retry", owner)
        raise


def complete(project, token, abort_reason=None):
    _, headless = paths(project)
    owner = load(headless / ".foreground.lockdir" / "owner.json")
    if owner["token"] != token:
        raise ValueError("Lease token mismatch; refusing to modify another tick")
    if abort_reason is not None:
        fail(headless, abort_reason, owner)
        print("INCOMPLETE: receipt saved; pending state discarded; lease released")
        return 1
    pending = headless / ".tick_context_state.next.json"
    context_path = headless / ".tick_context.json"
    if (not owner.get("context_sha256") or not owner.get("pending_sha256")
            or not context_path.is_file() or not pending.is_file()
            or digest(context_path) != owner["context_sha256"]
            or digest(pending) != owner["pending_sha256"]):
        receipt(headless, owner, "INCOMPLETE", reason="Missing or changed tick snapshot",
                context_committed=committed_state(headless, owner), lease_release="retained")
        print("POSTFLIGHT FAILED: missing/changed snapshot; lease retained; reconcile then abort")
        return 1
    rc, output = run("closure.py", project, "--require-enabled")
    if rc or "CLOSURE_POSTFLIGHT_PASS" not in output.splitlines():
        receipt(headless, owner, "INCOMPLETE",
                reason="Closure not enabled or postflight did not explicitly pass",
                closure_rc=rc, context_committed=False, lease_release="retained")
        print("POSTFLIGHT FAILED: lease retained; continue this tick or explicitly abort")
        return rc or 1
    if (digest(context_path) != owner["context_sha256"]
            or digest(pending) != owner["pending_sha256"]):
        raise ValueError("Snapshot changed during postflight; lease retained")
    receipt(headless, owner, "VALIDATED", postflight="PASS",
            context_sha256=owner["context_sha256"], pending_sha256=owner["pending_sha256"],
            context_committed=False, lease_release="retained")
    pending.replace(headless / ".tick_context_state.json")
    record = receipt(headless, owner, "FINALIZED", postflight="PASS",
                     context_sha256=owner["context_sha256"],
                     state_sha256=owner["pending_sha256"],
                     context_committed=True, lease_release="pending")
    context = load(context_path)
    work = closure.read(headless.parent / "research_work.json", {})
    cycle = work.get("design_cycle", {})
    if context.get("experiment_first", {}).get("enabled"):
        cycle = {}  # Candidate failures must not cool down independent design.
    if context["mode"] == "design" and cycle.get("stop_reason") in (
            "no_information_gain", "independent_routes_exhausted"):
        # Only a freshly validated early-stop disposition may suppress new design.
        try:
            closure.validate_early_stop(headless.parent.parent, context,
                                        work.get("candidates", []), cycle)
        except (ValueError, KeyError, TypeError, OSError):
            pass
        else:
            save(headless / ".research_cooldown.json", {
                "retry_after": cycle["retry_after"], "token": token,
                "signature": tick_efficiency.research_signature(headless.parent.parent),
                "resume_condition": cycle["resume_condition"],
                "stop_reason": cycle["stop_reason"],
            })
    elif context["mode"] != "steady" and cycle.get("stop_reason") == "external_resource_blocked":
        pending_work = closure.pending(headless.parent.parent)
        if pending_work and all(c.get("stage") == "blocked" for c in pending_work):
            now = datetime.now(timezone.utc)
            retries = [datetime.fromisoformat(c["retry_after"]) for c in pending_work]
            hours = 4 if all(c.get("blocker_kind") in tick_efficiency.HUMAN_BLOCKERS
                             for c in pending_work) else 2
            retry = min([now + timedelta(hours=hours), *retries])
            if retry > now:
                save(headless / ".research_cooldown.json", {
                    "retry_after": retry.isoformat(), "token": token,
                    "signature": tick_efficiency.research_signature(headless.parent.parent),
                    "resume_condition": cycle.get("resume_condition", "Resource or evidence changes"),
                    "stop_reason": cycle["stop_reason"],
                })
    for name in (".tick_unhealthy", ".tick_unhealthy_count"):
        (headless / name).unlink(missing_ok=True)
    release_recorded(headless, owner, record)
    print("COMPLETE: postflight passed; context committed; lease released")
    print(f"receipt={record}")
    return 0


def report(project, token, notes_path=None):
    pipeline, headless = paths(project)
    owner = load(headless / ".foreground.lockdir/owner.json")
    if owner["token"] != token:
        raise ValueError("Lease token mismatch")
    context_path = headless / ".tick_context.json"
    if digest(context_path) != owner.get("context_sha256"):
        raise ValueError("Cannot render changed snapshot")
    context = load(context_path)
    notes = load(Path(notes_path)) if notes_path else None
    output = pipeline / "reports" / ("summary_" + token + ".md")
    output.parent.mkdir(exist_ok=True)
    output.write_text(render_tick_report.render(context, notes), encoding="utf-8")
    return output


def query_candidates(project, candidate_id=None, offset=0):
    pipeline, headless = paths(project)
    if candidate_id is None:
        return tick_efficiency.candidate_page(load(headless / ".tick_context.json"), offset)
    work = closure.read(pipeline / "research_work.json", {})
    matches = [c for c in work.get("candidates", []) if c["id"] == candidate_id]
    if len(matches) != 1:
        raise ValueError("Candidate ID missing or duplicated")
    return matches[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("begin")
    start.add_argument("--thread-id", required=True)
    start.add_argument("--auto-steady", action="store_true")
    finish = commands.add_parser("finish")
    finish.add_argument("--token", required=True)
    abort = commands.add_parser("abort")
    abort.add_argument("--token", required=True)
    abort.add_argument("--reason", required=True)
    render = commands.add_parser("report")
    render.add_argument("--token", required=True)
    render.add_argument("--notes")
    detail = commands.add_parser("candidate")
    detail.add_argument("--id", required=True)
    page = commands.add_parser("candidates")
    page.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()
    if args.command == "begin":
        return begin(args.project, args.thread_id, args.auto_steady)
    if args.command == "report":
        print(report(args.project, args.token, args.notes))
        return 0
    if args.command in ("candidate", "candidates"):
        print(json.dumps(query_candidates(args.project, getattr(args, "id", None),
                                         getattr(args, "offset", 0)), ensure_ascii=False, indent=2))
        return 0
    return complete(args.project, args.token, getattr(args, "reason", None))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
