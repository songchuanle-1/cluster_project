"""Local AST/hash-only binding preparation; never imports packet or queries resources."""
from datetime import datetime, timezone
import ast
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path('D:/project/cluster_project')
BASE = ROOT / 'pipeline/diagnostic_bundles'
OLD = BASE / 'tick_7caf419d/cso_native_bound'
PREPARE = BASE / 'tick_2020a21f/cso_native_prepare'
HERE = Path(__file__).resolve().parent
NEW = HERE / 'cso_native_bound'
OWNER_KEYS = ('token', 'thread_id', 'generated_at', 'deadline_at', 'context_sha256', 'pending_sha256')
TOKEN = 'c1fe217800894083b65baac45f79aa83'
AUTHOR = '/root/cso_native_ops'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    with Path(path).open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


assert sys.dont_write_bytecode and os.environ['PYTHONDONTWRITEBYTECODE'] == '1'
assert os.environ['GIT_OPTIONAL_LOCKS'] == '0'
owner_full = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
OWNER = {key: owner_full[key] for key in OWNER_KEYS}
assert OWNER['token'] == TOKEN and OWNER['thread_id'] == '01a159c5-29ab-7a22-ba7f-e79174757253'
assert OWNER['deadline_at'] == '2026-11-14T02:52:47.538159+00:00'
for name, key in (('.tick_context.json', 'context_sha256'), ('.tick_context_state.next.json', 'pending_sha256')):
    assert sha(ROOT / 'pipeline/headless' / name) == OWNER[key]
assert read(ROOT / 'pipeline/execution_mode.json')['target_thread_id'] == OWNER['thread_id']
original = read(OLD / 'FROZEN.json')
prior_owner = original['owner']
assert sha(OLD / 'FROZEN.json') == '3d326e818a2d7691516c6279695fe7bbe08a78bd476400afd612ebcc87ee8474'
assert all(sha(OLD / name) == expected for name, expected in original['files'].items())
assert all(sha(ROOT / item['path']) == item['sha256'] for item in original['anchors'].values())
guard_path = BASE / 'tick_7caf419d/cso_ops_source_draft/direct_memory_free_guard.py'
guard_review = BASE / 'tick_4a0ed3c1/peer_review/guard_source_independent_review.json'
assert sha(guard_path) == '1d48570e42ee34e012194ccf412e475a12608396f946e0eac27902907006c111'
assert read(guard_review)['passed'] is True and read(guard_review)['guard_sha256'] == sha(guard_path)
assert not (NEW / 'FROZEN.json').exists() and not (HERE / 'cso_native_execution').exists(), 'Never overwrite frozen or executed binding'
NEW.mkdir(exist_ok=True)
for name in original['files']:
    path = NEW / name
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(OLD / name, path)
shutil.copyfile(guard_path, NEW / guard_path.name)
stage_old = '/data/songcl/Project/Cluster_project/pipeline/cso_7caf419d_gpu0'
stage_new = '/data/songcl/Project/Cluster_project/pipeline/cso_c1fe2178_gpu0'


def rewrite(name, text):
    (NEW / name).write_text(text, encoding='utf8', newline='\n')


def rebind_text(text):
    for key in OWNER_KEYS:
        text = text.replace(prior_owner[key], OWNER[key])
    return text.replace(stage_old, stage_new)


transport_original = (OLD / 'run_native_once.py').read_text()
transport = rebind_text(transport_original)
transport = transport.replace('"/root/sinc_prod")', '"/root/sinc_prod", "/root/cso_native_ops")')
transport = transport.replace('    assert review["source_and_native_protocol_review_passed"] is True\n',
    '    assert review["source_and_native_protocol_review_passed"] is True\n'
    '    assert review["direct_memory_free_guard_integration_review_passed"] is True\n')
rewrite('run_native_once.py', transport)
runtime_original = (OLD / 'native_runtime.py').read_text()
runtime = rebind_text(runtime_original)
runtime = runtime.replace('import subprocess\n', 'import subprocess\nfrom direct_memory_free_guard import require_direct_free_memory\n', 1)
start = runtime.index('    row = subprocess.check_output(["nvidia-smi", "-i", "0",', runtime.index('def observe('))
end = runtime.index('    contexts = subprocess.check_output(', start)
runtime = runtime[:start] + '''    if require_usable:
        measured = require_direct_free_memory()
        free, used, total, utilization = (measured[key] for key in
            ("memory_free_mib", "memory_used_mib", "memory_total_mib", "utilization_percent"))
        row = ", ".join(map(str, (0, GPU_UUID, free, used, total, utilization)))
    else:
        row = subprocess.check_output(["/usr/bin/nvidia-smi", "-i", "0",
            "--query-gpu=index,uuid,memory.free,memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader,nounits"], text=True, timeout=10).strip()
        fields = [part.strip() for part in row.split(",")]
        assert len(fields) == 6 and fields[:2] == ["0", GPU_UUID]
        free, used, total, utilization = map(int, fields[2:])
    assert 0 <= used <= total and free >= 0
''' + runtime[end:]
runtime = runtime.replace('    free = total - used\n', '')
runtime = runtime.replace('            "memory_free_mib": free, "utilization_percent": utilization,\n',
    '            "memory_free_mib": free, "utilization_percent": utilization,\n'
    '            "memory_free_queried_directly": True,\n')
