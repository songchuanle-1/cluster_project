"""Run the reviewed isolated CPU proof once; production remains disabled."""
from datetime import datetime, timezone
from pathlib import Path
import base64
import hashlib
import json
import os
import shlex
import subprocess

ROOT=Path("D:/project/cluster_project");H=Path(__file__).resolve().parent
V=H/"psc_path_lock_prepare/v2"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
o=read(ROOT/"pipeline/headless/.foreground.lockdir/owner.json")
assert o["token"]=="0bb874337dde412e98bbbaac369f3370" and o["thread_id"]==os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc)<datetime.fromisoformat(o["deadline_at"])
for name,key in ((".tick_context.json","context_sha256"),(".tick_context_state.next.json","pending_sha256")):
    assert sha(ROOT/"pipeline/headless"/name)==o[key]
review=H/"psc_path_lock_independent_review.json"
assert sha(review)=="b2b40402ca7c2f71ea9a78b35e11b7c09afd33742261c93ade47907dcae9ebbf"
assert read(review).get("passed") is True
request=read(V/"proof_request.draft.json")
request["owner"]={k:o[k] for k in ("token","thread_id","generated_at","deadline_at","context_sha256","pending_sha256")}
request["execution_authorized"]=True
assert request["production_activation_authorized"] is False
local=H/"psc_cpu_path_proof_request.json";result_path=H/"psc_cpu_path_proof_actual.json"
assert not local.exists() and not result_path.exists(),"Existing proof must reconcile, never replay"
with local.open("x",encoding="utf8",newline="\n") as f:json.dump(request,f,indent=2);f.write("\n")
for name,digest in request["files"].items():assert sha(V/name)==digest
packet={"stage":request["prospective_stage"],"request_bytes":base64.b64encode(local.read_bytes()).decode(),
        "request_sha256":sha(local),"files":{name:base64.b64encode((V/name).read_bytes()).decode() for name in request["files"]}}
program=r'''
from pathlib import Path
from datetime import datetime,timezone
import socket,json,sys,base64,hashlib,subprocess,os
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==1001
packet=json.load(sys.stdin);stage=Path(packet['stage'])
assert stage==Path('/data/songcl/Project/Cluster_project/pipeline/runtime/psc_path_cpu_0bb87433')
raw=base64.b64decode(packet['request_bytes']);assert hashlib.sha256(raw).hexdigest()==packet['request_sha256']
request=json.loads(raw);assert request['production_activation_authorized'] is False
assert datetime.now(timezone.utc)<datetime.fromisoformat(request['owner']['deadline_at'])
assert not stage.exists(),'Existing proof stage must reconcile; never replay'
for name,encoded in packet['files'].items():
 assert name in ('cpu_proof_runner.py','entry_factory.py','lock_core.py')
 assert hashlib.sha256(base64.b64decode(encoded)).hexdigest()==request['files'][name]
stage.parent.mkdir(parents=True,exist_ok=True);stage.mkdir(mode=0o700)
for name,encoded in packet['files'].items():
 with (stage/name).open('xb') as f:f.write(base64.b64decode(encoded))
with (stage/'proof_request.json').open('xb') as f:f.write(raw)
environment=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');environment.pop('CUDA_VISIBLE_DEVICES',None)
command=['/usr/bin/python3','-I','-B',str(stage/'cpu_proof_runner.py'),'--request',str(stage/'proof_request.json'),'--request-sha256',packet['request_sha256']]
with (stage/'runner_stdout.log').open('xb') as out,(stage/'runner_stderr.log').open('xb') as err:
 completed=subprocess.run(command,env=environment,stdout=out,stderr=err,timeout=160)
result=None
if (stage/'cpu_proof_result.json').exists():result=json.loads((stage/'cpu_proof_result.json').read_text())
print(json.dumps({'stage':str(stage),'returncode':completed.returncode,'result':result,
 'stdout_tail':(stage/'runner_stdout.log').read_text(errors='replace')[-4000:],
 'stderr_tail':(stage/'runner_stderr.log').read_text(errors='replace')[-2000:],
 'production_activation':False,'GPU_used':False,'replayed':False}))
'''
command=["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=8",
         "songcl@192.168.1.115","env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -B -c "+shlex.quote(program)]
completed=subprocess.run(command,input=json.dumps(packet),capture_output=True,text=True,encoding="utf8",timeout=180)
record={"recorded_at":datetime.now(timezone.utc).isoformat(),"owner":request["owner"],
        "review_sha256":sha(review),"request_sha256":sha(local),"command":command,
        "returncode":completed.returncode,"stderr":completed.stderr,
        "observation":json.loads(completed.stdout) if completed.returncode==0 else None}
with result_path.open("x",encoding="utf8") as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write("\n")
assert completed.returncode==0,completed.stderr[-1800:]
observation=record["observation"]
print(json.dumps({"returncode":observation["returncode"],"stage":observation["stage"],
                  "result_status":observation["result"].get("status") if isinstance(observation["result"],dict) else None,
                  "stderr_tail":observation["stderr_tail"],"evidence_sha256":sha(result_path),
                  "production_activation":False,"GPU_used":False}))
assert observation["returncode"]==0,"Preserve exact failed proof; do not replay"
