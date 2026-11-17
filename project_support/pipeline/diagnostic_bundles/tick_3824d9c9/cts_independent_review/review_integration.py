"""Bounded read-only source/AST/linear-cost audit; never imports candidate/Torch."""
from pathlib import Path
from datetime import datetime,timezone
import ast
import hashlib
import json
import math

HERE=Path(__file__).resolve().parent
TICK=HERE.parent
PROJECT=HERE.parents[3]
PREP=TICK/'new_candidate_prepare'
SOURCE=PREP/'staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cts'
BASE=PROJECT/'Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
BFC=PROJECT/'pipeline/diagnostic_bundles/tick_ab7e46d4/bfc_native_prepare/candidate_model'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=lambda p:{'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
assert sha(PREP/'preparation.json')=='bfab01a31a0fc7a0d679156d5e0e6fcfa987e56e5f3bb1bdf6bded9e2208f76e'
prep=json.loads((PREP/'preparation.json').read_text(encoding='utf-8'))
checks={};sources={}
for entry in prep['source_files']:
    path=PREP/entry['prepared_path'];assert sha(path)==entry['sha256'];sources[entry['path']]=entry['sha256']
checks['exact_frozen_nine_source_config_hashes']=len(sources)==9
checks['full_prepared14_hash_map_matches']=len(prep['prepared_file_hashes'])==14 and all(sha(PREP/name)==expected for name,expected in prep['prepared_file_hashes'].items())
checks['source_commit_and_future_parent_deferred']=prep['code_commit'] is None and prep['source_commit'] is None and prep['future_version_parent'] is None and prep['base_reference_is_not_a_future_version_parent'] is True
checks['five_original_common_source_files_byte_exact']=all((SOURCE/name).read_bytes()==(BASE/name).read_bytes() for name in ('__init__.py','backbone.py','loss.py','network.py','sample_model.py'))
for name in ('dec.py','hier_postprocess.py'):
    text=(SOURCE/name).read_text(encoding='utf-8')
    for old,new in (('ParentCyclicTriadicStateComposition','ParentButterflyTokenComposition'),('middle_triad','middle_butterfly'),('ctf_hcg_csort_cts','ctf_hcg_csort_bfc'),('CTS','BFC')):text=text.replace(old,new)
    previous=(BFC/name).read_text(encoding='utf-8')
    checks[name+'_only_namespace_operator_name_substitution_from_reviewed_BFC']=text==previous
    checks[name+'_normalized_whole_AST_matches_reviewed_BFC']=ast.dump(ast.parse(text),include_attributes=False)==ast.dump(ast.parse(previous),include_attributes=False)
trees={name:ast.parse((SOURCE/name).read_text(encoding='utf-8')) for name in ('hier_postprocess.py','middle_triad.py')}
baseline=ast.parse((BASE/'hier_postprocess.py').read_text(encoding='utf-8'))
def cls(tree,name):return next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name==name)
def method(tree,owner,name):return next(node for node in cls(tree,owner).body if isinstance(node,ast.FunctionDef) and node.name==name)
dump=lambda node:ast.dump(node,include_attributes=False)
for owner,name in (('PointCloudPartitioner','partition_points'),('PointCloudPartitioner','cluster_layer'),('SharedClusterBank','build_cluster_feats')):
    checks[owner+'.'+name+'_original_whole_AST']=dump(method(trees['hier_postprocess.py'],owner,name))==dump(method(baseline,owner,name))
for name in ('C2F_ClusterAttn_Lite','C2F_ClusterAttn_CTF_HCG','C2F_ClusterAttn_CTF_HCG_CSORT'):
    checks[name+'_original_whole_class_AST']=dump(cls(trees['hier_postprocess.py'],name))==dump(cls(baseline,name))
