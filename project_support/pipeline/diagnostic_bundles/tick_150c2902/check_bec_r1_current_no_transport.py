"""Default-disabled root-only current R1 resource guard; no transport allowed.

This never anchors a catalog, stages code, queries a GPU or changes shared state.
Root must explicitly pass --execute-root in its actual owner environment.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,builtins,hashlib,importlib.util,json,os,sys

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
OP=ROOT/'pipeline/diagnostic_bundles/tick_faccbed6/bec_r1_operational_prepare'
CID='hierarchy-cross-level-bipartite-edge-composition'
CODE='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'
PARENT='4e80006047d5cb3dcdfb9c1102e02c33f354a07d'
TOKEN='150c29025cb0435c8ec6ddc7a971e921'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf8'))
def ref(path):return {'path':Path(path).relative_to(ROOT).as_posix(),'sha256':sha(path)}
def exclusive(path,value):
    with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute-root',action='store_true');args=parser.parse_args()
    if not args.execute_root:
        print(json.dumps({'status':'PREPARED_DISABLED_REQUIRES_EXPLICIT_ROOT_FLAG','native':'NOT_RUN','resources':'NOT_RUN','transport_calls':0,'shared_state_modified':False}));return 2
    success=HERE/'bec_r1_actual_current_no_transport.json';failure=HERE/'bec_r1_actual_current_no_transport_failure.json'
    assert not success.exists() and not failure.exists(),'Existing result requires read-only reconciliation, never replay'
    events=[];calls=[];outcomes={};metadata_passed=False;owner=None;before={};execution=HERE/'bec_r1_execution'
    def audit(event,values):
        if event=='subprocess.Popen' or event.startswith('socket.'):
            events.append(event);raise RuntimeError('Real process/network prohibited by NoTransport guard')
    sys.addaudithook(audit)
    original_import=builtins.__import__
    def import_guard(name,*args,**kwargs):
        if name.startswith(('torch','framework','gorilla')):raise RuntimeError('Model/Torch import prohibited')
        return original_import(name,*args,**kwargs)
    builtins.__import__=import_guard
    try:
        # Rebound root guard is deliberately not bypassed for a child agent.
        from anchor_bfc_packet import guard
        provenance=read(HERE/'readonly_helpers_provenance.json')
        assert all(sha(HERE/item['file'])==item['new_sha256'] for item in provenance)
        owner=guard();assert owner['token']==TOKEN and owner['thread_id']==os.environ.get('CODEX_THREAD_ID')=='01a159c5-29ab-7a22-ba7f-e79174757253'
        assert owner['generated_at']=='2026-10-26T12:12:56.290224+00:00' and owner['deadline_at']=='2026-10-26T13:12:56.290224+00:00'
        assert owner['context_sha256']=='01f3df6d6a18559bac7117bcbbd0a44afe84ade67baa9b7fe88c5ffd562a9b46' and owner['pending_sha256']=='f64805308a5636fb444345b65935a9ca2138857c2d516f65ee7a4ec2d10348d4'
        assert not execution.exists(),'No execution directory may already exist or be modified'
        assert sha(OP/'preparation.json')=='9a81c28ac80f2f9f00184f67f7bd47841124cb8a18e0a22c554eaceb10957d35'
        assert sha(OP/'native/preparation.json')=='edd2049e2f990e94ffed784800797f033a27ef3a7f69dd928630715bf8bee078'
        assert sha(OP/'adapter_release.json')==sha(OP/'release_template.json')=='ee75b2934373d22362400e4fe66fd92ba17ef66405c7e7bcdd9aaae74fc2c059'
        observer=read(HERE/'cts_native_progress_observation.json');assert observer['owner_token']==TOKEN and observer['native_TRAIN_growth'] is True
        last=observer['observations'][-1];assert last['pid']==3505065 and last['start_ticks']=='61122472' and last['runtime_HEAD']==PARENT
        assert len(last['actual_model8_hashes'])==8 and all(sha(ROOT/'Cluster'/name)==value for name,value in last['actual_model8_hashes'].items())
        assert last['deployed_config_sha256']=='77eac419317cb7d7f5d4688337597a966b27d2f920484c1e2323d279240289ea'
        queue=read(ROOT/'pipeline/queue.json');cts=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M214-CTS')
        assert cts['pid']==3505065 and cts['status']=='running' and cts['launch_verified'] is True and cts['code_commit']==PARENT and str(cts['gpu'])=='0'
        running=read(ROOT/'pipeline/running.json');assert running['server-4']['0']=='M214-CTS'
        names=['SERVERS.yaml','pipeline/goal.json','pipeline/closure_policy.json','pipeline/research_work.json','pipeline/queue.json','pipeline/running.json','pipeline/experiments/M214-CTS.json','pipeline/admissions/M214-CTS.json']
        before={name:sha(ROOT/name) for name in names}
        spec=importlib.util.spec_from_file_location('current_R1_production_adapter',OP/'adapter.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        class NoTransport:
            def call(self,*args,**kwargs):calls.append({'operation':args[0] if args else None});raise RuntimeError('NoTransport forbids every actual remote operation')
        adapter=module.Adapter(root=ROOT,origin=OP,frozen=OP/'native',transport=NoTransport())
        # This reaches immutable pending-R1/hypothesis/catalog checks before the
        # separate registered-occupancy attempt. It creates no execution material.
        current=adapter.guard(360,0,mutation=True)
        assert current['owner']['token']==TOKEN and current['server']['allowed_gpus']==[0]
        metadata_passed=True
        for gpu in (0,1):
            try:adapter.prepare(gpu)
            except module.Refused as error:outcomes[str(gpu)]={'refused':True,'reason':str(error)}
            else:raise RuntimeError('Expected prepare refusal did not occur')
        assert outcomes['0']['reason']=='Selected GPU has registered running task'
        assert outcomes['1']['reason']=='Explicit physical GPU0 is required for R1'
        assert calls==[] and events==[] and 'torch' not in sys.modules and not execution.exists()
        assert before=={name:sha(ROOT/name) for name in names},'Shared state changed during readonly resource check'
        guard()
        result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'ACTUAL_CURRENT_R1_METADATA_PASS_REGISTERED_BUSY_AND_GPU1_UNAUTHORIZED_ZERO_TRANSPORT',
          'owner':{k:owner[k] for k in ['token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256']},'candidate_id':CID,'code_commit':CODE,'runtime_expected_commit':PARENT,
          'actual_metadata_source_catalog_pending_R1_guard_passed':True,'outcomes':outcomes,'transport_calls':0,'process_network_audit_events':events,'Torch_imported':False,
          'active_execution_directory_created':False,'active_manifest_or_lease_created':False,'static_anchor_created':False,'shared_state_unchanged':True,
          'native':'NOT_RUN_ON_R1','resources':'NOT_RUN_ON_R1','resource_check_result':'blocked','anchors':{'production_preparation':ref(OP/'preparation.json'),'existing_static_release':ref(OP/'adapter_release.json'),'current_root_CTS_observation':ref(HERE/'cts_native_progress_observation.json')},
          'scope':'Actual current local metadata/registered occupancy and explicit GPU0-only rejection. No hardware query/physical-idle measurement, model execution, original resource profiling or gate PASS.', 'material_concerns':[]}
        exclusive(success,result)
        print(json.dumps({'path':str(success),'sha256':sha(success),'resource_check_result':'blocked','transport_calls':0,'native':'NOT_RUN_ON_R1'}));return 0
    except Exception as error:
        result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'CURRENT_NO_TRANSPORT_GUARD_FAILED_NOT_NORMAL_TRAINING_RESULT','candidate_id':CID,'code_commit':CODE,
          'error_type':type(error).__name__,'error':str(error),'actual_metadata_guard_passed':metadata_passed,'outcomes_before_failure':outcomes,'transport_calls':len(calls),'process_network_audit_events':events,
          'Torch_imported':'torch' in sys.modules,'active_execution_directory_exists':execution.exists(),'scope':'Preserve this actual error. It does not establish CTS failure or BEC native/resource PASS. No retry/cleanup/source change is authorized.'}
        exclusive(failure,result);print(json.dumps({'path':str(failure),'sha256':sha(failure),'status':result['status'],'error':str(error)}));return 1
    finally:builtins.__import__=original_import

if __name__=='__main__':raise SystemExit(main())
