import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from datetime import datetime, timezone, timedelta

PROJECT = Path('D:/project/cluster_project')
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN = 'fded20f5ab50468ea49b50da64bc7522'
THREAD = '01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
OUT = PROJECT / 'pipeline/diagnostic_bundles/m202_recovery_fded20f5'
ROOT = '/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b'
PYTHON = '/home/songcl/.conda/envs/project_cluster/bin/python'
NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1'
CONFIG = f'configs/Quard/ctf_hcg_csort_hds_canon_r1/{NAME}.yaml'
LOG = f'{ROOT}/logs/train_{NAME}_20261016_173436.log'
CHECKPOINT = f'/data/songcl/Project/Cluster_project/Cluster_checkpoints/{NAME}/20261016_173442/last.pth'
UUID = 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'


def now():
    return datetime.now(timezone.utc).isoformat()


def lease():
    owner = json.loads((PROJECT / 'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf-8'))
    assert owner['token'] == TOKEN and owner['thread_id'] == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    return owner


def write_json(path, value):
    lease()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def evidence(path):
    return {'path': path.relative_to(PROJECT).as_posix(),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def remote(program, timeout=120, python='/usr/bin/python3', env=None):
    environment = {'PYTHONDONTWRITEBYTECODE': '1', **(env or {})}
    command = shlex.join(['env', *[f'{key}={value}' for key, value in environment.items()],
                          python, '-B', '-c', program])
    return subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                           '-o', 'ConnectTimeout=10', 'server-4', command],
                          capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=timeout)


def snapshot():
    lease()
    program = """
import datetime,fcntl,hashlib,json,pathlib,re,socket,subprocess
root=pathlib.Path(ROOT)
assert socket.gethostname()=='dl04-MS-7E06'
run=lambda args: subprocess.check_output(args,text=True,timeout=20).strip()
gpu=run(['nvidia-smi','--id=0','--query-gpu=index,uuid,name,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'])
assert UUID in gpu
apps=run(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'])
own_apps=[line for line in apps.splitlines() if UUID in line]
processes=[]
for path in pathlib.Path('/proc').glob('[0-9]*/cmdline'):
    try: args=path.read_bytes().split(b'\\0')
    except OSError: continue
    if b'tools/train.py' in args and CONFIG.encode() in args:
        processes.append({'pid':int(path.parent.name),'args':[x.decode(errors='replace') for x in args if x]})
locks={}
for kind in ['training','diagnostic','exclusive']:
    path=pathlib.Path('/tmp/cluster_project_gpu0_'+kind+'.lock')
    with path.open('a+') as handle:
        try:
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            locks[kind]='available_at_snapshot'
            fcntl.flock(handle,fcntl.LOCK_UN)
        except BlockingIOError: locks[kind]='held'
log=pathlib.Path(LOG)
raw=log.read_bytes()
text=raw.decode('utf-8',errors='replace')
trace=text[text.rfind('Traceback'):] if 'Traceback' in text else ''
progress=re.findall(r'Train\\[(\\d+)/(\\d+)\\]:[^\\r\\n]*?\\|\\s*(\\d+)/(\\d+)',text)
metrics=re.findall(r'mIoU\\s*:\\s*([0-9.eE+-]+)',text)
checkpoint=pathlib.Path(CHECKPOINT)
files=[str(p.relative_to(root)) for p in (root/'framework/model/Quard_model'/NAME).glob('*.py')]
files.extend([CONFIG,'tools/train.py','framework/utils/utils.py'])
hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'hostname':socket.gethostname(),'gpu0':gpu,'gpu0_compute_apps':own_apps,
    'same_config_processes':processes,'old_pid_present':pathlib.Path('/proc/216566').exists(),
    'locks':locks,'native_log':{'path':str(log),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
    'traceback':trace[-14000:],'last_native_train':progress[-1] if progress else None,
    'validation_miou':metrics},
    'checkpoint':{'path':str(checkpoint),'bytes':checkpoint.stat().st_size,
    'mtime':datetime.datetime.fromtimestamp(checkpoint.stat().st_mtime,datetime.timezone.utc).isoformat(),
    'sha256':hashlib.sha256(checkpoint.read_bytes()).hexdigest()},
    'remote_code_commit':run(['git','-C',str(root),'rev-parse','HEAD']),
    'source_hashes':hashes}))
"""
    constants = '\n'.join(f'{key}={value!r}' for key, value in {
        'ROOT': ROOT, 'NAME': NAME, 'CONFIG': CONFIG, 'LOG': LOG,
        'CHECKPOINT': CHECKPOINT, 'UUID': UUID}.items())
    result = remote(constants + '\n' + program)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    write_json(OUT / 'failure_snapshot.json', data)
    lease()
    (OUT / 'failure_traceback.log').write_text(data['native_log']['traceback'], encoding='utf-8')
    print(json.dumps({key: value for key, value in data.items()
                      if key not in {'source_hashes', 'native_log'}}, ensure_ascii=False, indent=2))
    print(json.dumps(data['native_log'], ensure_ascii=False, indent=2))


