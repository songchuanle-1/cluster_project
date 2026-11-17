"""Read live admitted training, native progress and lifetime lock ownership."""
from datetime import datetime,timezone
import json
from ops import OUT,ROOT,NAME,guard,save,remote,tick
import closure
import yaml

guard();task=tick.load(OUT/"dispatch_result.json")["task"]
assert task["launch_verified"] and task["id"]=="M203-FLE"
source=tick.load(OUT/"final_source.json")
old=tick.load(OUT/"manifest.json")
program=r'''
import datetime,hashlib,json,pathlib,socket,subprocess
assert socket.gethostname()=="dl04-MS-7E06"
root=pathlib.Path("/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b")
pid=PID
assert (pathlib.Path('/proc')/str(pid)).is_dir()
cmd=(pathlib.Path('/proc')/str(pid)/'cmdline').read_bytes().split(b'\0')
assert b'tools/train.py' in cmd and CONFIG.encode() in cmd
sources={name:hashlib.sha256((root/'framework/model/Quard_model'/NAME/name).read_bytes()).hexdigest() for name in HASHES}
assert sources==HASHES
for name,expected in OLD.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],universal_newlines=True,timeout=10).strip()
assert [x.strip() for x in row.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],universal_newlines=True,timeout=10).strip()
lock_rows=pathlib.Path('/proc/locks').read_text().splitlines();locks={}
for kind in ('training','diagnostic','exclusive'):
    path=pathlib.Path('/tmp/cluster_project_gpu0_'+kind+'.lock');inode=str(path.stat().st_ino)
    owners=[int(line.split()[4]) for line in lock_rows if len(line.split())>=6 and line.split()[1]=='FLOCK' and line.split()[5].rsplit(':',1)[-1]==inode]
    locks[kind]=owners;assert owners==[pid]
text=pathlib.Path(LOG).read_bytes()[-24000:].decode('utf-8',errors='replace')
assert 'Traceback' not in text and 'CUDA out of memory' not in text and 'RuntimeError' not in text
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':pid,'gpu':row,'contexts':contexts,'lock_owner_pids':locks,'native_log_tail':text,'source_hashes':sources,'HDS_and_shared_sources_unchanged':True,'remote_config':(root/CONFIG).read_text(),'remote_HEAD':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],universal_newlines=True).strip(),'reset_signal_lock_deletion':False}))
'''
prefix="PID="+repr(task["pid"])+"\nCONFIG="+repr(task["config"])+"\nNAME="+repr(NAME)+"\nHASHES="+repr(source["source_hashes"])+"\nOLD="+repr(old["hds_source_hashes"])+"\nLOG="+repr(task["log"])+"\n"
live=remote(prefix+program,90)
assert live["remote_HEAD"]==task["code_commit"]
actual=yaml.safe_load(live.pop("remote_config"))
local=yaml.safe_load((ROOT/"Cluster"/task["config"]).read_text(encoding="utf-8"))
local["work_dir"]="/data/songcl/Project/Cluster_project/Cluster_checkpoints"
assert actual==local,"Deployment changed more than candidate work_dir mapping"
steps=closure.steps(live.pop("native_log_tail"))
assert len(set(steps))>=2 and max(step for epoch,step in steps)>0
live.update(native_steps=steps,latest_native_step=max(steps),candidate_config_only_authorized_path_adaptation=True,
    training_peak_is_lower_bound_observation_only=True,full_training_peak=None,validation_metric=None)
save("live_training_postcheck.json",live)
program3=r'''
import datetime,json,socket,subprocess
assert socket.gethostname()=="sysu311-MS-7C59"
row=subprocess.check_output(['nvidia-smi','-i','1','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],universal_newlines=True,timeout=10).strip()
assert [x.strip() for x in row.split(',')][:2]==['1','GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0']
contexts=subprocess.check_output(['nvidia-smi','-i','1','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],universal_newlines=True,timeout=10).strip()
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'gpu':row,'contexts':contexts,'read_only':True,'cuda_initialized':False,'foreign_jobs_preserved':True}))
'''
from ops import run
import shlex
p=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','songcl@192.168.1.120',shlex.join(['/usr/bin/python3','-B','-c',program3])],45)
assert p.returncode==0,p.stderr
other=json.loads(p.stdout);save("server3_live_observation.json",other)
print(json.dumps({'observed_at':live['observed_at'],'experiment':'M203-FLE','latest_native_step':live['latest_native_step'],'gpu':live['gpu'],'locks':live['lock_owner_pids'],'server3_gpu1':other['gpu'],'validation_metric':None},indent=2))
