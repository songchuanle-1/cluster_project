"""Root static catalog anchor only; never creates a GPU execution binding."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,sys
from anchor_bfc_packet import guard
from verify_protected_assets_v3 import snapshot
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
PACKET=HERE/'bec_operational_prepare';OLD=ROOT/'pipeline/diagnostic_bundles/tick_f86d1cfa/bec_native_prepare'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
CID='hierarchy-cross-level-bipartite-edge-composition';COMMIT='9b6782f44ca7f2c8ac35baea01dfd070314b5701';PARENT='48fc302c3c02ffef0b241be3593c386b6b65a72e'
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def exclusive(p,value):
    with p.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def main():
    owner=guard();prep=read(PACKET/'preparation.json');native=read(PACKET/'native/preparation.json')
    review_path=HERE/'bec_operational_final_review.json';review=read(review_path)
    assert review['status']=='STATIC_OPERATIONAL_BEC_PACKET_REVIEWED_NOT_NATIVE_PASS' and review['material_concerns']==[]
    for key,p in [('outer_preparation',PACKET/'preparation.json'),('native_preparation',PACKET/'native/preparation.json'),('release_template',PACKET/'release_template.json')]:
        assert review['anchors'][key]==ref(p)
    for base,meta in [(PACKET,prep),(PACKET/'native',native)]:
        for name,h in meta['prepared_file_hashes'].items():
            p=(base/name).resolve();assert p.is_relative_to(base.resolve()) and sha(p)==h
    assert prep['candidate_id']==native['candidate_id']==CID and prep['code_commit']==native['source_commit']==COMMIT
    assert prep['source_parent_commit']==native['source_parent_commit']==PARENT
    assert prep['runtime_expected_commit']==PARENT
    assert prep['all_actual_execution']==prep['native_TRAIN2']==prep['resources']==native['native']==native['resources']=='NOT_RUN'
    assert prep['active_binding_manifest_lease']=='NOT_CREATED'
    assert (PACKET/'native/worker.py').read_bytes()==(OLD/'worker.py').read_bytes()
    assert sha(OLD/'preparation.json')=='322c8ce812ffccda6cfa3d6d2d6e1dd8f73859ab5d3a9835d0c1110328c3e3ff'
    oldprep=read(OLD/'preparation.json')
    assert oldprep['draft_execution_disabled'] is True and oldprep['source_commit'] is None and oldprep['source_parent_commit'] is None
    assert all(sha(OLD/name)==h for name,h in oldprep['prepared_file_hashes'].items())
    template=read(PACKET/'native/manifest_template.json')
    active=['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']
    assert all(template.get(k) is None for k in active)
    suite_ref=prep['current_passing_offline_suite'];suite_path=(PACKET/suite_ref['path']).resolve()
    assert suite_path.is_relative_to(PACKET.resolve()) and sha(suite_path)==suite_ref['sha256']
    suite=read(suite_path)
    assert suite['successful'] is True and suite['failures']==suite['errors']==0 and suite['torch_imported'] is False and suite['real_process_or_network_audit_events']==[]
    release=PACKET/'adapter_release.json'
    assert not release.exists() and not (HERE/'bec_static_anchor_intent.json').exists() and not (HERE/'bec_static_anchor_result.json').exists()
    assert not (HERE/'bec_execution').exists()
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();protected=read(HERE/'protected_assets_before.json')['protected_ledgers']
        assert all(sha(ROOT/'pipeline'/n)==h for n,h in protected.items())
        source_before=snapshot()
        original=read(HERE/'protected_assets_before.json')
        source_keys=['head','index_empty','status_hex','files','protected_ledgers','historical_baseline_sha256']
        assert all(source_before[k]==original[k] for k in source_keys)
        work=read(ROOT/'pipeline/research_work.json');oldwork=copy.deepcopy(work)
        c=next(c for c in work['candidates'] if c['id']==CID)
        assert c['stage']=='validation' and c['code_commit']==COMMIT and c['source_parent_commit']==PARENT and c['native_execution_code_commit'] is None
        assert c['worker_preparation']['preparation']==ref(OLD/'preparation.json')
        tasks=read(ROOT/'pipeline/queue.json')['gpu_queues']['server-4'];running=read(ROOT/'pipeline/running.json')['server-4']
        for eid,pid,gpu in [('M213-BFC',219369,'0'),('M212-BCR',1215422,'1')]:
            t=next(t for t in tasks if t['id']==eid)
            assert t['status']=='running' and t['pid']==pid and str(t['gpu'])==gpu and t['launch_verified'] is True and running[gpu]==eid
        pause=next(t for t in tasks if t['id']=='M206-CGCA');assert pause['dispatch_hold'] and pause['resume_authorized'] is False
        assert not any(t['id']=='M215-BEC' for t in tasks) and not (ROOT/'pipeline/admissions/M215-BEC.json').exists() and not (ROOT/'pipeline/experiments/M215-BEC.json').exists()
        exclusive(HERE/'bec_static_anchor_intent.json',{'token':owner['token'],'candidate_id':CID,'outer':ref(PACKET/'preparation.json'),'review':ref(review_path),'scope':'Only static module catalog bytecopy and existing BEC preparation metadata. No execution manifest, lease, native/resource run, queue/source/runtime/process operation.'})
        c.setdefault('execution_preparation_history',[]).append({'recorded_at':datetime.now(timezone.utc).isoformat(),
            'reason':'Preserve original322c disabled/null-native and old adapter declaration before separately reviewed version-bound static catalog.',
            'worker_preparation':copy.deepcopy(c['worker_preparation']),'execution_adapter':copy.deepcopy(c.get('execution_adapter',{'status':'NOT_PREPARED'}))})
        guard();assert read(ROOT/'pipeline/research_work.json')==oldwork
        assert all(sha(ROOT/'pipeline'/n)==h for n,h in protected.items())
        checked_snapshot=snapshot();assert all(checked_snapshot[k]==source_before[k] for k in source_keys)
        with release.open('xb') as f:f.write((PACKET/'release_template.json').read_bytes());f.flush();os.fsync(f.fileno())
        assert sha(release)==sha(PACKET/'release_template.json')
        n=PACKET/'native'
        c['worker_preparation']={'status':'PREPARED_REVIEWED_VERSION_BOUND_UNEXECUTED','preparation':ref(n/'preparation.json'),'worker':ref(n/'worker.py'),
            'runtime':ref(n/'native_runtime.py'),'manifest_template':ref(n/'manifest_template.json'),'source_commit':COMMIT,'source_parent_commit':PARENT,
            'runtime_expected_commit':PARENT,'native_backward_executed':False,'resource_profile_executed':False,'native_backward_passed':False,'resources_passed':False,
            'active_native_manifest_or_execution_lease_created':False,'independent_review':ref(review_path)}
        c['execution_adapter']={'status':'PREPARED_REVIEWED_STATIC_CATALOG_ONLY_UNEXECUTED','preparation':ref(PACKET/'preparation.json'),'release':ref(release),
            'adapter':ref(PACKET/'adapter.py'),'remote_ops':ref(PACKET/'remote_ops.py'),'README':ref(PACKET/'README.md'),'independent_review':ref(review_path),
            'independent_tests':ref(suite_path),'external_anchor_required':True,'source_commit':COMMIT,'runtime_expected_commit':PARENT,
            'native_execution_code_commit':None,'native_execution_tested':False,'remote_adapter_execution_tested':False,
            'active_binding_manifest_lease_created':False,'static_module_release_only':True,'standard_result_formatter_implemented':False}
        c['operational_preparation_status']='COMPLETE_REVIEWED_STATIC_GUARDED_VERSION_BOUND_BEC_PACKET_NATIVE_NOT_RUN'
        c['native_status']='NOT_RUN_REQUIRES_ACTUAL_CURRENT_IDLE_GPU_ASSETS_LOCKS_AND_FRESH_BINDING'
        for p in [PACKET/'preparation.json',n/'preparation.json',release,review_path,suite_path]:
            item=ref(p)
            if item not in c['evidence']:c['evidence'].append(item)
        work['updated_at']=datetime.now(timezone.utc).isoformat()
        assert [x for x in work['candidates'] if x['id']!=CID]==[x for x in oldwork['candidates'] if x['id']!=CID]
        guard();assert read(ROOT/'pipeline/research_work.json')==oldwork
        checked_snapshot=snapshot();assert all(checked_snapshot[k]==source_before[k] for k in source_keys)
        temporary=ROOT/'pipeline/research_work.json.521a6f59.tmp'
        exclusive(temporary,work);os.replace(temporary,ROOT/'pipeline/research_work.json')
        assert all(sha(ROOT/'pipeline'/name)==h for name,h in protected.items())
        source_after=snapshot();assert all(source_after[k]==source_before[k] for k in source_keys)
        exclusive(HERE/'bec_static_anchor_result.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'token':owner['token'],'candidate_id':CID,'code_commit':COMMIT,
            'status':'REVIEWED_VERSION_BOUND_BEC_STATIC_CATALOG_ANCHORED_NATIVE_NOT_RUN','outer':ref(PACKET/'preparation.json'),'native':ref(n/'preparation.json'),
            'release':ref(release),'independent_review':ref(review_path),'protected_lifecycle_unchanged':True,'primary_HEAD_index_status28bytes_unchanged':True,
            'active_binding_manifest_lease_created':False,'native_resources_transport_queue_launch':'NOT_RUN'})
        print(json.dumps({'status':'BEC_STATIC_CATALOG_ANCHORED','native':'NOT_RUN','active_binding':False}))
    finally:lock.close()
if __name__=='__main__':main()
