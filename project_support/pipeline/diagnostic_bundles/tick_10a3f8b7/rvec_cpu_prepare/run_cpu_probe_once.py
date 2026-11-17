"""Default NOP. Reviewed root-only once-only stdin CPU implementation test."""
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
SOURCE_ROOT = HERE.parent / "rvec_prepare/source"
EXPECTED_OWNER = {
    "token": "10a3f8b7d1bc4c5083b9b476c4d6fb94",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-08T21:09:22.656483+00:00",
    "deadline_at": "2026-11-08T22:09:22.656483+00:00",
    "context_sha256": "96ccdaba46f448a2c295d1407b3e782b9f9d1052825fe18b2e4f967a458d3d71",
    "pending_sha256": "a5a8fe814217e681000a6efca7eaeca7999792c27b10345892113ebb4f31ef9f",
}
PRODUCER_SHA = "9d329eecab5fa19345a64e5ec2d8c4ca8c06a968a27b35453ac801355eccf878"
SOURCE_BINDING_SHA = "f33a05f577c2da4da91636af9124b21c433ba3933030c917b6b4c9d028c9e60f"
RUNTIME_HEAD = "0747f6acec1c61018ec99acf2efa5329c9b3523c"


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
    assert HERE == ROOT / "pipeline/diagnostic_bundles/tick_10a3f8b7/rvec_cpu_prepare"
    assert len(PRODUCER_SHA) == len(SOURCE_BINDING_SHA) == 64
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {k: owner[k] for k in EXPECTED_OWNER} == EXPECTED_OWNER
    assert os.environ.get("CODEX_THREAD_ID") == EXPECTED_OWNER["thread_id"]
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 180
    mode = read(ROOT / "pipeline/execution_mode.json")
    assert mode["mode"] == "foreground" and mode["target_thread_id"] == EXPECTED_OWNER["thread_id"]
    for name, field in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == EXPECTED_OWNER[field]
    frozen = read(HERE / "FROZEN.json")
    assert frozen["owner"] == EXPECTED_OWNER and frozen["candidate_id"] == "fine-leaf-receiver-conditioned-vector-exchange"
    assert all(sha(HERE / name) == value for name, value in frozen["files"].items())
    assert sha(HERE / "rvec_cpu_probe.py") == PRODUCER_SHA
    assert sha(HERE / "source_binding.json") == SOURCE_BINDING_SHA
    binding = read(HERE / "source_binding.json")
    assert binding["owner"] == EXPECTED_OWNER and len(binding["source_files"]) == 9
    for relative, expected in binding["source_files"].items():
        path = (SOURCE_ROOT / relative).resolve()
        assert path.is_relative_to(SOURCE_ROOT.resolve()) and sha(path) == expected
    legacy = ROOT / binding["legacy_graph_reference"]["path"]
    assert sha(legacy) == binding["legacy_graph_reference"]["sha256"]
    for anchor in binding["anchors"].values():
        assert sha(ROOT / anchor["path"]) == anchor["sha256"]
    observation = read(ROOT / binding["anchors"]["native_identity"]["path"])["observation"]
    assert observation["hostname"] == "dl04-MS-7E06" and observation["runtime_HEAD"] == RUNTIME_HEAD
    assert "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c" in observation["gpu0"]
    review_path = Path(review_path).resolve()
    assert review_path.is_relative_to(ROOT.resolve()) and sha(review_path) == review_sha
    review = read(review_path)
    assert review["passed"] is True and review["owner"] == EXPECTED_OWNER
    assert review["producer_sha256"] == PRODUCER_SHA and review["transport_sha256"] == sha(__file__)
    assert review["source_binding_sha256"] == SOURCE_BINDING_SHA
    assert review["FROZEN_sha256"] == sha(HERE / "FROZEN.json")
    assert review["reviewer_thread_id"] not in (EXPECTED_OWNER["thread_id"], "/root/fresh_ops")
    assert review["source_review_passed"] is True and review["test_transport_review_passed"] is True
    assert review.get("material_concerns", []) == []


