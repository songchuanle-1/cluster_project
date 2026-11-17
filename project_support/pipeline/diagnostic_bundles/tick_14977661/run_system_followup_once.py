"""Read the reviewed corrected journal/Apport evidence once, without replay."""
import argparse
from datetime import datetime, timezone
import json
import shlex
import subprocess
from run_system_diagnostic_once import guard, read, sha, save, HERE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--review")
    parser.add_argument("--review-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP"}))
        return
    owner = guard()
    body = HERE / "system_followup_prepare/system_followup_remote.py.txt"
    expected = "82fe3de006337e67d82fcb417cfcdd7675724c184a78bd0ef753d9624474d30b"
    assert sha(body) == expected
    assert sha(args.review) == args.review_sha256
    peer = read(args.review)
    assert peer["passed"] is True and peer["owner"] == owner and peer["material_concerns"] == []
    assert peer["reviewer_thread_id"] not in (owner["thread_id"], "/root", "/root/fresh_ops")
    assert expected in json.dumps(peer)
    intent, output = HERE / "system_followup.intent.json", HERE / "system_followup.actual.json"
    assert not intent.exists() and not output.exists(), "Reconcile without replay."
    save(intent, {"owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
                  "body_sha256": expected, "review_sha256": args.review_sha256,
                  "prior_actual_sha256": sha(HERE / "system_diagnostic.actual.json"),
                  "read_only": True, "no_replay": True})
    process = subprocess.Popen(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
         "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
         "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c "
         + shlex.quote(body.read_text(encoding="utf-8"))],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace")
    result = {"owner": owner, "certainty": "uncertain", "local_ssh_pid": process.pid,
              "kind": "CURRENT_TARGETED_APPORT_AND_CORRECTED_KERNEL_QUERY", "read_only": True}
    try:
        stdout, stderr = process.communicate(
            json.dumps({"execute_root": True, "owner": owner}), timeout=45)
        result.update(returncode=process.returncode, certainty="terminal", stderr=stderr[:2000])
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
                      "observation_keys": list(result["observation"])}))


if __name__ == "__main__":
    main()
