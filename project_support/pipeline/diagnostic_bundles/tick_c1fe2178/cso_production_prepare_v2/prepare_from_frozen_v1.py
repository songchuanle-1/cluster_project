"""Local-only new producer namespace and exact Git blob reader correction; never SSH."""
import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
TICK = HERE.parent
ROOT = TICK.parents[2]
OLD = TICK / 'cso_production_prepare'
DETACHED = ROOT / 'pipeline/isolated_versions/m236_cso_integrated_7caf419d'
COMMIT = '5413102c57b526035f3920b5e7a81f3b58ad764d'
CONFIG = 'configs/Quard/ctf_hcg_csort_cso/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cso.yaml'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return {'path': Path(path).resolve().relative_to(ROOT).as_posix(), 'sha256': sha(Path(path).read_bytes())}


def save(name, value):
    with (HERE / name).open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def write_new(name, raw):
    with (HERE / name).open('xb') as stream:
        stream.write(raw)


assert sys.dont_write_bytecode and not sys.flags.optimize
assert not (HERE / 'FROZEN.json').exists()
frozen_path = OLD / 'FROZEN.json'
old_frozen = read(frozen_path)
old_files = {p.name: p.read_bytes() for p in OLD.iterdir() if p.is_file()}
assert sha(old_files['FROZEN.json']) == '319eefb852aa8a9a47dea65fd449ab983dca7f571499d6a5fa0b79139428c213'
assert all(sha(old_files[name]) == digest for name, digest in old_frozen['files'].items())
manifest_old = read(OLD / 'SOURCE_MANIFEST.NOT_EXECUTABLE.json')
owner = manifest_old['owner']
assert owner == read(TICK / 'current_owner_binding.json')
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
collect_path = TICK / 'cso_setup_execution/collect_actual.json'
failed = read(collect_path)
assert sha(collect_path.read_bytes()) == 'cc6df05a874e8a522cea69ed8f5b77e7e4cd4ca3be9d2d7fde86b6cf77248ea3'
assert failed['owner'] == owner and failed['certainty'] == 'terminal' and failed['ssh_returncode'] == 0
assert failed['observation']['returncode'] == 1 and failed['observation']['result'] is None
assert 'assert digest(original)' in failed['observation']['stderr']
sync_path = TICK / 'cso_deployment_execution/sync.actual.json'
assert sha(sync_path.read_bytes()) == 'd04ac71ed5f62a3a65d60b613cdee137476355cc9c2dc4575678a0de61bcdec1'
admission = ROOT / 'pipeline/admissions/M236-CSO.json'
assert sha(admission.read_bytes()) == '07b56b16948f7f7e1a4a0682fd6abc81d3eda586e05ae4424f89d16005d8be09'

rebind = {
    'cso_path_prepare_c1fe2178': 'cso_path_prepare_c1fe2178_v2',
    'cso_path_prod_c1fe2178': 'cso_path_prod_c1fe2178_v2',
    'cso_setup_execution': 'cso_setup_execution_v2',
    'cso_dispatch_execution': 'cso_dispatch_execution_v2',
    'cso_pointer_execution': 'cso_pointer_execution_v2',
}
rebound = {}
for name in manifest_old['files']:
    if name.endswith('.diff'):
        continue
    data = old_files[name]
    if name not in ('lock_core.py', 'entry_factory.py', 'direct_memory_free_guard.py'):
        for before, after in rebind.items():
            data = data.replace(before.encode(), after.encode())
    rebound[name] = data

controller = rebound['production_controller.py']
eol = '\r\n' if b'\r\n' in controller else '\n'
blob_reader = '''def git_blob(relative):
    """Return exact immutable Git blob bytes, preserving CRLF and every source byte."""
    process = subprocess.Popen(
        ["/usr/bin/git", "--no-optional-locks", "-c", "core.fsmonitor=false",
         "-C", str(RUNTIME), "cat-file", "blob", COMMIT + ":" + relative],
        env=GIT_ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        raise RuntimeError("Uncertain raw Git child; preserve PID " + str(process.pid))
    if process.returncode:
        raise RuntimeError("Raw Git blob read failed: " + repr(stderr[-1500:]))
    return stdout


'''.replace('\n', eol).encode()
needle = b'def observe(request):'
assert controller.count(needle) == 1
controller = controller.replace(needle, blob_reader + needle, 1)
old_train = b'git("show", COMMIT + ":tools/train.py").encode("utf-8")'
old_config = b'git("show", COMMIT + ":" + CONFIG).encode("utf-8")'
assert controller.count(old_train) == controller.count(old_config) == 1
controller = controller.replace(old_train, b'git_blob("tools/train.py")').replace(old_config, b'git_blob(CONFIG)')
rebound['production_controller.py'] = controller
for name in ('packet_runtime.py', 'run_setup_once.py'):
    rebound[name] = rebound[name].replace(b'"/root/cso_native_ops")', b'"/root/cso_native_ops", "/root/cso_readiness")')

