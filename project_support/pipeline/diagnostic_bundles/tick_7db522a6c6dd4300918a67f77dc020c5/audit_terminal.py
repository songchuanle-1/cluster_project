"""Audit the exact monitored terminal without treating a queue opening as GPU idle."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick
import pipeline_monitor as monitor

TOKEN = "7db522a6c6dd4300918a67f77dc020c5"
PROJECT = Path("D:/project/cluster_project")
BUNDLE = Path(__file__).resolve().parent
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=12", "server-4"]
PYTHON = "/home/songcl/.conda/envs/project_cluster/bin/python"


def guard(seconds=60):
    owner = tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > seconds


def command(args, code=None, timeout=60):
    guard(timeout + 30)
    run = subprocess.run(args, input=code, text=True, encoding="utf-8", capture_output=True, timeout=timeout)
    if run.returncode:
        raise RuntimeError(json.dumps({"rc": run.returncode, "stdout": run.stdout[-3000:], "stderr": run.stderr[-4000:]}))
    return run.stdout


def save(name, data):
    path = BUNDLE / (name + ".json")
    assert not path.exists()
    tick.save(path, {"token": TOKEN, "local_observed_at": datetime.now().astimezone().isoformat(), **data})


if __name__ == "__main__":
    guard()
    experiment = monitor.load_experiment(str(PROJECT), "M201-BPS")
    assert experiment["pid"] == 2634704 and experiment["status"] == "done_earlystop"
    config = experiment["config"]
    root = monitor.load_servers(str(PROJECT))["server-4"]["remote_code_root"]
    work = monitor.load_servers(str(PROJECT))["server-4"]["work_dir"]
    program = f"""
import datetime,fcntl,hashlib,json,os,pathlib,re,subprocess,time
os.environ['CUDA_VISIBLE_DEVICES']=''
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
pid=2634704;p=pathlib.Path('/proc')/str(pid)
def observe():
    process={{'pid':pid,'exists':p.exists()}}
    if p.exists():
        process.update(state=(p/'stat').read_text().split()[2],cwd=os.readlink(p/'cwd'),
                       args=[part.decode() for part in (p/'cmdline').read_bytes().split(b'\\0') if part])
    handles=[];locks={{}}
    try:
        for name in ('/tmp/cluster_project_gpu0_m201_migration.lock',
                     '/tmp/cluster_project_gpu0_exclusive.lock',
                     '/tmp/cluster_project_gpu0_parameter_transport.lock'):
            f=open(name,'a+b');handles.append(f)
            try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[name]='available'
            except BlockingIOError:locks[name]='held'
    finally:
        for f in reversed(handles):f.close()
    return {{'observed_at':datetime.datetime.now().astimezone().isoformat(),'process':process,
             'gpu':subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip(),
             'compute':subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip(),'locks':locks}}
first=observe();time.sleep(8);second=observe()
if second['process']['exists']:
    assert second['process']['cwd']=={root!r} and {config!r} in second['process']['args']
log=pathlib.Path({experiment["log"]!r});stat=log.stat()
with log.open('rb') as stream:
    stream.seek(max(0,stat.st_size-250000));text=stream.read().decode(errors='replace').replace('\\r','\\n')
lines=text.splitlines()
progress=re.findall(r'(Train|Val)\\[(\\d+)/(\\d+)\\]:[^\\n]*?\\|\\s*(\\d+)/(\\d+)',text)
signals=[line for line in lines if any(term in line.lower() for term in ('early stop','best miou','no improvement','traceback','killed','terminated'))][-12:]
import torch
assert not torch.cuda.is_initialized()
checkpoint=pathlib.Path({work!r})/{Path(config).stem!r}/'20261014_154431/last.pth'
before=checkpoint.stat();saved=torch.load(checkpoint,map_location='cpu',weights_only=False,mmap=True)
after=checkpoint.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
h=hashlib.sha256()
with log.open('rb') as stream:
    for block in iter(lambda:stream.read(8*1024**2),b''):h.update(block)
assert (stat.st_size,stat.st_mtime_ns)==(log.stat().st_size,log.stat().st_mtime_ns),'Log still growing; retain observation instead of claiming final log'
print(json.dumps({{'first':first,'second':second,'checkpoint':str(checkpoint),
                  'checkpoint_meta':saved['meta'],'checkpoint_bytes':before.st_size,
                  'log':str(log),'log_bytes':stat.st_size,'log_sha256':h.hexdigest(),
                  'latest_native_progress':progress[-1] if progress else None,
                  'terminal_lines':signals,'metrics_tail':[line for line in lines if line.startswith(('mIOU:','spmIOU:'))][-4:],
                  'cuda_initialized':torch.cuda.is_initialized(),
                  'scope':'Exact original PID and native metadata only; monitor terminal is not proof of process disappearance.'}},
                 default=lambda value:value.item()))
"""
    result = json.loads(command(SSH + [PYTHON, "-B", "-"], program, timeout=60))
    save("terminal_audit", result)
    print(json.dumps(result))
