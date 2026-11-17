"""Move the same frozen HDS experiment under its owning foreground lease."""
import argparse, ast, copy, hashlib, json, os, shlex, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN = '3c22e34d7205421387d37c5797f29a24'
CID = 'm95-hierarchical-mask-feature-path-audit'
DIAG = 'm202-server4-native-deployment-audit'
EXP = 'M202-HDS'
NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1'
CONFIG = f'configs/Quard/ctf_hcg_csort_hds_canon_r1/{NAME}.yaml'
COMMIT = '1400e0c3e580410e40e9b19634d321f0dc5e01b1'
PRIOR = 'pipeline/diagnostic_bundles/memory_trace_cc39552e325049f5b8ac15dd3e055b06'
REL = 'pipeline/diagnostic_bundles/hds_server4_3c22e34d'
BUNDLE = ROOT / REL
AUTH = 'pipeline/authorizations/hds_server4_fresh_start_20261016_3c22e34d.json'
OPTIONS = ['-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','-o','PasswordAuthentication=no']
os.environ.update(PROJECT_ROOT='D:/project', PYTHONDONTWRITEBYTECODE='1')
sys.path.insert(0,str(SKILL))
import closure, foreground_tick as tick, pipeline_monitor as monitor, yaml
def now(): return datetime.now(timezone.utc).isoformat()
def guard():
    o=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert o['token']==TOKEN and o['thread_id']==os.environ['CODEX_THREAD_ID']
    assert o['deadline_at']=='2026-10-16T09:59:08.113105+00:00'
    assert datetime.fromisoformat(o['deadline_at'])>datetime.now(timezone.utc)
    return o
def save(p,v):
    guard(); p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); tick.save(p,v)
def ev(p): return {'path':p,'sha256':tick.digest(ROOT/p)}
def add(c,*paths):
    for p in paths:
        if ev(p) not in c.setdefault('evidence',[]):c['evidence'].append(ev(p))
def remote(alias,cmd,source=None,timeout=90,check=True):
    assert alias in ('server-3','server-4')
    r=subprocess.run(['ssh',*OPTIONS,alias,cmd],input=source.encode('utf-8') if source is not None else None,capture_output=True,timeout=timeout)
    if check and r.returncode:raise RuntimeError(f'{alias}: {r.returncode}: {r.stderr.decode(errors="replace")[-1600:]}')
    return r
def remote_python(alias,program,env=False,timeout=90):
    if env:
        s=monitor.load_servers(str(ROOT))[alias]
        text=f"set -eu\nsource {shlex.quote(s['conda_source'])}\nconda activate {shlex.quote(s['conda_env'])}\ncd {shlex.quote(s['remote_code_root'])}\npython -B - <<'HDS_PROJECT_PY'\n"+program+'\nHDS_PROJECT_PY\n'
        r=remote(alias,'bash -s',text,timeout)
    else:
        python='/home/songcl/.conda/envs/3d-stmn/bin/python' if alias=='server-3' else '/home/songcl/.conda/envs/project_cluster/bin/python'
        r=remote(alias,python+' -B -',program,timeout)
    return r.stdout.decode('utf-8',errors='replace')
def verified_sources():
    assert closure.git(ROOT/'Cluster','rev-parse','HEAD')==COMMIT
    manifest=tick.load(ROOT/PRIOR/'independent_upload.json')['local_files']
    for item in manifest:assert tick.digest(ROOT/item['path'])==item['sha256'],item['path']
    assert tick.digest(ROOT/'Cluster/scripts/validate_pdc_20261009.py')=='00d58e60d96a61272d4c8719fbca85fab449252ea84311ee3af09be015b26c26'
    assert tick.digest(ROOT/'pipeline/goal.json')=='42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec'
    return manifest
def prepare():
    guard(); manifest=verified_sources(); assert not (ROOT/AUTH).exists()
    save(ROOT/AUTH,{'recorded_at':now(),'thread_id':os.environ['CODEX_THREAD_ID'],'token':TOKEN,'candidate_id':CID,'experiment_id':EXP,'user_quote':'嗯，那就移动到server4训练吧。','informed_context':'User was told server3 OOM at epoch1/step1896, PID gone and no checkpoint. Fresh start of SAME unchanged experiment is authorized, not a resume.','target':'server-4 physical GPU0','source_attempt_pid':40465,'source_commit':COMMIT,'source_files':manifest,'scope':'Placement/runtime only. Same revision2/config/seed1999/batch2/50epochs/max_iters70. No revision3, duplicate, tuning, eviction/reset, shared environment mutation, auxiliary reopening or scheduler change.'})
    plan={'recorded_at':now(),'hypothesis_id':DIAG,'hypothesis':'Exact admitted HDS can execute native loss/backward in server4 existing environment; placement may resolve server3 24GB failure.','matched_control':'Exact M95/HDS on frozen TRAIN [0,60] and [101,124], same frozen checkpoint/seed; unchanged arithmetic tolerances; native worker-count transport test.','tests':['Strict host/UUID, live occupation/original flock checks','ff-only exact source preserving dirty BPS YAML','frozen asset hashes','native full backward/point-path gradients and matched resource control','native data loading','canonical gated dispatch, increasing native steps and GPU UUID'],'reject_or_block':'Any drift, foreign lease, nonfinite/error/no-op or unmatched resource budget blocks deployment. Small cohorts do not establish whole-training capacity/efficacy.','authorization':ev(AUTH),'new_model_variant':False,'source_failure_scope':'deployment capacity, not hypothesis falsification'}
    save(BUNDLE/'deployment_prereg.json',plan)
    w=tick.load(ROOT/'pipeline/research_work.json'); assert not any(c['id']==DIAG for c in w['candidates'])
    w['candidates'].append({'id':DIAG,'stage':'diagnosis','research_role':'operational_deployment_diagnostic','parent_candidate_id':CID,'linked_experiment_id':EXP,'hypothesis':plan['hypothesis'],'matched_control':plan['matched_control'],'next_action':'Execute preregistered target native/runtime/resource tests; no new model/queue ID.','evidence':[ev(REL+'/deployment_prereg.json'),ev(AUTH)]})
    save(ROOT/'pipeline/research_work.json',w)
    print(json.dumps({'prepared':True,'candidate':DIAG,'same_experiment':EXP}))