old_controller_hash = sha(old_files['production_controller.py'])
new_controller_hash = sha(controller)
for name in ('collect_request.draft.json', 'render_request.draft.json', 'independent_review_contract.json'):
    assert old_controller_hash.encode() in rebound[name]
    rebound[name] = rebound[name].replace(old_controller_hash.encode(), new_controller_hash.encode())
for name, data in rebound.items():
    if name.endswith('.py') or name.endswith('.py.txt'):
        ast.parse(data, filename=name)

# Local-only exercise of the exact extracted new raw-reader function against the
# retained real Git objects. No controller module/observe/remote code is executed.
tree = ast.parse(controller)
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'git_blob')
local_env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
def local_popen(argv, **kwargs):
    assert 'text' not in kwargs and 'encoding' not in kwargs
    assert argv[0] == '/usr/bin/git' and argv[-3:-1] == ['cat-file', 'blob']
    argv = ['git', '--no-optional-locks', '-c', 'safe.directory=' + DETACHED.as_posix(),
            '-c', 'core.fsmonitor=false', '-C', str(DETACHED), *argv[-3:]]
    return subprocess.Popen(argv, stdout=kwargs['stdout'], stderr=kwargs['stderr'], env=local_env)
module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
ns = {'subprocess': SimpleNamespace(Popen=local_popen, PIPE=subprocess.PIPE, TimeoutExpired=subprocess.TimeoutExpired),
      'RUNTIME': DETACHED, 'COMMIT': COMMIT, 'GIT_ENV': local_env}
exec(compile(module, 'extracted_raw_git_blob_local_test', 'exec'), ns)
config_blob = ns['git_blob'](CONFIG)
train_blob = ns['git_blob']('tools/train.py')
assert sha(config_blob) == '908bc08a4d78dcc2723588abb7a6e3adeb169a79e788ce74ee5afbd78c991081'
assert sha(train_blob) == '4e870e9d24a184e59878c3bca2d70dfc1cc1c5cc66fe8ce6edf96fa364c10e40'
assert config_blob == (DETACHED / CONFIG).read_bytes() and train_blob == (DETACHED / 'tools/train.py').read_bytes()
assert b'\r\n' in config_blob and len(config_blob) == 2791
normalized = config_blob.decode('utf8').replace('\r\n', '\n').replace('\r', '\n').encode('utf8')
assert sha(normalized) != sha(config_blob)
assert sha(rebound['lock_core.py']) == 'ac2938f3258b2b215e1858f6c255b48f1ca3086c3b572a72a37a212701cb015d'
assert rebound['entry_factory.py'] == old_files['entry_factory.py']
assert rebound['direct_memory_free_guard.py'] == old_files['direct_memory_free_guard.py']
for name in ('collect_request.draft.json', 'render_request.draft.json'):
    request = json.loads(rebound[name])
    assert request['files']['production_controller.py'] == new_controller_hash
    assert request['files']['lock_core.py'] == sha(rebound['lock_core.py'])
    assert request['files']['entry_factory.py'] == sha(rebound['entry_factory.py'])

# The old packet's changed transport/guard identities must be pinned in v2's
# review contract as well as the source manifest and every setup request.
contract = json.loads(rebound['independent_review_contract.json'])
for key, name in (('controller_sha256', 'production_controller.py'), ('transport_sha256', 'run_setup_once.py'),
                  ('resolver_sha256', 'source_resolver.py'), ('guard_sha256', 'packet_runtime.py'),
                  ('receiver_sha256', 'remote_receiver.py.txt'), ('lock_core_sha256', 'lock_core.py')):
    contract['expected_file_hashes'][key] = sha(rebound[name])
rebound['independent_review_contract.json'] = (json.dumps(contract, indent=2) + '\n').encode()
validation = json.loads(rebound['draft_validation.json'])
validation.update(recorded_at=datetime.now(timezone.utc).isoformat(), author_thread_id='/root/cso_readiness')
validation['raw_git_blob_correction'] = {'controller_only_two_blob_identity_reads_are_raw': True,
    'HEAD_query_stays_text': True, 'actual_retained_git_objects_tested_locally': True,
    'original_core_entry_factory_direct_free_bytes_preserved': True, 'model_source_config_or_protocol_changed': False,
    'SSH_GPU_Torch_collect_render_or_training': False}
