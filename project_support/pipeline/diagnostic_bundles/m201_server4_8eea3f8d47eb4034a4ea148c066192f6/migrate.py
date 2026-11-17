"""Lease-bound, staged migration of the existing M201 run, never a cold launch."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick
import pipeline_monitor as monitor

TOKEN = "8eea3f8d47eb4034a4ea148c066192f6"
PROJECT = Path("D:/project/cluster_project")
BUNDLE = Path(__file__).resolve().parent
CODE = PROJECT / "Cluster"
COMMIT = "f8457d3b657e66306a7fce1afb3d81d8ab874669"
CONFIG = "configs/Quard/bps/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps.yaml"
OLD = "/data/songcl/Project/Cluster_project/Cluster"
ROOT = "/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b"
PIPE = "/data/songcl/Project/Cluster_project/pipeline"
REMOTE = PIPE + "/migration_" + TOKEN
TRAINING_LOCK = "/tmp/cluster_project_gpu0_m201_migration.lock"
PYTHON = "/home/songcl/.conda/envs/project_cluster/bin/python"
SOURCE = "songcl@100.64.3.28"
TARGET = "server-4"
SOURCE_ROOT = "/data3/songcl/Project/Cluster_project/Cluster"
SOURCE_PIPE = "/data3/songcl/Project/Cluster_project/pipeline"
LAST = "/data3/songcl/Project/Cluster_project/Cluster_checkpoints/" + Path(CONFIG).stem + "/20261014_020219/last.pth"
CATALOG = "bps_catalog_1d59938f077948578e91e2cf34fc9d53.json"
SSH_OPTS = ["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=12"]


def guard(seconds=30):
    owner = tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > seconds


def run(args, *, code=None, timeout=180):
    guard(min(timeout + 15, 900))
    result = subprocess.run(args, input=code, text=True, encoding="utf-8",
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(json.dumps({"args": args, "returncode": result.returncode,
                                      "stdout": result.stdout[-3500:], "stderr": result.stderr[-3500:]}))
    return result.stdout


def remote(host, program, python="python3", timeout=180):
    return run(["ssh", *SSH_OPTS, host, python, "-B", "-"], code=program, timeout=timeout)


def copy(source, target, timeout=180):
    return run(["scp", *SSH_OPTS, source, target], timeout=timeout)


def record(stage, result):
    path = BUNDLE / (stage + ".json")
    assert not path.exists(), "Recorded stages must be reconciled, never replayed"
    tick.save(path, {"token": TOKEN, "observed_at": datetime.now().astimezone().isoformat(), **result})


def deploy():
    # A detached worktree avoids all modifications in the historical checkout.
    identity = json.loads(remote(TARGET, f"""
import hashlib,json,pathlib,subprocess
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
p=pathlib.Path({ROOT!r})
assert not p.exists(), 'Reconcile existing deployment'
status=subprocess.check_output(['git','-C',{OLD!r},'status','--porcelain'],text=True)
print(json.dumps({{'original_status_sha256':hashlib.sha256(status.encode()).hexdigest(),
                  'original_head':subprocess.check_output(['git','-C',{OLD!r},'rev-parse','HEAD'],text=True).strip()}}))
"""))
    ref = "refs/heads/codex-migration-" + COMMIT[:12]
    pushed = run(["git", "-C", str(CODE), "push", "songcl@192.168.1.115:" + OLD, COMMIT + ":" + ref])
    setup = json.loads(remote(TARGET, f"""
