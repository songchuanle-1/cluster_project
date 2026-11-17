"""Execute only the human-authorized CPA-R1 run; do not fabricate scientific admission."""
import argparse
import ast
import hashlib
import time
from ops import *
import closure
import pipeline_monitor as monitor

AUTH=ROOT/'pipeline/authorizations/cpa_exploratory_20261019_72695a5d.json'
CODE=ROOT/'Cluster'
ID='M204-CPA'
SERVER=monitor.load_servers(str(ROOT))['server-4']

def transport(host,user,command,timeout=120):
    guard()
    assert host=='192.168.1.115' and user=='songcl'
    command='test "$(hostname)" = dl04-MS-7E06 && '+command
    value=run(['ssh',*SSH,user+'@'+host,command],timeout)
    if value.returncode:raise RuntimeError(value.stderr[-4000:])
    return value.stdout.strip()

def bind():
    auth=tick.load(AUTH)
    assert auth['authorized'] and auth['experiment_id']==ID and auth['maximum_training_launches']==1
    assert auth['goal_sha256']==GOAL and auth['scientific_admission'] is False
    commit=closure.git(CODE,'rev-parse','HEAD')
    for path,digest in auth['files'].items():
        assert tick.digest(CODE/path)==digest,path
        blob=subprocess.check_output(['git','-C',str(CODE),'show',commit+':'+path])
        assert hashlib.sha256(blob).hexdigest()==digest,path
    return auth,commit

