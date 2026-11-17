"""Default NOP. Reviewed root-only one-shot stdin CPU probe, no remote files."""
import argparse
import base64
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
EXPECTED_OWNER = {'token': '9dfa43fa89ad4dc4832126a940ed821e', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-08T19:05:14.568365+00:00', 'deadline_at': '2026-11-08T20:05:14.568365+00:00', 'context_sha256': '12e82b3f247ce035e8d9d8c8a16ad534b0ef96de3948a3d3c2d07c4abd3177c5', 'pending_sha256': 'a50fe33d3236d8b847c8c284b2fe917ac60aae7caf766e0969b25b33ee0a10d5'}
PRODUCER_SHA = "e58566fde0eb5179cfbea9477ffbb9ff7765868ec2919b6b1a2b29a3b9ae3388"
RECEIPT_SHA = "52bf897dc89729063ffb429035b1cd07f14d3ea8d3e690812a4e3adfb48ed266"
REVISION_SHA = "3edbff4aa35f05a36da799b23cb54e154e6387faa30b1953a659b47267ccf9e2"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, value):
    with Path(path).open("x", encoding="utf8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def guard(review_path, review_sha):
    assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    assert HERE == ROOT / "pipeline/diagnostic_bundles/tick_9dfa43fa/faketensor_cpu_prepare"
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {k: owner[k] for k in EXPECTED_OWNER} == EXPECTED_OWNER
    assert os.environ.get("CODEX_THREAD_ID") == EXPECTED_OWNER["thread_id"]
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 180
    mode = read(ROOT / "pipeline/execution_mode.json")
    assert mode["mode"] == "foreground" and mode["target_thread_id"] == EXPECTED_OWNER["thread_id"]
    for name, field in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == EXPECTED_OWNER[field]
    packet = read(HERE / "FROZEN.json")
    assert packet["owner_provenance_only"] == EXPECTED_OWNER
    assert all(sha(HERE / name) == value for name, value in packet["files"].items())
    assert sha(HERE / "faketensor_cpu_probe.py") == PRODUCER_SHA
    receipt = ROOT / "pipeline/admissions/M233-NDE.json"
    assert sha(receipt) == RECEIPT_SHA
    canonical = read(receipt)
    assert canonical["code_commit"] == "0747f6acec1c61018ec99acf2efa5329c9b3523c"
    assert canonical["implementation_revision_sha256"] == REVISION_SHA
    assert canonical["canonical_receipt"] is True and canonical["draft"] is False
    review_path = Path(review_path).resolve()
    assert review_path.is_relative_to(ROOT.resolve()) and sha(review_path) == review_sha
    review = read(review_path)
    assert review["passed"] is True and review["owner"] == EXPECTED_OWNER
    assert review["producer_sha256"] == PRODUCER_SHA and review["transport_sha256"] == sha(__file__)
    assert review["FROZEN_sha256"] == sha(HERE / "FROZEN.json")
    assert review["reviewer_thread_id"] != EXPECTED_OWNER["thread_id"] and review.get("material_concerns", []) == []


BOOTSTRAP = r"""
import base64,hashlib,json,os,socket,sys
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
assert os.environ.get('CUDA_VISIBLE_DEVICES')=='' and sys.flags.isolated and sys.dont_write_bytecode
payload=json.load(sys.stdin)
raw=base64.b64decode(payload['producer_bytes_base64'],validate=True)
request_raw=base64.b64decode(payload['request_bytes_base64'],validate=True)
assert hashlib.sha256(raw).hexdigest()=='e58566fde0eb5179cfbea9477ffbb9ff7765868ec2919b6b1a2b29a3b9ae3388'==payload['producer_sha256']
assert hashlib.sha256(request_raw).hexdigest()==payload['request_sha256']
request=json.loads(request_raw)
assert request['owner']=={'token': '9dfa43fa89ad4dc4832126a940ed821e', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-08T19:05:14.568365+00:00', 'deadline_at': '2026-11-08T20:05:14.568365+00:00', 'context_sha256': '12e82b3f247ce035e8d9d8c8a16ad534b0ef96de3948a3d3c2d07c4abd3177c5', 'pending_sha256': 'a50fe33d3236d8b847c8c284b2fe917ac60aae7caf766e0969b25b33ee0a10d5'}
assert datetime.now(timezone.utc)<datetime.fromisoformat(request['owner']['deadline_at'])
os.chdir('/')
sys.argv=['<hash-bound-faketensor-cpu-probe>','--execute-root']
scope={'__name__':'__main__','__file__':'<hash-bound-faketensor-cpu-probe>',
 'BOUND_REQUEST':request,'ACTUAL_PRODUCER_SHA256':payload['producer_sha256'],
 'ACTUAL_REQUEST_SHA256':payload['request_sha256']}
exec(compile(raw,'<hash-bound-faketensor-cpu-probe>','exec'),scope)
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--review")
    parser.add_argument("--review-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SSH_TORCH_OR_MUTATION"}))
        return
    assert args.review and args.review_sha256
    guard(args.review, args.review_sha256)
    request_path = HERE / "cpu_request.json"
    intent_path = HERE / "cpu_intent.json"
    result_path = HERE / "cpu_actual.json"
    assert not any(path.exists() for path in (request_path, intent_path, result_path)), "Existing attempt: reconcile, never replay"
    request = read(HERE / "cpu_request.draft.json")
    request.update(execution_authorized=True, recorded_at=datetime.now(timezone.utc).isoformat())
    receipt = ROOT / "pipeline/admissions/M233-NDE.json"
    request["admission_receipt"]["bytes_base64"] = base64.b64encode(receipt.read_bytes()).decode("ascii")
    save(request_path, request)
    packet = {"producer_sha256": PRODUCER_SHA, "producer_bytes_base64": base64.b64encode((HERE / "faketensor_cpu_probe.py").read_bytes()).decode("ascii"),
              "request_sha256": sha(request_path), "request_bytes_base64": base64.b64encode(request_path.read_bytes()).decode("ascii")}
    guard(args.review, args.review_sha256)
    command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
               "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 "
               "/home/songcl/.conda/envs/project_cluster/bin/python -I -B -c " + shlex.quote(BOOTSTRAP)]
    save(intent_path, {"recorded_at": datetime.now(timezone.utc).isoformat(), "owner": EXPECTED_OWNER,
                       "producer_sha256": PRODUCER_SHA, "request_sha256": sha(request_path),
                       "independent_review_sha256": args.review_sha256, "no_replay": True,
                       "remote_stage_created": False, "training_launch_authorized": False, "GPU_use": False})
    record = {"recorded_at": datetime.now(timezone.utc).isoformat(), "owner": EXPECTED_OWNER,
              "producer_sha256": PRODUCER_SHA, "request_sha256": sha(request_path),
              "intent_sha256": sha(intent_path), "certainty": "uncertain", "GPU_use": False, "remote_files_written": False}
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding="utf8", errors="replace")
        record["local_ssh_pid"] = process.pid
        try:
            stdout, stderr = process.communicate(json.dumps(packet), timeout=120)
        except subprocess.TimeoutExpired:
            record["reason"] = "CPU child/SSH uncertain; no signal, cleanup or replay"
            save(result_path, record)
            print(json.dumps({"status": "UNCERTAIN_PRESERVE_ATTEMPT", "path": str(result_path), "sha256": sha(result_path)}))
            raise SystemExit(75)
        record.update(certainty="terminal", returncode=process.returncode, stdout=stdout, stderr=stderr)
        try:
            record["observation"] = json.loads(stdout)
        except json.JSONDecodeError:
            record["observation"] = None
    except Exception as error:
        record.update(error_type=type(error).__name__, error=str(error))
        save(result_path, record)
        raise
    save(result_path, record)
    assert record["returncode"] == 0 and record["observation"] is not None, "Preserve terminal CPU failure; do not replay"
    observation = record["observation"]
    assert observation["owner"] == EXPECTED_OWNER and observation["producer_sha256"] == PRODUCER_SHA
    assert observation["request_sha256"] == sha(request_path)
    assert observation["cuda_initialized_before"] is False and observation["cuda_initialized_after"] is False
    guard(args.review, args.review_sha256)
    print(json.dumps({"status": "ACTUAL_CPU_OBSERVATION_CAPTURED_NOT_ROOT_CAUSE_OR_REPAIR", "path": str(result_path),
                      "sha256": sha(result_path), "GPU_use": False, "training_launch_authorized": False}))


if __name__ == "__main__":
    main()
