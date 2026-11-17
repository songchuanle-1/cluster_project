"""Default NOP; render one fresh, disabled operational copy from real new inputs.

This is software preparation only. It does not import the adapter, acquire a
lease, create a release/request/manifest, connect remotely or execute a worker.
Root must independently review and activate a distinct copy before operations.
"""
import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/project/cluster_project').resolve()
TICK = HERE.parent
OWNER_KEYS = ('token', 'thread_id', 'generated_at', 'deadline_at',
              'context_sha256', 'pending_sha256')
ACTIVE_FIELDS = ('current_token', 'stage', 'tick_generated_at', 'deadline_at',
                 'physical_gpu', 'gpu_uuid', 'allowed_gpus', 'context_sha256',
                 'pending_sha256', 'runtime_code_commit')


def check(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path).resolve()
    check(path.is_relative_to(ROOT), 'Artifact outside cluster_project')
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def dump(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def patch_assignments(source, changes):
    lines = source.splitlines(keepends=True)
    tree = ast.parse(source)
    patches = []
    for name, replacement in changes.items():
        nodes = [node for node in tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == name
                         for target in node.targets)]
        check(len(nodes) == 1, 'Assignment missing/ambiguous: ' + name)
        node = nodes[0]
        patches.append((node.lineno - 1, node.end_lineno,
                        name + ' = ' + replacement + '\n'))
    for start, end, replacement in sorted(patches, reverse=True):
        lines[start:end] = [replacement]
    result = ''.join(lines)
    compile(result, '<rendered-software-only>', 'exec')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-disabled', action='store_true')
    parser.add_argument('--native-dir')
    parser.add_argument('--source-review')
    parser.add_argument('--output')
    args = parser.parse_args()
    if not args.render_disabled:
        print(json.dumps({'status': 'DEFAULT_NOP_NO_FILES_OR_TRANSPORT',
                          'native': 'NOT_RUN', 'resources': 'NOT_RUN'}))
        return
    check(args.native_dir and args.source_review and args.output,
          'Real new native directory, source review and absent output required')
    inputs = read(HERE / 'known_inputs.json')
    prep = read(HERE / 'preparation.json')
    for name, expected in prep['prepared_file_hashes'].items():
        check(sha(HERE / name) == expected, 'Frozen software changed: ' + name)
    owner = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    check({key: owner[key] for key in OWNER_KEYS}
          == inputs['owner_provenance_only'], 'Fresh owner changed')
    check(datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at']),
          'Owner expired')
    for entry in inputs['input_artifacts'].values():
        check(sha(ROOT / entry['path']) == entry['sha256'],
              'Known source/preregistration/producers changed')
    native = Path(args.native_dir).resolve()
    review_path = Path(args.source_review).resolve()
    out = Path(args.output).resolve()
    check(native.is_relative_to(TICK) and review_path.is_relative_to(TICK),
          'New producer/source review must belong to this tick')
    check(out.is_relative_to(TICK) and not out.exists(),
          'Output must be fresh and within this tick; never overwrite')
    review = read(review_path)
    check(review.get('passed') is True, 'Actual source independent review missing')
    frozen = read(native / 'FROZEN.json')
    native_prep = read(native / 'preparation.json')
    manifest = read(native / 'manifest_template.json')
    for name, expected in frozen['files'].items():
        path = (native / name).resolve()
        check(path.is_relative_to(native) and sha(path) == expected,
              'Native frozen file changed: ' + name)
    for name, expected in native_prep['prepared_file_hashes'].items():
        path = (native / name).resolve()
        check(path.is_relative_to(native) and sha(path) == expected,
              'Native preparation file changed: ' + name)
    for value in (native_prep, manifest):
        check(value.get('candidate_id') == inputs['candidate_id'],
              'Native candidate identity mismatch')
    check(native_prep.get('source_commit') == inputs['code_commit']
          and native_prep.get('source_parent_commit') == inputs['runtime_code_commit']
          and manifest.get('code_commit') == inputs['code_commit']
          and manifest.get('goal_sha256') == inputs['goal_sha256'],
          'New native source/parent/goal mismatch')
    check(native_prep.get('source_files') == inputs['source_files_exact9'],
          'New native exact nine source hashes mismatch')
    check(manifest.get('root') == inputs['runtime_root']
          and manifest.get('runtime_expected_commit') == inputs['runtime_code_commit'],
          'Native actual NSD parent runtime root/version changed')
    check(all(key in manifest and manifest[key] is None for key in ACTIVE_FIELDS),
          'Native template must retain original ten NULL execution fields')
    check(manifest.get('resource_authorization') == inputs['resource_authorization']
          and manifest.get('resource_memory_policy') == inputs['resource_memory_policy'],
          'Original GPU0 overlay/memory/max1/three-lock policy changed')
    native_binding = read(native / 'source_version_binding.json')
    check(native_binding.get('code_commit', native_binding.get('source_commit'))
          == inputs['code_commit'], 'Native source version binding mismatch')

    binding = read(HERE / 'current_binding.template.json')
    binding['mother_FROZEN'] = ref(native / 'FROZEN.json')
    binding['mother_native_preparation'] = ref(native / 'preparation.json')
    binding['source_review'] = ref(review_path)
    binding['activation_files'] = {
        name: sha(HERE / name)
        for name in ('remote_ops.py', 'run_nde_operation.py')}
    native_prep_ref = ref(native / 'preparation.json')
    template_ref = ref(native / 'manifest_template.json')
    binding_bytes = (json.dumps(binding, ensure_ascii=False, indent=2,
                               allow_nan=False) + '\n').encode('utf-8')
    binding_sha = hashlib.sha256(binding_bytes).hexdigest()
    adapter = patch_assignments((HERE / 'adapter.py').read_text(encoding='utf-8'), {
        'FROZEN': 'Path(' + repr(str(native)) + ')',
        'PREPARATION_SHA': repr(native_prep_ref['sha256']),
        'TEMPLATE_SHA': repr(template_ref['sha256']),
        'CURRENT_BINDING_SHA256': repr(binding_sha),
    })
    check('DRAFT_EXECUTION_DISABLED = True' in adapter,
          'Rendering must leave operations disabled')
    payloads = {
        'adapter.py': adapter.encode('utf-8'),
        'remote_ops.py': (HERE / 'remote_ops.py').read_bytes(),
        'run_nde_operation.py': (HERE / 'run_nde_operation.py').read_bytes(),
        'current_binding.json': binding_bytes,
    }
    release = read(HERE / 'release_template.template.json')
    release['native_preparation_sha256'] = native_prep_ref['sha256']
    release['manifest_template_sha256'] = template_ref['sha256']
    release['source_version_binding_sha256'] = sha(native / 'source_version_binding.json')
    release['source_hashes'] = {
        name: hashlib.sha256(payloads[name]).hexdigest()
        for name in ('adapter.py', 'remote_ops.py')}
    release['current_binding'] = {
        'path': (out / 'current_binding.json').relative_to(ROOT).as_posix(),
        'sha256': binding_sha}
    payloads['release_template.json'] = (
        json.dumps(release, ensure_ascii=False, indent=2, allow_nan=False)
        + '\n').encode('utf-8')
    output_prep = copy.deepcopy(prep)
    output_prep['prepared_file_hashes'] = {
        name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()}
    output_prep['rendered_at'] = datetime.now(timezone.utc).isoformat()
    output_prep['disabled_generator'] = ref(HERE / 'FROZEN.json')
    output_prep['native_preparation'] = native_prep_ref
    output_prep['source_review'] = ref(review_path)
    out.mkdir()
    for name, data in payloads.items():
        with (out / name).open('xb') as stream:
            stream.write(data)
    dump(out / 'preparation.json', output_prep)
    dump(out / 'FROZEN.json', {
        'schema_version': 1, 'candidate_id': inputs['candidate_id'],
        'code_commit': inputs['code_commit'], 'draft_execution_disabled': True,
        'owner_provenance_only': inputs['owner_provenance_only'],
        'files': {name: sha(out / name) for name in
                  list(payloads) + ['preparation.json']},
        'native': 'NOT_RUN', 'resources': 'NOT_RUN',
        'adapter_release_created': False, 'execution_material_created': False})
    print(json.dumps({'status': 'DRAFT_DISABLED_SOFTWARE_RENDERED',
                      'output': str(out), 'FROZEN': ref(out / 'FROZEN.json'),
                      'native': 'NOT_RUN', 'resources': 'NOT_RUN'}))


if __name__ == '__main__':
    main()
