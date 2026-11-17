"""Default NOP; rebind previously reviewed software bytes to one fresh owner."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

ROOT = Path('D:/project/cluster_project').resolve()
TICK = ROOT / 'pipeline/diagnostic_bundles/tick_2bcb30da'
OLD = ROOT / 'pipeline/diagnostic_bundles/tick_f9fb4fbf'
HERE = Path(__file__).resolve().parent
TOKEN = '2bcb30da1bcc4f67a6193b8413cec6ec'
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


def assignment_values(source, values):
    lines = source.splitlines(keepends=True)
    patches = []
    for name, value in values.items():
        matches = [node for node in ast.parse(source).body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == name
                           for target in node.targets)]
        assert len(matches) == 1
        node = matches[0]
        patches.append((node.lineno - 1, node.end_lineno, name + ' = ' + value + '\n'))
    for start, end, value in sorted(patches, reverse=True):
        lines[start:end] = [value]
    result = ''.join(lines)
    compile(result, '<owner-data-delta-only>', 'exec')
    old_methods = [ast.dump(node, include_attributes=False) for node in ast.walk(ast.parse(source))
                   if isinstance(node, ast.FunctionDef)]
    new_methods = [ast.dump(node, include_attributes=False) for node in ast.walk(ast.parse(result))
                   if isinstance(node, ast.FunctionDef)]
    assert old_methods == new_methods
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rebind-software', action='store_true')
    parser.add_argument('--attestation')
    args = parser.parse_args()
    if not args.rebind_software:
        print(json.dumps({'status': 'DEFAULT_NOP_NO_FILES_OR_TRANSPORT'}))
        return
    assert args.attestation and sys_dont_write_bytecode()
    frozen = read(HERE / 'FROZEN.json')
    assert all(sha(HERE / name) == digest for name, digest in frozen['files'].items())
    owner = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    keys = ('token', 'thread_id', 'generated_at', 'deadline_at', 'context_sha256', 'pending_sha256')
    owner = {key: owner[key] for key in keys}
    assert owner['token'] == TOKEN and datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    attestation_path = Path(args.attestation).resolve()
    assert attestation_path.is_relative_to(TICK)
    attestation = read(attestation_path)
    assert attestation.get('passed') is True and attestation.get('owner') == owner
    assert attestation.get('bootstrap_sha256') == BOOTSTRAP_SHA
    assert attestation.get('fault_localization_only') is True
    protocol_path = TICK / 'crash_probe_protocol.json'
    protocol, original_protocol = read(protocol_path), read(OLD / 'crash_probe_protocol.json')
    assert protocol['owner'] == owner
    assert protocol['frozen_method_provenance'] == ref(OLD / 'crash_probe_protocol.json')
    assert protocol['execution_budget'] == original_protocol['execution_budget']
    assert protocol['kind'] == original_protocol['kind']
    assert protocol['source_commit'] == original_protocol['source_commit']
    assert protocol['runtime_code_commit'] == original_protocol['runtime_code_commit']
    old_native, old_ops, old_operation = (OLD / name for name in (
        'nde_crash_native_view', 'nde_crash_operational_active', 'nde_crash_probe_bound_operation'))
    native, ops, operation = (TICK / name for name in (
        'nde_crash_native_view', 'nde_crash_operational_active', 'nde_crash_probe_bound_operation'))
    assert not any(path.exists() for path in (native, ops, operation))
    mother = read(old_native / 'FROZEN.json')
    assert all(sha(old_native / name) == digest for name, digest in mother['files'].items())
    assert sha(old_native / 'worker.py') == 'b37fe5cf29ce04b8110752c7321d34b8d1a26218a6d8e02940b5773d9e4d5f72'
    assert sha(old_native / 'native_runtime.py') == '348024f11e6a106788840c1359ad8c65363914d1f1882cfe4a5f8d319d5ea1a4'
    assert sha(old_native / 'crash_probe_bootstrap.py') == BOOTSTRAP_SHA
    native.mkdir()
    metadata = {'manifest_template.json', 'preparation.json', 'projection_validation.json',
                'independent_probe_review.json'}
    for name in mother['files']:
        if name in metadata:
            continue
        destination = native / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.link(old_native / name, destination)
    os.link(attestation_path, native / 'independent_probe_review.json')
    manifest = read(old_native / 'manifest_template.json')
    original16 = dict(manifest['diagnostic_files'])
    assert len(original16) == 16
    manifest['diagnostic_files']['independent_probe_review.json'] = sha(attestation_path)
    assert all(sha(native / name) == digest for name, digest in original16.items()
               if name != 'independent_probe_review.json')
    write(native / 'manifest_template.json', manifest)
    projection = {
        'schema_version': 1, 'owner_provenance_only': owner,
        'project': 'cluster_project', 'candidate_id': manifest['candidate_id'],
        'source_commit': manifest['code_commit'], 'runtime_root': manifest['root'],
        'runtime_expected_commit': manifest['runtime_expected_commit'],
        'producer': 'fresh-owner data-only projection of reviewed f9 software',
        'render_executor_thread_id': os.environ.get('CODEX_THREAD_ID'),
        'original_native_FROZEN': ref(old_native / 'FROZEN.json'),
        'current_owner_attestation': ref(attestation_path),
        'current_owner_protocol': ref(protocol_path),
        'frozen_original_method': ref(OLD / 'crash_probe_protocol.json'),
        'original14_and_active_bootstrap_bytes_exact': True,
        'all_source_implementation_logic_unchanged': True,
        'actual_execution': 'NOT_RUN'}
    write(native / 'projection_validation.json', projection)
    prep = read(old_native / 'preparation.json')
    prep.update(owner_provenance_only=owner, projection=ref(native / 'projection_validation.json'),
                original_native_FROZEN=ref(old_native / 'FROZEN.json'),
                render_executor_thread_id=os.environ.get('CODEX_THREAD_ID'),
                independent_review='CURRENT_OWNER_DATA_ATTESTATION_AND_FINAL_ANCHORS_REQUIRED')
    prep['prepared_file_hashes'] = {name: sha(native / name) for name in prep['prepared_file_hashes']}
    write(native / 'preparation.json', prep)
    write(native / 'FROZEN.json', {
        **projection, 'files': {name: sha(native / name) for name in mother['files']},
        'draft_execution_disabled': False, 'execution_material_created': False})
    candidate = next(item for item in read(ROOT / 'pipeline/research_work.json')['candidates']
                     if item.get('id') == manifest['candidate_id'])
    revision_digest = hashlib.sha256(json.dumps(
        candidate['revision_history'][0], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    ops.mkdir()
    for name in ('remote_ops.py', 'run_nde_operation.py'):
        (ops / name).write_bytes((old_ops / name).read_bytes())
    binding = read(old_ops / 'current_binding.json')
    binding.update(owner=owner, mother_FROZEN=ref(native / 'FROZEN.json'),
                   mother_native_preparation=ref(native / 'preparation.json'),
                   native_view_projection=ref(native / 'projection_validation.json'),
                   implementation_revision_registration_sha256=revision_digest,
                   current_owner_attestation=ref(attestation_path))
    write(ops / 'current_binding.json', binding)
    source = assignment_values((old_ops / 'adapter.py').read_text(encoding='utf-8'), {
        'FROZEN': 'Path(' + repr(str(native)) + ')',
        'PREPARATION_SHA': repr(sha(native / 'preparation.json')),
        'TEMPLATE_SHA': repr(sha(native / 'manifest_template.json')),
        'CURRENT_BINDING_SHA256': repr(sha(ops / 'current_binding.json')),
        'IMPLEMENTATION_REVISION_REGISTRATION_SHA256': repr(revision_digest)})
    (ops / 'adapter.py').write_text(source, encoding='utf-8', newline='\n')
    release = read(old_ops / 'release_template.json')
    release.update(execution_owner=owner, current_binding=ref(ops / 'current_binding.json'),
                   native_preparation_sha256=sha(native / 'preparation.json'),
                   manifest_template_sha256=sha(native / 'manifest_template.json'),
                   implementation_revision_registration_sha256=revision_digest,
                   source_hashes={name: sha(ops / name) for name in ('adapter.py', 'remote_ops.py')},
                   independent_review='PENDING_CURRENT_OWNER_FINAL_DATA_REVIEW')
    write(ops / 'release_template.json', release)
    write(ops / 'software_validation.json', {
        **projection, 'adapter_function_AST_exact': True,
        'adapter_delta': 'Five binding/version constants only; historical preregistration owner unchanged'})
    ops_prep = read(old_ops / 'preparation.json')
    ops_prep.update(owner_provenance_only=owner, native_preparation=ref(native / 'preparation.json'),
                    independent_review='PENDING_CURRENT_OWNER_FINAL_DATA_REVIEW')
    ops_prep['prepared_file_hashes'] = {
        name: sha(ops / name) for name in ops_prep['prepared_file_hashes']}
    write(ops / 'preparation.json', ops_prep)
    write(ops / 'FROZEN.json', {
        **projection, 'files': {name: sha(ops / name) for name in
                               list(ops_prep['prepared_file_hashes']) + ['preparation.json']},
        'adapter_release_created': False})
    operation.mkdir()
    for name in ('remote_ops.py', 'run_crash_probe_operation.py'):
        (operation / name).write_bytes((old_operation / name).read_bytes())
    packet = read(old_operation / 'diagnostic_packet.json')
    packet.update(owner=owner, current_owner_attestation=ref(attestation_path),
                  preregistration_protocol=ref(protocol_path))
    packet['additional_diagnostic_files'] = {
        'crash_probe_bootstrap.py': ref(native / 'crash_probe_bootstrap.py'),
        'independent_probe_review.json': ref(attestation_path),
        'crash_probe_protocol.json': ref(protocol_path)}
    packet['new_manifest_entries_required']['independent_probe_review.json'] = sha(attestation_path)
    write(operation / 'diagnostic_packet.json', packet)
    operation_release = read(old_operation / 'release_template.json')
    operation_release['source_hashes'] = {
        name: sha(operation / name) for name in (
            'remote_ops.py', 'run_crash_probe_operation.py', 'diagnostic_packet.json')}
    operation_release['independent_review'] = 'PENDING_CURRENT_OWNER_FINAL_DATA_REVIEW'
    write(operation / 'release_template.json', operation_release)
    write(operation / 'FROZEN.json', {
        **projection, 'files': {name: sha(operation / name) for name in (
            'remote_ops.py', 'run_crash_probe_operation.py',
            'diagnostic_packet.json', 'release_template.json')},
        'operation_release_created': False})
    print(json.dumps({
        'status': 'FRESH_OWNER_DATA_ONLY_SOFTWARE_CREATED_RELEASES_ABSENT',
        'native_preparation': ref(native / 'preparation.json'),
        'adapter_preparation': ref(ops / 'preparation.json'),
        'adapter_FROZEN': ref(ops / 'FROZEN.json'),
        'operation_FROZEN': ref(operation / 'FROZEN.json'),
        'original_special_remote_and_root_bytes_exact': True}))


def sys_dont_write_bytecode():
    import sys
    return sys.dont_write_bytecode


if __name__ == '__main__':
    main()
