"""Create a static release template or freeze reviewed unexecuted tool metadata."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,ast,hashlib,json,os
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
PACKET=HERE/'btc_operational_prepare'; NATIVE=PACKET/'native'
CID='hierarchy-parent-binary-tree-complement-composition'; COMMIT='00e2b18c6b8d568a64edb496e6979d766440883c'
TOKEN='7dcc29e8844245ec87b6d58eee6ec966'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['template','freeze']);parser.add_argument('--offline-proof');args=parser.parse_args()
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    assert not (PACKET/'preparation.json').exists() and not (PACKET/'adapter_release.json').exists()
    module=ast.parse((PACKET/'adapter.py').read_text(encoding='utf-8')); constants={}
    for n in module.body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and isinstance(n.value,ast.Constant):constants[n.targets[0].id]=n.value.value
    assert constants['COMMIT']==COMMIT and constants['CANDIDATE']==CID
    assert constants['PREPARATION_SHA']==sha(NATIVE/'preparation.json') and constants['TEMPLATE_SHA']==sha(NATIVE/'manifest_template.json')
    template={'schema_version':1,'purpose':'Static reviewed module/version hash catalog; no token/lease/GPU grant',
        'candidate_id':CID,'experiment_id':'M211-BTC','code_commit':COMMIT,
        'native_preparation_sha256':sha(NATIVE/'preparation.json'),'manifest_template_sha256':sha(NATIVE/'manifest_template.json'),
        'source_version_binding_sha256':sha(NATIVE/'source_version_binding.json'),
        'source_hashes':{n:sha(PACKET/n) for n in ['adapter.py','remote_ops.py']},
        'external_candidate_preparation_and_release_anchors_required':True,'fresh_owned_binding_and_live_idle_still_required':True}
    if args.operation=='template':
        save(PACKET/'release_template.json',template)
        print(json.dumps({'release_template_sha256':sha(PACKET/'release_template.json'),'active_release_created':False,'execution':'NOT_RUN'}));return
    assert read(PACKET/'release_template.json')==template
    proof=Path(args.offline_proof).resolve();assert proof.is_relative_to(PACKET) and proof.is_file()
    for forbidden in ['native_manifest.json','execution_lease.json','execution_binding.json']:
        assert not list(PACKET.rglob(forbidden))
    files=[p for p in sorted(PACKET.rglob('*')) if p.is_file()]
    assert all('__pycache__' not in p.parts and not p.name.endswith('.pyc') for p in files)
    hashes={p.relative_to(PACKET).as_posix():sha(p) for p in files}
    assert {'adapter.py','remote_ops.py','release_template.json','native/preparation.json','native/manifest_template.json'}<=set(hashes)
    preparation={'schema_version':1,'candidate_id':CID,'experiment_id':'M211-BTC','code_commit':COMMIT,'source_commit':COMMIT,
        'base_reference_commit':'74fcd21df0af9a971792038ffe251af1ffea2604','source_parent_commit':'43dce016c1a1713c2a5dab7061810dc2efde8954',
        'status':'OPERATIONAL_CODE_PREPARED_UNEXECUTED_AWAITING_REVIEWED_STATIC_RELEASE_AND_FRESH_IDLE_OWNED_BINDING',
        'prepared_under_parent_token':TOKEN,'parent_thread_id':owner['thread_id'],'tick_generated_at_provenance':owner['generated_at'],
        'original_deadline_at_provenance':owner['deadline_at'],'context_sha256_provenance':owner['context_sha256'],'pending_sha256_provenance':owner['pending_sha256'],
        'prepared_at':datetime.now(timezone.utc).isoformat(),'preparation_reusable_across_ticks':True,'static_provenance_is_not_execution_lease':True,
        'native_preparation':ref(NATIVE/'preparation.json'),'source_version_binding':ref(NATIVE/'source_version_binding.json'),
        'original_source_preparation':ref(ROOT/'pipeline/diagnostic_bundles/tick_2c25f38f/new_candidate_prepare/preparation.json'),
        'prepared_file_hashes':hashes,'offline_tests':ref(proof),'transport_adapter_implemented':True,
        'interfaces':['guard','probe','prepare','stage','run','pair','run_pair','status','reconcile'],
        'physical_gpu_scope':[0],'ssh_target':'songcl@192.168.1.115','expected_hostname':'dl04-MS-7E06',
        'static_release_template':ref(PACKET/'release_template.json'),'native_execution':'NOT_RUN','resources':'NOT_RUN','transport_execution':'NOT_RUN',
        'active_native_manifest_lease_binding_created':False,'adapter_release_created':False,
        'Cluster_HEAD_index_or_protected28_modified':False,'shared_ledger_or_queue_modified':False,
        'standard_PASS_receipt_or_admission_created':False,'efficacy':'UNKNOWN',
        'remaining_execution_prerequisites':['Independent final review and root static catalog/external anchors',
            'Fresh exact owning thread/context/pending/deadline and current authorization/assets',
            'Real idle physicalGPU0/UUID/two observations/three locks after protected PSNC naturally finishes',
            'Actual paired M95/BTC native TRAIN2/common init/n>=3 paths/gradients and original resource checks before receipt/queue'],
        'limits':'Offline tests and source metadata only; no torch/native/GPU/remote execution, new candidate source change, new Git version, training efficacy or admission claim.'}
    save(PACKET/'preparation.json',preparation)
    save(HERE/'btc_operational_packet_freeze.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'preparation':ref(PACKET/'preparation.json'),
        'release_template':ref(PACKET/'release_template.json'),'prepared_file_count':len(hashes),'offline_tests':ref(proof),
        'execution':'NOT_RUN','static_release_materialized':False,'active_binding_created':False})
    print(json.dumps({'preparation':ref(PACKET/'preparation.json'),'release_template':ref(PACKET/'release_template.json'),'file_count':len(hashes),'execution':'NOT_RUN'}))
if __name__=='__main__':main()