import hashlib,json,pathlib,shutil,subprocess,yaml
old=pathlib.Path({OLD!r});root=pathlib.Path({ROOT!r})
subprocess.check_call(['git','-C',str(old),'worktree','add','--detach',str(root),{COMMIT!r}],stdout=subprocess.DEVNULL)
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()=={COMMIT!r}
status=subprocess.check_output(['git','-C',str(old),'status','--porcelain'],text=True)
assert hashlib.sha256(status.encode()).hexdigest()=={identity['original_status_sha256']!r}
so=list((old/'framework/lib/pointgroup_ops').glob('pointgroup_ops_ext*.so'))
assert len(so)==1
dst=root/'framework/lib/pointgroup_ops'/so[0].name
assert not dst.exists()
shutil.copy2(so[0],dst)
pathlib.Path({REMOTE!r}).mkdir(parents=True,exist_ok=False)
cfg=root/{CONFIG!r}
c=yaml.safe_load(cfg.read_text())
c['work_dir']='/data/songcl/Project/Cluster_project/Cluster_checkpoints'
c['model']['between_catalog']={PIPE + '/' + CATALOG!r}
assert c['train']['seed']==1999 and c['train']['epochs']==50
assert c['lr_scheduler']['max_iters']==70 and c['dataloader']['train']['batch_size']==2
cfg.write_text(yaml.safe_dump(c,sort_keys=False))
print(json.dumps({{'code_commit':{COMMIT!r},'code_root':str(root),
                  'original_status_unchanged':True,'extension_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),
                  'config_sha256':hashlib.sha256(cfg.read_bytes()).hexdigest()}}))
"""))
    catalog = PROJECT / "pipeline" / CATALOG
    assert tick.digest(catalog) == "9ddcddeff3629c50c50054a9eaadb0828f5dfcb8541defd16705341c0dc567f2"
    exists = remote(TARGET, f"from pathlib import Path\nprint(Path({PIPE + '/' + CATALOG!r}).exists())\n").strip()
    if exists != "True":
        copy(str(catalog), TARGET + ":" + PIPE + "/")
    manifest = tick.load(PROJECT / "pipeline/reports/bps_source_manifest_c9de23ffb1804f1eaa81cf54b94b9d6a.json")
    verified = json.loads(remote(TARGET, f"""
import hashlib,json,pathlib
root=pathlib.Path({ROOT!r});package=root/'framework/model/Quard_model'/{Path(CONFIG).stem!r}
observed={{name:hashlib.sha256((package/name).read_bytes()).hexdigest() for name in {list(manifest['package'])!r}}}
assert observed=={manifest['package']!r}
assert hashlib.sha256(pathlib.Path({PIPE + '/' + CATALOG!r}).read_bytes()).hexdigest()=='9ddcddeff3629c50c50054a9eaadb0828f5dfcb8541defd16705341c0dc567f2'
print(json.dumps({{'package_files_verified':len(observed),'catalog_verified':True}}))
"""))
    record("deploy", {"identity": identity, "deployment": setup, "verification": verified, "push_stdout": pushed})
    print(json.dumps(setup))


def data(host):
    data_root = "/data3/songcl/data/data_cluster" if host == SOURCE else "/home/songcl/data/data"
    result = json.loads(remote(host, f"""
from pathlib import Path
import hashlib,json,time
root=Path({data_root!r});started=time.time()
files=[]
for name in ('ScanRefer_train_new.json','ScanRefer_val_new.json','scene_graphs_new_train.json','scene_graphs_new_val.json'):
    files.append(root/'scanrefer'/name)
files.append(root/'scannetv2-labels.combined.tsv')
files.extend(sorted(p for p in (root/'roberta-base').rglob('*') if p.is_file()))
for split in ('train','val'):
    files.extend(sorted((root/'scannetv2'/split).glob('*_refer.pth')))
files.extend(sorted((root/'clip_feat').glob('*.pth')))
rows={{}}
for p in files:
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
    rows[p.relative_to(root).as_posix()]={{'bytes':p.stat().st_size,'sha256':h.hexdigest()}}
assert len(rows)==len(files)
print(json.dumps({{'data_root':str(root),'files':rows,'file_count':len(rows),
                  'total_bytes':sum(r['bytes'] for r in rows.values()),'seconds':time.time()-started}}))
