"""One separately preregistered crash probe; original helpers remain unchanged."""
import base64
import hashlib
from pathlib import Path
import re
import socket
import subprocess
import sys

EXPECTED_REVIEWED_REMOTE_SHA256 = 'db82eab9dd05fd90e30194119b0e1df559ed11a4178a2015923b11e16a48779e'
OPERATION = 'candidate_resources_fault_localization'
FILES = ('crash_probe_bootstrap.py', 'crash_probe_independent_review.json',
         'crash_probe_preregistration.json')


def check(value, message):
    if not value:
        raise RuntimeError(message)


def helpers(payload):
    source = base64.b64decode(payload['reviewed_remote_base64'], validate=True)
    check(hashlib.sha256(source).hexdigest() == EXPECTED_REVIEWED_REMOTE_SHA256,
          'Original reviewed remote source changed')
    namespace = {'__name__': 'original_reviewed_remote_helpers'}
    exec(compile(source, 'unchanged_reviewed_remote_ops', 'exec'), namespace)
    return namespace


def command_matches(command, stage):
    expected = ['-B', '-X', 'faulthandler', '-u', str(stage / FILES[0]),
                '--diagnostic-request', str(stage / 'crash_probe_request.json')]
    return (isinstance(command, list) and len(command) == len(expected) + 1
            and re.fullmatch(r'python(?:\d+(?:\.\d+)*)?', Path(command[0]).name) is not None
            and command[1:] == expected)


def workers(base, stage):
    found = []
    for path in Path('/proc').iterdir():
        if path.name.isdigit():
            info = base['process_info'](int(path.name))
            if info and command_matches(info['argv'], stage):
                found.append(info)
    return found


def validate(payload, base):
    binding, request = payload['binding'], payload['request']
    stage = base['binding_stage'](binding)
    check(request['operation'] == OPERATION
          and request['owner'] == binding['owner']
          and request['code_commit'] == binding['code_commit']
          and request['runtime_code_commit'] == binding['runtime_code_commit']
          and request['native_manifest_sha256'] == binding['native_manifest_sha256']
          and request['execution_lease_sha256'] == binding['execution_lease_sha256']
          and request['stage'] == str(stage) and request['physical_gpu'] == 0
          and request['gpu_uuid'] == binding['gpu_uuid'],
          'Fresh actual diagnostic request/binding identity mismatch')
    check(request['fault_localization_only'] is True
          and request['admission_evidence'] is False
          and request['comparable_resource_or_latency_evidence'] is False,
          'Only non-admitting fault localization is allowed')
    check(set(request['additional_diagnostic_files']) == set(FILES)
          and request['bootstrap_sha256'] == request['additional_diagnostic_files'][FILES[0]]
          and request['independent_review_sha256'] == request['additional_diagnostic_files'][FILES[1]]
          and request['preregistration_sha256'] == request['additional_diagnostic_files'][FILES[2]],
          'Separate diagnostic extension hash binding incomplete')
    return binding, request, stage


def reconcile(payload, base):
    binding, request, stage = validate(payload, base)
    found = {'read_only': True, 'stage': str(stage), 'certainty': 'uncertain',
             'native_manifest_sha256': base['sha'](stage / 'native_manifest.json'),
             'original_workers': base['exact_workers'](stage), 'workers': workers(base, stage)}
    path = stage / 'crash_probe_request.json'
    if not path.exists():
        found['remote_request_exists'] = False
        return found
    check(base['read'](path) == request, 'Remote diagnostic request changed')
    found.update(remote_request_exists=True, request_sha256=base['sha'](path))
    started = stage / 'crash_probe_started.json'
    if started.exists():
        info = base['read'](started)
        current, original = base['process_info'](info['pid']), info.get('process_identity')
        found.update(started=info, current_pid_identity=current,
                     original_pid_still_same=bool(original and current
                         and original['start_ticks'] == current['start_ticks']
                         and original['argv'] == current['argv']
                         and command_matches(current['argv'], stage)
                         and info.get('request') == request))
    completed = stage / 'crash_probe_completed.json'
    if completed.exists():
        value = base['read'](completed)
        valid = value.get('request') == request and command_matches(value.get('command'), stage)
        for name, digest in value.get('captured_file_hashes', {}).items():
            valid = valid and (stage / name).is_file() and base['sha'](stage / name) == digest
        found.update(completed=value, completed_sha256=base['sha'](completed),
                     completed_request_command_hashes_verified=valid)
        if valid and value.get('certainty') == 'terminal':
            found['certainty'] = 'terminal'
    return found


