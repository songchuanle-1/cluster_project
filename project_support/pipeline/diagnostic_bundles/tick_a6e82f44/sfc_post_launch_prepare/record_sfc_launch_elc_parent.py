"""Default NOP. Record only real SFC GPU1 growth and ELC technical-parent readiness."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,os,re,sys
TICK=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(TICK))
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
DRAFT_EXECUTION_DISABLED=True
SFC='hierarchy-synchronous-full-neighbor-composition'
ELC='hierarchy-undirected-edge-state-line-graph-composition'
SOURCE='c9be548699cd66bf68badff9ae6198a03eafa142'
ELC_CODE='18e64b8d95ed0ba5c1053ead114c0f91a4b0c324'
PEER_STATUS='SFC_ORIGINAL_GPU1_TRAINING_PROGRESS_INDEPENDENTLY_VALIDATED'

def encoded(value):return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
def checked(entry):
    assert isinstance(entry,dict) and isinstance(entry.get('path'),str) and re.fullmatch('[0-9a-f]{64}',str(entry.get('sha256','')))
    path=(ROOT/entry['path']).resolve();assert path.is_relative_to(ROOT.resolve()) and sha(path)==entry['sha256']
    return path,u.read(path)
def write_new(path,data):
    guard()
    with path.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
def step(sample):return sample.get('last_native_step',sample.get('max_native_step'))
def identities(value):
    if 'identity_before' in value:
        assert 'identity_after' in value;return [value['identity_before'],value['identity_after']]
    return [value]
def identity_matches(value,pid,start):
    return value['pid']==pid and type(value['pid']) is int and int(value['start_ticks'])==start

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-root',action='store_true');parser.add_argument('--inputs');parser.add_argument('--inputs-sha256')
    args=parser.parse_args()
    if not args.execute_root:print('DEFAULT_NO_SFC_POST_LAUNCH_RECORD_WRITE');return
    assert not DRAFT_EXECUTION_DISABLED,'Default-disabled draft; root must use a separately reviewed activation copy'
    guard();assert sys.dont_write_bytecode and os.environ.get('GIT_OPTIONAL_LOCKS')=='0'
    assert args.inputs and re.fullmatch('[0-9a-f]{64}',args.inputs_sha256 or '')
    ip=Path(args.inputs).resolve();assert ip.is_relative_to(TICK) and sha(ip)==args.inputs_sha256
    values=u.read(ip);assert values['owner']==EXPECTED
    required=('progress','launch_peer','process_identity','ELC_local_parent_guard','post_launch_baseline','source_ff','admission_receipt','native_smoke')
    actual={key:checked(values[key]) for key in required}
    pid,start=values['pid'],values['start_ticks'];assert type(pid) is int and pid>0 and type(start) is int and start>0 and values['physical_gpu']==1
    pp,progress=actual['progress'];lp,peer=actual['launch_peer'];identityp,identity=actual['process_identity'];gp,local=actual['ELC_local_parent_guard']
    bp,baseline=actual['post_launch_baseline'];ffp,ff=actual['source_ff'];rp,receipt=actual['admission_receipt'];sp,smoke=actual['native_smoke']
    assert peer['status']==PEER_STATUS and peer['material_concerns']==[] and peer['candidate_id']==SFC and peer['code_commit']==SOURCE and peer['owner']==EXPECTED
    assert peer['progress_observation']==u.ref(pp) and peer['process_identity']==u.ref(identityp)
    assert identity_matches(peer['original_process'],pid,start)
    assert progress['owner']==identity['owner']==EXPECTED and progress['returncode']==identity['returncode']==0
    ob=progress['observation'];iv=identity['observation']
    assert ob.get('runtime_commit',ob.get('runtime_code_commit'))==iv.get('runtime_commit',iv.get('runtime_code_commit'))==SOURCE
    assert all(identity_matches(v,pid,start) for v in identities(ob)+identities(iv))
    assert 'GPU1' in ob and 'GPU1_contexts' in ob and 'GPU1' in ob['GPU_queries']
    samples=ob['samples'];before,after=step(samples[0]),step(samples[-1])
    assert len(samples)>=2 and before==values['native_step_before'] and after==values['native_step_after']
    assert len(before)==len(after)==2 and all(type(v) is int for v in before+after) and tuple(after)>tuple(before)
    assert local['owner']==EXPECTED and local['status']=='ACTUAL_PARENT_PROMOTION_LOCAL_GUARD_PASSED_NOT_GPU_IDLE' and local['transport_calls']==0
    assert local['candidate_id']==ELC and local['code_commit']==ELC_CODE and local['expected_runtime_code_commit']==SOURCE
    assert receipt['id']=='M224-SFC' and receipt['candidate_id']==SFC and receipt['code_commit']==SOURCE and receipt['profile']=='experiment_first'
    assert rp.resolve()==(ROOT/'pipeline/admissions/M224-SFC.json').resolve()
    assert smoke['id']=='M224-SFC' and smoke['candidate_id']==SFC and smoke['code_commit']==SOURCE and smoke['steps']==2 and smoke['backward_finite'] is True
    assert ff['HEAD']==SOURCE and ff['only_nine_tested_additions'] is True and len(ff['source_paths'])==9
    assert baseline['owner']==EXPECTED and baseline['head']==SOURCE and baseline['index_empty'] is True and len(baseline['files'])==28 and len(baseline['protected_ledgers'])==32
    assert len(baseline['candidate_digests'])==151 and 'research_work.json' not in baseline['protected_ledgers']
    repo=ROOT/'Cluster';index=Path(u.git(repo,'rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else repo/index
    def protect():
        # Deliberately do not call u.primary_protection: its inherited SOURCE is oldD4.
        guard();assert u.git(repo,'rev-parse','HEAD').decode().strip()==SOURCE
        assert u.git(repo,'status','--porcelain=v1','--untracked-files=all','-z').hex()==baseline['status_hex']
        assert not u.git(repo,'diff','--cached','--name-only','-z') and sha(index)==baseline['index_sha256']
        assert all(sha(repo/n)==h for n,h in baseline['files'].items()) and all(sha(repo/n)==h for n,h in ff['source_paths'].items())
        assert all(sha(ROOT/'pipeline'/n)==h for n,h in baseline['protected_ledgers'].items())
    intent=TICK/'sfc_launch_elc_parent_record_intent.json';result=TICK/'sfc_launch_elc_parent_record_result.json';post=TICK/'post_sfc_launch_baseline.json'
    assert not any(p.exists() for p in (intent,result,post)),'Existing/partial record must be reconciled read-only, never replayed'
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        protect();path=ROOT/'pipeline/research_work.json';old_sha=sha(path);work=u.read(path)
        assert old_sha==baseline['research_work_sha256'] and {c['id']:u.digest(c) for c in work['candidates']}==baseline['candidate_digests']
        original=copy.deepcopy(work);old={c['id']:u.digest(c) for c in work['candidates']};assert len(old)==151
        s=next(c for c in work['candidates'] if c['id']==SFC);e=next(c for c in work['candidates'] if c['id']==ELC)
        assert s['code_commit']==SOURCE and s['stage'] in ('training','deployment') and e['code_commit']==ELC_CODE and e['source_parent_commit']==SOURCE
        assert e['stage']=='validation' and not any(e.get(k) for k in ('human_hold','scope_hold','numerical_hold','dispatch_hold','paused'))
        queue=mon.load_queue(str(ROOT));tasks=[task for rows in queue['gpu_queues'].values() for task in rows]
        live=next(task for task in tasks if task.get('id')=='M224-SFC');paused=next(task for task in tasks if task.get('id')=='M206-CGCA')
        assert live['status']=='running' and live['pid']==pid and live['code_commit']==SOURCE and live['launch_verified'] is True and live['launch_verification']=='training_progress' and str(live['gpu'])=='1'
        assert mon.load_running(str(ROOT))['server-4']['1']=='M224-SFC' and paused['status']=='waiting' and paused['dispatch_hold'] and paused.get('pid') is None
        now=datetime.now(timezone.utc).isoformat();s.update(stage='training',training_status='running',source_status='EXACT_TESTED_SFC_PRESENT_PRIMARY_AND_VERIFIED_REMOTE_RUNTIME')
        s['current_live_observation']={'recorded_at':now,'evidence':u.ref(pp),'independent_review':u.ref(lp),'process_identity':u.ref(identityp),
            'original_pid':pid,'original_start_ticks':start,'physical_gpu':1,'native_step_before':before,'native_step_after':after,
            'precise_native_validation':copy.deepcopy(progress.get('precise_native_validation')),'scope':'Actual original canonical SFC sourceC9 formal GPU1 strict native growth; training incomplete and efficacy unknown, no replay/recovery claim.'}
        s['next_action']='Monitor the exact original SFC PID/start/log/sourceC9 on authorized GPU1 through natural completion. No replay, schedule/data change or other task interference.'
        for entry in (u.ref(pp),u.ref(lp),u.ref(identityp),u.ref(rp)):
            if entry not in s['evidence']:s['evidence'].append(entry)
        if e.get('current_version_compatibility') is not None:e.setdefault('version_compatibility_history',[]).append(copy.deepcopy(e['current_version_compatibility']))
        e['current_version_compatibility']={'recorded_at':now,'current_source_commit':ELC_CODE,'current_parent_commit':SOURCE,'runtime_expected_commit':SOURCE,
            'current_primary_and_runtime':SOURCE,'status':'ACTUAL_SFC_TECHNICAL_PARENT_PROMOTED_LOCAL_GUARD_PASSED_NATIVE_OUTSTANDING',
            'SFC_technical_receipt':u.ref(rp),'local_parent_guard':u.ref(gp),'remote_parent_readback':u.ref(identityp),
            'scope':'Actual SFC technical receipt and testedC9 source/runtime promotion satisfy parent compatibility. ELC native/resources NOT_RUN. ELC diagnostic capability is physicalGPU0, distinct from SFC trainingGPU1; no exclusive-slot blocker is inferred. Fresh selected0 idle/UUID/assets/owner/original deadline/three locks still required at prepare, no parent training completion/efficacy gate.'}
        e.update(stage='validation',native_status='NOT_RUN_ACTUAL_SFC_C9_TECHNICAL_PARENT_READY',resource_status='NOT_RUN_ACTUAL_SFC_C9_TECHNICAL_PARENT_READY',
            source_status='ISOLATED_ELC_SOURCE_VALID_PARENT_TECHNICALLY_PROMOTED_NATIVE_NOT_RUN',required_server='server-4',required_physical_gpu=0,
            next_action='Use a fresh current owner/original window and actual compatible C9 runtime with current policy, selected GPU0 fresh idle/UUID/assets/all three locks to run original ELC paired TRAIN2/resources. SFC runs separately on GPU1; no exclusive_gpu_slot wait or SFC completion/efficacy gate, no ELC admission before actual checks.')
        for entry in (u.ref(gp),u.ref(identityp),u.ref(rp)):
            if entry not in e['evidence']:e['evidence'].append(entry)
        work['updated_at']=now;work['last_event_tick']=EXPECTED['generated_at']
        assert all(u.digest(c)==old[c['id']] for c in work['candidates'] if c['id'] not in (SFC,ELC))
        assert {k:v for k,v in work.items() if k not in ('candidates','updated_at','last_event_tick')}=={k:v for k,v in original.items() if k not in ('candidates','updated_at','last_event_tick')}
        data=encoded(work);after_sha=hashlib.sha256(data).hexdigest();pb=copy.deepcopy(baseline)
        pb.update(owner=EXPECTED,recorded_at=now,research_work_sha256=after_sha,candidate_digests={c['id']:u.digest(c) for c in work['candidates']},
            current_candidate_source_paths=ff['source_paths'],exact_tested_nine_source_paths=ff['source_paths'],native_progress=u.ref(pp),source_ff=u.ref(ffp))
        journal=encoded({'owner':EXPECTED,'research_work_before_sha256':old_sha,'inputs':u.ref(ip),'changed_candidate_ids':[SFC,ELC],'partial_replay_forbidden':True})
        result_bytes=encoded({'owner':EXPECTED,'status':'ACTUAL_SFC_GPU1_TRAINING_AND_ELC_PARENT_READY_VALIDATION_RECORDED','candidate_count':151,
            'other149_candidates_unchanged':True,'protected32_lifecycle_28_user_paths_tested9source_and_postff_index_preserved':True,'ELC_native_resources':'NOT_RUN','ELC_exclusive_gpu_slot_blocker_added':False})
        post_bytes=encoded(pb);tmp=path.with_name(path.name+'.a6e82f44.sfc_record.tmp');assert not tmp.exists()
        protect();assert sha(path)==old_sha and not any(p.exists() for p in (intent,result,post))
        write_new(intent,journal);write_new(tmp,data);protect();guard();os.replace(tmp,path)
        protect();assert sha(path)==after_sha;write_new(post,post_bytes);write_new(result,result_bytes)
        print({'status':'RECORDED_REAL_SFC_GPU1_AND_ELC_PARENT_READY','result':u.ref(result),'post_launch_baseline':u.ref(post)})
    finally:lock.close()

if __name__=='__main__':main()
