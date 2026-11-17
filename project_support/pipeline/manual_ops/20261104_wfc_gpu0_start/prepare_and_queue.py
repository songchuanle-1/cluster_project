"""Human asks to start on GPU0: prepare original WFC and invoke canonical dispatch."""
import copy
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
import shlex,subprocess,sys
import yaml

ROOT=Path('D:/project/cluster_project'); P=ROOT/'pipeline'; OUT=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
THREAD='01a159c5-29ab-7a22-ba7f-e79174757253'; REQUEST='启动'; ID='M226-WFC'
NEW_ROOT='/data/songcl/Project/Cluster_project/Cluster_resume_wfc_20261104'
OLD_ROOT='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
sys.path.insert(0,str(SKILL)); import pipeline_monitor as mon,closure,cluster_resume
def now(): return datetime.now(timezone.utc).isoformat()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def save(p,v):
    t=p.with_name(p.name+'.wfc_start.tmp')
    with t.open('x',encoding='utf-8') as f: json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False); f.flush(); os.fsync(f.fileno())
    os.replace(t,p)
def guard():
    assert os.environ.get('CODEX_THREAD_ID')==THREAD and load(P/'execution_mode.json')==dict(mode='foreground',target_thread_id=THREAD)
    assert not (P/'headless/.foreground.lockdir').exists() and not (P/'headless/.tick_context_state.next.json').exists()
    assert sha(P/'goal.json')=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
CALLS=[]
def strict_ssh(host,user,command,timeout=8):
    assert (host,user)==('192.168.1.115','songcl'); guard()
    inventory='nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null'
    if command==inventory: command=command.replace('nvidia-smi ','nvidia-smi -i 0 ',1)
    launch='proc=subprocess.Popen(' in command and 'tools/train.py' in command
    if launch:
        wrapper="import socket;assert socket.gethostname()=='dl04-MS-7E06'\nimport fcntl,subprocess,os,sys\nos.environ['PYTHONDONTWRITEBYTECODE']='1'\nlocks=[]\nfor k in ('training','diagnostic','exclusive'):\n f=open('/tmp/cluster_project_gpu0_'+k+'.lock','a+b');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)\nr=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().split(',')\nassert r[0].strip()=='0' and r[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' and int(r[2])<1024 and int(r[3])<10\ncontexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()\nassert not any(line.split(',')[0].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' for line in contexts.splitlines()),'GPU0 context appeared before native command; no Popen issued'\np=subprocess.run(['bash','-lc',"+repr(command)+"],text=True,capture_output=True)\nsys.stdout.write(p.stdout);sys.stderr.write(p.stderr);sys.exit(p.returncode)"
        command='/usr/bin/python3 -B -c '+shlex.quote(wrapper)
    else:
        command='/usr/bin/python3 -B -c '+shlex.quote("import socket;assert socket.gethostname()=='dl04-MS-7E06'")+ ' && '+command
    cp=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',user+'@'+host,command],text=True,encoding='utf-8',capture_output=True,timeout=max(timeout,150))
    CALLS.append(dict(observed_at=now(),command=command,returncode=cp.returncode,stdout=cp.stdout,stderr=cp.stderr,launch_request=launch)); save(OUT/'transport_calls.json',CALLS)
    if cp.returncode: raise RuntimeError('Pinned SSH failed; preserve state, do not blindly retry: '+cp.stderr[-1200:])
    return cp.stdout.strip()
