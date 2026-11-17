"""Default NOP; bind actual fresh worker/runtime hashes into disabled software.

No result normalization, SSH, GPU, native import, admission or shared mutation.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/project/cluster_project').resolve()
TICK = ROOT / 'pipeline/diagnostic_bundles/tick_f6536795'


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(value, message):
    if not value:
        raise ValueError(message)


def ref(path):
    path = Path(path).resolve()
    check(path.is_relative_to(ROOT), 'Artifact outside cluster_project')
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def dump(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def replace_assignments(text, values):
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)
    patches = []
    for name, replacement in values.items():
        nodes = [node for node in tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == name
                         for target in node.targets)]
        check(len(nodes) == 1, 'Unknown/ambiguous assignment: ' + name)
        node = nodes[0]
        patches.append((node.lineno - 1, node.end_lineno,
                        name + ' = ' + replacement + '\n'))
    for start, end, replacement in sorted(patches, reverse=True):
        lines[start:end] = [replacement]
    result = ''.join(lines)
    compile(result, '<disabled-normalizer-software-only>', 'exec')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-disabled', action='store_true')
    parser.add_argument('--native-dir')
    parser.add_argument('--base-native-dir')
    parser.add_argument('--output')
    args = parser.parse_args()
    if not args.render_disabled:
        print(json.dumps({'status': 'DEFAULT_NOP_NO_NORMALIZATION_OR_FILES'}))
        return
    check(args.native_dir and args.base_native_dir and args.output,
          'Actual new active and disabled mother native paths and absent output required')
    prep = read(HERE / 'preparation.json')
    for name, expected in prep['prepared_file_hashes'].items():
        check(sha(HERE / name) == expected, 'Frozen software changed: ' + name)
    inputs = read(HERE / 'known_inputs.json')
    owner = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    check(all(owner[key] == value for key, value in
              inputs['owner_provenance_only'].items()), 'Current owner changed')
    check(datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at']),
          'Current owner expired')
    for name in ('new_source_proof', 'new_source_review', 'historical_champion_provenance',
                 'historical_reuse_review'):
        entry = inputs[name]
        check(sha(ROOT / entry['path']) == entry['sha256'],
              'Actual source/review/provenance changed: ' + name)
    review = read(ROOT / inputs['historical_reuse_review']['path'])
    check(review.get('passed') is True
          and review.get('historical_control_reuse_eligible') is True,
          'Historical champion compatibility review is not affirmative')
    native, mother, output = (Path(value).resolve() for value in
                              (args.native_dir, args.base_native_dir, args.output))
    check(native == (ROOT / inputs['reused_native']['directory']).resolve()
          and mother == (ROOT / inputs['reused_native']['disabled_mother_directory']).resolve()
          and native != mother, 'Use the exact immutable reviewed revision1 native and disabled mother')
    for name, entry in inputs['reused_native']['files'].items():
        check(sha(ROOT / entry['path']) == entry['sha256'],
              'Immutable reused native/source payload changed: ' + name)
    operational_refs = inputs['fresh_operational_refs']
    check(isinstance(operational_refs, dict) and bool(operational_refs),
          'Actual current-owner operational software hashes are not finalized')
    for name, entry in operational_refs.items():
        artifact = (ROOT / entry['path']).resolve()
        check(artifact.is_relative_to(TICK) and sha(artifact) == entry['sha256'],
              'Actual current-owner operational artifact changed: ' + name)
    check(output.is_relative_to(TICK) and not output.exists(),
          'Output must be absent and inside this tick')
    manifest = read(native / 'manifest_template.json')
    check(manifest['candidate_id'] == inputs['candidate_id']
          and manifest['code_commit'] == inputs['code_commit']
          and manifest['runtime_expected_commit'] == 'f6257de79148581334ee495e6e2d60ccb525457c'
          and manifest['root'] == '/data/songcl/Project/Cluster_project/Cluster_nsd_20261107',
          'New actual source/runtime/root mismatch')
    check(sha(native / 'worker.py') == sha(mother / 'worker.py'),
          'Actual new worker differs from reviewed disabled mother')
    check((native / 'native_runtime.py').read_bytes() ==
          (mother / 'native_runtime.py').read_bytes().replace(
              b'DRAFT_EXECUTION_DISABLED = True',
              b'DRAFT_EXECUTION_DISABLED = False', 1),
          'Active runtime is not the sole original DRAFT flag change')
    source = (HERE / 'normalize_nde_actual_results.py').read_text(encoding='utf-8')
    source = replace_assignments(source, {
        'BASE_NATIVE': 'Path(' + repr(str(mother)) + ')',
        'EXPECTED_WORKER_SHA256': repr(sha(native / 'worker.py')),
        'EXPECTED_RUNTIME_SHA256': repr(sha(native / 'native_runtime.py')),
        'EXPECTED_NATIVE': 'Path(' + repr(str(native)) + ')',
        'EXPECTED_OPERATIONAL_REFS': repr(operational_refs),
    })
    check('DRAFT_NORMALIZATION_DISABLED = True' in source,
          'Rendered normalizer must remain DRAFT-disabled')
    output.mkdir()
    with (output / 'normalize_nde_actual_results.py').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(source)
    record = {
        'schema_version': 1, 'candidate_id': inputs['candidate_id'],
        'experiment_id': 'M233-NDE', 'source_commit': inputs['code_commit'],
        'owner_provenance_only': inputs['owner_provenance_only'],
        'rendered_at': datetime.now(timezone.utc).isoformat(),
        'draft_normalization_disabled': True, 'normalization_executed': False,
        'native_actual_payload': {
            'worker': ref(native / 'worker.py'),
            'runtime': ref(native / 'native_runtime.py'),
            'mother_runtime': ref(mother / 'native_runtime.py')},
        'historical_reuse_review': inputs['historical_reuse_review'],
        'historical_champion_provenance': inputs['historical_champion_provenance'],
        'generator': ref(HERE / 'FROZEN.json'),
        'fresh_operational_refs': operational_refs,
        'reused_native': inputs['reused_native'],
        'fresh_arms': inputs['fresh_arms'], 'historical_arm': inputs['historical_arm'],
        'prepared_file_hashes': {
            'normalize_nde_actual_results.py': sha(output / 'normalize_nde_actual_results.py')},
        'admission_granted': False}
    dump(output / 'preparation.json', record)
    dump(output / 'FROZEN.json', {
        'schema_version': 1, 'draft_normalization_disabled': True,
        'files': {name: sha(output / name) for name in
                  ('normalize_nde_actual_results.py', 'preparation.json')},
        'normalization_executed': False, 'admission_granted': False})
    print(json.dumps({'status': 'ACTUAL_HASHES_BOUND_SOFTWARE_DISABLED',
                      'FROZEN': ref(output / 'FROZEN.json'),
                      'normalization_executed': False}))


if __name__ == '__main__':
    main()
