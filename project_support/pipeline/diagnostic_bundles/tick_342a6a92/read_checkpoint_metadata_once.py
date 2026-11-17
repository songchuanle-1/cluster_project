"""Root-only bounded checkpoint metadata observation; no Torch or unpickling."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
from reconcile_existing_once import guard, read, sha, save, HERE, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP"}))
        return
    owner = guard()
    body = HERE / "checkpoint_metadata_prepare/checkpoint_metadata_remote.py.txt"
    assert sha(body) == "a0b0c63b5fef131ce8c53446c7f60f195573906d64633a0d1b2341682514dc14"
    terminal = read(HERE / "reconcile.actual.json")
    assert terminal["owner"] == owner and terminal["passed"] is True
    assert terminal["observation"]["process"]["exists"] is False
    prior = read(ROOT / "pipeline/diagnostic_bundles/tick_6d1f5659/native_summary.actual.json")
    request = {"owner": owner, "work_dir": prior["observation"]["actual_work_dir"]}
    intent, output = HERE / "checkpoint_metadata.intent.json", HERE / "checkpoint_metadata.actual.json"
    assert not intent.exists() and not output.exists(), "Reconcile without replay."
    save(intent, {"owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
                  "body_sha256": sha(body), "script_sha256": sha(__file__),
                  "terminal_observation_sha256": sha(HERE / "reconcile.actual.json"),
                  "request": request, "read_only": True, "no_replay": True})
    process = subprocess.Popen(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
         "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
         "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c "
         + shlex.quote(body.read_text(encoding="utf-8"))],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace")
    result = {"owner": owner, "certainty": "uncertain", "local_ssh_pid": process.pid,
              "kind": "CURRENT_BOUNDED_CHECKPOINT_METADATA_OBSERVATION", "read_only": True}
    try:
        stdout, stderr = process.communicate(json.dumps(request), timeout=35)
        result.update(certainty="terminal", returncode=process.returncode, stderr=stderr[:2000])
        assert process.returncode == 0, stderr[:2000]
        assert len(stdout.encode()) < 32768
        observed = result["observation"] = json.loads(stdout)
        assert observed["owner"] == owner
        assert observed["Torch_imported"] is False and observed["GPU_compute"] is False
        assert observed["unpickling_or_code_execution"] is False
        for row in observed["checkpoints"]:
            assert row["metadata_prefix_bytes_read"] <= 65536
            assert row["tensor_storage_read"] is False
        guard()
        result["passed"] = True
    except BaseException as error:
        result.update(passed=False, error_type=type(error).__name__, error=str(error))
        save(output, result)
        raise
    save(output, result)
    print(json.dumps({"path": str(output), "sha256": sha(output),
                      "checkpoints": [{"name": Path(row["path"]).name,
                                       "status": row["status"], "meta": row["meta"],
                                       "metadata_prefix_bytes_read": row["metadata_prefix_bytes_read"]}
                                      for row in observed["checkpoints"]],
                      "tensor_storage_read": False}))


if __name__ == "__main__":
    main()