def inspect():
    guard(); servers=monitor.load_servers(str(ROOT))
    t=next(t for t in monitor.load_queue(str(ROOT))['gpu_queues']['server-3'] if t['id']==EXP); assert t['pid']==40465
    raw=remote('server-3','cat '+shlex.quote(t['log'])).stdout; assert b'CUDA out of memory' in raw
    guard(); (BUNDLE/'server3_native_oom.log').write_bytes(raw)
    s=servers['server-3']
    code=f"""
import json,pathlib,subprocess
base=pathlib.Path({s['work_dir']!r})/{NAME!r}
runs=['20261016_135235','20261016_135959','20261016_141015']
print(json.dumps(dict(hostname=subprocess.check_output(['hostname'],text=True).strip(),pid_exists=pathlib.Path('/proc/40465').exists(),log_mtime=pathlib.Path({t['log']!r}).stat().st_mtime,checkpoints={{r:[str(p) for p in (base/r).rglob('*.pth')] for r in runs}},gpu=subprocess.check_output(['nvidia-smi','-i','1','--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip(),contexts=subprocess.check_output(['nvidia-smi','-i','1','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip())))
"""
    source=json.loads(remote_python('server-3',code)); assert source['hostname']=='sysu311-MS-7C59' and not source['pid_exists']
    assert all(not v for v in source['checkpoints'].values())
    source.update(recorded_at=now(),log=t['log'],raw_log=ev(REL+'/server3_native_oom.log'),last_steps=closure.steps(raw.decode(errors='replace'))[-4:],scope='Real whole-training OOM, not NVML cache alone; no checkpoint/optimizer state available.')
    save(BUNDLE/'server3_failure.json',source)
    s=servers['server-4']
    code=f"""
import fcntl,hashlib,json,pathlib,subprocess
root=pathlib.Path({s['remote_code_root']!r})
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
locks=[]
for p in sorted(pathlib.Path('/tmp').glob('cluster_project_gpu0*.lock')):
    try:
        with p.open('a+b') as h:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB)
        locks.append(dict(path=str(p),available=True))
    except BlockingIOError:locks.append(dict(path=str(p),available=False))
dirty=root/'configs/Quard/bps/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps.yaml'
print(json.dumps(dict(hostname='dl04-MS-7E06',gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip(),contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip(),head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),dirty_status=subprocess.check_output(['git','-C',str(root),'status','--porcelain','-uno'],text=True).strip(),dirty_bps_sha256=hashlib.sha256(dirty.read_bytes()).hexdigest(),flocks=locks,frozen_assets=[str(p) for p in (root.parent/'pipeline').glob('*/*m95*.pth')],pretrain_exists=pathlib.Path('/home/songcl/data/data/sp_unet_backbone.pth').is_file())))
"""
    target=json.loads(remote_python('server-4',code))
    assert 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' in target['gpu'] and not target['contexts']
    assert all(r['available'] for r in target['flocks']); target['recorded_at']=now(); save(BUNDLE/'server4_inventory.json',target)
    runtime=remote_python('server-4',"import json,os,pathlib,sys,torch; p=pathlib.Path(torch.__file__).parent/'bin/torch_shm_manager';print(json.dumps(dict(python=sys.executable,torch=torch.__version__,cuda=torch.version.cuda,cuda_initialized=torch.cuda.is_initialized(),manager=str(p),manager_executable=os.access(p,os.X_OK))))",env=True)
    save(BUNDLE/'server4_runtime.json',{'recorded_at':now(),'output':runtime})
    print(json.dumps({'source':source,'target':target,'runtime':runtime}))
