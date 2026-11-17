"""Default NOP; one separately bound diagnostic request, never ordinary adapter.run."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import uuid

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
ACTIVE = TICK / 'nde_operational_active'
EXECUTION = TICK / 'nde_execution'
LOCAL = TICK / 'nde_crash_probe_execution'
INTENT = TICK / 'nde_root_crash_probe_intent.json'


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
        print(json.dumps({'status': 'DEFAULT_NOP_NO_ENTRY_TRANSPORT_OR_FILES'}))
        return
    release = read(HERE / 'operation_release.json')
    assert release == read(HERE / 'release_template.json'), 'Actual independent review/release required'
    for name, expected in release['source_hashes'].items():
        assert sha(HERE / name) == expected
    packet = read(HERE / 'diagnostic_packet.json')
    assert packet['binding_complete'] is True, 'Default deny: actual bootstrap/preregistration/review not bound'
    module = load('reviewed_current_NDE_adapter_for_crash_probe', ACTIVE / 'adapter.py')
    wrapper = load('reviewed_current_NDE_snapshot_for_crash_probe', ACTIVE / 'run_nde_operation.py')
    adapter = module.Adapter()
    current = adapter.guard(1020 if args.operation == 'run' else 60, 0,
                            mutation=args.operation == 'run')
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        current, directory, binding = adapter._binding(
            mutation=args.operation == 'run', required_seconds=1020 if args.operation == 'run' else 60)
        assert directory == EXECUTION.resolve() and binding['owner'] == packet['owner']
        before = wrapper.snapshot(current['owner'])
        base = (ACTIVE / 'remote_ops.py').read_bytes()
        transport = module.SSHTransport(origin=HERE)
        request = read(LOCAL / 'crash_probe_request.json') if LOCAL.exists() else None
        payload = {'binding': binding, 'reviewed_remote_base64': base64.b64encode(base).decode()}
        if args.operation == 'reconcile' or INTENT.exists() or LOCAL.exists():
            assert request is not None, 'Local root intent exists without request; preserve and inspect, no replay'
            found = transport.call('reconcile_crash_probe', {**payload, 'request': request},
                                   current['server'], timeout=40)
            write_x(LOCAL / ('reconcile_' + uuid.uuid4().hex + '.json'), found)
            print(json.dumps({'status': 'RECONCILIATION_ONLY_NO_REPLAY', 'result': found}))
            return
        adapter.guard(1020, 0, mutation=True)
        adapter._local_idle(0)
        adapter._previous_complete(current, directory, binding)
        adapter._check_probe(adapter.probe(0), 0)
        adapter.guard(1020, 0, mutation=True)
        files = {}
        for name, entry in packet['additional_diagnostic_files'].items():
            path = (ROOT / entry['path']).resolve()
            assert path.is_relative_to(ROOT.resolve()) and sha(path) == entry['sha256']
            files[name] = base64.b64encode(path.read_bytes()).decode()
        request = {
            'operation': 'candidate_resources_fault_localization', 'request_id': uuid.uuid4().hex,
            'owner': binding['owner'], 'project': 'cluster_project',
            'candidate_id': binding['candidate_id'], 'code_commit': binding['code_commit'],
            'runtime_code_commit': binding['runtime_code_commit'], 'stage': binding['stage'],
            'physical_gpu': 0, 'gpu_uuid': binding['gpu_uuid'],
            'native_manifest_sha256': binding['native_manifest_sha256'],
            'execution_lease_sha256': binding['execution_lease_sha256'],
            'fault_localization_only': True, 'admission_evidence': False,
            'comparable_resource_or_latency_evidence': False,
            'additional_diagnostic_files': {
                name: entry['sha256'] for name, entry in packet['additional_diagnostic_files'].items()},
            'bootstrap_sha256': packet['additional_diagnostic_files']['crash_probe_bootstrap.py']['sha256'],
            'worker_sha256': 'b37fe5cf29ce04b8110752c7321d34b8d1a26218a6d8e02940b5773d9e4d5f72',
            'runtime_sha256': '348024f11e6a106788840c1359ad8c65363914d1f1882cfe4a5f8d319d5ea1a4',
            'independent_review_file': 'crash_probe_independent_review.json',
            'independent_review_sha256': packet['additional_diagnostic_files']['crash_probe_independent_review.json']['sha256'],
            'preregistration_file': 'crash_probe_preregistration.json',
            'preregistration_sha256': packet['additional_diagnostic_files']['crash_probe_preregistration.json']['sha256'],
            'original_worker_argv': [binding['stage'] + '/worker.py', '--lease',
                                     binding['stage'] + '/execution_lease.json',
                                     '--mode', 'resources', '--target', 'candidate']}
        write_x(INTENT, {'owner': binding['owner'], 'request': request,
                         'diagnostic_packet_sha256': sha(HERE / 'diagnostic_packet.json'),
                         'protected_before': before})
        LOCAL.mkdir()
        write_x(LOCAL / 'crash_probe_request.json', request)
        adapter.guard(1020, 0, mutation=True)
        try:
            result = transport.call('run_crash_probe', {**payload, 'request': request, 'files': files},
                                    current['server'], timeout=900, conda=True)
            assert result.get('request') == request and result.get('certainty') == 'terminal'
            write_x(LOCAL / 'crash_probe_execution.json', result)
        except Exception as error:
            uncertain = {'certainty': 'uncertain', 'request': request,
                         'error_type': type(error).__name__, 'error': str(error)}
            try:
                uncertain['reconcile'] = transport.call(
                    'reconcile_crash_probe', {**payload, 'request': request},
                    current['server'], timeout=40)
            except Exception as followup:
                uncertain['reconcile_error'] = str(followup)
            write_x(LOCAL / 'crash_probe_uncertain.json', uncertain)
            raise
        adapter.guard(0, 0, mutation=False)
        assert wrapper.snapshot(current['owner']) == before
        print(json.dumps({'status': 'DIAGNOSTIC_TERMINAL_RESULT_PRESERVED',
                          'result': result, 'admission_evidence': False,
                          'comparable_resource_or_latency_evidence': False}, allow_nan=False))
    finally:
        lock.close()


if __name__ == '__main__':
    main()
