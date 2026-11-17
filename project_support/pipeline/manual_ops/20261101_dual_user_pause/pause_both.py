import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import yaml

ROOT=Path('D:/project/cluster_project'); P=ROOT/'pipeline'; OUT=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
THREAD='01a159c5-29ab-7a22-ba7f-e79174757253'; REQUEST='先暂停这两个实验 停止使用'
sys.path.insert(0,str(SKILL)); import pipeline_monitor as pm
def now(): return datetime.now(timezone.utc).isoformat()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def evidence(p): return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def save(p,v):
    temp=p.with_name(p.name+'.dual_pause.tmp')
    with temp.open('x',encoding='utf-8') as f:
        json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False); f.flush(); os.fsync(f.fileno())
    os.replace(temp,p)
def guard():
    assert os.environ['CODEX_THREAD_ID']==THREAD
    assert load(P/'execution_mode.json')==dict(mode='foreground',target_thread_id=THREAD)
    assert not (P/'headless/.foreground.lockdir').exists()
    assert sha(P/'goal.json')=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
def main():
    guard(); lock=pm.acquire_lock(str(ROOT)); assert lock is not None,'Other writer active'
    try:
        guard()
        paths=['SERVERS.yaml','pipeline/queue.json','pipeline/running.json','pipeline/research_work.json','pipeline/codex_memory.md',
            'pipeline/experiments/M226-WFC.json','pipeline/experiments/M227-LFT.json']
        for relative in paths: (OUT/('before_'+relative.replace('/','__'))).write_bytes((ROOT/relative).read_bytes())
        save(OUT/'human_request.json',dict(recorded_at=now(),request=REQUEST,thread_id=THREAD,source='direct_human_message',
            scope='Pause M226-WFC and M227-LFT; cease use of server4 GPU0/1. No replacement, migration, diagnostic GPU execution or automatic resume. Preserve existing logs/checkpoints.'))
        q=load(P/'queue.json'); tasks=[t for t in q['gpu_queues']['server-4'] if t['id'] in ('M226-WFC','M227-LFT')]
        assert len(tasks)==2
        expected={'M226-WFC':(2085005,'105948793','0'),'M227-LFT':(2685912,'106767833','1')}
        for t in tasks:
            pid,start,gpu=expected[t['id']]; assert t['status']=='running' and t['pid']==pid and str(t['gpu'])==gpu
        originals=copy.deepcopy(tasks)
        auth=P/'authorizations'/'server4_all_gpu_user_pause_20261101.json'; assert not auth.exists()
        save(auth,dict(schema_version=1,purpose='cluster_resource_authorization',source='human',recorded_at=now(),
            human_request=REQUEST,owning_thread_id=THREAD,project='cluster_project',server='server-4',host='192.168.1.115',
            expected_hostname='dl04-MS-7E06',allowed_gpus=[],dispatch_enabled=False,authorization_granted=False,
            scope='User revokes current server4 GPU0/1 use until a later explicit instruction; pause both original tasks and prohibit substitutes, native GPU diagnostics, migration and automatic resume.',
            human_request_evidence=evidence(OUT/'human_request.json')))
        sp=ROOT/'SERVERS.yaml'; original=sp.read_text(encoding='utf-8')
        a=original.index('  server-4:'); b=original.index('  server-6:',a); block=original[a:b]
        block,n=re.subn(r'^    allowed_gpus: \[0, 1\].*$', '    allowed_gpus: []   # User 2026-11-01: pause both experiments and cease GPU use.',block,flags=re.M); assert n==1
        block,n=re.subn(r'^    dispatch_enabled: true$', '    dispatch_enabled: false',block,flags=re.M); assert n==1
        updated=original[:a]+block+original[b:]
        before=yaml.safe_load(original); after=yaml.safe_load(updated); wanted=copy.deepcopy(before)
        wanted['servers']['server-4'].update(allowed_gpus=[],dispatch_enabled=False); assert after==wanted
        temporary=sp.with_name('SERVERS.dual_pause.tmp'); temporary.write_text(updated,encoding='utf-8',newline='\n'); os.replace(temporary,sp)
        for t in tasks:
            t.update(dispatch_hold='Direct user pause: cease both GPU0/1 use; no relaunch, substitute, migration or automatic resume.',
                dispatch_phase='user_pause_stop_pending',pause_request=evidence(OUT/'human_request.json'),resume_authorized=False)
        save(P/'queue.json',q)
        print('Durable hold applied: server4 allowed_gpus=[], dispatch_enabled=false. Stopping only verified WFC/LFT original sessions.',flush=True)
        k=load(P/'diagnostic_bundles/tick_d94467a9/dual_original_run_observer/constants.json')
        uuids={'0':'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c','1':'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}
        params=dict(operation_id=OUT.name,request=REQUEST,head=k['LFT_COMMIT'],yaml_sha=k['DEPLOYED_YAML_SHA256'],uuids=uuids,
            targets=[dict(id=t['id'],pid=t['pid'],starttime=expected[t['id']][1],gpu=t['gpu'],uuid=uuids[str(t['gpu'])],config=t['config'],log=t['log'],
                hashes=k['WFC']['hashes'] if t['id']=='M226-WFC' else k['LFT_HASHES']) for t in originals])
        save(OUT/'stop_intent.json',dict(recorded_at=now(),params=params,source_script=evidence(OUT/'remote_pause.py')))
        payload='PARAMS='+repr(params)+'\n'+(OUT/'remote_pause.py').read_text(encoding='utf-8')
        cp=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'],
            input=payload,text=True,encoding='utf-8',capture_output=True,timeout=75)
        record=dict(observed_at=now(),returncode=cp.returncode,stdout=cp.stdout,stderr=cp.stderr)
        if cp.returncode==0: record['data']=json.loads(cp.stdout)
        save(OUT/'stop_confirmation.json',record)
        assert cp.returncode==0,cp.stderr[-2000:]
        stopped=record['data']; assert stopped['stop_confirmed'] and stopped['all_original_member_cuda_contexts_absent']
        run=load(P/'running.json'); work=load(P/'research_work.json')
        for t,orig in zip(tasks,originals):
            observed=next(r for r in stopped['targets'] if r['id']==t['id'])
            paused=dict(original_task=orig,paused_at=now(),reason=REQUEST,starttime=expected[t['id']][1],
                checkpoint_files=observed['checkpoint_files_before'],checkpoint_full_state_validation='NOT_YET_INSPECTED',
                partial_current_epoch_saved=False,stop_confirmation=evidence(OUT/'stop_confirmation.json'))
            t.update(status='waiting',training_status='paused_by_user',dispatch_phase='user_paused',paused_run=paused,paused_at=now(),
                launch_verified=False,launch_verification='user_paused',resume_authorized=False,resource_authorization=evidence(auth),
                note='Manual operational pause, not terminal scientific early-stop. Saved complete checkpoints/logs retained; current partial epoch is not saved. No automatic resume or replacement.')
            for key in ('pid','log','launched','claimed_gpu'): t.pop(key,None)
            assert run['server-4'][str(orig['gpu'])]==t['id']; del run['server-4'][str(orig['gpu'])]
            ep=P/'experiments'/f"{t['id']}.json"; exp=load(ep)
            for key in ('status','training_status','dispatch_phase','dispatch_hold','paused_run','paused_at','launch_verified','launch_verification','resume_authorized','resource_authorization'): exp[key]=copy.deepcopy(t[key])
            for key in ('pid','log','launched','claimed_gpu'): exp.pop(key,None)
            exp.setdefault('history',[]).append(dict(ts=now(),action='direct_user_pause_both_gpus',stop_confirmation=evidence(OUT/'stop_confirmation.json'),no_auto_resume=True))
            save(ep,exp)
            cand=next(c for c in work['candidates'] if c.get('experiment_id')==t['id'])
            cand.update(training_status='paused_by_user',human_hold=True,resume_authorized=False,paused_run=paused,
                next_action='Direct human instruction paused WFC/LFT and ceased all current GPU use. Preserve original admitted source/log/checkpoint. No automatic resume, migration, diagnostic GPU run or replacement; wait for later explicit instruction.')
            cand.setdefault('evidence',[]).extend([evidence(auth),evidence(OUT/'stop_confirmation.json')])
        work.update(latest_resource_authorization=evidence(auth),updated_at=now(),
            next_action='USER_PAUSED_ALL_CURRENT_GPU_USE: allowed server4 GPUs empty and dispatch disabled. WFC/LFT paused, M206 unchanged paused. NEC/MIC remain prepared/NOT_RUN and must not be substituted or run on GPUs. Await later explicit human instruction.')
        save(P/'queue.json',q); save(P/'running.json',run); save(P/'research_work.json',work)
        save(OUT/'operation_summary.json',dict(recorded_at=now(),status='BOTH_USER_PAUSED_GPU_USE_REVOKED',ids=[t['id'] for t in tasks],
            stopped_pids=[t['pid'] for t in originals],allowed_gpus=[],dispatch_enabled=False,contexts_after=stopped['contexts_after'],gpus_after=stopped['gpus_after'],
            resume_authorized=False,partial_current_epoch_saved=False,resource_authorization=evidence(auth),stop_confirmation=evidence(OUT/'stop_confirmation.json')))
        print(json.dumps(load(OUT/'operation_summary.json'),ensure_ascii=False),flush=True)
    finally: lock.close()
if __name__=='__main__': main()
