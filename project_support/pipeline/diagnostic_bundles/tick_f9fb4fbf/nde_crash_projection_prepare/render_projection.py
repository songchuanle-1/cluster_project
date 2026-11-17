"""Default NOP; project existing native bytes and adapter metadata into new views.

No SSH, GPU, prepare/stage/run, source/worker implementation, or old-file edits.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path('D:/project/cluster_project').resolve()
TICK = ROOT / 'pipeline/diagnostic_bundles/tick_f9fb4fbf'
HERE = Path(__file__).resolve().parent
NATIVE = ROOT / 'pipeline/diagnostic_bundles/tick_4fa1481e/nde_revision_native_active'
OPS = TICK / 'nde_operational_active'
OPERATION = TICK / 'nde_crash_probe_operation_instrumented_v2'
TOKEN = 'f9fb4fbf347949f4b1285134263481be'
BOOTSTRAP_SHA = '4d3d8230d09ebf3dbc834a9cb879eb3f5f2df5db9a090dfe85e31f3067494146'


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def assignments(source, values):
    lines = source.splitlines(keepends=True)
    patches = []
    for name, replacement in values.items():
        nodes = [node for node in ast.parse(source).body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == name
                         for target in node.targets)]
        assert len(nodes) == 1, name
        node = nodes[0]
        patches.append((node.lineno - 1, node.end_lineno, name + ' = ' + replacement + '\n'))
    for start, end, replacement in sorted(patches, reverse=True):
        lines[start:end] = [replacement]
    result = ''.join(lines)
    compile(result, '<metadata-constants-only>', 'exec')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-software', action='store_true')
    parser.add_argument('--bootstrap')
    parser.add_argument('--review')
    parser.add_argument('--with-bound-operation', action='store_true')
    args = parser.parse_args()
    if not args.project_software:
        print(json.dumps({'status': 'DEFAULT_NOP_NO_FILES_OR_TRANSPORT'}))
        return
    assert args.bootstrap and args.review and sys.dont_write_bytecode
    own_frozen = read(HERE / 'FROZEN.json')
    assert all(sha(HERE / name) == digest for name, digest in own_frozen['files'].items())
    owner = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    keys = ('token', 'thread_id', 'generated_at', 'deadline_at', 'context_sha256', 'pending_sha256')
    owner = {key: owner[key] for key in keys}
    assert owner['token'] == TOKEN
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    bootstrap, review_path = Path(args.bootstrap).resolve(), Path(args.review).resolve()
    assert bootstrap.is_relative_to(TICK) and review_path.is_relative_to(TICK)
    assert sha(bootstrap) == BOOTSTRAP_SHA
    review = read(review_path)
    assert review.get('passed') is True and review.get('owner') == owner
    assert review.get('bootstrap_sha256') == BOOTSTRAP_SHA and review.get('fault_localization_only') is True
    mother = read(NATIVE / 'FROZEN.json')
    assert sha(NATIVE / 'worker.py') == 'b37fe5cf29ce04b8110752c7321d34b8d1a26218a6d8e02940b5773d9e4d5f72'
    assert sha(NATIVE / 'native_runtime.py') == '348024f11e6a106788840c1359ad8c65363914d1f1882cfe4a5f8d319d5ea1a4'
    assert sha(OPS / 'adapter.py') == 'd2bc21778fb5fed364ceb51802d679982b3fd133ff4f5b90082a05a96e9935bb'
    assert all(sha(NATIVE / name) == digest for name, digest in mother['files'].items())
    view, ops = TICK / 'nde_crash_native_view', TICK / 'nde_crash_operational_active'
    bound_operation = TICK / 'nde_crash_probe_bound_operation'
    assert not view.exists() and not ops.exists()
    if args.with_bound_operation:
        assert not bound_operation.exists()
    view.mkdir()
    # Immutable original payload is reused by hardlink; writable metadata is new.
    for name in mother['files']:
        if name in ('manifest_template.json', 'preparation.json'):
            continue
        destination = view / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.link(NATIVE / name, destination)
    os.link(bootstrap, view / 'crash_probe_bootstrap.py')
    os.link(review_path, view / 'independent_probe_review.json')
    manifest = read(NATIVE / 'manifest_template.json')
    original_files = dict(manifest['diagnostic_files'])
    assert len(original_files) == 14
    manifest['diagnostic_files'] = {
        **original_files, 'crash_probe_bootstrap.py': BOOTSTRAP_SHA,
        'independent_probe_review.json': sha(review_path)}
    write(view / 'manifest_template.json', manifest)
    assert {key: value for key, value in manifest.items() if key != 'diagnostic_files'} == {
        key: value for key, value in read(NATIVE / 'manifest_template.json').items()
        if key != 'diagnostic_files'}
    assert all(sha(view / name) == digest for name, digest in original_files.items())
    projection = {
        'schema_version': 1, 'owner_provenance_only': owner,
        'project': 'cluster_project', 'candidate_id': manifest['candidate_id'],
        'source_commit': manifest['code_commit'],
        'runtime_expected_commit': manifest['runtime_expected_commit'],
        'runtime_root': manifest['root'],
        'producer': 'render_projection.py metadata-only native/adapter view',
        'render_executor_thread_id': os.environ.get('CODEX_THREAD_ID'),
        'original_native_FROZEN': ref(NATIVE / 'FROZEN.json'),
        'bootstrap': ref(bootstrap), 'independent_review': ref(review_path),
        'original14_hashes_exact': True, 'manifest_only_adds_two_entries': True,
        'worker_runtime_model_source_implementation_changed': False,
        'native_or_diagnostic_executed': False}
    write(view / 'projection_validation.json', projection)
    preparation = read(NATIVE / 'preparation.json')
    preparation.update(owner_provenance_only=owner,
                       producer_agent='reused_native_bytes_metadata_projection',
                       render_executor_thread_id=os.environ.get('CODEX_THREAD_ID'),
                       original_native_FROZEN=ref(NATIVE / 'FROZEN.json'),
                       projection=ref(view / 'projection_validation.json'),
                       independent_review='PENDING_PROJECTION_AND_OPERATION_REVIEW')
    names = list(preparation['prepared_file_hashes']) + [
        'crash_probe_bootstrap.py', 'independent_probe_review.json', 'projection_validation.json']
    preparation['prepared_file_hashes'] = {name: sha(view / name) for name in names}
    write(view / 'preparation.json', preparation)
    write(view / 'FROZEN.json', {
        **projection, 'files': {name: sha(view / name) for name in names + ['preparation.json']},
        'draft_execution_disabled': False, 'execution_material_created': False})
    ops.mkdir()
    for name in ('remote_ops.py', 'run_nde_operation.py'):
        with (ops / name).open('xb') as stream:
            stream.write((OPS / name).read_bytes())
    binding = read(OPS / 'current_binding.json')
    binding.update(mother_FROZEN=ref(view / 'FROZEN.json'),
                   mother_native_preparation=ref(view / 'preparation.json'),
                   native_view_projection=ref(view / 'projection_validation.json'),
                   original_native_FROZEN=ref(NATIVE / 'FROZEN.json'))
    write(ops / 'current_binding.json', binding)
    adapter = assignments((OPS / 'adapter.py').read_text(encoding='utf-8'), {
        'FROZEN': 'Path(' + repr(str(view)) + ')',
        'PREPARATION_SHA': repr(sha(view / 'preparation.json')),
        'TEMPLATE_SHA': repr(sha(view / 'manifest_template.json')),
        'CURRENT_BINDING_SHA256': repr(sha(ops / 'current_binding.json'))})
    with (ops / 'adapter.py').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(adapter)
    def methods(source):
        return {(node.name, method.name): ast.dump(method, include_attributes=False)
                for node in ast.parse(source).body if isinstance(node, ast.ClassDef)
                for method in node.body if isinstance(method, ast.FunctionDef)}
    assert methods(adapter) == methods((OPS / 'adapter.py').read_text(encoding='utf-8'))
    release = read(OPS / 'release_template.json')
    release.update(native_preparation_sha256=sha(view / 'preparation.json'),
                   manifest_template_sha256=sha(view / 'manifest_template.json'),
                   current_binding=ref(ops / 'current_binding.json'),
                   source_hashes={name: sha(ops / name) for name in ('adapter.py', 'remote_ops.py')},
                   independent_review='PENDING_PROJECTION_AND_OPERATION_REVIEW')
    write(ops / 'release_template.json', release)
    write(ops / 'software_validation.json', {
        **projection, 'adapter_delta': 'Four top-level metadata assignments only; methods unchanged'})
    ops_names = ['adapter.py', 'remote_ops.py', 'run_nde_operation.py', 'current_binding.json',
                 'release_template.json', 'software_validation.json']
    ops_preparation = read(OPS / 'preparation.json')
    ops_preparation.update(native_preparation=ref(view / 'preparation.json'),
                           prepared_file_hashes={name: sha(ops / name) for name in ops_names},
                           independent_review='PENDING_PROJECTION_AND_OPERATION_REVIEW')
    write(ops / 'preparation.json', ops_preparation)
    write(ops / 'FROZEN.json', {
        **projection, 'files': {name: sha(ops / name) for name in ops_names + ['preparation.json']},
        'adapter_release_created': False, 'execution_material_created': False})
    if args.with_bound_operation:
        command = [sys.executable, '-B', '-X', 'utf8', str(OPERATION / 'render_bound_operation.py'),
                   '--bind-software', '--bootstrap', str(bootstrap),
                   '--preregistration', str(TICK / 'crash_probe_protocol.json'),
                   '--review', str(review_path), '--output', str(bound_operation)]
        process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=15)
        assert process.returncode == 0, (process.stdout, process.stderr)
        source = assignments((bound_operation / 'run_crash_probe_operation.py').read_text(encoding='utf-8'),
                             {'ACTIVE': "TICK / 'nde_crash_operational_active'"})
        (bound_operation / 'run_crash_probe_operation.py').write_text(source, encoding='utf-8', newline='\n')
        operation_release = read(bound_operation / 'release_template.json')
        operation_release['source_hashes']['run_crash_probe_operation.py'] = sha(
            bound_operation / 'run_crash_probe_operation.py')
        (bound_operation / 'release_template.json').write_text(
            json.dumps(operation_release, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        operation_frozen = read(bound_operation / 'FROZEN.json')
        operation_frozen['files'] = {
            name: sha(bound_operation / name) for name in operation_frozen['files']}
        operation_frozen['native_and_adapter_metadata_projection'] = ref(ops / 'FROZEN.json')
        (bound_operation / 'FROZEN.json').write_text(
            json.dumps(operation_frozen, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({
        'status': 'SOFTWARE_PROJECTION_ONLY_RELEASES_ABSENT_NO_SSH',
        'native_view': ref(view / 'FROZEN.json'), 'native_preparation': ref(view / 'preparation.json'),
        'adapter': ref(ops / 'adapter.py'), 'adapter_preparation': ref(ops / 'preparation.json'),
        'adapter_FROZEN': ref(ops / 'FROZEN.json'),
        'operation_FROZEN': ref(bound_operation / 'FROZEN.json') if args.with_bound_operation else None}))


if __name__ == '__main__':
    main()
