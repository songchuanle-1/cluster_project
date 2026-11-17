"""Archive only the observed original FCB startup exit; default is inert."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, hashlib, json, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent
EXP='M223-FCB';CID='hierarchy-fine-coarse-complete-bipartite-composition'
SOURCE='d4d062ef075abfe7cde93d4b4347ce146572762f';STATE='stopped_unknown'

def protect(b):
    guard();repo=ROOT/'Cluster'
    assert u.git(repo,'rev-parse','HEAD').decode().strip()==SOURCE==b['head']
    assert u.git(repo,'status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex']
    assert not u.git(repo,'diff','--cached','--name-only','-z')
    index=Path(u.git(repo,'rev-parse','--git-path','index').decode().strip())
    if not index.is_absolute():index=repo/index
    assert sha(index)==b['index_sha256']
    assert all(sha(repo/n)==h for n,h in {**b['files'],**b['exact_tested_nine_source_paths']}.items())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--peer');ap.add_argument('--peer-sha256');a=ap.parse_args()
    if not a.execute_root:print('DEFAULT_NO_ARCHIVE');return
    guard();b=u.read(HERE/'post_fcb_dispatch_baseline.json');protect(b);u.lifecycle_protection(b)
    peer=Path(a.peer);assert peer.resolve().is_relative_to(HERE) and sha(peer)==a.peer_sha256
    pv=u.read(peer);assert pv['canonical_archive_boundary']['archive_blockers']==[]
    assert pv['owner']==EXPECTED and pv['candidate_id']==CID and pv['code_commit']==SOURCE
    assert pv['disposition']['canonical_state']==STATE and pv['disposition']['root_cause']=='UNKNOWN'
    identity=HERE/'fcb_launch_identity_readback.json';i=u.read(identity);assert i['owner']==EXPECTED
    ob=i['observation'];assert not ob['reported_pid_exists'] and ob['matching_owned_processes']==[] and ob['GPU0_contexts']==''
    assert ob['remote_head']==SOURCE and ob['locks']==dict.fromkeys(('training','diagnostic','exclusive'),'available')
    assert ob['log_bytes']==41707 and ob['log_sha256']=='5289333a5ace29a777e0b1c5c331247de32cb53df279174c31442a8dd9fcfad9'
    meta=u.read(HERE/'fcb_launch_exact_log/exact_log_evidence.json');log=ROOT/meta['local']['path']
    assert sha(log)==meta['local']['sha256']==ob['log_sha256']
    assert meta['remote']['original_pid_absent_before_after'] and meta['remote']['same_config_processes']==[]
    native=HERE/'fcb_native_startup_log_readback.json';n=u.read(native);assert n['owner']==EXPECTED
    rows=n['observation']['native_logs'];assert len(rows)==1 and rows[0]['bytes']==293
    assert rows[0]['sha256']=='37a745f2a43de6120be6159fd83e2f9e56db06adee9edb318a08b1b322609195'
    assert 'Train batch size per gpu: 2' in rows[0]['text']
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon;import closure
    assert closure.steps(log.read_text('utf8'))==[] and closure.steps(rows[0]['text'])==[]
    dispatch=u.read(HERE/'fcb_dispatch_result.json');assert dispatch['canonical_dispatch_invoked_once'] and not dispatch['verified_native_progress']
    calls=u.read(HERE/'fcb_dispatch_transport_calls.json');assert sum(x['canonical_native_launch_request'] is True for x in calls)==1
    receipt=ROOT/'pipeline/admissions/M223-FCB.json';assert sha(receipt)=='189f8d89fcaec6a2079e74a2af6bd378c2df184ef68798d0cace260d8433d9b6'
    assert not any((HERE/x).exists() for x in ('fcb_finalize_intent.json','fcb_finalize_result.json','post_fcb_terminal_baseline.json'))
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        protect(b);u.lifecycle_protection(b);q=mon.load_queue(str(ROOT));before=copy.deepcopy(q)
        task=next(t for rows in q['gpu_queues'].values() for t in rows if t.get('id')==EXP)
        assert task==dispatch['task_after'] and task['status']=='claiming' and task['pid']==3190302 and task['code_commit']==SOURCE and not task['launch_verified']
        work=u.read(ROOT/'pipeline/research_work.json');old={c['id']:u.digest(c) for c in work['candidates']};assert len(old)==151
        c=next(x for x in work['candidates'] if x['id']==CID);assert c['stage']=='deployment' and c['code_commit']==SOURCE
        refs=[u.ref(identity),u.ref(HERE/'fcb_launch_exact_log/exact_log_evidence.json'),u.ref(log),u.ref(native),u.ref(peer),u.ref(HERE/'fcb_readonly_kernel_diagnostic.json')]
        journal=ROOT/'pipeline/archive_pending'/(hashlib.sha256(EXP.encode()).hexdigest()+'.json');assert not journal.exists()
        u.save(HERE/'fcb_finalize_intent.json',dict(owner=EXPECTED,recorded_at=datetime.now(timezone.utc).isoformat(),task=task,evidence=refs,protected_ledgers_before=b['protected_ledgers'],candidate_digests_before=old,scope='One original launch terminal archive. No retry, signal, source patch, checkpoint recovery, or model rejection.'))
        original=mon.pull_log
        def exact_pull(project_dir,host,user,remote_log,cfg_name,state,srv_name=''):
            assert Path(project_dir).resolve()==ROOT.resolve()
            assert(host,user,remote_log,cfg_name,state,srv_name)==('192.168.1.115','songcl',task['log'],Path(task['config']).stem,STATE,'server-4')
            assert sha(log)==ob['log_sha256'];return str(log)
        mon.pull_log=exact_pull;events=[]
        try:mon.finalize_task(str(ROOT),q,'server-4','192.168.1.115','songcl',task,Path(task['config']).stem,STATE,None,'?','0',task['log'],events)
        finally:mon.pull_log=original
        exp=mon.load_experiment(str(ROOT),EXP);assert exp['status']==STATE and exp['final_best']=='?' and exp['launch_verified'] is False
        exp.update(training_status=STATE,pid=task['pid'],log=task['log'],failure_scope='runtime_startup_inconclusive',root_cause='UNKNOWN',original_launch_attempt=copy.deepcopy(task),terminal_evidence=refs)
        mon.save_experiment(str(ROOT),exp)
        now=datetime.now(timezone.utc).isoformat()
        c.update(stage='complete',training_status=STATE,admission_status='ADMITTED_ORIGINAL_STARTUP_EXIT_ARCHIVED',queued=False,finished_at=exp['finished_at'],final_best_miou=None,epochs_final='UNKNOWN_NO_OBSERVED_TRAIN',terminal_archive_id=exp['archive_id'],failure_scope='runtime_startup_inconclusive',root_cause='UNKNOWN',completion_outcome='Original process gone before observed TRAIN; technical native gates remain valid, trained efficacy UNKNOWN.',next_action='Preserve exact original launch logs, source d4, native four-arm checks and technical receipt. Diagnose startup exit from original evidence before a concrete safe recovery plan; never blind-relaunch. Advance independent SFC on a fresh adequate owner window and GPU0 checks.')
        c['terminal_assessment']=dict(recorded_at=now,state=STATE,observed_TRAIN_steps=[],validation_values=None,final_best=None,root_cause='UNKNOWN',native_logger=rows[0]['path'],warning_not_proven_fatal=True,no_recovery_or_model_rejection=True)
        for r in refs:
            if r not in c['evidence']:c['evidence'].append(r)
        smoke=HERE/'fcb_native_smoke.json';sm=u.read(smoke)
        work.update(updated_at=now,last_terminal_event=dict(recorded_at=now,experiment_id=EXP,status=STATE,archive_id=exp['archive_id']))
        work['tick_attempt']=dict(tick_started_at=EXPECTED['generated_at'],candidate_id=CID,kind='native_smoke',result='passed',command=sm['command'],observation='Actual paired native TRAIN2 and wholemodel resources passed independently. Canonical formal launch requested once, then exited before observed TRAIN; cause/validation/efficacy UNKNOWN. No retry.',evidence=[u.ref(smoke),u.ref(HERE/'fcb_actual_four_result_review.json'),u.ref(peer)])
        for r in work['tick_attempt']['evidence']:
            if r not in c['evidence']:c['evidence'].append(r)
        assert all(u.digest(x)==old[x['id']] for x in work['candidates'] if x['id']!=CID)
        u.atomic(ROOT/'pipeline/research_work.json',work)
        after=mon.load_queue(str(ROOT));expected=copy.deepcopy(before)
        for rows0 in expected['gpu_queues'].values():rows0[:]=[t for t in rows0 if t.get('id')!=EXP]
        assert after==expected and not journal.exists()
        assert all(sha(ROOT/'pipeline'/n)==h for n,h in b['protected_ledgers'].items() if n not in {'queue.json','running.json','experiments.csv','experiments/M223-FCB.json'})
        protect(b);post=copy.deepcopy(b);post.update(recorded_at=now,protected_ledgers={n:sha(ROOT/'pipeline'/n) for n in b['protected_ledgers']},candidate_digests={x['id']:u.digest(x) for x in work['candidates']},research_work_sha256=sha(ROOT/'pipeline/research_work.json'))
        u.save(HERE/'post_fcb_terminal_baseline.json',post)
        u.save(HERE/'fcb_finalize_result.json',dict(owner=EXPECTED,recorded_at=now,status='CANONICAL_ORIGINAL_STARTUP_EXIT_ARCHIVED_UNKNOWN_CAUSE',experiment_id=EXP,archive_id=exp['archive_id'],state=STATE,observed_TRAIN_steps=[],best_miou=None,evidence=refs,events=events,technical_gates_and_receipt_preserved=True,no_signal_restart_patch_recovery_or_model_rejection=True,other_candidates_and_ledgers_preserved=True))
        print(json.dumps(dict(state=STATE,archive_id=exp['archive_id'],result=u.ref(HERE/'fcb_finalize_result.json'))))
    finally:lock.close()

if __name__=='__main__':main()
