"""Default NOP. New root-only source-bound native smoke/resources transport."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
OWNER = {
    "token": "2020a21f92b2424b8ebba78c4f9f14bf",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-10T13:10:18.102098+00:00",
    "deadline_at": "2026-11-10T14:10:18.102098+00:00",
    "context_sha256": "5d0914e95e16bc321726a9c371531296b82b0a1b0446d25ec237e39cd98d861b",
    "pending_sha256": "2d8c41483e9a663f2c335485c667deccc9f35355096101089bd612c78fcd0c59"
}
REMOTE_STAGE = "/data/songcl/Project/Cluster_project/pipeline/cso_2020a21f_gpu0"


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
    assert (datetime.fromisoformat(OWNER["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 300
    mode = read(ROOT / "pipeline/execution_mode.json")
    assert mode["mode"] == "foreground" and mode["target_thread_id"] == OWNER["thread_id"]
    for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == OWNER[key]
    frozen = read(HERE / "FROZEN.json")
    assert frozen["owner"] == OWNER
    assert all(sha(HERE / name) == value for name, value in frozen["files"].items())
    for item in frozen["anchors"].values():
        assert sha(ROOT / item["path"]) == item["sha256"]
    proof_path = Path(args.source_version).resolve()
    assert proof_path == (HERE / "source_version.json").resolve()
    assert sha(proof_path) == args.source_version_sha256 == frozen["source_version_sha256"]
    version = read(proof_path)
    assert version["owner"] == OWNER and version["source_commit"] == "af45707d7b6089f764843337c5f88af285383f88"
    template = read(HERE / "source_binding.template.json")
    assert version["source_files_exact9"] == template["source_files"]
    review_path = Path(args.review).resolve()
    assert review_path.is_relative_to(ROOT.resolve()) and sha(review_path) == args.review_sha256
    review = read(review_path)
    assert review["passed"] is True and review["owner"] == OWNER and review["material_concerns"] == []
    assert review["FROZEN_sha256"] == sha(HERE / "FROZEN.json")
    assert review["source_version_sha256"] == args.source_version_sha256
    assert review["worker_sha256"] == sha(HERE / "worker.py")
    assert review["runtime_sha256"] == sha(HERE / "native_runtime.py")
    assert review["transport_sha256"] == sha(__file__)
    assert review["reviewer_thread_id"] not in (OWNER["thread_id"], "/root", "/root/fresh_ops", "/root/sinc_prod")
    assert review["source_and_native_protocol_review_passed"] is True
    # The local canonical queue blocks transport while M235 or any server4/GPU0 project slot is active.
    queue = read(ROOT / "pipeline/queue.json")
    occupied = [task for task in queue["gpu_queues"].get("server-4", [])
                if task.get("status") in ("running", "claiming", "launching", "dispatching")
                and str(task.get("gpu", "0")) == "0"]
    assert not occupied, "GPU0 cap1 occupied (including M235); no SSH, staging or GPU attempt authorized"
    assert version["source_parent_commit"] == "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
    assert version["runtime_original_parent_commit"] == "b1e639b3ceb14bb5c65d9f81a084d41c834b951c"
    assert template["runtime_original_parent_commit"] == version["runtime_original_parent_commit"]
    return version, template



BOOTSTRAP = r"""
import base64,hashlib,json,os,pathlib,shlex,subprocess,sys
from datetime import datetime,timezone
assert os.getuid()==os.geteuid()==1001
import socket
assert socket.gethostname()=='dl04-MS-7E06' and not sys.flags.isolated and sys.dont_write_bytecode
assert 'torch' not in sys.modules,'Native guards must precede Torch import'
payload=json.load(sys.stdin)
owner=payload['owner']
assert owner['token']=='2020a21f92b2424b8ebba78c4f9f14bf'
assert owner['thread_id']=='01a159c5-29ab-7a22-ba7f-e79174757253'
assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>300
root='/data/songcl/Project/Cluster_project/Cluster_nsd_20261107'
actual=subprocess.check_output(['/usr/bin/git','--no-optional-locks','-c','core.fsmonitor=false','-C',root,'rev-parse','HEAD'],text=True,timeout=15).strip()
assert actual=='b1e639b3ceb14bb5c65d9f81a084d41c834b951c'
stage=pathlib.Path('/data/songcl/Project/Cluster_project/pipeline/cso_2020a21f_gpu0')
new=not stage.exists()
if payload.get('collect_only'):assert not new,'Collection cannot stage or launch'
if new:stage.mkdir(mode=0o700,exist_ok=False)
for name,item in payload['files'].items():
 path=(stage/name).resolve()
 assert path.is_relative_to(stage.resolve())
 raw=base64.b64decode(item['base64'],validate=True)
 assert hashlib.sha256(raw).hexdigest()==item['sha256']
 if new:
  path.parent.mkdir(parents=True,exist_ok=True)
  with path.open('xb') as stream:stream.write(raw)
 else:assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],name
