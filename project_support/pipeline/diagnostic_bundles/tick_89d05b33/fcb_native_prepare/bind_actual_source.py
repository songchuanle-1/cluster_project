"""Bind only this private conditional FCB packet to real source proof; not execution."""
from pathlib import Path
from datetime import datetime,timezone
import difflib,hashlib,json,shutil
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_f8d84d12/new_candidate_prepare'
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_2ef53d6b/aoc_native_prepare'
CODE='d4d062ef075abfe7cde93d4b4347ce146572762f'
PARENT='0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'
CID='hierarchy-fine-coarse-complete-bipartite-composition'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(name,value):(HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
proof=HERE.parent/'fcb_version_prepare/isolated_source_version.json'
peer=HERE.parent/'fcb_actual_source_version_independent_review.json'
assert sha(proof)=='0a792bff4e64c8bb8feb18f8b6d11a7330ad22b691185b1f6b7eca94d6bbee71'
assert sha(peer)=='408dae944e3e5e7a690d6adf68cf7eac08fecad2e1a24158318890a1a3191bb8'
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
binding={'schema_version':1,'candidate_id':CID,'experiment_id':'M223-FCB','code_commit':CODE,'parent_commit':PARENT,'runtime_expected_commit':PARENT,
    'candidate_source_hashes':hashes,'candidate_config_sha256':sha(HERE/'candidate.yaml'),'source_files':source['source_files'],
    'original_source_preparation_sha256':sha(SOURCE/'preparation.json'),'source_preparation':ref(SOURCE/'preparation.json'),
    'native_protocol':ref(SOURCE/'native_protocol.md'),'isolated_source_version':ref(proof),'isolated_source_version_independent_review':ref(peer),
    'independent_source_review':ref(ROOT/'pipeline/diagnostic_bundles/tick_f8d84d12/fcb_source_independent_review.json'),
    'scope':'Actual isolated FCBd4d062 singlechildAOC0314, conditional runtime0314. Currentmain/runtimePES9c is untouched and ineligible; cumulative9c-to-FCB18A is not an exact9A fast-forward. Future fresh operational binding requires genuine AOC technical receipt and actualmain/runtime0314, not AOC training completion/efficacy. If AOC is not promoted or main changes, preserve this packet and save/test an actually compatible source. Prototype44c63 NULL/ref9c unchanged.'}
save('source_version_binding.json',binding)
template=json.loads((ORIGIN/'manifest_template.json').read_text(encoding='utf-8'))
base=template['name']
template.update(candidate_id=CID,candidate_name=base+'_fcb',experiment_id='M223-FCB',code_commit=CODE,
    config='configs/Quard/ctf_hcg_csort_fcb/'+base+'_fcb.yaml',scientific_admission=False,draft_execution_disabled=False,
    candidate_source_hashes=hashes,candidate_config_sha256=sha(HERE/'candidate.yaml'),source_preparation_sha256=sha(SOURCE/'preparation.json'),
    base_reference_commit=source['base_reference_commit'],source_version_commit=CODE,source_version_binding_sha256=sha(HERE/'source_version_binding.json'),
    source_parent_commit=PARENT,future_version_parent=PARENT,runtime_expected_commit=PARENT,
    protocol='Original M95/FCB naturalTRAIN2 and unchanged resource protocol. Actual scene-local truefine x truecoarse pair-map/GELU q, sameq two marginals, fine_delta originalparent thirdmean, middle-map/GELU, original3LN/3skips/HCG/singleinst. Wholecore weight aggregate finite/nonzero original-loss plus real aggregate weight/module update only; maps/columns/rows/pairs/bias0 legal, no marginal/Jacobian/multiroot/per-scene/latency gate. Version-bound DRAFTFalse but10activeNULL/missingmanifest refuses beforeTorch; future actualruntime0314 and genuineAOC technical promotion/freshowner/lease/physical0/idle/3locks required, current9c ineligible. Native/resourcesNOT_RUN.')
active=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')
for key in active:template[key]=None
diagnostic={p.relative_to(HERE).as_posix():sha(p) for p in sorted((HERE/'candidate_model').glob('*.py'))}
diagnostic.update({name:sha(HERE/name) for name in ('candidate.yaml','worker.py','native_runtime.py','source_version_binding.json')})
assert len(diagnostic)==12;template['diagnostic_files']=diagnostic
save('manifest_template.json',template)
save('binding_provenance.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'source_proof':ref(proof),'actual_source_peer':ref(peer),
    'original_NULL_source_preparation':ref(SOURCE/'preparation.json'),'unversioned_disabled_snapshot':{p.name:ref(p) for p in snapshot.iterdir()},
    'runtime_exact_diff':''.join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='unversioned_disabled_wip/native_runtime.py',tofile='native_runtime.py')),
    'runtime_functions_changed_by_binding':False,'worker_changed_by_binding':False,'formal_draft_execution_disabled':False,
    'all_ten_active_fields_NULL':all(template[k] is None for k in active),'main_runtime_not_promoted':'CurrentPES9c; sourceAOC0314 conditional parent has not been claimed technically promoted.',
    'native':'NOT_RUN','resources':'NOT_RUN','no_Git_SSH_GPU_Torch_or_shared_operation':True})
print(json.dumps({'runtime':ref(HERE/'native_runtime.py'),'binding':ref(HERE/'source_version_binding.json'),'template':ref(HERE/'manifest_template.json')}))
