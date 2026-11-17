"""Local schema correction and read-only self-check; never runs the publication generator."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TICK = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def save(name, value):
    with (HERE / name).open('x', encoding='utf8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


v1 = HERE / 'generate_version_binding.py'
assert sha(v1) == '4ca3209184c9efbba14b4ced40f2bfb80eb1a6894607a1f6ef9034e821f3ea63'
body = v1.read_text(encoding='utf8')
old = "    for key in ('batches', 'losses', 'steps', 'core_calls', 'raw_bank_observations', 'inst_to_mask_path_observations'):\n"
new = """    comparator_path = ROOT / 'pipeline/diagnostic_bundles/tick_71e15360/nde_execution/smoke_champion_execution.json'
    require(ref(comparator_path)['sha256'] == 'adb5f2659a34b6c7622f20155fc4ff41fda08383df8c2b0c653ccb509b474a7b', 'Retained M95 natural TRAIN observation changed')
    require(len(r['batches']) == 2 and r['batches'] == read(comparator_path)['result']['batches'], 'Natural batch hashes/metadata differ from original M95')
    for key in ('losses', 'steps', 'core_calls', 'raw_bank_observations', 'inst_to_mask_path_observations'):
"""
assert body.count(old) == 1
body = body.replace(old, new)
old_inputs = "                   EXECUTION / 'source_binding.json', EXECUTION / 'native_manifest.json', proof_path, review_path]"
new_inputs = "                   EXECUTION / 'source_binding.json', EXECUTION / 'native_manifest.json', proof_path, review_path,\n                   ROOT / 'pipeline/diagnostic_bundles/tick_71e15360/nde_execution/smoke_champion_execution.json']"
assert body.count(old_inputs) == 1
body = body.replace(old_inputs, new_inputs)
body = body.replace("default=TICK / 'peer_review/cso_version_binding_prepare_independent_review.json'", "default=TICK / 'peer_review/cso_version_binding_v2_prepare_independent_review.json'")
v2 = HERE / 'generate_version_binding_v2.py'
ast.parse(body)
with v2.open('x', encoding='utf8', newline='\n') as stream:
    stream.write(body)
owner = read(TICK / 'current_owner_binding.json')
smoke_path = TICK / 'cso_native_execution/run_smoke_candidate_actual.json'
resource_path = TICK / 'cso_native_execution/run_resources_candidate_actual.json'
smoke = read(smoke_path)['observation']['result']
resources = read(resource_path)['observation']['result']
v1_code = runpy.run_path(str(v1), run_name='readonly_v1_check')
try:
    v1_code['check_smoke'](smoke)
except KeyError as error:
    assert str(error) == "'forward'"
    save('generator_v1_failure.actual.json', {
        'owner': owner, 'recorded_at': datetime.now(timezone.utc).isoformat(),
        'kind': 'LOCAL_CHECKER_REPRODUCTION_OF_ROOT_REPORTED_GENERATION_FAILURE',
        'generator': {'path': str(v1), 'sha256': sha(v1)}, 'actual': {'path': str(smoke_path), 'sha256': sha(smoke_path)},
        'error_type': type(error).__name__, 'error': str(error), 'traceback': traceback.format_exc(),
        'root_reported_execute_result': 'FAIL_CLOSED_NO_ADMISSION KeyError:forward; no derived outputs',
        'reproduction_scope': 'Direct check_smoke on immutable saved real actual; no generate/SSH/Torch/model replay',
        'root_execute_returncode_reported': 1, 'scientific_admission': False,
        'derived_outputs_present': [p.name for p in HERE.iterdir() if p.name in ('version_bound_evidence.json', 'native_smoke.version_bound.json', 'resources.version_bound.summary.json')]})
else:
    raise AssertionError('Expected original checker failure was not reproduced')
ns = runpy.run_path(str(v2), run_name='readonly_v2_check')
checks = {}
ns['check_smoke'](smoke)
checks['check_smoke_current_actual_all_native_finite_common841_core9_natural_batches'] = True
ns['check_resources'](resources)
checks['check_resources_current_actual_original_profiler_and_repeats'] = True
bound = TICK / 'cso_native_bound'
execution = TICK / 'cso_native_execution'
frozen, source, manifest, version = [read(p) for p in (bound / 'FROZEN.json', execution / 'source_binding.json', execution / 'native_manifest.json', bound / 'source_version.json')]
protocol_path = TICK / 'peer_review/cso_native_bound_independent_review.json'
ns['current_review'](protocol_path, owner, 'source_and_native_protocol_review_passed')
for mode in ('smoke', 'resources'):
    ns['actual'](mode, owner, manifest, source, frozen, protocol_path)
checks['actual_transport_request_intent_remote_result_source_manifest_worker_runtime_producer_hashes'] = True
for mode, flag in (('smoke', 'native_smoke_passed'), ('resources', 'resource_gate_passed')):
    ns['current_review'](TICK / ('peer_review/cso_native_' + mode + '_actual_independent_review.json') if mode == 'smoke' else TICK / 'peer_review/cso_resources_actual_independent_review.json', owner, flag, smoke_path if mode == 'smoke' else resource_path)
checks['actual_new_independent_reviews_exact_raw_hashes'] = True
assert all(x['owner'] == owner for x in (frozen, source, manifest, version))
assert source['source_version_proof'] == version
assert source['source_commit'] == version['source_commit'] == manifest['code_commit'] == ns['SOURCE']
assert source['source_parent_commit'] == version['source_parent_commit'] == manifest['source_parent_commit'] == ns['SOURCE_PARENT']
assert source['runtime_original_parent_commit'] == version['runtime_original_parent_commit'] == manifest['runtime_code_commit'] == ns['RUNTIME']
assert source['source_version_sha256'] == frozen['source_version_sha256'] == sha(bound / 'source_version.json')
assert manifest['source_binding_sha256'] == sha(execution / 'source_binding.json')
for name, digest in frozen['files'].items():
    assert sha(bound / name) == digest
for item in frozen['anchors'].values():
    assert sha(ROOT / item['path']) == item['sha256']
checks['current_owner6_frozen_files_anchors_source_parent_runtime_and_embedded_version'] = True
proof_path = ROOT / 'pipeline/diagnostic_bundles/tick_7caf419d/cso_integration_commit/commit_proof.json'
proof = read(proof_path)
ns['verify_git'](proof, proof['files_exact9_sha256'])
checks['actual_readonly_git_both_clean_worktrees_parents_exact9_blobs_equal'] = True
assert sha(v1) == '4ca3209184c9efbba14b4ced40f2bfb80eb1a6894607a1f6ef9034e821f3ea63'
assert all(not (HERE / name).exists() for name in ('version_bound_evidence.json', 'native_smoke.version_bound.json', 'resources.version_bound.summary.json'))
checks['v1_unchanged_no_derived_or_admission_output_created'] = True
save('v2_readonly_input_validation.actual.json', {'owner': owner, 'recorded_at': datetime.now(timezone.utc).isoformat(),
     'scope': 'LOCAL_READONLY_SAVED_INPUT_VALIDATION_ONLY_NO_GENERATION_OR_MODEL_REPLAY', 'generator_v2': {'path': str(v2), 'sha256': sha(v2)},
     'v1_sha256_preserved': sha(v1), 'checks': checks, 'generator_preparation_review': 'PENDING_V2_DISTINCT_REVIEW',
     'generation_executed': False, 'SSH': False, 'Torch_imported': False, 'scientific_admission': False})
print(json.dumps({'v2_sha256': sha(v2), 'readonly_input_checks': checks, 'v1_preserved': sha(v1), 'publication_executed': False}))