mode,target=payload['mode'],payload['target']
assert mode in ('smoke','resources') and target in ('candidate','champion')
result=stage/(mode+'_'+target+'_result.json')
attempt=stage/(mode+'_'+target+'_attempt.json')
if payload.get('collect_only'):
 assert result.is_file()
 print(json.dumps({'certainty':'terminal','result':json.loads(result.read_text()),'result_sha256':hashlib.sha256(result.read_bytes()).hexdigest()}));sys.exit(0)
assert not result.exists() and not attempt.exists(),'Never replay an existing or uncertain arm'
with attempt.open('x') as stream:json.dump({'owner':owner,'mode':mode,'target':target,'no_replay':True},stream)
entry="import runpy,sys;sys.path.insert(0,"+repr(str(stage))+");sys.argv=["+repr(str(stage/'worker.py'))+",'--execute-root','--lease',"+repr(str(stage/'execution_lease.json'))+",'--mode',"+repr(mode)+",'--target',"+repr(target)+"];runpy.run_path("+repr(str(stage/'worker.py'))+",run_name='__main__')"
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',GIT_OPTIONAL_LOCKS='0')
assert not sys.flags.isolated
outpath,errpath=stage/(mode+'_'+target+'_stdout.partial'),stage/(mode+'_'+target+'_stderr.partial')
outfile,errfile=outpath.open('xb'),errpath.open('xb')
process=subprocess.Popen([sys.executable,'-B','-c',entry],cwd=str(stage),env=env,stdout=outfile,stderr=errfile)
try:
 process.wait(timeout=650)
 outfile.flush();errfile.flush()
 def tail(path,limit):
  with path.open('rb') as stream:
   stream.seek(0,2);stream.seek(max(0,stream.tell()-limit));return stream.read(limit).decode('utf8','replace')
 stdout,stderr=tail(outpath,65536),tail(errpath,65536)
except subprocess.TimeoutExpired:
 print(json.dumps({'certainty':'uncertain','remote_pid':process.pid,'reason':'No signal or replay; preserve stage and attempt'}));sys.exit(75)
record={'certainty':'terminal','returncode':process.returncode,'worker_stdout':stdout,'worker_stderr':stderr,'remote_pid':process.pid}
if result.is_file():
 record['result']=json.loads(result.read_text());record['result_sha256']=hashlib.sha256(result.read_bytes()).hexdigest()
