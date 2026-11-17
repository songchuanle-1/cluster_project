"""Reconcile only the interrupted M204 lifecycle and due scope holds."""
from ops import *
import copy
import csv
import pipeline_monitor as monitor

guard(120)
observed=tick.load(OUT/'original_run_after.json')
interruption=tick.load(OUT/'original_run_reconciliation.json')
checkpoint=tick.load(OUT/'checkpoint_cpu.json')
contract=tick.load(OUT/'resume_contract_cpu.json')
assert interruption['original_run_absent_in_two_fresh_probes'] and interruption['boot_after_original_launch']
assert not contract['nonfinite_tensors'] and not contract['cuda_initialized']
assert all(value['unchanged'] for value in checkpoint['runtime_files'].values())
assert tick.digest(OUT/'native_training.log')==contract['native_log']['sha256']
auth_path=ROOT/'pipeline/authorizations/cpa_exploratory_20261019_72695a5d.json'
auth=tick.load(auth_path)
assert tick.digest(auth_path)=='2b139af1820c167dbb0a044518acbfa6a441543bb4b559b706439099583dd2ee'
assert auth['maximum_training_launches']==1 and auth['automatic_retry_or_restart'] is False
lock=monitor.acquire_lock(str(ROOT))
assert lock is not None,'Pipeline monitor lock is held; no lifecycle writes permitted'
try:
    guard(90)
    experiment=monitor.load_experiment(str(ROOT),'M204-CPA')
    queue=monitor.load_queue(str(ROOT))
    running=monitor.load_running(str(ROOT))
    deathwatch=monitor.load_deathwatch(str(ROOT))
    tasks=[task for task in queue['gpu_queues']['server-4'] if task.get('id')=='M204-CPA']
    assert len(tasks)==1 and tasks[0]['status']=='running' and experiment['status']=='running'
    assert experiment['pid']==141278 and experiment['automatic_restart'] is False
    assert running['server-4']['0']=='M204-CPA'
    save('lifecycle_before.json',{'experiment':experiment,'task':tasks[0],'running':running,'deathwatch_entry':deathwatch.get('server-4',{}).get(Path(experiment['config']).stem)})
    other_queue={server:[task for task in values if task.get('id')!='M204-CPA'] for server,values in queue['gpu_queues'].items()}
    now=datetime.now(timezone.utc)
    best=observed['native_log']['best']
    experiment.update(status='stopped_unknown',finished_at=now.isoformat(),
        final_best=f"{best['mIoU']:.4f}",epochs_final='6/50',partial_result_only=True,
        last_completed_epoch=contract['metadata']['epoch'],observed_native_best_miou=best['mIoU'],
        observed_native_best_epoch=best['epoch'],observed_validation_count=len(observed['native_log']['validation_history']),
        observed_native_step=observed['last_stdout_steps'][-1],process_live=False,
        observed_stopped_at=observed['observed_at'],host_boot_at=observed['boot_at'],
        interruption_reason='host reboot after original launch;exact process absent in two fresh probes;native exit code unavailable',
        requires_resume_authorization=True,automatic_restart=False,
        latest_training_observation=evidence(OUT/'original_run_reconciliation.json'),
        checkpoint_inspection=evidence(OUT/'checkpoint_cpu.json'),
        checkpoint_resume_contract=evidence(OUT/'resume_contract_cpu.json'),
        log_local=str(OUT/'native_training.log'),
        note=experiment['note']+' Original launch interrupted by host reboot;partial validation only. No restart or migration authorized;preserve same stable experiment and await scoped resume consent.')
    experiment.setdefault('history',[]).append({'ts':now.isoformat(),'action':'reconciled_host_reboot_interruption','status':'stopped_unknown','observed_stopped_at':observed['observed_at'],'host_boot_at':observed['boot_at'],'best_miou':best['mIoU'],'best_epoch':best['epoch'],'checkpoint_epoch':5,'original_launch_retained':True,'restarted':False})
    monitor.save_experiment(str(ROOT),experiment)
    queue['gpu_queues']['server-4']=[task for task in queue['gpu_queues']['server-4'] if task.get('id')!='M204-CPA']
    assert queue['gpu_queues']==other_queue
    monitor.save_queue(str(ROOT),queue)
    del running['server-4']['0']
    if not running['server-4']:del running['server-4']
    monitor.save_running(str(ROOT),running)
    deathwatch.get('server-4',{}).pop(Path(experiment['config']).stem,None)
    monitor.save_deathwatch(str(ROOT),deathwatch)
    rows=list(csv.DictReader((ROOT/'pipeline/experiments.csv').open(encoding='utf-8-sig',newline='')))
    assert not any(row.get('id')=='M204-CPA' for row in rows)
    monitor.ledger_append(str(ROOT),finished_at=now.astimezone().strftime('%Y-%m-%d %H:%M:%S'),id='M204-CPA',config=experiment['config'],server='server-4',gpu='0',state='stopped_unknown',best_miou=f"{best['mIoU']:.4f}",epochs='6/50',log_local=str(OUT/'native_training.log'))
    assert monitor.load_experiment(str(ROOT),'M204-CPA')['status']=='stopped_unknown'
    assert not any(task.get('id')=='M204-CPA' for tasks in monitor.load_queue(str(ROOT))['gpu_queues'].values() for task in tasks)
    assert all('M204-CPA' not in (value if isinstance(value,list) else [value]) for values in monitor.load_running(str(ROOT)).values() for value in values.values())
    save('lifecycle_reconciled.json',{'recorded_at':now.isoformat(),'experiment_id':'M204-CPA','state':'stopped_unknown','reason':'original process absent after host reboot','launches_this_tick':0,'restarts':0,'migrations':0,'scientific_state':'inconclusive;not scientific rejection','best_miou':best['mIoU'],'best_epoch':best['epoch'],'last_completed_epoch':5,'last_partial_step':observed['last_stdout_steps'][-1],'resume_requires_new_human_authorization':True,'checkpoint_sha256':checkpoint['checkpoints']['last.pth']['sha256'],'native_log':evidence(OUT/'native_training.log'),'evidence':[evidence(OUT/name) for name in ('original_run_reconciliation.json','checkpoint_cpu.json','resume_contract_cpu.json')],'queue_entry_removed':True,'running_mapping_removed':True,'other_queue_entries_unchanged':True,'monitor_lock_held_during_reconciliation':True})
