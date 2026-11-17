"""Private SFC prototype freeze; no Git/source-version/native/shared operation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
CID='hierarchy-synchronous-full-neighbor-composition'
EXP='M224-SFC'
REF='0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
CONFIG='configs/Quard/ctf_hcg_csort_sfc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_sfc.yaml'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(path):
    path=HERE/path if isinstance(path,str) else path
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)}
def save(name,value):(HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
source={p.relative_to(HERE/'staged_repository').as_posix():sha(p) for p in sorted((HERE/'staged_repository').rglob('*')) if p.is_file()}
assert len(source)==9 and sum(k.endswith('.py') for k in source)==8
save('source_manifest.json',{'schema_version':1,'candidate_id':CID,'experiment_id':EXP,'code_commit':None,'source_commit':None,'source_parent_commit':None,'future_version_parent':REF,'source_file_count':9,'model_file_count':8,'config':CONFIG,'source_files':source,'source_files_exact9':source})
description='Synchronous full-neighbor nonlinear node-state composition over the original true-supported three-level forest for each component exact tree diameter may provide a useful whole-DAG alternative before unchanged raw skips/HCG/singleinst. Ordinary GNN-family efficacy/novelty/task deficit remain UNKNOWN; this does not repair PES or prove new information.'
save('hypothesis.json',{'candidate_id':CID,'experiment_id':EXP,'hypothesis':description,'formula':'h0=original3LN(raw); for each component exactlyD genuine tree-diameter rounds: h_v_next=GELU(W[h_v_old,mean_{all original neighbors} h_u_old]); simultaneous replacement; finalhD is delta directly.',
    'matched_control':'Original M95 exact YAML/seed/data/pretrain/optimizer with paired naturalTRAIN2/resources',
    'closest_graphs':['PES ordered single-sender receiver events','CTS middle-only geometric cyclic triads','HPC fixed linear resolver/3FFN/resolver','DCE reverse-recipient cavity exclusion'],
    'risks':['Oversmoothing/degree averaging','Backtracking and repeated self-information','Shared map reduces separate layer-role capacity','Weak/unstable learned gradients and actual resource overhead','No proven new information, task deficit, novelty or efficacy'],
    'parameter_source_inference':{'C':256,'new':131328,'replaced':1576704,'delta':-1445376,'full_model':156038714,'maxN':328,'maxE':320,'maxD':4,'max_update_rows':1312,'linear_MAC':171966464,'original_linear_MAC':171966464,'scope':'Source algebra only, not actual resource inventory/PASS'},'native':'NOT_RUN','resources':'NOT_RUN','efficacy':'UNKNOWN','novelty':'UNKNOWN'})
validation=json.loads((HERE/'static_validation.json').read_text(encoding='utf-8'))
assert validation['status']=='PASS_SOFTWARE_ONLY_NOT_NATIVE' and validation['check_count']==35
save('candidate_record.json',{'id':CID,'experiment_id':EXP,'stage':'implementation','priority':1,'hypothesis':description,'matched_control':'Original M95 exact nativeYAML/seed/data/pretrain/optimizer and paired naturalTRAIN2/resources','config':CONFIG,'code_commit':None,'source_commit':None,'source_parent_commit':None,'future_version_parent':REF,'goal_sha256':GOAL,'authorization':{'path':'pipeline/authorizations/experiment_first_20261021.json','sha256':'2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8'},'evidence':[ref(name) for name in ('source_manifest.json','hypothesis.json','native_protocol.md','static_validation.json','static_validation_run1.json','software_oracle_correction.json')],'native_status':'NOT_RUN','resource_status':'NOT_RUN','efficacy':'UNKNOWN','novelty':'UNKNOWN','next_action':'Independent actual source/software review; leave source/code/actual-parentNULL. Future actual intended-main-compatible version/native tooling and fresh idleGPU0 paired TRAIN2/resources are separate steps. CurrentAOC/FCB and all old source/history remain protected; no Git/native/op/queue/receipt/promotion or old candidate recovery from this prototype.'})
prepared={p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='preparation.json'}
save('preparation.json',{'schema_version':1,'status':'PREPARED_STATIC_ONLY_UNVERSIONED_NATIVE_UNEXECUTED','recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,'experiment_id':EXP,'config':CONFIG,
    'code_commit':None,'source_commit':None,'source_parent_commit':None,'future_version_parent':REF,'base_reference_commit':REF,'future_version_parent_scope':'Reference only. Actual intended then-current main determines a separately saved/tested compatible version; no pre-signed sibling fast-forward.',
    'source_file_count':9,'model_file_count':8,'source_files':source,'prepared_file_hashes':prepared,'source_manifest':ref('source_manifest.json'),'native_protocol':ref('native_protocol.md'),'bounded_proposal_review':ref(HERE.parent/'sfc_proposal_boundary_review.json'),
    'static_check_command':'python -B pipeline/diagnostic_bundles/tick_9169196d/new_candidate_prepare/static_check.py','static_validation':ref('static_validation.json'),'actual_static_check_count':35,'actual_forward_scalar_GELU_carrier_cases':8,'invalid_metadata_cases':8,
    'first_software_failure':ref('static_validation_run1.json'),'software_oracle_correction':ref('software_oracle_correction.json'),'native':'NOT_RUN','resources':'NOT_RUN','Torch_FP32_autograd':'NOT_RUN','efficacy':'UNKNOWN','novelty':'UNKNOWN','frozen_sources':True,'no_primary_shared_Git_SSH_GPU_operations':True})
print(json.dumps({'preparation':ref('preparation.json'),'source_manifest':ref('source_manifest.json'),'native_protocol':ref('native_protocol.md'),'candidate_record':ref('candidate_record.json'),'prepared_file_count':len(prepared)}))
