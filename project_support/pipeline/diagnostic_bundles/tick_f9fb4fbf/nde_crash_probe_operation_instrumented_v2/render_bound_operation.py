"""Default NOP. Bind actual bootstrap/preregistration/review into a new packet."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/project/cluster_project').resolve()


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bind-software', action='store_true')
    parser.add_argument('--bootstrap')
    parser.add_argument('--preregistration')
    parser.add_argument('--review')
    parser.add_argument('--output')
    args = parser.parse_args()
    if not args.bind_software:
        print(json.dumps({'status': 'DEFAULT_NOP_NO_FILES_OR_TRANSPORT'}))
        return
    assert all((args.bootstrap, args.preregistration, args.review, args.output))
    frozen = read(HERE / 'FROZEN.json')
    for name, expected in frozen['files'].items():
        assert sha(HERE / name) == expected
    owner = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    expected_owner = read(HERE / 'diagnostic_packet.json')['owner']
    assert all(owner[key] == value for key, value in expected_owner.items())
    paths = {name: Path(value).resolve() for name, value in (
        ('crash_probe_bootstrap.py', args.bootstrap),
        ('crash_probe_protocol.json', args.preregistration),
        ('independent_probe_review.json', args.review))}
    assert all(path.is_relative_to(ROOT) for path in paths.values())
    bootstrap = paths['crash_probe_bootstrap.py']
    source = bootstrap.read_text(encoding='utf-8')
    compile(source, str(bootstrap), 'exec')
    draft = [node.value.value for node in ast.parse(source).body
             if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
             and any(isinstance(target, ast.Name) and target.id == 'DRAFT_DIAGNOSTIC_DISABLED'
                     for target in node.targets)]
    assert draft == [False], 'Use separately reviewed active bootstrap; this renderer never activates it'
    # Bootstrap's existing manifest contract is satisfied by a separately reviewed
    # fresh manifest view; old native package and fourteen original entries stay frozen.
    review = read(paths['independent_probe_review.json'])
    prereg = read(paths['crash_probe_protocol.json'])
    assert review.get('passed') is True and review.get('owner') == expected_owner
    assert review.get('bootstrap_sha256') == sha(bootstrap) and review.get('fault_localization_only') is True
    assert prereg.get('owner') == expected_owner
    assert prereg.get('kind') == 'ONE_BOUNDED_RESOURCE_PROCESS_CRASH_LOCALIZATION'
    assert prereg.get('execution_budget', {}).get('max_attempts') == 1
    assert prereg['execution_budget'].get('minimum_remaining_seconds') == 1020
    assert sha(paths['crash_probe_protocol.json']) == '8b2dd93ee7b62c729609a306a89c782185720c1eb721652a5378f09cbb285513'
    assert sha(bootstrap) == '4d3d8230d09ebf3dbc834a9cb879eb3f5f2df5db9a090dfe85e31f3067494146', 'Actual instrumented_v2 sole-flag active bootstrap required'
    output = Path(args.output).resolve()
    assert output.parent == HERE.parent.resolve() and not output.exists()
    output.mkdir()
    for name in ('remote_ops.py', 'run_crash_probe_operation.py'):
        shutil.copyfile(HERE / name, output / name)
    packet = read(HERE / 'diagnostic_packet.json')
    packet.update(binding_complete=True, additional_diagnostic_files={
        name: {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}
        for name, path in paths.items()})
    write(output / 'diagnostic_packet.json', packet)
    release = read(HERE / 'release_template.json')
    release['source_hashes'] = {name: sha(output / name) for name in (
        'remote_ops.py', 'run_crash_probe_operation.py', 'diagnostic_packet.json')}
    write(output / 'release_template.json', release)
    write(output / 'FROZEN.json', {
        'schema_version': 1, 'owner_provenance_only': expected_owner,
        'files': {name: sha(output / name) for name in (
            'remote_ops.py', 'run_crash_probe_operation.py',
            'diagnostic_packet.json', 'release_template.json')},
        'operation_release_created': False, 'actual_execution': 'NOT_RUN',
        'admission_evidence': False, 'comparable_resource_or_latency_evidence': False})
    print(json.dumps({'status': 'BOUND_SOFTWARE_ONLY_RELEASE_ABSENT',
                      'output': str(output), 'FROZEN_sha256': sha(output / 'FROZEN.json')}))


if __name__ == '__main__':
    main()
