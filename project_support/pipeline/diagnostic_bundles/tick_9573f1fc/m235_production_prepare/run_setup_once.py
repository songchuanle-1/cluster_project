"""Default NOP. Root-only fresh stage/CPU collect/render; no training launch."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
from packet_runtime import (ROOT, HERE, TICK, OWNER, SOURCE, CONFIG, PRODUCER,
                            PRODUCTION, sha, read, save, guard, arguments, require_arguments)

FILES = ("production_controller.py", "lock_core.py", "entry_factory.py")


def embedded(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT.resolve())
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path),
            "bytes_base64": base64.b64encode(path.read_bytes()).decode("ascii")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--action", choices=("stage", "collect", "render"))
    parser.add_argument("--activation")
    parser.add_argument("--observation-review")
    parser.add_argument("--observation-review-sha256")
    arguments(parser)
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SSH_TORCH_GPU_OR_MUTATION"}))
        return
    require_arguments(args)
    assert args.action
    owner, receipt, server = guard(args)
    execution = TICK / "m235_setup_execution"
    execution.mkdir(exist_ok=True)
    intent, result_path = (execution / (args.action + "_" + name + ".json")
                           for name in ("intent", "actual"))
    assert not intent.exists() and not result_path.exists(), "Existing or uncertain action; reconcile, never replay"
    hashes = {name: sha(HERE / name) for name in FILES}
    packet = {"action": args.action, "stage": PRODUCER, "owner": owner,
              "training_launch_authorized": False}
    if args.action == "stage":
        packet["files"] = {name: {"sha256": hashes[name], "bytes_base64":
            base64.b64encode((HERE / name).read_bytes()).decode("ascii")} for name in FILES}
        request_reference = None
    else:
        staged = read(execution / "stage_actual.json")
        assert staged["owner"] == owner and staged["certainty"] == "terminal"
        assert staged["observation"]["files"] == hashes
        request = read(HERE / (args.action + "_request.draft.json"))
        request.update(owner=owner, execution_authorized=True)
        if args.action == "render":
            assert args.activation and args.observation_review and args.observation_review_sha256
            collected = read(execution / "collect_actual.json")
            assert collected["owner"] == owner and collected["certainty"] == "terminal"
            assert collected["observation"]["returncode"] == 0
            request["actual_observation_sha256"] = collected["observation"]["remote_result_sha256"]
            request["admission_receipt"] = embedded(args.admission)
            request["activation_receipt"] = embedded(args.activation)
            request["observation_independent_review"] = embedded(args.observation_review)
            assert request["observation_independent_review"]["sha256"] == args.observation_review_sha256
            peer = read(args.observation_review)
            assert peer["passed"] is True and peer["owner"] == owner and peer["material_concerns"] == []
            assert peer["reviewer_thread_id"] not in (owner["thread_id"], "/root", "/root/fresh_ops", "/root/sinc_prod")
            assert peer["source_commit"] == SOURCE
            assert peer["actual_observation_sha256"] == request["actual_observation_sha256"]
            assert peer["collect_actual_sha256"] == sha(execution / "collect_actual.json")
            activation = read(args.activation)
            assert activation["decision"] == "ALLOW_PRODUCTION_PATH_RENDER" and activation["owner"] == owner
            assert activation["source_commit"] == SOURCE
            assert activation["actual_observation_sha256"] == request["actual_observation_sha256"]
            assert activation["admission_receipt_sha256"] == args.admission_sha256
            assert activation["independent_observation_review_sha256"] == args.observation_review_sha256
            assert activation["training_launch_authorized"] is False
            assert not activation.get("draft_not_an_actual_receipt")
        request_path = execution / (args.action + "_request.json")
        save(request_path, request)
        packet.update(files=hashes, request_bytes_base64=base64.b64encode(request_path.read_bytes()).decode("ascii"),
                      request_sha256=sha(request_path))
        request_reference = {"path": request_path.relative_to(ROOT).as_posix(), "sha256": sha(request_path)}
    guard(args)
    save(intent, {"owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
                  "action": args.action, "request": request_reference, "FROZEN_sha256": sha(HERE / "FROZEN.json"),
                  "review_sha256": args.review_sha256, "current_verification_sha256": args.current_verification_sha256,
                  "admission_sha256": args.admission_sha256, "no_replay": True})
    remote = (HERE / "remote_receiver.py.txt").read_text(encoding="utf-8")
    command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
               "-o", "ConnectTimeout=8", "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no", "songcl@192.168.1.115",
               "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -B -c " + shlex.quote(remote)]
    record = {"owner": owner, "action": args.action, "certainty": "uncertain",
              "intent_sha256": sha(intent), "training_launch_or_GPU_use": False}
    try:
        outpath = execution / (args.action + "_transport.stdout.partial")
        errpath = execution / (args.action + "_transport.stderr.partial")
        outfile, errfile = outpath.open("x+b"), errpath.open("x+b")
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=outfile, stderr=errfile)
        record["local_ssh_pid"] = process.pid
        try:
            process.communicate(json.dumps(packet).encode("utf-8"), timeout=270)
            outfile.flush(); errfile.flush()
            assert outpath.stat().st_size <= 4194304
            stdout = outpath.read_text(encoding="utf-8", errors="replace")
            with errpath.open("rb") as stream:
                stream.seek(0, 2); stream.seek(max(0, stream.tell() - 32768))
                stderr = stream.read(32768).decode("utf-8", "replace")
            outfile.close(); errfile.close()
        except subprocess.TimeoutExpired:
            record["reason"] = "CPU setup uncertain; no signal, cleanup or replay"
            save(result_path, record)
            raise SystemExit(75)
        record.update(ssh_returncode=process.returncode, stdout=stdout, stderr=stderr)
        if process.returncode == 0:
            record["observation"] = json.loads(stdout)
            assert record["observation"]["owner"] == owner and record["observation"]["stage"] == PRODUCER
            record["certainty"] = record["observation"]["certainty"]
            if args.action != "stage" and record["observation"].get("remote_result_bytes_base64"):
                raw = base64.b64decode(record["observation"]["remote_result_bytes_base64"], validate=True)
                assert hashlib.sha256(raw).hexdigest() == record["observation"]["remote_result_sha256"]
                assert json.loads(raw) == record["observation"]["result"]
                save(execution / (args.action + "_result.json"), json.loads(raw))
    except Exception as error:
        record.update(error_type=type(error).__name__, error=str(error))
        save(result_path, record)
        raise
    save(result_path, record)
    assert record["certainty"] == "terminal" and record["ssh_returncode"] == 0
    if args.action != "stage":
        assert record["observation"]["returncode"] == 0 and record["observation"]["result"] is not None
    guard(args)
    print(json.dumps({"action": args.action, "path": str(result_path), "sha256": sha(result_path),
                      "training_launch_or_GPU_use": False}))


if __name__ == "__main__":
    main()
