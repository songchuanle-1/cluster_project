"""Bounded recognized-block recheck, not a new scientific experiment."""
from datetime import datetime,timedelta,timezone
import json
from check_current import guard,save,evidence,ROOT,OUT
import closure
import foreground_tick as tick

guard()
auth=tick.load(OUT/'authorization_recheck.json')
four=tick.load(OUT/'server4_live.json');three=tick.load(OUT/'server3_live.json')
assert not auth['new_authorization'] and len(auth['candidates'])==4
assert four['occupied'] and three['occupied'] and four['training_pid_alive']
assert all(pids==[1995443] for pids in four['lock_owner_pids'].values())
now=datetime.now(timezone.utc)
for observation in (four,three):assert (now-datetime.fromisoformat(observation['observed_at'])).total_seconds()<900
work=tick.load(ROOT/'pipeline/research_work.json')
ids=[c['id'] for c in auth['candidates']]
primary=next(c for c in work['candidates'] if c['id']=='fle-self-neighbor-content-separation')
assert primary['stage']=='blocked' and primary['blocker_kind']=='exclusive_gpu_slot'
assert primary['required_server']=='server-4'
assert datetime.fromisoformat(primary['retry_after'])<now
targets=[c for c in work['candidates'] if c['id'] in ids]+[primary]
verification={'observed_at':now.isoformat(),'checked_candidates':len(targets),'verified_references':0,'passed':False}
try:
    for candidate in targets:
        for entry in candidate['evidence']:
            closure.artifact(ROOT,entry);verification['verified_references']+=1
    verification['passed']=True
finally:save('existing_evidence_verification.json',verification)
auth_evidence=evidence(OUT/'authorization_recheck.json')
for candidate in targets[:-1]:
    assert candidate['stage']=='blocked' and candidate['blocker_kind']=='human_authorization'
    assert 'auxiliary' in candidate['blocker']
    candidate['evidence'].append(auth_evidence)
    candidate['last_rechecked_at']=now.isoformat()
    candidate['retry_after']=(now+timedelta(hours=4)).isoformat()
    # Keep the original human/auxiliary release condition and science gates.
primary['evidence']+= [evidence(OUT/'server4_live.json'),evidence(OUT/'server3_live.json')]
primary['blocker']='Non-GPU preparations remain the frozen prior-tick results,not rerun. Resource-only recheck at2026-10-18 02:14:04Shanghai:server4GPU0 M203training PID1995443 owns allthree locks;server3GPU1 occupied by a foreign job. No authorized idle slot,no CUDA/native diagnostic call. Original controls and1e-6tolerance unchanged.'
primary['last_rechecked_at']=now.isoformat()
primary['retry_after']=(now+timedelta(hours=1)).isoformat()
entries=[evidence(OUT/name) for name in ('authorization_recheck.json','server4_live.json','server3_live.json','existing_evidence_verification.json')]
summary={'observed_at':now.isoformat(),'kind':'bounded_blocker_recheck_only','scientific_status':'unchanged_inconclusive',
    'authorization_holds_rechecked':4,'resource_hold_rechecked':1,'new_candidates':0,'native_forwards':0,'native_backwards':0,
    'cpu_contracts_rerun':0,'optimizer_steps':0,'models':0,'admissions':0,'launches':0,
    'native_validation_miou':four['validation_miou'],'latest_epoch_steps':four['epoch_steps'],
    'best_current_run':max(four['validation_miou']),'historical_champion':.5020,'target':.51,
    'both_authorized_slots_occupied':True,'frozen_diagnostic_unchanged':True,
    'explanation':'Four due auxiliary authorization holds remain unchanged;reuse current live resource facts to refresh the primary resource retry after more than one hour,without rerunning cached CPU tests,reviews or native capture.',
    'evidence':entries}
save('recheck_summary.json',summary)
entries.append(evidence(OUT/'recheck_summary.json'))
work['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':ids+[primary['id']],
    'evidence':entries,'retry_after':primary['retry_after'],
    'resume_condition':'Resume frozen point-feature native diagnostic when an authorized pinned card is actually idle and fresh execution lease/lifetime GPU locks plus target asset checks pass;auxiliary holds resume only under their original explicit-authorization or mainline-needed auxiliary-test conditions.',
    'scope':'Bounded due authorization rechecks and resource-only reconciliation;no scientific experiment,new model or route exhaustion claimed.'}
guard();tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'held_authorization_candidates':4,'held_resource_candidates':1,'native_diagnostics_run':0,'new_candidates':0,
    'best_early_miou':summary['best_current_run'],'resource_retry_after':primary['retry_after'],'historical_evidence_verified':verification['passed']}))
