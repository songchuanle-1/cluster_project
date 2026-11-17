"""Separate EQ entry only; original reviewed remote helpers remain unchanged."""
import base64
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import sys

EXPECTED_REVIEWED_REMOTE_SHA256 = 'db82eab9dd05fd90e30194119b0e1df559ed11a4178a2015923b11e16a48779e'
MODE = 'revision1_equivalence'
ENTRY = 'equivalence_diagnostic.py'
ENTRY_SHA = 'ed2c1bb56d5a27040ae6557c061bbeb64d5e9c0c76646bc25caa09584e00febc'


def check(value, message):
    if not value:
        raise RuntimeError(message)


def base_ops(payload):
    source = base64.b64decode(payload['reviewed_remote_base64'], validate=True)
    check(hashlib.sha256(source).hexdigest() == payload['reviewed_remote_sha256']
          == EXPECTED_REVIEWED_REMOTE_SHA256, 'Reviewed base changed')
    namespace = {'__name__': 'unchanged_reviewed_NDE_remote_helpers'}
    exec(compile(source, 'unchanged_reviewed_remote_ops', 'exec'), namespace)
    return namespace


def identity(binding, request):
    return {'project': 'cluster_project',
            'candidate_id': 'hierarchy-native-distribution-embedding-composition',
            'code_commit': '0747f6acec1c61018ec99acf2efa5329c9b3523c',
            'stage': binding['stage'], 'token': binding['owner']['token'],
            'request_id': request['request_id'], 'operation': MODE,
            'physical_gpu': 0, 'gpu_uuid': binding['gpu_uuid'],
            'native_manifest_sha256': binding['native_manifest_sha256'],
            'entry': ENTRY, 'entry_sha256': ENTRY_SHA}


def command_matches(command, stage):
    return (isinstance(command, list) and len(command) == 5
            and re.fullmatch(r'python(?:\d+(?:\.\d+)*)?', Path(command[0]).name) is not None
            and command[1:] == ['-B', str(stage / ENTRY), '--lease',
                                str(stage / 'execution_lease.json')])


def exact_eq_workers(base, stage):
    found = []
    for path in Path('/proc').iterdir():
        if path.name.isdigit():
            info = base['process_info'](int(path.name))
            if info and command_matches(info['argv'], stage):
                found.append(info)
    return found


def result_matches(base, result, binding, stage):
    expected = {
        'mode': MODE, 'candidate_id': binding['candidate_id'],
        'experiment_id': 'M233-NDE', 'code_commit': binding['code_commit'],
        'goal_sha256': binding['goal_sha256'],
        'runtime_code_commit': binding['runtime_code_commit'],
        'current_token': binding['owner']['token'], 'stage': str(stage),
        'physical_gpu': 0, 'gpu_uuid': binding['gpu_uuid'],
        'native_manifest_sha256': binding['native_manifest_sha256'],
        'diagnostic_worker_sha256': ENTRY_SHA,
        'runtime_sha256': base['sha'](stage / 'native_runtime.py')}
    expected.update({key: binding['owner'][owner_key] for key, owner_key in (
        ('tick_generated_at', 'generated_at'), ('deadline_at', 'deadline_at'),
        ('context_sha256', 'context_sha256'), ('pending_sha256', 'pending_sha256'))})
    return isinstance(result, dict) and all(result.get(k) == v for k, v in expected.items())