cfg=PREP/'staged_repository/configs/Quard/ctf_hcg_csort_cts/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cts.yaml'
base_cfg=PROJECT/'Cluster/configs/Quard/ctf_hcg_csort/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml'
checks['original_complete_YAML_a18f_byte_exact']=sha(cfg)=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a' and cfg.read_bytes()==base_cfg.read_bytes()
for path in SOURCE.glob('*.py'):compile(path.read_text(encoding='utf-8'),str(path),'exec')
checks['eight_sources_AST_and_compile_without_import']=len(list(SOURCE.glob('*.py')))==8
helper=(SOURCE/'middle_triad.py').read_text(encoding='utf-8');hpost=(SOURCE/'hier_postprocess.py').read_text(encoding='utf-8')
checks['one_registered_shared_3C_to_C_map_default_GELU_no_gate_QKV_new_skip']=helper.count('nn.Linear(')==1 and 'nn.Linear(3 * channels, channels)' in helper and helper.count('nn.GELU()')==1 and 'register_buffer' not in helper and 'softmax' not in helper
checks['original_middle_identity_replacement_cf_skip_and_CPU_rng_scope']='self.cluster_ffn[1] = nn.Identity()' in hpost and 'refined = cf + self.middle_triad(' in hpost and 'with torch.random.fork_rng(devices=[]):' in hpost and 'manual_seed' not in hpost
topology=TICK/'cts_topology_review.json'
checks['external_actual_stdlib_topology_review_bound']=sha(topology)=='3de1e79f8d1e14d447185b1aff7fb6624c3cb450b1f42906f9bb2c888f7ede97' and json.loads(topology.read_text(encoding='utf-8'))['material_concerns']==[]
protocol=PREP/'native_protocol.md'
checks['frozen_future_native_protocol70363']=sha(protocol)=='70363d43bdac998d346cf06c817389267cb69682242430dca8819dd29b0fefdc'

C=256;K=64
def rows(n):
    if n==1:return 1
    offset=1;rounds=0
    while offset<n:rounds+=1;offset*=3
    return n*rounds
