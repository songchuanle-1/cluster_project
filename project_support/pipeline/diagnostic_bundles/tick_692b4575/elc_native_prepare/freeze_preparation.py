"""Freeze only private ELC native preparation metadata, never execute runtime or model."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_928313fd/sfc_native_prepare'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
assert not (HERE/'preparation.json').exists(),'Frozen packet must remain immutable'
manifest=read(HERE/'manifest_template.json');binding=read(HERE/'source_version_binding.json');validation=read(HERE/'static_validation.json')
assert validation['status']=='PASS_SOFTWARE_PREPARATION_ONLY_NOT_NATIVE' and validation['Torch'] is False
assert validation['worker_sha256']==sha(HERE/'worker.py') and validation['runtime_sha256']==sha(HERE/'native_runtime.py')
assert validation['manifest_template_sha256']==sha(HERE/'manifest_template.json') and validation['source_version_binding_sha256']==sha(HERE/'source_version_binding.json')
active=['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']
assert all(manifest[k] is None for k in active)
assert manifest['draft_execution_disabled'] is False and not any((HERE/n).exists() for n in ('native_manifest.json','lease.json','adapter_release.json'))
owner_ast=ast.parse((HERE.parent/'anchor.py').read_text(encoding='utf-8'))
owner=next(ast.literal_eval(n.value) for n in owner_ast.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED' for t in n.targets))
model_source_files={k:v for k,v in binding['source_files'].items()}
prepared={p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='preparation.json'}
preparation={'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'status':'CONDITIONAL_VERSION_BOUND_ELC_NATIVE_SOFTWARE_PREPARATION_NOT_NATIVE_PASS',
    'candidate_id':binding['candidate_id'],'experiment_id':binding['experiment_id'],'code_commit':binding['code_commit'],
    'source_commit':binding['code_commit'],'source_parent_commit':binding['parent_commit'],'runtime_expected_commit':binding['runtime_expected_commit'],
    'current_primary_runtime_reference':'0314b932a92a8cc7f67804068ecb1c1f7a5f2e33',
    'execution_condition':binding['scope'],'source_preparation':binding['source_preparation'],'source_preparation_sha256':binding['original_source_preparation_sha256'],
    'native_protocol':binding['native_protocol'],'isolated_source_version':binding['isolated_source_version'],
    'isolated_source_version_independent_review':binding['isolated_source_version_independent_review'],'independent_source_review':binding['independent_source_review'],
    'source_version_binding':ref(HERE/'source_version_binding.json'),'manifest_template':ref(HERE/'manifest_template.json'),
    'draft_execution_disabled':False,'prepared_under_parent':owner,'manifest_execution_fields':{k:None for k in active},
    'source_file_count':9,'model_file_count':8,'source_files':model_source_files,'diagnostic_file_count':len(manifest['diagnostic_files']),
    'static_validation':ref(HERE/'static_validation.json'),'actual_static_check_count':validation['check_count'],
    'static_check_command':'python -B pipeline/diagnostic_bundles/tick_692b4575/elc_native_prepare/static_check.py',
    'binding_provenance':ref(HERE/'binding_provenance.json'),'reference_native_preparation':ref(ORIGIN/'preparation.json'),
    'resources_scope':'Entire original resources AST/handlers/fullunsupported/bs1lang1/warm20repeat100/10G/existing15%-memory condition unchanged. No new latency gate.',
    'common_scope':'Dynamic original initialized names/shapes/count/hash, exclude old3FFNs/new edge_line_graph and retain3LN. Actual equality unmeasured.',
    'trainability_scope':'Whole initialize+cell core weight original-loss finite/nonzero aggregate and actual aggregate weight/module update only; maps/edges/rounds/nodes/columns/bias0 legal. No lineD3/multicomponent/FP32/conservation/Jacobian/coverage threshold.',
    'capture_scope':'Actual initialize/GELU/prepare/plan/round/adjacentmean/cell/GELU/indexcopy/finalincidentmean returns once, original objects propagated. Scoped stack/select/copy installed in try and restored finally. Frozen mean semantics observed via input/plan/gather identity, no operator/model/backward replay.',
    'native':'NOT_RUN','native_TRAIN2':'NOT_RUN','resources':'NOT_RUN','Torch_autograd_FP32_behavior':'NOT_RUN',
    'actual_common_initialization_and_TRAIN_pairing':'NOT_RUN','efficacy':'UNKNOWN','novelty':'UNKNOWN',
    'current_binding_manifest_lease_release_created':False,'author_native_SSH_GPU_Git_shared_or_primary_operation':False,
    'independent_review':'EXTERNAL_PENDING_NOT_CIRCULARLY_MAPPED','material_concerns':[],'prepared_file_hashes':prepared}
(HERE/'preparation.json').write_text(json.dumps(preparation,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({'preparation_sha256':sha(HERE/'preparation.json'),'map_count':len(prepared),'worker_sha256':sha(HERE/'worker.py'),
    'runtime_sha256':sha(HERE/'native_runtime.py'),'template_sha256':sha(HERE/'manifest_template.json'),'binding_sha256':sha(HERE/'source_version_binding.json')}))
