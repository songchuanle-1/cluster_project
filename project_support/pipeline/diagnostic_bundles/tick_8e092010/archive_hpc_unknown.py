"""One exact canonical unknown-terminal archive and record alignment, never restart."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,csv,hashlib,io,json,os,sys
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
EXP='M218-HPC';CID=u.HPC;SOURCE='6282263d805c1741234f97afc981a05aca2ad6e3'
def durable(p,v):
    guard();data=(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');args=ap.parse_args()
    if not args.execute_root:print('DEFAULT_READ_ONLY');return
    guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b)
    obs=u.read(HERE/'hpc_end_and_slot_observation.json');assert obs['owner']==EXPECTED
    assert obs['observation']['process']=={'pid':187081,'exists':False}
    assert obs['observation']['last_TRAIN_progress']==[2,50,3687,4686]
    assert obs['observation']['explicit_early_stop_lines']==[] and obs['observation']['explicit_exception_lines']==[]
    assert obs['reviewed_HPC_readonly_probe']['idle'] is True
    meta=u.read(HERE/'hpc_exact_terminal_archive/exact_log_evidence.json');sem=u.read(HERE/'hpc_exact_terminal_archive/local_terminal_semantics.json')
    log=ROOT/meta['local']['path'];assert sha(log)==meta['remote']['sha256']==meta['local']['sha256']=='b42505d31ebc7a7b49e12bc4db5c828605ac56f28c2ef3afc3ecfefbc460f826'
    assert meta['remote']['original_pid_absent_before_after'] is True and meta['remote']['same_config_processes']==[]
    assert sem['end_markers_in_last16KB']==[]
    assert sha(ROOT/'pipeline/admissions/M218-HPC.json')=='41e648d669684de525270f69b696af7540b21dfb5ceec186f0132e8682b17b8c'
    assert not (HERE/'hpc_finalize_intent.json').exists() and not (HERE/'hpc_finalize_result.json').exists()
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();u.primary_protection(b)
        queue=mon.load_queue(str(ROOT));task=next(t for rows in queue['gpu_queues'].values() for t in rows if t.get('id')==EXP)
        assert task['status']=='running' and task['pid']==187081 and task['code_commit']==SOURCE and str(task['gpu'])=='0'
        assert task['admission_receipt']=='pipeline/admissions/M218-HPC.json' and task['launch_verified'] is True
        before_queue=copy.deepcopy(queue);before_running=mon.load_running(str(ROOT));before_ledgers={n:sha(ROOT/'pipeline'/n) for n in b['protected_ledgers']}
        work=u.read(ROOT/'pipeline/research_work.json');before_work=copy.deepcopy(work);assert len(work['candidates'])==145
        c=next(c for c in work['candidates'] if c['id']==CID);assert c['stage']=='training' and c['code_commit']==SOURCE
        journal=ROOT/'pipeline/archive_pending'/(hashlib.sha256(EXP.encode()).hexdigest()+'.json');assert not journal.exists()
        durable(HERE/'hpc_finalize_intent.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'task':task,
            'exact_log':meta['local'],'observation':u.ref(HERE/'hpc_end_and_slot_observation.json'),
            'scope':'One canonical stopped_unknown archive: no normal end/error marker, original process gone. Cause UNKNOWN; no OOM/mechanism falsification or recovery inference.',
            'protected_ledgers_before':before_ledgers,'candidate_digests_before':{x['id']:u.digest(x) for x in work['candidates']}})
        original=mon.pull_log
        def exact_pull(project_dir,host,user,remote_log,cfg_name,state,srv_name=''):
            assert Path(project_dir).resolve()==ROOT.resolve()
            assert (host,user,remote_log,cfg_name,state,srv_name)==('192.168.1.115','songcl',task['log'],Path(task['config']).stem,'stopped_unknown','server-4')
            assert sha(log)==meta['local']['sha256'];return str(log)
        mon.pull_log=exact_pull;events=[]
        try:mon.finalize_task(str(ROOT),queue,'server-4','192.168.1.115','songcl',task,Path(task['config']).stem,'stopped_unknown',0.2811,'2/50','0',task['log'],events)
        finally:mon.pull_log=original
        exp=mon.load_experiment(str(ROOT),EXP)
        assert exp['status']=='stopped_unknown' and exp['code_commit']==SOURCE and exp['final_best']=='0.2811' and exp['epochs_final']=='2/50'
        assert exp['log_local']==str(log) and exp['admission_receipt']=='pipeline/admissions/M218-HPC.json'
        if exp.get('training_status')!='stopped_unknown':exp['training_status']='stopped_unknown';mon.save_experiment(str(ROOT),exp)
        now=datetime.now(timezone.utc).isoformat();c.update(stage='complete',training_status='stopped_unknown',finished_at=exp['finished_at'],
            final_best_miou=0.2810768485069275,epochs_final='2/50',terminal_archive_id=exp['archive_id'],completion_outcome='incomplete_training_stop_cause_unknown',
            next_action='Preserve exact original source6282, passed technical gates, epoch1 validation and full stopped_unknown log. No normal-earlystop/OOM/hypothesis rejection or automatic restart/resume inference. Any recovery needs a concrete checkpoint/source/resource plan and its required authorization; continue independent APF preparation.')
        c['terminal_assessment']={'recorded_at':now,'state':'stopped_unknown','last_native_epoch':2,'last_native_step':3687,'steps_per_epoch':4686,
            'native_validation_values':[0.2810768485069275],'best_scope':'Only one epoch1 validation; not converged/final method efficacy','root_cause':'UNKNOWN',
            'explicit_normal_or_error_end_marker':False,'hypothesis_falsified':False,'automatic_recovery_authorized':False}
        c.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_current_resource_check':copy.deepcopy(c.get('current_resource_check'))})
        c['current_resource_check']={'recorded_at':now,'result':'original_HPC_ended_registered_slot_canonically_cleared','evidence':u.ref(HERE/'hpc_end_and_slot_observation.json'),
            'scope':'Actual prior physicalGPU0 idle snapshot is dated; no future idle permission or signal. Root must recheck before APF.'}
        for ref in [u.ref(HERE/'hpc_end_and_slot_observation.json'),u.ref(HERE/'hpc_exact_terminal_archive/exact_log_evidence.json'),u.ref(log)]:
            if ref not in c['evidence']:c['evidence'].append(ref)
        work['updated_at']=now;work['last_terminal_event']={'recorded_at':now,'experiment_id':EXP,'status':'stopped_unknown','archive_id':exp['archive_id'],'cause':'UNKNOWN'}
        assert all(u.digest(x)==u.digest(next(y for y in before_work['candidates'] if y['id']==x['id'])) for x in work['candidates'] if x['id']!=CID)
        u.atomic(ROOT/'pipeline/research_work.json',work)
        q=mon.load_queue(str(ROOT));running=mon.load_running(str(ROOT))
        assert not any(t.get('id')==EXP for rows in q['gpu_queues'].values() for t in rows) and not journal.exists()
        old_other=copy.deepcopy(before_queue)
        for rows in old_other['gpu_queues'].values():rows[:]=[t for t in rows if t.get('id')!=EXP]
        assert q==old_other
        allowed={'queue.json','running.json','experiments.csv','experiments/M218-HPC.json'}
        assert all(sha(ROOT/'pipeline'/n)==h for n,h in before_ledgers.items() if n not in allowed)
        u.primary_protection(b)
        durable(HERE/'hpc_finalize_result.json',{'owner':EXPECTED,'recorded_at':now,'status':'CANONICAL_STOPPED_UNKNOWN_AND_RESEARCH_TERMINAL_RECORDED',
            'experiment_id':EXP,'archive_id':exp['archive_id'],'state':'stopped_unknown','printed_best':'0.2811','exact_logger_best':0.2810768485069275,
            'epochs':'2/50','last_native_step':3687,'root_cause':'UNKNOWN','exact_full_log':meta['local'],'events':events,
            'no_signals_restart_or_new_training':True,'other_candidates_and_lifecycle_preserved':True})
        print(json.dumps({'state':'stopped_unknown','archive_id':exp['archive_id'],'result':u.ref(HERE/'hpc_finalize_result.json')}))
    finally:lock.close()
if __name__=='__main__':main()
