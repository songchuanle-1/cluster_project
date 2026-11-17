"""One current-owner read-only kernel-file observation; default is NOP."""
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
BODY = HERE / "ops_prepare/target_kernel_log_suffix_remote.py.txt"
BODY_SHA = "c71934e70d925039e17460447b988efbe270bb7eb7c07695a3b3cb80e2cb0c68"
KEYS = ("token", "thread_id", "generated_at", "deadline_at",
        "context_sha256", "pending_sha256")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def guard():
    state = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    owner = {key: state[key] for key in KEYS}
    assert owner == read(HERE / "current_owner_binding.json")
    assert owner["token"] == "eb84540382834ffd88f5a83a0b797ee3"
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert sys.dont_write_bytecode and os.environ["GIT_OPTIONAL_LOCKS"] == "0"
    assert (datetime.fromisoformat(owner["deadline_at"])
            - datetime.now(timezone.utc)).total_seconds() > 120
    for name, key in ((".tick_context.json", "context_sha256"),
                      (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[key]
    before = read(HERE / "integrity_before.json")
    assert sha(ROOT / "pipeline/goal.json") == before["goal_sha256"]
    assert sha(ROOT / "SERVERS.yaml") == before["servers_sha256"]
    return owner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--review", type=Path)
    parser.add_argument("--review-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP"}))
        return
    owner = guard()
    assert sha(BODY) == BODY_SHA
    assert args.review and args.review.resolve().is_relative_to(HERE)
    assert sha(args.review) == args.review_sha256
    review = read(args.review)
    assert review["owner"] == owner and review["passed"] is True
    assert review["material_concerns"] == []
    assert review["reviewer_thread_id"] not in (
        owner["thread_id"], "/root", "/root/fresh_ops")
    assert review["body_sha256"] == BODY_SHA
    assert review["wrapper_sha256"] == sha(Path(__file__))
    intent = HERE / "kernel_suffix.intent.json"
    actual = HERE / "kernel_suffix.actual.json"
    assert not intent.exists() and not actual.exists(), "Reconcile; never replay."
    # This operation reads system records, not a runtime or GPU execution.
    # Runtime and training provenance remain immutable historical anchors.
    save(intent, {
        "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "kind": "READ_ONLY_SYSTEM_LOG_RECORDS_ONLY",
        "body_sha256": BODY_SHA, "wrapper_sha256": sha(Path(__file__)),
        "review_sha256": args.review_sha256,
        "candidate_id": "fine-leaf-receiver-conditioned-vector-exchange",
        "historical_source_commit": "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e",
        "historical_runtime_root": "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107",
        "historical_physical_gpu_UUID": "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c",
        "runtime_or_GPU_test": False,
        "previous_owner_binding_renewed": False, "no_replay": True,
    })
    process = subprocess.Popen(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
         "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
         "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c "
         + shlex.quote(BODY.read_text(encoding="utf-8"))],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace")
    result = {
        "owner": owner, "kind": "NEW_TARGETED_KERNEL_FILE_READ",
        "body_sha256": BODY_SHA, "wrapper_sha256": sha(Path(__file__)),
        "local_ssh_pid": process.pid, "certainty": "uncertain",
        "read_only": True, "signals_sent": False,
    }
    try:
        stdout, stderr = process.communicate(
            json.dumps({"execute_root": True, "owner": owner}), timeout=30)
        result.update(certainty="terminal", returncode=process.returncode,
                      stderr=stderr[:2000])
        assert process.returncode == 0, stderr[:2000]
        assert len(stdout.encode("utf-8")) <= 32768
        result["observation"] = json.loads(stdout)
        assert result["observation"]["owner"] == owner
        guard()
        result["transport_passed"] = True
    except BaseException as error:
        result.update(transport_passed=False, error_type=type(error).__name__,
                      error=str(error)[:1000])
        save(actual, result)
        raise
    save(actual, result)
    print(json.dumps({
        "path": str(actual), "sha256": sha(actual),
        "transport_passed": True,
        "outcome": result["observation"]["outcome"],
        "files": [
            {"path": row["path"], "outcome": row["outcome"],
             "target_matches": row.get("target_match_count_in_suffix")}
            for row in result["observation"]["files"]
        ],
    }))


if __name__ == "__main__":
    main()