def probe():
    lease()
    import yaml
    saved=json.loads((OUT/'failure_snapshot.json').read_text(encoding='utf-8'))
    hashes=saved['source_hashes']
    for name,digest in hashes.items():
        if name!=CONFIG:
            assert hashlib.sha256((PROJECT/'Cluster'/name).read_bytes()).hexdigest()==digest,name
    expected=yaml.safe_load((PROJECT/'Cluster'/CONFIG).read_text(encoding='utf-8'))
    expected['work_dir']='/data/songcl/Project/Cluster_project/Cluster_checkpoints'
    prefix='import hashlib,pathlib,yaml\n'
    prefix+=f'root=pathlib.Path({ROOT!r})\n'
    prefix+=f'expected_hashes={hashes!r}\n'
    prefix+='for name,digest in expected_hashes.items(): assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name\n'
    prefix+=f'assert yaml.safe_load((root/{CONFIG!r}).read_text())=={expected!r}\n'
    code=prefix+(OUT/'recovery_probe.py').read_text(encoding='utf-8')
    attempt=1+len(list(OUT.glob('probe_attempt_[0-9].json')))
    write_json(OUT/f'probe_intent_{attempt}.json',{'registered_at':now(),'preregistration':evidence(OUT/'recovery_prereg.md'),
        'script':evidence(OUT/'recovery_probe.py'),'source_equivalence_checked':True,
        'checkpoint':saved['checkpoint'],'timeout_seconds':600,'model_changes':0})
    result=remote(code,timeout=650,python=PYTHON,env={
        'LD_LIBRARY_PATH':'/home/songcl/.conda/envs/project_cluster/lib:/home/songcl/.conda/envs/project_cluster/lib/python3.10/site-packages/torch/lib',
        'PYTHONUNBUFFERED':'1'})
    write_json(OUT/f'probe_attempt_{attempt}.json',{'recorded_at':now(),'returncode':result.returncode,
        'stdout':result.stdout,'stderr':result.stderr})
    marker='M202_RECOVERY_RESULT='
    rows=[line[len(marker):] for line in result.stdout.splitlines() if line.startswith(marker)]
    if result.returncode==0 and len(rows)==1:
        data=json.loads(rows[0]);write_json(OUT/'probe_result.json',data)
        print(json.dumps({key:value for key,value in data.items() if key!='native_backward'},indent=2))
        print(json.dumps([{'pair':row['pair'],'loss':row['loss'],'active_gradients':row['point_path_gradient_count']} for row in data['native_backward']]))
    else:
        print(json.dumps({'returncode':result.returncode,'stderr':result.stderr[-7000:],'stdout_tail':result.stdout[-1500:]},ensure_ascii=False))
        raise SystemExit(1)