finally:
    lock.close()

guard(60)
scope_ids=['m95-native-relation-other-sign-conflict','m95-native-main-role-weight-precedence','m95-native-secondary-positive-mass','m95-native-between-pair-support']
now=datetime.now(timezone.utc)
retry=(now+__import__('datetime').timedelta(hours=4)).isoformat()
work=tick.load(ROOT/'pipeline/research_work.json')
scope_records=[]
for cid in scope_ids:
    candidate=next(c for c in work['candidates'] if c['id']==cid)
    assert candidate['stage']=='blocked' and candidate['blocker_kind']=='human_authorization'
    scope_records.append({'id':cid,'decision':'scope hold unchanged;CPA-only launch consent is not auxiliary-scope restoration','prior_retry_after':candidate['retry_after'],'retry_after':retry,'scientific_retest':False,'promoted':False})
save('scope_holds_recheck.json',{'recorded_at':now.isoformat(),'actual_check':'Re-read primary point-feature-path directive;verify unchanged goal and exact one-launch CPA consent against the four due auxiliary scope holds. No new human restoration authorization or mainline-required auxiliary test exists in this tick.','goal':evidence(ROOT/'pipeline/goal.json'),'mainline_directive':evidence(ROOT/'docs/research_mainline_correction_20261015.md'),'authorization':evidence(auth_path),'candidates':scope_records,'retry_after':retry,'resource_shortage_claimed':False,'new_candidates':0,'scientific_tests':0})
save('resume_request.json',{'recorded_at':now.isoformat(),'candidate_id':CID,'experiment_id':'M204-CPA','authorized':False,'reason':'The consumed single-launch exception explicitly forbids automatic retry/restart. Host reboot creates a new resume operation,not an old permission re-request.','requested_operation':'Resume the SAME interrupted experiment from verified epoch5 last.pth on server4 physical GPU0;retain model/optimizer/PolyLR/best/patience state and frozen seed1999,batch2,workers4,50-epoch total limit;no tuning,cold restart,migration or extra variant.','checkpoint_path':checkpoint['checkpoints']['last.pth']['path'],'checkpoint_sha256':checkpoint['checkpoints']['last.pth']['sha256'],'planned_start_epoch':6,'mid_epoch_replay_available':False,'rng_state_saved':False,'native_resumed_step_verified':False,'fresh_identity_idleness_and_exclusive_gpu_lease_still_required':True,'question':'是否授权从已核验的 last.pth 恢复同一 M204-CPA（server4 GPU0，从第6轮继续，保留优化器和学习率状态，总轮数仍为50，不调参）？'})
advance([OUT/name for name in ('lifecycle_before.json','lifecycle_reconciled.json','resume_request.json','reconcile_tick.py')],stage='blocked',blocker_kind='human_authorization',blocker='Original authorized CPA launch ended after host reboot. Full epoch5 model/AdamW/PolyLR checkpoint is intact,but the one-launch exception explicitly forbids automatic retry or restart;new scoped human resume consent is absent. This is NOT a GPU resource block or scientific falsification.',retry_after=retry,unblock_condition='New explicit human authorization in the owning chat to resume SAME M204-CPA from the verified epoch5 last.pth on server4 physicalGPU0;then reverify source/hash,server identity,idleness and exclusive GPU lease before native resumed-step verification. No cold restart,migration,tuning or additional launch is implicit.',next_action='Await one explicit answer to the scoped M204-CPA resume request. Do not relaunch on a due timer or an idle GPU. On consent record its provenance,prepare a scoped guarded native resume and verify model/optimizer/scheduler restoration plus increasing native epoch6 steps.',gate_result='Operational host-reboot interruption;epoch5 partial nativeVAL best .43399661779403687. Diagnosis/semantic-control gates remain unpassed,revision1 remains inconclusive;no trained efficacy/falsification claim.',wake_paths=['pipeline/goal.json','pipeline/authorizations/cpa_resume_M204.json'])
for record in scope_records:
    advance([OUT/'scope_holds_recheck.json'],candidate_id=record['id'],retry_after=retry)
