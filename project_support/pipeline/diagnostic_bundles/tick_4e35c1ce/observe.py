"""Current-lease read-only authorized resource and native progress evidence."""
import json
import re
import shlex
import subprocess
from study import ROOT, OUT, SSH, guard, remote_code, save, now
import yaml

guard(180)
program = r'''
import json,subprocess,fcntl,os,re
from pathlib import Path
from datetime import datetime,timezone
expected={0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',1:'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}
cards={}
for index,uuid in expected.items():
 row=subprocess.check_output(['nvidia-smi','-i',str(index),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 assert [part.strip() for part in row.split(',')][:2]==[str(index),uuid]
 contexts=subprocess.check_output(['nvidia-smi','-i',str(index),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 locks={}
 for kind in ('training','diagnostic','exclusive'):
  with open('/tmp/cluster_project_gpu'+str(index)+'_'+kind+'.lock','a+b') as handle:
   try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True
   except BlockingIOError:locks[kind]=False
 processes=[]
 for line in contexts.splitlines():
  pid=int(line.split(',')[0])
  process=subprocess.run(['ps','-p',str(pid),'-o','pid=,user=,etime=,args='],capture_output=True,text=True,timeout=10)
  processes.append({'pid':pid,'ps':process.stdout.strip(),'ps_returncode':process.returncode})
 cards[str(index)]={'gpu':row,'contexts':contexts,'locks_available':locks,'processes':processes}
log=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1_resume_2546d803_native_serializer.log')
with log.open('rb') as stream:
 stream.seek(max(0,log.stat().st_size-131072));tail=stream.read().decode('utf-8',errors='replace')
steps=re.findall(r'Train\[(\d+)/50\][^\r\n]*?(\d+)/4686',tail)
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'cards':cards,'M204_pid':1085297,'M204_native_steps':steps[-8:],'M204_log_modified_at':datetime.fromtimestamp(log.stat().st_mtime,timezone.utc).isoformat(),'M204_recent_traceback':'Traceback (most recent call last)' in tail[-20000:],'new_training':0,'training_restarted_or_migrated':False}))
'''
server4 = remote_code(program, timeout=100)
cfg = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]["server-3"]
assert cfg["host"] == "192.168.1.120" and cfg["allowed_gpus"] == [1]
code = """import socket,json,subprocess
assert socket.gethostname()=='sysu311-MS-7C59'
p=subprocess.run(['nvidia-smi','-i','1','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
if p.returncode==0:
 assert [x.strip() for x in p.stdout.strip().split(',')][:2]==['1','GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0']
print(json.dumps({'hostname':socket.gethostname(),'gpu_returncode':p.returncode,'gpu_stdout':p.stdout,'gpu_stderr':p.stderr}))
"""
process = subprocess.run(["ssh", *SSH, cfg["user"] + "@" + cfg["host"],
                          shlex.join(["/usr/bin/python3", "-B", "-c", code])],
                         capture_output=True, text=True, timeout=25)
server3 = {"observed_at": now(), "ssh_returncode": process.returncode,
           "stdout": process.stdout[-4000:], "stderr": process.stderr[-4000:]}
path = save("current_resources_and_training.json", {"server4": server4, "server3": server3,
            "scope": "Authorized cards only; read-only occupation/progress, no eviction/reset/restart or scheduler changes."})
print(json.dumps({"evidence": str(path), "server4": server4, "server3": server3}, indent=2))
