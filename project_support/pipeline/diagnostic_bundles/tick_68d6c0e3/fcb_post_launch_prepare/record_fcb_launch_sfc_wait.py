"""Record actual FCB progress and actual SFC local parent readiness; default no action."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse, copy, hashlib, json, os, re, sys
TICK=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(TICK))
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
FCB='hierarchy-fine-coarse-complete-bipartite-composition'
SFC='hierarchy-synchronous-full-neighbor-composition'
SOURCE='d4d062ef075abfe7cde93d4b4347ce146572762f'
SFC_CODE='c9be548699cd66bf68badff9ae6198a03eafa142'

def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def checked(e):
    assert isinstance(e,dict) and re.fullmatch('[0-9a-f]{64}',str(e.get('sha256','')))
    p=(ROOT/e['path']).resolve();assert p.is_relative_to(ROOT.resolve()) and sha(p)==e['sha256']
    return p,u.read(p)
def write_new(p,data):
    guard()
    with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def step(sample):return sample.get('last_native_step',sample.get('max_native_step'))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute-root',action='store_true');ap.add_argument('--inputs');ap.add_argument('--inputs-sha256')
    a=ap.parse_args()
    if not a.execute_root:print('DEFAULT_NO_POST_LAUNCH_RECORD_WRITE');return
    guard();assert sys.dont_write_bytecode and os.environ.get('GIT_OPTIONAL_LOCKS')=='0'
    ip=Path(a.inputs).resolve();assert ip.is_relative_to(TICK) and sha(ip)==a.inputs_sha256
    v=u.read(ip);assert v['owner']==EXPECTED
    required=('progress','launch_peer','process_identity','SFC_local_parent_guard','post_launch_baseline','source_ff','admission_receipt','native_smoke')
    actual={k:checked(v[k]) for k in required}
    pid,start=v['pid'],v['start_ticks'];assert type(pid) is int and pid>0 and type(start) is int and start>0
    progress,ob=actual['progress'];peer,pv=actual['launch_peer'];identity,iv=actual['process_identity'];local,lv=actual['SFC_local_parent_guard'];bp,b=actual['post_launch_baseline'];ffp,ff=actual['source_ff'];receipt,rv=actual['admission_receipt'];smokep,smoke=actual['native_smoke']
    assert pv['material_concerns']==[] and pv['candidate_id']==FCB and pv['code_commit']==SOURCE
    assert ob['owner']==iv['owner']==EXPECTED and ob['returncode']==iv['returncode']==0
    assert ob['observation'].get('runtime_commit',ob['observation'].get('runtime_code_commit'))==SOURCE
    identity_value=iv['observation'];assert identity_value['pid']==pid and int(identity_value['start_ticks'])==start and identity_value['runtime_commit']==SOURCE
    samples=ob['observation']['samples'];before,after=step(samples[0]),step(samples[-1])
    assert before==v['native_step_before'] and after==v['native_step_after'] and len(before)==len(after)==2 and all(type(x) is int for x in before+after) and tuple(after)>tuple(before)
    assert lv['status']=='ACTUAL_PARENT_PROMOTION_LOCAL_GUARD_PASSED_NOT_GPU_IDLE' and lv['transport_calls']==0
    assert rv['id']=='M223-FCB' and rv['candidate_id']==FCB and rv['code_commit']==SOURCE and rv['profile']=='experiment_first'
    assert sha(ROOT/'pipeline/admissions/M222-AOC.json')=='bf4426ca1b9251ed850de7d8a13f643a26de14ef59a1329c345140d4436a1778'
    assert ff['HEAD']==SOURCE and ff['only_nine_tested_additions'] is True and len(ff['source_paths'])==9
    assert b['head']==SOURCE and len(b['files'])==28 and len(b['protected_ledgers'])==30 and b['index_empty'] is True
    repo=ROOT/'Cluster';index=Path(u.git(repo,'rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else repo/index
    def protect():
        guard();assert u.git(repo,'rev-parse','HEAD').decode().strip()==SOURCE
        assert u.git(repo,'status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex'] and not u.git(repo,'diff','--cached','--name-only','-z')
        assert sha(index)==b['index_sha256'] and all(sha(repo/n)==h for n,h in b['files'].items())
        assert all(sha(repo/n)==h for n,h in ff['source_paths'].items()) and all(sha(ROOT/'pipeline'/n)==h for n,h in b['protected_ledgers'].items())
    intent=TICK/'fcb_launch_sfc_wait_record_intent.json';result=TICK/'fcb_launch_sfc_wait_record_result.json';post=TICK/'post_fcb_launch_baseline.json'
    assert not any(p.exists() for p in (intent,result,post)),'Existing/partial record is never replayed'
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        protect();path=ROOT/'pipeline/research_work.json';old_sha=sha(path);work=u.read(path);old={c['id']:u.digest(c) for c in work['candidates']};assert len(old)==151
        c=next(x for x in work['candidates'] if x['id']==FCB);s=next(x for x in work['candidates'] if x['id']==SFC)
        assert c['code_commit']==SOURCE and c['stage'] in ('training','deployment') and s['code_commit']==SFC_CODE
        q=mon.load_queue(str(ROOT));tasks=[t for rows in q['gpu_queues'].values() for t in rows]
        live=next(t for t in tasks if t.get('id')=='M223-FCB');paused=next(t for t in tasks if t.get('id')=='M206-CGCA')
        assert live['status']=='running' and live['pid']==pid and live['launch_verified'] is True and live['launch_verification']=='training_progress' and str(live['gpu'])=='0'
        assert mon.load_running(str(ROOT))['server-4']['0']=='M223-FCB' and paused['status']=='waiting' and paused['dispatch_hold'] and paused.get('pid') is None
        now=datetime.now(timezone.utc);c.update(stage='training',training_status='running',source_status='EXACT_TESTED_FCB_PRESENT_PRIMARY_AND_VERIFIED_REMOTE_RUNTIME')
        c['current_live_observation']={'recorded_at':now.isoformat(),'evidence':u.ref(progress),'independent_review':u.ref(peer),'original_pid':pid,'original_start_ticks':start,'native_step_before':before,'native_step_after':after,'precise_native_validation':copy.deepcopy(ob.get('precise_native_validation')),'scope':'Actual original canonical FCB formal native growth; technical admission is not efficacy or repair of prior failures.'}
        c['next_action']='Monitor exact original FCB PID/start/log/source d4 on GPU0 through natural completion. Do not replay dispatch or change schedule; GPU1 forbidden and all prior archives/holds retained.'
        for e in (u.ref(progress),u.ref(peer),u.ref(identity),u.ref(receipt)):
            if e not in c['evidence']:c['evidence'].append(e)
        s.setdefault('version_compatibility_history',[]).append(copy.deepcopy(s.get('current_version_compatibility')))
        s['current_version_compatibility']={'recorded_at':now.isoformat(),'current_source_commit':SFC_CODE,'current_parent_commit':SOURCE,'runtime_expected_commit':SOURCE,'current_primary_and_runtime':SOURCE,'status':'ACTUAL_FCB_PARENT_PROMOTED_LOCAL_GUARD_PASSED_GPU0_OCCUPIED_BY_FCB','FCB_technical_receipt':u.ref(receipt),'local_parent_guard':u.ref(local),'physical_occupation_scope':u.ref(progress),'scope':'Parent technical receipt/source promotion ready; SFC native/resources NOT_RUN. Fresh compatible parent/owner/idle/UUID/assets/three locks remain required; no FCB completion/effect gate.'}
        s.update(stage='blocked',blocker_kind='exclusive_gpu_slot',blocked_from_stage='validation',resume_stage='validation',required_server='server-4',required_physical_gpu=0,blocked_at=now.isoformat(),retry_after=(now+timedelta(hours=1)).isoformat(),blocker='Sole authorized GPU0 is occupied by the original admitted FCB. SFC parent d4 is now promoted; its native/resources remain NOT_RUN.',unblock_condition='Original FCB naturally frees GPU0, then fresh current owner/original deadline and compatible source/runtime/UUID/assets/idle/three locks permit SFC checks; no GPU1, eviction or replay.',native_status='NOT_RUN_GPU0_OCCUPIED_BY_ORIGINAL_FCB',resource_status='NOT_RUN_GPU0_OCCUPIED_BY_ORIGINAL_FCB',source_status='ISOLATED_SFC_SOURCE_VALID_PARENT_PROMOTED_NATIVE_NOT_RUN',next_action='Wait for original FCB GPU0 task to finish naturally, then perform original SFC paired TRAIN2/resources with fresh owner and actual compatible d4 runtime/idle/assets/three locks. No SFC admission before genuine passes.')
        for e in (u.ref(local),u.ref(progress),u.ref(peer),u.ref(receipt)):
            if e not in s['evidence']:s['evidence'].append(e)
        work['updated_at']=now.isoformat();work['last_event_tick']=EXPECTED['generated_at'];work['next_action']=c['next_action']
        work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':FCB,'kind':'native_smoke','result':'passed','command':smoke['command'],'observation':'Actual original paired TRAIN2/resources independently reviewed, one canonical FCB launch and strict native growth. SFC parent ready/GPU0 occupied; efficacy UNKNOWN.','evidence':[u.ref(smokep),u.ref(progress),u.ref(peer)]}
        assert all(u.digest(x)==old[x['id']] for x in work['candidates'] if x['id'] not in (FCB,SFC))
        data=encoded(work);after_sha=hashlib.sha256(data).hexdigest();pb=copy.deepcopy(b);pb.update(owner=EXPECTED,recorded_at=now.isoformat(),research_work_sha256=after_sha,candidate_digests={x['id']:u.digest(x) for x in work['candidates']},current_candidate_source_paths=ff['source_paths'],exact_tested_nine_source_paths=ff['source_paths'],native_progress=u.ref(progress),source_ff=u.ref(ffp))
        journal=encoded({'owner':EXPECTED,'research_work_before_sha256':old_sha,'inputs':u.ref(ip),'changed_candidate_ids':[FCB,SFC],'partial_replay_forbidden':True})
        result_bytes=encoded({'owner':EXPECTED,'status':'ACTUAL_FCB_TRAINING_AND_SFC_PARENT_READY_GPU0_WAIT_RECORDED','candidate_count':151,'other149_candidates_unchanged':True,'protected30_lifecycle_and28_user_paths_and_postff_index_preserved':True})
        post_bytes=encoded(pb);tmp=path.with_name(path.name+'.68d6c0e3.record.tmp');assert not tmp.exists()
        protect();assert sha(path)==old_sha and not any(p.exists() for p in (intent,result,post))
        write_new(intent,journal);write_new(tmp,data);guard();os.replace(tmp,path)
        protect();assert sha(path)==after_sha;write_new(post,post_bytes);write_new(result,result_bytes)
        print({'status':'RECORDED_ACTUAL_FCB_PROGRESS_AND_SFC_WAIT','result':u.ref(result),'post_launch_baseline':u.ref(post)})
    finally:lock.close()

if __name__=='__main__':main()