def sync():
    guard(); manifest=verified_sources(); s=monitor.load_servers(str(ROOT))['server-4']; before=tick.load(BUNDLE/'server4_inventory.json')
    assert remote('server-4','hostname').stdout.decode().strip()=='dl04-MS-7E06'
    def ssh(host,user,cmd,timeout=60):
        assert host==s['host'] and user==s['user']; return remote('server-4',cmd,timeout=timeout).stdout.decode(errors='replace').strip()
    os.environ['GIT_SSH_COMMAND']='ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10 -o PasswordAuthentication=no'
    closure.safe_sync(ROOT,ROOT/'Cluster',s,ssh)
    files={i['path'].removeprefix('Cluster/'):i['sha256'] for i in manifest}
    code=f"""
import hashlib,json,pathlib,subprocess
root=pathlib.Path({s['remote_code_root']!r}); files={files!r}
actual={{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files}}; assert actual==files
dirty=root/'configs/Quard/bps/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps.yaml'
assert hashlib.sha256(dirty.read_bytes()).hexdigest()=={before['dirty_bps_sha256']!r}
print(json.dumps(dict(head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),files=actual,dirty_bps_preserved=True)))
"""
    result=json.loads(remote_python('server-4',code));result.update(recorded_at=now(),ff_only=True,source_commit=COMMIT);save(BUNDLE/'sync_verified.json',result)
    print(json.dumps({'synced':True,'commit':result['head'],'files':len(files),'dirty_bps_preserved':True}))
def reconcile():
    guard(); failure=tick.load(BUNDLE/'server3_failure.json'); assert not failure['pid_exists']
    lock=monitor.acquire_lock(str(ROOT)); assert lock is not None
    try:
        q=monitor.load_queue(str(ROOT)); task=next(t for t in q['gpu_queues']['server-3'] if t['id']==EXP)
        assert task['pid']==40465 and task['status']=='running'
        save(BUNDLE/'server3_task_before_reconcile.json',copy.deepcopy(task))
        original=monitor.pull_log
        monitor.pull_log=lambda *a,**k:str(BUNDLE/'server3_native_oom.log')
        events=[]
        try:
            monitor.finalize_task(str(ROOT),q,'server-3','192.168.1.120','songcl',task,NAME,'crashed',None,'1/50','1',task['log'],events)
        finally:monitor.pull_log=original
        exp=monitor.load_experiment(str(ROOT),EXP)
        exp.setdefault('attempt_history',[]).append({**copy.deepcopy(task),'terminal_status':'crashed_oom','evidence':ev(REL+'/server3_failure.json')})
        exp.setdefault('history',[]).append({'ts':now(),'action':'user_authorized_fresh_start_migration','target':'server-4 GPU0','authorization':ev(AUTH)})
        monitor.save_experiment(str(ROOT),exp)
        w=tick.load(ROOT/'pipeline/research_work.json');c=next(c for c in w['candidates'] if c['id']==CID)
        c.update(stage='deployment',next_action='Verify unchanged target-native gates and migrate SAME M202-HDS to authorized server4 GPU0. No surviving source process/checkpoint.')
        add(c,REL+'/server3_failure.json',REL+'/server3_task_before_reconcile.json',AUTH)
        save(ROOT/'pipeline/research_work.json',w)
        save(BUNDLE/'source_reconciled.json',{'recorded_at':now(),'source_pid_absent':True,'events':events,'canonical_finalizer':True,'foreign_pid_not_touched':77671,'no_duplicate_queue_entry':True})
    finally:lock.close()
    print(json.dumps({'source_reconciled':True,'same_experiment':EXP,'source_failure':'OOM; no checkpoint'}))
def assets():
    guard(); assert remote('server-4','hostname').stdout.decode().strip()=='dl04-MS-7E06'
    source='/sdc1/songcl/Project/Cluster_project/pipeline/server3_fallback_abdff23d/frozen_m95.pth'
    target='/data/songcl/Project/Cluster_project/pipeline/hds_server4_3c22e34d/frozen_m95.pth'
    expected='fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
    assert remote('server-3','sha256sum '+shlex.quote(source)).stdout.decode().split()[0]==expected
    code=f"import pathlib,json;p=pathlib.Path({target!r});p.parent.mkdir(parents=True,exist_ok=True);print(json.dumps(dict(exists=p.exists())))"
    existed=json.loads(remote_python('server-4',code))['exists']
    if not existed:
        subprocess.run(['scp','-3',*OPTIONS,'server-3:'+source,'server-4:'+target],check=True,timeout=300)
    actual=remote('server-4','sha256sum '+shlex.quote(target)).stdout.decode().split()[0]; assert actual==expected
    save(BUNDLE/'frozen_asset.json',{'recorded_at':now(),'source':source,'target':target,'sha256':actual,'checkpoint_role':'Frozen M95 diagnostic control only, NOT an M202 training resume checkpoint.'})
    print(json.dumps({'frozen_diagnostic_asset':True,'sha256':actual}))
