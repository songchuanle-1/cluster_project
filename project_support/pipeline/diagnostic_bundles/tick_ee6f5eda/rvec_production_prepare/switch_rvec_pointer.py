"""Default NOP. Reviewed local conda_source-only switch after actual setup."""
import argparse
import copy
import json
import os
from pathlib import Path
from packet_runtime import (ROOT, HERE, TICK, OWNER, PRODUCTION, SOURCE, sha, read, save,
                            guard, arguments, require_arguments, actual_production)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--production-result")
    parser.add_argument("--production-review")
    parser.add_argument("--production-review-sha256")
    arguments(parser)
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SERVERS_QUEUE_SSH_OR_SOURCE_MUTATION"}))
        return
    require_arguments(args)
    assert all((args.production_result, args.production_review, args.production_review_sha256))
    guard(args)
    production = actual_production(args.production_result, args.production_review, args.production_review_sha256)
    import pipeline_monitor as monitor
    import yaml
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard(args)
        execution = TICK / "rvec_pointer_execution"
        execution.mkdir(exist_ok=True)
        intent, result = (execution / name for name in ("switch_intent.json", "switch_result.json"))
        assert not intent.exists() and not result.exists(), "Existing or uncertain switch; reconcile, never replay"
        baseline = read(HERE / "baseline.json")
        path = ROOT / "SERVERS.yaml"
        before = path.read_bytes()
        old = baseline["SERVERS_parsed"]["servers"]["server-4"]["conda_source"]
        new = production["shim"]
        assert new == PRODUCTION + "/conda_source.sh"
        assert before.count(old.encode()) == 1
        changed = before.replace(old.encode(), new.encode(), 1)
        expected = copy.deepcopy(baseline["SERVERS_parsed"])
        expected["servers"]["server-4"]["conda_source"] = new
        assert yaml.safe_load(changed) == expected
        protected = {name: sha(ROOT / name) for name in ("pipeline/queue.json", "pipeline/running.json",
                     "pipeline/research_work.json", "pipeline/goal.json", "pipeline/closure_policy.json")}
        save(intent, {"owner": OWNER, "source_commit": SOURCE, "SERVERS_before_sha256": sha(path),
                      "production_result_sha256": sha(args.production_result),
                      "production_review_sha256": args.production_review_sha256,
                      "only_conda_source_changed": True, "no_replay": True})
        temporary = ROOT / "SERVERS.yaml.rvec_ee6f5eda.tmp"
        assert not temporary.exists()
        with temporary.open("xb") as stream:
            stream.write(changed)
            stream.flush()
            os.fsync(stream.fileno())
        assert path.read_bytes() == before
        guard(args)
        os.replace(temporary, path)
        assert yaml.safe_load(path.read_text(encoding="utf-8")) == expected
        assert all(sha(ROOT / name) == value for name, value in protected.items())
        guard(args, pointer=True)
        save(result, {"owner": OWNER, "source_commit": SOURCE, "SERVERS_before_sha256": baseline["SERVERS_sha256"],
                      "SERVERS_after_sha256": sha(path), "only_conda_source_changed": True,
                      "remote_code_root_unchanged": True, "queue_unchanged": True,
                      "training_started": False, "SSH_GPU": False})
        print(json.dumps({"path": str(result), "sha256": sha(result), "training_started": False}))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
