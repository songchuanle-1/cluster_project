"""Audit only the exact current M202 run and its authorized diagnostic slots."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

os.environ.update(PROJECT_ROOT="D:/project", PYTHONDONTWRITEBYTECODE="1")
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

ROOT = Path("D:/project/cluster_project")
OUT = Path(__file__).resolve().parent
TOKEN = "21500d1a24a149c4bc63ba867beea115"
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"


def guard():
    owner = tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    return owner


def save(name, value):
    guard()
    tick.save(OUT / name, value)


def remote(host, command, timeout=90):
    response = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
                               "-o", "ConnectTimeout=10", "songcl@" + host, command],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    assert response.returncode == 0, response.stderr
    return response.stdout


if __name__ == "__main__":
    guard()
    exp = tick.load(ROOT / "pipeline/experiments/M202-HDS.json")
    assert exp["pid"] == 1592337 and exp["server"] == "server-4" and str(exp["gpu"]) == "0"
    previous = tick.load(ROOT / "pipeline/diagnostic_bundles/evidence_producer_86290288/resources_d7dee0a1.json")
    scalar_log = previous["server-4"]["samples"][-1]["current_scalar_logs"][0]["path"]
    frozen = tick.load(ROOT / "pipeline/diagnostic_bundles/m202_recovery_fded20f5/failure_snapshot.json")
    constants = {"LOG": exp["log"], "SCALAR_LOG": scalar_log, "PID": exp["pid"], "CONFIG": exp["config"],
                 "EXPECTED_HASHES": frozen["source_hashes"], "BASE": BASE,
                 "REMOTE_ROOT": "/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b"}
    program = "\n".join(name + "=" + repr(value) for name, value in constants.items()) + "\n" + r'''
import csv,datetime,fcntl,hashlib,json,pathlib,re,socket,subprocess
assert socket.gethostname()=='dl04-MS-7E06'
root=pathlib.Path(REMOTE_ROOT)
def sha(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open('rb') as handle:
        for block in iter(lambda:handle.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
def gpu():
    row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],universal_newlines=True,timeout=10).strip()
    cells=[value.strip() for value in row.split(',')]
    assert cells[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
    processes=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],universal_newlines=True,timeout=10).strip()
    return {'raw':row,'compute_contexts':processes,'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
exact=[]
for proc in pathlib.Path('/proc').iterdir():
    if not proc.name.isdecimal():continue
    try:args=(proc/'cmdline').read_bytes().split(b'\0')
    except OSError:continue
    if b'tools/train.py' in args and CONFIG.encode() in args:exact.append(int(proc.name))
path=pathlib.Path(LOG)
with path.open('rb') as handle:
    head=handle.read(16384)
    handle.seek(max(0,path.stat().st_size-131072))
    tail=handle.read()
text=tail.decode('utf-8',errors='replace')
native=pathlib.Path(SCALAR_LOG)
assert native.stat().st_size<64*1024*1024
value=native.read_text(errors='replace')
pattern=r'Early stopping at epoch (\d+): no improvement for (\d+) epochs'
stop=re.findall(pattern,value+'\n'+text)
stops=[line for line in value.splitlines() if re.search(pattern,line)]
metrics=[float(x) for x in re.findall(r'(?<![A-Za-z])mIoU\s*:\s*([0-9.eE+-]+)',value)]
counts=[int(x) for x in re.findall(r'Evaluate referring segmentation:\s*(\d+)',value)]
locks={}
for suffix in ('training','diagnostic','exclusive'):
    name='/tmp/cluster_project_gpu0_'+suffix+'.lock'
    with open(name,'rb') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:locks[name]='held'
        else:
            locks[name]='acquired_and_released'
            fcntl.flock(handle,fcntl.LOCK_UN)
ckpts={}
for name in ('best.pth','last.pth'):
    p=native.parent/name
    ckpts[name]={'path':str(p),'exists':p.is_file()}
    if p.is_file():ckpts[name].update(bytes=p.stat().st_size,mtime=p.stat().st_mtime)
hashes={name:sha(root/name) for name in EXPECTED_HASHES}
baseline_config='configs/Quard/ctf_hcg_csort/'+BASE+'.yaml'
producer_sources=['framework/model/Quard_model/'+BASE+'/network.py','framework/dataset/scannetv2.py','framework/dataset/__init__.py',baseline_config,'tools/train.py']
trusted=root.parent/'pipeline/hds_server4_3c22e34d/frozen_m95.pth'
result={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':socket.gethostname(),
 'pid_exists':pathlib.Path('/proc',str(PID)).exists(),'exact_training_pids':exact,
 'stdout':{'path':LOG,'bytes':path.stat().st_size,'tail_sha256':hashlib.sha256(tail).hexdigest(),
 'tail_crash_markers':[word for word in ('Traceback','CUDA out of memory','TypeError:','RuntimeError:') if word in text]},
 'native_scalar_log':{'path':str(native),'sha256':sha(native),'bytes':native.stat().st_size,'miou':metrics,'expression_counts':counts},
 'explicit_earlystop_matches':stop,'explicit_native_earlystop_lines':stops,'gpu0':gpu(),'locks':locks,
 'checkpoint_paths':ckpts,'source_hashes':hashes,'frozen_sources_match':hashes==EXPECTED_HASHES,
 'producer_source_hashes':{name:sha(root/name) for name in producer_sources},
 'frozen_m95':{'path':str(trusted),'sha256':sha(trusted),'bytes':trusted.stat().st_size},
 'resume_lineage':re.findall(r'resume start_epoch:(\d+),best_miou:([0-9.eE+-]+),epochs_no_improve:(\d+)!',head.decode(errors='replace')),
 'no_signals_or_gpu_computation':True}
print(json.dumps(result))
'''
    result = json.loads(remote("192.168.1.115", shlex.join(["env", "PYTHONDONTWRITEBYTECODE=1", "/usr/bin/python3", "-B", "-c", program])))
    save("terminal_observation.json", result)
    source3 = r'''
import datetime,json,socket,subprocess
assert socket.gethostname()=='sysu311-MS-7C59'
rows=subprocess.check_output(['nvidia-smi','-i','1','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],universal_newlines=True).strip()
assert rows.split(',')[1].strip()=='GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0'
contexts=subprocess.check_output(['nvidia-smi','-i','1','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],universal_newlines=True).strip()
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'gpu':rows,'contexts':contexts,'no_process_signal':True}))
'''
    other = json.loads(remote("192.168.1.120", shlex.join(["/usr/bin/python3", "-B", "-c", source3])))
    save("resource_observation.json", {"server-4": result["gpu0"], "server-3": other})
    print(json.dumps({"observed_at": result["observed_at"], "pid_exists": result["pid_exists"],
                      "exact_training_pids": result["exact_training_pids"], "earlystop": result["explicit_earlystop_matches"],
                      "earlystop_lines": result["explicit_native_earlystop_lines"],
                      "best": max(result["native_scalar_log"]["miou"]), "val_records": len(result["native_scalar_log"]["miou"]),
                      "locks": result["locks"], "gpu0": result["gpu0"], "frozen_sources_match": result["frozen_sources_match"],
                      "frozen_m95": result["frozen_m95"], "other_slot": other}, indent=2))