def main():
    guard(); lock=mon.acquire_lock(str(ROOT)); assert lock is not None
    previous_ssh=mon.ssh
    try:
        guard()
        for n in ('SERVERS.yaml','pipeline/queue.json','pipeline/running.json','pipeline/research_work.json','pipeline/codex_memory.md','pipeline/experiments/M226-WFC.json'):
            assert not (OUT/('before_'+n.replace('/','__'))).exists()
            (OUT/('before_'+n.replace('/','__'))).write_bytes((ROOT/n).read_bytes())
        queue=load(P/'queue.json'); task=next(t for t in queue['gpu_queues']['server-4'] if t['id']==ID); beforetask=copy.deepcopy(task)
        assert task['training_status']=='paused_by_user' and task['status']=='waiting' and str(task['gpu'])=='0' and not load(P/'running.json')['server-4']
        save(OUT/'human_request.json',dict(recorded_at=now(),source='direct_human_message',owning_thread_id=THREAD,human_request=REQUEST,
            preceding_instruction='可使用一张卡server4-gpu0',preceding_resource_authorization=ref(P/'authorizations/server4_gpu0_20261104.json'),
            operational_interpretation='Start one existing experiment on authorized GPU0. Select original GPU0 WFC full-state resume from saved epoch25 under original code94, YAML and parameters. LFT/M206 remain paused; GPU1 excluded.',
            exact_human_quote_only='启动'))
        constants=load(P/'diagnostic_bundles/tick_d94467a9/dual_original_run_observer/constants.json')
        manifest=load(P/'diagnostic_bundles/tick_9bb5908b/wfc_execution/native_manifest.json')
        oldproof=load(P/'manual_ops/20261101_dual_user_pause/checkpoint_confirmation.json')['data']
        ck=next(c for c in oldproof['checkpoints'] if c['id']==ID); checkpoint=next(c for c in ck['checkpoints'] if c['path'].endswith('/last.pth'))
        assert task['resume_from']==checkpoint['path'] and task['code_commit']==constants['WFC']['commit']
        params=dict(old_root=OLD_ROOT,old_head=constants['LFT_COMMIT'],remote_code_root=NEW_ROOT,code_commit=task['code_commit'],config=task['config'],
            resume_from=checkpoint['path'],checkpoint_sha256=checkpoint['sha256'],hashes=constants['WFC']['hashes'],
            deployed_yaml_sha=constants['DEPLOYED_YAML_SHA256'],assets=manifest['assets'],mappings=[('/home/songcl/data/data','/home/songcl/data/data'),('/home/songcl/3dres/project/cluster_project/Checkpoints','/data/songcl/Project/Cluster_project/Cluster_checkpoints')])
        save(OUT/'operation_plan.json',dict(recorded_at=now(),params=params,old_receipt=ref(P/'admissions/M226-WFC.json'),local_head='4457a46f9075f61e83340aa0f0af87d5bf4e986c',human_request=ref(OUT/'human_request.json')))
        payload='PARAMS='+repr(params)+'\n'+(OUT/'remote_prepare.py').read_text(encoding='utf-8')
        cp=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115',
            '/home/songcl/.conda/envs/project_cluster/bin/python -B -'],input=payload,text=True,encoding='utf-8',capture_output=True,timeout=180)
        prepared=dict(recorded_at=now(),returncode=cp.returncode,stdout=cp.stdout,stderr=cp.stderr)
        if cp.returncode==0: prepared['data']=json.loads(cp.stdout)
        save(OUT/'runtime_preparation_and_checkpoint.json',prepared); assert cp.returncode==0,cp.stderr[-1800:]
        print('Original WFC94 isolated directory and epoch25 full checkpoint verified; preparing canonical resume.',flush=True)
        sp=ROOT/'SERVERS.yaml'; original=sp.read_text(encoding='utf-8'); a=original.index('  server-4:'); b=original.index('  server-6:',a)
        block=original[a:b]; oldline='    remote_code_root: '+OLD_ROOT; assert block.count(oldline)==1
        new=original[:a]+block.replace(oldline,'    remote_code_root: '+NEW_ROOT)+original[b:]
        wanted=yaml.safe_load(original); wanted['servers']['server-4']['remote_code_root']=NEW_ROOT; assert yaml.safe_load(new)==wanted
        temp=sp.with_name('SERVERS.wfc_start.tmp'); temp.write_text(new,encoding='utf-8',newline='\n'); os.replace(temp,sp)
        server=mon.load_servers(str(ROOT))['server-4']; assert server['allowed_gpus']==[0] and server['dispatch_enabled'] and server['max_tasks_per_gpu']==1
        identity=dict(schema_version=1,purpose='cluster_native_resume',id=ID,config=task['config'],code_commit=task['code_commit'],server='server-4',gpu='0',remote_code_root=NEW_ROOT,resume_from=task['resume_from'],checkpoint_sha256=checkpoint['sha256'])
        grant=dict(identity,authorization_granted=True,source='human',human_request=REQUEST,recorded_at=now(),owning_thread_id=THREAD,
            human_request_evidence=ref(OUT/'human_request.json'),scope='Only selected original WFC full-state resume on GPU0 following direct start instruction; original code94/checkpoint25/protocol unchanged. This grant does not resume LFT/M206 or use GPU1.',
            original_runtime_root=OLD_ROOT,isolated_original_version_root=NEW_ROOT,old_receipt=ref(P/'admissions/M226-WFC.json'))
        gp=P/'authorizations/m226_resume_gpu0_20261104.json'; assert not gp.exists(); save(gp,grant)
        proof=dict(identity,cpu_inspection=prepared['data']['cpu_inspection'],observed_at=prepared['data']['observed_at'],evidence=[ref(OUT/'runtime_preparation_and_checkpoint.json')],partial_current_epoch_saved=False)
        save(OUT/'checkpoint_evidence.json',proof)
        task.update(training_status='waiting_resume',dispatch_phase='resume_waiting',resume_authorized=True,resume_authorization=ref(gp),resume_checkpoint_evidence=ref(OUT/'checkpoint_evidence.json'),
            requires_exclusive_ownership=True,launch_verified=False,launch_verification='waiting_full_resume',remote_code_root=NEW_ROOT,
            note='Direct human start on GPU0: same WFC94 full epoch25 resume in isolated original checkout; old4457 directory and checkpoint remain. GPU0 exclusively required; never overlap foreign process. LFT/M206 remain paused.')
        for k in ('dispatch_hold','admission_error','pid','log','launched','claimed_gpu'): task.pop(k,None)
        closure.admission(ROOT,task); cluster_resume.validate(ROOT,server,task,'0'); cluster_resume.verify_source(ROOT,ROOT/'Cluster',server,task,'0',strict_ssh)
        closure.validate_foreground_dispatch_budget(ROOT,queue,task)
        exp=load(P/'experiments/M226-WFC.json'); exp.update(status='waiting',training_status='waiting_resume',dispatch_phase='resume_waiting',resume_authorized=True,
            resume_from=task['resume_from'],resume_authorization=task['resume_authorization'],resume_checkpoint_evidence=task['resume_checkpoint_evidence'],remote_code_root=NEW_ROOT,
            launch_verified=False,launch_verification='waiting_full_resume')
        for k in ('dispatch_hold','pid','log','launched','claimed_gpu'): exp.pop(k,None)
        exp.setdefault('history',[]).append(dict(ts=now(),action='human_start_full_resume_queued',human_request=ref(OUT/'human_request.json'),authorization=ref(gp),from_checkpoint_epoch=25,expected_resume_start_epoch=26,original_runtime_root=OLD_ROOT,remote_code_root=NEW_ROOT))
        save(P/'experiments/M226-WFC.json',exp); mon.save_queue(str(ROOT),queue)
        work=load(P/'research_work.json'); c=next(c for c in work['candidates'] if c.get('experiment_id')==ID)
        c.update(stage='deployment',resume_stage='training',training_status='waiting_resume',human_hold=False,resume_authorized=True,required_gpu='0',required_server='server-4',resume_authorization=ref(gp),resume_checkpoint_evidence=ref(OUT/'checkpoint_evidence.json'),
            next_action='Direct human start authorizes original WFC94 checkpoint25 full resume on physicalGPU0 in isolated original94 checkout. Wait for real exclusive GPU0 vacancy; then canonical --resume and verify epoch26 increasing progress. Preserve LFT/M206 pauses and GPU1 ban; no foreign eviction or overlay.')
        c['evidence'].extend([ref(gp),ref(OUT/'human_request.json'),ref(OUT/'runtime_preparation_and_checkpoint.json')]); work['updated_at']=now(); work['next_action']=c['next_action']; save(P/'research_work.json',work)
        mon.ssh=strict_ssh; events=[]
        mon._process_queue(queue,'server-4',server['host'],server['user'],str(ROOT),set(),{'0'},events,max_tasks_per_gpu=1,allow_external_overlay=False,remote_code_root=NEW_ROOT,current_tasks=0)
        current=next(t for t in mon.load_queue(str(ROOT))['gpu_queues']['server-4'] if t['id']==ID)
        assert [t for t in load(P/'queue.json')['gpu_queues']['server-4'] if t['id']!=ID]==[t for t in load(OUT/'before_pipeline__queue.json')['gpu_queues']['server-4'] if t['id']!=ID]
        save(OUT/'dispatch_result.json',dict(recorded_at=now(),canonical_dispatch_invoked=True,task_after=current,events=events,running_after=mon.load_running(str(ROOT)),
            old_source_tree_unchanged=True,gpu1_used=False,signals_sent=False,training_retried=False,authorization=ref(gp),checkpoint_evidence=ref(OUT/'checkpoint_evidence.json'),
            verified_native_progress=current.get('status')=='running' and current.get('launch_verified') is True))
        print(json.dumps(dict(status=current['status'],training_status=current['training_status'],launch_verified=current.get('launch_verified'),pid=current.get('pid'),dispatch_hold=current.get('dispatch_hold'),events=events),ensure_ascii=False),flush=True)
    finally: mon.ssh=previous_ssh; lock.close()
if __name__=='__main__': main()
