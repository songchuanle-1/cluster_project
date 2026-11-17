"""Bounded runtime-only repair; preserve checkpoint, config and failed launch."""

from datetime import datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import migrate as m

m.guard(300)
assert not (m.BUNDLE / "launch_retry.json").exists()
short_tmp = m.PIPE + "/tmp"
failed = m.tick.load(m.BUNDLE / "launch.json")
loader_test = json.loads(m.remote(m.TARGET, f"""
import json,os,pathlib,subprocess
root=pathlib.Path({m.ROOT!r});tmp=pathlib.Path({short_tmp!r})
tmp.mkdir(exist_ok=True)
assert os.access(tmp,os.W_OK)
program={'''import json
import torch
import tools.train
import gorilla
from framework.dataset import build_dataset,build_dataloader
from framework.utils import get_root_logger
cfg=gorilla.Config.fromfile(CONFIG)
gorilla.set_random_seed(cfg.train.seed)
dataset=build_dataset(cfg.data.train,get_root_logger())
loader=build_dataloader(dataset,**cfg.dataloader.train)
iterator=iter(loader)
try:
    batches=[next(iterator),next(iterator)]
    assert all(len(b["scan_ids"])==2 for b in batches)
    print(json.dumps({"status":"PASS","strategy":torch.multiprocessing.get_sharing_strategy(),
                     "workers":cfg.dataloader.train.num_workers,"batch_size":2,
                     "scan_ids":[b["scan_ids"] for b in batches]}))
finally:
    iterator._shutdown_workers()
'''.replace('CONFIG', repr(m.ROOT + '/' + m.CONFIG))!r}
env=os.environ.copy();env.update(PYTHONPATH={m.ROOT + ':' + m.ROOT + '/framework/lib'!r},
    LD_LIBRARY_PATH='/home/songcl/.conda/envs/project_cluster/lib:/home/songcl/.conda/envs/project_cluster/lib/python3.10/site-packages/torch/lib',
    TMPDIR={short_tmp!r},PYTHONDONTWRITEBYTECODE='1',TOKENIZERS_PARALLELISM='false')
result=subprocess.run(['timeout','--signal=TERM','--kill-after=10s','90',{m.PYTHON!r},'-B','-c',program],
                      cwd=root,env=env,text=True,capture_output=True)
print(json.dumps({{'returncode':result.returncode,'stdout':result.stdout[-3000:],'stderr':result.stderr[-3000:],
                  'tmpdir':{short_tmp!r},'environment_only':True}}))
""", timeout=110))
m.record("loader_smoke", loader_test)
assert loader_test["returncode"] == 0, json.dumps(loader_test)
assert json.loads(loader_test["stdout"].splitlines()[-1])["status"] == "PASS"

