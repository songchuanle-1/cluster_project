"""Default NOP. Root-only one current-owner CPU core launch."""
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
    "token": "1aa2d994ab004c93b2ea069c90ef9356",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-10T05:07:20.849412+00:00",
    "deadline_at": "2026-11-10T06:07:20.849412+00:00",
    "context_sha256": "eff960250947a7e168ea5f144742d7a877fd810d38f3f958cca86ab058cc9a93",
    "pending_sha256": "d7e6661624a7282adbfadedf6e35e015206fb97cb7ab4add04a79974af7a6f58"
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def guard(args):
    assert sys.dont_write_bytecode and not sys.flags.optimize and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    assert os.environ.get("CODEX_THREAD_ID") == OWNER["thread_id"]
    live = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {key: live[key] for key in OWNER} == OWNER
    assert (datetime.fromisoformat(OWNER["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 180
    for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == OWNER[key]
    mode = read(ROOT / "pipeline/execution_mode.json")
    assert mode["mode"] == "foreground" and mode["target_thread_id"] == OWNER["thread_id"]
    frozen = read(HERE / "FROZEN.json")
    assert frozen["owner"] == OWNER and all(sha(HERE / n) == h for n, h in frozen["files"].items())
    assert all(sha(ROOT / item["path"]) == item["sha256"] for item in frozen["anchors"])
    review_path = Path(args.review).resolve()
    assert review_path.is_relative_to(HERE.parent) and sha(review_path) == args.review_sha256
    review = read(review_path)
    assert review["owner"] == OWNER and review["passed"] is True and review["material_concerns"] == []
    assert review["reviewer_thread_id"] not in (OWNER["thread_id"], "/root/fresh_ops")
    assert review["FROZEN_sha256"] == sha(HERE / "FROZEN.json")
    assert review["producer_sha256"] == sha(HERE / "sinc_cpu_core.py")
    assert review["transport_sha256"] == sha(__file__)
    assert review["source_sha256"] == sha(HERE / "simplex_incidence.py")


BOOTSTRAP = r"""
import base64,hashlib,json,os,pathlib,socket,subprocess,sys
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
assert sys.dont_write_bytecode and not sys.flags.isolated and not sys.flags.optimize
assert os.environ['CUDA_VISIBLE_DEVICES']=='' and 'torch' not in sys.modules
p=json.load(sys.stdin);owner=p['owner']
assert owner['token']=='1aa2d994ab004c93b2ea069c90ef9356'
assert owner['thread_id']=='01a159c5-29ab-7a22-ba7f-e79174757253'
assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>150
assert sys.executable=='/home/songcl/.conda/envs/project_cluster/bin/python'
assert hashlib.sha256(pathlib.Path(sys.executable).read_bytes()).hexdigest()=='61ae9cdb79cb325d09a903fc05610369ee6488e954b19e165aad9dd6ba0e72f5'
stage=pathlib.Path('/data/songcl/Project/Cluster_project/pipeline/cpu_core_1aa2d994')
assert not stage.exists(),'Existing or uncertain stage: preserve and reconcile, never replay'
stage.mkdir(mode=0o700,exist_ok=False)
for name,item in p['files'].items():
 assert name in ('sinc_cpu_core.py','simplex_incidence.py','request.json')
 raw=base64.b64decode(item['base64'],validate=True)
 assert hashlib.sha256(raw).hexdigest()==item['sha256']
 with (stage/name).open('xb') as stream:stream.write(raw)
outpath,errpath=stage/'stdout.partial',stage/'stderr.partial'
out,err=outpath.open('xb'),errpath.open('xb')
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',TOKENIZERS_PARALLELISM='false')
process=subprocess.Popen([sys.executable,'-B',str(stage/'sinc_cpu_core.py'),'--execute-root'],cwd=stage,env=env,stdout=out,stderr=err)
try:
 process.wait(timeout=110)
 out.flush();err.flush()
 record={'certainty':'terminal','returncode':process.returncode,'remote_pid':process.pid}
 if (stage/'result.json').is_file():
  raw=(stage/'result.json').read_bytes();assert len(raw)<=65536
  record.update(result=json.loads(raw),result_sha256=hashlib.sha256(raw).hexdigest())
 with errpath.open('rb') as stream:
  stream.seek(0,2);stream.seek(max(0,stream.tell()-4096));record['stderr_tail']=stream.read(4096).decode('utf8','replace')
 print(json.dumps(record),flush=True)
except subprocess.TimeoutExpired:
 print(json.dumps({'certainty':'uncertain','remote_pid':process.pid,'reason':'SOFT_TIMEOUT_PRESERVE_NO_SIGNAL_OR_RETRY','remote_stage':str(stage)}),flush=True)
 sys.exit(75)
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--review", type=Path)
    parser.add_argument("--review-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SSH_TORCH_OR_MUTATION"}))
        return
    assert args.review and args.review_sha256
    guard(args)
    intent, actual = HERE / "cpu.intent.json", HERE / "cpu.actual.json"
    assert not intent.exists() and not actual.exists(), "Preserve existing attempt; never replay"
    request = {"owner": OWNER, "GPU_use": False, "producer_sha256": sha(HERE / "sinc_cpu_core.py"),
               "source_sha256": sha(HERE / "simplex_incidence.py"), "native_TRAIN": "NOT_RUN", "resources": "NOT_RUN"}
    request_raw = (json.dumps(request, sort_keys=True) + "\n").encode()
    files = {name: (HERE / name).read_bytes() for name in ("sinc_cpu_core.py", "simplex_incidence.py")}
    files["request.json"] = request_raw
    payload = {"owner": OWNER, "files": {name: {"sha256": hashlib.sha256(raw).hexdigest(),
               "base64": base64.b64encode(raw).decode()} for name, raw in files.items()}}
    base = "/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh"
    verifier = ("import pathlib,hashlib,os,socket;assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001;"
                "assert hashlib.sha256(pathlib.Path(" + repr(base) + ").read_bytes()).hexdigest()=='6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0'")
    activation = ("/usr/bin/python3 -I -B -c " + shlex.quote(verifier) + " && source " + shlex.quote(base)
                  + " && conda activate project_cluster && exec " + shlex.join(["python", "-B", "-c", BOOTSTRAP]))
    command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8",
               "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no",
               "songcl@192.168.1.115", "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 " + shlex.join(["bash", "-lc", activation])]
    save(intent, {"owner": OWNER, "no_replay": True, "review_sha256": args.review_sha256,
                  "producer_sha256": request["producer_sha256"], "source_sha256": request["source_sha256"],
                  "GPU_use": False, "remote_stage": "/data/songcl/Project/Cluster_project/pipeline/cpu_core_1aa2d994"})
    record = {"owner": OWNER, "certainty": "uncertain", "signals_sent": False, "automatic_retry": False,
              "GPU_use": False, "native_TRAIN": "NOT_RUN", "resources": "NOT_RUN", "intent_sha256": sha(intent)}
    outpath, errpath = HERE / "transport.stdout.partial", HERE / "transport.stderr.partial"
    out, err = outpath.open("x+b"), errpath.open("x+b")
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err)
        record["local_ssh_pid"] = process.pid
        process.communicate(json.dumps(payload).encode(), timeout=120)
        out.flush()
        err.flush()
        assert outpath.stat().st_size <= 131072
        record.update(certainty="terminal", returncode=process.returncode)
        record["stdout"] = outpath.read_text(encoding="utf-8", errors="replace")
        with errpath.open("rb") as stream:
            stream.seek(0, 2)
            stream.seek(max(0, stream.tell() - 4096))
            record["stderr_tail"] = stream.read(4096).decode("utf-8", "replace")
        try:
            record["observation"] = json.loads(record["stdout"])
        except json.JSONDecodeError:
            record["observation"] = None
    except BaseException as error:
        record.update(error_type=type(error).__name__, error=str(error)[:1000],
                      reason="PRESERVE_UNKNOWN_OUTCOME_NO_SIGNAL_OR_RETRY")
        save(actual, record)
        raise
    finally:
        out.close()
        err.close()
    save(actual, record)
    print(json.dumps({"path": str(actual), "sha256": sha(actual),
                      "status": "ACTUAL_CPU_OUTCOME_CAPTURED_REQUIRES_REVIEW", "GPU_use": False}))


if __name__ == "__main__":
    main()