def reconcile():
    lease()
    import copy
    os.environ['PROJECT_ROOT']='D:/project'
    sys.path.insert(0,str(SKILL))
    import pipeline_monitor as monitor
    saved=json.loads((OUT/'failure_snapshot.json').read_text(encoding='utf-8'))
    result=json.loads((OUT/'probe_result.json').read_text(encoding='utf-8'))
    assert not saved['old_pid_present'] and not saved['same_config_processes']
    assert "TypeError: 'Parameter' object is not callable" in saved['native_log']['traceback']
    assert result['meta']['epoch']==7 and result['native_resume_executed']
    assert not (OUT/'reconciled.json').exists()
    raw=OUT/'crashed_native_stdout.log'
    transfer=subprocess.run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
        'server-4:'+LOG,str(raw)],capture_output=True,text=True,encoding='utf-8',timeout=120)
    assert transfer.returncode==0,transfer.stderr
    assert hashlib.sha256(raw.read_bytes()).hexdigest()==saved['native_log']['sha256']
    lock=monitor.acquire_lock(str(PROJECT));assert lock is not None
    try:
        q=monitor.load_queue(str(PROJECT))
        task=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M202-HDS')
        assert task['pid']==216566 and task['status']=='running' and task['log']==LOG
        write_json(OUT/'task_before_reconcile.json',copy.deepcopy(task))
        original=monitor.pull_log
        monitor.pull_log=lambda *args,**kwargs:str(raw)
        events=[]
        try:
            monitor.finalize_task(str(PROJECT),q,'server-4','192.168.1.115','songcl',
                task,NAME,'crashed',result['meta']['best_miou'],'8/50','0',LOG,events)
        finally:
            monitor.pull_log=original
        exp=monitor.load_experiment(str(PROJECT),'M202-HDS')
        exp.setdefault('attempt_history',[]).append({**copy.deepcopy(task),
            'terminal_status':'crashed_typeerror','evidence':evidence(OUT/'failure_snapshot.json'),
            'checkpoint':saved['checkpoint'],'last_native_step':[8,2998,4686]})
        exp.update(launch_verified=False,launch_verification='crashed_confirmed',
            best_miou_exact=result['meta']['best_miou'])
        monitor.save_experiment(str(PROJECT),exp)
        work=json.loads((PROJECT/'pipeline/research_work.json').read_text(encoding='utf-8'))
        candidate=next(c for c in work['candidates'] if c['id']=='m95-hierarchical-mask-feature-path-audit')
        candidate.update(stage='validation',failure_scope='implementation',
            next_action='Use the passed same-source native resume probe to attempt ONE bounded checkpoint resume of SAME M202 on server4 GPU0 through canonical gated dispatcher; original TypeError root cause remains unconfirmed.')
        for path in (OUT/'failure_snapshot.json',OUT/'failure_traceback.log',raw,OUT/'recovery_prereg.md',OUT/'probe_result.json'):
            item=evidence(path)
            if item not in candidate['evidence']:candidate['evidence'].append(item)
        write_json(PROJECT/'pipeline/research_work.json',work)
        write_json(OUT/'reconciled.json',{'recorded_at':now(),'canonical_finalizer':True,
            'events':events,'prior_attempt_preserved':True,'old_running_mapping_removed':True,
            'resume_checkpoint_sha256':saved['checkpoint']['sha256'],'root_cause':'UNCONFIRMED'})
    finally:
        lock.close()
    print(json.dumps({'dead_attempt_archived':True,'same_experiment':'M202-HDS','checkpoint_epoch':7}))