""", timeout=750))
    label = "data_source" if host == SOURCE else "data_target"
    record(label, result)
    print(json.dumps({key: result[key] for key in ("data_root", "file_count", "total_bytes", "seconds")}))


def reconcile_deployment():
    # The first attempt created the worktree but found no local catalog.
    catalog = BUNDLE / CATALOG
    if not catalog.exists():
        copy(SOURCE + ":" + SOURCE_PIPE + "/" + CATALOG, str(catalog), timeout=45)
    assert tick.digest(catalog) == "9ddcddeff3629c50c50054a9eaadb0828f5dfcb8541defd16705341c0dc567f2"
    exists = remote(TARGET, f"from pathlib import Path\nprint(Path({PIPE + '/' + CATALOG!r}).exists())\n").strip()
    if exists != "True":
        copy(str(catalog), TARGET + ":" + PIPE + "/")
    manifest = tick.load(PROJECT / "pipeline/reports/bps_source_manifest_c9de23ffb1804f1eaa81cf54b94b9d6a.json")
    result = json.loads(remote(TARGET, f"""
import hashlib,json,pathlib,subprocess,yaml
root=pathlib.Path({ROOT!r});old=pathlib.Path({OLD!r})
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()=={COMMIT!r}
original_head=subprocess.check_output(['git','-C',str(old),'rev-parse','HEAD'],text=True).strip()
assert original_head=='a490710624530115c3430a8c3693fd8c8d74208b'
package=root/'framework/model/Quard_model'/{Path(CONFIG).stem!r}
observed={{name:hashlib.sha256((package/name).read_bytes()).hexdigest() for name in {list(manifest['package'])!r}}}
assert observed=={manifest['package']!r}
assert hashlib.sha256(pathlib.Path({PIPE + '/' + CATALOG!r}).read_bytes()).hexdigest()=='9ddcddeff3629c50c50054a9eaadb0828f5dfcb8541defd16705341c0dc567f2'
cfg=yaml.safe_load((root/{CONFIG!r}).read_text())
assert cfg['train']['seed']==1999 and cfg['train']['epochs']==50
assert cfg['lr_scheduler']['max_iters']==70 and cfg['dataloader']['train']['batch_size']==2
assert cfg['model']['between_catalog']=={PIPE + '/' + CATALOG!r}
print(json.dumps({{'code_commit':{COMMIT!r},'code_root':str(root),'package_files_verified':len(observed),
                  'catalog_verified':True,'original_head':original_head,
                  'original_status_sha256':hashlib.sha256(subprocess.check_output(['git','-C',str(old),'status','--porcelain'])).hexdigest(),
                  'config_sha256':hashlib.sha256((root/{CONFIG!r}).read_bytes()).hexdigest(),
                  'recovery':'First deploy copied extension/adapted candidate and verified original status unchanged before missing-local-catalog failure. This continuation only retrieves/verifies catalog; no git/deployment replay.'}}))
"""))
    record("deploy", {"deployment": result, "initial_attempt": "FileNotFoundError: catalog absent locally; worktree creation succeeded and was not replayed."})
    print(json.dumps(result))


def freeze():
    result = json.loads(remote(SOURCE, f"""
import hashlib,json,pathlib,shutil,subprocess,torch
assert subprocess.check_output(['hostname'],text=True).strip()=='das'
root=pathlib.Path({SOURCE_ROOT!r})
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()=={COMMIT!r}
source=pathlib.Path({LAST!r});dest=pathlib.Path({SOURCE_PIPE + '/migration_' + TOKEN + '/resume.pth'!r})
dest.parent.mkdir(parents=True,exist_ok=True)
before=source.stat()
if not dest.exists():
    shutil.copyfile(source,dest);after=source.stat()
    assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Checkpoint changed during copy'
c=torch.load(dest,map_location='cpu',weights_only=False)
assert all(k in c for k in ('model','optimizer','scheduler','meta'))
assert c['meta']['epoch']>=7 and c['optimizer']['state']
steps=[float(s['step']) for s in c['optimizer']['state'].values() if 'step' in s]
h=hashlib.sha256()
with dest.open('rb') as stream:
    for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
print(json.dumps({{'path':str(dest),'sha256':h.hexdigest(),'bytes':dest.stat().st_size,'meta':c['meta'],
 'optimizer_state_count':len(c['optimizer']['state']),'optimizer_step_min':min(steps),'optimizer_step_max':max(steps),
 'scheduler':c['scheduler'],'source_mtime_ns':before.st_mtime_ns}},default=lambda x:x.item()))
