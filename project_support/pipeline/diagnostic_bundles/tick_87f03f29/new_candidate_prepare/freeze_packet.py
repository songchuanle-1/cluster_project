"""One-time private metadata freeze; never touch primary source, Git or shared records."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
CID='hierarchy-undirected-edge-state-line-graph-composition'
EXP='M225-ELC'
MODEL='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_elc'
CONFIG=f'configs/Quard/ctf_hcg_csort_elc/{MODEL}.yaml'
REFERENCE='0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'

def digest(path):return sha256(path.read_bytes()).hexdigest()
def ref(path):return {'path':path.relative_to(ROOT).as_posix(),'sha256':digest(path)}
def save(name,value):
    p=HERE/name
    if p.exists():raise RuntimeError('Freeze output exists; preserve it: '+name)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def main():
    if (HERE/'preparation.json').exists():raise RuntimeError('Already frozen')
    review=HERE.parent/'elc_proposal_boundary_review.json'
    assert digest(review)=='246fb8d5be7f776d1a6a19e63362e0d092205c18967416d98cd24adf2c8654c5'
    assert json.loads(review.read_text(encoding='utf-8'))['material_concerns']==[]
    validation=json.loads((HERE/'static_validation.json').read_text(encoding='utf-8'))
    assert validation['status']=='PASS_SOFTWARE_ONLY_NOT_NATIVE' and validation['Torch'] is False
    staged=HERE/'staged_repository'
    source_files={p.relative_to(staged).as_posix():digest(p) for p in sorted(staged.rglob('*')) if p.is_file()}
    assert len(source_files)==9 and sum(p.endswith('.py') for p in source_files)==8 and CONFIG in source_files
    assert source_files[CONFIG]=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
    assert validation['source_file_hashes']=={'staged_repository/'+p:s for p,s in source_files.items()}
    version={'code_commit':None,'source_commit':None,'source_parent_commit':None,
             'future_version_parent':None,'base_reference_commit':REFERENCE,
             'future_version_parent_scope':'Current-main reference only. A future actual intended-main-compatible source version and real native tests must bind the then-current parent; no pre-signed sibling fast-forward.'}
    manifest={'schema_version':1,'candidate_id':CID,'experiment_id':EXP,**version,'config':CONFIG,
              'source_file_count':9,'model_file_count':8,'source_files':source_files,'source_files_exact9':source_files,
              'staged_repository':staged.relative_to(ROOT).as_posix(),
              'original_model':'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort',
              'original_YAML_sha256':source_files[CONFIG]}
    save('source_manifest.json',manifest)
    hypothesis='Persistent undirected states on the original true-supported hierarchy edges, composed through synchronous OTHER-incident-edge line-graph neighborhoods and shared endpoint readout, may provide a useful whole-DAG alternative before unchanged HCG/singleinst. This is an ordinary edge-state message-passing family hypothesis; task deficit, efficacy and novelty remain UNKNOWN.'
    save('hypothesis.json',{'candidate_id':CID,'experiment_id':EXP,'hypothesis':hypothesis,
         'matched_control':'Original M95, unchanged native YAML/seed/data/pretrain/optimizer/criterion/precision/schedule and future paired natural TRAIN2/resources',
         'closest_routes':{'M224-SFC':'N persistent node states and original-node neighbor means, unlike E shared undirected edge states and incident-node readout.',
                          'M220-DCE':'Directed receiver-specific cavity messages/up-down feed-forward graph, unlike one shared undirected edge state with synchronous edge feedback.',
                          'M216-AEF':'Middle sibling MST pair-flux with signed endpoint scatter, unlike positive incident means on original cross-level edges.'},
         'risks':['Endpoint incidence readout imposes real-arithmetic bipartite signed-degree constraint, including three-node middle/endpoint coupling; no FP32 admission test.',
                  'E states carry fewer vectors than N nodes and can lose independently addressable node semantics.',
                  'Smoothing, backtracking/self-information, degree mixing, CPU synchronization, actual resources and optimization are UNKNOWN.',
                  'Original raw ancestors/HCG may already provide global context. No diagnosed deficit, new-information, novelty, prior-crash repair or benefit claim.'],
         'source_parameter_arithmetic':{'channels':256,'new_core_parameters':262656,'removed_three_FFN_parameters':1576704,'delta_parameters':-1314048,'inferred_full_model_parameters':156170042,'actual_inventory':'NOT_RUN'},
         'source_linear_MAC_upper_estimate':{'original_native_K':[256,64,8],'maximum_edges':320,'maximum_line_rounds':3,'ELC':167772160,'original_three_FFN':171966464,'scope':'Linear layers only. Not full implementation FLOPs/resource proof.'},
         'native':'NOT_RUN','resources':'NOT_RUN','efficacy':'UNKNOWN','novelty':'UNKNOWN'})
    implementation='''# ELC frozen source prototype

Eight standalone model files use the original M95 package. Six originals (including dec.py) and native YAML are byte identical. Only CTF constructor/forward change, plus new edge_line_graph.py. The original FFN and LN constructors run first; both new Linear maps are created inside CPU fork_rng(devices=[]), and original FFNs become Identity. This preserves construction RNG position as a design control; actual named common initialization equality is NOT_RUN.

The helper APIs are build_edge_line_graph_plan, prepare_edge_line_graph_plans, build_edge_rounds, mean_adjacent_edge_states and incident_node_means. Module EdgeLineGraphComposition is held in cluster_att.edge_line_graph, with initialize/cell/activation. The forward returns three deltas, not raw+delta. Original three LN calls precede the core; original cf+delta/HCG/message_norm/pointmask path follows it. Original raw means/FPS/CSORT and one inst_feats delivery remain unchanged.

Real support is composed from point IDs through the original fine-to-middle and middle-to-coarse maps. Empty membership rows cannot create roots. Node/edge order uses original level/IDs, with child-parent initialization roles. Duplicate points do not duplicate factors. A supported component always has at least two edges; its exact tree diameter is found by two BFS and the line-graph diameter is Dtree-1. Empty scenes produce zero deltas. Active components stop after their own exact diameter.

Endpoint incidence groups are bucketed by degree. Each bucket gathers actual OLD edge states; exclusive prefix/suffix sums omit own edge at both endpoints. Their contributions are summed and divided once by deg(child)+deg(parent)-2, so each other edge has equal weight even under unequal endpoint degrees. No endpoint-mean-of-means, fake padding events or explicit edge-pair feature maps occur. Final incident means share the same final edge vector at both endpoints. Planner/reductions are O(N+E) per bounded round, excluding sorting and degree-bucket scheduling; whole-call CPU/kernel cost is unknown.

The small author check executes actual production plan/reduction/forward AST with an exact rational nonlinear/list carrier and one minimal-chain scalar-erf-GELU case against an independent keyed line-graph all-pairs-BFS oracle. This is source/control software evidence, not Torch/FP32/GELU/autograd/native or efficacy evidence. The first checker failed after 25 successful checks because one integration text read used Windows GBK implicitly. The preserved checker and negative JSON retain identical source hashes; the correction specifies UTF-8 only. Final 27 checks pass without model/source/protocol changes. No thresholds or sampling changes were introduced.

Only a source prototype is prepared. Version fields remain NULL; current 0314 is a reference, not an actual chosen future parent. Native tools/version save, actual common pairing, TRAIN2 and resource checks on a future compatible source version are separate work. GPU0 is occupied by original AOC; GPU1 remains forbidden. No main source/Git/shared record/remote/native operation occurred.
'''
    (HERE/'implementation.md').write_text(implementation,encoding='utf-8')
    evidence=[ref(HERE/name) for name in ('source_manifest.json','hypothesis.json','native_protocol.md','static_validation.json','static_validation_failed.json','software_harness_correction.json')]
    record={'id':CID,'experiment_id':EXP,'stage':'implementation','priority':1,'hypothesis':hypothesis,
            'matched_control':'Original M95 exact native YAML/seed/data/pretrain/criterion/optimizer and future paired natural TRAIN2/resources',
            'config':CONFIG,**version,'goal_sha256':'0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85',
            'authorization':{'path':'pipeline/authorizations/experiment_first_20261021.json','sha256':'2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8'},
            'evidence':evidence,'native_status':'NOT_RUN','resource_status':'NOT_RUN','efficacy':'UNKNOWN','novelty':'UNKNOWN',
            'next_action':'Independent actual source/software review and root-only registration. Future compatible actual source version and native tooling/paired TRAIN2/resources require fresh authorized idle GPU0. Current AOC remains untouched; no version, native, receipt, queue, promotion or recovery claim from this prototype.'}
    save('candidate_record.json',record)
    prepared={p.relative_to(HERE).as_posix():digest(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='preparation.json'}
    preparation={'schema_version':1,'status':'PREPARED_STATIC_ONLY_UNVERSIONED_NATIVE_UNEXECUTED',
                 'recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,'experiment_id':EXP,'config':CONFIG,**version,
                 'source_file_count':9,'model_file_count':8,'source_files':source_files,'prepared_file_hashes':prepared,
                 'source_manifest':ref(HERE/'source_manifest.json'),'native_protocol':ref(HERE/'native_protocol.md'),
                 'bounded_proposal_review':ref(review),'static_check_command':'python -B '+(HERE/'static_check.py').relative_to(ROOT).as_posix(),
                 'static_validation':ref(HERE/'static_validation.json'),'actual_static_check_count':validation['check_count'],
                 'actual_forward_carrier_cases':validation['actual_forward_cases'],'invalid_metadata_cases':validation['invalid_metadata_cases'],
                 'first_software_failure':ref(HERE/'static_validation_failed.json'),'software_harness_correction':ref(HERE/'software_harness_correction.json'),
                 'native':'NOT_RUN','resources':'NOT_RUN','Torch_FP32_autograd':'NOT_RUN','efficacy':'UNKNOWN','novelty':'UNKNOWN',
                 'frozen_sources':True,'no_primary_shared_Git_SSH_GPU_operations':True}
    save('preparation.json',preparation)
    print(json.dumps({'preparation_sha256':digest(HERE/'preparation.json'),'prepared_file_count':len(prepared),'source_file_count':len(source_files),
                      'manifest_sha256':digest(HERE/'source_manifest.json'),'protocol_sha256':digest(HERE/'native_protocol.md'),
                      'candidate_sha256':digest(HERE/'candidate_record.json'),'static_validation_sha256':digest(HERE/'static_validation.json')}))

if __name__=='__main__':main()
