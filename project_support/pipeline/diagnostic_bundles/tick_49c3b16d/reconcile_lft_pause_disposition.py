"""Administrative pause-stage reconciliation after an honest postflight rejection."""
from datetime import datetime,timezone,timedelta
from collections import Counter
import copy,json,os,sys
from observe_and_record import ROOT,P,HERE,EXPECTED,guard,load,sha,ref,save,digest,protect,now

guard(); sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline'); import pipeline_monitor as mon
lock=mon.acquire_lock(str(ROOT)); assert lock is not None
try:
    guard(); b=load(HERE/'protected_assets_before.json'); protect(b)
    w=load(P/'research_work.json'); c=next(c for c in w['candidates'] if c.get('experiment_id')=='M227-LFT'); old=copy.deepcopy(c)
    q=load(P/'queue.json'); task=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M227-LFT')
    assert task['status']=='waiting' and task['training_status']=='paused_by_user' and task['launch_verified'] is False and task['resume_authorized'] is False and task['dispatch_hold']
    assert c['stage']=='training' and c['human_hold'] is True and c['training_status']=='paused_by_user'
    receipt=P/'tick_receipts'/(EXPECTED['token']+'.json'); failed=load(receipt)
    assert failed['status']=='INCOMPLETE' and failed['lease_release']=='retained'
    record=dict(recorded_at=now(),owner=EXPECTED,postflight_attempt1='CLOSURE_INCOMPLETE: Training disposition lacks verified launch',
        failed_receipt=failed,failed_receipt_sha256=sha(receipt),affected_experiment_id='M227-LFT',candidate_before=old,
        queue_unchanged_snapshot=task,pause_evidence=ref(P/'manual_ops/20261101_dual_user_pause/human_request.json'),
        distinction='WFC is actually running/launch_verified=true. LFT has been correctly human-paused since Nov01 with launch_verified=false; only its research candidate stage still falsely read training. Reconcile stage to blocked/human_authorization without any training, scientific rejection or changed permission.',
        preserve='All original evidence/source/receipt/paused_run/metrics and queue/experiment files remain; original failed postflight is retained here.')
    save(HERE/'postflight_attempt1_failed_and_lft_pause_repair.json',record,True)
    c.update(stage='blocked',resume_stage='training',blocked_from_stage='training',blocker_kind='human_authorization',
        blocker='Direct human Nov01 paused LFT; Nov04 GPU0 resource opening and WFC start do not resume LFT. Queue remains paused_by_user/resume_authorized=false with dispatch_hold. Research stage is operationally blocked, not a scientific failure.',
        unblock_condition='A later direct human instruction authorizes this original LFT full-state resume on a currently allowed card, with original source/checkpoint/resource validation. A timer or WFC launch is not authorization.',
        retry_after=(datetime.now(timezone.utc)+timedelta(hours=4)).isoformat(),
        next_action='Preserve LFT manually paused checkpoint22, original source4457, receipt and paused_run. No resume, migration or cold start until later explicit human authorization; GPU1 remains excluded. WFC alone continues GPU0. Paused research stage is blocked/human_authorization.')
    evidence=ref(HERE/'postflight_attempt1_failed_and_lft_pause_repair.json'); c['evidence'].append(evidence)
    w['updated_at']=now(); save(P/'research_work.json',w)
    assert all(digest(z)==b['candidate_digests'][z['id']] for z in w['candidates'] if z['id'] not in ('hierarchy-coupled-node-edge-state-composition',c['id']))
    notes=load(HERE/'final_report_notes.json'); notes['actions'].append('首次postflight真实拒绝Training disposition lacks verified launch：WFC已有verified进程，根因是LFT自人工暂停后候选stage仍training。已留存原失败receipt与旧记录，仅将LFT研究stage规范为blocked/human_authorization，保queue/experiment/原source/receipt/paused_run/metrics和实际暂停，无训练或科学拒绝。')
    notes['decisions'].append('此行政账修复不解除LFT暂停，不改变checker或科学门，不制造恢复权限；NEC之外仅LFT候选操作状态改变，其他153候选及38生命周期文件保持，旧失败回执完整留档后按实际修复重验收尾。')
    notes['actions']=[x.replace('其他154候选','其他153候选及LFT原暂停/历史证据') for x in notes['actions']]
    save(HERE/'final_report_notes.json',notes)
    memory=(P/'codex_memory.md').read_text(encoding='utf-8').replace('其他154候选、LFT/M206暂停','其他153候选、LFT/M206实际暂停')
    memory+='- 首次postflight拒绝Training disposition lacks verified launch，真实原因是LFT仍stage training但已人工暂停/launchfalse；原失败receipt/完整旧LFT/queue在postflight_attempt1_failed_and_lft_pause_repair.json。仅将LFT研究stage→blocked/human_authorization，保留training_statuspaused/hold/resumefalse及全部原证据，其他153候选和queue/exp不动；不修checker，不新增科学结论，按实际修复重验。\n'
    assert memory.count('\n## ')==7 and len(memory.splitlines())<120
    temp=P/'codex_memory.49c3_lft_pause.tmp'; temp.write_text(memory,encoding='utf-8',newline='\n'); guard();os.replace(temp,P/'codex_memory.md')
    state=load(HERE/'preclosure_actual_state.json'); state.update(recorded_at=now(),work_sha256=sha(P/'research_work.json'),memory_sha256=sha(P/'codex_memory.md'),notes=ref(HERE/'final_report_notes.json'),candidate_stage_counts=dict(Counter(z['stage'] for z in w['candidates'])),
        all154_other_candidates_and_all38_lifecycle_user28_source18_index_preserved=False,
        other153_candidates_and_all38_lifecycle_user28_source18_index_preserved=True,LFT_operational_pause_stage_reconciled_no_permission_or_science_change=True)
    state['evidence'].append(evidence); save(HERE/'preclosure_actual_state.json',state); protect(b)
    print(json.dumps(dict(status='LFT_PAUSE_STAGE_RECONCILED_NO_TRAINING_OR_PERMISSION_CHANGE',evidence=evidence,notify='DONT_NOTIFY'),ensure_ascii=False))
finally: lock.close()