BOOTSTRAP = r"""
import base64,hashlib,json,os,socket,sys
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
assert os.environ.get('CUDA_VISIBLE_DEVICES')=='' and sys.flags.isolated and sys.dont_write_bytecode
assert os.environ.get('PYTHONDONTWRITEBYTECODE')=='1'
payload=json.load(sys.stdin)
raw=base64.b64decode(payload['producer_bytes_base64'],validate=True)
request_raw=base64.b64decode(payload['request_bytes_base64'],validate=True)
assert hashlib.sha256(raw).hexdigest()=='9d329eecab5fa19345a64e5ec2d8c4ca8c06a968a27b35453ac801355eccf878'==payload['producer_sha256']
assert hashlib.sha256(request_raw).hexdigest()==payload['request_sha256']
request=json.loads(request_raw)
assert request['owner']['token']=='10a3f8b7d1bc4c5083b9b476c4d6fb94'
assert request['source_binding_sha256']=='f33a05f577c2da4da91636af9124b21c433ba3933030c917b6b4c9d028c9e60f'
assert datetime.now(timezone.utc)<datetime.fromisoformat(request['owner']['deadline_at'])
operator_raw=base64.b64decode(payload['operator_bytes_base64'],validate=True)
legacy_raw=base64.b64decode(payload['legacy_bytes_base64'],validate=True)
os.chdir('/')
sys.argv=['<hash-bound-rvec-cpu-probe>','--execute-root']
scope={'__name__':'__main__','__file__':'<hash-bound-rvec-cpu-probe>',
 'BOUND_REQUEST':request,'BOUND_OPERATOR_BYTES':operator_raw,'BOUND_LEGACY_BYTES':legacy_raw,
 'ACTUAL_PRODUCER_SHA256':payload['producer_sha256'],'ACTUAL_REQUEST_SHA256':payload['request_sha256']}
exec(compile(raw,'<hash-bound-rvec-cpu-probe>','exec'),scope)
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
    request_path, intent_path, result_path = (HERE / name for name in (
        "cpu_request.json", "cpu_intent.json", "cpu_actual.json"))
    assert not any(path.exists() for path in (request_path, intent_path, result_path)), "Existing attempt: reconcile, never replay"
    request = read(HERE / "cpu_request.draft.json")
    request.update(execution_authorized=True, recorded_at=datetime.now(timezone.utc).isoformat())
    request["source_binding_bytes_base64"] = base64.b64encode((HERE / "source_binding.json").read_bytes()).decode("ascii")
    save(request_path, request)
    binding = read(HERE / "source_binding.json")
    operator_path = SOURCE_ROOT / request["operator_relative_path"]
    legacy_path = ROOT / binding["legacy_graph_reference"]["path"]
    payload = {
        "producer_sha256": PRODUCER_SHA,
        "producer_bytes_base64": base64.b64encode((HERE / "rvec_cpu_probe.py").read_bytes()).decode("ascii"),
        "request_sha256": sha(request_path), "request_bytes_base64": base64.b64encode(request_path.read_bytes()).decode("ascii"),
        "operator_bytes_base64": base64.b64encode(operator_path.read_bytes()).decode("ascii"),
        "legacy_bytes_base64": base64.b64encode(legacy_path.read_bytes()).decode("ascii"),
    }
    guard(args.review, args.review_sha256)
    command = [
        "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8",
        "songcl@192.168.1.115",
        "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 "
        "/home/songcl/.conda/envs/project_cluster/bin/python -I -B -c " + shlex.quote(BOOTSTRAP),
    ]
    save(intent_path, {
        "recorded_at": datetime.now(timezone.utc).isoformat(), "owner": EXPECTED_OWNER,
        "producer_sha256": PRODUCER_SHA, "source_binding_sha256": SOURCE_BINDING_SHA,
        "request_sha256": sha(request_path), "independent_review_sha256": args.review_sha256,
        "no_replay": True, "remote_stage_created": False, "training_launch_authorized": False, "GPU_use": False,
    })
    record = {
        "recorded_at": datetime.now(timezone.utc).isoformat(), "owner": EXPECTED_OWNER,
        "producer_sha256": PRODUCER_SHA, "source_binding_sha256": SOURCE_BINDING_SHA,
        "request_sha256": sha(request_path), "intent_sha256": sha(intent_path),
        "certainty": "uncertain", "GPU_use": False, "remote_files_written": False,
    }
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding="utf8", errors="replace")
        record["local_ssh_pid"] = process.pid
        try:
            stdout, stderr = process.communicate(json.dumps(payload), timeout=120)
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
    assert observation["source_binding_sha256"] == SOURCE_BINDING_SHA
    assert observation["cuda_initialized_before"] is False and observation["cuda_initialized_after"] is False
    assert observation["all_fixed_tests_passed"] is True
    assert observation["python_rng_restored_exact"] and observation["torch_CPU_rng_restored_exact"] and observation["numpy_rng_restored_exact"]
    guard(args.review, args.review_sha256)
    print(json.dumps({
        "status": "ACTUAL_CPU_IMPLEMENTATION_TEST_CAPTURED_NOT_NATIVE_OR_ADMISSION",
        "path": str(result_path), "sha256": sha(result_path),
        "GPU_use": False, "training_launch_authorized": False,
    }))


if __name__ == "__main__":
    main()