def run(payload, base):
    binding, request, stage = validate(payload, base)
    base['require_fresh'](binding, minimum=1020)
    base['require_usable'](binding)
    base['native_verify'](stage, binding)
    check(base['read'](stage / 'stage_completed.json').get('verified') is True,
          'Original verified stage required')
    forbidden = ['crash_probe_request.json', 'crash_probe_started.json', 'crash_probe_completed.json',
                 'resources_candidate_request.json', 'resources_candidate_result.json',
                 'resources_candidate_completed.json', 'fault_localization_markers.jsonl']
    check(not any((stage / name).exists() for name in forbidden)
          and not base['exact_workers'](stage) and not workers(base, stage),
          'Existing attempt/worker: reconcile only, never retry')
    manifest_sha = base['sha'](stage / 'native_manifest.json')
    lease_sha = base['sha'](stage / 'execution_lease.json')
    # Separate x-created files; original fourteen manifest entries and lease remain untouched.
    check(set(payload['files']) == set(FILES), 'Unexpected extra diagnostic file')
    for name in FILES:
        data = base64.b64decode(payload['files'][name], validate=True)
        check(hashlib.sha256(data).hexdigest() == request['additional_diagnostic_files'][name],
              'Extra diagnostic file hash mismatch')
        with (stage / name).open('xb') as stream:
            stream.write(data)
    review = base['read'](stage / FILES[1])
    prereg = base['read'](stage / FILES[2])
    check(review.get('passed') is True and review.get('owner') == binding['owner']
          and review.get('bootstrap_sha256') == request['bootstrap_sha256']
          and review.get('fault_localization_only') is True, 'Actual diagnostic review required')
    check(prereg.get('owner') == binding['owner']
          and prereg.get('fault_localization_only') is True, 'Actual preregistration required')
    base['require_fresh'](binding, minimum=1020)
    base['write'](stage / 'crash_probe_request.json', request)
    command = [sys.executable, '-B', '-X', 'faulthandler', '-u', str(stage / FILES[0]),
               '--diagnostic-request', str(stage / 'crash_probe_request.json')]
    stdout, stderr = stage / 'crash_probe_stdout.log', stage / 'crash_probe_stderr.log'
    with stdout.open('xb') as out, stderr.open('xb') as err:
        process = subprocess.Popen(command, stdout=out, stderr=err, cwd=str(stage),
                                   start_new_session=False)
        base['write'](stage / 'crash_probe_started.json', {
            'request': request, 'pid': process.pid, 'process_identity': base['process_info'](process.pid),
            'command': command, 'stdout': str(stdout), 'stderr': str(stderr)})
        try:
            returncode = process.wait(timeout=660)
        except subprocess.TimeoutExpired:
            return {'request': request, 'certainty': 'uncertain', 'wait_timed_out': True,
                    'pid': process.pid, 'process_identity': base['process_info'](process.pid)}
    captured = {}
    for name in ('crash_probe_stdout.log', 'crash_probe_stderr.log',
                 'fault_localization_markers.jsonl', 'resources_candidate_result.json'):
        if (stage / name).is_file():
            captured[name] = base['sha'](stage / name)
    check(base['sha'](stage / 'native_manifest.json') == manifest_sha
          and base['sha'](stage / 'execution_lease.json') == lease_sha,
          'Original native manifest/lease changed; preserve evidence')
    result = {'request': request, 'certainty': 'terminal', 'returncode': returncode,
              'pid': process.pid, 'command': command, 'captured_file_hashes': captured,
              'fault_localization_only': True, 'admission_evidence': False,
              'comparable_resource_or_latency_evidence': False}
    base['write'](stage / 'crash_probe_completed.json', result)
    return result


def dispatch(operation, payload):
    check(socket.gethostname() == 'dl04-MS-7E06', 'Pinned server4 hostname required')
    check(operation in ('run_crash_probe', 'reconcile_crash_probe'), 'Default deny')
    base = helpers(payload)
    return run(payload, base) if operation == 'run_crash_probe' else reconcile(payload, base)
