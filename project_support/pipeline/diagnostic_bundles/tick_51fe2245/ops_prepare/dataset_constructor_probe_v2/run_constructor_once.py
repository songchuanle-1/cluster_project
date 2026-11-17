"""One readonly CPU dataset-constructor/cache-coverage probe; default NOP. Default NOP; independently reviewed root execution only."""
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


def guard(minimum_margin=110):
    live = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    owner = {key: live[key] for key in KEYS}
    assert live["mode"] == "design"
    assert owner == read(TICK / "current_owner_binding.json")
    assert owner["token"] == "51fe22452ecf43a390b8cfa6fddbc733"
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert sys.dont_write_bytecode and os.environ["GIT_OPTIONAL_LOCKS"] == "0"
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > minimum_margin
    for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[key]
    integrity = read(TICK / "integrity_before.json")
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
    assert review["reviewer_thread_id"] not in (owner["thread_id"], "/root", "/root/fresh_ops")
    assert review["frozen_sha256"] == sha(HERE / "FROZEN.json")
    assert review["wrapper_sha256"] == sha(Path(__file__))
    assert review["body_sha256"] == sha(HERE / "supervisor.py.txt")
    assert review["carrier_sha256"] == sha(HERE / "carrier.py.txt")
    binding = read(HERE / "binding.json")
    assert binding["owner"] == owner
    pins = read(HERE / "provenance_pins.json")
    assert pins["owner"] == owner
    payload = json.dumps({"execute_root": True, "owner": owner,
                          "carrier_source": (HERE / "carrier.py.txt").read_text(encoding="utf-8"),
                          "pins": pins["pins"], "lineage": read(HERE / "lineage.json")}).encode("utf-8")
    assert len(payload) <= 65536
    intent, actual = HERE / "constructor_v2.intent.json", HERE / "constructor_v2.actual.json"
    assert not intent.exists() and not actual.exists(), "Reconcile existing intent/result; never replay."
    save(intent, {"owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
                  "kind": "CPU_READONLY_DATASET_CONSTRUCTOR_CACHE_COVERAGE_V2",
                  "frozen_sha256": sha(HERE / "FROZEN.json"), "review_sha256": args.review_sha256,
                  "source_commit": binding["source_commit"], "no_replay": True,
                  "signals_sent": False, "training_restart": False})
    body = (HERE / "supervisor.py.txt").read_text(encoding="utf-8")
    command = ("test \"$(hostname)\" = dl04-MS-7E06 && test \"$(id -u)\" = 1001 && "
               "PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' TOKENIZERS_PARALLELISM=false "
               "/usr/bin/python3 -I -B -c " + shlex.quote(body))
    stdout_path, stderr_path = HERE / "constructor_v2.transport.stdout.partial", HERE / "constructor_v2.transport.stderr.partial"
    stdout_file, stderr_file = stdout_path.open("x+b"), stderr_path.open("x+b")
    process = subprocess.Popen(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "PasswordAuthentication=no",
         "-o", "KbdInteractiveAuthentication=no", "-o", "ConnectTimeout=8",
         "songcl@192.168.1.115", command],
        stdin=subprocess.PIPE, stdout=stdout_file, stderr=stderr_file)
    result = {"owner": owner, "kind": "CPU_READONLY_DATASET_CONSTRUCTOR_CACHE_COVERAGE_V2",
              "local_ssh_pid": process.pid, "local_ssh_started_at": datetime.now(timezone.utc).isoformat(),
              "certainty": "uncertain", "signals_sent": False, "automatic_retry": False,
              "frozen_sha256": sha(HERE / "FROZEN.json")}
    try:
        process.communicate(payload, timeout=88)
        stdout_file.flush(); stderr_file.flush()
        assert stdout_path.stat().st_size <= 1048576
        stdout, stderr = stdout_path.read_bytes(), stderr_path.read_bytes()[-4096:]
        result.update(certainty="terminal", returncode=process.returncode,
                      stderr_tail=stderr[-4096:].decode("utf-8", "replace"))
        assert len(stdout) <= 1048576
        result["stdout"] = stdout.decode("utf-8", "replace")
        assert process.returncode == 0
        result["observation"] = json.loads(result.pop("stdout"))
        assert result["observation"]["owner"] == owner
        guard(0)
        result["transport_passed"] = True
    except BaseException as error:
        result.update(transport_passed=False, error_type=type(error).__name__, error=str(error)[:1000])
        if isinstance(error, subprocess.TimeoutExpired):
            result["partial_stdout"] = stdout_path.read_bytes()[-1048576:].decode("utf-8", "replace")
            result["partial_stderr"] = stderr_path.read_bytes()[-4096:].decode("utf-8", "replace")
            result["reason"] = "SOFT_TIMEOUT_PRESERVE_SSH_PID_AND_REMOTE_DESCENDANTS_NO_SIGNAL_OR_RETRY"
        result["retained_local_transport_captures"] = [str(stdout_path), str(stderr_path)]
        stdout_file.close(); stderr_file.close()
        save(actual, result)
        raise
    stdout_file.close(); stderr_file.close()
    save(actual, result)
    print(json.dumps({"path": str(actual), "sha256": sha(actual), "transport_passed": True,
                      "status": result["observation"].get("status"),
                      "constructor_complete": result["observation"].get("constructor_complete", False)}))


if __name__ == "__main__":
    main()
