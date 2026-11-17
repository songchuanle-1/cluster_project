"""Current-owner read-only GPU0 and runtime observation; no launch."""
import argparse
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
KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
TOKEN = "79656807d78e4cd687c70bdc7df26f5f"
BODY = r"""
import hashlib,json,os,pathlib,socket,subprocess
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
root=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_nsd_20261107')
def query(argv):
 r=subprocess.run(argv,capture_output=True,text=True,timeout=20)
 assert len(r.stdout.encode())<131072 and len(r.stderr.encode())<8192
 return {'argv':argv,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
result={'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'uid':os.getuid(),'runtime_root':str(root)}
result['head']=query(['/usr/bin/git','--no-optional-locks','-c','core.fsmonitor=false','-C',str(root),'rev-parse','HEAD'])
assert result['head']['returncode']==0 and result['head']['stdout'].strip()=='d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e'
result['inventory']=query(['/usr/bin/nvidia-smi','-i','0','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'])
result['compute']=query(['/usr/bin/nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'])
assert result['inventory']['returncode']==result['compute']['returncode']==0
fields=[v.strip() for v in result['inventory']['stdout'].strip().split(',')]
assert fields[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'] and len(fields)==6
total,used,free,util=map(int,fields[2:])
result.update(physical_gpu=0,gpu_uuid=fields[1],memory_total_mib=total,memory_used_mib=used,memory_free_mib=free,utilization_percent=util,minimum_free_mib=20000,launch_memory_satisfied=free>=20000)
result['lock_identities']=[]
for kind,ino in [('training',92537152),('diagnostic',92537153),('exclusive',92537154)]:
 p=pathlib.Path('/tmp/cluster_project_gpu0_'+kind+'.lock'); s=p.lstat()
 assert (s.st_dev,s.st_ino)==(66308,ino)
 result['lock_identities'].append({'kind':kind,'device':s.st_dev,'inode':s.st_ino,'stat_only':True})
result['project_trainers']=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  if p.stat().st_uid==1001 and (p/'cwd').resolve()==root:
   argv=(p/'cmdline').read_bytes().split(b'\0')
   if b'tools/train.py' in argv:result['project_trainers'].append({'pid':int(p.name),'native_entry_observed':True})
 except (OSError,RuntimeError):pass
result['producer_pins']=[]
for path,expected in [
('/data/songcl/Project/Cluster_project/pipeline/runtime/rvec_path_prepare_21ebd237/entry_factory.py','0a8ed26bd62327314de89f4228b53c8c633fdd73e4e1867d674df94b24d073dd'),
('/data/songcl/Project/Cluster_project/pipeline/runtime/rvec_path_prod_21ebd237/bin/python','62ae097cd67499ab86941c79c4eb8526173f4a694ffb6e41406f42355b37a64e'),
('/data/songcl/Project/Cluster_project/pipeline/runtime/rvec_path_prod_21ebd237/binding.json','beb2c6497cc5fa5fdf0bb33e0d1d7cff2060a9a0315c919f45ef2124e6c07e29')]:
 h=hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest();assert h==expected
 result['producer_pins'].append({'path':path,'sha256':h,'read_only_not_executed':True})
result.update(read_only=True,torch_imported=False,gpu_context_created=False,signals_or_job_control=False,GPU1_accessed=False)
print(json.dumps(result))
"""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--label", default="initial")
    args = parser.parse_args()
    if not args.execute_root:
        print("DEFAULT_NOP")
        return
    assert args.label.replace("_", "").isalnum()
    assert sys.dont_write_bytecode and os.environ["GIT_OPTIONAL_LOCKS"] == "0"
    live = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text(encoding="utf-8-sig"))
    owner = {key: live[key] for key in KEYS}
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[key]
    path = HERE / ("gpu0_" + args.label + ".actual.json")
    assert not path.exists()
    command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
               "-o", "ConnectTimeout=8", "-o", "PasswordAuthentication=no",
               "-o", "KbdInteractiveAuthentication=no", "songcl@192.168.1.115",
               "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -B -c " + shlex.quote(BODY)]
    actual = {"owner": owner, "started_at": datetime.now(timezone.utc).isoformat(),
              "body_sha256": hashlib.sha256(BODY.encode()).hexdigest(),
              "command": command, "read_only": True}
    completed = subprocess.run(command, capture_output=True, text=True, timeout=90)
    actual.update(returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)
    actual["observation"] = json.loads(completed.stdout) if completed.returncode == 0 else None
    with path.open("x", encoding="utf-8") as stream:
        json.dump(actual, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    assert completed.returncode == 0
    observation = actual["observation"]
    print(json.dumps({"path": str(path), "sha256": sha(path),
                      "free_mib": observation["memory_free_mib"],
                      "launch_memory_satisfied": observation["launch_memory_satisfied"],
                      "project_trainers": observation["project_trainers"]}))


if __name__ == "__main__":
    main()
