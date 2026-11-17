"""Default NOP; peer-reviewed, root-only, at-most-120s remote CPU transport."""
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
AUTHOR_THREAD_ID = "01a1ba7b-e7ea-7e33-8551-b1fdfce9cdf5"
OWNER = {
    "token": "79656807d78e4cd687c70bdc7df26f5f",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-10T03:23:05.152371+00:00",
    "deadline_at": "2026-11-10T04:23:05.152371+00:00",
    "context_sha256": "a8ff28e14e85f34d389e9d57fb8a121d432965972597e466fb0410fe52c231a3",
    "pending_sha256": "fbbd449cc56296157ebace8fd2e5acce20f0474cf34aa4614575895cf8ffd0d9",
}
REMOTE_STAGE = "/data/songcl/Project/Cluster_project/pipeline/cso_cpu_79656807"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, value):
    with Path(path).open("x", encoding="utf8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def protected_snapshot():
    main = ROOT / "Cluster"
    def git(*args):
        return subprocess.check_output(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(main), *args],
            timeout=15)
    index = Path(git("rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = main / index
    paths = git("ls-files", "--modified", "--others", "--exclude-standard", "-z").decode().split("\0")
    return {
        "head": git("rev-parse", "HEAD").decode().strip(), "index_sha256": sha(index),
        "porcelain_hex": git("status", "--porcelain=v1", "-z", "--untracked-files=all").hex(),
        "dirty_file_sha256": {
            name: sha(main / name) if (main / name).is_file() else "MISSING"
            for name in paths if name},
    }


def guard(args):
    assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    assert os.environ.get("CODEX_THREAD_ID") == OWNER["thread_id"], "Root executor only"
    # Only these six live top-level lease fields are used; historical work is not an owner source.
    live = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {key: live[key] for key in OWNER} == OWNER
    assert (datetime.fromisoformat(OWNER["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 180
    mode = read(ROOT / "pipeline/execution_mode.json")
    assert mode["mode"] == "foreground" and mode["target_thread_id"] == OWNER["thread_id"]
    for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == OWNER[key]
    frozen = read(HERE / "FROZEN.json")
    assert frozen["owner"] == OWNER and frozen["author_thread_id"] == AUTHOR_THREAD_ID
    assert frozen["scope"] == "REMOTE_CPU_ONLY_SYNTHETIC_EXACT_CORE_CHECK"
    for name, digest in frozen["files"].items():
        path = (HERE / name).resolve()
        assert path.is_relative_to(HERE) and sha(path) == digest, name
    policy = read(HERE / "guard_policy.json")
    assert policy["owner"] == OWNER and policy["remote_stage"] == REMOTE_STAGE
    assert policy["cpu_only"] is True and policy["allowed_gpus"] == []
    assert policy["native_or_dataset_launch_allowed"] is False
    assert policy["ssh_wall_seconds"] == 120 and policy["worker_wall_seconds"] == 95
    for anchor in policy["anchors"].values():
        assert sha(ROOT / anchor["path"]) == anchor["sha256"], anchor["path"]
    assert protected_snapshot() == read(HERE / "protected_before.json"), "Protected main state changed"
    review_path = Path(args.review).resolve()
    assert review_path.is_relative_to(ROOT.resolve()) and sha(review_path) == args.review_sha256
    review = read(review_path)
    assert review["passed"] is True and review["owner"] == OWNER and review["material_concerns"] == []
    assert review["reviewer_thread_id"] not in (OWNER["thread_id"], AUTHOR_THREAD_ID)
    assert review["FROZEN_sha256"] == sha(HERE / "FROZEN.json")
    for field, name in (("worker_sha256", "worker.py"), ("runtime_sha256", "cso_runtime.py"),
                        ("transport_sha256", "run_cpu_once.py")):
        assert review[field] == sha(HERE / name)
    assert review["cpu_only_no_native_launch"] is True
    assert review["source_and_test_protocol_review_passed"] is True
    return frozen


BOOTSTRAP = r"""
import base64,hashlib,json,os,pathlib,signal,socket,subprocess,sys
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
assert sys.dont_write_bytecode and not sys.flags.isolated and 'torch' not in sys.modules
assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
signal.alarm(110)
payload=json.load(sys.stdin)
owner={
 'token':'79656807d78e4cd687c70bdc7df26f5f',
 'thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253',
 'generated_at':'2026-11-10T03:23:05.152371+00:00',
 'deadline_at':'2026-11-10T04:23:05.152371+00:00',
 'context_sha256':'a8ff28e14e85f34d389e9d57fb8a121d432965972597e466fb0410fe52c231a3',
 'pending_sha256':'fbbd449cc56296157ebace8fd2e5acce20f0474cf34aa4614575895cf8ffd0d9'}
assert payload['owner']==owner
assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>180
assert payload['scope']=='REMOTE_CPU_ONLY_SYNTHETIC_EXACT_CORE_CHECK'
assert payload['review_sha256'] and payload['packet_sha256']
root='/data/songcl/Project/Cluster_project/Cluster_nsd_20261107'
actual=subprocess.check_output(['/usr/bin/git','--no-optional-locks','-c','core.fsmonitor=false',
 '-C',root,'rev-parse','--verify','HEAD'],text=True,timeout=10).strip()
assert actual=='d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e'
stage=pathlib.Path('/data/songcl/Project/Cluster_project/pipeline/cso_cpu_79656807')
collect=payload['collect_only']
if collect:assert stage.is_dir(),'Collection cannot stage or launch'
else:stage.mkdir(mode=0o700,exist_ok=False)
assert len(payload['files'])<=32
total=0
for name,item in payload['files'].items():
 path=(stage/name).resolve()
 assert path.is_relative_to(stage.resolve()) and pathlib.Path(name).name==name
 raw=base64.b64decode(item['base64'],validate=True)
 total+=len(raw)
 assert len(raw)<=262144 and total<=1048576
 assert hashlib.sha256(raw).hexdigest()==item['sha256']
 if collect:assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],name
 else:
  with path.open('xb') as stream:stream.write(raw)
assert hashlib.sha256((stage/'FROZEN.json').read_bytes()).hexdigest()==payload['packet_sha256']
result=stage/'core_result.json'
if collect:
 assert result.is_file()
 print(json.dumps({'certainty':'terminal','result':json.loads(result.read_text()),
  'result_sha256':hashlib.sha256(result.read_bytes()).hexdigest(),'collection_only':True}))
 sys.exit(0)
with (stage/'attempt.json').open('x') as stream:
 json.dump({'owner':owner,'scope':payload['scope'],'review_sha256':payload['review_sha256'],
  'packet_sha256':payload['packet_sha256'],'no_replay':True},stream)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',
 CODEX_THREAD_ID=owner['thread_id'],GIT_OPTIONAL_LOCKS='0',OMP_NUM_THREADS='1',
 MKL_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
outpath,errpath=stage/'worker_stdout.partial',stage/'worker_stderr.partial'
with outpath.open('xb') as out,errpath.open('xb') as err:
 process=subprocess.Popen([sys.executable,'-B',str(stage/'worker.py'),'--execute-root',
  '--lease',str(stage/'execution_lease.json')],cwd=str(stage),env=env,stdout=out,stderr=err)
 try:process.wait(timeout=103)
 except subprocess.TimeoutExpired:
  print(json.dumps({'certainty':'uncertain','remote_pid':process.pid,
   'reason':'Preserve stage and attempt; no external signal, replay, or native launch'}));sys.exit(75)
def tail(path,limit=65536):
 with path.open('rb') as stream:
  stream.seek(0,2);stream.seek(max(0,stream.tell()-limit));return stream.read(limit).decode('utf8','replace')
record={'certainty':'terminal','returncode':process.returncode,'remote_pid':process.pid,
 'worker_stdout':tail(outpath),'worker_stderr':tail(errpath),'native_launch':False}
if result.is_file():
 record['result']=json.loads(result.read_text())
 record['result_sha256']=hashlib.sha256(result.read_bytes()).hexdigest()
print(json.dumps(record))
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--collect-only", action="store_true")
    parser.add_argument("--review")
    parser.add_argument("--review-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_TORCH_SSH_GPU_OR_MUTATION"}))
        return
    assert args.review and args.review_sha256
    frozen = guard(args)
    files = {name: (HERE / name).read_bytes() for name in frozen["files"]}
    files["FROZEN.json"] = (HERE / "FROZEN.json").read_bytes()
    assert len(files) <= 32 and sum(map(len, files.values())) <= 1048576
    payload = {
        "owner": OWNER, "scope": frozen["scope"], "collect_only": args.collect_only,
        "review_sha256": args.review_sha256, "packet_sha256": sha(HERE / "FROZEN.json"),
        "files": {name: {"sha256": hashlib.sha256(raw).hexdigest(),
                         "base64": base64.b64encode(raw).decode("ascii")}
                  for name, raw in files.items()},
    }
    execution = HERE.parent / "cso_cpu_execution"
    execution.mkdir(exist_ok=True)
    action = "collect" if args.collect_only else "run"
    request_path, intent_path, actual_path = (execution / (action + "_" + name + ".json")
                                              for name in ("request", "intent", "actual"))
    assert not any(path.exists() for path in (request_path, intent_path, actual_path)), "No replay of existing or uncertain attempt"
    save(request_path, {
        "owner": OWNER, "scope": frozen["scope"], "action": action,
        "transport_sha256": sha(__file__), "packet_sha256": sha(HERE / "FROZEN.json"),
        "review_sha256": args.review_sha256,
        "payload_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
        "remote_stage": REMOTE_STAGE, "maximum_ssh_seconds": 120,
    })
    guard(args)
    save(intent_path, {"owner": OWNER, "request_sha256": sha(request_path),
                       "no_replay": True, "remote_stage": REMOTE_STAGE, "action": action})
    base_conda = "/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh"
    base_sha = "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
    verifier = ("import pathlib,hashlib,os,socket;"
                "assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001;"
                "assert hashlib.sha256(pathlib.Path(" + repr(base_conda) + ").read_bytes()).hexdigest()==" + repr(base_sha))
    activation = ("/usr/bin/python3 -I -B -c " + shlex.quote(verifier)
                  + " && source " + shlex.quote(base_conda)
                  + " && conda activate project_cluster && exec "
                  + shlex.join(["python", "-B", "-c", BOOTSTRAP]))
    remote = ("PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 "
              + shlex.join(["bash", "-lc", activation]))
    command = [
        "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8",
        "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no",
        "songcl@192.168.1.115", remote,
    ]
    record = {
        "owner": OWNER, "certainty": "uncertain", "scope": frozen["scope"],
        "request_sha256": sha(request_path), "intent_sha256": sha(intent_path),
        "packet_sha256": sha(HERE / "FROZEN.json"), "review_sha256": args.review_sha256,
        "ssh_options": {"BatchMode": "yes", "StrictHostKeyChecking": "yes", "ConnectTimeout": 8,
                        "PasswordAuthentication": "no", "KbdInteractiveAuthentication": "no"},
        "native_launch": False,
    }
    try:
        with (execution / (action + "_transport.stdout.partial")).open("x+b") as out, (
                execution / (action + "_transport.stderr.partial")).open("x+b") as err:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err)
            record["local_ssh_pid"] = process.pid
            try:
                process.communicate(json.dumps(payload).encode("utf8"), timeout=120)
            except subprocess.TimeoutExpired:
                record["reason"] = "SSH outcome uncertain; preserve all evidence, no signals or replay"
                save(actual_path, record)
                print(json.dumps({"status": "UNCERTAIN_PRESERVED_NO_REPLAY", "path": str(actual_path)}))
                return
            out.flush()
            err.flush()
            out.seek(0, 2)
            assert out.tell() <= 4194304
            out.seek(0)
            stdout = out.read().decode("utf8", "replace")
            err.seek(0, 2)
            err.seek(max(0, err.tell() - 65536))
            stderr = err.read().decode("utf8", "replace")
        record.update(certainty="terminal", returncode=process.returncode, stdout=stdout, stderr=stderr)
        try:
            record["observation"] = json.loads(stdout)
        except json.JSONDecodeError:
            record["observation"] = None
        record["main_protected_state_unchanged"] = protected_snapshot() == read(HERE / "protected_before.json")
    except BaseException as error:
        record.update(error_type=type(error).__name__, error=str(error))
        save(actual_path, record)
        raise
    save(actual_path, record)
    observation = record.get("observation") or {}
    result = observation.get("result") or {}
    passed = (
        record["returncode"] == 0 and observation.get("certainty") == "terminal"
        and (args.collect_only or observation.get("returncode") == 0)
        and result.get("owner") == OWNER and result.get("execution_completed") is True
        and result.get("passed") is True and record.get("main_protected_state_unchanged") is True)
    print(json.dumps({
        "status": "ACTUAL_CORE_CHECKS_PASSED_REQUIRES_RESULT_REVIEW" if passed else "ACTUAL_OUTCOME_PRESERVED",
        "path": str(actual_path), "sha256": sha(actual_path), "core_checks_passed": passed,
        "native_backward": "NOT_RUN", "resources": "NOT_RUN", "scientific_admission": False,
    }))


if __name__ == "__main__":
    main()
