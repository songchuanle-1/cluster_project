"""Default NOP; separate, reviewed EQ operation using an existing native stage."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import uuid

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
ACTIVE = TICK / 'nde_resource_operational_active'
EXECUTION = TICK / 'nde_execution'
EQ_EXECUTION = TICK / 'nde_equivalence_execution'
ROOT_INTENT = TICK / 'nde_root_revision1_equivalence_intent.json'
MODE = 'revision1_equivalence'
ENTRY_SHA = 'ed2c1bb56d5a27040ae6557c061bbeb64d5e9c0c76646bc25caa09584e00febc'


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_x(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-root', action='store_true')
    parser.add_argument('--operation', choices=('run', 'reconcile'), default='run')
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({'status': 'DEFAULT_NOP_NO_ENTRY_OR_TRANSPORT',
                          'native_TRAIN_steps': 0, 'execution_material_created': False}))
        return
    release = read(HERE / 'operation_release.json')
    assert release == read(HERE / 'release_template.json'), 'Reviewed EQ software release required'
    for name, expected in release['source_hashes'].items():
        assert sha(HERE / name) == expected, 'EQ source changed'
    inputs = read(HERE / 'inputs.json')
    for name, entry in inputs['reviewed_inputs'].items():
        assert sha(ROOT / entry['path']) == entry['sha256'], 'Reviewed input changed: ' + name
    adapter_module = load('reviewed_current_NDE_adapter_for_EQ', ACTIVE / 'adapter.py')
    wrapper = load('reviewed_current_NDE_snapshot_for_EQ', ACTIVE / 'run_nde_operation.py')
    adapter = adapter_module.Adapter()
    minimum = 1020 if args.operation == 'run' else 60
    current = adapter.guard(minimum, 0, mutation=args.operation == 'run')
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None, 'Project operation lock busy'
    try:
        current, directory, binding = adapter._binding(
            mutation=args.operation == 'run', required_seconds=minimum)
        assert directory == EXECUTION.resolve()
        assert binding['owner'] == inputs['current_owner']
        assert sha(EXECUTION / 'execution_binding.json') == inputs['execution_binding_sha256']
        assert read(EXECUTION / 'native_manifest.json')['diagnostic_files']['equivalence_diagnostic.py'] == ENTRY_SHA
        before = wrapper.snapshot(current['owner'])
        base_source = (ACTIVE / 'remote_ops.py').read_bytes()
        payload = {'binding': binding,
                   'reviewed_remote_base64': base64.b64encode(base_source).decode(),
                   'reviewed_remote_sha256': sha(ACTIVE / 'remote_ops.py')}
        transport = adapter_module.SSHTransport(origin=HERE)

        def reconcile():
            previous = read(EQ_EXECUTION / 'equivalence_request.json') if (
                EQ_EXECUTION / 'equivalence_request.json').exists() else None
            result = transport.call(
                'equivalence_reconcile',
                {**payload, 'request_id': previous['request_id'] if previous else None},
                current['server'], timeout=40)
            assert result.get('stage') == binding['stage']
            assert result.get('native_manifest_sha256') in (None, binding['native_manifest_sha256'])
            EQ_EXECUTION.mkdir(exist_ok=True)
            write_x(EQ_EXECUTION / ('reconcile_' + uuid.uuid4().hex + '.json'), result)
            return result

        if args.operation == 'reconcile' or ROOT_INTENT.exists() or EQ_EXECUTION.exists():
            result = reconcile()
            print(json.dumps({'status': 'RECONCILIATION_ONLY_NO_REPLAY', 'result': result}))
            return
        adapter.guard(1020, 0, mutation=True)
        adapter._local_idle(0)
        adapter._previous_complete(current, directory, binding)
        adapter._check_probe(adapter.probe(0), 0)
        adapter.guard(1020, 0, mutation=True)
        identity = {'project': 'cluster_project', 'candidate_id': binding['candidate_id'],
                    'code_commit': binding['code_commit'], 'stage': binding['stage'],
                    'token': binding['owner']['token'], 'request_id': uuid.uuid4().hex,
                    'operation': MODE, 'physical_gpu': 0, 'gpu_uuid': binding['gpu_uuid'],
                    'native_manifest_sha256': binding['native_manifest_sha256'],
                    'entry': 'equivalence_diagnostic.py', 'entry_sha256': ENTRY_SHA}
        write_x(ROOT_INTENT, {'owner': binding['owner'], 'request': identity,
                             'execution_binding_sha256': sha(EXECUTION / 'execution_binding.json'),
                             'protected_before': before,
                             'entry': 'separate_EQ_no_TRAIN2_no_original_worker_mode'})
        EQ_EXECUTION.mkdir()
        write_x(EQ_EXECUTION / 'equivalence_request.json', identity)
        adapter.guard(1020, 0, mutation=True)
        try:
            result = transport.call('equivalence_run', {**payload, 'request': identity},
                                    current['server'], timeout=900, conda=True)
            assert result.get('identity') == identity and result.get('certainty') == 'terminal'
            write_x(EQ_EXECUTION / 'equivalence_execution.json', result)
        except Exception as error:
            uncertain = {'certainty': 'uncertain', 'request': identity,
                         'error_type': type(error).__name__, 'error': str(error)}
            try:
                uncertain['reconciliation'] = reconcile()
            except Exception as followup:
                uncertain['reconciliation_error'] = str(followup)
            write_x(EQ_EXECUTION / 'equivalence_uncertain.json', uncertain)
            raise
        adapter.guard(0, 0, mutation=False)
        assert wrapper.snapshot(current['owner']) == before, 'Protected assets changed; no replay'
        raw = result.get('result') or {}
        assert result['returncode'] == 0 and raw.get('execution_completed') is True
        expected_raw = {
            'mode': MODE, 'candidate_id': binding['candidate_id'],
            'experiment_id': 'M233-NDE', 'code_commit': binding['code_commit'],
            'goal_sha256': binding['goal_sha256'],
            'runtime_code_commit': binding['runtime_code_commit'],
            'current_token': binding['owner']['token'], 'stage': binding['stage'],
            'physical_gpu': 0, 'gpu_uuid': binding['gpu_uuid'],
            'native_manifest_sha256': binding['native_manifest_sha256'],
            'diagnostic_worker_sha256': ENTRY_SHA,
            'runtime_sha256': inputs['reviewed_inputs']['native_runtime']['sha256']}
        expected_raw.update({key: binding['owner'][owner_key] for key, owner_key in (
            ('tick_generated_at', 'generated_at'), ('deadline_at', 'deadline_at'),
            ('context_sha256', 'context_sha256'), ('pending_sha256', 'pending_sha256'))})
        assert all(raw.get(key) == value for key, value in expected_raw.items())
        assert result['command'] == [
            '/home/songcl/.conda/envs/project_cluster/bin/python', '-B',
            binding['stage'] + '/equivalence_diagnostic.py',
            '--lease', binding['stage'] + '/execution_lease.json']
        assert raw.get('native_TRAIN_steps') == raw.get('new_training') == 0
        assert raw.get('native_data_loaded') is False
        assert raw.get('equivalence_passed') is True and raw.get('distinguishing_control_passed') is True
        print(json.dumps({'status': 'SEPARATE_EQ_TERMINAL_RESULT_CAPTURED',
                          'result': result, 'native_TRAIN_steps': 0,
                          'scientific_admission': False}, allow_nan=False))
    finally:
        lock.close()


if __name__ == '__main__':
    main()
