"""Record actual original PES progress and AOC's physical GPU wait."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse, json, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent
PES='hierarchy-palindromic-euler-state-composition';AOC='hierarchy-ancestral-order-commutator-composition'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');a=ap.parse_args()
    if not a.execute_root:print('DEFAULT_NO_STATE_CHANGE');return
    guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b);u.lifecycle_protection(b)
    obs=HERE/'pes_progress_observer/pes_training_progress_observation.json';assert sha(obs)=='2d6a5c9142e0f669718be9c8fb5ef6d930f925577960e0331ff17c8e2371d4b9'
    ob=u.read(obs);assert ob['owner']==EXPECTED and ob['returncode']==0 and ob['observation']['runtime_commit']==u.SOURCE
    samples=ob['observation']['samples'];assert samples[0]['last_native_step']==[1,2325] and samples[-1]['last_native_step']==[1,2330]
    assert all(ob['precise_native_validation'][k] is None for k in ('values','best','no_improve'))
    peer=HERE/'current_pes_wait_independent_review.json';assert sha(peer)=='ea89e2d77348eb4d8200f95e3fc6af8a3484f84e055961f4ac7556c84f8f0bea' and u.read(peer)['material_concerns']==[]
    assert '2265073' in [x.split(',')[0].strip() for x in ob['observation']['GPU0_contexts'].splitlines()]
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();u.primary_protection(b);u.lifecycle_protection(b)
        path=ROOT/'pipeline/research_work.json';before=sha(path);w=u.read(path);old={c['id']:u.digest(c) for c in w['candidates']};assert len(old)==148
        p=next(c for c in w['candidates'] if c['id']==PES);c=next(c for c in w['candidates'] if c['id']==AOC)
        assert p['stage']=='training' and p['code_commit']==u.SOURCE and c['stage']=='validation' and c['code_commit']=='0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'
        now=datetime.now(timezone.utc)
        p['current_live_observation']={'recorded_at':now.isoformat(),'evidence':u.ref(obs),'independent_review':u.ref(peer),'original_pid':2265073,'original_start_ticks':88396735,'native_step_before':[1,2325],'native_step_after':[1,2330],'precise_native_validation':ob['precise_native_validation'],'scope':'Only actual original native training progress. No validation printed, no new efficacy or launch claim.'}
        c.update(stage='blocked',blocker_kind='exclusive_gpu_slot',blocked_from_stage='validation',resume_stage='validation',required_server='server-4',required_physical_gpu=0,blocked_at=now.isoformat(),retry_after=(now+timedelta(hours=1)).isoformat(),blocker='Sole authorized physicalGPU0 is occupied by the original admitted PES2265073; preserve that training. AOC native TRAIN2/resources remain NOT_RUN.',unblock_condition='Original PES ends naturally; then fresh actual GPU0 occupation/UUID/source9c/three-lock/owner-original-deadline checks permit original AOC0314 native execution. No GPU1, eviction, automatic recovery or sibling ff.')
        c['current_resource_check']={'recorded_at':ob['observed_at'],'result':'Original_PES_compute_PID_and_GPU0_context_confirmed_busy','evidence':u.ref(obs),'scope':'Dated actual original process/context/source observation only. Canonical current-owner occupation proof follows before finish; no resource profile or AOC native PASS.'}
        c['next_action']='Preserve original PES GPU0 task. Parent9c and PES technical receipt are already genuinely promoted; after natural GPU0 release, execute original AOC0314 paired natural TRAIN2/resources under fresh owner/original deadline, current compatible source/runtime/assets/UUID and all three locks. No AOC queue/admission before actual passes.'
        for candidate in (p,c):
            for r in (u.ref(obs),u.ref(peer)):
                if r not in candidate['evidence']:candidate['evidence'].append(r)
        w['updated_at']=now.isoformat();w['last_event_tick']=EXPECTED['generated_at'];w['next_action']=c['next_action']
        assert all(u.digest(x)==old[x['id']] for x in w['candidates'] if x['id'] not in (PES,AOC))
        u.save(HERE/'current_wait_record_intent.json',{'owner':EXPECTED,'research_work_before_sha256':before,'changed_candidate_ids':[PES,AOC],'observation':u.ref(obs),'independent_review':u.ref(peer),'scope':'Current progress and actual AOC GPU0 resource disposition only, no native/profile/queue/source/launch operation.'})
        guard();assert sha(path)==before;u.atomic(path,w);u.primary_protection(b);u.lifecycle_protection(b)
        u.save(HERE/'current_wait_record_result.json',{'owner':EXPECTED,'status':'ORIGINAL_PES_PROGRESS_AND_AOC_GPU0_WAIT_RECORDED','candidate_count':148,'other146_candidates_unchanged':True,'all26_lifecycle_and28_user_paths_and_index_preserved':True,'research_work_sha256':sha(path)})
        print('Original PES healthy; AOC now explicitly waits for occupied GPU0. Native tests not executed.')
    finally:lock.close()

if __name__=='__main__':main()
