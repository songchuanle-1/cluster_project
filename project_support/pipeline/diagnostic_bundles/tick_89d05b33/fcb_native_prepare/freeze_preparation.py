"""Freeze private conditional FCB native metadata only; no entry import or operation."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_f8d84d12/new_candidate_prepare'
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_2ef53d6b/aoc_native_prepare'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
source,binding,template,validation=(read(p) for p in (SOURCE/'preparation.json',HERE/'source_version_binding.json',HERE/'manifest_template.json',HERE/'static_validation.json'))
assert validation['status']=='PASS_SOFTWARE_ONLY_NOT_NATIVE' and validation['check_count']==32
assert validation['worker_sha256']==sha(HERE/'worker.py') and validation['runtime_sha256']==sha(HERE/'native_runtime.py') and validation['manifest_template_sha256']==sha(HERE/'manifest_template.json')
for name,expected in template['diagnostic_files'].items():assert sha(HERE/name)==expected
active=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')
assert template['draft_execution_disabled'] is False and all(template[key] is None for key in active)
owner=next(ast.literal_eval(n.value) for n in ast.parse((HERE.parent/'anchor.py').read_text(encoding='utf-8')).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED' for t in n.targets))
prepared={p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='preparation.json'}
packet={'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'CONDITIONAL_VERSION_BOUND_FCB_NATIVE_SOFTWARE_PREPARATION_NOT_NATIVE_PASS',
    'candidate_id':binding['candidate_id'],'experiment_id':binding['experiment_id'],'code_commit':binding['code_commit'],'source_commit':binding['code_commit'],
    'source_parent_commit':binding['parent_commit'],'runtime_expected_commit':binding['runtime_expected_commit'],
    'current_primary_runtime_reference':'9c42fdc4e9168acec18980d782ee9c163e043bb7',
    'execution_condition':'Future actualmain/runtime0314 and genuineAOC technical receipt plus fresh reviewed operational binding. Current9c is ineligible; no AOC training completion or efficacy gate. If main path changes, save/test an actually compatible source, not cumulative18A fast-forward.',
    'source_preparation':ref(SOURCE/'preparation.json'),'source_preparation_sha256':sha(SOURCE/'preparation.json'),'native_protocol':ref(SOURCE/'native_protocol.md'),
    'isolated_source_version':binding['isolated_source_version'],'isolated_source_version_independent_review':binding['isolated_source_version_independent_review'],
    'independent_source_review':binding['independent_source_review'],'source_version_binding':ref(HERE/'source_version_binding.json'),
    'manifest_template':ref(HERE/'manifest_template.json'),'draft_execution_disabled':False,'prepared_under_parent':owner,
    'manifest_execution_fields':{key:template[key] for key in active},'source_file_count':9,'model_file_count':8,'source_files':source['source_files'],
    'diagnostic_file_count':len(template['diagnostic_files']),'static_validation':ref(HERE/'static_validation.json'),'actual_static_check_count':32,
    'static_check_command':'python -B pipeline/diagnostic_bundles/tick_89d05b33/fcb_native_prepare/static_check.py','binding_provenance':ref(HERE/'binding_provenance.json'),
    'reference_native_preparation':ref(ORIGIN/'preparation.json'),
    'resources_scope':'Complete original resource function AST/handlers/fullunsupported/bs1lang1/warm20repeat100/10G/existing15%-memory condition unchanged. No new latency gate.',
    'common_scope':'Dynamic original initialized names/shapes/count/hash; exclude original3FFNs/newfine_coarse_bipartite, retain3LN. Actual paired equality unmeasured.',
    'trainability_scope':'Whole two-map core weight original-loss finite/nonzero aggregate and actual aggregate weight/module update only. Individual maps/pairs/rows/4columns/bias0 legal. No FP32marginal/Jacobian/multiroot/per-scene gate.',
    'native':'NOT_RUN','native_TRAIN2':'NOT_RUN','resources':'NOT_RUN','Torch_autograd_FP32_behavior':'NOT_RUN',
    'actual_common_initialization_and_TRAIN_pairing':'NOT_RUN','efficacy':'UNKNOWN','novelty':'UNKNOWN',
    'current_binding_manifest_lease_release_created':False,'author_native_SSH_GPU_Git_shared_or_primary_operation':False,
    'independent_review':'EXTERNAL_PENDING_NOT_CIRCULARLY_MAPPED','material_concerns':[],'prepared_file_hashes':prepared}
(HERE/'preparation.json').write_text(json.dumps(packet,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({'preparation':ref(HERE/'preparation.json'),'worker':ref(HERE/'worker.py'),'runtime':ref(HERE/'native_runtime.py'),
    'template':ref(HERE/'manifest_template.json'),'source_version_binding':ref(HERE/'source_version_binding.json'),'prepared_file_count':len(prepared),'diagnostic_file_count':len(template['diagnostic_files'])}))
