"""Start the reviewed CPU guardian once; never launch or signal a trainer."""
from datetime import datetime, timezone
from pathlib import Path
import base64
import hashlib
import json
import os
import shlex
import subprocess

ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
HERE = Path(__file__).resolve().parent
TOKEN = "fd2aae2a3cd648c3a18c0119362783fe"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
RUNTIME = "/data/songcl/Project/Cluster_project/Cluster_mic_20261105"
STAGE = "/data/songcl/Project/Cluster_project/pipeline/cooperative_guards/m229_fd2aae2a"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guard():
    owner = read(PIPE / "headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"] == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(PIPE / "headless/.tick_context.json") == owner["context_sha256"]
    assert sha(PIPE / "headless/.tick_context_state.next.json") == owner["pending_sha256"]
    return {k: owner[k] for k in (
        "token", "thread_id", "generated_at", "deadline_at",
        "context_sha256", "pending_sha256",
    )}


owner = guard()
request = HERE / "mic_guardian_start_request.json"
result_path = HERE / "mic_guardian_start_result.json"
assert not request.exists() and not result_path.exists(), "Reconcile any existing CPU start; never replay"
script_path = HERE / "mic_cooperative_guardian.py"
assert sha(script_path) == "24d90a20cb27538297a3904272a28f6fb0383ce70c94ff9741de0590ffa4ecf7"
observation = read(HERE / "mic_live_observation_2.json")["observation"]
assert observation["pid"] == 2881795 and observation["starttime"] == "152216088"
assert not observation["fatal_error_markers"]
task = next(t for t in read(PIPE / "queue.json")["gpu_queues"]["server-4"] if t["id"] == "M229-MIC")
assert task["pid"] == 2881795 and task["launch_verified"] is True and task["status"] == "running"
assert task["log"] == observation["log"] and task["code_commit"] == observation["runtime_source_commit"]
assert sha(PIPE / "authorizations/server4_gpu0_overlay_20261104.json") == "783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88"
assert sha(ROOT / "SERVERS.yaml") == "84730b8f91db3022d2e1819362d803b20293ea6224cfa9d607b8d4e45e8f43c0"
binding = {
    "owner": owner, "project": "cluster_project", "experiment_id": "M229-MIC",
    "operation": "postlaunch_existing_training_cooperative_lock_protection",
    "runtime_root": RUNTIME,
    "source_commit": observation["runtime_source_commit"],
    "physical_gpu": 0, "gpu_uuid": observation["gpu_uuid"],
    "trainer_pid": observation["pid"], "trainer_starttime": observation["starttime"],
    "trainer_argv": observation["argv"], "trainer_log": observation["log"],
    "guardian_script_sha256": sha(script_path),
    "resource_authorization_sha256": sha(PIPE / "authorizations/server4_gpu0_overlay_20261104.json"),
    "servers_sha256": sha(ROOT / "SERVERS.yaml"),
    "admission_receipt_sha256": sha(PIPE / "admissions/M229-MIC.json"),
    "lifetime": "Only until the exact already-running trainer exits; no research, scheduling, GPU use, restart or signals.",
    "prelaunch_lock_check_proven": False,
    "missing_lock_observation_at": observation["observed_at"],
}
payload = {
    "binding": binding, "stage": STAGE,
    "script_base64": base64.b64encode(script_path.read_bytes()).decode("ascii"),
}
remote_program = r'''
import base64,hashlib,json,os,pathlib,socket,subprocess,sys,time
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06'
packet=json.load(sys.stdin);b=packet['binding'];stage=pathlib.Path(packet['stage'])
assert str(stage)=='/data/songcl/Project/Cluster_project/pipeline/cooperative_guards/m229_fd2aae2a'
assert datetime.now(timezone.utc)<datetime.fromisoformat(b['owner']['deadline_at'])
proc=pathlib.Path('/proc')/str(b['trainer_pid'])
def start(pid):
 t=(pathlib.Path('/proc')/str(pid)/'stat').read_text()
 return t[t.rfind(')')+2:].split()[19]
def trainer():
 assert start(b['trainer_pid'])==b['trainer_starttime']
 assert proc.stat().st_uid==os.getuid()
 assert os.readlink(proc/'cwd')==b['runtime_root']
 assert os.readlink(proc/'fd/1')==b['trainer_log']
 assert [x.decode() for x in (proc/'cmdline').read_bytes().split(b'\0') if x]==b['trainer_argv']
trainer()
assert subprocess.check_output(['git','-C',b['runtime_root'],'rev-parse','HEAD'],text=True).strip()==b['source_commit']
script=base64.b64decode(packet['script_base64'])
assert hashlib.sha256(script).hexdigest()==b['guardian_script_sha256']
assert not stage.exists(),'Existing stage/start must reconcile; never replay'
stage.parent.mkdir(parents=True,exist_ok=True);stage.mkdir()
code=stage/'guardian.py';binding_path=stage/'binding.json'
with code.open('xb') as f:f.write(script)
b['trainer_uid']=os.getuid();b['stage_created_at']=datetime.now(timezone.utc).isoformat()
with binding_path.open('x') as f:json.dump(b,f,indent=2);f.write('\n')
trainer()
assert datetime.now(timezone.utc)<datetime.fromisoformat(b['owner']['deadline_at'])
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
with (stage/'guardian_stdout.log').open('ab',buffering=0) as out:
 child=subprocess.Popen(['/usr/bin/python3','-B',str(code),str(binding_path)],cwd=stage,env=env,
   stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
spawn={'guardian_pid':child.pid,'guardian_starttime':start(child.pid),'recorded_at':datetime.now(timezone.utc).isoformat()}
with (stage/'spawn.json').open('x') as f:json.dump(spawn,f,indent=2);f.write('\n')
state=None
for _ in range(50):
 if (stage/'state.json').exists():
  state=json.loads((stage/'state.json').read_text());break
 if child.poll() is not None:break
 time.sleep(.2)
if state is None or state.get('status')!='HOLDING':
 print(json.dumps({'stage':str(stage),'spawn':spawn,'binding':b,'state':state,
  'stderr_tail':(stage/'guardian_stdout.log').read_text(errors='replace')[-2000:],
  'requires_reconciliation':True}));raise SystemExit(2)
assert state['guardian_pid']==spawn['guardian_pid'] and state['guardian_starttime']==spawn['guardian_starttime']
assert child.poll() is None
assert start(child.pid)==spawn['guardian_starttime'];trainer()
assert len(state['locks'])==3 and state['trainer_pid']==b['trainer_pid']
table=pathlib.Path('/proc/locks').read_text().splitlines()
live_locks=[]
for lock in state['locks']:
 info=pathlib.Path(lock['path']).stat()
 assert info.st_ino==lock['inode']
 key='%02x:%02x:%d'%(lock['device_major'],lock['device_minor'],lock['inode'])
 rows=[line for line in table if len(line.split())>5 and line.split()[5]==key]
 assert len(rows)==1
 fields=rows[0].split()
 assert fields[1]=='FLOCK' and fields[3]=='WRITE' and int(fields[4])==child.pid
 live_locks.append(rows[0])
assert child.poll() is None
print(json.dumps({'stage':str(stage),'spawn':spawn,'binding':b,'state':state,
 'live_lock_table':live_locks,'live_three_locks_confirmed':True,
 'trainer_unchanged':True,'CPU_guardian_only':True,'training_launches':0,'signals_sent':False}))
'''
command = [
    "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
    "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
    "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c " + shlex.quote(remote_program),
]
with request.open("x", encoding="utf-8") as stream:
    json.dump({
        "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Once-only CPU guardian for existing trainer, no training Popen or GPU use.",
        "guardian_script_sha256": sha(script_path), "binding": binding,
        "actual_command": command,
    }, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
guard()
completed = subprocess.run(
    command, input=json.dumps(payload), capture_output=True,
    encoding="utf-8", errors="replace", timeout=40,
)
with result_path.open("x", encoding="utf-8") as stream:
    json.dump({
        "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "returncode": completed.returncode, "stdout": completed.stdout,
        "stderr": completed.stderr, "actual_command": command,
        "request_sha256": sha(request), "guardian_script_sha256": sha(script_path),
    }, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
assert completed.returncode == 0, "Preserve exact CPU start result and reconcile; no repeat: " + completed.stderr[-1500:]
result = json.loads(completed.stdout)
assert result["state"]["status"] == "HOLDING" and result["trainer_unchanged"] is True
print(json.dumps({
    "CPU_guardian_pid": result["spawn"]["guardian_pid"],
    "guardian_starttime": result["spawn"]["guardian_starttime"],
    "trainer_pid": result["state"]["trainer_pid"], "three_locks": "HOLDING",
    "postlaunch_correction": True, "training_restarted": False,
    "evidence": {"path": result_path.relative_to(ROOT).as_posix(), "sha256": sha(result_path)},
}))
