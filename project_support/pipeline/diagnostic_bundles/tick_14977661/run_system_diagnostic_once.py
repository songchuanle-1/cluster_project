"""Execute the reviewed current-owner read-only system diagnostic once."""
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
PACKET = HERE / "system_diagnostic_prepare_v2"
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
    current = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    owner = {key: current[key] for key in KEYS}
    assert owner == read(HERE / "current_owner_binding.json")
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert sys.dont_write_bytecode and os.environ["GIT_OPTIONAL_LOCKS"] == "0"
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 100
    for name, key in ((".tick_context.json", "context_sha256"),
                      (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[key]
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
    assert sha(PACKET / "FROZEN.json") == "a5049725dde80c5495e0ec5c7b67d5c4aafd1b312ddcb0edf8e72207b50ed9a5"
    frozen = read(PACKET / "FROZEN.json")
    assert frozen["owner"] == owner
    for name, digest in frozen["files"].items():
        assert sha(PACKET / name) == digest
    binding = read(PACKET / "binding.json")
    for item in binding["anchors"].values():
        assert sha(item["path"]) == item["sha256"]
    body = PACKET / "system_diagnostic_remote.py.txt"
    assert sha(body) == binding["body_sha256"] == "90fb7ccb5184fcb2011c32e74169cf577db435df73a928ec67e128e1f8423f4e"
    assert args.review and args.review.resolve().is_relative_to(HERE.resolve())
    assert sha(args.review) == args.review_sha256
    peer = read(args.review)
    assert peer["passed"] is True and peer["owner"] == owner and peer["material_concerns"] == []
    assert peer["reviewer_thread_id"] not in (owner["thread_id"], "/root", "/root/fresh_ops")
    assert peer["body_sha256"] == sha(body)
    intent, output = HERE / "system_diagnostic.intent.json", HERE / "system_diagnostic.actual.json"
    assert not intent.exists() and not output.exists(), "Reconcile without replay."
    save(intent, {"owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
                  "FROZEN_sha256": sha(PACKET / "FROZEN.json"), "body_sha256": sha(body),
                  "source_review": {"path": str(args.review), "sha256": args.review_sha256},
                  "read_only": True, "no_replay": True})
    process = subprocess.Popen(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
         "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
         "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c "
         + shlex.quote(body.read_text(encoding="utf-8"))],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace")
    result = {"owner": owner, "certainty": "uncertain", "local_ssh_pid": process.pid,
              "kind": "CURRENT_TARGETED_WORKER_SYSTEM_FORENSIC_OBSERVATION",
              "body_sha256": sha(body), "read_only": True}
    try:
        stdout, stderr = process.communicate(json.dumps({"execute_root": True, "owner": owner}), timeout=65)
        result.update(certainty="terminal", returncode=process.returncode, stderr=stderr[:2000])
        assert process.returncode == 0, stderr[:2000]
        assert len(stdout.encode()) <= 65536
        result["observation"] = json.loads(stdout)
        assert result["observation"]["owner"] == owner
        guard()
        result["transport_passed"] = True
    except BaseException as error:
        result.update(transport_passed=False, error_type=type(error).__name__, error=str(error))
        save(output, result)
        raise
    save(output, result)
    print(json.dumps({"path": str(output), "sha256": sha(output),
                      "transport_passed": True,
                      "observation_keys": list(result["observation"]),
                      "read_only": True, "diagnostic_findings_not_assumed_pass": True}))


if __name__ == "__main__":
    main()
