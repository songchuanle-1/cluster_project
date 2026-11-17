"""Observe the existing M234 trainer; never launch, resume or signal it."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
OLD = ROOT / "pipeline/diagnostic_bundles/tick_21ebd237"
KEYS = ("token", "thread_id", "generated_at", "deadline_at",
        "context_sha256", "pending_sha256")
TOKEN = "6d1f565934d24b4798bd9b2279360cbd"
SOURCE = "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
BODY_SHA = "1f468e34266069c78443faeba1b2cad2f9114610b8009200e6c84737babde939"
PROOF_SHA = "805bec8e842e12f0e81262e6a1d5a6c3b19e321ec48d5c3358de8efaa0bd0b66"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def guard():
    actual = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    owner = {key: actual[key] for key in KEYS}
    assert owner["token"] == TOKEN
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sys.dont_write_bytecode and os.environ["GIT_OPTIONAL_LOCKS"] == "0"
    for name, key in ((".tick_context.json", "context_sha256"),
                      (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[key]
    return owner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--label")
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--previous-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SSH_OR_SHARED_MUTATION"}))
        return
    owner = guard()
    assert args.label and re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", args.label)
    binding = HERE / "current_observer_binding.json"
    proof_path = OLD / "dispatch_proof_execution/dispatch_proof.json"
    body_path = OLD / "launch_observe_prepare/observe_remote.py.txt"
    assert sha(proof_path) == PROOF_SHA and sha(body_path) == BODY_SHA
    proof = read(proof_path)
    assert proof["owner"]["token"] == "21ebd23722904fa3ac93d7330cbb58c1"
    assert proof["source_commit"] == SOURCE and proof["pid"] == 3813109
    assert proof["start_ticks"] == "183481242"
    queue = read(ROOT / "pipeline/queue.json")
    tasks = [task for task in queue["gpu_queues"]["server-4"]
             if task["id"] == "M234-RVE"]
    assert len(tasks) == 1
    task = tasks[0]
    assert task["status"] == "running" and task["pid"] == proof["pid"]
    assert task["code_commit"] == SOURCE and task["log"] == proof["log"]
    assert str(task["gpu"]) == "0" and task["launch_verified"] is True
    if binding.exists():
        current = read(binding)
        assert current["owner"] == owner and current["historical_launch_owner"] == proof["owner"]
    else:
        save(binding, {
            "owner": owner, "kind": "READONLY_EXISTING_TRAINER_OBSERVATION_ONLY",
            "historical_launch_owner": proof["owner"],
            "historical_dispatch_proof": {"path": proof_path.relative_to(ROOT).as_posix(),
                                          "sha256": PROOF_SHA},
            "remote_body": {"path": body_path.relative_to(ROOT).as_posix(), "sha256": BODY_SHA},
            "historical_launch_binding_not_modified": True,
            "new_producer_stage_or_training_lease": False,
            "training_launch_authorized_by_this_observer": False,
        })
    intent = HERE / (args.label + ".intent.json")
    output = HERE / (args.label + ".actual.json")
    assert not intent.exists() and not output.exists(), "Reconcile; never replay."
    save(intent, {
        "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "binding_sha256": sha(binding), "script_sha256": sha(__file__),
        "queue_sha256": sha(ROOT / "pipeline/queue.json"), "read_only": True,
        "no_replay": True,
    })
    command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
               "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
               "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c "
               + shlex.quote(body_path.read_text(encoding="utf-8"))]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, encoding="utf-8",
                               errors="replace")
    result = {
        "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "kind": "CURRENT_EXISTING_TRAINER_RUNTIME_AND_RESOURCE_CHECK",
        "certainty": "uncertain", "local_ssh_pid": process.pid,
        "historical_dispatch_proof_sha256": PROOF_SHA,
        "historical_launch_owner_preserved": True, "training_started_by_observer": False,
        "signals_sent": False, "GPU_compute_started": False, "read_only": True,
    }
    try:
        stdout, stderr = process.communicate(json.dumps(proof), timeout=35)
        result.update(certainty="terminal", returncode=process.returncode,
                      stderr=stderr[:2000])
        assert process.returncode == 0, stderr[:2000]
        assert len(stdout.encode()) < 24576
        observed = result["observation"] = json.loads(stdout)
        assert observed["alive"] is True and observed["pid"] == proof["pid"]
        assert observed["source_commit"] == SOURCE
        assert observed["start_ticks"] == proof["start_ticks"]
        assert observed["all_three_original_lock_inodes_inherited"] is True
        assert not any(observed["error_markers"].values())
        for key in ("binding_sha256", "entry_sha256", "core_sha256", "marker_sha256"):
            assert observed[key] == proof[key]
        assert observed["signals_sent"] is False
        assert observed["training_started_by_observer"] is False
        assert observed["remote_files_written"] is False
        if args.previous:
            assert args.previous.resolve().is_relative_to(ROOT.resolve())
            assert sha(args.previous) == args.previous_sha256
            previous = read(args.previous)
            prior = previous["observation"]
            assert all(prior[key] == observed[key] for key in
                       ("pid", "start_ticks", "source_commit"))
            before, after = prior.get("latest_native_step"), observed.get("latest_native_step")
            result["native_step_growth_observed"] = bool(
                before and after and tuple(after) > tuple(before))
            result["previous"] = {
                "path": args.previous.relative_to(ROOT).as_posix(),
                "sha256": args.previous_sha256, "original_owner": previous["owner"],
            }
        result["passed"] = True
        guard()
    except BaseException as error:
        result.update(passed=False, error_type=type(error).__name__, error=str(error))
        save(output, result)
        raise
    save(output, result)
    observed = result["observation"]
    print(json.dumps({
        "path": str(output), "sha256": sha(output), "passed": result["passed"],
        "pid": observed["pid"], "start_ticks": observed["start_ticks"],
        "latest_native_step": observed["latest_native_step"],
        "native_step_growth_observed": result.get("native_step_growth_observed"),
        "original_three_locks_inherited": observed["all_three_original_lock_inodes_inherited"],
        "bytes_read": observed["bytes_read"],
        "validation_epochs_in_bounded_tail": observed["validation_epochs_last5"],
        "error_markers": observed["error_markers"],
    }))


if __name__ == "__main__":
    main()
