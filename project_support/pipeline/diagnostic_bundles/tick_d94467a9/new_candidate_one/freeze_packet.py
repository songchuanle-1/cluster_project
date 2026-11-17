"""Freeze one NEC source-only prototype; no shared/Git/native operations."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
import author_guard as ag
ag.check();HERE=ag.HERE;ROOT=ag.ROOT
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
ref=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
CID='hierarchy-coupled-node-edge-state-composition';EXP='M228-NEC'
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nec'
CONFIG='configs/Quard/ctf_hcg_csort_nec/'+NAME+'.yaml'
BASE='94c4fe61b38f46f321a7ee84236fea70ade04d9b'
assert not (HERE/'preparation.json').exists()
assert sha(HERE/'proposal.md')=='82aaccf5e244e2487fb9f5f3391bed6d168d94b65dcc437a994fa51c4a7e4247'
assert sha(HERE/'native_protocol.md')=='17ba9fabee4b30da3ecbba33a8ca8d7096f017223013a0548b3a04551711c709'
valid=read(HERE/'static_validation.json');assert valid['status']=='PASS_SOFTWARE_ONLY_NOT_NATIVE' and valid['check_count']==29 and valid['Torch'] is False
sources={p.relative_to(HERE/'staged_repository').as_posix():sha(p) for p in sorted((HERE/'staged_repository').rglob('*')) if p.is_file()}
assert len(sources)==9 and sum(p.endswith('.py') for p in sources)==8 and sources==valid['source_files_exact9']
assert sources[CONFIG]=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
version={'code_commit':None,'source_commit':None,'source_parent_commit':None,'future_version_parent':None,'base_reference_commit':BASE}
work=read(ROOT/'pipeline/research_work.json');records=[{'id':c['id'],'experiment_id':c.get('experiment_id')} for c in work['candidates']]
assert not any(str(c.get('experiment_id','')).startswith('M228-') and c['id']!=CID for c in records)
near=('hierarchy-synchronous-full-neighbor-composition','hierarchy-undirected-edge-state-line-graph-composition','hierarchy-palindromic-euler-state-composition','hierarchy-directed-cavity-edge-composition','hierarchy-wedge-factor-incidence-composition','hierarchy-nonlinear-lifting-analysis-synthesis')
ag.save(HERE/'bounded_history_check.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_identifier_count':len(records),
    'candidate_identifiers_sha256':hashlib.sha256(json.dumps(records,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
    'proposed_id':CID,'proposed_experiment_id':EXP,'conflicting_global_id_or_M228':False,
    'initial_programmatic_namespace_check':'153 identifiers; neither proposed ID/M228 nor own primary model/YAML path existed at12:19Z. Root selected this exact single mechanism before any model write.',
    'relevant_short_hypotheses':[{'id':c['id'],'experiment_id':c.get('experiment_id'),'stage':c.get('stage'),'hypothesis':c.get('hypothesis')} for c in work['candidates'] if c['id'] in near],
    'read_scope':'IDs/experiment labels and bounded nearby short hypotheses only; actual SFC/ELC source used for graph contrast. No evidence-body/grants/checkpoint traversal.',
    'constraints_and_bans_checked':{'goal_sha256':sha(ROOT/'pipeline/goal.json'),'constraint_count':25,'banned_count':11},
    'no_general_novelty_or_efficacy_conclusion':True})
ag.save(HERE/'source_manifest.json',{'schema_version':1,'candidate_id':CID,'experiment_id':EXP,'config':CONFIG,**version,
    'source_files':sources,'source_files_exact9':sources,'source_file_count':9,'model_file_count':8,
    'staged_repository':(HERE/'staged_repository').relative_to(ROOT).as_posix(),
    'source_origin':'Six original M95 modules and a18 YAML from frozen WFC6595; original M95 hierarchy recovered from pinned7e1488 frozen LFT text. Only new NEC helper and CTF ctor/forward differ.',
    'current_dirty_user_or_primary_source_used':False})
ag.save(HERE/'hypothesis.json',{'candidate_id':CID,'experiment_id':EXP,**version,
    'hypothesis':'Coupled persistent true-node and true-edge states with synchronized edge-before-node nonlinear feedback may provide a useful different hierarchy point-feature factorization before original HCG/singleinst. No diagnosed deficit or novelty/efficacy claim.',
    'whole_DAG':'h0=original3LN(raw), e0=zeros on true original edges. For genuine component D rounds, edge=GELU(E[oldedge,mean2(oldendpointnodes)]); node=GELU(N[oldnode,meanincident(newedges)]); functional replacements, inactive components retained; finalhD→threeoriginal-IDdelta banks→originalrawskips/HCG.',
    'closest_differences':{'SFC':'Only N-state old-neighbor first-order recurrence; no persistent edge state or nonlinear edge-before-node feedback.','ELC':'Only E-state OTHER-line-neighbor recurrence; node means read once at end rather than persistent node feedback.','PES':'Asynchronous receiver-only node events, no E-state carrier.','DCE':'Recipient-excluded directed cavity DAG, not coupled undirected N/E dynamics.'},
    'source_inference_only':{'new_parameters_C256':262656,'old3FFN_parameters_C256':1576704,'parameter_delta':-1314048,
        'max_original_nodes':328,'max_original_edges':320,'component_diameter_bound':4,'new_linear_MAC_upper_original_caps':339738624,
        'old3FFN_linear_MAC':171966464,'historical_M95_countedG_reference':9.762532428,'linear_delta_proxyG_NOT_MEASURED':9.930304588,
        'no_width_depth_degree_sampling_or_handler_budget_adjustment':True,'whole_model_resource_status':'NOT_RUN'},
    'failure_modes':['Endpoint mean discards child-parent difference/role in new edge state.','Backtracking/self-information and ancestor descendant overlap can amplify redundant content.','Nonlinear overwrite can oversmooth/forget or amplify features; coupled states enlarge activation memory/kernel cost.','Maps, individual rows/columns or whole paths can degenerate; no per-map positivity gate.'],
    'native_trainability_gate':'Whole NEW two-map core aggregate finite/nonzero original-loss weight gradient and actual aggregate weight/module update only.',
    'efficacy':'UNKNOWN','novelty':'UNKNOWN','Torch_FP32_autograd':'NOT_RUN','native':'NOT_RUN','resources':'NOT_RUN'})
ag.write_text(HERE/'implementation.md','''# NEC source-only implementation

`NodeEdgeComposition` lives in the independent `_nec/node_edge_coupling.py`; attribute `dec.cluster_att.node_edge_coupling`, maps `edge_cell/node_cell` and one shared original GELU. Original constructor consumes all FFN/LN initialization before CPUfork creates new maps, then replaced FFNs become Identity rather than unused parameters. Common native pairing must exclude only removedFFNs/newcore and retain3LN dynamically.

Actual production helpers build true original-ID support, two-BFS exact component diameters, and scene-local rounds with separate node/edge offsets. Each round edge-cell reads OLD own edge and OLD endpoint nodes, then a single functional edge copy precedes the node-cell reading OLD own node and newly updated incident edges. Components that completed D generate neither edge nor node rows. Unsupported/pad rows get zero deltas; finalhD directly feeds original3rawskips/HCG/rawCSORT/singleinst path. No feature detach or mutation of raw banks/parents/FPS exists.

Metadata traversal is linear in true nodes/edges plus deterministic sorting; active round records and tensor work scale with D*(N+E), D at most4 for the original supported three-level forest. Python planning, copies/means and synchronization have real cost; source linear MAC proxy is not whole-call resources or10G PASS.

Executed command: `python -B -X utf8 pipeline/diagnostic_bundles/tick_d94467a9/new_candidate_one/static_check.py`. First run passed29 software checks, including9 actual production-forward AST/list cases, independent original-ID dual-state equations, a scalar-erf GELU case, mixedD2/D4 stop/no-fake-row control, edge-memory/NEWedge-read counterexamples and8 invalid metadata cases. Only four generic list primitives were extracted from an old checker; no old test main/assertions were executed. No first failure occurred. This is not Torch, FP32, parameter initialization equality, autograd, nativeTRAIN or resources evidence.

Prototype source/code/actual-parent remainNULL with current94 reference. No Git/source promotion/native/op/queue or shared state action occurred. A future then-current compatible version must be saved/tested; do not assume a sibling source can fast-forward. The ordinary message-passing family and all limitations remain explicit.
''')
ag.save(HERE/'candidate_record.json',{'id':CID,'experiment_id':EXP,'stage':'implementation','priority':1,'config':CONFIG,**version,
    'hypothesis':'Persistent node AND edge state, with synchronous edge-before-node nonlinear feedback on the unchanged true hierarchy forest, may alter useful point features before original HCG/singleinst; task deficit, efficacy and novelty UNKNOWN.',
    'matched_control':'OriginalM95 same nativeYAML/a18/seed1999/data/pretrain/criterion/optimizer/50epochs/maxiters70; no new dataset, loss, routing or repeat injection.',
    'native_status':'NOT_RUN','resource_status':'NOT_RUN','Torch_FP32_autograd':'NOT_RUN','efficacy':'UNKNOWN','novelty':'UNKNOWN',
    'evidence':[ref(HERE/name) for name in ('proposal.md','native_protocol.md','source_manifest.json','hypothesis.json','static_validation.json')],
    'next_action':'Root independent source review/register; later save exact9 on an actually compatible then-current parent and prepare fresh native tools; run original matchedTRAIN2/resources only on a genuinely free authorized slot. No ready/receipt/native claim from software.'})
files={p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='preparation.json'}
ag.save(HERE/'preparation.json',{'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'PREPARED_STATIC_ONLY_UNVERSIONED_NATIVE_UNEXECUTED',
    'candidate_id':CID,'experiment_id':EXP,'config':CONFIG,**version,'source_file_count':9,'model_file_count':8,'source_files':sources,
    'prepared_file_hashes':files,'source_manifest':ref(HERE/'source_manifest.json'),'native_protocol':ref(HERE/'native_protocol.md'),
    'candidate_record':ref(HERE/'candidate_record.json'),'static_validation':ref(HERE/'static_validation.json'),
    'static_check_command':valid['command'],'actual_static_check_count':29,'actual_forward_carrier_cases':9,'invalid_metadata_cases':8,
    'first_software_failure':None,'native':'NOT_RUN','resources':'NOT_RUN','Torch_FP32_autograd':'NOT_RUN','efficacy':'UNKNOWN','novelty':'UNKNOWN',
    'private_author_guard':ref(HERE/'private_author_guard_record.json'),'frozen_sources':True,'current_dirty_or_primary_source_used':False,
    'no_shared_Git_SSH_GPU_or_model_entry_operations':True,'independent_review':'EXTERNAL_PENDING_NO_CIRCULAR_HASH'})
print(json.dumps({'preparation':ref(HERE/'preparation.json'),'map_count':len(files),'source_manifest':ref(HERE/'source_manifest.json'),'candidate':ref(HERE/'candidate_record.json'),'protocol':ref(HERE/'native_protocol.md'),'helper_sha256':sources['framework/model/Quard_model/'+NAME+'/node_edge_coupling.py']},indent=2))