""", python="/home/songcl/miniconda3/envs/project_cluster/bin/python", timeout=120))
    local = BUNDLE / "resume.pth"
    copy(SOURCE + ":" + result["path"], str(local), timeout=300)
    assert tick.digest(local) == result["sha256"]
    copy(str(local), TARGET + ":" + REMOTE + "/resume.pth", timeout=300)
    target = json.loads(remote(TARGET, f"""
import hashlib,json,pathlib,torch
p=pathlib.Path({REMOTE + '/resume.pth'!r})
h=hashlib.sha256()
with p.open('rb') as stream:
    for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
assert h.hexdigest()=={result['sha256']!r}
c=torch.load(p,map_location='cpu',weights_only=False)
assert c['meta']=={result['meta']!r}
print(json.dumps({{'path':str(p),'sha256':h.hexdigest(),'meta':c['meta'],'optimizer_state_count':len(c['optimizer']['state']),'scheduler':c['scheduler']}},default=lambda x:x.item()))
""", python=PYTHON, timeout=90))
    record("checkpoint", {"source": result, "target": target, "local_sha256": tick.digest(local)})
    print(json.dumps({"meta": result["meta"], "sha256": result["sha256"], "optimizer_step_max": result["optimizer_step_max"]}))


def validate(compat=False):
    source = tick.load(BUNDLE / "data_source.json")["files"]
    target = tick.load(BUNDLE / "data_target.json")["files"]
    missing = sorted(set(source) - set(target))
    different = sorted(k for k in source.keys() & target.keys() if source[k] != target[k])
    extra = sorted(set(target) - set(source))
    comparison = {"missing": missing, "different": different, "extra": extra, "matched": len(source) - len(missing) - len(different)}
    assert not missing and not different and not extra, json.dumps(comparison)
    name = "native_probe_compat" if compat else "native_probe"
    copy(str(BUNDLE / (name + ".py")), TARGET + ":" + REMOTE + "/")
    env = {"CONDA_PREFIX": "/home/songcl/.conda/envs/project_cluster",
           "CUDA_VISIBLE_DEVICES": "0", "PYTHONPATH": ROOT + ":" + ROOT + "/framework/lib",
           "LD_LIBRARY_PATH": "/home/songcl/.conda/envs/project_cluster/lib:/home/songcl/.conda/envs/project_cluster/lib/python3.10/site-packages/torch/lib",
           "TMPDIR": REMOTE, "PYTHONDONTWRITEBYTECODE": "1", "HF_HUB_OFFLINE": "1", "TOKENIZERS_PARALLELISM": "false"}
    output = remote(TARGET, f"""
import json,os,subprocess
env=os.environ.copy();env.update({env!r})
p=subprocess.run(['timeout','--signal=TERM','--kill-after=15s','300',{PYTHON!r},
                  '-B',{REMOTE + '/' + name + '.py'!r},{ROOT!r},{CONFIG!r},{REMOTE + '/resume.pth'!r},
                  {REMOTE + '/' + name + '.json'!r}],cwd={ROOT!r},env=env,capture_output=True,text=True)
print(json.dumps({{'returncode':p.returncode,'stdout':p.stdout[-6000:],'stderr':p.stderr[-6000:]}}))
""", timeout=340)
    result = json.loads(output)
    copy(TARGET + ":" + REMOTE + "/" + name + ".json", str(BUNDLE / (name + ".json")), timeout=30)
    record("validation_compat" if compat else "validation", {"dataset_comparison": comparison, "execution": result})
    assert result["returncode"] == 0, output
    probe = tick.load(BUNDLE / (name + ".json"))
    assert probe["status"] == "PASS"
    print(json.dumps(probe))


def cutover():
    assert tick.load(BUNDLE / "native_probe_compat.json")["status"] == "PASS"
    assert tick.load(BUNDLE / "validation_compat.json")["execution"]["returncode"] == 0
    checkpoint = tick.load(BUNDLE / "checkpoint.json")
    servers = monitor.load_servers(str(PROJECT))
    assert servers["server-4"]["allowed_gpus"] == [0]
    assert servers["server-4"]["remote_code_root"] == ROOT
    assert not servers["server-6"]["dispatch_enabled"]
    lock = monitor.acquire_lock(str(PROJECT))
    assert lock is not None, "Another queue writer owns the pipeline lock"
    try:
        readiness = json.loads(remote(TARGET, f"""
