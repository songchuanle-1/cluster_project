"""Bind a new private disabled packet to actual AOC source evidence; no entry execution."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,shutil
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_e666cac0/new_candidate_prepare'
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_9db8f3be/pes_native_prepare'
CODE='0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'
PARENT='9c42fdc4e9168acec18980d782ee9c163e043bb7'
CID='hierarchy-ancestral-order-commutator-composition'
EXP='M222-AOC'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(name,value):(HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
proof=ROOT/'pipeline/diagnostic_bundles/tick_2ef53d6b/aoc_version_prepare/isolated_source_version.json'
assert sha(proof)=='83d8bedd7ae1fae56c835028460f380ae797ed57f1b99f1016f155a88fec414e'
version=json.loads(proof.read_text(encoding='utf-8'))
assert version['code_commit']==CODE and version['parent_commit']==PARENT
prep=json.loads((SOURCE/'preparation.json').read_text(encoding='utf-8'))
assert prep['candidate_id']==CID and all(prep[k] is None for k in ('code_commit','source_commit','source_parent_commit'))
for relative,expected in prep['source_files'].items():assert sha(SOURCE/'staged_repository'/relative)==expected
runtime=(HERE/'native_runtime.py').read_text(encoding='utf-8')
if not (HERE/'initial_native_runtime_draft.py.txt').exists():
    (HERE/'initial_native_runtime_draft.py.txt').write_text(runtime,encoding='utf-8',newline='\n')
runtime=runtime.replace("'M221-AOC'","'M222-AOC'")
assert runtime.count('CANDIDATE_COMMIT = None')==1 and runtime.count('SOURCE_PARENT_COMMIT = None')==1
runtime=runtime.replace('CANDIDATE_COMMIT = None',f'CANDIDATE_COMMIT = {CODE!r}')
runtime=runtime.replace('SOURCE_PARENT_COMMIT = None',f'SOURCE_PARENT_COMMIT = {PARENT!r}')
assert 'DRAFT_EXECUTION_DISABLED = True' in runtime and f"RUNTIME_EXPECTED_COMMIT = '{PARENT}'" in runtime
(HERE/'native_runtime.py').write_text(runtime,encoding='utf-8',newline='\n')
if (HERE/'draft_scope.json').exists() and not (HERE/'initial_draft_scope.json').exists():
    shutil.copyfile(HERE/'draft_scope.json',HERE/'initial_draft_scope.json')
candidate_hashes={p.name:sha(p) for p in sorted((HERE/'candidate_model').glob('*.py'))}
binding={'schema_version':1,'candidate_id':CID,'experiment_id':EXP,'code_commit':CODE,'parent_commit':PARENT,
    'runtime_expected_commit':PARENT,'candidate_source_hashes':candidate_hashes,'candidate_config_sha256':sha(HERE/'candidate.yaml'),
    'source_files':prep['source_files'],'original_source_preparation_sha256':sha(SOURCE/'preparation.json'),
    'source_preparation':ref(SOURCE/'preparation.json'),'native_protocol':ref(SOURCE/'native_protocol.md'),
    'isolated_source_version':ref(proof),'independent_source_review':ref(ROOT/'pipeline/diagnostic_bundles/tick_e666cac0/aoc_source_independent_review.json'),
    'scope':'Actual source0314 childPES9c; primary/runtime currently5c untouched. Prototypef7 NULL/reference5c unchanged. DRAFTTrue and expectedruntime9c refuse now; future PES technical admission and real main/runtime9c required before a separately reviewed operational activation. No sibling fast-forward or old native relabel.'}
save('source_version_binding.json',binding)
template=json.loads((ORIGIN/'manifest_template.json').read_text(encoding='utf-8'))
name=template['name']
template.update(candidate_id=CID,candidate_name=name+'_aoc',experiment_id=EXP,code_commit=CODE,
    config='configs/Quard/ctf_hcg_csort_aoc/'+name+'_aoc.yaml',source_preparation_sha256=sha(SOURCE/'preparation.json'),
    candidate_source_hashes=candidate_hashes,candidate_config_sha256=sha(HERE/'candidate.yaml'),
    scientific_admission=False,draft_execution_disabled=True,base_reference_commit=prep['base_reference_commit'],
    source_version_commit=CODE,source_version_binding_sha256=sha(HERE/'source_version_binding.json'),
    source_parent_commit=PARENT,future_version_parent=PARENT,runtime_expected_commit=PARENT,
    protocol='Original M95/AOC paired naturalTRAIN2 and unchanged resource function. Two actual shared binary-cell/GELU globalcalls each2F rows; second two halves contrast q feeds fine and two directfinepath means, original3LN/3rawskips/HCG/singleinst. Only wholecellweight aggregate original-loss finite/nonzero and real weight/module update. Per-call/branch/row/bias/2column zeros legal; swap/equalancestor/Jacobian no new numerical gate. Current DRAFTTrue; runtime9c requires actual future PES testing/promotion, current5c refused. No native/resources result.')
active=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')
for key in active:template[key]=None
diagnostics={p.relative_to(HERE).as_posix():sha(p) for p in sorted((HERE/'candidate_model').glob('*.py'))}
diagnostics.update({name:sha(HERE/name) for name in ('candidate.yaml','native_runtime.py','worker.py','source_version_binding.json')})
assert len(diagnostics)==12
template['diagnostic_files']=diagnostics
save('manifest_template.json',template)
save('actual_source_binding_provenance.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'code_commit':CODE,'source_parent_commit':PARENT,
    'runtime_expected_commit':PARENT,'primary_current_reference':'5c0c211c8ecc9479ecb34dbb8118a95f4b20e391',
    'source_proof':ref(proof),'original_prototype':ref(SOURCE/'preparation.json'),'draft_execution_disabled':True,
    'initial_draft_preserved':ref(HERE/'initial_draft_scope.json'),'initial_runtime_preserved':ref(HERE/'initial_native_runtime_draft.py.txt'),
    'initial_draft_metadata_correction':'M221-AOC copied declaration corrected to M222-AOC before freeze; initial runtime early-disabled and never executed. No model or protocol change.',
    'manifest_execution_fields':{key:template[key] for key in active},'native':'NOT_RUN','resources':'NOT_RUN',
    'no_active_binding_lease_or_native_manifest_created':True,'no_Git_SSH_GPU_or_shared_operation':True})
print(json.dumps({'source_version_binding':ref(HERE/'source_version_binding.json'),'manifest_template':ref(HERE/'manifest_template.json'),'runtime':ref(HERE/'native_runtime.py')}))
