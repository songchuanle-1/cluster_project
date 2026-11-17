"""Default NOP. Root-only once-only reviewed stdin CPU constructor transport."""
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
OWNER = {
    "token": "b410c66a6c6243e1bbb8f970d1bd8c29",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-09T03:06:13.222314+00:00",
    "deadline_at": "2026-11-09T04:06:13.222314+00:00",
    "context_sha256": "bfe9accafc09e5b58f8d8a53cc83cd308e01dfd40be224a91b76b68c1abbb60c",
    "pending_sha256": "da4f035909f955959b6ff4b21a0b5e54744a6ff95bf13fa645526f18ec1a2db2"
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, value):
    with Path(path).open("x", encoding="utf8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def guard(args):
    assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    assert os.environ.get("CODEX_THREAD_ID") == OWNER["thread_id"]
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {key: owner[key] for key in OWNER} == OWNER
    assert (datetime.fromisoformat(OWNER["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 180
    mode = read(ROOT / "pipeline/execution_mode.json")
    assert mode["mode"] == "foreground" and mode["target_thread_id"] == OWNER["thread_id"]
    for name, field in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == OWNER[field]
    frozen = read(HERE / "FROZEN.json")
    assert frozen["owner"] == OWNER
    assert all(sha(HERE / name) == expected for name, expected in frozen["files"].items())
    for anchor in frozen["anchors"].values():
        assert sha(ROOT / anchor["path"]) == anchor["sha256"]
    binding = read(HERE / "source_binding.json")
    assert binding["owner"] == OWNER and binding["source_commit"] == frozen["source_commit"]
    assert binding["source_parent_commit"] == "0f8cc0f978b38c24e159d3a2d37344f59cc9a0be"
    assert binding["runtime_original_parent_commit"] == "0747f6acec1c61018ec99acf2efa5329c9b3523c"
    assert binding["source_version_proof"]["owner"] == OWNER
    assert binding["source_version_proof"]["source_files_exact9"] == binding["source_files_exact9"]
    for name, relative in binding["probe_source_paths"].items():
        path = (ROOT / relative).resolve()
        assert path.is_relative_to(ROOT.resolve()) and sha(path) == binding["probe_source_hashes"][name]
    for relative, expected in binding["source_files_exact9"].items():
        assert sha(ROOT / binding["r1_source_root"] / relative) == expected
    review_path = Path(args.review).resolve()
    assert review_path.is_relative_to(ROOT.resolve()) and sha(review_path) == args.review_sha256
    review = read(review_path)
    assert review["passed"] is True and review["owner"] == OWNER
    assert review["reviewer_thread_id"] not in (OWNER["thread_id"], "/root", "/root/fresh_ops")
    assert review["FROZEN_sha256"] == sha(HERE / "FROZEN.json")
    assert review["producer_sha256"] == sha(HERE / "constructor_probe.py")
    assert review["transport_sha256"] == sha(__file__)
    assert review["source_binding_sha256"] == sha(HERE / "source_binding.json")
    assert review["source_version_sha256"] == frozen["source_version_sha256"]
    assert review["source_review_passed"] is True and review["test_transport_review_passed"] is True
    assert review["material_concerns"] == []
    return binding


BOOTSTRAP = r"""
import base64,hashlib,json,os,socket,sys
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
assert not sys.flags.isolated and sys.dont_write_bytecode
assert os.environ.get('CUDA_VISIBLE_DEVICES')=='' and 'torch' not in sys.modules
payload=json.load(sys.stdin)
request=payload['request']
assert request['owner']['token']=='b410c66a6c6243e1bbb8f970d1bd8c29'
assert request['owner']['thread_id']=='01a159c5-29ab-7a22-ba7f-e79174757253'
assert datetime.now(timezone.utc)<datetime.fromisoformat(request['owner']['deadline_at'])
raw=base64.b64decode(payload['producer'],validate=True)
assert hashlib.sha256(raw).hexdigest()==request['producer_sha256']
request_raw=base64.b64decode(payload['request_raw'],validate=True)
assert json.loads(request_raw)==request
os.chdir('/')
sys.argv=['<hash-bound-r1-constructor-probe>','--execute-root']
scope={'__name__':'__main__','__file__':'<hash-bound-r1-constructor-probe>',
 'BOUND_PAYLOAD':payload,'ACTUAL_PRODUCER_SHA256':request['producer_sha256'],
 'ACTUAL_REQUEST_SHA256':hashlib.sha256(request_raw).hexdigest()}
exec(compile(raw,scope['__file__'],'exec'),scope)
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--review")
    parser.add_argument("--review-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SSH_TORCH_GPU_OR_MUTATION"}))
        return
    assert args.review and args.review_sha256
    binding = guard(args)
    execution = HERE.parent / "rvec_constructor_cpu_execution"
    execution.mkdir(exist_ok=True)
    request_path, intent_path, result_path = (execution / name for name in (
        "constructor_request.json", "constructor_intent.json", "constructor_actual.json"))
    assert not any(path.exists() for path in (request_path, intent_path, result_path)), "Preserve existing/uncertain attempt; no replay"
    request = {
        "owner": OWNER, "recorded_at": datetime.now(timezone.utc).isoformat(), "execution_authorized": True,
        "producer_sha256": sha(HERE / "constructor_probe.py"),
        "source_binding_sha256": sha(HERE / "source_binding.json"),
        "source_commit": binding["source_commit"], "GPU_use_authorized": False,
        "training_launch_authorized": False, "independent_review_sha256": args.review_sha256}
    save(request_path, request)
    payload = {
        "request": request, "request_raw": base64.b64encode(request_path.read_bytes()).decode("ascii"),
        "producer": base64.b64encode((HERE / "constructor_probe.py").read_bytes()).decode("ascii"),
        "binding": base64.b64encode((HERE / "source_binding.json").read_bytes()).decode("ascii"),
        "sources": {name: base64.b64encode((ROOT / path).read_bytes()).decode("ascii")
                    for name, path in binding["probe_source_paths"].items()}}
    guard(args)
    save(intent_path, {"owner": OWNER, "request_sha256": sha(request_path),
                       "review_sha256": args.review_sha256, "no_replay": True,
                       "remote_files_written": False, "GPU_use": False})
    base = "/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh"
    base_sha = "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
    verifier = "import pathlib,hashlib,os,socket;assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001;assert hashlib.sha256(pathlib.Path(" + repr(base) + ").read_bytes()).hexdigest()==" + repr(base_sha)
    activation = "/usr/bin/python3 -I -B -c " + shlex.quote(verifier) + " && source " + shlex.quote(base) + " && conda activate project_cluster && exec " + shlex.join(["python", "-B", "-c", BOOTSTRAP])
    command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8",
               "songcl@192.168.1.115", "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 GIT_OPTIONAL_LOCKS=0 " + shlex.join(["bash", "-lc", activation])]
    record = {"owner": OWNER, "certainty": "uncertain", "request_sha256": sha(request_path),
              "intent_sha256": sha(intent_path), "GPU_use": False, "remote_files_written": False}
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding="utf8", errors="replace")
        record["local_ssh_pid"] = process.pid
        try:
            stdout, stderr = process.communicate(json.dumps(payload), timeout=150)
        except subprocess.TimeoutExpired:
            record["reason"] = "CPU/SSH uncertain; preserve attempt, no signal or replay"
            save(result_path, record)
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
    assert record["returncode"] == 0 and record["observation"] is not None, "Preserve actual CPU failure"
    observed = record["observation"]
    assert observed["owner"] == OWNER and observed["all_fixed_tests_passed"] is True
    assert observed["producer_sha256"] == request["producer_sha256"]
    assert observed["source_binding_sha256"] == request["source_binding_sha256"]
    assert observed["request_sha256"] == sha(request_path)
    assert observed["cuda_initialized_before"] is False and observed["cuda_initialized_after"] is False
    assert all(observed[name] is True for name in ("all_five_parameters_identical",
        "raw_caller_rng_advanced", "guarded_caller_rng_preserved_exact",
        "python_rng_restored_exact", "numpy_rng_restored_exact", "torch_CPU_rng_restored_exact"))
    print(json.dumps({"status": "ACTUAL_CONSTRUCTOR_CPU_RESULT_REQUIRES_INDEPENDENT_REVIEW",
                      "path": str(result_path), "sha256": sha(result_path), "scientific_admission": False}))


if __name__ == "__main__":
    main()