def probe(condition):
    guard(); assert condition in ('baseline','candidate','transport')
    assert not (BUNDLE/(condition+'_attempt.json')).exists()
    s=monitor.load_servers(str(ROOT))['server-4']; verified_sources()
    path=BUNDLE/'target_native_probe.py'; text=path.read_text(encoding='utf-8');compile(text,str(path),'exec')
    dest='/data/songcl/Project/Cluster_project/pipeline/hds_server4_3c22e34d/target_native_probe.py'
    code=f"import pathlib,hashlib;p=pathlib.Path({dest!r});s={text!r}.encode();assert not p.exists() or p.read_bytes()==s;p.write_bytes(s);print(hashlib.sha256(p.read_bytes()).hexdigest())"
    digest=remote_python('server-4',code).strip();assert digest==tick.digest(path)
    script=(f"set -eu\nsource {shlex.quote(s['conda_source'])}\nconda activate {shlex.quote(s['conda_env'])}\ncd {shlex.quote(s['remote_code_root'])}\n"
        f"export PYTHONPATH={shlex.quote(s['remote_code_root']+':'+s['remote_code_root']+'/framework/lib')}\n"
        'export PYTHONDONTWRITEBYTECODE=1 CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0\n'
        'export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$CONDA_PREFIX/lib/python3.10/site-packages/torch/lib:${LD_LIBRARY_PATH:-}"\n'
        f"timeout --signal=TERM --kill-after=15 620 python -B {shlex.quote(dest)} {condition}\n")
    started=now();r=remote('server-4','bash -s',script,timeout=650,check=False)
    stdout=r.stdout.decode(errors='replace');stderr=r.stderr.decode(errors='replace')
    save(BUNDLE/(condition+'_attempt.json'),{'started_at':started,'finished_at':now(),'returncode':r.returncode,'stdout':stdout,'stderr':stderr,'probe_sha256':digest})
    rows=[json.loads(line.split('=',1)[1]) for line in stdout.splitlines() if line.startswith('HDS_SERVER4_NATIVE_RESULT=')]
    if rows:
        assert len(rows)==1;row=rows[0];row['attempt']=ev(REL+'/'+condition+'_attempt.json');save(BUNDLE/(condition+'_result.json'),row)
        print(json.dumps({k:v for k,v in row.items() if k!='train_rows'}))
        if row.get('train_rows'):print(json.dumps({'train_rows':[{k:v for k,v in row.items() if k!='gradient_norms'} for row in row['train_rows']]}))
    else:print(stdout[-2500:]);print(stderr[-4500:])
    if r.returncode:raise SystemExit(r.returncode)
