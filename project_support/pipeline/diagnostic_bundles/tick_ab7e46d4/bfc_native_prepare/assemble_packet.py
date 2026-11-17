"""Local-only immutable disabled-packet assembly; never imports model/Torch."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
TICK = HERE.parent
ORIGIN = PROJECT / 'pipeline/diagnostic_bundles/tick_41eb62fa/bcr_native_prepare'
SOURCE = TICK / 'new_candidate_prepare'
COMMIT = '48fc302c3c02ffef0b241be3593c386b6b65a72e'
PARENT = '11a811618179ab1ddc0cee299194667413b7fdb9'
CID = 'hierarchy-parent-butterfly-token-composition'
EXP = 'M213-BFC'
PREP_SHA = '8512a69de3d5fcdd32523bbf966833485f3e17329235881de7aa0bd5adbe4501'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {'path': path.relative_to(PROJECT).as_posix(), 'sha256': sha(path)}


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


owner = json.loads((PROJECT / 'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf-8'))
fields = ('token', 'thread_id', 'generated_at', 'deadline_at', 'context_sha256', 'pending_sha256')
owner = {key: owner[key] for key in fields}
assert owner['token'] == 'ab7e46d4f6c64d99af3ae07d0f4e5e73'
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
assert sha(SOURCE / 'preparation.json') == PREP_SHA
source = json.loads((SOURCE / 'preparation.json').read_text(encoding='utf-8'))
version_path = TICK / 'isolated_source_version.json'
version = json.loads(version_path.read_text(encoding='utf-8'))
assert version['code_commit'] == COMMIT and version['parent_commit'] == PARENT
assert version['candidate_id'] == CID and len(source['source_files']) == 9
actual_parent = subprocess.check_output(['git', '-C', str(version['worktree']), 'rev-parse', 'HEAD^'], text=True).strip()
actual_commit = subprocess.check_output(['git', '-C', str(version['worktree']), 'rev-parse', 'HEAD'], text=True).strip()
assert (actual_commit, actual_parent) == (COMMIT, PARENT)
candidate = {}
source_files = {}
(HERE / 'candidate_model').mkdir(exist_ok=False)
for item in source['source_files']:
    path = SOURCE / item['prepared_path']
    assert sha(path) == item['sha256'] == version['committed_blob_sha256'][item['path']]
    blob = subprocess.check_output(['git', '-C', str(version['worktree']), 'show', COMMIT + ':' + item['path']])
    assert hashlib.sha256(blob).hexdigest() == item['sha256']
    source_files[item['path']] = item['sha256']
    if item['path'].endswith('.yaml'):
        dest = HERE / 'candidate.yaml'
        config_sha = item['sha256']
    else:
        candidate[path.name] = item['sha256']
        dest = HERE / 'candidate_model' / path.name
        ast.parse(blob.decode('utf-8'))
    with dest.open('xb') as stream:
        stream.write(blob)
assert len(candidate) == 8
binding = {
    'schema_version': 1, 'candidate_id': CID, 'experiment_id': EXP,
    'code_commit': COMMIT, 'parent_commit': PARENT,
    'candidate_source_hashes': candidate, 'candidate_config_sha256': config_sha,
    'source_files': source_files, 'original_source_preparation_sha256': PREP_SHA,
    'isolated_source_version': ref(version_path),
    'verification_scope': 'Actual local isolated Git48fc child11a nine committed blobs equal original frozen8512 source bytes. No primary/remote checkout or model/native execution changed.',
}
save('source_version_binding.json', binding)

readme = '''# Disabled BFC native preparation

This package binds M213-BFC / hierarchy-parent-butterfly-token-composition to actual source48fc302c3c02ffef0b241be3593c386b6b65a72e, single parent11a811618179ab1ddc0cee299194667413b7fdb9. The original source preparation8512 remains immutable and retains its original null commit. Eight model files and original YAML are exact frozen/committed bytes.

Execution is disabled. Both worker and runtime stop with their own error before fcntl, manifest access, NVML, model/Torch imports or CUDA. No execution manifest, lease, active binding, adapter release, receipt, queue entry or operation exists here. The ten manifest execution fields are null. The source commit, preparation timestamps and parent-owner provenance are static history, not authorization or an active lease.

No operational adapter is created this round. Any future operational promotion requires a separately reviewed copied package, new hashes/maps/metadata and an actual fresh owner/context/pending/deadline/manifest/lease. The narrow permitted source transformation, if root explicitly chooses it later, is exactly DRAFT_EXECUTION_DISABLED = True to False in the new runtime copy; origin bytes and refusal evidence stay immutable. The candidate source commit, original8512 source hash and every remaining runtime guard stay unchanged. Any different source change needs review. Recompute runtime hash, diagnostic map, template hash, prepared map, preparation hash and external anchoring in that order; do not create self-hash cycles. Promotion is not scientific admission or hardware availability.

A future selected physical device must be one currently authorized GPU0 or GPU1 with the matching exact UUID, fresh live idle observations on only that device, and all three selected training/diagnostic/exclusive flocks. A future stage is bfc_<fresh token8>_gpu<selected physical index>. CUDA_VISIBLE_DEVICES exposes that one UUID and the worker continues to use logical CUDA0. The source48fc and future actual runtime checkout commit are distinct bindings; no sync/reset/checkout is performed. Current BTC0 and BCR1 are protected and busy; this package claims no available card. Paused M206 remains paused.

The worker retains original YAML, seed1999, original backbone pretrain, native two TRAIN batches, one original loss backward and optimizer step per batch; no auxiliary forward/replay/backward, changed samples, dtype or threshold. Candidate-only hooks capture actual production plans, shared Linear/GELU calls and original outputs, both old-state pair halves, simultaneous output scatter/carry, native four W quadrant gradients and actual slice updates, original cf skip/LN, fine/coarse FFNs, raw CSORT and HCG-to-inst path. Coverage requires the original batches themselves to exercise n>=3, a nonpower-of-two supported parent and multiple stages; missing coverage is INCONCLUSIVE with no resampling. Per-call gradient zeros are allowed; aggregate four block gradients/updates and finite recorded output-half loss gradients are checked. Individual half gradients may be zero; no same-call simultaneous nonzero requirement is added. Own state is included; no self-exclusive, mean conservation, bias-neutrality or efficacy claim is made.

The resource function is whole-AST identical to the reviewed original BCR function: original fvcore handlers, bs1/lang1/warmup20/repeat100, median/P90, allocated/reserved peaks, and unsupported operators preserved. Resource runs do not install smoke hooks. Actual resource values and original <=10G / memory condition are unmeasured. Smoke memory includes observer CPU copies/references and is not pure TRAIN memory.

Author-local AST/compile, pure production-plan and list callback stand-ins, and two actual stdlib disabled-entry refusals are preparation checks only. They are not Torch/Tensor/GELU/FP32/autograd/native, independent packet review, resource PASS or model efficacy evidence. The prior pre-binding worker and12-check proof remain preserved; the final version-bound proof records14 logical checks. Future actual common initialized named-parameter fingerprints exclude only original middle FFN and new butterfly prefixes, retain middle LN, and must be compared across actual targets; full buffers/RNG/common state were not recorded here. Empty/padding/singleton and actual gradients remain UNKNOWN until native evidence exists.
'''
with (HERE / 'README.md').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(readme)

template = json.loads((ORIGIN / 'manifest_template.json').read_text(encoding='utf-8'))
template.update(candidate_id=CID, experiment_id=EXP,
    candidate_name=source['model_name'], config=source['config'], code_commit=COMMIT,
    source_parent_commit=PARENT, source_preparation_sha256=PREP_SHA,
    source_version_commit=COMMIT, source_version_binding_sha256=sha(HERE / 'source_version_binding.json'),
    candidate_source_hashes=candidate, candidate_config_sha256=config_sha,
    draft_execution_disabled=True,
    protocol='Version-bound disabled BFC preparation only. Original TRAIN2 and original resources are NOT_RUN. Future selected authorized physical0or1 requires a separately reviewed operational copy and fresh current owner, actual selected-card idle, assets, three flocks, manifest and lease. No adapter is included.')
active_fields = ('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')
for field in active_fields:
    template[field] = None
diagnostic = {name: sha(HERE / name) for name in ('native_runtime.py','worker.py','candidate.yaml','source_version_binding.json')}
diagnostic.update({'candidate_model/' + name: digest for name, digest in candidate.items()})
assert len(diagnostic) == 12
template['diagnostic_files'] = diagnostic
save('manifest_template.json', template)
prepared = dict(diagnostic)
prepared.update({name: sha(HERE / name) for name in ('README.md','manifest_template.json')})
assert len(prepared) == 14
proof = HERE / 'static_validation_final.json'
validation = json.loads(proof.read_text(encoding='utf-8'))
assert validation['source_hashes'] == {n: sha(HERE/n) for n in ('worker.py','native_runtime.py')}
save('preparation.json', {
    'schema_version': 1, 'recorded_at': datetime.now(timezone.utc).isoformat(),
    'status': 'SOURCE_VERSION_BOUND_DISABLED_NATIVE_PREPARATION_NOT_RUN',
    'candidate_id': CID, 'experiment_id': EXP, 'code_commit': COMMIT, 'source_commit': COMMIT,
    'source_parent_commit': PARENT, 'source_preparation_sha256': PREP_SHA,
    'draft_execution_disabled': True, 'prepared_file_hashes': prepared,
    'manifest_execution_fields': {field: None for field in active_fields},
    'prepared_under_parent': owner,
    'provenance_scope': 'Preparation owner and time are historical only, not active binding, resource grant or reusable lease.',
    'native': 'NOT_RUN', 'resources': 'NOT_RUN', 'transport': 'NOT_RUN',
    'scientific_admission': False, 'active_manifest_lease_binding_created': False,
    'static_validation': ref(proof), 'offline_check_source': ref(HERE / 'static_check.py'),
    'assembly_source': ref(Path(__file__)),
    'original_native_reference': ref(ORIGIN / 'preparation.json'),
    'source_preparation': ref(SOURCE / 'preparation.json'),
    'native_protocol': ref(SOURCE / 'native_protocol.md'),
    'source_integration_review': ref(TICK / 'bfc_integration_review.json'),
    'source_topology_independent_review': ref(TICK / 'bfc_topology_review.json'),
    'preserved_prebinding_evidence': {
        'worker_snapshot': ref(HERE / 'worker_before_empty_coverage_guard.py.txt'),
        'static_validation': ref(HERE / 'static_validation.json'),
        'version_bound_pre_half_zero_protocol_validation': ref(HERE / 'static_validation_version_bound.json'),
        'pre_half_zero_protocol_worker': ref(HERE / 'worker_before_half_zero_protocol_guard.py.txt'),
        'change_scope': 'Observer only: classify absent/all-empty required coverage before gradient-watch, make quadrant names exactly match native protocol, and remove an extra per-call simultaneous-half nonzero gate (individual zero halves remain valid; the four aggregate W quadrant gates remain). No frozen model source change.',
    },
    'limitations': [
        'Author checks are not independent packet review or actual Torch/Tensor/autograd/FP32/native evidence.',
        'Historical assets are static bindings, not current remote or hardware checks. Future original inputs, common initialization, coverage, gradients and resources are UNKNOWN.',
        'Resource function and native training entry are retained; actual original budget and memory condition must be evaluated from real paired results. Observer smoke memory is not pure TRAIN.',
        'No operational adapter, release, binding, lease, manifest, resource availability or scientific admission is created or claimed.',
    ],
})
print(json.dumps({'preparation': ref(HERE/'preparation.json'), 'worker_sha256': sha(HERE/'worker.py'),
    'runtime_sha256': sha(HERE/'native_runtime.py'), 'template_sha256': sha(HERE/'manifest_template.json'),
    'source_version_binding_sha256': sha(HERE/'source_version_binding.json'), 'prepared_files': len(prepared),
    'diagnostic_files': len(diagnostic), 'native': 'NOT_RUN', 'draft_execution_disabled': True}))
