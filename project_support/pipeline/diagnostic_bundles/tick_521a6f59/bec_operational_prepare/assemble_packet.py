"""Local-only BEC version binding. This program never invokes Git or transport."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
NATIVE = HERE / 'native'
ORIGINAL = ROOT / 'pipeline/diagnostic_bundles/tick_f86d1cfa/bec_native_prepare'
REFERENCE = ROOT / 'pipeline/diagnostic_bundles/tick_6bdbcf77/cts_operational_prepare'
SOURCE = ROOT / 'pipeline/diagnostic_bundles/tick_6bdbcf77/new_candidate_prepare'
VERSION = ROOT / 'pipeline/diagnostic_bundles/tick_b5dc39b4/bec_version_execute/isolated_source_version.json'
VERSION_REVIEW = ROOT / 'pipeline/diagnostic_bundles/tick_b5dc39b4/bec_isolated_source_version_review.json'
CID = 'hierarchy-cross-level-bipartite-edge-composition'
COMMIT = '9b6782f44ca7f2c8ac35baea01dfd070314b5701'
PARENT = '48fc302c3c02ffef0b241be3593c386b6b65a72e'
SOURCE_SHA = '2d0606030583fd29719a39a114e11c1c31f44b63ca0fa2cff849baf40e7ca14d'
VERSION_SHA = 'e2f3439ead898c3f8acdc8d54d929720515aa5783650850ae2c8d20666c30f44'
VERSION_REVIEW_SHA = 'cb7ec9d87a8fabdc32a51ebdbc593557f42afd331a96c3d4cddc3cc7aa7dfd61'
ACTIVE = ('current_token', 'stage', 'tick_generated_at', 'deadline_at', 'physical_gpu',
          'gpu_uuid', 'allowed_gpus', 'context_sha256', 'pending_sha256', 'runtime_code_commit')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def ref(path): return {'path': Path(path).relative_to(ROOT).as_posix(), 'sha256': sha(path)}
def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
def text(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(value)


assert sha(ORIGINAL/'preparation.json') == '322c8ce812ffccda6cfa3d6d2d6e1dd8f73859ab5d3a9835d0c1110328c3e3ff'
assert sha(ORIGINAL/'worker.py') == '7e5d0f5b109e85d0d2f0bb7f2f806dd9db73fb7885add5abc372ce244ee753e3'
assert sha(SOURCE/'preparation.json') == SOURCE_SHA
assert sha(VERSION) == VERSION_SHA and sha(VERSION_REVIEW) == VERSION_REVIEW_SHA
version = read(VERSION)
assert version['candidate_id'] == CID and version['code_commit'] == COMMIT and version['parent_commit'] == PARENT
assert version['frozen_source_files'] == version['committed_blob_sha256'] and len(version['frozen_source_files']) == 9
review = read(VERSION_REVIEW)
assert review['material_concerns'] == []
source = read(SOURCE/'preparation.json')
assert all(source[k] is None for k in ('code_commit', 'source_commit', 'future_version_parent'))
owner = read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
prepared_owner = {k: owner[k] for k in ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')}
assert owner['token'] == '521a6f59f2a74a69b41144aa6a8b6153'
NATIVE.mkdir(exist_ok=False)
(NATIVE/'candidate_model').mkdir()
for name in ['worker.py','candidate.yaml']:
    (NATIVE/name).write_bytes((ORIGINAL/name).read_bytes())
for name in read(ORIGINAL/'manifest_template.json')['candidate_source_hashes']:
    (NATIVE/'candidate_model'/name).write_bytes((ORIGINAL/'candidate_model'/name).read_bytes())

runtime = (ORIGINAL/'native_runtime.py').read_text(encoding='utf-8')
runtime_changes = [
    ('DRAFT_EXECUTION_DISABLED = True', 'DRAFT_EXECUTION_DISABLED = False'),
    ('CANDIDATE_COMMIT = None', 'CANDIDATE_COMMIT = '+repr(COMMIT)),
    ('SOURCE_PARENT_COMMIT = None', 'SOURCE_PARENT_COMMIT = '+repr(PARENT)),
    ("SOURCE_PREPARATION_SHA256 = '"+SOURCE_SHA+"'", "SOURCE_PREPARATION_SHA256 = '"+SOURCE_SHA+"'\nRUNTIME_EXPECTED_COMMIT = "+repr(PARENT)),
    ("assert MANIFEST['code_commit'] == CANDIDATE_COMMIT", "assert MANIFEST['code_commit'] == CANDIDATE_COMMIT\nassert MANIFEST['runtime_code_commit'] == RUNTIME_EXPECTED_COMMIT"),
]
for before, after in runtime_changes:
    assert runtime.count(before) == 1
    runtime = runtime.replace(before, after, 1)
text(NATIVE/'native_runtime.py', runtime)
proof = read(ORIGINAL/'source_version_binding.json')
proof.update(code_commit=COMMIT, parent_commit=PARENT, future_version_parent=PARENT, source_files=version['committed_blob_sha256'],
             isolated_source_version=ref(VERSION), isolated_source_version_independent_review=ref(VERSION_REVIEW),
             runtime_expected_commit=PARENT, verification_scope='Version binding to existing actual isolated BEC9b67 child48fc and exact frozen2d06 nine blobs, supported by originale2f3 source-version result and independentcb7 review. This assembly performs no Git, remote operation or model run.')
assert proof['original_source_preparation_sha256'] == SOURCE_SHA
save(NATIVE/'source_version_binding.json', proof)
text(NATIVE/'README.md', '''# BEC native version-bound private copy

This copy binds the existing actual isolated BEC9b67 single child of48fc. Original2d06 source preparation and322c disabled/unversioned native preparation remain immutable. The original BEC worker7e5, all eight model files and native YAML are copied byte for byte. No native model, TRAIN, resource profile, Git, SSH or GPU was run by this assembly.

Only this runtime copy is capability-enabled, binds candidate9b67/source-parent48fc and requires the live runtime checkout to remain48fc. Its original seven guard/function bodies remain unchanged. Before torch/model/data/CUDA import, the future worker still requires exact current-owner manifest/lease, original deadline, selected physical0or1/UUID, live whitelist, two idle observations, all three selected-card flock handles and exact assets/source hashes. Visible physical selection maps to logicalcuda0; worker.cuda() and logical index0 are unchanged.

The manifest template has ten execution fields null. No native_manifest.json, execution_lease.json, execution_binding.json, adapter_release.json or transport is created here. Static version/source evidence is historical provenance, not a lease, idle proof or GPU grant. Future original two TRAIN batches must actually establish common initialization/input pairing, true three-distinct source IDs and multi-round/dilation coverage, and all three aggregate W input-column original-loss gradients/updates. Individual call/row zeros are legal. Missing required coverage is INCONCLUSIVE; no resampling or threshold/dtype change.

The original resource function/handlers/bs1/lang1/warmup20/repeat100 are unchanged. Unsupported operators must be disclosed from actual runs. Smoke peaks include observers/reference snapshots and are not pure TRAIN memory; pure TRAIN and efficacy remain UNKNOWN. This package creates no admission, receipt, queue entry, source promotion, scheduler action or scientific PASS.
''')
manifest = read(ORIGINAL/'manifest_template.json')
manifest.update(code_commit=COMMIT, source_version_commit=COMMIT, source_parent_commit=PARENT,
                future_version_parent=PARENT, runtime_expected_commit=PARENT,
                source_version_binding_sha256=sha(NATIVE/'source_version_binding.json'),
                draft_execution_disabled=False,
                protocol='Version-bound BEC private operational capability only. Original TRAIN2/resources NOT_RUN. Future exact current owner/context/deadline, live runtime48fc, selected authorized idle physical0or1, three locks, assets and fresh manifest/lease are mandatory. Static provenance is not an execution grant.')
assert all(manifest[k] is None for k in ACTIVE)
manifest['diagnostic_files'] = {n:sha(NATIVE/n) for n in manifest['diagnostic_files']}
save(NATIVE/'manifest_template.json', manifest)
native_map = dict(manifest['diagnostic_files'])
native_map.update({'README.md':sha(NATIVE/'README.md'),'manifest_template.json':sha(NATIVE/'manifest_template.json')})
native_prep = {'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'status':'VERSION_BOUND_BEC_NATIVE_PREPARATION_REQUIRES_FRESH_OWNER_IDLE_AND_LEASE',
    'candidate_id':CID,'experiment_id':'M215-BEC','code_commit':COMMIT,'source_commit':COMMIT,
    'source_parent_commit':PARENT,'runtime_expected_commit':PARENT,'source_preparation_sha256':SOURCE_SHA,
    'source_preparation':ref(SOURCE/'preparation.json'),'native_protocol':ref(SOURCE/'native_protocol.md'),
    'original_native_preparation':ref(ORIGINAL/'preparation.json'),'original_native_independent_review':ref(ROOT/'pipeline/diagnostic_bundles/tick_f86d1cfa/bec_native_preparation_final_review.json'),
    'isolated_source_version':ref(VERSION),'isolated_source_version_independent_review':ref(VERSION_REVIEW),
    'draft_execution_disabled':False,'prepared_file_hashes':native_map,
    'manifest_execution_fields':{k:None for k in ACTIVE},'prepared_under_parent':prepared_owner,
    'provenance_scope':'Historical preparation owner only; future current owner is dynamically revalidated. No active execution binding or hardware claim.',
    'native':'NOT_RUN','resources':'NOT_RUN','transport':'NOT_RUN','scientific_admission':False,
    'active_manifest_lease_binding_created':False,
    'runtime_declared_ordered_text_transformations':runtime_changes,
    'limitations':['The enabled private runtime is not runnable without the independently reviewed adapter, external root anchors, current authorized idle resources and fresh manifest/lease.','Actual coverage, twelve W block original-loss gradients/updates, common pairing, numerical/resource/efficacy results remain unmeasured.','Author local tests are mocked/static only; no Torch/model, Git, transport or GPU use occurred.']}
save(NATIVE/'preparation.json', native_prep)

translations = [
    ('hierarchy-parent-cyclic-triadic-state-composition', CID), ('M214-CTS','M215-BEC'),
    ('CTS','BEC'), ('cts','bec'),
    ('tick_6bdbcf77/bec_operational_prepare/native','tick_521a6f59/bec_operational_prepare/native'),
    ('aab40a87e8fcdff7b92cdd95ceb07340d81f8e9acb71ec101e100d9ac42edfc4',sha(NATIVE/'preparation.json')),
    ('9d6125187ccec3378d372c3952705cc8190cd855e5beb223d1300c82a6b9ef5d',sha(NATIVE/'manifest_template.json')),
    ('4e80006047d5cb3dcdfb9c1102e02c33f354a07d',COMMIT),
]
for name in ['adapter.py','remote_ops.py']:
    value = (REFERENCE/name).read_text(encoding='utf-8')
    for before, after in translations: value=value.replace(before, after)
    text(HERE/name,value)
save(HERE/'native_promotion.json',{'schema_version':1,'original_native_preparation':ref(ORIGINAL/'preparation.json'),
     'promoted_native_preparation':ref(NATIVE/'preparation.json'),'runtime_declared_ordered_text_transformations':runtime_changes,
     'worker_original_sha256':sha(ORIGINAL/'worker.py'),'worker_copy_sha256':sha(NATIVE/'worker.py'),
     'source_version_proof':ref(VERSION),'source_version_review':ref(VERSION_REVIEW),
     'native_resources_transport':'NOT_RUN','active_material_created':False})
save(HERE/'port_provenance.json',{'schema_version':1,'reference_package':ref(REFERENCE/'preparation.json'),
    'reference_sources':{n:ref(REFERENCE/n) for n in ['adapter.py','remote_ops.py']},
    'declared_ordered_text_transformations':translations,
    'additional_adapter_source_changes':[],
    'source_parent_runtime_scope':'BEC candidate9b67, isolated parent48fc and live runtime_expected48fc are distinct explicit fields. Source save and prepared capability do not promote runtime.',
    'raw_UUID_interface':'Adapter reads actual SERVERS.yaml raw expected_gpu_uuids; no normalized pipeline monitor dictionary is substituted. Original strict physical index/UUID checks and SSH hostname pinning remain.',
    'guard_scope':'Every other adapter/remote function is an exact namespace/metadata translation; current-owner deadline/context, whitelist, registered busy, uncertain/replay/read-only old-binding boundaries remain unchanged.',
    'actual_operations':'NOT_RUN'})
release=read(REFERENCE/'release_template.json')
release.update(candidate_id=CID,experiment_id='M215-BEC',code_commit=COMMIT,
               native_preparation_sha256=sha(NATIVE/'preparation.json'),manifest_template_sha256=sha(NATIVE/'manifest_template.json'),
               source_version_binding_sha256=sha(NATIVE/'source_version_binding.json'),
               source_hashes={n:sha(HERE/n) for n in ['adapter.py','remote_ops.py']})
save(HERE/'release_template.json',release)
print(json.dumps({'native_preparation_sha256':sha(NATIVE/'preparation.json'),'manifest_template_sha256':sha(NATIVE/'manifest_template.json'),'adapter_sha256':sha(HERE/'adapter.py'),'remote_sha256':sha(HERE/'remote_ops.py'),'release_template_sha256':sha(HERE/'release_template.json'),'actual_operations':'NOT_RUN'}))