rebound['draft_validation.json'] = (json.dumps(validation, indent=2) + '\n').encode()
rebound['README.md'] = ('''# CSO production v2: exact Git blob identity

This fresh producer namespace fixes only the raw Git blob identity reader after the preserved v1 terminal collect failure. Scientific source541, original CSO YAML bytes, current native/resource gates, admission07b56, and successful canonical syncd04ac remain unchanged. No source synchronization or model retest is required or performed by this preparation.

The controller now reads the immutable tools/train.py and original YAML blobs using binary cat-file output. HEAD queries retain the original text path. The YAML's CRLF bytes are authenticated before the unchanged semantic YAML adaptation preview. All original host/uid/owner/source/environment/resource/lock/entry/one-shot guards remain. Coreac2938 (including explicit python -B, retained FD inheritance, cap1 and direct memory.free) and entry_factory/direct-free helper are byte-identical to v1.

Remote producer and production directories end in _v2; local setup/dispatch/pointer execution directories also end in _v2. The scoped resolver and exact fixed production shim use the new production directory. This package consumes the same real current cso_deployment_execution/sync.actual.json and must never repeat safe_sync. Old package, remote stage, failed request/intent and actual evidence are retained without replay or cleanup.

The finalizer is default NOP. Root may freeze this new local package against the genuine unchanged M236-CSO admission, then obtain a distinct review of the new FROZEN before any new stage/setup. This preparation has not run stage, collect, render, GPU work, training or queue changes. See failure_provenance.json, raw_git_blob_local_validation.actual.json, and the .diff files against frozen v1.
''').encode()
for name, data in rebound.items():
    write_new(name, data)
changed = []
for name, data in rebound.items():
    if data != old_files.get(name):
        changed.append(name)
        delta = ''.join(difflib.unified_diff(old_files[name].decode().splitlines(keepends=True),
                    data.decode().splitlines(keepends=True), fromfile='frozen_v1/' + name, tofile='fresh_v2/' + name))
        write_new(name + '.diff', delta.encode())
save('failure_provenance.json', {'owner': owner, 'recorded_at': datetime.now(timezone.utc).isoformat(),
    'kind': 'NEW_PRODUCER_ONLY_AFTER_KNOWN_TERMINAL_CPU_COLLECT_FAILURE', 'old_frozen': ref(frozen_path),
    'old_stage_actual': ref(TICK / 'cso_setup_execution/stage_actual.json'), 'old_collect_actual': ref(collect_path),
    'old_collect_intent': ref(TICK / 'cso_setup_execution/collect_intent.json'),
    'old_terminal': {'certainty': 'terminal', 'ssh_returncode': 0, 'controller_returncode': 1, 'result': None,
                     'error': 'Assertion on YAML raw SHA after text universal newline conversion'},
    'old_packet_and_old_stage_requests_intents_evidence_preserved': True,
    'raw_scientific_source': COMMIT, 'same_admission': ref(admission), 'same_successful_sync': ref(sync_path),
    'safe_sync_repeated': False, 'new_setup_or_GPU_training_executed': False, 'scientific_admission_changed': False})
save('raw_git_blob_local_validation.actual.json', {'owner': owner, 'recorded_at': datetime.now(timezone.utc).isoformat(),
    'scope': 'LOCAL_EXTRACTED_RAW_READER_REAL_RETAINED_GIT_OBJECTS_ONLY', 'worktree': str(DETACHED), 'commit': COMMIT,
    'raw_config': {'bytes': len(config_blob), 'CRLF_count': config_blob.count(b'\r\n'), 'sha256': sha(config_blob)},
    'text_universal_newline_reproduction': {'bytes': len(normalized), 'sha256': sha(normalized), 'differs_from_expected_raw': True},
    'raw_train': {'bytes': len(train_blob), 'sha256': sha(train_blob)},
    'exact_new_git_blob_function_tested_with_local_Git_executable_adapter': True,
    'raw_reader_stdout_bytes_no_text_or_encoding_argument': True,
    'core_sha256_preserved': sha(rebound['lock_core.py']), 'entry_factory_sha256_preserved': sha(rebound['entry_factory.py']),
    'AST_compile_all_prepared_sources': True, 'new_namespace': list(rebind.values()), 'changed_files': changed,
    'prepared_controller_observe_or_module_executed': False, 'SSH_Torch_GPU_queue_or_model_source_change': False})
manifest = dict(manifest_old)
manifest.update(author_thread_id='/root/cso_readiness', status='V2_SOURCE_DRAFT_RAW_BLOB_CORRECTION_PENDING_GENUINE_ADMISSION_FREEZE_AND_NEW_DISTINCT_REVIEW')
manifest['anchors'] = list(manifest_old['anchors']) + [ref(frozen_path), ref(collect_path), ref(sync_path)]
manifest['files'] = {p.name: sha(p.read_bytes()) for p in HERE.iterdir() if p.is_file() and p.name not in ('SOURCE_MANIFEST.NOT_EXECUTABLE.json', 'FROZEN.json')}
save('SOURCE_MANIFEST.NOT_EXECUTABLE.json', manifest)
assert all(sha((OLD / name).read_bytes()) == sha(data) for name, data in old_files.items())
assert all(sha((HERE / name).read_bytes()) == digest for name, digest in manifest['files'].items())
print(json.dumps({'status': manifest['status'], 'controller_sha256': new_controller_hash,
    'manifest_sha256': sha((HERE / 'SOURCE_MANIFEST.NOT_EXECUTABLE.json').read_bytes()),
    'core_sha256_preserved': sha(rebound['lock_core.py']), 'old_frozen_preserved': ref(frozen_path),
    'new_FROZEN_exists': (HERE / 'FROZEN.json').exists(), 'new_setup_execution': 'cso_setup_execution_v2'}))