def resume_assets():
    guard()
    source='/sdc1/songcl/Project/Cluster_project/pipeline/server3_fallback_abdff23d/frozen_m95.pth'
    target='/data/songcl/Project/Cluster_project/pipeline/hds_server4_3c22e34d/frozen_m95.pth'
    size=int(remote('server-4','stat -c %s '+shlex.quote(target)).stdout.decode())
    total=int(remote('server-3','stat -c %s '+shlex.quote(source)).stdout.decode())
    assert 0<size<total==936269892
    save(BUNDLE/'asset_copy_timeout.json',{'recorded_at':now(),'timeout_seconds':300,'partial_bytes':size,'total_bytes':total,'native_use_before_hash':False})
    prefix=remote('server-4','sha256sum '+shlex.quote(target)).stdout.decode().split()[0]
    expected_prefix=remote('server-3',f'head -c {size} '+shlex.quote(source)+' | sha256sum').stdout.decode().split()[0]
    assert prefix==expected_prefix
    writer=f"import pathlib,sys,shutil;p=pathlib.Path({target!r});assert p.parent.resolve()==pathlib.Path('/data/songcl/Project/Cluster_project/pipeline/hds_server4_3c22e34d').resolve();assert p.stat().st_size=={size};f=p.open('ab');shutil.copyfileobj(sys.stdin.buffer,f,1024*1024);f.close();assert p.stat().st_size=={total}"
    sender=subprocess.Popen(['ssh',*OPTIONS,'server-3',f'tail -c +{size+1} '+shlex.quote(source)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    receiver=subprocess.Popen(['ssh',*OPTIONS,'server-4','/home/songcl/.conda/envs/project_cluster/bin/python -B -c '+shlex.quote(writer)],stdin=sender.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    sender.stdout.close()
    try:
        out,err=receiver.communicate(timeout=300);srcerr=sender.communicate(timeout=20)[1]
        assert receiver.returncode==sender.returncode==0,(err,srcerr)
    finally:
        for child in (sender,receiver):
            if child.poll() is None:child.kill();child.communicate()
    actual=remote('server-4','sha256sum '+shlex.quote(target)).stdout.decode().split()[0]
    assert actual=='fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
    save(BUNDLE/'frozen_asset.json',{'recorded_at':now(),'source':source,'target':target,'sha256':actual,'verified_partial_prefix_sha256':prefix,'resumed_from_bytes':size,'checkpoint_role':'Frozen M95 diagnostic only, NOT M202 resume.'})
    print(json.dumps({'frozen_asset_verified':True,'sha256':actual,'resumed_from_bytes':size}))
def launch_guard_source(server,manifest):
    config=yaml.safe_load((ROOT/'Cluster'/CONFIG).read_text(encoding='utf-8'))
    policy=tick.load(ROOT/'pipeline/closure_policy.json')
    mappings=[(m['source'],server[m['server_key']].rstrip('/')) for m in policy['path_mappings']]
    def adapt(v):
        if isinstance(v,dict):return {k:adapt(x) for k,x in v.items()}
        if isinstance(v,list):return [adapt(x) for x in v]
        if isinstance(v,str):
            for a,b in mappings:v=v.replace(a,b)
        return v
    expected=adapt(config)
    model_files={x['path'].removeprefix('Cluster/'):x['sha256'] for x in manifest if x['path'].endswith('.py')}
    return f'''"""Project-only early GPU0 binding and lifetime original exclusive locks."""
import os
os.environ.update(CUDA_DEVICE_ORDER='PCI_BUS_ID',CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
import fcntl,hashlib,json,pathlib,subprocess,sys,yaml
from datetime import datetime,timezone
root=pathlib.Path({server['remote_code_root']!r})
assert pathlib.Path.cwd().resolve()==root.resolve()
assert sys.argv[1:]==['tools/train.py',{CONFIG!r},'--gpu_ids','0','--num_gpus','1']
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
handles=[]
for name in ('training','diagnostic','exclusive'):
    h=open('/tmp/cluster_project_gpu0_'+name+'.lock','a+b')
    fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);os.set_inheritable(h.fileno(),True);handles.append(h)
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
parts=[p.strip() for p in gpu.split(',')]
assert parts[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
assert int(parts[2])<1000 and int(parts[3])>=30000 and int(parts[4])<10
assert not subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
for p,d in {model_files!r}.items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==d,p
actual=yaml.safe_load((root/{CONFIG!r}).read_text());assert actual=={expected!r}
assert hashlib.sha256(pathlib.Path(actual['train']['pretrain']).read_bytes()).hexdigest()=='a6f400bcf9bd722230d16ea7c3424b0d7658730126df604f67b4cccf42e25c1f'
assert pathlib.Path(actual['model']['data_root']).is_dir()
print('HDS_GPU_LEASE='+json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),gpu=gpu,physical_gpu=0,flocks=3,fresh_start=True,source_commit={COMMIT!r})),flush=True)
import runpy,torch
manager=pathlib.Path(torch.__file__).parent/'bin/torch_shm_manager';assert os.access(manager,os.X_OK)
dummy=torch.zeros(1,device='cuda');torch.cuda.synchronize()
own=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader,nounits'],text=True)
rows=[r for r in own.splitlines() if int(r.split(',')[0])==os.getpid()]
assert len(rows)==1 and 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' in rows[0]
del dummy
print('HDS_RUNTIME_READY='+json.dumps(dict(torch=torch.__version__,cuda=torch.version.cuda,physical_gpu0_confirmed=True,project_only_guard=True,shared_environment_modified=False)),flush=True)
sys.argv=sys.argv[1:]
runpy.run_path(sys.argv[0],run_name='__main__')
'''
class InsertGuard(ast.NodeTransformer):
    def __init__(self,path):self.path=path;self.count=0
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='subprocess' and node.func.attr=='Popen':
            argv=node.args[0];assert isinstance(argv,ast.List) and argv.elts[0].value=='python' and argv.elts[1].value=='tools/train.py'
            argv.elts.insert(1,ast.Constant(self.path));self.count+=1
        return node
def admit_dispatch(decision):
    guard(); manifest=verified_sources()
    baseline=tick.load(BUNDLE/'baseline_result.json');candidate=tick.load(BUNDLE/'candidate_result.json');transport=tick.load(BUNDLE/'transport_result.json')
    assert all(r['passed'] for r in (baseline,candidate,transport))
    prefix=tick.load(BUNDLE/'prefix_result.json');assert prefix['check_count']==prefix['passed']==20 and not prefix['failures']
    assert baseline['parameters']==candidate['parameters']==157484090
    assert all(len(r['train_rows'])==2 for r in (baseline,candidate))
    comparisons=[]
    for a,b in zip(baseline['train_rows'],candidate['train_rows']):
        assert a['scan_ids']==b['scan_ids'] and a['ann_ids']==b['ann_ids'] and a['batch_offsets']==b['batch_offsets']
        ratio=b['peak_allocated_bytes']/a['peak_allocated_bytes']-1; assert ratio<=.15
        comparisons.append({'pair':a['pair'],'baseline_peak':a['peak_allocated_bytes'],'candidate_peak':b['peak_allocated_bytes'],'increase':ratio})
    inference_ratio=candidate['inference']['peak_allocated_bytes']/baseline['inference']['peak_allocated_bytes']-1
    assert inference_ratio<=.15
    w=tick.load(ROOT/'pipeline/research_work.json');c=next(c for c in w['candidates'] if c['id']==CID);d=next(c for c in w['candidates'] if c['id']==DIAG)
    assert len(c['revision_history'])==2 and all(r['result']=='passed' for r in c['revision_history'])
    review={'recorded_at':now(),'candidate_id':CID,'same_experiment':EXP,'same_code_commit':COMMIT,'same_revision_count':2,'matched_train_memory':comparisons,'matched_inference_memory_increase':inference_ratio,'matched_inference':[baseline['inference'],candidate['inference']],'native_loss_backward_two_pairs_each':True,'point_path_tensors_each':24,'transport':ev(REL+'/transport_result.json'),'source_oom':ev(REL+'/server3_failure.json'),'target_assets':ev(REL+'/pretrain_integrity.json'),'native_evidence':[ev(REL+'/baseline_result.json'),ev(REL+'/candidate_result.json')],'limitations':'Small frozen cohort only. Whole-training memory/benefit unknown. Source full-training OOM preserved, no source optimizer state or exact failed batch replay. FLOPs original source-bound exception unchanged; no new model or scientific claim.'}
    review['target_prefix_arithmetic_equivalence']=ev(REL+'/prefix_result.json')
    review['prefix_original_tolerance']=1e-6
    save(BUNDLE/'target_gate_review.json',review)
    c.setdefault('gate_history',[]).append({'recorded_at':now(),'reason':'New hardware/runtime review after real server3 full-training OOM','gates':copy.deepcopy(c['gates']),'evidence':[ev(REL+'/server3_failure.json')]})
    for gate in ('controls','native_backward','resources','independence','constraints'):
        c['gates'][gate]['evidence'].append(ev(REL+'/target_gate_review.json'))
    c['gates']['resources']['status']='Exact source-bound FLOPs exception retained. New target matched fixed-cohort memory within original+15% and native transport/backward passed. Full-training capacity is NOT guaranteed; source24GB OOM retained.'
    c.update(stage='admission',next_action='Canonical gated dispatch of SAME unchanged M202 on server4 physicalGPU0; verify native step growth and UUID.')
    d.update(stage='complete',failure_scope='implementation',result='Target-native fixed-cohort backward and resource/transport checks passed; no efficacy or full-training-capacity conclusion.',next_action='Use actual training/terminal evidence; this diagnostic is not another model/queue variant.')
    add(c,REL+'/target_gate_review.json',REL+'/sync_verified.json',AUTH,decision)
    add(d,REL+'/target_gate_review.json',REL+'/sync_verified.json',REL+'/frozen_asset.json',REL+'/transport_result.json')
    s=monitor.load_servers(str(ROOT))['server-4'];assert s['allowed_gpus']==[0] and s['dispatch_enabled'] and s['max_tasks_per_gpu']==1
    source=launch_guard_source(s,manifest);compile(source,'<server4-gpu0-guard>','exec')
    remote_guard='/data/songcl/Project/Cluster_project/pipeline/runtime/hds_gpu0_guard_3c22e34d.py'
    save(BUNDLE/'launch_guard_source.json',{'recorded_at':now(),'source':source,'remote':remote_guard,'sha256':hashlib.sha256(source.encode()).hexdigest()})
    code=f"import pathlib,hashlib;p=pathlib.Path({remote_guard!r});s={source!r}.encode();assert not p.exists() or p.read_bytes()==s;p.write_bytes(s);print(hashlib.sha256(p.read_bytes()).hexdigest())"
    assert remote_python('server-4',code).strip()==hashlib.sha256(source.encode()).hexdigest()
    receipt=tick.load(ROOT/'pipeline/admissions/M202-HDS_plan_reference_v2.json')
    receipt.update(recorded_at=now(),decision=ev(decision),gates=copy.deepcopy(c['gates']),target='server-4 physicalGPU0',fresh_start_authorization=ev(AUTH),target_gate_review=ev(REL+'/target_gate_review.json'),prior_admission=ev('pipeline/admissions/M202-HDS_plan_reference_v2.json'))
    receipt_path='pipeline/admissions/M202-HDS_server4_3c22e34d.json';assert not (ROOT/receipt_path).exists();save(ROOT/receipt_path,receipt)
    add(c,receipt_path);save(ROOT/'pipeline/research_work.json',w)
    old=tick.load(BUNDLE/'server3_task_before_reconcile.json')
    archived={k:v for k,v in old.items() if k!='launch_attempts'};archived.update(terminal_status='crashed_oom',evidence=ev(REL+'/server3_failure.json'))
    task={'id':EXP,'label':old['label'],'config':CONFIG,'status':'waiting','gpu':'0','server':'server-4','code_commit':COMMIT,'admission_receipt':receipt_path,'launch_attempts':[*old.get('launch_attempts',[]),archived],'admission_history':[*old.get('admission_history',[]),ev('pipeline/admissions/M202-HDS_plan_reference_v2.json')],'migration_authorization':ev(AUTH),'fresh_start':True}
    closure.admission(ROOT,task)
    original_ssh=monitor.ssh;original_launch=closure.safe_launch
    def checked(host,user,cmd,timeout=60):
        assert host==s['host'] and user==s['user'];return remote('server-4',cmd,timeout=timeout).stdout.decode(errors='replace').strip()
    def launch(project,target,item,gpu,ssh):
        assert target['name']=='server-4' and item['id']==EXP and str(gpu)=='0'
        def guarded(host,user,command,timeout=60):
            args=shlex.split(command);assert args[-3:-1]==['python','-c']
            transform=InsertGuard(remote_guard);tree=transform.visit(ast.parse(args[-1]));assert transform.count==1
            program=ast.unparse(ast.fix_missing_locations(tree));compile(program,'<guarded-canonical-launch>','exec')
            cmd=f"source {shlex.quote(target['conda_source'])} && conda activate {shlex.quote(target['conda_env'])} && python -B -c "+shlex.quote(program)
            return checked(host,user,cmd,timeout)
        return original_launch(project,target,item,gpu,guarded)
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        q=monitor.load_queue(str(ROOT));assert not any(t['id']==EXP for group in q['gpu_queues'].values() for t in group)
        q['gpu_queues'].setdefault('server-4',[]).append(task);monitor.save_queue(str(ROOT),q)
        monitor.ssh=checked;closure.safe_launch=launch;events=[]
        monitor._process_queue(q,'server-4',s['host'],s['user'],str(ROOT),set(),{'0'},events,max_tasks_per_gpu=1,allow_external_overlay=False,task_memory_mb=s['task_memory_mb'],remote_code_root=s['remote_code_root'],current_tasks=0,max_tasks_total=2)
    finally:
        monitor.ssh=original_ssh;closure.safe_launch=original_launch;lock.close()
        actual=next(t for t in monitor.load_queue(str(ROOT))['gpu_queues'].get('server-4',[]) if t['id']==EXP)
        save(BUNDLE/'dispatch_result.json',{'recorded_at':now(),'task':actual,'canonical_dispatcher':True,'no_repeated_preflight':True,'launch_guard':ev(REL+'/launch_guard_source.json')})
        w=tick.load(ROOT/'pipeline/research_work.json');c=next(c for c in w['candidates'] if c['id']==CID)
        c.update(stage='training' if actual.get('launch_verified') else 'deployment',next_action='Verify target native continuity/validation; do not duplicate launch or tune the frozen recipe.')
        add(c,REL+'/dispatch_result.json');save(ROOT/'pipeline/research_work.json',w)
    print(json.dumps({k:v for k,v in actual.items() if k not in ('launch_attempts','admission_history')}))
def prefix():
    owner=guard();assert not (BUNDLE/'prefix_attempt.json').exists()
    tree=ast.parse((BUNDLE/'target_native_probe.py').read_text(encoding='utf-8'))
    branch=next(n for n in tree.body if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Name) and n.test.left.id=='condition' and isinstance(n.test.comparators[0],ast.Constant) and n.test.comparators[0].value=='transport')
    index=next(i for i,n in enumerate(branch.orelse) if isinstance(n,ast.Expr) and ast.unparse(n).startswith('model.cuda().train()'))
    original=(ROOT/PRIOR/'revision2_controls.py').read_text(encoding='utf-8')
    remat=(ROOT/'Cluster/framework/model/Quard_model'/NAME/'rematerialization.py').read_text(encoding='utf-8')
    setup=f"FOREGROUND_TOKEN={TOKEN!r}\nFOREGROUND_DEADLINE={owner['deadline_at']!r}\nREMATERIALIZATION_SOURCE={remat!r}\nobservations=[]\nobserve=lambda stage: dict(stage=stage,**gpu())\n"
    branch.orelse=branch.orelse[:index+1]+ast.parse(setup+original+'\nraise SystemExit(0)\n').body
    source=ast.unparse(ast.fix_missing_locations(tree))+'\n';compile(source,'<target-prefix-controls>','exec')
    guard();path=BUNDLE/'target_prefix_controls.py';path.write_bytes(source.encode('utf-8'))
    dest='/data/songcl/Project/Cluster_project/pipeline/hds_server4_3c22e34d/target_prefix_controls.py'
    code=f"import pathlib,hashlib;p=pathlib.Path({dest!r});s={source!r}.encode();assert not p.exists() or p.read_bytes()==s;p.write_bytes(s);print(hashlib.sha256(p.read_bytes()).hexdigest())"
    assert remote_python('server-4',code).strip()==tick.digest(path)
    s=monitor.load_servers(str(ROOT))['server-4']
    script=(f"set -eu\nsource {shlex.quote(s['conda_source'])}\nconda activate {shlex.quote(s['conda_env'])}\ncd {shlex.quote(s['remote_code_root'])}\n"
        f"export PYTHONPATH={shlex.quote(s['remote_code_root']+':'+s['remote_code_root']+'/framework/lib')}\n"
        'export PYTHONDONTWRITEBYTECODE=1 CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0\n'
        'export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$CONDA_PREFIX/lib/python3.10/site-packages/torch/lib:${LD_LIBRARY_PATH:-}"\n'
        f"timeout --signal=TERM --kill-after=15 620 python -B {dest} baseline\n")
    r=remote('server-4','bash -s',script,timeout=650,check=False);out=r.stdout.decode(errors='replace');err=r.stderr.decode(errors='replace')
    save(BUNDLE/'prefix_attempt.json',{'recorded_at':now(),'returncode':r.returncode,'stdout':out,'stderr':err,'generated_source':ev(REL+'/target_prefix_controls.py'),'unchanged_controls_source':ev(PRIOR+'/revision2_controls.py')})
    rows=[json.loads(line.split('=',1)[1]) for line in out.splitlines() if line.startswith('HIER_NATIVE_RESULT=')]
    if rows:
        assert len(rows)==1;row=rows[0];row['attempt']=ev(REL+'/prefix_attempt.json');save(BUNDLE/'prefix_result.json',row)
        print(json.dumps({k:v for k,v in row.items() if k not in ('records','observations')}))
    else:print(out[-2000:]);print(err[-4500:])
    if r.returncode:raise SystemExit(r.returncode)
def observe():
    guard();s=monitor.load_servers(str(ROOT))['server-4'];q=monitor.load_queue(str(ROOT));t=next(t for t in q['gpu_queues']['server-4'] if t['id']==EXP)
    assert t.get('pid') and t.get('log');pid=int(t['pid'])
    code=f"""
import json,os,pathlib,re,subprocess
p=pathlib.Path('/proc/{pid}');log=pathlib.Path({t['log']!r})
with log.open('rb') as f:
    f.seek(0,2);size=f.tell();f.seek(max(0,size-24000));tail=f.read().decode(errors='replace')
with log.open('rb') as f:prefix=f.read(1600).decode(errors='replace')
steps=[list(map(int,r)) for r in re.findall(r'Train\\[(\\d+)/\\d+\\]:[^\\r\\n]*?\\|\\s*(\\d+)/\\d+',tail)]
contexts=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_memory','--format=csv,noheader,nounits'],text=True)
own=[r for r in contexts.splitlines() if int(r.split(',')[0])=={pid}]
fds=[]
if p.exists():
    for fd in (p/'fd').iterdir():
        try:link=os.readlink(fd)
        except OSError:continue
        if 'cluster_project_gpu0_' in link and link.endswith('.lock'):fds.append(link)
print(json.dumps(dict(pid={pid},alive=p.exists(),steps_last=steps[-8:],crash_markers=[m for m in ('Traceback','CUDA out of memory','RuntimeError') if m in tail],own_contexts=own,flock_fds=fds,lease_guard_present='HDS_GPU_LEASE=' in prefix,runtime_guard_present='HDS_RUNTIME_READY=' in prefix,gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip())))
"""
    r=json.loads(remote_python('server-4',code));r.update(recorded_at=now(),log=t['log'])
    r['verified']=bool(r['alive'] and not r['crash_markers'] and len({tuple(p) for p in r['steps_last']})>=2 and len(r['flock_fds'])==3 and len(r['own_contexts'])==1 and 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' in r['own_contexts'][0])
    stamp=datetime.now(timezone.utc).strftime('%H%M%S');path=REL+'/observation_'+stamp+'.json';save(ROOT/path,r)
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        if r['verified']:
            q=monitor.load_queue(str(ROOT));actual=next(t for t in q['gpu_queues']['server-4'] if t['id']==EXP);assert actual['pid']==pid
            actual.update(status='running',launch_verified=True,launch_verification='training_progress');actual.pop('dispatch_hold',None);monitor.save_queue(str(ROOT),q)
            exp=monitor.load_experiment(str(ROOT),EXP);exp.update(status='running',launch_verified=True,launch_verification='training_progress',server='server-4',gpu='0',pid=pid,log=t['log'],admission_receipt=actual['admission_receipt'])
            summary={k:exp.pop(k) for k in ('final_best','finished_at','log_local','epochs_final') if k in exp}
            if summary:exp.setdefault('historical_terminal_summaries',[]).append({'server':'server-3','summary':summary,'evidence':ev(REL+'/server3_failure.json')})
            monitor.save_experiment(str(ROOT),exp)
        w=tick.load(ROOT/'pipeline/research_work.json');c=next(c for c in w['candidates'] if c['id']==CID)
        c.update(stage='training' if r['verified'] else 'deployment',next_action='Monitor real native progress/validation and frozen post-training plan; no duplicate launch, model/config tuning, or efficacy claim.')
        add(c,path)
        held=[x for x in w['candidates'] if x.get('stage')=='blocked' and x.get('blocker_kind')=='human_authorization'];assert len(held)==4
        scope_path=REL+'/scope_disposition_'+stamp+'.json'
        save(ROOT/scope_path,{'recorded_at':now(),'verified_training':r['verified'],'held_ids':[x['id'] for x in held],'reason':'Four auxiliary scope holds remain, not GPU blocks or scientific falsification. User request is same-experiment migration, not duplicate filling. No claim that independent scientific routes were exhausted.','source_oom_preserved':True,'new_model_revisions':0,'new_model_variants':0})
        w['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':[CID,DIAG],'evidence':[ev(scope_path),ev(path)],'resume_condition':'Monitor this unchanged mainline training. Auxiliary candidates need explicit human scope authorization, not idle GPU; no claim of GPU exhaustion.','scope':'Only the remaining four human scope holds; target-native deployment diagnostic is complete.'}
        add(c,scope_path,REL+'/orchestration_failures.json')
        d=next(x for x in w['candidates'] if x['id']==DIAG);add(d,REL+'/orchestration_failures.json')
        save(ROOT/'pipeline/research_work.json',w)
    finally:lock.close()
    print(json.dumps(r))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','inspect','sync','reconcile','assets','resume_assets','probe','prefix','dispatch','observe'));p.add_argument('--condition',choices=('baseline','candidate','transport'));p.add_argument('--decision');a=p.parse_args()
    if a.action=='probe':probe(a.condition)
    elif a.action=='dispatch':admit_dispatch(a.decision)
    else:globals()[a.action]()
