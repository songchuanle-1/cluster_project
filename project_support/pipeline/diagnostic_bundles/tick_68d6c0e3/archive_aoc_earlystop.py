"""One canonical archive of the verified original AOC normal early stop."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, hashlib, json, os, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent;EXP='M222-AOC';CID='hierarchy-ancestral-order-commutator-composition'
SOURCE=u.SOURCE;STATE='done_earlystop';BEST=0.5000720620155334

def durable(p,v):
    guard()
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--peer-sha256');a=ap.parse_args()
    if not a.execute_root:print('DEFAULT_NO_ARCHIVE');return
    guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b)
    path=HERE/'aoc_end_and_slot_observation.json';assert sha(path)=='73a4bbac11faa8872b9687966c7b120f0dfde929f4566fd3d3ebbc7ffeb2e416'
    ob=u.read(path);o=ob['observation'];assert ob['owner']==EXPECTED and o['process']=={'pid':3437349,'exists':False}
    assert o['last_TRAIN_progress']==[30,50,4686,4686] and o['explicit_exception_lines']==[]
    assert any('Early stopping at epoch 30: no improvement for 10 epochs (best=0.5001)' in x for x in o['explicit_early_stop_lines'])
    assert len(ob['precise_native_validation']['values'])==30 and ob['precise_native_validation']['best']==BEST and ob['precise_native_validation']['no_improve']==10
    meta=u.read(HERE/'aoc_exact_terminal_archive/exact_log_evidence.json');log=ROOT/meta['local']['path']
    assert sha(log)==meta['remote']['sha256']==meta['local']['sha256']=='f44d1fd647884e83fc0232afe618c1997b4e10f40c38454dbaa91da6d701e370'
    assert meta['remote']['original_pid_absent_before_after'] and meta['remote']['same_config_processes']==[]
    assert 'Early stopping at epoch 30: no improvement for 10 epochs (best=0.5001)' in log.read_bytes()[-16000:].decode('utf8',errors='replace')
    assert sha(ROOT/'pipeline/admissions/M222-AOC.json')=='bf4426ca1b9251ed850de7d8a13f643a26de14ef59a1329c345140d4436a1778'
    peer=HERE/'aoc_terminal_independent_review.json';assert sha(peer)==a.peer_sha256 and u.read(peer)['material_concerns']==[]
    assert not any((HERE/n).exists() for n in ('aoc_finalize_intent.json','aoc_finalize_result.json'))
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();u.primary_protection(b);queue=mon.load_queue(str(ROOT));task=next(t for rows in queue['gpu_queues'].values() for t in rows if t.get('id')==EXP)
        assert task['status']=='running' and task['pid']==3437349 and task['code_commit']==SOURCE and str(task['gpu'])=='0' and task['launch_verified']
        before_queue=copy.deepcopy(queue);ledgers={n:sha(ROOT/'pipeline'/n) for n in b['protected_ledgers']}
        work=u.read(ROOT/'pipeline/research_work.json');old={c['id']:u.digest(c) for c in work['candidates']};assert len(old)==151
        c=next(x for x in work['candidates'] if x['id']==CID);assert c['stage']=='training' and c['code_commit']==SOURCE
        journal=ROOT/'pipeline/archive_pending'/(hashlib.sha256(EXP.encode()).hexdigest()+'.json');assert not journal.exists()
        durable(HERE/'aoc_finalize_intent.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'task':task,'exact_log':meta['local'],'observation':u.ref(path),'independent_review':u.ref(peer),'protected_ledgers_before':ledgers,'candidate_digests_before':old,'scope':'One canonical original normal early-stop archive; keep receipt and all source/launch/technical evidence. No signals, source patch, restart/resume or new training.'})
        original=mon.pull_log
        def exact_pull(project_dir,host,user,remote_log,cfg_name,state,srv_name=''):
            assert Path(project_dir).resolve()==ROOT.resolve() and (host,user,remote_log,cfg_name,state,srv_name)==('192.168.1.115','songcl',task['log'],Path(task['config']).stem,STATE,'server-4')
            assert sha(log)==meta['local']['sha256'];return str(log)
        mon.pull_log=exact_pull;events=[]
        try:mon.finalize_task(str(ROOT),queue,'server-4','192.168.1.115','songcl',task,Path(task['config']).stem,STATE,0.5001,'30/50','0',task['log'],events)
        finally:mon.pull_log=original
        exp=mon.load_experiment(str(ROOT),EXP);assert exp['status']==STATE and exp['code_commit']==SOURCE and exp['final_best']=='0.5001' and exp['epochs_final']=='30/50' and exp['log_local']==str(log)
        if exp.get('training_status')!=STATE:exp['training_status']=STATE;mon.save_experiment(str(ROOT),exp)
        now=datetime.now(timezone.utc).isoformat();c.setdefault('admission_status_history',[]).append({'recorded_at':now,'admission_status':c.get('admission_status')})
        c.update(stage='complete',training_status=STATE,admission_status='ADMITTED_NORMAL_EARLYSTOP_ARCHIVED',queued=False,finished_at=exp['finished_at'],final_best_miou=BEST,epochs_final='30/50',terminal_archive_id=exp['archive_id'],completion_outcome='normal_earlystop_no_gain_vs_M95_on_registered_seed',next_action='Preserve original AOC source0314, technical gates/receipt, launch evidence and exact full log. Registered seed1999 best0.5000720620155334 is below M95 0.5020; no gain on this realization, no new champion or automatic restart. Advance independent FCB on fresh authorized idle GPU0 checks.')
        c['terminal_assessment']={'recorded_at':now,'state':STATE,'last_native_epoch':30,'last_native_step':4686,'steps_per_epoch':4686,'native_validation_values':ob['precise_native_validation']['values'],'exact_best':BEST,'no_improve':10,'explicit_native_early_stop':True,'matched_M95_reference':0.5020,'delta_vs_M95':BEST-0.5020,'scope':'Registered single-seed structural realization did not improve M95. This is not a universal claim against hierarchical interaction. No new seed/recovery authorized by archival.'}
        c.setdefault('resource_check_history',[]).append(copy.deepcopy(c.get('current_resource_check')))
        c['current_resource_check']={'recorded_at':now,'result':'original_AOC_normal_earlystop_registered_slot_canonically_cleared','evidence':u.ref(path),'scope':'Dated physicalGPU0 idle proof only. Every new native operation must perform fresh idle/source/UUID/three-lock guards.'}
        for r in [u.ref(path),u.ref(HERE/'aoc_exact_terminal_archive/exact_log_evidence.json'),u.ref(log),u.ref(peer)]:
            if r not in c['evidence']:c['evidence'].append(r)
        work['updated_at']=now;work['last_terminal_event']={'recorded_at':now,'experiment_id':EXP,'status':STATE,'archive_id':exp['archive_id']}
        assert all(u.digest(x)==old[x['id']] for x in work['candidates'] if x['id']!=CID);u.atomic(ROOT/'pipeline/research_work.json',work)
        q=mon.load_queue(str(ROOT));expected_queue=copy.deepcopy(before_queue)
        for rows in expected_queue['gpu_queues'].values():rows[:]=[t for t in rows if t.get('id')!=EXP]
        assert q==expected_queue and not journal.exists()
        assert all(sha(ROOT/'pipeline'/n)==h for n,h in ledgers.items() if n not in {'queue.json','running.json','experiments.csv','experiments/M222-AOC.json'})
        u.primary_protection(b)
        post=dict(b);post.update(owner=EXPECTED,recorded_at=now,protected_ledgers={n:sha(ROOT/'pipeline'/n) for n in ledgers},candidate_digests={x['id']:u.digest(x) for x in work['candidates']},research_work_sha256=sha(ROOT/'pipeline/research_work.json'),original_AOC_terminal=u.ref(path))
        durable(HERE/'post_aoc_terminal_baseline.json',post)
        durable(HERE/'aoc_finalize_result.json',{'owner':EXPECTED,'recorded_at':now,'status':'CANONICAL_NORMAL_EARLYSTOP_AND_RESEARCH_TERMINAL_RECORDED','experiment_id':EXP,'archive_id':exp['archive_id'],'state':STATE,'printed_best':'0.5001','exact_logger_best':BEST,'epochs':'30/50','exact_full_log':meta['local'],'events':events,'no_signals_restart_patch_or_new_training':True,'other_candidates_and_lifecycle_preserved':True})
        print(json.dumps({'state':STATE,'archive_id':exp['archive_id'],'result':u.ref(HERE/'aoc_finalize_result.json')}))
    finally:lock.close()

if __name__=='__main__':main()
