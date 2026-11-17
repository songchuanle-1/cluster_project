"""Private explicitly authorized version-bound conditional identity, not execution."""
from pathlib import Path
from datetime import datetime,timezone
import difflib,hashlib,json,shutil
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(name,value):(HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
snapshot=HERE/'disabled_wip';snapshot.mkdir(exist_ok=False)
for name in ('native_runtime.py','manifest_template.json','source_version_binding.json','static_validation.json','static_check.py','actual_source_binding_provenance.json'):
    shutil.copyfile(HERE/name,snapshot/name)
before_runtime=(HERE/'native_runtime.py').read_text(encoding='utf-8')
assert before_runtime.count('DRAFT_EXECUTION_DISABLED = True')==1
after_runtime=before_runtime.replace('DRAFT_EXECUTION_DISABLED = True','DRAFT_EXECUTION_DISABLED = False')
(HERE/'native_runtime.py').write_text(after_runtime,encoding='utf-8',newline='\n')
binding=json.loads((HERE/'source_version_binding.json').read_text(encoding='utf-8'))
peer=ROOT/'pipeline/diagnostic_bundles/tick_2ef53d6b/aoc_actual_source_version_independent_review.json'
assert sha(peer)=='c11cccf7d3f98d77ca275845b2ac6346bfa13e39366f164d2453cc705dd5b1fc'
binding['isolated_source_version_independent_review']=ref(peer)
binding['scope']='Actual source0314 childPES9c; primary/runtime currently5c untouched. Prototypef7 NULL/reference5c unchanged. Final version-bound DRAFTFalse still requires absent-currently active manifest/lease plus fresh owner/context/deadline/assets/physical0 UUID/three locks and actual runtime9c. Operational parent-promotion guard requires PES technical admission and actualmain9c; current5c refuses all mutation/transport. If PES is not promoted or main changes, preserve this packet and create/test a genuinely compatible version; no sibling fast-forward or old native relabel.'
save('source_version_binding.json',binding)
template=json.loads((HERE/'manifest_template.json').read_text(encoding='utf-8'))
template['draft_execution_disabled']=False
template['source_version_binding_sha256']=sha(HERE/'source_version_binding.json')
template['protocol']=template['protocol'].replace('Current DRAFTTrue; runtime9c requires actual future PES testing/promotion, current5c refused.','Version-bound DRAFTFalse; absent active manifest/lease refuses before Torch, runtime9c requires actual future PES technical admission/promotion and the operational parent-promotion guard, current5c refused. No PES training completion or efficacy gate.')
template['diagnostic_files']['native_runtime.py']=sha(HERE/'native_runtime.py')
template['diagnostic_files']['source_version_binding.json']=sha(HERE/'source_version_binding.json')
save('manifest_template.json',template)
save('conditional_identity_provenance.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'instruction':'Root explicitly selected final DRAFTFalse version-bound capability along original PES activebinding contract. Private identity assembly only; no entry, Torch, CUDA, transport, lease or GPU action.',
    'initial_disabled_snapshot':{p.name:ref(p) for p in snapshot.iterdir()},
    'runtime_before':ref(snapshot/'native_runtime.py'),'runtime_after':ref(HERE/'native_runtime.py'),
    'exact_runtime_diff':''.join(difflib.unified_diff(before_runtime.splitlines(keepends=True),after_runtime.splitlines(keepends=True),fromfile='disabled_wip/native_runtime.py',tofile='native_runtime.py')),
    'runtime_function_bodies_changed':False,'worker_changed_by_transition':False,
    'manifest_metadata_changes':['draft_execution_disabled True to False','runtime and sourcebinding diagnostic hashes','sourcebinding hash','protocol capability wording'],
    'sourcebinding_changes':['actual source version independent peer c11c added','scope clarifies version-bound capability and parent-promotion guard'],
    'code_commit':binding['code_commit'],'source_parent_commit':binding['parent_commit'],'runtime_expected_commit':binding['runtime_expected_commit'],
    'actual_primary_runtime_reference':'5c0c211c8ecc9479ecb34dbb8118a95f4b20e391','all_ten_execution_fields_remain_null':all(template[k] is None for k in ('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')),
    'native':'NOT_RUN','resources':'NOT_RUN','current_packet_executable_without_active_lease':False})
print(json.dumps({'runtime':ref(HERE/'native_runtime.py'),'template':ref(HERE/'manifest_template.json'),'binding':ref(HERE/'source_version_binding.json')}))