work=tick.load(ROOT/'pipeline/research_work.json')
work['design_cycle']={'recorded_at':datetime.now(timezone.utc).isoformat(),'stop_reason':'external_resource_blocked','blocker_kind':'human_authorization','actual_reason':'All five pending stable IDs have evidenced human authorization/scope holds. For CPA the new resume needs explicit consent after host reboot;the other four remain auxiliary only. This legacy stop_reason label does NOT claim GPU shortage,route exhaustion,phase hold or scientific rejection. Reserve preparation budget is zero;no duplicate candidates are permitted.','attempted_ids':[CID,*scope_ids],'evidence':[evidence(OUT/name) for name in ('lifecycle_reconciled.json','checkpoint_cpu.json','resume_contract_cpu.json','scope_holds_recheck.json','resume_request.json')],'resume_condition':'Human consent for the exact same M204 checkpoint resume,or explicit auxiliary-scope restoration / a separately justified mainline-required auxiliary diagnostic. Due retries and idle cards alone never grant consent. Recheck actual resource/identity/leases before any newly authorized GPU action.','retry_after':retry}
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
decision=monitor.log_decision(str(ROOT),'question','M204-CPA original process disappeared after the server4 reboot;how should the interrupted run proceed?','Record stopped_unknown and preserve epoch5 full checkpoint/native logs. Ask once for SAME-experiment checkpoint resume consent;do not restart,migrate or tune automatically.','Single-launch human exception explicitly forbids automatic retry/restart. Two fresh process probes,host boot time,and CPU checkpoint/native resume-contract checks establish interruption and recoverable epoch state;scientific gates remain unresolved.',str(OUT/'lifecycle_reconciled.json'))
save('reconciliation_summary.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'lifecycle':'stopped_unknown','candidate_stage':'blocked','blocker_kind':'human_authorization','pending_human_holds':5,'new_candidates':0,'training_launches':0,'restarts':0,'migrations':0,'cuda_diagnostics':0,'scope_rechecks':4,'checkpoint_cpu_inspections':2,'retry_after':retry,'decision_file':decision,'lease_still_owned':guard()['token']==TOKEN})
print(json.dumps(tick.load(OUT/'reconciliation_summary.json'),ensure_ascii=True,indent=2))
