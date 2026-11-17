"""One-shot user-requested CPS launch on the idle whitelisted H100."""
import importlib.util
import json
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path("D:/project/cluster_project")
HOST = "songcl@100.64.3.28"
CODE = "/data3/songcl/Project/Cluster_project/Cluster"
ID = "M195-CTF-HCG-CSORT-CPS"
REPAIR = "--repair1" in sys.argv


def ssh(command):
    return subprocess.check_output(["ssh", HOST, command], text=True, timeout=90).strip()


spec = importlib.util.spec_from_file_location(
    "monitor", "D:/project/.claude/skills/songcl_research_pipeline/pipeline_monitor.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
lock = m.acquire_lock(str(ROOT))
assert lock is not None, "Pipeline lock busy"
try:
    queue = m.load_queue(str(ROOT))
    origin = "server-6" if REPAIR else "server-4"
    task = next(t for t in queue["gpu_queues"][origin] if t["id"] == ID)
    if REPAIR:
        assert task.get("repair_attempts", 0) == 0
        assert ssh(f"if kill -0 {int(task['pid'])} 2>/dev/null; then echo alive; else echo dead; fi") == "dead"
        assert "Duplicate physical seeds" in ssh("tail -25 " + shlex.quote(task["log"]))
        task["code_commit"] = subprocess.check_output(
            ["git","-C",str(ROOT/"Cluster"),"rev-parse","HEAD"],text=True).strip()
        assert task["code_commit"].startswith("acae108")
    else:
        assert task["status"] == "waiting" and not task.get("launched")
    assert ssh(f"git -C {CODE} rev-parse HEAD") == task["code_commit"]
    gpu = ssh("nvidia-smi --id=7 --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits")
    util, memory = map(int, gpu.split(","))
    assert util < 10 and memory < 1024, gpu
    running = m.load_running(str(ROOT))
    assert running.get("server-6", {}).get("7") in (None, ID) if REPAIR else not running.get("server-6", {}).get("7")
    config = task["config"]
    # Adapt this candidate's deployment paths only, using YAML rather than
    # touching unrelated running experiments' configuration files.
    adapt = f"""
import pathlib,yaml
p=pathlib.Path({str(CODE + '/' + config)!r})
c=yaml.safe_load(p.read_text())
def adapt(v):
    if isinstance(v,dict): return {{k:adapt(x) for k,x in v.items()}}
    if isinstance(v,list): return [adapt(x) for x in v]
    if isinstance(v,str):
        return v.replace('/home/songcl/data/data','/data3/songcl/data/data_cluster').replace('/home/songcl/3dres/project/cluster_project/Checkpoints','/data3/songcl/Project/Cluster_project/Cluster_checkpoints')
    return v
d=adapt(c)
assert pathlib.Path(d['train']['pretrain']).is_file()
assert pathlib.Path(d['model']['data_root']).is_dir()
p.write_text(yaml.safe_dump(d,sort_keys=False))
"""
    activate = "source /data3/songcl/miniconda3/etc/profile.d/conda.sh && conda activate project_cluster"
    ssh(activate + " && python -c " + shlex.quote(adapt))
    now = datetime.now()
    log = f"{CODE}/logs/train_{Path(config).stem}_{now:%Y%m%d_%H%M%S}.log"
    launch = f"""
import subprocess,os,pathlib,json
root={CODE!r}
cfg={config!r}
for p in pathlib.Path('/proc').glob('[0-9]*/cmdline'):
    try: cmd=p.read_bytes().split(b'\\0')
    except OSError: continue
    if b'tools/train.py' in cmd and cfg.encode() in cmd:
        raise RuntimeError('CPS already running')
pathlib.Path(root+'/logs').mkdir(exist_ok=True)
env=os.environ.copy()
env['PYTHONPATH']=root+':'+root+'/framework/lib:'+env.get('PYTHONPATH','')
env['LD_LIBRARY_PATH']=env['CONDA_PREFIX']+'/lib:'+env['CONDA_PREFIX']+'/lib/python3.10/site-packages/torch/lib:'+env.get('LD_LIBRARY_PATH','')
with open({log!r},'ab',buffering=0) as out:
    p=subprocess.Popen(['python','tools/train.py',cfg,'--gpu_ids','7','--num_gpus','1'],cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
pathlib.Path(root+'/logs/.pid_'+pathlib.Path(cfg).stem).write_text(str(p.pid))
print(json.dumps(dict(pid=p.pid,log={log!r})))
"""
    result = json.loads(ssh(activate + " && python -c " + shlex.quote(launch)))
    task.update(status="running", server="server-6", gpu=7, pid=result["pid"],
                log=log, launched=now.isoformat(timespec="seconds"))
    if origin != "server-6":
        queue["gpu_queues"][origin].remove(task)
        queue["gpu_queues"]["server-6"].append(task)
    if REPAIR:
        task["repair_attempts"] = 1
    running.setdefault("server-6", {})["7"] = ID
    record = m.load_experiment(str(ROOT), ID) or {}
    record.update(task)
    record.setdefault("history", []).append(
        dict(ts=now.isoformat(), action="repair1_launch" if REPAIR else "manual_launch",
             decision="20260914-202000_manual.md" if REPAIR else "20260914-194215_manual.md"))
    m.save_experiment(str(ROOT), record)
    m.save_queue(str(ROOT), queue)
    m.save_running(str(ROOT), running)
    print(json.dumps(task, indent=2))
finally:
    lock.close()