runtime = runtime.replace('        verify()\n        os.environ.update(',
    '        verify()\n'
    '        # Recheck directly after source/asset verification, while all three original locks remain held.\n'
    '        before["last_pre_Torch_observation"] = observe(True)\n'
    '        os.environ.update(', 1)
rewrite('native_runtime.py', runtime)

for name in ('environment_binding.json', 'source_version.json', 'source_binding.template.json', 'manifest_template.json',
             'execution_lease.template.json', 'peer_review_request.json'):
    obj = read(NEW / name)
    assert obj['owner'] == prior_owner
    obj['owner'] = copy.deepcopy(OWNER)
    if name == 'source_version.json':
        obj['previous_tick7caf_execution_binding'] = {'path': str((OLD / name).relative_to(ROOT)).replace('\\', '/'),
            'sha256': sha(OLD / name), 'owner_preserved': prior_owner}
    if name == 'environment_binding.json':
        obj['previous_tick7caf_execution_binding'] = {'path': str((OLD / name).relative_to(ROOT)).replace('\\', '/'),
            'sha256': sha(OLD / name), 'owner_preserved': prior_owner}
    if name == 'manifest_template.json':
        obj['stage'] = stage_new
    if name == 'peer_review_request.json':
        obj['request'] = ('Current-owner/private-stage rebind of reviewed CSO native packet plus exact historical direct-free '
            'helper integration into pre-Torch guards. Worker/source9/YAML/resources protocol byte-exact. '
            'Native BOOTSTRAP conservative one-shot attempt position preserved. Root alone executes after distinct current '
            'caller integration review and current resource checks; actual native/resources NOT_RUN.')
        obj['required_review_fields'].append('direct_memory_free_guard_integration_review_passed')
    (NEW / name).unlink()
    save(NEW / name, obj)

source_hash = sha(NEW / 'source_version.json')
binding = read(NEW / 'source_binding.template.json')
binding['source_snapshot_sha256'] = source_hash
(NEW / 'source_binding.template.json').unlink()
save(NEW / 'source_binding.template.json', binding)
manifest = read(NEW / 'manifest_template.json')
manifest['source_snapshot_sha256'] = source_hash
manifest['environment_binding_sha256'] = sha(NEW / 'environment_binding.json')
manifest['diagnostic_files']['direct_memory_free_guard.py'] = sha(NEW / 'direct_memory_free_guard.py')
for name in manifest['diagnostic_files']:
    manifest['diagnostic_files'][name] = sha(NEW / name)
(NEW / 'manifest_template.json').unlink()
save(NEW / 'manifest_template.json', manifest)

version = read(NEW / 'source_version.json')
assert version['source_files_exact9'] == binding['source_files']
proof = read(NEW / 'historical_cso_commit_proof.json')
assert proof['commit'] == version['source_commit'] == 'af45707d7b6089f764843337c5f88af285383f88'
assert version['source_parent_commit'] == 'd21477b0d85e6ddcef428ea98ddf6b86fcc38f7e'
assert version['runtime_original_parent_commit'] == manifest['runtime_code_commit'] == 'b1e639b3ceb14bb5c65d9f81a084d41c834b951c'
source_tree = Path(version['source_worktree'])
git_env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
def git_bytes(*args):
    return subprocess.check_output(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-c', 'safe.directory=' + str(source_tree).replace('\\', '/'), '-C', str(source_tree), *args],
                                   env=git_env, timeout=20)
assert git_bytes('rev-parse', version['source_commit'] + '^').decode().strip() == version['source_parent_commit']
for source_name, expected in version['source_files_exact9'].items():
    raw = git_bytes('show', version['source_commit'] + ':' + source_name)
    assert hashlib.sha256(raw).hexdigest() == expected
    packet_name = 'candidate.yaml' if source_name.endswith('.yaml') else 'candidate_model/' + Path(source_name).name
    assert (NEW / packet_name).read_bytes() == raw