def dispatch():
    lease()
    import ast
    import copy
    os.environ['PROJECT_ROOT']='D:/project'
    sys.path.insert(0,str(SKILL))
    import closure
    import pipeline_monitor as monitor
    assert (OUT/'reconciled.json').is_file() and not (OUT/'dispatch_result.json').exists()
    probe_data=json.loads((OUT/'probe_result.json').read_text(encoding='utf-8'))
    assert probe_data['passed'] and probe_data['optimizer_steps']==0
    assert probe_data['model_optimizer_scheduler_exactly_restored']
    original_guard=json.loads((PROJECT/'pipeline/diagnostic_bundles/hds_server4_3c22e34d/launch_guard_source.json').read_text(encoding='utf-8'))
    tree=ast.parse(original_guard['source'])
    original_args=['tools/train.py',CONFIG,'--gpu_ids','0','--num_gpus','1']
    revised_args=original_args+['--resume',CHECKPOINT]
    changed=0
    for node in ast.walk(tree):
        if isinstance(node,ast.Assert) and isinstance(node.test,ast.Compare):
            test=node.test
            if len(test.comparators)==1 and isinstance(test.comparators[0],ast.List):
                try:value=ast.literal_eval(test.comparators[0])
                except (ValueError,TypeError):continue
                if value==original_args:
                    test.comparators[0]=ast.List(elts=[ast.Constant(x) for x in revised_args],ctx=ast.Load())
                    changed+=1
        if isinstance(node,ast.Call):
            for keyword in node.keywords:
                if keyword.arg=='fresh_start':keyword.value=ast.Constant(False)
    assert changed==1
    check=ast.parse(f"assert hashlib.sha256(pathlib.Path({CHECKPOINT!r}).read_bytes()).hexdigest()=={probe_data['checkpoint_sha256']!r}").body
    tree.body[6:6]=check
    source=ast.unparse(ast.fix_missing_locations(tree))+'\n'
    compile(source,'<same-source-resume-guard>','exec')
    guard_path='/data/songcl/Project/Cluster_project/pipeline/runtime/hds_gpu0_resume_fded20f5.py'
    write_json(OUT/'resume_guard.json',{'recorded_at':now(),'remote':guard_path,
        'source':source,'sha256':hashlib.sha256(source.encode()).hexdigest(),
        'prior_guard_sha256':original_guard['sha256'],'argument_only_resume_adaptation':True,
        'native_model_train_utils_modified':False,'checkpoint_sha256':probe_data['checkpoint_sha256']})
    upload=f"import pathlib,hashlib;p=pathlib.Path({guard_path!r});data={source.encode()!r};assert not p.exists() or p.read_bytes()==data;p.write_bytes(data);print(hashlib.sha256(p.read_bytes()).hexdigest())"
    result=remote(upload)
    assert result.returncode==0 and result.stdout.strip()==hashlib.sha256(source.encode()).hexdigest(),result.stderr
    server=monitor.load_servers(str(PROJECT))['server-4']
    assert server['allowed_gpus']==[0] and server['dispatch_enabled']
    decision=monitor.log_decision(str(PROJECT),'other',
        'M202原进程TypeError中断；同源码原生resume及固定TRAIN反向已核验，是否恢复同一实验？',
        '归档原故障后，仅在server4物理GPU0对同一M202执行一次epoch7检查点原生resume；不改模型、协议、修订或阈值。',
        '模型、优化器、调度器精确恢复且参数身份保留；历史TypeError未重现，根因仍未知。不是修复成功或精确随机状态重放。',
        evidence(OUT/'probe_result.json')['path']+'; '+evidence(OUT/'failure_snapshot.json')['path'])
    receipt=json.loads((PROJECT/'pipeline/admissions/M202-HDS_server4_3c22e34d.json').read_text(encoding='utf-8'))
    receipt.update(recorded_at=now(),decision=evidence(Path(decision)),
        prior_admission=evidence(PROJECT/'pipeline/admissions/M202-HDS_server4_3c22e34d.json'),
        native_resume={'path':CHECKPOINT,'sha256':probe_data['checkpoint_sha256'],
        'start_epoch':8,'best_miou':probe_data['meta']['best_miou'],'epochs_no_improve':0,
        'runtime_guard':evidence(OUT/'resume_guard.json'),
        'probe':evidence(OUT/'probe_result.json'),'exact_stochastic_replay':False})
    receipt['gates']['native_backward']['evidence'].append(evidence(OUT/'probe_result.json'))
    receipt['gates']['resources']['evidence'].append(evidence(OUT/'failure_snapshot.json'))
    receipt['gates']['constraints']['evidence'].append(evidence(OUT/'recovery_prereg.md'))
    receipt_path=PROJECT/'pipeline/admissions/M202-HDS_resume_fded20f5.json'
    write_json(receipt_path,receipt)
    old=json.loads((OUT/'task_before_reconcile.json').read_text(encoding='utf-8'))
    task={key:copy.deepcopy(old[key]) for key in ('id','label','config','code_commit')}
    task.update(status='waiting',server='server-4',gpu='0',admission_receipt=receipt_path.relative_to(PROJECT).as_posix(),
        resume_checkpoint=CHECKPOINT,resume_checkpoint_sha256=probe_data['checkpoint_sha256'],
        launch_attempts=[*copy.deepcopy(old.get('launch_attempts',[])),
            {**copy.deepcopy(old),'terminal_status':'crashed_typeerror','evidence':evidence(OUT/'failure_snapshot.json')}],
        admission_history=[*copy.deepcopy(old.get('admission_history',[])),
            evidence(PROJECT/'pipeline/admissions/M202-HDS_server4_3c22e34d.json')],
        fresh_start=False,recovery_attempt=1)
    closure.admission(PROJECT,task)
    def checked(host,user,command,timeout=60):
        assert host==server['host'] and user==server['user']
        response=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
            '-o','ConnectTimeout=10','server-4',command],capture_output=True,text=True,
            encoding='utf-8',errors='replace',timeout=timeout)
        assert response.returncode==0,response.stderr
        return response.stdout.strip()
    original_ssh=monitor.ssh
    original_launch=closure.safe_launch
    class ResumeGuard(ast.NodeTransformer):
        count=0
        def visit_Call(self,node):
            self.generic_visit(node)
            if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='subprocess' and node.func.attr=='Popen':
                argv=node.args[0]
                assert isinstance(argv,ast.List) and argv.elts[0].value=='python' and argv.elts[1].value=='tools/train.py'
                argv.elts.insert(1,ast.Constant(guard_path))
                argv.elts.extend([ast.Constant('--resume'),ast.Constant(CHECKPOINT)])
                self.count+=1
            return node
    def launch(project,target,item,gpu,ssh):
        assert target['name']=='server-4' and item['id']=='M202-HDS' and str(gpu)=='0'
        def guarded(host,user,command,timeout=60):
            args=shlex.split(command)
            assert args[-3:-1]==['python','-c']
            transform=ResumeGuard()
            program=transform.visit(ast.parse(args[-1]))
            assert transform.count==1
            code=ast.unparse(ast.fix_missing_locations(program))
            command=f"source {shlex.quote(target['conda_source'])} && conda activate {shlex.quote(target['conda_env'])} && python -B -c "+shlex.quote(code)
            return checked(host,user,command,timeout)
        return original_launch(project,target,item,gpu,guarded)
    lock=monitor.acquire_lock(str(PROJECT));assert lock is not None
    try:
        q=monitor.load_queue(str(PROJECT))
        assert not any(t['id']=='M202-HDS' for group in q['gpu_queues'].values() for t in group)
        q['gpu_queues']['server-4'].append(task)
        monitor.save_queue(str(PROJECT),q)
        monitor.ssh=checked
        closure.safe_launch=launch
        events=[]
        monitor._process_queue(q,'server-4',server['host'],server['user'],str(PROJECT),
            set(),{'0'},events,max_tasks_per_gpu=1,allow_external_overlay=False,
            task_memory_mb=server['task_memory_mb'],remote_code_root=server['remote_code_root'],
            current_tasks=0,max_tasks_total=2)
    finally:
        monitor.ssh=original_ssh
        closure.safe_launch=original_launch
        lock.close()
        actual=next(t for t in monitor.load_queue(str(PROJECT))['gpu_queues']['server-4'] if t['id']=='M202-HDS')
        write_json(OUT/'dispatch_result.json',{'recorded_at':now(),'task':actual,
            'canonical_dispatcher':True,'preflight_repeated':False,'model_changes':0,
            'decision':evidence(Path(decision)),'admission_receipt':evidence(receipt_path)})
        work=json.loads((PROJECT/'pipeline/research_work.json').read_text(encoding='utf-8'))
        c=next(c for c in work['candidates'] if c['id']=='m95-hierarchical-mask-feature-path-audit')
        c.update(stage='training' if actual.get('launch_verified') else 'deployment',
            next_action='Verify SAME resumed PID/log native epoch8 step growth, saved best/patience lineage, expected GPU0 UUID and three lifetime locks; do not relaunch blindly.')
        c['evidence'].extend([evidence(OUT/'dispatch_result.json'),evidence(receipt_path)])
        write_json(PROJECT/'pipeline/research_work.json',work)
    print(json.dumps({key:actual.get(key) for key in ('id','status','pid','log','launch_verified','dispatch_hold')},ensure_ascii=False))