lock = m.monitor.acquire_lock(str(m.PROJECT))
assert lock is not None
try:
    stopped = json.loads(m.remote(m.TARGET, f"""
import json,os,pathlib,re,signal,time
pid={failed['pid']!r};p=pathlib.Path('/proc')/str(pid)
assert os.readlink(p/'cwd')=={m.ROOT!r}
args=(p/'cmdline').read_bytes().split(b'\\0')
assert {m.CONFIG.encode()!r} in args and b'--resume' in args
assert (p/'stat').read_text().split()[21]=='154329268'
log=pathlib.Path({failed['log']!r})
text=log.read_text()
assert 'torch_shm_manager' in text and 'Invalid argument' in text
assert not re.search(r'Epoch \\[9/50\\]\\[\\d+/',text),'Unexpected training updates; reconcile checkpoint before retry'
children=[]
for item in (p/'task'/str(pid)/'children').read_text().split():
    q=pathlib.Path('/proc')/item
    try:
        assert os.readlink(q/'cwd')=={m.ROOT!r}
        children.append((int(item),(q/'stat').read_text().split()[21]))
    except FileNotFoundError:pass
os.kill(pid,signal.SIGTERM)
for child,start in children:
    q=pathlib.Path('/proc')/str(child)
    try:
        if (q/'stat').read_text().split()[21]==start and (q/'stat').read_text().split()[2]!='Z':
            assert os.readlink(q/'cwd')=={m.ROOT!r};os.kill(child,signal.SIGTERM)
    except FileNotFoundError:pass
deadline=time.time()+20
def active(q):
    try:return (q/'stat').read_text().split()[2]!='Z'
    except FileNotFoundError:return False
while any(active(pathlib.Path('/proc')/str(x)) for x in [pid]+[x[0] for x in children]) and time.time()<deadline:
    time.sleep(.2)
assert not any(active(pathlib.Path('/proc')/str(x)) for x in [pid]+[x[0] for x in children])
print(json.dumps({{'failed_pid':pid,'stopped_exact_process_tree':True,
                  'owned_children':[x[0] for x in children],'log':str(log),'log_bytes':log.stat().st_size,
                  'no_completed_training_steps_observed':True,
                  'failure':'Long TMPDIR causes torch_shm_manager Invalid argument; native multiprocess loading PASS with short project temp directory.'}}))
""", timeout=30))
    m.record("failed_launch_stopped", stopped)
    m.copy(m.TARGET + ":" + failed["log"], str(m.BUNDLE / "failed_launch.log"), timeout=30)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = m.ROOT + "/logs/train_" + Path(m.CONFIG).stem + "_resume_retry_" + timestamp + ".log"
    launched = json.loads(m.remote(m.TARGET, f"""
import fcntl,json,os,pathlib,subprocess
root=pathlib.Path({m.ROOT!r});lease=open({m.TRAINING_LOCK!r},'a+')
fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
env=os.environ.copy();env.update(CONDA_PREFIX='/home/songcl/.conda/envs/project_cluster',
    PYTHONPATH={m.ROOT + ':' + m.ROOT + '/framework/lib'!r},
    LD_LIBRARY_PATH='/home/songcl/.conda/envs/project_cluster/lib:/home/songcl/.conda/envs/project_cluster/lib/python3.10/site-packages/torch/lib',
    TMPDIR={short_tmp!r},PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
assert not pathlib.Path({log!r}).exists()
cmd=[{m.PYTHON!r},'tools/train.py',{m.CONFIG!r},'--resume',{m.REMOTE + '/resume.pth'!r},'--gpu_ids','0','--num_gpus','1']
with open({log!r},'ab',buffering=0) as out:
    proc=subprocess.Popen(cmd,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,
                          start_new_session=True,pass_fds=(lease.fileno(),))
(root/'logs'/('.pid_'+pathlib.Path({m.CONFIG!r}).stem)).write_text(str(proc.pid))
print(json.dumps({{'pid':proc.pid,'log':{log!r},'command':cmd,'tmpdir':{short_tmp!r},
                  'checkpoint_meta':{failed['checkpoint_meta']!r},'launch_verified':False,
                  'launch_verification':'pending_progress','repair':'TMPDIR only; same checkpoint/config/code/seed/schedule/workers.'}}))
""", timeout=30))
    m.record("launch_retry", launched)
    queue = m.monitor.load_queue(str(m.PROJECT))
    task = next(task for task in queue["gpu_queues"]["server-4"] if task["id"] == "M201-BPS")
    assert task["pid"] == failed["pid"]
    task.setdefault("failed_migration_launches", []).append({**failed, **stopped})
    task.update(pid=launched["pid"], log=launched["log"], launch_verified=False,
                launch_verification="pending_progress", migration_repair_count=1)
    exp = m.monitor.load_experiment(str(m.PROJECT), "M201-BPS")
    exp.update({key: task[key] for key in ("pid", "log", "launch_verified", "launch_verification",
                                         "migration_repair_count", "failed_migration_launches")})
    exp["history"].append({"ts": datetime.now().astimezone().isoformat(), "action": "migration_runtime_retry",
                           "server": "server-4", "gpu": "0", "pid": launched["pid"], "repair": "short TMPDIR only"})
    m.monitor.save_queue(str(m.PROJECT), queue)
    m.monitor.save_experiment(str(m.PROJECT), exp)
    print(json.dumps(launched))
finally:
    lock.close()