import fcntl,hashlib,json,pathlib,subprocess
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
lease=open({TRAINING_LOCK!r},'a+')
fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=uuid,memory.free','--format=csv,noheader,nounits'],text=True).strip()
assert gpu.split(',')[0]=='GPU-7f82edb9-f620-8045-caea-a75232265cd1' and int(gpu.split(',')[1])>30000
assert not subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
for root in ({OLD!r},{ROOT!r}):
    marker=pathlib.Path(root)/'logs'/('.pid_'+pathlib.Path({CONFIG!r}).stem)
    if not marker.exists():continue
    pid=marker.read_text().strip()
    assert pid.isdigit()
    p=pathlib.Path('/proc')/pid
    try:
        cmd=(p/'cmdline').read_bytes().split(b'\\0')
        state=(p/'stat').read_text().split()[2]
    except FileNotFoundError:continue
    assert not (state!='Z' and b'tools/train.py' in cmd and {CONFIG.encode()!r} in cmd),'Candidate already running'
p=pathlib.Path({REMOTE + '/resume.pth'!r});h=hashlib.sha256()
with p.open('rb') as stream:
    for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
assert h.hexdigest()=={checkpoint['source']['sha256']!r}
print(json.dumps({{'gpu':gpu,'checkpoint_sha256':h.hexdigest(),'exclusive_lease_available':True}}))
""", timeout=90))
        record("cutover_ready", readiness)
        stopped = json.loads(remote(SOURCE, f"""
import hashlib,json,os,pathlib,signal,subprocess,time
assert subprocess.check_output(['hostname'],text=True).strip()=='das'
pid=2867534;p=pathlib.Path('/proc')/str(pid)
assert os.readlink(p/'cwd')=={SOURCE_ROOT!r}
args=(p/'cmdline').read_bytes().split(b'\\0')
assert b'tools/train.py' in args and {CONFIG.encode()!r} in args
assert args[args.index(b'--gpu_ids')+1]==b'7'
start=(p/'stat').read_text().split()[21]
last=pathlib.Path({LAST!r});h=hashlib.sha256()
with last.open('rb') as stream:
    for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
assert h.hexdigest()=={checkpoint['source']['sha256']!r},'Latest complete checkpoint changed; do not stop source before refreshing'
children=[]
for q in pathlib.Path('/proc').glob('[0-9]*/stat'):
    try:
        fields=q.read_text().split()
        if int(fields[3])==pid and os.readlink(q.parent/'cwd')=={SOURCE_ROOT!r}:
            children.append((int(fields[0]),fields[21]))
    except (OSError,ValueError):pass
log=pathlib.Path('/data3/songcl/Project/Cluster_project/Cluster/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps_20261014_095849.log')
with log.open('rb') as stream:
    stream.seek(max(0,log.stat().st_size-12000));tail=stream.read().decode(errors='replace').replace('\\r','\\n').splitlines()[-5:]
assert (p/'stat').read_text().split()[21]==start
os.kill(pid,signal.SIGTERM)
deadline=time.time()+25
def active(p):
    try:return (p/'stat').read_text().split()[2]!='Z'
    except FileNotFoundError:return False
while active(p) and time.time()<deadline:time.sleep(.2)
assert not active(p),'Exact source process did not terminate'
terminated=[]
for child,child_start in children:
    q=pathlib.Path('/proc')/str(child)
    try:
        if active(q) and (q/'stat').read_text().split()[21]==child_start:
            assert os.readlink(q/'cwd')=={SOURCE_ROOT!r}
            os.kill(child,signal.SIGTERM);terminated.append(child)
    except FileNotFoundError:pass
print(json.dumps({{'source_pid':pid,'source_start_ticks':start,'source_stopped':True,
                  'interrupted_tail':tail,'terminated_owned_children':terminated,
                  'checkpoint_meta':{checkpoint['source']['meta']!r},
                  'scope':'Current unfinished epoch is replayed. Native checkpoint lacks mid-epoch/RNG restoration; no bitwise trajectory claim.'}}))
