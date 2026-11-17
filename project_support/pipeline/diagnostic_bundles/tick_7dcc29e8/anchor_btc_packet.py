"""Anchor only the independently reviewed, unexecuted BTC tool catalog."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import argparse,hashlib,json,os,sys
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
PACKET=HERE/'btc_operational_prepare'; TOKEN='7dcc29e8844245ec87b6d58eee6ec966'
CID='hierarchy-parent-binary-tree-complement-composition'; COMMIT='00e2b18c6b8d568a64edb496e6979d766440883c'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x,exclusive=False):
    if exclusive:
        with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
    else:
        t=p.with_name(p.name+'.'+TOKEN+'.tmp')
        with t.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(t,p)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--review',required=True);parser.add_argument('--review-sha',required=True);args=parser.parse_args()
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    path=Path(args.review).resolve();assert path.is_relative_to(HERE) and sha(path)==args.review_sha
    review=read(path)
    assert review['status']=='STATIC_OPERATIONAL_BTC_PACKET_REVIEWED_NOT_NATIVE_PASS' and review['material_concerns']==[]
    assert review['candidate_id']==CID and review['code_commit']==COMMIT
    for name,p in [('outer_preparation',PACKET/'preparation.json'),('native_preparation',PACKET/'native/preparation.json'),('release_template',PACKET/'release_template.json')]:
        assert review['anchors'][name]==ref(p)
    prep=read(PACKET/'preparation.json');native=read(PACKET/'native/preparation.json');template=read(PACKET/'release_template.json')
    for base,metadata in [(PACKET,prep),(PACKET/'native',native)]:
        for name,h in metadata['prepared_file_hashes'].items():
            p=(base/name).resolve();assert p.is_relative_to(base) and sha(p)==h
    assert prep['code_commit']==native['code_commit']==template['code_commit']==COMMIT
    assert prep['native_execution']==native['native']=='NOT_RUN' and prep['resources']==native['resources']=='NOT_RUN'
    assert not prep['active_native_manifest_lease_binding_created']
    assert not any((PACKET/'native'/name).exists() for name in ['native_manifest.json','execution_lease.json'])
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        work=read(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==CID)
        assert c['stage']=='blocked' and c['blocker_kind']=='exclusive_gpu_slot' and c['resume_stage']=='validation'
        assert c['code_commit']==COMMIT and c['native_execution_code_commit'] is None
        queue=monitor.load_queue(str(ROOT));m210=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M210-PSNC')
        m206=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M206-CGCA')
        assert m210['status']=='running' and m210['pid']==2502712 and m210['launch_verified']
        assert m206['dispatch_hold'] and m206['resume_authorized'] is False
        assert not any(t['id']=='M211-BTC' for ts in queue['gpu_queues'].values() for t in ts)
        assert monitor.load_experiment(str(ROOT),'M211-BTC') is None
        observation=read(HERE/'psnc_progress_observation.json')
        assert observation['same_exact_registered_process_and_native_TRAIN_growth']
        evidence_paths=[PACKET/'preparation.json',PACKET/'native/preparation.json',path,HERE/'btc_source_packet_binding.json',HERE/'btc_native_packet_freeze.json',HERE/'btc_operational_packet_freeze.json',HERE/'psnc_progress_observation.json']
        evidence_refs=[ref(p) for p in evidence_paths]
        release=PACKET/'adapter_release.json'
        with release.open('xb') as f:f.write((PACKET/'release_template.json').read_bytes())
        assert sha(release)==sha(PACKET/'release_template.json')
        native_dir=PACKET/'native'
        c['worker_preparation']={'status':'PREPARED_REVIEWED_UNEXECUTED','preparation':ref(native_dir/'preparation.json'),
            'worker':ref(native_dir/'worker.py'),'runtime':ref(native_dir/'native_runtime.py'),'manifest_template':ref(native_dir/'manifest_template.json'),
            'source_commit':COMMIT,'native_backward_passed':False,'resources_passed':False,'native_backward_executed':False,
            'resource_profile_executed':False,'active_native_manifest_or_execution_lease_created':False}
        c['execution_adapter']={'status':'PREPARED_REVIEWED_STATIC_CATALOG_ONLY_UNEXECUTED','preparation':ref(PACKET/'preparation.json'),
            'release':ref(release),'adapter':ref(PACKET/'adapter.py'),'remote_ops':ref(PACKET/'remote_ops.py'),'README':ref(PACKET/'README.md'),
            'independent_review':ref(path),'independent_tests':prep['offline_tests'],'external_anchor_required':True,
            'source_commit':COMMIT,'native_execution_code_commit':None,'native_execution_tested':False,'remote_adapter_execution_tested':False,
            'active_binding_manifest_lease_created':False,'static_module_release_only':True,'standard_result_formatter_implemented':False,
            'static_release_scope':'Exact independently reviewed BTC module/version hashes only; no active binding, idle proof, resource grant, native PASS or admission.',
            'provenance':'Root materialized identical reviewed static release and external anchors. Native/runtime/remote/GPU execution NOT_RUN. Future fresh owner/context/deadline/assets/idleGPU0/three locks remain mandatory; PSNC current run and M206 pause protected.'}
        c['native_status']='NOT_RUN_waiting_future_idle_authorized_GPU0_and_fresh_execution_binding'
        c['resource_status']='NOT_RUN_waiting_future_idle_authorized_GPU0_and_fresh_execution_binding'
        c['native_worker_adapter']='PREPARED_REVIEWED_STATIC_ONLY_NOT_EXECUTED'
        c['native_smoke_status']='NOT_RUN';c['resource_profile_status']='NOT_RUN';c['admission_status']='NOT_EVALUATED';c['efficacy']='UNKNOWN'
        c['last_resource_check_at']=observation['recorded_at']
        c['retry_after']=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
        c['blocker']='Only authorizedGPU0 runs exact PSNC2502712/start41082267, observed original Train4/50 1352->1361/4686 at '+observation['recorded_at']+'. BTC complete static tools are prepared, but no GPU/native work, active binding or admission occurred. GPU1 remains released and M206 paused.'
        c['unblock_condition']='PSNC exact active run naturally ends; fresh actual authorizedGPU0 UUID/idle/occupation/exclusive checks and original current owner/context/deadline/assets pass. Never disturb existing/foreign work or use GPU1.'
        c['next_action']='Reuse the frozen reviewed BTC00e operational packet/static catalog. Once protected PSNC naturally finishes and actualGPU0 is free, prepare a fresh owned binding, stage and run M95/BTC original native TRAIN2 plus original resource pair. Verify true supported n>=3 inside/outside/leaf gradients and updates, matched initialization/data and constraints before any summary/receipt/queue. Source00e and original protocol unchanged; no GPU1/M206 resume.'
        for item in evidence_refs+[ref(release)]:
            if item not in c['evidence']:c['evidence'].append(item)
        work['updated_at']=datetime.now(timezone.utc).isoformat();work['next_action']='Monitor original PSNC2502712/GPU0; BTC00e complete static operational preparation waits fresh idleGPU0 for actual native/resource checks. GPU1 released, M206 paused; no goal/protocol/resource/scheduler changes.'
        save(ROOT/'pipeline/research_work.json',work)
        save(HERE/'btc_static_anchor_result.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,
            'outer_preparation':ref(PACKET/'preparation.json'),'native_preparation':ref(native_dir/'preparation.json'),'static_release':ref(release),
            'independent_review':ref(path),'source_commit':COMMIT,'source_or_Git_changed':False,'queue_or_existing_run_changed':False,
            'active_binding_manifest_lease_created':False,'native_or_resources_or_remote_execution':False,'admission_created':False},exclusive=True)
        print(json.dumps({'candidate_id':CID,'static_catalog_anchored':True,'native_or_resources_executed':False,'active_binding_created':False,'training_launched':False}))
    finally:lock.close()
if __name__=='__main__':main()
