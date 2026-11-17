"""One current-owner read-only GPU0/GPU1 resource observation; default NOP."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TICK = HERE.parents[1]
KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def tail(path, maximum):
    with Path(path).open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        stream.seek(max(0, stream.tell() - maximum))
        return stream.read(maximum).decode("utf-8", "replace")


def guard(minimum_margin=60):
    live = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    owner = {key: live[key] for key in KEYS}
    assert live["mode"] == "design"
    assert owner == read(TICK / "current_owner_binding.json")
    assert owner["token"] == "4ecb5020c4c54abeb26dc874ed90080e"
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert sys.dont_write_bytecode and os.environ["GIT_OPTIONAL_LOCKS"] == "0"
    assert not sys.flags.optimize
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > minimum_margin
    for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[key]
    integrity = read(TICK / "integrity_before.json")
    assert integrity["owner"] == owner
    assert sha(ROOT / "pipeline/goal.json") == integrity["goal_sha256"]
    assert sha(ROOT / "SERVERS.yaml") == integrity["servers_sha256"]
    return owner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--review", type=Path)
    parser.add_argument("--review-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SSH_NATIVE_OR_PROCESS_LAUNCH"}))
        return
    owner = guard()
    frozen = read(HERE / "FROZEN.json")
    assert frozen["owner"] == owner and frozen["author_executed"] is False
    for name, expected in frozen["files"].items():
        path = (HERE / name).resolve()
        assert path.is_relative_to(HERE) and sha(path) == expected
    for anchor in frozen["anchors"]:
        assert sha(ROOT / anchor["path"]) == anchor["sha256"]
    assert args.review and args.review.is_absolute() and args.review.resolve().is_relative_to(TICK)
    assert sha(args.review) == args.review_sha256
    review = read(args.review)
    assert review["owner"] == owner and review["passed"] is True and review["material_concerns"] == []
    reviewer = review["reviewer_thread_id"]
    assert isinstance(reviewer, str) and reviewer.strip()
    assert reviewer not in (owner["thread_id"], "/root", "/root/fresh_ops")
    assert review["frozen_sha256"] == sha(HERE / "FROZEN.json")
    assert review["wrapper_sha256"] == sha(Path(__file__))
    assert review["body_sha256"] == sha(HERE / "resource_remote.py.txt")
    binding = read(HERE / "binding.json")
    assert binding["owner"] == owner
    intent, actual = HERE / "dual_resource.intent.json", HERE / "dual_resource.actual.json"
    assert not intent.exists() and not actual.exists(), "Reconcile existing intent/result; never replay."
    save(intent, {"owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
                  "kind": "ONE_CURRENT_GPU0_GPU1_RESOURCE_OBSERVATION",
                  "frozen_sha256": sha(HERE / "FROZEN.json"), "review_sha256": args.review_sha256,
                  "source_commit": binding["source_commit"], "no_replay": True,
                  "signals_sent": False, "training_restart": False})
    body = (HERE / "resource_remote.py.txt").read_text(encoding="utf-8")
    command = ("test \"$(hostname)\" = dl04-MS-7E06 && test \"$(id -u)\" = 1001 && "
               "PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' TOKENIZERS_PARALLELISM=false "
               "/usr/bin/python3 -I -B -c " + shlex.quote(body))
    stdout_path, stderr_path = HERE / "dual_resource.transport.stdout.partial", HERE / "dual_resource.transport.stderr.partial"
    stdout_file, stderr_file = stdout_path.open("x+b"), stderr_path.open("x+b")
    result = {"owner": owner, "kind": "ONE_CURRENT_GPU0_GPU1_RESOURCE_OBSERVATION",
              "certainty": "uncertain", "signals_sent": False, "automatic_retry": False,
              "frozen_sha256": sha(HERE / "FROZEN.json")}
    process = None
    try:
        guard(40)
        process = subprocess.Popen(
            ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8",
             "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no",
             "songcl@192.168.1.115", command],
            stdin=subprocess.PIPE, stdout=stdout_file, stderr=stderr_file)
        result.update(local_ssh_pid=process.pid, local_ssh_started_at=datetime.now(timezone.utc).isoformat())
        payload = json.dumps({"execute_root": True, "owner": owner}).encode("utf-8")
        process.communicate(payload, timeout=30)
        stdout_file.flush()
        stderr_file.flush()
        result.update(certainty="terminal", returncode=process.returncode, stderr_tail=tail(stderr_path, 4096))
        assert stdout_path.stat().st_size <= 65536
        result["stdout"] = stdout_path.read_bytes().decode("utf-8", "replace")
        assert process.returncode == 0
        result["observation"] = json.loads(result.pop("stdout"))
        assert result["observation"]["owner"] == owner
        guard(0)
        result["transport_passed"] = True
    except BaseException as error:
        result.update(transport_passed=False, error_type=type(error).__name__, error=str(error)[:1000])
        if isinstance(error, subprocess.TimeoutExpired):
            result["partial_stdout"] = tail(stdout_path, 32768)
            result["partial_stderr"] = tail(stderr_path, 4096)
            result["reason"] = "SOFT_TIMEOUT_PRESERVE_SSH_PID_AND_REMOTE_DESCENDANTS_NO_SIGNAL_OR_RETRY"
        result["retained_local_transport_captures"] = [str(stdout_path), str(stderr_path)]
        stdout_file.close()
        stderr_file.close()
        save(actual, result)
        raise
    stdout_file.close()
    stderr_file.close()
    save(actual, result)
    print(json.dumps({"path": str(actual), "sha256": sha(actual), "transport_passed": True,
                      "outcome": result["observation"].get("status"),
                      "observed_empty_compute_lists": result["observation"].get("both_empty_compute_lists_observed", False),
                      "GPU1_dispatch_admitted": False}))


if __name__ == "__main__":
    main()
