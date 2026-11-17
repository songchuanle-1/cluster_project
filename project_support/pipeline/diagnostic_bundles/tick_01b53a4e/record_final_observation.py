"""Final fresh status and current successful attempt; no queue/source/launch mutation."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,importlib.util,json,sys
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('current_record_utilities',HERE/'finalize_research_records.py');u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
guard();p=HERE/'cre_training_progress_observation_final.json';assert sha(p)=='4ef31396407a40bccf32095b79cf625ce98a40f105d3186ad940180396d8026a'
live=u.read(p);ob=live['observation'];samples=ob['samples'];assert live['owner']==EXPECTED and live['returncode']==0 and samples[-1]['max_native_step']>samples[0]['max_native_step']
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon;import closure
lock=mon.acquire_lock(str(ROOT));assert lock is not None
try:
    guard();b=u.read(HERE/'protected_assets_before.json');u.source_protection(b)
    names=list(b['protected_ledgers'])+['experiments/M217-CRE.json','admissions/M217-CRE.json'];protected={n:sha(ROOT/'pipeline'/n) for n in names}
    work=u.read(ROOT/'pipeline/research_work.json');assert len(work['candidates'])==145
    now=datetime.now(timezone.utc).isoformat();held=[c for c in work['candidates'] if c['stage']=='blocked'];assert len(held)==10
    rows=[]
    for c in held:
        assert u.digest(c)==b['candidate_digests'][c['id']]
        rows.append({'id':c['id'],'stage':c['stage'],'blocker_kind':c.get('blocker_kind'),'failure_scope':c.get('failure_scope'),'record_digest':u.digest(c),'same_as_begin':True})
    u.save(HERE/'current_held_boundary_check.json',{'recorded_at':now,'owner':EXPECTED,'status':'TEN_UNCHANGED_DUE_HOLDS_METADATA_ONLY','held_records':rows,'source_baseline':u.ref(HERE/'protected_assets_before.json'),'evidence_targets_or_old_grant_bodies_read':False,'new_human_authorization':False,'native_or_resume_or_reopen':False})
    if work.get('held_boundary_review'):work.setdefault('held_boundary_review_history',[]).append(copy.deepcopy(work['held_boundary_review']))
    work['held_boundary_review']=u.ref(HERE/'current_held_boundary_check.json')
    cre=next(c for c in work['candidates'] if c['id']==u.CRE);assert cre['stage']=='training'
    cre.setdefault('observation_history',[]).append({'recorded_at':now,'prior_latest_native_training_progress':copy.deepcopy(cre['latest_native_training_progress'])})
    cre['latest_native_training_progress'].update(recorded_at=ob['observed_at'],epoch=samples[-1]['max_native_step'][0],step=samples[-1]['max_native_step'][1],observed_steps=samples,precise_native_validation=live['precise_native_validation'],evidence=u.ref(p))
    cre['current_resource_check'].update(recorded_at=ob['observed_at'],evidence=u.ref(p))
    for cid in [u.CRE,u.HPC,u.APF]:
        c=next(c for c in work['candidates'] if c['id']==cid)
        if u.ref(p) not in c['evidence']:c['evidence'].append(u.ref(p))
        if cid!=u.CRE:c['current_resource_check'].update(recorded_at=ob['observed_at'],evidence=u.ref(p))
    if work.get('tick_attempt'):work.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
    work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':u.CRE,'kind':'native_smoke','result':'passed','command':'python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_d08825b5/cre_compatible_tooling/adapter.py run --mode smoke --target candidate','observation':'Current new-owned original CRE actual2TRAIN finite loss/backward/path/optimizer updates and actual paired resources independently passed, then exact-source canonical one-shot dispatch and original deployed native TRAIN progress were verified. This is technical readiness/current operation, not accuracy or old import root-cause repair. APF is only source/static prepared.','evidence':[u.ref(HERE/'cre_native_smoke.json'),u.ref(HERE/'cre_actual_four_result_review.json'),u.ref(p)]}
    for e in work['tick_attempt']['evidence']:assert e in cre['evidence'];closure.artifact(ROOT,e)
    work['latest_operational_readiness']['current_training']=u.ref(p);work['updated_at']=now;u.atomic(ROOT/'pipeline/research_work.json',work)
    memory=(ROOT/'pipeline/codex_memory.md').read_text('utf8');newtime=datetime.fromisoformat(ob['observed_at']).astimezone(timezone(timedelta(hours=8))).strftime('%H:%M:%S')
    memory=memory.replace('02:45:02',newtime).replace('602→611','2219→2228').replace('观察d399876d','首观察d399876d/末观察4ef31396')
    assert len(memory.splitlines())<120;u.atomic(ROOT/'pipeline/codex_memory.md',memory,text=True)
    notes_path=HERE/'report_notes.json';backup=HERE/'report_notes_initial.json';guard()
    with backup.open('xb') as f:f.write(notes_path.read_bytes())
    notes=u.read(notes_path)
    notes['actions']=[s.replace('02:45:02',newtime).replace('602→611','2219→2228') for s in notes['actions']]
    notes['actions'].append('收尾前同一原PID/source8/YAML/runtime/GPU0再只读复核，原TRAIN1/50步2219→2228，仍无已观测验证mIoU；当前tick_attempt已绑定真实CRE成功检查，历史0f失败保留。10旧held本轮metadata/digest与begin完全相同，未追读历史目标或授新许可。')
    u.atomic(notes_path,notes)
    assert all(sha(ROOT/'pipeline'/n)==h for n,h in protected.items());u.source_protection(b)
    u.save(HERE/'final_observation_recorded.json',{'recorded_at':now,'owner':EXPECTED,'current_training':u.ref(p),'native_progress':samples[-1]['max_native_step'],'validation_best':live['precise_native_validation']['best'],'source_queue_exp_receipt_lifecycle_unchanged':True,'report_notes':u.ref(notes_path),'new_launches':0})
    print(json.dumps({'progress':samples[-1]['max_native_step'],'validation_best':live['precise_native_validation']['best'],'source_queue_exp_receipt_preserved':True,'report_notes':u.ref(notes_path)},ensure_ascii=False))
finally:lock.close()
