"""ROOT-only once runner. Default NOP; large bodies travel on SSH stdin."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from finalize_packet import build_packet

HERE = Path(__file__).resolve().parent
TICK = HERE.parent
ROOT = Path("D:/project/cluster_project")
KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
LIMIT = 32 * 1024 * 1024


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def save(path, value):
    encoded = (json.dumps(value, ensure_ascii=True, indent=2) + "\n").encode()
    if len(encoded) > LIMIT:
        raise RuntimeError("LOCAL_ACTUAL_ARTIFACT_32MIB_BOUND")
    with Path(path).open("xb") as output:
        output.write(encoded)


def guard(margin=175):
    live = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    owner = {key: live[key] for key in KEYS}
    assert owner == read(TICK / "current_owner_binding.json")
    assert owner["token"] == "4ecb5020c4c54abeb26dc874ed90080e" and live["mode"] == "design"
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert sys.dont_write_bytecode and os.environ["GIT_OPTIONAL_LOCKS"] == "0"
    now = dt.datetime.now(dt.timezone.utc)
    assert (dt.datetime.fromisoformat(owner["deadline_at"]) - now).total_seconds() > margin
    if margin:
        latest = dt.datetime.fromisoformat(owner["deadline_at"]) - dt.timedelta(minutes=9)
        assert now < latest, "LATEST_ROOT_START_IS_CURRENT_DEADLINE_MINUS_NINE_MINUTES"
    for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[key]
    integrity = read(TICK / "integrity_before.json")
    assert sha(ROOT / "pipeline/goal.json") == integrity["goal_sha256"]
    assert sha(ROOT / "SERVERS.yaml") == integrity["servers_sha256"]
    return owner


def bootstrap(supervisor_sha, carrier_sha, packet_sha):
    # Only these small fixed literals enter the Windows/SSH command line.
    return (
        "import hashlib,io,json,os,socket,sys\n"
        "from pathlib import Path\n"
        "assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001\n"
        "assert Path.cwd()==Path('/data/songcl/Project/Cluster_project/Cluster_nsd_20261107')\n"
        "raw=sys.stdin.buffer.read(2097153);assert len(raw)<=2097152\n"
        "p=json.loads(raw)\n"
        "h=lambda b:hashlib.sha256(b).hexdigest()\n"
        "assert h(p['supervisor_source'].encode())==" + repr(supervisor_sha) + "\n"
        "assert h(p['carrier_source'].encode())==" + repr(carrier_sha) + "\n"
        "packet=json.dumps(p['packet'],sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()\n"
        "assert h(packet)==" + repr(packet_sha) + "\n"
        "assert p['packet']['owner']['token']=='4ecb5020c4c54abeb26dc874ed90080e'\n"
        "body=json.dumps({'execute_root':True,'carrier_source':p['carrier_source'],'packet':p['packet']}).encode()\n"
        "sys.stdin=io.TextIOWrapper(io.BytesIO(body),encoding='utf-8')\n"
        "sys.argv=['reviewed_trace_supervisor','--execute-reviewed']\n"
        "exec(compile(p['supervisor_source'],'<reviewed_trace_supervisor>','exec'),"
        "{'__name__':'__main__','__file__':'<reviewed_trace_supervisor>'})\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--constructor-actual", type=Path)
    parser.add_argument("--constructor-sha256")
    parser.add_argument("--review", type=Path)
    parser.add_argument("--review-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SSH_OR_DATA_EXECUTION"}))
        return
    owner = guard()
    frozen = read(HERE / "FROZEN.json")
    assert frozen["owner"] == owner and frozen["author_executed"] is False
    assert frozen["scope"] == "SOURCE_FREEZE_ONLY_ACTUAL_CONSTRUCTOR_AND_FINAL_PEER_STILL_REQUIRED"
    for name, expected in frozen["files"].items():
        target = (HERE / name).resolve()
        assert target.is_relative_to(HERE) and sha(target) == expected
    assert args.review and args.review.is_absolute() and args.review.resolve().is_relative_to(TICK)
    assert sha(args.review) == args.review_sha256
    review = read(args.review)
    assert review["owner"] == owner and review["passed"] is True and review["material_concerns"] == []
    assert review["reviewer_thread_id"] != owner["thread_id"]
    assert review["frozen_sha256"] == sha(HERE / "FROZEN.json")
    for key, name in (("wrapper_sha256", "run_trace_once.py"),
                      ("body_sha256", "trace_supervisor.py"),
                      ("carrier_sha256", "trace_carrier.py"),
                      ("finalizer_sha256", "finalize_packet.py")):
        assert review[key] == sha(HERE / name)
    packet = build_packet(args.constructor_actual, args.constructor_sha256, args.review_sha256)
    assert packet["owner"] == owner
    packet_sha = hashlib.sha256(canonical(packet)).hexdigest()
    payload = json.dumps({"supervisor_source": (HERE / "trace_supervisor.py").read_bytes().decode(),
                          "carrier_source": (HERE / "trace_carrier.py").read_bytes().decode(),
                          "packet": packet}, ensure_ascii=True).encode()
    assert len(payload) <= 2 * 1024 * 1024
    small_bootstrap = bootstrap(sha(HERE / "trace_supervisor.py"), sha(HERE / "trace_carrier.py"), packet_sha)
    command = ("cd /data/songcl/Project/Cluster_project/Cluster_nsd_20261107 && "
               "PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' TOKENIZERS_PARALLELISM=false "
               "/usr/bin/python3 -I -B -c " + shlex.quote(small_bootstrap))
    argv = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
            "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no",
            "-o", "ConnectTimeout=8", "songcl@192.168.1.115", command]
    assert len(subprocess.list2cmdline(argv)) < 8000, "SMALL_BOOTSTRAP_COMMAND_BOUND"
    intent = HERE / "trace.intent.json"
    actual = HERE / "trace.actual.json"
    assert not intent.exists() and not actual.exists(), "Existing intent/result must be reconciled; no replay."
    save(HERE / "packet.final.json", packet)
    save(intent, {"owner": owner, "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                  "kind": "SINGLE_CPU_REAL_TRAIN_DATA_STAGE_TRACE", "no_replay": True,
                  "frozen_sha256": sha(HERE / "FROZEN.json"), "review_sha256": args.review_sha256,
                  "constructor_actual_sha256": args.constructor_sha256, "canonical_packet_sha256": packet_sha,
                  "small_bootstrap_bytes": len(small_bootstrap.encode()),
                  "large_source_transport": "JSON_STDIN_ONLY", "training_restart": False,
                  "GPU_compute": False})
    stdout_path = HERE / "trace.transport.stdout.partial"
    stderr_path = HERE / "trace.transport.stderr.partial"
    result = {"owner": owner, "kind": "SINGLE_CPU_REAL_TRAIN_DATA_STAGE_TRACE",
              "certainty": "uncertain", "automatic_retry": False,
              "frozen_sha256": sha(HERE / "FROZEN.json"), "canonical_packet_sha256": packet_sha}
    stdout_file = stdout_path.open("x+b")
    stderr_file = stderr_path.open("x+b")
    process = None
    try:
        process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=stdout_file, stderr=stderr_file)
        result.update(local_ssh_pid=process.pid, local_ssh_started_at=dt.datetime.now(dt.timezone.utc).isoformat())
        process.communicate(payload, timeout=150)
        stdout_file.flush()
        stderr_file.flush()
        assert stdout_path.stat().st_size <= LIMIT
        result.update(certainty="terminal", returncode=process.returncode,
                      stderr_tail=stderr_path.read_bytes()[-4096:].decode("utf-8", "replace"))
        assert process.returncode == 0
        observed = json.loads(stdout_path.read_bytes())
        assert observed["owner"] == owner
        result["observation"] = observed
        guard(0)
        result["transport_passed"] = True
    except BaseException as exc:
        result.update(transport_passed=False, error_type=type(exc).__name__, error=str(exc)[:1000],
                      reason="PRESERVE_TRANSPORT_AND_ALL_IDENTITIES_NO_AUTOMATIC_RETRY",
                      retained_local_transport_captures=[str(stdout_path), str(stderr_path)])
        if process is not None:
            result["local_ssh_returncode_observed"] = process.poll()
    finally:
        stdout_file.close()
        stderr_file.close()
        result["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        save(actual, result)
    observed = result.get("observation", {})
    print(json.dumps({"path": str(actual), "sha256": sha(actual),
                      "transport_passed": result["transport_passed"],
                      "carrier_returncode": observed.get("carrier_returncode"),
                      "stop_reason": observed.get("stop_reason"),
                      "captured_worker_identities": len(observed.get("worker_fates", [])),
                      "outer_cleanup_signals": len(observed.get("signals_sent", [])),
                      "scope": "CPU data diagnostic only; inspect inner status/fault/RSS/sharing evidence."}))


if __name__ == "__main__":
    main()