def scope():
    lease()
    work=json.loads((PROJECT/'pipeline/research_work.json').read_text(encoding='utf-8'))
    ids=['m95-native-relation-other-sign-conflict','m95-native-main-role-weight-precedence',
         'm95-native-secondary-positive-mass','m95-native-between-pair-support']
    records=[]
    for cid in ids:
        c=next(c for c in work['candidates'] if c['id']==cid)
        assert c['stage']=='blocked' and c['blocker_kind']=='human_authorization'
        records.append({key:c.get(key) for key in ('id','stage','blocker_kind','blocker','unblock_condition','next_action')})
    path=OUT/'scope_recheck.json'
    write_json(path,{'recorded_at':now(),'goal':evidence(PROJECT/'pipeline/goal.json'),
        'servers':evidence(PROJECT/'SERVERS.yaml'),'due_ids':records,
        'new_scope_authorization':False,'scope':'Existing auxiliary human scope holds remain. Not hypothesis rejection or a GPU availability claim. Mainline recovery has priority.'})
    for cid in ids:
        c=next(c for c in work['candidates'] if c['id']==cid)
        c['evidence'].append(evidence(path))
        c['retry_after']=(datetime.now(timezone.utc)+timedelta(hours=4)).isoformat()
    write_json(PROJECT/'pipeline/research_work.json',work)
    print(json.dumps({'scope_rechecked':4,'no_auxiliary_promotions':True}))


