"""Local-only CTS version binding. This program never invokes Git or transport."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
NATIVE = HERE / 'native'
ORIGINAL = ROOT / 'pipeline/diagnostic_bundles/tick_4694ba96/cts_native_prepare'
REFERENCE = ROOT / 'pipeline/diagnostic_bundles/tick_64ac844e/bfc_operational_prepare'
SOURCE = ROOT / 'pipeline/diagnostic_bundles/tick_3824d9c9/new_candidate_prepare'
VERSION = ROOT / 'pipeline/diagnostic_bundles/tick_336ca5d7/cts_version_execute/isolated_source_version.json'
VERSION_REVIEW = ROOT / 'pipeline/diagnostic_bundles/tick_336ca5d7/cts_isolated_source_version_review.json'
CID = 'hierarchy-parent-cyclic-triadic-state-composition'
COMMIT = '4e80006047d5cb3dcdfb9c1102e02c33f354a07d'
PARENT = '48fc302c3c02ffef0b241be3593c386b6b65a72e'
SOURCE_SHA = 'bfab01a31a0fc7a0d679156d5e0e6fcfa987e56e5f3bb1bdf6bded9e2208f76e'
VERSION_SHA = '6b666a8c8e9d0f5bed8422fa02e6e2ea17192b1114c6eda5ecf28affb409c2d0'
VERSION_REVIEW_SHA = '5f3eb45ef1672730a18cf1d211837e1bc06e47f5c0010dd550f55227ac59de87'
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


assert sha(ORIGINAL/'preparation.json') == 'ff7fb7a65999369f277744828598822883a222a10ce1ef02732aafeb561fb2cf'
assert sha(ORIGINAL/'worker.py') == '03329ec50fba63d67330342052ec34262f772aee6cc16d3d8d2978d58628c27c'
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
assert owner['token'] == '6bdbcf775b4b4239933ce966f98664d2'
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
             runtime_expected_commit=PARENT, verification_scope='Version binding to existing actual isolated CTS4e8 child48fc and exact frozenbfab nine blobs, supported by original6b666 source-version result and independent5f3 review. This assembly performs no Git, remote operation or model run.')
assert proof['original_source_preparation_sha256'] == SOURCE_SHA
save(NATIVE/'source_version_binding.json', proof)
text(NATIVE/'README.md', '''# CTS native version-bound private copy

This copy binds the existing actual isolated CTS4e8 single child of48fc. Original bfab source preparation and ff7 disabled/unversioned native preparation remain immutable. The original CTS worker03329, all eight model files and native YAML are copied byte for byte. No native model, TRAIN, resource profile, Git, SSH or GPU was run by this assembly.

Only this runtime copy is capability-enabled, binds candidate4e8/source-parent48fc and requires the live runtime checkout to remain48fc. Its original seven guard/function bodies remain unchanged. Before torch/model/data/CUDA import, the future worker still requires exact current-owner manifest/lease, original deadline, selected physical0or1/UUID, live whitelist, two idle observations, all three selected-card flock handles and exact assets/source hashes. Visible physical selection maps to logicalcuda0; worker.cuda() and logical index0 are unchanged.

The manifest template has ten execution fields null. No native_manifest.json, execution_lease.json, execution_binding.json, adapter_release.json or transport is created here. Static version/source evidence is historical provenance, not a lease, idle proof or GPU grant. Future original two TRAIN batches must actually establish common initialization/input pairing, true three-distinct source IDs and multi-round/dilation coverage, and all three aggregate W input-column original-loss gradients/updates. Individual call/row zeros are legal. Missing required coverage is INCONCLUSIVE; no resampling or threshold/dtype change.

The original resource function/handlers/bs1/lang1/warmup20/repeat100 are unchanged. Unsupported operators must be disclosed from actual runs. Smoke peaks include observers/reference snapshots and are not pure TRAIN memory; pure TRAIN and efficacy remain UNKNOWN. This package creates no admission, receipt, queue entry, source promotion, scheduler action or scientific PASS.
''')
manifest = read(ORIGINAL/'manifest_template.json')
manifest.update(code_commit=COMMIT, source_version_commit=COMMIT, source_parent_commit=PARENT,
                future_version_parent=PARENT, runtime_expected_commit=PARENT,
                source_version_binding_sha256=sha(NATIVE/'source_version_binding.json'),
                draft_execution_disabled=False,
                protocol='Version-bound CTS private operational capability only. Original TRAIN2/resources NOT_RUN. Future exact current owner/context/deadline, live runtime48fc, selected authorized idle physical0or1, three locks, assets and fresh manifest/lease are mandatory. Static provenance is not an execution grant.')
assert all(manifest[k] is None for k in ACTIVE)
manifest['diagnostic_files'] = {n:sha(NATIVE/n) for n in manifest['diagnostic_files']}
save(NATIVE/'manifest_template.json', manifest)
native_map = dict(manifest['diagnostic_files'])
native_map.update({'README.md':sha(NATIVE/'README.md'),'manifest_template.json':sha(NATIVE/'manifest_template.json')})
native_prep = {'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'status':'VERSION_BOUND_CTS_NATIVE_PREPARATION_REQUIRES_FRESH_OWNER_IDLE_AND_LEASE',
    'candidate_id':CID,'experiment_id':'M214-CTS','code_commit':COMMIT,'source_commit':COMMIT,
    'source_parent_commit':PARENT,'runtime_expected_commit':PARENT,'source_preparation_sha256':SOURCE_SHA,
    'source_preparation':ref(SOURCE/'preparation.json'),'native_protocol':ref(SOURCE/'native_protocol.md'),
    'original_native_preparation':ref(ORIGINAL/'preparation.json'),'original_native_independent_review':ref(ROOT/'pipeline/diagnostic_bundles/tick_4694ba96/cts_native_preparation_independent_review_v2.json'),
    'isolated_source_version':ref(VERSION),'isolated_source_version_independent_review':ref(VERSION_REVIEW),
    'draft_execution_disabled':False,'prepared_file_hashes':native_map,
    'manifest_execution_fields':{k:None for k in ACTIVE},'prepared_under_parent':prepared_owner,
    'provenance_scope':'Historical preparation owner only; future current owner is dynamically revalidated. No active execution binding or hardware claim.',
    'native':'NOT_RUN','resources':'NOT_RUN','transport':'NOT_RUN','scientific_admission':False,
    'active_manifest_lease_binding_created':False,
    'runtime_declared_ordered_text_transformations':runtime_changes,
    'limitations':['The enabled private runtime is not runnable without the independently reviewed adapter, external root anchors, current authorized idle resources and fresh manifest/lease.','Actual coverage, three W block original-loss gradients/updates, common pairing, numerical/resource/efficacy results remain unmeasured.','Author local tests are mocked/static only; no Torch/model, Git, transport or GPU use occurred.']}
save(NATIVE/'preparation.json', native_prep)

translations = [
    ('hierarchy-parent-butterfly-token-composition', CID), ('M213-BFC','M214-CTS'),
    ('BFC','CTS'), ('bfc','cts'),
    ('tick_64ac844e/cts_operational_prepare/native','tick_6bdbcf77/cts_operational_prepare/native'),
    ('0c50b957129c44367d63ade6984d997fa1e0a22c59469a2355542095d0f25cf5',sha(NATIVE/'preparation.json')),
    ('4d9caaab1e857fda73e9c2ef863ec815c2a81f26f128d614cb1368826e21ddb5',sha(NATIVE/'manifest_template.json')),
    (PARENT,COMMIT),
]
for name in ['adapter.py','remote_ops.py']:
    value = (REFERENCE/name).read_text(encoding='utf-8')
    for before, after in translations: value=value.replace(before, after)
    if name == 'adapter.py':
        marker="COMMIT = '"+COMMIT+"'"
        assert value.count(marker)==1
        value=value.replace(marker,marker+"\nRUNTIME_EXPECTED_COMMIT = '"+PARENT+"'",1)
        marker="        require(re.fullmatch(r'[0-9a-f]{40}',observation.get('runtime_code_commit','')) is not None,'Runtime HEAD unknown')"
        assert value.count(marker)==1
        value=value.replace(marker,marker+"\n        require(observation['runtime_code_commit']==RUNTIME_EXPECTED_COMMIT,'Live runtime checkout is not the required tested48fc parent; no sync or fallback')",1)
    text(HERE/name,value)
save(HERE/'native_promotion.json',{'schema_version':1,'original_native_preparation':ref(ORIGINAL/'preparation.json'),
     'promoted_native_preparation':ref(NATIVE/'preparation.json'),'runtime_declared_ordered_text_transformations':runtime_changes,
     'worker_original_sha256':sha(ORIGINAL/'worker.py'),'worker_copy_sha256':sha(NATIVE/'worker.py'),
     'source_version_proof':ref(VERSION),'source_version_review':ref(VERSION_REVIEW),
     'native_resources_transport':'NOT_RUN','active_material_created':False})
save(HERE/'port_provenance.json',{'schema_version':1,'reference_package':ref(REFERENCE/'preparation.json'),
    'reference_sources':{n:ref(REFERENCE/n) for n in ['adapter.py','remote_ops.py']},
    'declared_ordered_text_transformations':translations,
    'additional_adapter_source_changes':["RUNTIME_EXPECTED_COMMIT='48fc...' global",'Exact required live runtime48fc assertion added to _check_probe; no source sync/fallback'],
    'source_parent_runtime_scope':'CTS candidate4e8, isolated parent48fc and live runtime_expected48fc are distinct explicit fields. Source save and prepared capability do not promote runtime.',
    'raw_UUID_interface':'Adapter reads actual SERVERS.yaml raw expected_gpu_uuids; no normalized pipeline monitor dictionary is substituted. Original strict physical index/UUID checks and SSH hostname pinning remain.',
    'guard_scope':'Every other adapter/remote function is an exact namespace/metadata translation; current-owner deadline/context, whitelist, registered busy, uncertain/replay/read-only old-binding boundaries remain unchanged.',
    'actual_operations':'NOT_RUN'})
release=read(REFERENCE/'release_template.json')
release.update(candidate_id=CID,experiment_id='M214-CTS',code_commit=COMMIT,
               native_preparation_sha256=sha(NATIVE/'preparation.json'),manifest_template_sha256=sha(NATIVE/'manifest_template.json'),
               source_version_binding_sha256=sha(NATIVE/'source_version_binding.json'),
               source_hashes={n:sha(HERE/n) for n in ['adapter.py','remote_ops.py']})
save(HERE/'release_template.json',release)
print(json.dumps({'native_preparation_sha256':sha(NATIVE/'preparation.json'),'manifest_template_sha256':sha(NATIVE/'manifest_template.json'),'adapter_sha256':sha(HERE/'adapter.py'),'remote_sha256':sha(HERE/'remote_ops.py'),'release_template_sha256':sha(HERE/'release_template.json'),'actual_operations':'NOT_RUN'}))