def run_eq(payload, base):
    binding, request = payload['binding'], payload['request']
    stage = base['binding_stage'](binding)
    check(request == identity(binding, request), 'Foreign EQ request')
    base['require_fresh'](binding, minimum=1020)
    base['require_usable'](binding)
    base['native_verify'](stage, binding)
    manifest = base['read'](stage / 'native_manifest.json')
    check(manifest['diagnostic_files'].get(ENTRY) == ENTRY_SHA
          and base['sha'](stage / ENTRY) == ENTRY_SHA, 'Exact staged EQ entry required')
    check(base['read'](stage / 'stage_completed.json').get('verified') is True,
          'Original verified stage required')
    check(not (stage / 'equivalence_request.json').exists()
          and not (stage / 'equivalence_started.json').exists()
          and not (stage / 'equivalence_result.json').exists()
          and not (stage / 'equivalence_completed.json').exists(),
          'EQ already attempted; reconcile, never replay')
    check(not base['exact_workers'](stage) and not exact_eq_workers(base, stage),
          'Existing exact-stage worker; no overlapping project execution')
    base['require_fresh'](binding, minimum=1020)
    base['write'](stage / 'equivalence_request.json', request)
    command = [sys.executable, '-B', str(stage / ENTRY),
               '--lease', str(stage / 'execution_lease.json')]
    stdout, stderr = stage / 'equivalence_stdout.log', stage / 'equivalence_stderr.log'
    with stdout.open('xb') as out, stderr.open('xb') as err:
        process = subprocess.Popen(command, stdout=out, stderr=err,
                                   cwd=str(stage), start_new_session=False)
        started = {'identity': identity(binding, request), 'mode': MODE,
                   'pid': process.pid, 'process_identity': base['process_info'](process.pid),
                   'command': command, 'stdout': str(stdout), 'stderr': str(stderr)}
        base['write'](stage / 'equivalence_started.json', started)
        try:
            returncode = process.wait(timeout=660)
        except subprocess.TimeoutExpired:
            return {'identity': identity(binding, request), 'certainty': 'uncertain',
                    'wait_timed_out': True, 'pid': process.pid,
                    'process_identity': base['process_info'](process.pid)}
    result_path = stage / 'equivalence_result.json'
    result = {'identity': identity(binding, request), 'certainty': 'terminal',
              'returncode': returncode, 'pid': process.pid,
              'original_process_identity': started['process_identity'], 'command': command,
              'result_sha256': base['sha'](result_path) if result_path.exists() else None,
              'result': base['read'](result_path) if result_path.exists() else None,
              'stdout_sha256': base['sha'](stdout), 'stderr_sha256': base['sha'](stderr)}
    base['write'](stage / 'equivalence_completed.json', result)
    return result


def reconcile_eq(payload, base):
    binding = payload['binding']
    stage = base['binding_stage'](binding)
    found = {'read_only': True, 'stage': str(stage), 'exists': stage.exists(),
             'native_manifest_sha256': None, 'certainty': 'uncertain',
             'workers': exact_eq_workers(base, stage), 'original_workers': base['exact_workers'](stage)}
    if not stage.exists():
        return found
    manifest = stage / 'native_manifest.json'
    found['native_manifest_sha256'] = base['sha'](manifest) if manifest.exists() else None
    path = stage / 'equivalence_request.json'
    if not path.exists():
        found['remote_request_exists'] = False
        return found
    request = base['read'](path)
    expected = identity(binding, request)
    check(request == expected, 'EQ reconciliation request identity changed')
    if payload.get('request_id') is not None:
        check(request['request_id'] == payload['request_id'], 'Different EQ request')
    found.update(remote_request_exists=True, request=request, request_sha256=base['sha'](path))
    started = stage / 'equivalence_started.json'
    if started.exists():
        value = base['read'](started)
        current = base['process_info'](value['pid'])
        original = value.get('process_identity')
        found.update(started=value, current_pid_identity=current,
                     original_pid_still_same=bool(
                         original and current and value.get('identity') == expected
                         and original['start_ticks'] == current['start_ticks']
                         and original['argv'] == current['argv']
                         and command_matches(current['argv'], stage)
                         and command_matches(value.get('command'), stage)))
    completed = stage / 'equivalence_completed.json'
    if completed.exists():
        value = base['read'](completed)
        valid = (value.get('identity') == expected
                 and command_matches(value.get('command'), stage)
                 and result_matches(base, value.get('result'), binding, stage))
        result = stage / 'equivalence_result.json'
        valid = valid and result.exists() and value.get('result_sha256') == base['sha'](result)
        found.update(completed=value, completed_sha256=base['sha'](completed),
                     completed_identity_command_and_result_verified=valid)
        if valid and value.get('certainty') == 'terminal':
            found['certainty'] = 'terminal'
    return found


def dispatch(operation, payload):
    check(socket.gethostname() == 'dl04-MS-7E06', 'Pinned server hostname required')
    check(operation in ('equivalence_run', 'equivalence_reconcile'),
          'Default deny: no original run/probe/stage or worker mode accepted')
    base = base_ops(payload)
    return run_eq(payload, base) if operation == 'equivalence_run' else reconcile_eq(payload, base)