def observe():
    lease()
    sys.path.insert(0,str(SKILL))
    os.environ['PROJECT_ROOT']='D:/project'
    import pipeline_monitor as monitor
    q=monitor.load_queue(str(PROJECT))
    task=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M202-HDS')
    assert task.get('pid') and task['log']!=LOG
    code=f"""
import datetime,json,pathlib,re,socket,subprocess
assert socket.gethostname()=='dl04-MS-7E06'
pid={task['pid']!r}
path=pathlib.Path('/proc')/str(pid)
text=pathlib.Path({task['log']!r}).read_text(errors='replace')
steps=re.findall(r'Train\\[(\\d+)/(\\d+)\\]:[^\\r\\n]*?\\|\\s*(\\d+)/(\\d+)',text)
lineage=re.findall(r'resume start_epoch:(\\d+),best_miou:([0-9.eE+-]+),epochs_no_improve:(\\d+)!',text)
fds=[]
if path.exists():
    for item in (path/'fd').iterdir():
        try:target=str(item.resolve(strict=True))
        except OSError:continue
        if target.startswith('/tmp/cluster_project_gpu0_') and target.endswith('.lock'):fds.append(target)
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert {UUID!r} in row
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'],text=True)
apps=[line for line in apps.splitlines() if {UUID!r} in line]
print(json.dumps({{'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'pid':pid,'alive':path.exists(),'log':{task['log']!r},'native_steps':steps[-12:],
    'resume_lineage':lineage,'lifetime_lock_fds':sorted(fds),'gpu0':row,'gpu0_apps':apps,
    'traceback_markers':[term for term in ['Traceback','CUDA out of memory','TypeError:','RuntimeError:'] if term in text],
    'guard_present':'HDS_GPU_LEASE=' in text,'runtime_ready':'HDS_RUNTIME_READY=' in text,
    'tail_if_not_started':text[-2500:] if not steps else ''}}))
"""
    response=remote(code)
    assert response.returncode==0,response.stderr
    data=json.loads(response.stdout)
    unique=sorted({tuple(map(int,row)) for row in data['native_steps']})
    lineage={(int(epoch),float(best),int(patience)) for epoch,best,patience in data['resume_lineage']}
    verified=bool(data['alive'] and len(unique)>=2 and unique[-1]>unique[0]
        and unique[-1][:2]==(8,50) and not data['traceback_markers']
        and len(set(data['lifetime_lock_fds']))==3 and data['guard_present'] and data['runtime_ready']
        and lineage=={(8,0.47346487641334534,0)}
        and data['gpu0_apps'] and all(int(line.split(',')[1])==task['pid'] for line in data['gpu0_apps']))
    data['native_resume_verified']=verified
    path=OUT/('observation_'+datetime.now(timezone.utc).strftime('%H%M%S')+'.json')
    write_json(path,data)
    if verified:
        lock=monitor.acquire_lock(str(PROJECT));assert lock is not None
        try:
            q=monitor.load_queue(str(PROJECT))
            current=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M202-HDS')
            assert current['pid']==task['pid'] and current['log']==task['log']
            current.update(status='running',launch_verified=True,launch_verification='training_progress',
                native_resume_verified=True,resume_progress_evidence=evidence(path))
            current.pop('dispatch_hold',None)
            monitor.save_queue(str(PROJECT),q)
            exp=monitor.load_experiment(str(PROJECT),'M202-HDS')
            if 'finished_at' in exp:
                summary={key:exp.pop(key) for key in ('final_best','finished_at','log_local','epochs_final') if key in exp}
                exp.setdefault('historical_terminal_summaries',[]).append({'server':'server-4','summary':summary,'evidence':evidence(OUT/'failure_snapshot.json')})
            exp.update(status='running',launch_verified=True,launch_verification='training_progress',
                native_resume_verified=True,resume_checkpoint=CHECKPOINT,
                resume_checkpoint_sha256='fe4301ec2607f0ee0604173ea31422ae91df8e15b082657c557955c2c4d67e6c',
                resume_progress_evidence=evidence(path),best_miou_exact=0.47346487641334534)
            monitor.save_experiment(str(PROJECT),exp)
            work=json.loads((PROJECT/'pipeline/research_work.json').read_text(encoding='utf-8'))
            c=next(c for c in work['candidates'] if c['id']=='m95-hierarchical-mask-feature-path-audit')
            c.update(stage='training',next_action='Monitor SAME unchanged resumed M202 on server4 GPU0; root cause of original TypeError remains unconfirmed. Preserve original failure, epoch7 lineage and frozen evaluation plan; no duplicate restart or tuning.')
            c['evidence'].append(evidence(path))
            write_json(PROJECT/'pipeline/research_work.json',work)
        finally:lock.close()
    print(json.dumps(data,ensure_ascii=False,indent=2))