immutable_names = ['worker.py', 'candidate.yaml', 'protocol_validation.json', 'historical_cso_commit_proof.json',
                   'historical_sinc_source_version.json'] + ['candidate_model/' + name for name in manifest['candidate_source_hashes']]
assert all((NEW / name).read_bytes() == (OLD / name).read_bytes() for name in immutable_names)
assert (NEW / 'worker.py').read_bytes() == (PREPARE / 'worker.py').read_bytes()
assert (NEW / 'direct_memory_free_guard.py').read_bytes() == guard_path.read_bytes()

def ast_function(text, name):
    tree = ast.parse(text)
    return next(node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)
worker = (NEW / 'worker.py').read_text()
resources = ast_function(worker, 'resources')
resources_bytes = ast.get_source_segment(worker, resources).encode()
old_resources = ast_function((OLD / 'worker.py').read_text(), 'resources')
assert resources_bytes == ast.get_source_segment((OLD / 'worker.py').read_text(), old_resources).encode()
runtime_tree = ast.parse(runtime)
transport_tree = ast.parse(transport)
for path in NEW.rglob('*.py'):
    compile(path.read_bytes(), str(path), 'exec')
old_bootstrap = next(ast.literal_eval(node.value) for node in ast.parse(transport_original).body
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'BOOTSTRAP' for t in node.targets))
new_bootstrap = next(ast.literal_eval(node.value) for node in transport_tree.body
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'BOOTSTRAP' for t in node.targets))
assert new_bootstrap == rebind_text(old_bootstrap)
compile(new_bootstrap, 'BOOTSTRAP', 'exec')
assert 'total - used' not in runtime
assert runtime.count('observe(True)') == 3
assert runtime.index('before["last_pre_Torch_observation"] = observe(True)') > runtime.index('        verify()')
assert manifest['resource_memory_policy'] == read(OLD / 'manifest_template.json')['resource_memory_policy']
assert manifest['assets'] == read(OLD / 'manifest_template.json')['assets']

anchors = copy.deepcopy(original['anchors'])
for name, path in {
    'reviewed_tick7caf_native_binding': OLD / 'FROZEN.json',
    'reviewed_tick7caf_native_binding_review': BASE / 'tick_7caf419d/peer_review/cso_native_bound_independent_review.json',
    'historical_direct_free_guard': guard_path,
    'historical_direct_free_guard_static_review': guard_review,
    'retained_integration_commit_proof': BASE / 'tick_7caf419d/cso_integration_commit/commit_proof.json',
    'retained_integration_independent_review': BASE / 'tick_7caf419d/peer_review/cso_integration_independent_review.json',
}.items():
    anchors[name] = {'path': str(path.relative_to(ROOT)).replace('\\', '/'), 'sha256': sha(path)}
integration = read(ROOT / anchors['retained_integration_commit_proof']['path'])
assert integration['commit'] == '5413102c57b526035f3920b5e7a81f3b58ad764d'
assert integration['files_exact9_sha256'] == version['source_files_exact9']
now = datetime.now(timezone.utc).isoformat()
validation = {
    'owner': OWNER, 'recorded_at': now, 'author_thread_id': AUTHOR,
    'scope': 'Current owner/stage/lease templates and direct memory.free pre-Torch runtime integration only',
    'prior_FROZEN': anchors['reviewed_tick7caf_native_binding'],
    'worker_source9_native_yaml_historical_protocol_byte_exact': True,
    'worker_exact_to_tick2020_prepare': True,
    'native_resources_function_source_byte_exact': True,
    'native_resources_function_source_sha256': hashlib.sha256(resources_bytes).hexdigest(),
    'direct_free_helper_byte_exact_to_independently_reviewed_source': True,
    'direct_free_guard_sha256': sha(NEW / 'direct_memory_free_guard.py'),
    'runtime_observe_true_direct_free_checked_before_locks_after_locks_and_after_verify_before_Torch': True,
    'runtime_observe_false_direct_memory_free_observation_without_postrun_threshold': True,
    'no_total_minus_used_memory_gate': True,
    'BOOTSTRAP_byte_exact_except_owner_token_and_new_stage': True,
    'BOOTSTRAP_conservative_one_shot_attempt_position_unchanged': True,
    'production_marker_protocol_not_claimed': True,
    'cap1_original_three_lock_paths_device66308_inodes92537152_92537153_92537154_retained': True,
    'resource_policy_and_assets_unchanged': True,
    'only_GPU0_UUID': manifest['gpu_uuid'],
    'external_overlay_allowed_no_idle_or_utilization_gate': True,
    'expected_source_commit': version['source_commit'], 'source_parent': version['source_parent_commit'],
    'runtime_expected_HEAD': manifest['runtime_code_commit'], 'runtime_root': manifest['root'],
    'private_stage': stage_new, 'retained_integration_commit_not_recreated': integration['commit'],
    'producer_hashes': {n: sha(NEW / n) for n in ('worker.py', 'native_runtime.py', 'run_native_once.py', 'direct_memory_free_guard.py')},
    'source9_verified_against_retained_git_objects_read_only': True,
    'old_packet_and_anchors_hash_verified_unchanged': True,
    'AST_and_compile_only_no_prepared_import_or_execution': True,
    'remote_stage_or_producer_observed_by_author': False,
    'draft_lease_not_sent_or_used': True, 'no_old_lease_renewal_or_replay': True,
    'SSH_Torch_GPU_or_shared_mutation': False, 'CPU_tests': 'NOT_RERUN',
    'native_TRAIN2': 'NOT_RUN', 'resources': 'NOT_RUN', 'scientific_admission': False,
}
(NEW / 'rebind_validation.json').unlink()
save(NEW / 'rebind_validation.json', validation)
for name in ('native_runtime.py', 'run_native_once.py'):
    diff = ''.join(difflib.unified_diff((OLD / name).read_text().splitlines(True),
        (NEW / name).read_text().splitlines(True), fromfile='tick_7caf419d/' + name, tofile='tick_c1fe2178/' + name))
    rewrite(name + '.diff', diff)
