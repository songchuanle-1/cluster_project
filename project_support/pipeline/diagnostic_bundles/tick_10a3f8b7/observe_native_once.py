"""Read-only current-owner native process and authorized GPU0 observation."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "10a3f8b7d1bc4c5083b9b476c4d6fb94"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
PROGRAM = r"""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,os,socket,subprocess
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==1001
root=Path('/data/songcl/Project/Cluster_project/Cluster_nsd_20261107')
env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
head=subprocess.check_output(['/usr/bin/git','--no-optional-locks','-c','core.fsmonitor=false','-C',str(root),'rev-parse','HEAD'],text=True,env=env,timeout=10).strip()
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.free,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
assert gpu.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
trainers=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  if proc.stat().st_uid!=1001 or (proc/'cwd').resolve()!=root:continue
  args=[v.decode(errors='replace') for v in (proc/'cmdline').read_bytes().split(b'\0') if v]
  if 'tools/train.py' in args:
   trainers.append({'pid':int(proc.name),'argv':args,'state':(proc/'stat').read_text().split(')')[-1].split()[0]})
 except (OSError,RuntimeError):pass
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'runtime_root':str(root.resolve()),'runtime_HEAD':head,'gpu0':gpu,'same_root_native_trainers':trainers,'GPU_compute_started':False,'signals_sent':False,'remote_files_written':False}))
"""


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
assert os.environ.get("CODEX_THREAD_ID") == THREAD
owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text(encoding="utf-8"))
assert owner["token"] == TOKEN and owner["thread_id"] == THREAD
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
for name, key in [
    (".tick_context.json", "context_sha256"),
    (".tick_context_state.next.json", "pending_sha256"),
]:
    assert digest(ROOT / "pipeline/headless" / name) == owner[key]
binding = {
    key: owner[key] for key in [
        "token", "thread_id", "generated_at", "deadline_at",
        "context_sha256", "pending_sha256",
    ]
}
result_path = HERE / "native_current_observation.json"
assert not result_path.exists()
save(HERE / "native_observation_intent.json", {
    "recorded_at": datetime.now(timezone.utc).isoformat(), "owner": binding,
    "producer_sha256": hashlib.sha256(PROGRAM.encode()).hexdigest(),
    "transport_sha256": digest(Path(__file__)), "read_only": True, "no_replay": True,
})
process = subprocess.Popen([
    "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
    "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
    "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -",
], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, encoding="utf-8", errors="replace")
record = {
    "recorded_at": datetime.now(timezone.utc).isoformat(), "owner": binding,
    "producer_sha256": hashlib.sha256(PROGRAM.encode()).hexdigest(),
    "certainty": "uncertain", "local_ssh_pid": process.pid,
}
try:
    stdout, stderr = process.communicate(PROGRAM, timeout=35)
except subprocess.TimeoutExpired:
    record["reason"] = "Read-only observation uncertain; no signals or replay."
    save(result_path, record)
    raise SystemExit(75)
record.update(certainty="terminal", returncode=process.returncode, stderr=stderr)
try:
    record["observation"] = json.loads(stdout)
except json.JSONDecodeError:
    record["stdout"] = stdout[:3000]
save(result_path, record)
assert record["returncode"] == 0 and "observation" in record
print(json.dumps({
    "path": str(result_path), "sha256": digest(result_path),
    "observation": record["observation"],
}))
