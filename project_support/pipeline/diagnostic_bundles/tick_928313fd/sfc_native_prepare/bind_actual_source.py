"""Private actual-source conditional binding only; no native/runtime entry execution."""
from pathlib import Path
from datetime import datetime,timezone
import difflib,hashlib,json,shutil
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_9169196d/new_candidate_prepare'
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_89d05b33/fcb_native_prepare'
CODE='c9be548699cd66bf68badff9ae6198a03eafa142'
PARENT='d4d062ef075abfe7cde93d4b4347ce146572762f'
CID='hierarchy-synchronous-full-neighbor-composition'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(name,value):(HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
proof=HERE.parent/'sfc_version_prepare/isolated_source_version.json';peer=HERE.parent/'sfc_actual_source_version_independent_review.json'
assert sha(proof)=='79e3f7b00f2fe5dfd852ee57165e1a574dee65523632d3c0656c501836abadf0'
assert sha(peer)=='d1dbc9dfb4afb0bdaf4bf7a9301b617c1f029bd431349c71859b937adc74172e'
version=json.loads(proof.read_text(encoding='utf-8'));source=json.loads((SOURCE/'preparation.json').read_text(encoding='utf-8'))
assert version['code_commit']==CODE and version['parent_commit']==PARENT and version['frozen_source_files']==version['committed_blob_sha256']==source['source_files']
assert all(source[k] is None for k in ('code_commit','source_commit','source_parent_commit'))
snapshot=HERE/'unversioned_disabled_wip';snapshot.mkdir(exist_ok=False)
for name in ('worker.py','native_runtime.py','draft_scope.json'):shutil.copyfile(HERE/name,snapshot/name)
before=(HERE/'native_runtime.py').read_text(encoding='utf-8')
assert before.count('DRAFT_EXECUTION_DISABLED = True')==1 and before.count('CANDIDATE_COMMIT = None')==1 and before.count('SOURCE_PARENT_COMMIT = None')==1
after=before.replace('DRAFT_EXECUTION_DISABLED = True','DRAFT_EXECUTION_DISABLED = False').replace('CANDIDATE_COMMIT = None',f'CANDIDATE_COMMIT = {CODE!r}').replace('SOURCE_PARENT_COMMIT = None',f'SOURCE_PARENT_COMMIT = {PARENT!r}')
(HERE/'native_runtime.py').write_text(after,encoding='utf-8',newline='\n')
hashes={p.name:sha(p) for p in sorted((HERE/'candidate_model').glob('*.py'))}
binding={'schema_version':1,'candidate_id':CID,'experiment_id':'M224-SFC','code_commit':CODE,'parent_commit':PARENT,'runtime_expected_commit':PARENT,
    'candidate_source_hashes':hashes,'candidate_config_sha256':sha(HERE/'candidate.yaml'),'source_files':source['source_files'],
    'original_source_preparation_sha256':sha(SOURCE/'preparation.json'),'source_preparation':ref(SOURCE/'preparation.json'),
    'native_protocol':ref(SOURCE/'native_protocol.md'),'isolated_source_version':ref(proof),'isolated_source_version_independent_review':ref(peer),
    'independent_source_review':ref(ROOT/'pipeline/diagnostic_bundles/tick_9169196d/sfc_source_independent_review.json'),
    'scope':'Actual isolated SFCc9be54 singlechildFCBd4d062, conditional runtime d4d. Currentmain/runtimeAOC0314 is untouched/ineligible; cumulative0314-to-SFC18A is not an exact9A fast-forward. Future fresh binding requires genuineFCB technical receipt and actualmain/runtime d4d, not FCB training completion or efficacy. If FCB is not promoted or main changes, preserve this packet and save/test genuinely compatible source. Prototype963dc NULL/ref0314/21map/negative history unchanged.'}
save('source_version_binding.json',binding)
template=json.loads((ORIGIN/'manifest_template.json').read_text(encoding='utf-8'));base=template['name']
template.update(candidate_id=CID,candidate_name=base+'_sfc',experiment_id='M224-SFC',code_commit=CODE,
    config='configs/Quard/ctf_hcg_csort_sfc/'+base+'_sfc.yaml',scientific_admission=False,draft_execution_disabled=False,
    candidate_source_hashes=hashes,candidate_config_sha256=sha(HERE/'candidate.yaml'),source_preparation_sha256=sha(SOURCE/'preparation.json'),
    base_reference_commit=source['base_reference_commit'],source_version_commit=CODE,source_version_binding_sha256=sha(HERE/'source_version_binding.json'),
    source_parent_commit=PARENT,future_version_parent=PARENT,runtime_expected_commit=PARENT,
    protocol='Original M95/SFC naturalTRAIN2 and full original resource function. Original3LN h0, true forest plan/twoBFS diameter, per-round sameOLDstate full-neighbor degree mean/sharedcell/GELU/oneactualfunctionalindexcopy; D2 components stop before D4, hD direct3delta/3rawskip/HCG/singleinst. Capture actual original operators once and return real objects, no mean/cell/GELU/gather/indexcopy/model/criterion replay. Wholecore original-loss finite/nonzero weight aggregate and real weight/module update only; round/node/column/bias0 legal, no D4/multicomponent/FP32/Jacobian/convergence gate. Version-bound DRAFTFalse+10activeNULL, missingmanifest beforeTorch; future actualruntime d4d/genuineFCB technical receipt/freshowner/physical0/idle/3locks required, current0314 ineligible. Native/resourcesNOT_RUN.')
active=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')
for key in active:template[key]=None
diagnostic={p.relative_to(HERE).as_posix():sha(p) for p in sorted((HERE/'candidate_model').glob('*.py'))}
diagnostic.update({name:sha(HERE/name) for name in ('candidate.yaml','worker.py','native_runtime.py','source_version_binding.json')})
assert len(diagnostic)==12;template['diagnostic_files']=diagnostic;save('manifest_template.json',template)
save('binding_provenance.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'source_proof':ref(proof),'actual_source_peer':ref(peer),
    'original_NULL_source_preparation':ref(SOURCE/'preparation.json'),'unversioned_disabled_snapshot':{p.name:ref(p) for p in snapshot.iterdir()},
    'runtime_exact_diff':''.join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='unversioned_disabled_wip/native_runtime.py',tofile='native_runtime.py')),
    'runtime_functions_changed_by_binding':False,'worker_changed_by_binding':False,'formal_draft_execution_disabled':False,
    'all_ten_active_fields_NULL':all(template[k] is None for k in active),'currentmain_runtime':'AOC0314, no FCB parent technical promotion claimed',
    'native':'NOT_RUN','resources':'NOT_RUN','no_Git_SSH_GPU_Torch_or_shared_operation':True})
print(json.dumps({'runtime':ref(HERE/'native_runtime.py'),'binding':ref(HERE/'source_version_binding.json'),'template':ref(HERE/'manifest_template.json')}))