rewrite('README.md', '''# Current-owner CSO native packet

Prepared under the current six-field foreground owner for root execution only after a distinct current caller-integration review. No SSH, Torch, resource query or GPU/native execution was performed by the packet author. Historical source, CPU and protocol evidence retain their original owners; old tick7caf stage/lease/attempts must never be renewed, rewritten or replayed.

Worker, eight model source files, native YAML, data/seed1999/epochs50/max_iters70, loss, optimizer, common841 and nine-core update checks, and the original resources function remain byte-exact. Native source af45707d on d214 is privately loaded over unchanged runtime b1e639b3. Retained integration5413102c remains separate and was not recreated or deployed.

Runtime observe(True) calls the byte-exact reviewed direct-free helper before locks, after the three original inode locks, and again after source/asset verification immediately before permitting Torch. It requires physical GPU0 UUID GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c with directly queried memory.free >=20000 MiB. Postrun observe(False) directly records memory.free without imposing that prelaunch threshold on the worker's own allocated memory. Overlay remains allowed; no idle/utilization gate is added. Native BOOTSTRAP conservatively consumes its one-shot attempt before worker guards, as in the reviewed protocol; a refusal is terminal and must not be replayed. Production marker integration is outside this packet.

The default packet entry is NOP. Actual source_binding/native_manifest/execution_lease are created exclusively by the reviewed root transport upon explicit --execute-root. The draft template is never an actual lease. Current root must independently verify server identity, runtime/environment/source/assets/producer, cap1 and three original locks, and preserve every existing external context without signals. Actual TRAIN2/resources and trained efficacy remain unmeasured.
''')
frozen = {
    'owner': OWNER, 'recorded_at': now, 'author_thread_id': AUTHOR,
    'status': 'CURRENT_OWNER_DIRECT_MEMORY_FREE_CALLER_PREPARED_NOT_RUN_AWAITING_DISTINCT_REVIEW_AND_ROOT_EXECUTION',
    'author_executed': False, 'source_commit': version['source_commit'],
    'source_parent_commit': version['source_parent_commit'], 'runtime_expected_HEAD': manifest['runtime_code_commit'],
    'private_stage_only_no_runtime_sync': True, 'source_version_sha256': source_hash,
    'native_TRAIN2': 'NOT_RUN', 'resources': 'NOT_RUN', 'scientific_admission': False,
    'files': {str(p.relative_to(NEW)).replace('\\', '/'): sha(p) for p in sorted(NEW.rglob('*')) if p.is_file() and p.name != 'FROZEN.json'},
    'anchors': anchors,
}
save(NEW / 'FROZEN.json', frozen)
assert all(sha(OLD / name) == expected for name, expected in original['files'].items())
assert all(sha(ROOT / item['path']) == item['sha256'] for item in frozen['anchors'].values())
assert all(sha(NEW / name) == expected for name, expected in frozen['files'].items())
assert not (HERE / 'cso_native_execution').exists()
print(json.dumps({'packet': str(NEW), 'FROZEN_sha256': sha(NEW / 'FROZEN.json'),
    'source_version_sha256': source_hash, 'validation_sha256': sha(NEW / 'rebind_validation.json'),
    'producer_hashes': validation['producer_hashes'], 'actual_native_or_resources': 'NOT_RUN'}, indent=2))
