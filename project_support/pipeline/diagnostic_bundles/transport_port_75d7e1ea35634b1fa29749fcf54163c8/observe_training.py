"""Verify exact live training and the scoped monitor repair, without preflight."""

import json
from pathlib import Path

import stage

stage.guard(120)
monitor = stage.monitor
project = str(stage.PROJECT)
experiment = monitor.load_experiment(project, "M201-BPS")
assert experiment["pid"] == 2634704 and experiment["server"] == "server-4"
servers = monitor.load_servers(project)
queue = monitor.load_queue(project)
probe = monitor.find_project_processes("cluster_project", "server-4", servers["server-4"], queue)
assert probe is not None and experiment["config"] in probe, probe
assert probe[experiment["config"]][0] == "2634704"
stage.save("registered_probe_live", {"result": probe, "status": "PASS",
                                  "monitor_sha256": stage.tick.digest(Path(monitor.__file__))})
result = json.loads(stage.remote(f"""
import datetime,json,os,pathlib,re,subprocess,time,torch
pid=2634704;p=pathlib.Path('/proc')/str(pid)
assert p.exists() and (p/'stat').read_text().split()[2]!='Z'
assert os.readlink(p/'cwd')=={stage.ROOT!r}
args=(p/'cmdline').read_bytes().split(b'\\0')
assert {experiment["config"].encode()!r} in args and b'--resume' in args
log=pathlib.Path({experiment["log"]!r})
def observe():
    with log.open('rb') as stream:
        stream.seek(max(0,log.stat().st_size-64000));text=stream.read().decode(errors='replace')
    matches=re.findall(r'(Train|Val)\\[(\\d+)/(\\d+)\\]:[^\\r\\n]*?\\|\\s*(\\d+)/(\\d+)',text)
    assert matches and 'Traceback (most recent call last)' not in text
    return {{'progress':matches[-1],'bytes':log.stat().st_size}}
first=observe();time.sleep(8);second=observe()
assert second['bytes']>first['bytes'] and second['progress']!=first['progress']
base=pathlib.Path({servers["server-4"]["work_dir"]!r})/{Path(experiment["config"]).stem!r}
path=base/'20261014_154431/last.pth'
before=path.stat();saved=torch.load(path,map_location='cpu',weights_only=False,mmap=True)
after=path.stat()
assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
assert saved['meta']['epoch']>=9
print(json.dumps({{'observed_at':datetime.datetime.now().astimezone().isoformat(),
                  'pid':pid,'config':{experiment["config"]!r},'first':first,'second':second,
                  'native_progress_verified':True,'checkpoint':str(path),'checkpoint_meta':saved['meta'],
                  'gpu':subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip(),
                  'compute':subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()}},
                 default=lambda value:value.item()))
""", timeout=45, python=stage.PYTHON))
stage.save("exact_training_observation", result)
lock = monitor.acquire_lock(project)
assert lock is not None
try:
    deathwatch = monitor.load_deathwatch(project)
    previous = deathwatch.get("server-4", {}).pop(Path(experiment["config"]).stem, None)
    monitor.save_deathwatch(project, deathwatch)
    stage.save("deathwatch_reconciliation", {"previous": previous, "pid": 2634704,
               "scope": "Only remove this exact experiment's proven false miss after increasing native steps."})
finally:
    lock.close()
print(json.dumps(result))