""", timeout=40))
        record("source_stopped", stopped)
        queue = monitor.load_queue(str(PROJECT))
        matches = [(server, task) for server, tasks in queue["gpu_queues"].items()
                   for task in tasks if task["id"] == "M201-BPS"]
        assert len(matches) == 1 and matches[0][0] == "server-6"
        task = matches[0][1]
        source_run = {key: task.get(key) for key in ("server", "gpu", "pid", "log", "launched")}
        task.setdefault("source_runs", []).append({**source_run, **stopped})
        queue["gpu_queues"]["server-6"].remove(task)
        queue["gpu_queues"].setdefault("server-4", []).append(task)
        task.update(server="server-4", gpu="0", pid=None, status="claiming",
                    launch_verified=False, launch_verification="migration_launch_pending",
                    resume_checkpoint=REMOTE + "/resume.pth",
                    resume_sha256=checkpoint["source"]["sha256"],
                    resume_meta=checkpoint["source"]["meta"])
        running = monitor.load_running(str(PROJECT))
        slot = running.get("server-6", {}).get("7", [])
        if isinstance(slot, str):
            slot = [slot]
        slot = [item for item in slot if item != "M201-BPS"]
        if slot:
            running["server-6"]["7"] = slot
        else:
            running.get("server-6", {}).pop("7", None)
        running.setdefault("server-4", {})["0"] = ["M201-BPS"]
        monitor.save_queue(str(PROJECT), queue)
        monitor.save_running(str(PROJECT), running)
        exp = monitor.load_experiment(str(PROJECT), "M201-BPS")
        exp.update({key: task[key] for key in ("server", "gpu", "pid", "status", "launch_verified",
                                              "launch_verification", "resume_checkpoint", "resume_sha256", "resume_meta", "source_runs")})
        monitor.save_experiment(str(PROJECT), exp)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log = ROOT + "/logs/train_" + Path(CONFIG).stem + "_resume_" + timestamp + ".log"
        launched = json.loads(remote(TARGET, f"""
