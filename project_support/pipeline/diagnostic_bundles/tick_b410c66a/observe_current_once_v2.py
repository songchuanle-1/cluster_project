"""Default NOP. Current-owner read-only native-stage/source/lock observation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "b410c66a6c6243e1bbb8f970d1bd8c29"
PROGRAM = r"""
from datetime import datetime,timezone
from pathlib import Path
import fcntl,hashlib,json,os,socket,subprocess,sys
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
payload=json.load(sys.stdin)
root=Path('/data/songcl/Project/Cluster_project/Cluster_nsd_20261107')
stage=Path('/data/songcl/Project/Cluster_project/pipeline/rvec_b410c66a_gpu0')
assert stage.is_dir() and not stage.is_symlink()
manifest_path=stage/'native_manifest.json'
manifest=json.loads(manifest_path.read_text())
assert manifest['owner']==payload['owner']
assert manifest['code_commit']==payload['source_commit']
assert manifest['runtime_code_commit']=='0747f6acec1c61018ec99acf2efa5329c9b3523c'
assert manifest['source_binding_sha256']==hashlib.sha256((stage/'source_binding.json').read_bytes()).hexdigest()
for name,expected in manifest['diagnostic_files'].items():
 p=(stage/name).resolve()
 assert p.is_relative_to(stage.resolve()) and hashlib.sha256(p.read_bytes()).hexdigest()==expected,name
processes=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:
  if proc.stat().st_uid!=1001:continue
  cwd=(proc/'cwd').resolve()
  argv=[a.decode(errors='replace') for a in (proc/'cmdline').read_bytes().split(b'\0') if a]
  if cwd==stage or (cwd==root and 'tools/train.py' in argv) or any(str(stage) in a for a in argv):
   processes.append({'pid':int(proc.name),'cwd':str(cwd),'argv':argv[:12]})
 except (OSError,RuntimeError):pass
locks=[]
for kind,inode in [('training',92537152),('diagnostic',92537153),('exclusive',92537154)]:
 path=Path('/tmp/cluster_project_gpu0_'+kind+'.lock')
 assert path.is_file() and not path.is_symlink()
 descriptor=os.open(path,os.O_RDWR|os.O_NOFOLLOW)
 available=False
 try:
  info=os.fstat(descriptor)
  assert (info.st_dev,info.st_ino)==(66308,inode)
  try:fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB);available=True
  except BlockingIOError:pass
  locks.append({'kind':kind,'device':info.st_dev,'inode':info.st_ino,'original_inode_matches':True,'nonblocking_available':available})
 finally:
  if available:fcntl.flock(descriptor,fcntl.LOCK_UN)
  os.close(descriptor)
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.free,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
assert gpu.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
head=subprocess.check_output(['/usr/bin/git','--no-optional-locks','-C',str(root),'rev-parse','HEAD'],text=True,timeout=10).strip()
assert head==manifest['runtime_code_commit']
results=[]
for name in ('smoke_candidate_result.json','resources_candidate_result.json','resources_champion_result.json'):
 path=stage/name
 if path.is_file():
  raw=path.read_bytes();value=json.loads(raw)
  assert value['owner']==payload['owner'] and value['code_commit']==payload['source_commit']
  results.append({'name':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
   'execution_completed':value.get('execution_completed'),'optimizer_steps':value.get('optimizer_steps'),
   'error_type':value.get('error_type'),'error':value.get('error'),
   'common_init_passed':value.get('original_common_initialization_comparison',{}).get('passed')})
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),
 'runtime_root':str(root),'runtime_HEAD':head,'source_commit':manifest['code_commit'],
 'source_binding_sha256':manifest['source_binding_sha256'],'diagnostic_source_hashes_verified':True,
 'stage_processes_or_native_trainers':processes,'original_locks':locks,'gpu0':gpu,'gpu0_contexts':contexts,
 'results':results,'signals_sent':False,'remote_files_written':False,'GPU_compute_started':False}))
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--label", choices=("smoke", "resources", "final"))
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SSH"}))
        return
    assert args.label and sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    owner_raw = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
    owner = {k: owner_raw[k] for k in ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")}
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 120
    for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert hashlib.sha256((ROOT / "pipeline/headless" / name).read_bytes()).hexdigest() == owner[key]
    source_path = HERE / "rvec_r1_source_prepare/source_version.json"
    version = json.loads(source_path.read_text())
    assert version["owner"] == owner and version["implementation_revision"] == 1
    result_path = HERE / ("post_" + args.label + "_actual_v2.json")
    assert not result_path.exists()
    payload = {"owner": owner, "source_commit": version["source_commit"]}
    record = {"owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
              "source_version_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
              "producer_sha256": hashlib.sha256(PROGRAM.encode()).hexdigest(),
              "wrapper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "certainty": "uncertain"}
    process = subprocess.Popen([
        "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8",
        "songcl@192.168.1.115", "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c " + __import__("shlex").quote(PROGRAM),
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace")
    try:
        stdout, stderr = process.communicate(json.dumps(payload), timeout=40)
    except subprocess.TimeoutExpired:
        record["reason"] = "Read-only outcome uncertain; no signal or replay."
    else:
        record.update(certainty="terminal", returncode=process.returncode, stderr=stderr[:3000])
        try:
            record["observation"] = json.loads(stdout)
        except json.JSONDecodeError:
            record["stdout_excerpt"] = stdout[:2000]
    with result_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    assert record.get("returncode") == 0 and "observation" in record
    print(json.dumps({"path": str(result_path), "sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
                      "observation": record["observation"]}))


if __name__ == "__main__":
    main()