def persist():
    lease()
    observations=[(path,json.loads(path.read_text(encoding='utf-8'))) for path in sorted(OUT.glob('observation_*.json'))]
    path,actual=observations[-1]
    assert actual['native_resume_verified']
    probe_data=json.loads((OUT/'probe_result.json').read_text(encoding='utf-8'))
    scope_data=json.loads((OUT/'scope_recheck.json').read_text(encoding='utf-8'))
    ids=[row['id'] for row in scope_data['due_ids']]
    work=json.loads((PROJECT/'pipeline/research_work.json').read_text(encoding='utf-8'))
    primary=next(c for c in work['candidates'] if c['id']=='m95-hierarchical-mask-feature-path-audit')
    assert primary['stage']=='training' and len(primary['revision_history'])==2
    for file in ('probe_attempt.json','probe_attempt_1.json','resume_guard.json','reconciled.json'):
        item=evidence(OUT/file)
        if item not in primary['evidence']:primary['evidence'].append(item)
    primary['evidence'].append(evidence(PROJECT/'pipeline/bugfixes/bugfix_20261017-003548.md'))
    work['design_cycle']={'stop_reason':'external_resource_blocked',
        'attempted_ids':[primary['id'],*ids],
        'evidence':[evidence(OUT/'scope_recheck.json'),evidence(path),evidence(OUT/'probe_result.json')],
        'resume_condition':'Monitor SAME resumed M202 and evaluate under unchanged frozen plan. The four auxiliary candidates require explicit scope restoration or an independently justified mainline-matched auxiliary need; elapsed retry or free GPU alone is insufficient.',
        'scope':'Only the four remaining human_authorization holds. Primary checkpoint recovery completed and is now verified training. Not a claim that every GPU is occupied or that independent scientific routes were exhausted.'}
    write_json(PROJECT/'pipeline/research_work.json',work)
    write_json(OUT/'execution_summary.json',{'recorded_at':now(),'snapshot_at':lease()['generated_at'],
        'scientific_status':'training; historical TypeError cause unknown; no new trained efficacy result',
        'execution_status':'POSTFLIGHT_NOT_YET_RUN','same_experiment':'M202-HDS',
        'native_resume_verified':True,'current_observation':evidence(path),
        'actual_output':{'same_experiment_resume_launches':1,'new_models':0,'new_candidates':0,
            'new_implementation_revisions':0,'passed_recovery_probe_runs':1,'fixed_train_groups':2,
            'unique_train_scenes':4,'train_expressions':16,'optimizer_steps_in_probes':0,
            'repeated_cuda_calls_in_passed_probe':48,'auxiliary_scope_rechecks':4,
            'new_validation_rounds':0},
        'orchestration_limitations':['Initial local GBK read failed before remote test; explicit UTF-8 fixed only collector.',
            'First remote probe reached final metadata serialization but failed on extra checkpoint time string; retained probe_attempt.json. Subsequent same frozen tests passed with serializer-only correction.'],
        'usage_scope':'Only begin-to-receipt local visible log window; excludes early reads/final reply. Current usage UNKNOWN until receipt. Cache already belongs to input and reasoning to output; not billing.'})
    steps=actual['native_steps']
    notes={'actions':[
        '实际后续观测时间 '+datetime.fromisoformat(actual['observed_at']).astimezone(timezone(timedelta(hours=8))).isoformat()+'（上海时间）。初始0-3段仅为begin快照；本段记录之后发生的变化。',
        '实证归档原PID216566已退出、TypeError异常及第8/50轮2998/4686步；原始日志10,070,812字节和epoch7 last.pth均有SHA256，标准finalizer已纠正旧running映射，所有失败保留。',
        '冻结模型/config、tools/train.py及cuda_cast未修改。实际gorilla.resume恢复epoch7/best0.47346487641334534/patience0；1163当前模型state项、642优化器state及调度器逐项精确匹配，两个原生provider已知额外非持久text buffer仍按原strict=False协议处理。',
        '一次有正式结果的恢复测试：48次原样model.cuda，参数对象身份保留；固定TRAIN两组/四场景/16表达的loss与backward通过，24个点云路径参数梯度均有限非零；优化器step为0。仅恢复可执行性，不证明TypeError根因、长期稳定性或精度收益。',
        '经标准门控dispatcher对同一M202执行1次原生--resume。实际PID1592337/server4物理GPU0；第8/50轮步数 '+steps[0][2]+'→'+steps[-1][2]+'/4686已增长，正确UUID和原始三把生命周期flock保持，无新异常。epoch8从头接续，不冒充丢失的中间batch/RNG精确重放。',
        '本轮产出：1个通过的检查点恢复诊断、1次同实验续训与进度核验、4项到期human scope hold复核；新增模型/候选/结构修订/验证轮次均为0。第一次诊断结果序列化失败及前置UTF-8问题保留，不计科学反证或修订。',
        '科学状态：当前M202最佳0.4735仍低于baseline0.4894/champion0.5020，目标0.5100；没有本轮新增验证结果。历史故障根因、全程峰值显存、场景配对置信区间和最终效果仍未知。',
        '收据用量仅覆盖本轮begin至receipt本地日志窗口，缺失/此刻最终值记未知，最终原始记录见收据；cache已含在input、reasoning已含在output，不重复相加，不是账单。'
        ],'decisions':[
        '保持同一稳定主线ID/M202、恰好2次已通过实现修订、原seed1999/batch2/workers4/50epochs/max_iters70、验证边界和精确源码FLOPs例外；没有扩大授权、改调度或恢复M201。',
        '不将本次原样恢复称为修复根因。若TypeError再次出现，保留新现场并调查，不盲目重启或绕过精确源码/修订限制；当前无需用户增加授权。',
        '余下4个辅助候选仍受human_authorization主线优先级hold；本轮外部阻塞收尾只指这些真实scope holds，不声称GPU耗尽或独立路线已穷尽。当前主线已确认训练，储备4/2、预算0，不凑新变体。',
        '完整六段报告与七段记忆在租约内保存；本段写入时postflight尚未运行，只有随后finish成功且核实匹配租约不存在，才能称本轮执行完成。'
        ]}
    write_json(OUT/'report_notes.json',notes)
    print(json.dumps({'notes_saved':True,'design_cycle_scope':'four auxiliary human holds only',
        'training_observation':evidence(path),'postflight':'not yet run'}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['snapshot','probe','reconcile','dispatch','scope','observe','persist'])
    args = parser.parse_args()
    globals()[args.action]()


if __name__ == '__main__':
    main()
