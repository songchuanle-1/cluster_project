import copy
import json
import os
import subprocess
import yaml
from pause_both import ROOT,P,OUT,SKILL,THREAD,now,load,sha,evidence,save,guard,pm
guard(); lock=pm.acquire_lock(str(ROOT)); assert lock is not None
try:
    before=load(OUT/'before_pipeline__research_work.json'); after=load(P/'research_work.json')
    target_ids={'M226-WFC','M227-LFT'}
    assert {c['id']:c for c in before['candidates'] if c.get('experiment_id') not in target_ids}=={c['id']:c for c in after['candidates'] if c.get('experiment_id') not in target_ids}
    oldq=load(OUT/'before_pipeline__queue.json'); q=load(P/'queue.json')
    for server,tasks in oldq['gpu_queues'].items():
        assert [t for t in tasks if t['id'] not in target_ids]==[t for t in q['gpu_queues'][server] if t['id'] not in target_ids]
    targets=[t for t in q['gpu_queues']['server-4'] if t['id'] in target_ids]
    for task in targets:
        assert task['status']=='waiting' and task['training_status']=='paused_by_user' and task['dispatch_phase']=='user_paused'
        assert task['resume_authorized'] is False and task['dispatch_hold'] and not any(k in task for k in ('pid','log','launched','claimed_gpu'))
        assert task['paused_run']['checkpoint_full_state_validation']=='CPU_VALIDATED_SAVED_COMPLETE_EPOCH'
    oldrun=load(OUT/'before_pipeline__running.json'); run=load(P/'running.json')
    wanted=copy.deepcopy(oldrun); wanted['server-4']={k:v for k,v in wanted['server-4'].items() if v not in target_ids}; assert wanted==run
    s=yaml.safe_load((ROOT/'SERVERS.yaml').read_text(encoding='utf-8')); old=yaml.safe_load((OUT/'before_SERVERS.yaml').read_text(encoding='utf-8'))
    old['servers']['server-4'].update(allowed_gpus=[],dispatch_enabled=False); assert s==old
    assets=load(P/'diagnostic_bundles/tick_25fc0b57/protected_assets_before.json')
    for name,digest in assets['files'].items(): assert sha(ROOT/'Cluster'/name)==digest,name
    changed_ledger={'queue.json','running.json','experiments/M226-WFC.json','experiments/M227-LFT.json'}
    for name,digest in assets['protected_ledgers'].items():
        if name not in changed_ledger: assert sha(P/name)==digest,name
    git='C:/Program Files (x86)/Git/cmd/git.exe'; code=ROOT/'Cluster'
    def cmd(*args): return subprocess.check_output([git,'--no-optional-locks','-c','core.fsmonitor=false','-C',str(code),*args])
    assert cmd('rev-parse','HEAD').decode().strip()==assets['head']
    assert cmd('status','--porcelain=v1','--untracked-files=all','-z').hex()==assets['status_hex']
    index=cmd('rev-parse','--git-path','index').decode().strip(); ip=__import__('pathlib').Path(index)
    if not ip.is_absolute(): ip=code/ip
    assert sha(ip)==assets['index_sha256'] and not cmd('diff','--cached','--name-only')
    m=P/'codex_memory.md'; memory=m.read_text(encoding='utf-8')
    lines=memory.splitlines()
    lines=[('- 最近研究owner25fc0b57已于2026-11-01T02:13:17Z释放；本次人工操作无active研究租约。真实root thread01a159c5-29ab-7a22-ba7f-e79174757253与foreground target一致。' if line.startswith('- 当前owner25fc0b57') else line) for line in lines]
    memory='\n'.join(lines)+'\n'; assert memory.count('\n## ')==7 and len(lines)<120
    tmp=m.with_name('codex_memory.audit_pause.tmp'); tmp.write_text(memory,encoding='utf-8',newline='\n'); os.replace(tmp,m)
    result=dict(recorded_at=now(),status='PASS',two_user_pauses_persisted=True,server4_all_gpu_use_disabled=True,
        no_replacement_or_automatic_resume=True,M206_and_other153_candidates_unchanged=True,
        source_user_files_git_status_index_and_nontarget_lifecycle_unchanged=True,
        stop_confirmation=evidence(OUT/'stop_confirmation.json'),checkpoint_confirmation=evidence(OUT/'checkpoint_confirmation.json'),
        original_native_checkpoint_epochs={t['id']:t['paused_run']['checkpoint_meta']['epoch'] for t in targets},
        last_cpu_inspection_contexts=load(OUT/'checkpoint_confirmation.json')['data']['contexts'],
        checkpoint_first_attempt='CPU checks succeeded but JSON rejected numpy.float32; attempt1 preserved; serialization normalized to native scalar types in attempt2. No repeat signal or training performed.',
        memory=evidence(m),manual_report=evidence(OUT/'manual_report.md'))
    save(OUT/'final_audit.json',result)
    summary=load(OUT/'operation_summary.json'); summary.update(final_audit=evidence(OUT/'final_audit.json'),checkpoint_confirmation=evidence(OUT/'checkpoint_confirmation.json'),
        gpus_after=load(OUT/'checkpoint_confirmation.json')['data']['gpus'],checkpoint_full_state_validation='CPU_VALIDATED_SAVED_COMPLETE_EPOCH'); save(OUT/'operation_summary.json',summary)
    print(json.dumps({k:v for k,v in result.items() if k not in ('checkpoint_first_attempt','memory','manual_report')},ensure_ascii=False))
finally: lock.close()