print(json.dumps(record))
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--collect-only", action="store_true")
    parser.add_argument("--mode", choices=("smoke", "resources"))
    parser.add_argument("--target", choices=("candidate", "champion"))
    parser.add_argument("--experiment-id", required=False)
    parser.add_argument("--source-version")
    parser.add_argument("--source-version-sha256")
    parser.add_argument("--review")
    parser.add_argument("--review-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_TORCH_SSH_GPU_OR_MUTATION"}))
        return
    assert all((args.experiment_id, args.mode, args.target, args.source_version, args.source_version_sha256, args.review, args.review_sha256))
    assert args.experiment_id == "M236-CSO", "No new candidate or experiment is authorized"
    version, binding = guard(args)
    suffix = args.mode + "_" + args.target
    execution = HERE.parent / "cso_native_execution"
    execution.mkdir(exist_ok=True)
    binding_path = execution / "source_binding.json"
    manifest_path = execution / "native_manifest.json"
    lease_path = execution / "execution_lease.json"
    if not binding_path.exists():
        binding.update(source_commit=version["source_commit"], source_version_sha256=args.source_version_sha256,
                       source_version_proof=version, experiment_id=args.experiment_id)
        save(binding_path, binding)
        manifest = read(HERE / "manifest_template.json")
        manifest.update(owner=OWNER, code_commit=version["source_commit"], experiment_id=args.experiment_id, source_binding_sha256=sha(binding_path))
        save(manifest_path, manifest)
        save(lease_path, {"project": "cluster_project", "thread_id": OWNER["thread_id"], "owner": OWNER,
            "physical_gpu": 0, "gpu_uuid": manifest["gpu_uuid"], "allowed_gpus": [0],
            "native_manifest_sha256": sha(manifest_path), "source_binding_sha256": sha(binding_path),
            "resource_authorization": manifest["resource_authorization"], "resource_memory_policy": manifest["resource_memory_policy"]})
    else:
        assert read(binding_path)["source_version_sha256"] == args.source_version_sha256
        assert read(binding_path)["experiment_id"] == args.experiment_id
        assert read(manifest_path)["owner"] == OWNER
        assert read(lease_path)["native_manifest_sha256"] == sha(manifest_path)
    paths = dict(read(HERE / "manifest_template.json")["diagnostic_files"])
    raw_files = {name: (HERE / name).read_bytes() for name in paths}
    raw_files.update({"source_binding.json": binding_path.read_bytes(), "native_manifest.json": manifest_path.read_bytes(),
                      "execution_lease.json": lease_path.read_bytes()})
    payload = {"owner": OWNER, "mode": args.mode, "target": args.target, "collect_only": args.collect_only,
        "files": {name: {"sha256": hashlib.sha256(raw).hexdigest(), "base64": base64.b64encode(raw).decode("ascii")}
                  for name, raw in raw_files.items()}}
    action = "collect" if args.collect_only else "run"
    request_path, intent_path, result_path = (execution / (action + "_" + suffix + "_" + name + ".json")
                                             for name in ("request", "intent", "actual"))
    assert not any(path.exists() for path in (request_path, intent_path, result_path)), "Existing or uncertain attempt; never replay"
    save(request_path, {"owner": OWNER, "mode": args.mode, "target": args.target, "action": action,
        "source_version_sha256": args.source_version_sha256, "native_manifest_sha256": sha(manifest_path),
        "independent_review_sha256": args.review_sha256, "transport_sha256": sha(__file__),
        "payload_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()})
    guard(args)
    save(intent_path, {"owner": OWNER, "no_replay": True, "request_sha256": sha(request_path),
                       "remote_stage": REMOTE_STAGE, "mode": args.mode, "target": args.target, "action": action})
    record = {"owner": OWNER, "certainty": "uncertain", "request_sha256": sha(request_path), "intent_sha256": sha(intent_path)}
    base_conda = "/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh"
    base_sha = "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
    verifier = "import pathlib,hashlib,os,socket;assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001;assert hashlib.sha256(pathlib.Path(" + repr(base_conda) + ").read_bytes()).hexdigest()==" + repr(base_sha)
    activation = "/usr/bin/python3 -I -B -c " + shlex.quote(verifier) + " && source " + shlex.quote(base_conda) + " && conda activate project_cluster && exec " + shlex.join(["python", "-B", "-c", BOOTSTRAP])
    command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8", "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no",
        "songcl@192.168.1.115", "PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' " + shlex.join(["bash", "-lc", activation])]
    try:
        capture_out = (execution / (action + "_" + suffix + "_transport.stdout.partial")).open("x+b")
        capture_err = (execution / (action + "_" + suffix + "_transport.stderr.partial")).open("x+b")
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=capture_out, stderr=capture_err)
        record["local_ssh_pid"] = process.pid
        try:
            process.communicate(json.dumps(payload).encode("utf8"), timeout=700)
            capture_out.flush(); capture_err.flush()
            assert capture_out.tell() <= 4194304
            capture_out.seek(0); stdout = capture_out.read().decode("utf8", "replace")
            capture_err.seek(0, 2); capture_err.seek(max(0, capture_err.tell()-65536)); stderr = capture_err.read().decode("utf8", "replace")
            capture_out.close(); capture_err.close()
        except subprocess.TimeoutExpired:
            record["reason"] = "SSH/native outcome uncertain; no signal, replay or stage deletion"
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
    assert process.returncode == 0 and record["observation"] is not None, "Preserve actual outcome; no replay"
    observation = record["observation"]
    assert observation["certainty"] == "terminal" and observation["result"]["execution_completed"] is True
    assert observation["result"]["owner"] == OWNER
    print(json.dumps({"path": str(result_path), "sha256": sha(result_path), "mode": args.mode,
                      "target": args.target, "scientific_admission": False,
                      "status": "ACTUAL_NATIVE_OUTCOME_PRESERVED_REQUIRES_INDEPENDENT_RESULT_REVIEW"}))


if __name__ == "__main__":
    main()
