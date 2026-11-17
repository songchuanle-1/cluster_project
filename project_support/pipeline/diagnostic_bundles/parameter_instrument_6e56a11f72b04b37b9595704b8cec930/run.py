"""Execute CPU instrumentation and reconcile only the exact running experiment."""

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

TOKEN = "6e56a11f72b04b37b9595704b8cec930"
PROJECT = Path("D:/project/cluster_project")
BUNDLE = Path(__file__).resolve().parent
SOURCE = PROJECT / "pipeline/diagnostic_bundles/bps_task_2bbb4e0b9a814185a795b2ea2178483f/parameter_transport.py"
REMOTE = "/data/songcl/Project/Cluster_project/pipeline/parameter_instrument_" + TOKEN
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=12", "server-4"]
PYTHON = "/home/songcl/.conda/envs/project_cluster/bin/python"
owner = tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.fromisoformat(owner["deadline_at"]) > datetime.now(timezone.utc)
assert not (BUNDLE / "execution.json").exists()
exp = monitor.load_experiment(str(PROJECT), "M201-BPS")
assert exp["server"] == "server-4" and exp["gpu"] == "0" and exp["pid"] == 2634704


def execute(args, *, code=None, timeout=60):
    p = subprocess.run(args, input=code, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    if p.returncode:
        raise RuntimeError(json.dumps({"args": args, "rc": p.returncode, "stdout": p.stdout[-3000:], "stderr": p.stderr[-3000:]}))
    return p.stdout


setup = execute(SSH + ["python3", "-"], code=f"""
import pathlib,subprocess
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
pathlib.Path({REMOTE!r}).mkdir(exist_ok=False)
print('verified CPU bundle directory')
""")
for path in (SOURCE, BUNDLE / "cpu_test.py"):
    execute(["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", str(path), "server-4:" + REMOTE + "/"])
native = execute(SSH + ["python3", "-"], code=f"""
import datetime,json,os,pathlib,re,subprocess,time
pid=2634704;p=pathlib.Path('/proc')/str(pid)
root='/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b'
assert p.exists() and (p/'stat').read_text().split()[2]!='Z'
assert os.readlink(p/'cwd')==root
args=(p/'cmdline').read_bytes().split(b'\\0')
assert {exp['config'].encode()!r} in args and b'--resume' in args
log=pathlib.Path({exp['log']!r})
def observation():
    with log.open('rb') as f:
        f.seek(max(0,log.stat().st_size-48000));text=f.read().decode(errors='replace')
    matches=re.findall(r'(Train|Val)\\[(\\d+)/(\\d+)\\]:[^\\r\\n]*?\\|\\s*(\\d+)/(\\d+)',text)
    assert matches and 'Traceback (most recent call last)' not in text
    return {{'progress':matches[-1],'bytes':log.stat().st_size}}
first=observation();time.sleep(8);second=observation()
assert second['bytes']>first['bytes'],'No new native log progress; reconcile, do not relaunch'
print(json.dumps({{'observed_at':datetime.datetime.now().astimezone().isoformat(),
                  'pid':pid,'first':first,'second':second,'native_progress_verified':True,
                  'gpu':subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip(),
                  'compute':subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()}}))
""", timeout=25)
native = json.loads(native)
tick.save(BUNDLE / "exact_training_observation.json", native)
execution = execute(SSH + ["python3", "-"], code=f"""
import json,os,subprocess
env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
run=subprocess.run(['timeout','--signal=TERM','--kill-after=10s','60',{PYTHON!r},'-B',
                    {REMOTE + '/cpu_test.py'!r},{REMOTE + '/parameter_transport.py'!r},
                    {REMOTE + '/result.json'!r}],env=env,capture_output=True,text=True)
print(json.dumps({{'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr}}))
""", timeout=75)
execution = json.loads(execution)
tick.save(BUNDLE / "execution.json", {"token": TOKEN, "source_sha256": tick.digest(SOURCE),
                                    "script_sha256": tick.digest(BUNDLE / "cpu_test.py"), **execution})
execute(["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
         "server-4:" + REMOTE + "/result.json", str(BUNDLE / "result.json")])
assert execution["returncode"] == 0
result = tick.load(BUNDLE / "result.json")
assert result["status"] == "PASS" and result["source_sha256"] == tick.digest(SOURCE)
lock = monitor.acquire_lock(str(PROJECT))
assert lock is not None
try:
    dw = monitor.load_deathwatch(str(PROJECT))
    previous = dw.get("server-4", {}).pop(Path(exp["config"]).stem, None)
    monitor.save_deathwatch(str(PROJECT), dw)
    tick.save(BUNDLE / "deathwatch_reconciliation.json", {
        "previous": previous, "exact_pid": 2634704, "native_progress_verified": True,
        "scope": "Only clear this exact live experiment's false miss; no scheduler, foreign task, scientific gate or training launch changed.",
    })
finally:
    lock.close()
print(json.dumps({"cpu_instrument": execution["stdout"], "exact_training": native, "cleared_miss": previous}))
