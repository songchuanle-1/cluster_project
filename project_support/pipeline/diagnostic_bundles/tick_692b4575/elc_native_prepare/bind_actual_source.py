"""Bind proven isolated ELC source metadata in a new private packet; no Git or runtime entry."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,shutil
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_87f03f29/new_candidate_prepare'
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_928313fd/sfc_native_prepare'
CODE='18e64b8d95ed0ba5c1053ead114c0f91a4b0c324';PARENT='c9be548699cd66bf68badff9ae6198a03eafa142'
CID='hierarchy-undirected-edge-state-line-graph-composition';EXP='M225-ELC'
MODEL='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_elc'
CONFIG=f'configs/Quard/ctf_hcg_csort_elc/{MODEL}.yaml'
ACTIVE=['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def read_ref(rel,h):
    p=ROOT/rel;assert sha(p)==h,p;return p,json.loads(p.read_text(encoding='utf-8'))
def save(name,value):
    p=HERE/name
    if p.exists():raise RuntimeError('Do not overwrite bound evidence '+name)
    p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert not (HERE/'source_version_binding.json').exists()
proof_path,proof=read_ref('pipeline/diagnostic_bundles/tick_692b4575/elc_version_prepare/isolated_source_version.json','c1950ac3eb158ad5aaf4c5a034f6de39125da360fc66e22bae81d0d3295196b1')
peer_path,peer=read_ref('pipeline/diagnostic_bundles/tick_692b4575/elc_actual_source_version_independent_review.json','fd6c9f7be6dcded39ea141c9200a484ca15617e03ca1042f5a75e9a7d91fa36e')
source_path,source=read_ref('pipeline/diagnostic_bundles/tick_87f03f29/new_candidate_prepare/preparation.json','c77746ae35e4f3bfbc1c58e62aff629798946bb91dd0befbd08f247ca5dd7dd8')
old_peer=ROOT/'pipeline/diagnostic_bundles/tick_87f03f29/elc_source_independent_review.json'
assert sha(old_peer)=='4348ded58c6f70cb9d0c7e7915b9794ceb27958051e7cc77d8bd0c8c7eb1d792'
assert proof['code_commit']==CODE and proof['parent_commit']==PARENT and proof['diff_exact9A'] is True
assert proof['frozen_source_files']==proof['committed_blob_sha256']==source['source_files']
assert peer['code_commit']==CODE and peer['material_concerns']==[]
assert all(source[k] is None for k in ('code_commit','source_commit','source_parent_commit'))
model_hashes={Path(rel).name:h for rel,h in source['source_files'].items() if rel.endswith('.py')}
assert len(model_hashes)==8 and all(sha(HERE/'candidate_model'/n)==h for n,h in model_hashes.items())
runtime_path=HERE/'native_runtime.py';before=runtime_path.read_bytes();runtime=before.decode('utf-8')
assert b'DRAFT_EXECUTION_DISABLED = True' in before and b'CANDIDATE_COMMIT = None' in before and b'SOURCE_PARENT_COMMIT = None' in before
runtime=runtime.replace('DRAFT_EXECUTION_DISABLED = True','DRAFT_EXECUTION_DISABLED = False',1)
runtime=runtime.replace('CANDIDATE_COMMIT = None',"CANDIDATE_COMMIT = '"+CODE+"'",1)
runtime=runtime.replace('SOURCE_PARENT_COMMIT = None',"SOURCE_PARENT_COMMIT = '"+PARENT+"'",1)
compile(runtime,str(runtime_path),'exec');runtime_path.write_text(runtime,encoding='utf-8',newline='\n')
scope='Actual ELC18e singlechildSFCc9, conditional expectedruntime c9. Current main/runtime AOC0314 untouched/ineligible. Future mutation requires genuine M224-SFC technical receipt and actual main/runtime c9, fresh owner/deadline/physical0/idle/three locks; no SFC training completion or efficacy gate. If main takes another path, preserve this packet and save/test a genuinely compatible source version. Original c777 NULL/ref0314/22map and prior WIPTrue/None preserved.'
binding={'schema_version':1,'candidate_id':CID,'experiment_id':EXP,'code_commit':CODE,'parent_commit':PARENT,'runtime_expected_commit':PARENT,
    'candidate_source_hashes':model_hashes,'candidate_config_sha256':sha(HERE/'candidate.yaml'),'source_files':source['source_files'],
    'original_source_preparation_sha256':sha(source_path),'source_preparation':ref(source_path),'native_protocol':source['native_protocol'],
    'isolated_source_version':ref(proof_path),'isolated_source_version_independent_review':ref(peer_path),'independent_source_review':ref(old_peer),'scope':scope}
save('source_version_binding.json',binding)
manifest=json.loads((ORIGIN/'manifest_template.json').read_text(encoding='utf-8'))
manifest.update(candidate_id=CID,experiment_id=EXP,candidate_name=MODEL,config=CONFIG,code_commit=CODE,
    source_preparation_sha256=sha(source_path),draft_execution_disabled=False,source_version_commit=CODE,
    source_version_binding_sha256=sha(HERE/'source_version_binding.json'),source_parent_commit=PARENT,future_version_parent=PARENT,
    runtime_expected_commit=PARENT,base_reference_commit=source['base_reference_commit'],candidate_source_hashes=model_hashes,candidate_config_sha256=sha(HERE/'candidate.yaml'),
    protocol='Original unchanged native M95/ELC paired naturalTRAIN2 and full original resource function. Actual original3LN -> U[child,parent]/GELU once -> E undirected states -> exact line-D OLDstate own/OTHER incident-edge degree mean -> sharedR/GELU -> one functionalcopy per active round -> original finalincidentmean once ->3delta/rawskip/HCG/singleinst. Capture each original return once unchanged, no operator/model/criterion/backward replay. Whole initialize+cell aggregate original-loss finite/nonzero weight and aggregate actual weight/module updates only; individual map/edge/round/column/bias0 legal; no forced line-D3/multicomponent/FP32/Jacobian gate. Version-bound conditionalDRAFTFalse+10activeNULL; missingmanifest beforeTorch. ActualruntimeSFCc9/genuineM224 technicalreceipt/freshowner/idleGPU0/three locks required; current0314 ineligible. Native/resourcesNOT_RUN.')
for key in ACTIVE:manifest[key]=None
diagnostic={f'candidate_model/{n}':h for n,h in model_hashes.items()}
diagnostic.update({n:sha(HERE/n) for n in ('candidate.yaml','worker.py','native_runtime.py','source_version_binding.json')})
manifest['diagnostic_files']=diagnostic;assert len(diagnostic)==12
save('manifest_template.json',manifest)
save('binding_provenance.json',{'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,
    'original_unversioned_disabled_wip':{'runtime':ref(HERE/'unversioned_disabled_wip/native_runtime.py'),'worker':ref(HERE/'unversioned_disabled_wip/worker.py'),'scope':ref(HERE/'unversioned_disabled_wip/draft_scope.json')},
    'formal_constant_changes_only':['DRAFT_EXECUTION_DISABLED True -> False','CANDIDATE_COMMIT None -> actual18e','SOURCE_PARENT_COMMIT None -> actualc9'],
    'wip_worker_bytes_equal_formal_worker':sha(HERE/'worker.py')==sha(HERE/'unversioned_disabled_wip/worker.py'),
    'actual_source_version':ref(proof_path),'actual_source_peer':ref(peer_path),'scope':scope,'native':'NOT_RUN','resources':'NOT_RUN'})
print(json.dumps({'worker':sha(HERE/'worker.py'),'runtime':sha(runtime_path),'template':sha(HERE/'manifest_template.json'),'binding':sha(HERE/'source_version_binding.json')}))