def deploy():
    auth,commit=bind()
    assert closure.safe_sync(str(ROOT),str(CODE),SERVER,transport)
    raw=tick.load(PREVIOUS/'raw_key_revision1/native_manifest.json')
    program='''import json,hashlib,pathlib,yaml,subprocess
root=pathlib.Path(ROOT)
def sha(path):
 h=hashlib.sha256()
 with pathlib.Path(path).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==COMMIT
for path,digest in FILES.items():assert sha(root/path)==digest,path
config=root/CONFIG
cfg=yaml.safe_load(config.read_text())
assert cfg['train']['seed']==1999 and cfg['train']['epochs']==50 and cfg['lr_scheduler']['max_iters']==70
assert cfg['dataloader']['train']['batch_size']==2 and cfg['dataloader']['train']['num_workers']==4
def adapt(value):
 if isinstance(value,dict):return {k:adapt(v) for k,v in value.items()}
 if isinstance(value,list):return [adapt(v) for v in value]
 if isinstance(value,str):
  for old,new in MAPPINGS:value=value.replace(old,new)
 return value
runtime=adapt(cfg)
assert pathlib.Path(runtime['train']['pretrain']).is_file()
for split in ('train','val'):assert pathlib.Path(runtime['data'][split]['data_root']).is_dir()
config.write_text(yaml.safe_dump(runtime,sort_keys=False))
files={path:sha(root/path) for path in FILES}
files['tools/train.py']=sha(root/'tools/train.py')
files['framework/dataset/scannetv2.py']=sha(root/'framework/dataset/scannetv2.py')
assert files['framework/dataset/scannetv2.py']==DATASET_HASH
assert sha(runtime['train']['pretrain'])==PRETRAIN_HASH
assert sha(ANNOTATION)==ANNOTATION_HASH
print(json.dumps(dict(code_commit=COMMIT,config=CONFIG,runtime_files=files,pretrain=runtime['train']['pretrain'],pretrain_sha256=PRETRAIN_HASH,annotation=ANNOTATION,annotation_sha256=ANNOTATION_HASH,config_deployment_only=True)))
'''
    program='\n'.join(['ROOT='+repr(SERVER['remote_code_root']),'COMMIT='+repr(commit),'FILES='+repr(auth['files']),
        'CONFIG='+repr(auth['config']),'MAPPINGS='+repr([('/home/songcl/data/data',SERVER['data_root'].rstrip('/')),('/home/songcl/3dres/project/cluster_project/Checkpoints',SERVER['work_dir'].rstrip('/'))]),
        'DATASET_HASH='+repr(raw['assets']['dataset_source_sha256']),'PRETRAIN_HASH='+repr('a6f400bcf9bd722230d16ea7c3424b0d7658730126df604f67b4cccf42e25c1f'),
        'ANNOTATION='+repr(raw['assets']['annotation_path']),'ANNOTATION_HASH='+repr(raw['assets']['annotation_sha256']),program])
    command='source '+shlex.quote(SERVER['conda_source'])+' && conda activate '+shlex.quote(SERVER['conda_env'])+' && python -B -c '+shlex.quote(program)
    result=json.loads(transport(SERVER['host'],SERVER['user'],command))
    result.update(root=SERVER['remote_code_root'],authorization_path=STAGE+'/'+AUTH.name,authorization_sha256=tick.digest(AUTH),guard_sha256=tick.digest(OUT/'guarded_train.py'),scientific_admission=False,experiment_id=ID)
    save('runtime_manifest.json',result)
    stage=ssh('from pathlib import Path\nimport json\nPath('+repr(STAGE)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
    copied=run(['scp',*SSH,str(AUTH),str(OUT/'runtime_manifest.json'),str(OUT/'guarded_train.py'),'songcl@192.168.1.115:'+STAGE+'/'])
    assert copied.returncode==0,copied.stderr
    save('deployment.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'code_commit':commit,'safe_ff_sync':True,'authorization':evidence(AUTH),'runtime_manifest':evidence(OUT/'runtime_manifest.json'),'scientific_admission':False,'remote_stage':STAGE})
    advance([OUT/'deployment.json',OUT/'runtime_manifest.json',OUT/'guarded_train.py'],stage='deployment',experiment_id=ID,
        next_action='Start the single manually authorized guarded native CPA run;do not use a fabricated scientific receipt or change unresolved gates')
    print(json.dumps({'deployment':True,'commit':commit,'stage':stage,'config':auth['config']}))

def launch():
    auth,commit=bind()
    manifest=tick.load(OUT/'runtime_manifest.json')
    assert manifest['code_commit']==commit
    mutex=monitor.acquire_lock(str(ROOT))
    assert mutex is not None,'Project monitor lock busy;no launch'
    try:
        queue=monitor.load_queue(str(ROOT))
        assert not any(t.get('id')==ID for tasks in queue['gpu_queues'].values() for t in tasks),'Already registered;reconcile instead of relaunch'
        running=monitor.load_running(str(ROOT))
        assert not running.get('server-4',{}).get('0'),'Authorized GPU slot already registered'
        task={'id':ID,'candidate_id':CID,'config':auth['config'],'server':'server-4','gpu':'0','status':'claiming','label':'CPA-R1 coarse point attention (human-authorized exploration)',
          'code_commit':commit,'manual_exploratory_authorization':evidence(AUTH),'scientific_admission':False,
          'launch_authorization_mode':'human_exploratory_exception','automatic_restart':False,'requires_exclusive_ownership':True,
          'launch_verified':False,'launch_verification':'pending_progress','depends_on':[],'patience':10,
          'note':'One explicitly authorized exploration;diagnosis/semantic controls remain unpassed,revision1 remains inconclusive. No scientific PASS.'}
        queue.setdefault('gpu_queues',{}).setdefault('server-4',[]).append(task)
        monitor.save_queue(str(ROOT),queue)
        monitor.save_experiment(str(ROOT),dict(task,history=[]))
        running.setdefault('server-4',{})['0']=ID
        monitor.save_running(str(ROOT),running)
        log=SERVER['remote_code_root']+'/logs/train_'+Path(auth['config']).stem+'_manual_72695a5d.log'
        program='''import json,os,pathlib,subprocess,sys,hashlib,socket
assert socket.gethostname()=='dl04-MS-7E06'
root=pathlib.Path(ROOT)
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==COMMIT
stage=pathlib.Path(STAGE)
assert hashlib.sha256((stage/'runtime_manifest.json').read_bytes()).hexdigest()==MANIFEST_HASH
with (stage/'launch_claim.json').open('x') as f:json.dump({'experiment_id':'M204-CPA','authorized_one_launch':True},f)
env=os.environ.copy()
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
env['PYTHONPATH']=str(root)+':'+str(root/'framework/lib')+':'+env.get('PYTHONPATH','')
pyver='.'.join(str(v) for v in sys.version_info[:2])
env['LD_LIBRARY_PATH']=env['CONDA_PREFIX']+'/lib:'+env['CONDA_PREFIX']+'/lib/python'+pyver+'/site-packages/torch/lib:'+env.get('LD_LIBRARY_PATH','')
temp=root.parent/'pipeline/tmp'
temp.mkdir(parents=True,exist_ok=True)
env['TMPDIR']=str(temp)
(root/'logs').mkdir(exist_ok=True)
command=[sys.executable,'-u','-B',str(stage/'guarded_train.py'),'--manifest',str(stage/'runtime_manifest.json'),'tools/train.py',CONFIG,'--gpu_ids','0','--num_gpus','1']
with open(LOG,'xb',buffering=0) as out:
 process=subprocess.Popen(command,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
(root/'logs'/('.pid_'+pathlib.Path(CONFIG).stem)).write_text(str(process.pid))
print(json.dumps({'pid':process.pid,'log':LOG,'command':command}))
'''
        program='\n'.join(['ROOT='+repr(SERVER['remote_code_root']),'COMMIT='+repr(commit),'STAGE='+repr(STAGE),'CONFIG='+repr(auth['config']),'LOG='+repr(log),'MANIFEST_HASH='+repr(tick.digest(OUT/'runtime_manifest.json')),program])
        command='source '+shlex.quote(SERVER['conda_source'])+' && conda activate '+shlex.quote(SERVER['conda_env'])+' && python -B -c '+shlex.quote(program)
        result=json.loads(transport(SERVER['host'],SERVER['user'],command))
        assert isinstance(result['pid'],int) and result['log']==log
        task.update(pid=result['pid'],log=result['log'],status='running',launched=datetime.now(timezone.utc).isoformat())
        monitor.save_queue(str(ROOT),queue)
        monitor.save_experiment(str(ROOT),dict(task,history=[{'ts':task['launched'],'action':'human_authorized_exploratory_launch','gpu':'0'}]))
        save('launch.json',dict(result,observed_at=datetime.now(timezone.utc).isoformat(),scientific_admission=False,authorization=evidence(AUTH),launch_verified=False))
        advance([OUT/'launch.json'],next_action='Verify increasing native training steps for M204-CPA;PID alone is not success,no blind restart')
        print(json.dumps(result))
    finally:
        mutex.close()

def verify():
    task=monitor.load_experiment(str(ROOT),ID)
    assert task and task.get('pid') and task['manual_exploratory_authorization']==evidence(AUTH)
    before=transport(SERVER['host'],SERVER['user'],'tail -c 160000 '+shlex.quote(task['log']))
    passed=closure.verify_progress(SERVER,task,transport,wait_s=180)
    after=transport(SERVER['host'],SERVER['user'],'tail -c 160000 '+shlex.quote(task['log']))
    observed=ssh('''import json,subprocess,os
from pathlib import Path
pid=PID
live=Path('/proc/'+str(pid)).exists()
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert [s.strip() for s in gpu.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
print(json.dumps({'pid_alive':live,'gpu':gpu,'contexts':contexts}))
'''.replace('PID',str(task['pid'])))
    result={'observed_at':datetime.now(timezone.utc).isoformat(),'launch_verified':passed,'before_steps':closure.steps(before),'after_steps':closure.steps(after),'environment':observed,
      'guard_observed':'CPA_EXPLORATORY_STARTUP_GUARD=' in after,'traceback':'Traceback (most recent call last)' in after,'unstable_loss_skip':'Skipping backward due to unstable loss' in after,
      'log_tail':after[-18000:],'scientific_admission':False}
    save('progress_verification.json',result)
    assert passed and observed['pid_alive'] and not result['traceback'],'Training progress unverified;inspect exact PID/log,do not restart blindly'
    mutex=monitor.acquire_lock(str(ROOT));assert mutex is not None
    try:
        queue=monitor.load_queue(str(ROOT))
        current=next(t for t in queue['gpu_queues']['server-4'] if t['id']==ID)
        current.update(launch_verified=True,launch_verification='training_progress',launch_evidence=evidence(OUT/'progress_verification.json'))
        monitor.save_queue(str(ROOT),queue)
        exp=monitor.load_experiment(str(ROOT),ID)
        exp.update(launch_verified=True,launch_verification='training_progress',launch_evidence=evidence(OUT/'progress_verification.json'))
        exp['history'].append({'ts':result['observed_at'],'action':'native_training_steps_verified','steps':result['after_steps'][-4:]})
        monitor.save_experiment(str(ROOT),exp)
    finally:mutex.close()
    advance([OUT/'progress_verification.json'],stage='training',experiment_id=ID,
      gate_result='Human-authorized exploratory training with native progress verified;diagnosis/semantic controls remain unpassed,revision1 inconclusive,scientific efficacy unknown',
      next_action='Monitor M204-CPA native ScanReferVAL training and predeclared scene-level evaluation;no automatic restart or new variant from this authorization')
    print(json.dumps({key:value for key,value in result.items() if key!='log_tail'},ensure_ascii=False,indent=2))

parser=argparse.ArgumentParser()
parser.add_argument('phase',choices=['deploy','launch','verify'])
phase=parser.parse_args().phase
guard(240)
{'deploy':deploy,'launch':launch,'verify':verify}[phase]()