import fcntl,json,os,pathlib,subprocess
root=pathlib.Path({ROOT!r})
lease=open({TRAINING_LOCK!r},'a+')
fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
env=os.environ.copy()
env.update(CONDA_PREFIX='/home/songcl/.conda/envs/project_cluster',
           PYTHONPATH={ROOT + ':' + ROOT + '/framework/lib'!r},
           LD_LIBRARY_PATH='/home/songcl/.conda/envs/project_cluster/lib:/home/songcl/.conda/envs/project_cluster/lib/python3.10/site-packages/torch/lib',
           TMPDIR={REMOTE!r},PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
(root/'logs').mkdir(exist_ok=True)
assert not pathlib.Path({log!r}).exists()
cmd=[{PYTHON!r},'tools/train.py',{CONFIG!r},'--resume',{REMOTE + '/resume.pth'!r},'--gpu_ids','0','--num_gpus','1']
with open({log!r},'ab',buffering=0) as out:
    proc=subprocess.Popen(cmd,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,
                          start_new_session=True,pass_fds=(lease.fileno(),))
(root/'logs'/('.pid_'+pathlib.Path({CONFIG!r}).stem)).write_text(str(proc.pid))
print(json.dumps({{'pid':proc.pid,'log':{log!r},'command':cmd,'checkpoint_meta':{checkpoint['source']['meta']!r},
                  'launch_verified':False,'launch_verification':'pending_progress'}}))
""", timeout=30))
        record("launch", launched)
        task.update(status="running", pid=launched["pid"], log=launched["log"],
                    launch_verification="pending_progress",
                    migrated_at=datetime.now().astimezone().isoformat())
        exp.update({key: task[key] for key in ("status", "pid", "log", "launch_verification", "migrated_at")})
        exp.setdefault("history", []).append({"ts": task["migrated_at"], "action": "migrated_resume",
                                               "from_server": "server-6", "server": "server-4", "gpu": "0",
                                               "checkpoint_meta": checkpoint["source"]["meta"],
                                               "checkpoint_sha256": checkpoint["source"]["sha256"]})
        monitor.save_queue(str(PROJECT), queue)
        monitor.save_experiment(str(PROJECT), exp)
        print(json.dumps(launched))
    finally:
        lock.close()


def verify():
    import re
    launched = tick.load(BUNDLE / ("launch_retry.json" if (BUNDLE / "launch_retry.json").exists() else "launch.json"))
    result = json.loads(remote(TARGET, f"""
import json,os,pathlib,subprocess,time
p=pathlib.Path('/proc')/{str(launched['pid'])!r}
assert p.is_dir() and (p/'stat').read_text().split()[2]!='Z'
assert os.readlink(p/'cwd')=={ROOT!r}
cmd=(p/'cmdline').read_bytes().split(b'\\0')
assert {CONFIG.encode()!r} in cmd and b'--resume' in cmd
path=pathlib.Path({launched['log']!r})
def tail():
    with path.open('rb') as f:
        f.seek(max(0,path.stat().st_size-90000))
        return f.read().decode(errors='replace')
first=tail();time.sleep(8);second=tail()
assert 'Traceback (most recent call last)' not in second
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
compute=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
print(json.dumps({{'pid':{launched['pid']!r},'first_tail':first,'second_tail':second,'gpu':gpu,'compute':compute}}))
""", timeout=25))
    pattern = r"Train\[(\d+)/(\d+)\]:[^\r\n]*?\|\s*(\d+)/(\d+)"
    first = re.findall(pattern, result["first_tail"])
    second = re.findall(pattern, result["second_tail"])
    expected_epoch = launched["checkpoint_meta"]["epoch"] + 1
    passed = bool(first and second and int(first[-1][0]) == expected_epoch
                  and int(second[-1][0]) == expected_epoch and int(second[-1][2]) > int(first[-1][2]))
    report = {"pid": result["pid"], "gpu": result["gpu"], "compute": result["compute"],
              "first_step": first[-1] if first else None, "second_step": second[-1] if second else None,
              "expected_start_epoch": expected_epoch, "native_progress_verified": passed,
              "tail": result["second_tail"].replace("\r", "\n").splitlines()[-8:]}
    suffix = "progress" if passed else "progress_pending_" + datetime.now().strftime("%H%M%S")
    record(suffix, report)
    if not passed:
        print(json.dumps(report))
        raise RuntimeError("Native progress not yet confirmed; reconcile only, never relaunch")
    lock = monitor.acquire_lock(str(PROJECT))
    assert lock is not None
    try:
        queue = monitor.load_queue(str(PROJECT))
        task = next(task for task in queue["gpu_queues"]["server-4"] if task["id"] == "M201-BPS")
        assert task["pid"] == launched["pid"]
        task.update(launch_verified=True, launch_verification="training_progress")
        exp = monitor.load_experiment(str(PROJECT), "M201-BPS")
        exp.update(launch_verified=True, launch_verification="training_progress",
                   migration_progress_evidence="pipeline/diagnostic_bundles/" + BUNDLE.name + "/progress.json")
        monitor.save_queue(str(PROJECT), queue)
        monitor.save_experiment(str(PROJECT), exp)
    finally:
        lock.close()
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("deploy", "reconcile-deploy", "data-source", "data-target", "freeze", "validate", "validate-compat", "cutover", "verify"))
    args = parser.parse_args()
    guard()
    try:
        if args.stage == "deploy":
            deploy()
        elif args.stage == "reconcile-deploy":
            reconcile_deployment()
        elif args.stage == "data-source":
            data(SOURCE)
        elif args.stage == "data-target":
            data(TARGET)
        elif args.stage == "freeze":
            freeze()
        elif args.stage == "cutover":
            cutover()
        elif args.stage == "verify":
            verify()
        elif args.stage == "validate-compat":
            validate(compat=True)
        else:
            validate()
    except BaseException as exc:
        guard(0)
        failure = BUNDLE / ("failure_" + args.stage + "_" + datetime.now().strftime("%H%M%S") + ".json")
        tick.save(failure, {"token": TOKEN, "observed_at": datetime.now().astimezone().isoformat(),
                            "stage": args.stage, "error_type": type(exc).__name__, "error": str(exc)})
        raise
