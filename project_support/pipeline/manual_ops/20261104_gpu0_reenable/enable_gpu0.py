"""Apply direct human GPU0 resource grant, without clearing experiment holds."""
import copy
from datetime import datetime,timezone
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
THREAD='01a159c5-29ab-7a22-ba7f-e79174757253'; REQUEST='可使用一张卡server4-gpu0'
sys.path.insert(0,str(SKILL)); import pipeline_monitor as pm
def now(): return datetime.now(timezone.utc).isoformat()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def save(p,v):
    temp=p.with_name(p.name+'.gpu0_reenable.tmp')
    with temp.open('x',encoding='utf-8') as f:
        json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False); f.flush(); os.fsync(f.fileno())
    os.replace(temp,p)
def guard():
    assert os.environ.get('CODEX_THREAD_ID')==THREAD
    assert load(P/'execution_mode.json')==dict(mode='foreground',target_thread_id=THREAD)
    assert not (P/'headless/.foreground.lockdir').exists()
    assert not (P/'headless/.tick_context_state.next.json').exists()
    assert sha(P/'goal.json')=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
PAYLOAD=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
from datetime import datetime,timezone
import json,subprocess
def run(a): return subprocess.check_output(a,text=True,timeout=15).strip()
inventory=run(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'])
r=[x.strip() for x in inventory.split(',')]
assert r[0]=='0' and r[1]=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=run(['nvidia-smi','-i','0','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'])
print(json.dumps(dict(observed_at=datetime.now(timezone.utc).isoformat(),hostname=socket.gethostname(),physical_gpu=0,
    inventory=inventory,contexts=contexts,empty_compute_context_list=not bool(contexts),
    runtime_head=run(['git','--no-optional-locks','-C','/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1','rev-parse','HEAD']),
    gpu1='NOT_QUERIED_NOT_AUTHORIZED',no_gpu_computation_or_signals=True)))
'''
def main():
    guard(); lock=pm.acquire_lock(str(ROOT)); assert lock is not None,'Other project writer active'
    try:
        guard()
        for name in ('SERVERS.yaml','pipeline/research_work.json','pipeline/codex_memory.md','pipeline/queue.json','pipeline/running.json'):
            (OUT/('before_'+name.replace('/','__'))).write_bytes((ROOT/name).read_bytes())
        save(OUT/'human_request.json',dict(recorded_at=now(),source='direct_human_message',thread_id=THREAD,request=REQUEST,
            scope='Only server4 physical GPU0 becomes usable for project work; GPU1 remains excluded. Resource grant does not erase separately paused experiment records.'))
        cp=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'],
            input=PAYLOAD,text=True,encoding='utf-8',capture_output=True,timeout=45)
        probe=dict(observed_at=now(),returncode=cp.returncode,stdout=cp.stdout,stderr=cp.stderr,payload_sha256=hashlib.sha256(PAYLOAD.encode()).hexdigest())
        if cp.returncode==0: probe['data']=json.loads(cp.stdout)
        save(OUT/'identity_and_gpu0_observation.json',probe)
        assert cp.returncode==0,cp.stderr[-1200:]
        sp=ROOT/'SERVERS.yaml'; old=sp.read_text(encoding='utf-8'); start=old.index('  server-4:'); end=old.index('  server-6:',start); block=old[start:end]
        block,n=re.subn(r'^    allowed_gpus: \[\].*$', '    allowed_gpus: [0]   # User 2026-11-04: only server4 GPU0 is available.',block,flags=re.M); assert n==1
        block,n=re.subn(r'^    dispatch_enabled: false$', '    dispatch_enabled: true',block,flags=re.M); assert n==1
        new=old[:start]+block+old[end:]; original=yaml.safe_load(old); expected=copy.deepcopy(original)
        expected['servers']['server-4'].update(allowed_gpus=[0],dispatch_enabled=True); assert yaml.safe_load(new)==expected
        auth=P/'authorizations/server4_gpu0_20261104.json'; assert not auth.exists()
        grant=dict(schema_version=1,authorized_at=now(),project='cluster_project',owning_thread_id=THREAD,
            authorization_source='Direct human instruction in owning chat',human_instruction=REQUEST,
            server='server-4',host='192.168.1.115',expected_hostname='dl04-MS-7E06',allowed_gpus_after=[0],
            allowed_gpus=[0],dispatch_enabled=True,physical_gpu_authorized=0,gpu_uuid='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',max_tasks_per_gpu=1,
            scope='Restore only physical GPU0 for current scoped project work under standing experiment-first authorization. GPU1 remains prohibited.',
            supersedes_only='2026-11-01 all-GPU resource exclusion for future GPU0 operations only; old records and experiment-specific pause holds are retained.',
            does_not_authorize=['Automatic removal of M226-WFC/M227-LFT/M206-CGCA individual human holds','GPU1 use or migration','Cold restart of an interrupted experiment','Goal, data, seed, schedule, source identity, gates, bans or scheduler changes','Signals or eviction of foreign or existing jobs'],
            human_request=ref(OUT/'human_request.json'),live_probe=ref(OUT/'identity_and_gpu0_observation.json'),
            SERVERS_before_sha256=sha(sp),actual_idle_exclusive_asset_source_checks_required_before_each_compute=True)
        temp=sp.with_name('SERVERS.gpu0_reenable.tmp'); temp.write_text(new,encoding='utf-8',newline='\n'); os.replace(temp,sp)
        grant['SERVERS_after_sha256']=sha(sp); save(auth,grant)
        work=load(P/'research_work.json'); work.update(updated_at=now(),latest_resource_authorization=ref(auth),
            next_action='Latest human reopens server4 GPU0 only. Individual WFC/LFT/M206 pause holds remain; no automatic resume. Prepared NEC/MIC may advance under a fresh ordinary foreground snapshot on genuinely idle/exclusive authorized GPU0, original YAML/source/native/resource gates. GPU1 excluded.')
        save(P/'research_work.json',work)
        memory=(P/'codex_memory.md').read_text(encoding='utf-8'); lines=memory.splitlines()
        lines=[('- 最新直接用户指令“可使用一张卡server4-gpu0”（2026-11-04）：仅恢复server4物理GPU0资源授权，allowed_gpus=[0]/dispatch_enabled=true；GPU1保持禁用，单卡最多1任务。WFC/LFT/M206独立人工暂停记录保留，不把资源开放写成具体实验续训授权。' if x.startswith('- 最新直接用户指令') else
            '- 最新资源授权pipeline/authorizations/server4_gpu0_20261104.json；其他服务器新dispatch仍禁用，goal0441/closure2993及科学协议保持，Pipeline-cluster_project仍Disabled。原双卡授权和11-01全部停用是历史记录。' if x.startswith('- 目前无GPU使用授权') else x) for x in lines]
        memory='\n'.join(lines)+'\n'
        memory=memory.replace('两卡不再给本项目派发。','当时两卡停止派发；11-04新授权只重新开放GPU0，独立任务hold保持。')
        memory=memory.replace('NEC/MIC仍validation，native/resources NOT_RUN，未入队；不能作为替补启动。','NEC/MIC仍validation，native/resources NOT_RUN，未入队；GPU0资源已重新开放，后续须新快照真实原生检查/准入后才能启动。')
        a=memory.index('## Last Tick')
        memory=memory[:a]+'## Last Tick\n- 2026-11-04直接用户授权仅server4 GPU0；本次manual_ops/20261104_gpu0_reenable在实际owner与target一致且无foreground租约下，持canonical project锁记录授权、hostname先核dl04/.115并只读查询物理GPU0。\n- SERVERS仅server4 allowed[]→[0]/dispatchfalse→true，GPU1不授权；queue/running及全部候选记录不变，WFC/LFT/M206仍人工暂停。未计算、信号、同步、checkout或启动训练；后续按新快照走已授权候选。\n- 当前实测见identity_and_gpu0_observation.json；空闲观察不是独占租约，运行前必须再次核当时卡/源码/资产/三锁。11-01检查点与停止回执完整保留。\n'
        temp=P/'codex_memory.gpu0_reenable.tmp'; temp.write_text(memory,encoding='utf-8',newline='\n'); os.replace(temp,P/'codex_memory.md')
        assert sha(P/'queue.json')==sha(OUT/'before_pipeline__queue.json') and sha(P/'running.json')==sha(OUT/'before_pipeline__running.json')
        assert load(P/'research_work.json')['candidates']==load(OUT/'before_pipeline__research_work.json')['candidates']
        logged=subprocess.run(['C:/Program Files (x86)/Git/bin/bash.exe',str(SKILL/'log_decision.sh'),'cluster_project','manual',
            '用户重新开放server4 GPU0','仅开放GPU0，GPU1禁用，保留独立暂停实验hold',REQUEST,'pipeline/manual_ops/20261104_gpu0_reenable'],text=True,encoding='utf-8',capture_output=True,timeout=20)
        save(OUT/'manual_decision_log.json',dict(returncode=logged.returncode,stdout=logged.stdout,stderr=logged.stderr)); assert logged.returncode==0
        summary=dict(recorded_at=now(),status='GPU0_ONLY_RESOURCE_REAUTHORIZED',allowed_gpus=[0],dispatch_enabled=True,
            live_observation=probe['data'],resource_authorization=ref(auth),queue_running_and_all_candidates_unchanged=True,
            GPU1_used=False,training_started=False,scheduler_changed=False)
        save(OUT/'operation_summary.json',summary); print(json.dumps(summary,ensure_ascii=False))
    finally: lock.close()
if __name__=='__main__': main()
