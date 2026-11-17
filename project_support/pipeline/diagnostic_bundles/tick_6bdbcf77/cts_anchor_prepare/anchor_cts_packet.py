"""DISABLED root-only static CTS catalog anchor. No default operation or GPU use."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
PACKET=ROOT/'pipeline/diagnostic_bundles/tick_6bdbcf77/cts_operational_prepare'
ORIGINAL=ROOT/'pipeline/diagnostic_bundles/tick_4694ba96/cts_native_prepare'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
CID='hierarchy-parent-cyclic-triadic-state-composition'
COMMIT='4e80006047d5cb3dcdfb9c1102e02c33f354a07d'
RUNTIME='48fc302c3c02ffef0b241be3593c386b6b65a72e'
PREPARATION_SHA='51cbc658fcf5877a0b46776e361adb99d36d4551841aacdf7559ac6d46c937d6'
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
DRAFT_EXECUTION_ENABLED=False
EXPECTED_OWNER={'token':'6bdbcf775b4b4239933ce966f98664d2','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253',
 'generated_at':'2026-10-25T18:06:28.721162+00:00','deadline_at':'2026-10-25T19:06:28.721162+00:00',
 'context_sha256':'723e5dea136798a6fc12574293a524f1df9859e17a0f4f57832076b58ff98d15',
 'pending_sha256':'e4f95c6f88fa7e8b18770f03fda93e8ad143d3d863950df3b53332f1df8e53e3'}
PROTECTED=['queue.json','running.json','experiments/M206-CGCA.json','experiments/M207-HAP.json',
 'experiments/M210-PSNC.json','experiments/M211-BTC.json','experiments/M212-BCR.json','experiments/M213-BFC.json',
 'admissions/M206-CGCA.json','admissions/M210-PSNC.json','admissions/M211-BTC.json','admissions/M212-BCR.json','admissions/M213-BFC.json']
BASELINE=ROOT/'pipeline/diagnostic_bundles/tick_16b87793/protected_worktree_before.json'


def require(value,message):
    if not value:raise RuntimeError(message)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def exclusive(p,value):
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())


def owner_guard():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json');mode=read(ROOT/'pipeline/execution_mode.json')
    require({k:owner.get(k) for k in EXPECTED_OWNER}==EXPECTED_OWNER,'Actual six-field owner changed')
    require(mode['mode']=='foreground' and mode['target_thread_id']==os.environ.get('CODEX_THREAD_ID')==EXPECTED_OWNER['thread_id'],'Actual foreground root required')
    require(datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED_OWNER['deadline_at']),'Original deadline expired')
    require(sha(ROOT/'pipeline/headless/.tick_context.json')==EXPECTED_OWNER['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==EXPECTED_OWNER['pending_sha256'],'Original snapshot changed')
    require(sha(ROOT/'pipeline/goal.json')==GOAL,'Goal changed')
    require(sha(ROOT/'SERVERS.yaml')=='d5277972e80b6fe184a3e07f0fff34f7e1e7950b558d60905416ced302b206a2','Resource configuration changed')
    require(sha(ROOT/'pipeline/authorizations/experiment_first_20261021.json')=='2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8','Experiment-first authorization changed')
    require(sha(ROOT/'pipeline/authorizations/server4_gpu1_20261025.json')=='90f8820a60ef4d4e277904815b025658f7b8b457b0711a4d0ef5f7395fdd23f8','Resource grant changed')


def git(*args):
    result=subprocess.run(['git','--no-optional-locks','-c','core.fsmonitor=false','-C',str(ROOT/'Cluster'),*args],capture_output=True,timeout=30,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0'))
    require(result.returncode==0,'Read-only Git check failed');return result.stdout


def primary_snapshot():
    require(sha(BASELINE)=='deb2f6e1093be710fbbae886b4008c187b2e6b63d63276bfb47706b36b4be142','Protected28 baseline changed')
    expected=read(BASELINE)['protected_existing_worktree'];require(len(expected)==28,'Protected28 inventory changed')
    raw=git('status','--porcelain=v1','-z','--untracked-files=all');rows=[r for r in raw.split(b'\0') if r]
    require(all(b'R' not in r[:2] and b'C' not in r[:2] for r in rows),'Rename/copy requires review')
    require({(r[:2].decode(),r[3:].decode()) for r in rows}=={(r['status'],r['path']) for r in expected},'Primary protected status changed')
    hashes={}
    for row in expected:
        p=(ROOT/'Cluster'/row['path']).resolve();require(p.is_relative_to((ROOT/'Cluster').resolve()),'Protected path escapes primary')
        hashes[row['path']]=sha(p);require(hashes[row['path']]==row['sha256'],'Protected28 bytes changed')
    require(not git('diff','--cached','--name-only','-z'),'Primary index not empty')
    index=Path(git('rev-parse','--git-path','index').decode().strip())
    if not index.is_absolute():index=ROOT/'Cluster'/index
    head=git('rev-parse','HEAD').decode().strip();require(head==RUNTIME,'Public runtime is not tested48fc')
    return {'HEAD':head,'index_sha256':sha(index),'status_hex':raw.hex(),'protected28':hashes}


def packet_guard(review_path,review_sha):
    require(sha(PACKET/'preparation.json')==PREPARATION_SHA,'Frozen outer preparation changed')
    p=read(PACKET/'preparation.json');np=read(PACKET/'native/preparation.json')
    for base,meta in [(PACKET,p),(PACKET/'native',np)]:
        for name,h in meta['prepared_file_hashes'].items():
            f=(base/name).resolve();require(f.is_relative_to(base.resolve()) and sha(f)==h,'Frozen package file changed')
    require(p['code_commit']==np['source_commit']==COMMIT and np['source_parent_commit']==RUNTIME,'CTS source/version identity changed')
    require(p['all_actual_execution']==p['native_TRAIN2']==p['resources']==np['native']==np['resources']=='NOT_RUN','Preparation is no longer unexecuted')
    require(sha(ORIGINAL/'preparation.json')=='ff7fb7a65999369f277744828598822883a222a10ce1ef02732aafeb561fb2cf','Original disabled ff7 changed')
    require((ORIGINAL/'worker.py').read_bytes()==(PACKET/'native/worker.py').read_bytes(),'Original worker03329 changed')
    rp=Path(review_path).resolve();require(rp.is_relative_to((ROOT/'pipeline/diagnostic_bundles/tick_6bdbcf77').resolve()) and re.fullmatch(r'[0-9a-f]{64}',review_sha or '') and sha(rp)==review_sha,'Actual independent review path/SHA required')
    review=read(rp);require(review['status']=='STATIC_OPERATIONAL_CTS_PACKET_REVIEWED_NOT_NATIVE_PASS' and review['material_concerns']==[] and review['candidate_id']==CID and review['code_commit']==COMMIT,'Independent review is not this actual passing static packet')
    for key,path in [('outer_preparation',PACKET/'preparation.json'),('native_preparation',PACKET/'native/preparation.json'),('release_template',PACKET/'release_template.json')]:require(review['anchors'][key]==ref(path),'Independent review anchor mismatch')
    tr=p['current_passing_offline_suite'];tp=(PACKET/tr['path']).resolve();require(tp.is_relative_to(PACKET.resolve()) and sha(tp)==tr['sha256'],'Actual final suite proof changed')
    test=read(tp);require(test['successful'] and test['tests_run']==61 and test['failures']==test['errors']==0 and test['torch_imported'] is False and test['real_process_or_network_audit_events']==[],'Actual offline checks did not pass')
    for n,h in test['source_hashes'].items():require(sha(PACKET/n)==h,'Current sources differ from tested fixture sources')
    return rp,tp


def lifecycle_guard():
    q=read(ROOT/'pipeline/queue.json')['gpu_queues']['server-4'];running=read(ROOT/'pipeline/running.json').get('server-4',{})
    for eid,pid,gpu,commit,receipt in [('M213-BFC',219369,'0',RUNTIME,'812454a819702e8f4d53080c1b479617d605f2175bf44a3422905688253ca01c'),('M212-BCR',1215422,'1','11a811618179ab1ddc0cee299194667413b7fdb9','b8532405ba05101355898016aeeb45e1776217bc95a64a2ae449c1ff02ef60ac')]:
        rows=[x for x in q if x.get('id')==eid];require(len(rows)==1,'Protected active task missing/duplicated')
        task=rows[0];require(task['status']=='running' and task['pid']==pid and str(task['gpu'])==gpu and task['launch_verified'] is True and task['code_commit']==commit,'Protected running identity changed')
        require(task['admission_receipt']=='pipeline/admissions/'+eid+'.json' and sha(ROOT/task['admission_receipt'])==receipt and running.get(gpu)==eid,'Protected receipt/running registry changed')
    m=[x for x in q if x.get('id')=='M206-CGCA'];require(len(m)==1 and m[0].get('dispatch_hold') and m[0].get('resume_authorized') is False and m[0].get('pid') is None,'M206 pause changed')
    require(not any(x.get('id')=='M214-CTS' for x in q) and not (ROOT/'pipeline/admissions/M214-CTS.json').exists() and not (ROOT/'pipeline/experiments/M214-CTS.json').exists(),'CTS already admitted/queued')
    require(not (ROOT/'pipeline/diagnostic_bundles/tick_6bdbcf77/cts_execution').exists(),'CTS has active/partial execution requiring reconciliation')


def execute(review_path,review_sha):
    owner_guard();rp,tp=packet_guard(review_path,review_sha)
    release=PACKET/'adapter_release.json'
    require(not release.exists() and not (HERE/'cts_static_anchor_intent.json').exists() and not (HERE/'cts_static_anchor_result.json').exists(),'Existing/partial anchor requires exact read-only reconciliation')
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));require(lock is not None,'Canonical project lock busy')
    try:
        owner_guard();lifecycle_guard();before=primary_snapshot();protected={n:sha(ROOT/'pipeline'/n) for n in PROTECTED}
        work=read(ROOT/'pipeline/research_work.json');oldwork=copy.deepcopy(work)
        matches=[c for c in work['candidates'] if c.get('id')==CID];require(len(matches)==1,'CTS missing/ambiguous');c=matches[0]
        require(c['stage']=='validation' or (c['stage']=='blocked' and c.get('resume_stage')=='validation' and c.get('blocker_kind') in ('resource','exclusive_gpu_slot')),'CTS not in validation/resource hold')
        require(c['code_commit']==COMMIT and c['source_parent_commit']==RUNTIME and c['native_execution_code_commit'] is None,'CTS current source/native identity changed')
        require(c['worker_preparation']['preparation']==ref(ORIGINAL/'preparation.json'),'Original ff7 preparation history changed')
        c.setdefault('execution_preparation_history',[]).append({'recorded_at':datetime.now(timezone.utc).isoformat(),'reason':'Preserve original disabled/null ff7 worker and previous adapter state before reviewed static catalog anchor; no native execution inferred.','worker_preparation':copy.deepcopy(c['worker_preparation']),'execution_adapter':copy.deepcopy(c['execution_adapter'])})
        exclusive(HERE/'cts_static_anchor_intent.json',{'token':EXPECTED_OWNER['token'],'candidate_id':CID,'packet':ref(PACKET/'preparation.json'),'independent_review':ref(rp),'protected_files':protected,'primary':before,'scope':'Only identical static catalog and CTS preparation metadata; no native/queue/launch/resource action'})
        owner_guard();lifecycle_guard();require(primary_snapshot()==before and {n:sha(ROOT/'pipeline'/n) for n in PROTECTED}==protected and read(ROOT/'pipeline/research_work.json')==oldwork,'Protected state changed before materialization');packet_guard(review_path,review_sha)
        with release.open('xb') as f:f.write((PACKET/'release_template.json').read_bytes());f.flush();os.fsync(f.fileno())
        require(sha(release)==sha(PACKET/'release_template.json'),'Static catalog byte copy differs')
        n=PACKET/'native'
        c['worker_preparation']={'status':'PREPARED_REVIEWED_UNEXECUTED','preparation':ref(n/'preparation.json'),'worker':ref(n/'worker.py'),'runtime':ref(n/'native_runtime.py'),'manifest_template':ref(n/'manifest_template.json'),'source_commit':COMMIT,'source_parent_commit':RUNTIME,'runtime_expected_commit':RUNTIME,'native_backward_executed':False,'resource_profile_executed':False,'native_backward_passed':False,'resources_passed':False,'active_native_manifest_or_execution_lease_created':False,'independent_review':ref(rp)}
        c['execution_adapter']={'status':'PREPARED_REVIEWED_STATIC_CATALOG_ONLY_UNEXECUTED','preparation':ref(PACKET/'preparation.json'),'release':ref(release),'adapter':ref(PACKET/'adapter.py'),'remote_ops':ref(PACKET/'remote_ops.py'),'README':ref(PACKET/'README.md'),'independent_review':ref(rp),'independent_tests':ref(tp),'external_anchor_required':True,'source_commit':COMMIT,'runtime_expected_commit':RUNTIME,'native_execution_code_commit':None,'native_execution_tested':False,'remote_adapter_execution_tested':False,'active_binding_manifest_lease_created':False,'static_module_release_only':True,'standard_result_formatter_implemented':False}
        c['operational_preparation_status']='COMPLETE_REVIEWED_STATIC_GUARDED_CTS_PACKET_NATIVE_NOT_RUN'
        c['native_status']='NOT_RUN_REQUIRES_FRESH_AUTHORIZED_IDLE_GPU_AND_BINDING';c['native_smoke_status']='NOT_RUN';c['resource_status']='NOT_RUN';c['resource_profile_status']='NOT_RUN';c['admission_status']='NOT_EVALUATED';c['efficacy']='UNKNOWN'
        c['next_action']='Preserve isolated CTS4e8 and actual runtime48fc. Use reviewed static packet only under a fresh exact owner/context/original deadline after a selected authorized physical0or1 is genuinely idle with matching UUID/assets/three locks. Registered BFC0/BCR1 remain protected and M206 stays paused. Run only original M95/CTS TRAIN2 and resources, validate actual three-source/multiround coverage and three W-block original-loss gradients/updates; missing coverage INCONCLUSIVE, individual call zeros legal. No native/admission/queue claim from this static anchor.'
        for path in [PACKET/'preparation.json',n/'preparation.json',release,rp,tp,PACKET/'native_promotion.json']:
            entry=ref(path)
            if entry not in c.setdefault('evidence',[]):c['evidence'].append(entry)
        work['updated_at']=datetime.now(timezone.utc).isoformat();work['next_action']=c['next_action']
        owner_guard();lifecycle_guard();require(primary_snapshot()==before and {n:sha(ROOT/'pipeline'/n) for n in PROTECTED}==protected and read(ROOT/'pipeline/research_work.json')==oldwork,'Protected state changed before ledger write')
        target=ROOT/'pipeline/research_work.json';temporary=target.with_name(target.name+'.'+EXPECTED_OWNER['token']+'.tmp')
        exclusive(temporary,work);os.replace(temporary,target)
        require(primary_snapshot()==before and {n:sha(ROOT/'pipeline'/n) for n in PROTECTED}==protected,'Protected source/lifecycle changed after anchor')
        current=read(target);require([x for x in current['candidates'] if x.get('id')!=CID]==[x for x in oldwork['candidates'] if x.get('id')!=CID],'Other candidates changed')
        exclusive(HERE/'cts_static_anchor_result.json',{'status':'REVIEWED_CTS_STATIC_CATALOG_ANCHORED_NATIVE_NOT_RUN','recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,'source_commit':COMMIT,'runtime_commit':RUNTIME,'outer':ref(PACKET/'preparation.json'),'native':ref(n/'preparation.json'),'release':ref(release),'independent_review':ref(rp),'protected_lifecycle_unchanged':True,'primary_HEAD_index_status28bytes_unchanged':True,'active_binding_manifest_lease_created':False,'native_resources_transport_queue_launch':'NOT_RUN'})
        print(json.dumps({'status':'REVIEWED_CTS_STATIC_CATALOG_ANCHORED_NATIVE_NOT_RUN','active_binding':False}))
    finally:lock.close()


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--execute-root',action='store_true');parser.add_argument('--review');parser.add_argument('--review-sha');args=parser.parse_args(argv)
    if not args.execute_root:print('DRAFT_CTS_STATIC_ANCHOR_DISABLED_NO_ACTION');return 0
    require(DRAFT_EXECUTION_ENABLED,'Draft disabled; root must independently review and materialize a separate one-flag execution copy')
    require(args.review is not None and args.review_sha is not None,'Actual independent review path/SHA required')
    execute(args.review,args.review_sha);return 0


if __name__=='__main__':raise SystemExit(main())
