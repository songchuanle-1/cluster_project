"""Record current read-only native progress, preserving all lifecycle state."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, json, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent
DCE='hierarchy-directed-cavity-edge-composition'
PES='hierarchy-palindromic-euler-state-composition'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');a=ap.parse_args()
    if not a.execute_root:
        print('DEFAULT_NO_MUTATION');return
    guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b);u.lifecycle_protection(b)
    obs=HERE/'dce_progress_observer/dce_training_progress_observation.json'
    peer=HERE/'dce_pes_current_independent_review.json'
    assert sha(obs)=='abc944e47deb7f0a79f2706daf64e656d2e417a85fd6e86bd084fc84f033e57a'
    assert sha(peer)=='7e1e9bbc8d519436108f0d795db4c6d0a9501bf023aa54b865e973633f6c91f4'
    ob=u.read(obs);assert ob['owner']==EXPECTED and ob['returncode']==0
    assert ob['observation']['runtime_commit']==u.SOURCE and ob['observation']['signals_sent'] is False
    samples=ob['observation']['samples'];assert samples[1]['last_native_step']>samples[0]['last_native_step']
    values=ob['precise_native_validation'];assert values['best']==0.44330915808677673 and len(values['values'])==5
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();u.primary_protection(b);u.lifecycle_protection(b)
        path=ROOT/'pipeline/research_work.json';before=sha(path);w=u.read(path)
        old={c['id']:u.digest(c) for c in w['candidates']};assert len(old)==147
        now=datetime.now(timezone.utc).isoformat()
        d=next(c for c in w['candidates'] if c['id']==DCE);p=next(c for c in w['candidates'] if c['id']==PES)
        assert d['stage']=='training' and d['code_commit']==u.SOURCE
        assert p['stage']=='blocked' and p['blocker_kind']=='exclusive_gpu_slot'
        d['current_live_observation']={'recorded_at':now,'evidence':u.ref(obs),'independent_review':u.ref(peer),'original_pid':1327826,'original_start_ticks':81524190,'native_step_before':samples[0]['last_native_step'],'native_step_after':samples[1]['last_native_step'],'precise_native_validation':copy.deepcopy(values),'scope':'Original native live logger only; incomplete training. No checkpoint body, new training, restart or efficacy claim.'}
        p['current_resource_check']={'recorded_at':now,'result':'Original_DCE_GPU0_compute_process_confirmed_busy','evidence':u.ref(obs),'scope':'Dated original training/context observation only. Fresh canonical occupation evidence must follow before finish; no PES native/resource PASS.'}
        for c in (d,p):
            for r in (u.ref(obs),u.ref(peer)):
                if r not in c['evidence']:c['evidence'].append(r)
        w['updated_at']=now;w['last_event_tick']=EXPECTED['generated_at']
        assert all(u.digest(c)==old[c['id']] for c in w['candidates'] if c['id'] not in (DCE,PES))
        u.save(HERE/'current_progress_record_intent.json',{'owner':EXPECTED,'research_work_before_sha256':before,'changed_candidate_ids':[DCE,PES],'observation':u.ref(obs),'independent_review':u.ref(peer),'scope':'Current native progress and physical occupancy observation only; all lifecycle/receipts/queue/index/user/source preserved.'})
        guard();assert sha(path)==before;u.atomic(path,w)
        u.primary_protection(b);u.lifecycle_protection(b)
        u.save(HERE/'current_progress_record_result.json',{'owner':EXPECTED,'status':'CURRENT_READ_ONLY_PROGRESS_RECORDED','research_work_sha256':sha(path),'candidate_count':147,'all_other_candidates_unchanged':True,'all24_lifecycle_and28_user_paths_and_index_preserved':True,'observation':u.ref(obs)})
        print('Original DCE progress recorded; PES remains unrun and resource-held.')
    finally:lock.close()

if __name__=='__main__':main()
