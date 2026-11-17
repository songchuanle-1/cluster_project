"""Freeze only the private unversioned WFC prototype; never touch primary/shared records."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
CID='hierarchy-wedge-factor-incidence-composition';EXP='M226-WFC'
BASE='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort';MODEL=BASE+'_wfc'
CONFIG=f'configs/Quard/ctf_hcg_csort_wfc/{MODEL}.yaml';REFERENCE='18e64b8d95ed0ba5c1053ead114c0f91a4b0c324'
FROZEN=ROOT/'pipeline/diagnostic_bundles/tick_87f03f29/new_candidate_prepare'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(name,value):
 p=HERE/name;assert not p.exists(),name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert not (HERE/'preparation.json').exists()
boundary=HERE.parent/'wfc_proposal_boundary_review.json'
assert sha(boundary)=='1e491a1cc4730907b7078cdfcc34e62438f56621a6bc37f0298ec2b4f66d91db' and json.loads(boundary.read_text(encoding='utf-8'))['material_concerns']==[]
assert sha(HERE/'proposal.md')=='692a0b49a218bda7253912b2161907e9640bec101342123bdcdb291d27636ede'
assert sha(HERE/'native_protocol.md')=='cc9a6be9f1683d0dae0526c8c41fdd0bc752ff9b6b731c35269b52dec1d4c6f0'
validation=json.loads((HERE/'static_validation.json').read_text(encoding='utf-8'))
assert validation['status']=='PASS_SOFTWARE_ONLY_NOT_NATIVE' and validation['Torch'] is False
staged=HERE/'staged_repository';sources={p.relative_to(staged).as_posix():sha(p) for p in sorted(staged.rglob('*')) if p.is_file()}
assert len(sources)==9 and sum(k.endswith('.py') for k in sources)==8 and sources[CONFIG]=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
assert validation['source_file_hashes']=={'staged_repository/'+p:h for p,h in sources.items()}
version={'code_commit':None,'source_commit':None,'source_parent_commit':None,'future_version_parent':None,'base_reference_commit':REFERENCE,
         'future_version_parent_scope':'Reference only; actual future then-current intended main must determine a separately saved/tested compatible source version. No sibling fast-forward assumption.'}
save('source_manifest.json',{'schema_version':1,'candidate_id':CID,'experiment_id':EXP,**version,'config':CONFIG,'source_file_count':9,'model_file_count':8,
    'source_files':sources,'source_files_exact9':sources,'staged_repository':staged.relative_to(ROOT).as_posix(),
    'frozen_base_preparation':ref(FROZEN/'preparation.json'),'original_M95_hier_recovered_sha256':'7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f',
    'original_YAML_sha256':sources[CONFIG],'primary_or_dirty_user_file_read':False})
hypothesis='One shared nonlinear factor for each original-tree center and unordered pair of real neighbors, followed by equal incidence readout to its three nodes, may provide a useful whole-DAG hierarchy alternative before unchanged HCG/singleinst. Ordinary hypergraph-factor family efficacy, task deficit and novelty remain UNKNOWN.'
save('hypothesis.json',{'candidate_id':CID,'experiment_id':EXP,'hypothesis':hypothesis,'matched_control':'Original M95 with exact native YAML/seed/data/pretrain/criterion/optimizer/precision/schedule and future paired natural TRAIN2/resources',
    'closest_routes':{'M219-APF':'Only ancestor triplets and three independent output slices, versus all real wedges and sameq three-node incidence readout.',
                      'M224-SFC':'One neighbor mean before learned node update, versus each distinct-neighbor-pair learned factor before incidence mean; no iterations.',
                      'M225-ELC':'Persistent undirected edge states with nonlinear line-graph recurrence, versus stateless three-node wedge factors.'},
    'source_arithmetic':{'channels':256,'new_map_parameters':131328,'removed_three_FFN_parameters':1576704,'delta_parameters':-1445376,'inferred_full_model_parameters':156038714,
                         'linear_MAC_formula':'2*C*C*W','W_formula':'sum_m choose(f_m+1,2)+sum_c choose(m_c,2)','balanced_native_cap_W':864,'balanced_linear_MAC':113246208,
                         'conservative_independent_max_W_upper_bound':34912,'upper_bound_not_jointly_attainable':True,'conservative_MAC_upper_bound':4575985664,
                         'prior_unchanged_geometry_TRAIN_trace_W_per_model_slot':[948,992],'prior_trace_scope':'Only metadata-derived source estimate, NOT WFC model/native/resource evidence. No degree cap or sampling.'},
    'risks':['Single true fine path gives one factor and all three deltas equal q; sameq node-role capacity coupling.',
             'Endpoint sum makes swapped endpoints or equal-sum endpoint values indistinguishable; some learned parameters may ignore endpoint/center information.',
             'Degree-squared factor count/CPU planning, high-branch incidence weighting, smoothing, optimizer and actual10G/latency/memory are unknown.',
             'Original raw banks/HCG already carry wider context; no new-information/bottleneck/novelty/earlier crash repair claim.'],
    'native':'NOT_RUN','resources':'NOT_RUN','Torch_FP32_autograd':'NOT_RUN','efficacy':'UNKNOWN','novelty':'UNKNOWN'})
(HERE/'implementation.md').write_text('''# WFC implementation and evidence limits

The standalone package has eight Python files plus original native YAML bytes under a unique filename. Six original M95 files are copied byte-for-byte from frozen ELC prototype c777. The original M95 hierarchy file is recovered by reversing its recorded exact ELC constructor/forward changes and pinned to original SHA7e1488 before applying WFC changes. No primary repository or28 dirty user file was read or modified.

Only CTF constructor/forward and new wedge_factor.py differ from frozen original M95. Original three FFNs and three LNs are constructed in their original order. New WedgeFactorComposition.factor_map(default2C-toC) and original-type GELU are built in CPU fork_rng(devices=[]), then old three FFNs become Identity with zero unused parameters. Three original LN outputs feed the core once, and its three delta arrays feed original cf+delta/HCG/message_norm/masking/singleinst path. Common initialization pairing is intended by construction but is NOT_RUN.

Helper APIs: build_wedge_factor_plan, prepare_wedge_factor_plans, mean_wedge_incidence and WedgeFactorComposition.forward. Module attr is cluster_att.wedge_factor, learned map factor_map and activation. True support composes original point IDs through both original parent maps, not unique allocated coarse rows. Node keys are(level,originalID); duplicate points do not duplicate a node/factor. Each center enumerates every unordered distinct adjacent pair once. No learned weights, altered raw pools, gates, QKV, extra raw skips or inst injections occur.

Forward packs original normalized node rows, gathers center and endpoints, forms [center,left+right], calls one global factor_map/GELU for all actual wedges, calls one original private incidence mean and scatters three deltas to original bank IDs. Every true supported node in the legal three-level forest has at least one wedge; no epsilon denominator or fake factor is needed. Empty scenes/zero batch produce zero deltas and no map. Complexity is O(nodes+edges+wedges) metadata plus per-factorC operations, excluding sorting. Degree-squared W can violate resource budget in some geometry; only actual original resource measurement may decide, without cap/resampling.

The author executed actual production plan/mean/forward AST with a small rational nonlinear/list carrier and one scalar-erf-GELU/list case, against an independent original-ID keyed neighbor-pair oracle. Eleven forward cases, eight invalid metadata examples and bounded integration/arithmetic checks passed35 checks first-run. Generic list primitive definitions were reused without executing any old test main or production helper. This is software evidence only, not real Torch/Linear/GELU/FP32/autograd/TRAIN or efficacy proof. The sibling-dependency example uses a controlled legal map, not a mandatory future Jacobian or positivity gate.

Code/source/actual-parent remain NULL;18e is reference only. Both original SFC/ELC formal runs remain protected. No Git/version/source promotion, native tools/compute, remote/GPU, scheduler/shared research write, receipt, queue or checkpoint access occurred. Native/resource/actual common pairing are NOT_RUN and effect/novelty UNKNOWN.
''',encoding='utf-8')
evidence=[ref(HERE/n) for n in ('proposal.md','source_manifest.json','hypothesis.json','native_protocol.md','static_validation.json')]
save('candidate_record.json',{'id':CID,'experiment_id':EXP,'stage':'implementation','priority':1,'hypothesis':hypothesis,'matched_control':'Original M95 exact nativeYAML/data/seed/pretrain/criterion/optimizer/precision/schedule and future paired natural TRAIN2/resources',
    'config':CONFIG,**version,'goal_sha256':'0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85',
    'authorization':{'path':'pipeline/authorizations/experiment_first_20261021.json','sha256':'2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8'},
    'evidence':evidence,'native_status':'NOT_RUN','resource_status':'NOT_RUN','efficacy':'UNKNOWN','novelty':'UNKNOWN',
    'next_action':'Independent actual source/software review and root-only registration as source prototype. Future actual compatible version/native tooling and original paired TRAIN2/resources need a genuinely free authorized card, fresh owner/original window/assets/UUID/three locks. Protect original SFC/ELC formal runs; no version/admission/queue/promotion or old route recovery from this prototype.'})
prepared={p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='preparation.json'}
prep={'schema_version':1,'status':'PREPARED_STATIC_ONLY_UNVERSIONED_NATIVE_UNEXECUTED','recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,'experiment_id':EXP,'config':CONFIG,**version,
    'source_file_count':9,'model_file_count':8,'source_files':sources,'prepared_file_hashes':prepared,'source_manifest':ref(HERE/'source_manifest.json'),'native_protocol':ref(HERE/'native_protocol.md'),
    'bounded_proposal_review':ref(boundary),'reference_frozen_base_preparation':ref(FROZEN/'preparation.json'),'generic_list_carrier_definitions_reference':ref(FROZEN/'static_check.py'),
    'static_check_command':'python -B pipeline/diagnostic_bundles/tick_34f4e385/new_candidate_prepare/static_check.py','static_validation':ref(HERE/'static_validation.json'),
    'actual_static_check_count':validation['check_count'],'actual_forward_carrier_cases':validation['actual_forward_carrier_cases'],'invalid_metadata_cases':validation['invalid_metadata_cases'],
    'first_software_failure':None,'native':'NOT_RUN','resources':'NOT_RUN','Torch_FP32_autograd':'NOT_RUN','efficacy':'UNKNOWN','novelty':'UNKNOWN','frozen_sources':True,
    'primary_or_dirty_user_file_read':False,'no_primary_shared_Git_SSH_GPU_operations':True,'independent_review':'EXTERNAL_PENDING_NOT_CIRCULARLY_MAPPED'}
save('preparation.json',prep)
print(json.dumps({'preparation':sha(HERE/'preparation.json'),'prepared_file_count':len(prepared),'manifest':sha(HERE/'source_manifest.json'),'candidate_record':sha(HERE/'candidate_record.json'),'protocol':sha(HERE/'native_protocol.md'),'static_validation':sha(HERE/'static_validation.json')}))