dp=[0]
for total in range(1,K+1):dp.append(max(dp[total-n]+rows(n) for n in range(1,total+1)))
new_params=3*C*C+C;old_params=2*C*(4*C)+(4*C)+C
new_linear=3*C*C*dp[K];old_linear=8*C*C*K
checks['independent_linear_parameter_and_max_rows_bound']=new_params==196864 and old_params==525568 and dp[K]==256 and new_linear==50331648 and new_linear-old_linear==16777216
assert all(checks.values()),checks
report={
    'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'status':'CTS_SOURCE_INTEGRATION_LINEAR_COST_AND_FUTURE_NATIVE_PROTOCOL_REVIEWED_NOT_NATIVE_PASS',
    'candidate_id':prep['candidate_id'],'experiment_id':'M214-CTS','code_commit':None,'source_commit':None,'future_version_parent':None,
    'preparation':ref(PREP/'preparation.json'),'source_preparation':ref(PREP/'preparation.json'),
    'frozen_nine_source_config_hashes':sources,'checks':checks,'logical_checks':len(checks),'material_concerns':[],
    'independent_topology_review':ref(topology),'author_static_validation':ref(PREP/'static_validation.json'),
    'source_review_script':ref(Path(__file__)),'native_protocol':ref(protocol),
    'integration':{
        'original_graph_preserved':'Five original common files/YAML exact; actual partition/FPS helpers, raw feature means, CSORT and HCG class ASTs exact. Dec/hpost differ from reviewed BFC only by namespace/operator names. Original middle LN/raw-cf skip and remaining FFNs/point injection retained.',
        'true_support':'Original detached per_layer_coords[2], original ids2 parents and actual point counts ids1[ids0]; no new partition, threshold, target/language selector or label-derived input.',
        'new_graph':'Each original parent uses fixed xyz+originalID order; at offsets1,3,9,...<n all receivers read the same OLD own/+/- state, within-row duplicate negative donors become private zero, then shared3C-toC map/GELU and one functional scatter. Different receiver rows intentionally share donors; own state is included.',
        'boundaries':'n1 uses the same map[x,0,0]; n0 none; unsupported/padded delta0 stays outside original raw IDs/CSORT/HCG. Singleton/alias/empty/pad tensor behavior and actual nonzero derivatives remain unmeasured.',
        'RNG':'Only new-module constructor uses CPU fork_rng after consuming the original FFN construction sequence; no seed or default initialization changes. Random sequence reuse correlations and actual common-init pairing remain unknown.',
    },
    'bounded_mechanism_scope':{
        'closest_family':'Dense3tap dilated circular Conv1D-family and whole-graph factorization alternative, explicitly acknowledged; no novelty or newly discovered whole-parent reachability claim.',
        'MDC_difference':'MDC is one-hop six geometric nearest directions with depthwise then pointwise mixing, potentially across parents. CTS is parent-only geometry-order cycles, three dense role matrices and repeated overlapping nonlinear receiver updates; more than a neighbor-count/kernel hyperparameter edit.',
        'BFC_difference':'BFC uses disjoint two-input/two-output pair stages; CTS uses overlapping three-input/one-output receiver stages. BFC already reaches full parent support; no CTS efficacy/coverage/causal benefit follows.',
        'held_routes':'No evidence of this being a repair/revision of weighted reversible transport/contact graph/complement scan; those old records remain untouched. This bounded source comparison is not a global history search or literature novelty conclusion.',
    },
    'cost_inference_only':{'channels':C,'middle_cap':K,'new_map_parameters':new_params,'old_middle_FFN_parameters':old_params,'parameter_delta':new_params-old_params,
        'max_rounds_per_group_at_cap':4,'per_group_linear_receiver_rows':'n*ceil(log3(n)) for n>=2; n1 one private-boundary row',
        'arbitrary_parent_partition_DP_max_receiver_rows':dp[K],'new_middle_linear_MAC_bound':new_linear,'old_middle_FFN_linear_MAC':old_linear,'linear_MAC_excess_bound':new_linear-old_linear,
        'not_counted':'GELU/index gather/scatter/allocation/CPU sort/tolist/synchronization and actual batch shape behavior. No counted10G, memory or latency PASS follows; original real profiler pair remains required.'},
    'future_native_contract':{
        'version_first':'code/futureparent intentionally null; choose actual future main parent and preserve exact9bytes before worker/runtime/source binding. No sibling branch/source ff promised by base_reference11a.',
        'original_inputs':'Exactly two original real TRAIN batches/native loss backward+optimizer once each, unchanged YAML/seed1999/pretrain/data/FP32/schedule, no full M95 training checkpoint or auxiliary backward/replay.',
        'required_actual_coverage':'Three distinct real source slots, multiround groups and actually consumed r>=1 within each original batch. Missing coverage INCONCLUSIVE; no resampling or changed seed.',
        'required_three_blocks':'own/positive/negative CxC column blocks each original-loss finite nonzero gradient and actual slice update per step; bias and individual call/row gradients may be zero if finite. No simultaneous-call nonzero rule.',
        'observer':'Original mix/GELU outputs captured once; old-state reference copies only actual outputs, exact private-zero alias and scatter/carry/source IDs, original cfskip/FFN0,2/CSORT/HCG/inst-mask loss path. No new tolerance/mean/QTQ/conservation gate.',
        'optional_boundaries':'Alias/singleton/internal-empty/padding counts recorded; absent cases NOT_EXERCISED, not hard coverage requirements.',
        'pairing_resources':'Actual complete input and common named-init fingerprints excluding only FFN1/new middle_triad; middle LN retained, full buffers/RNG not assumed. Original independent no-observer resource pair with handlers/unsupported/bs1/lang1/warm20/repeat100 and existing memory condition. Pure TRAIN/efficacy unknown.',
    },
    'limitations':['No Torch/Tensor/GELU/FP32/autograd, native loss, real gradients, dynamic parameter inventory, actual paired loader initialization, GPU resource or accuracy run occurred in this review.',
        'Reused actual independent stdlib plan/forward-list oracle report; did not rerun the264384 author assertions or old native/operational tests.',
        'Cycle wrap may connect distant centers; lex order is axis-dependent and ties use original ID. No rigid-motion/tie-relabel invariance, zero response, mean conservation, bias neutrality or invertibility claim.',
        'Repeated shared nonlinear updates can attenuate/amplify information; symbolic reachability is not useful learned information or empirical gain.',
        'Primary/remote/global state was not changed or queried by Git/SSH/GPU here; this is bounded source/AST evidence, not a fresh global runtime integrity or card availability check.'],
    'native_resources_transport_or_Git_actions':'NOT_RUN','scientific_admission':False,'source_version_ready':False,
    'recommendation':'Accept as statically reviewed external source reserve with deliberate version-packaging pending. Actual version, worker, original TRAIN2/path/three-block pairing and unchanged resource protocol remain mandatory before any technical admission.',
}
with (TICK/'cts_integration_review.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
print(json.dumps({'path':str(TICK/'cts_integration_review.json'),'sha256':sha(TICK/'cts_integration_review.json'),'checks':len(checks),'material_concerns':[],'source_commit':None,'native_resources':'NOT_RUN'}))
