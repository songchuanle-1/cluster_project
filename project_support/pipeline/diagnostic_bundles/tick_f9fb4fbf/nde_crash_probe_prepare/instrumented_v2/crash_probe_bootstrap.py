"""Default-denied SIGSEGV localization around the exact original NDE worker.

Only stdlib before original entry. No CUDA/RNG/precision/model/protocol changes.
The instrumented invocation is fault localization, never comparable resources.
"""
import argparse
import builtins
from datetime import datetime, timezone
import faulthandler
import hashlib
import json
import os
from pathlib import Path
import runpy
import socket
import sys
import time

DRAFT_DIAGNOSTIC_DISABLED = True
WORKER_SHA256 = 'b37fe5cf29ce04b8110752c7321d34b8d1a26218a6d8e02940b5773d9e4d5f72'
RUNTIME_SHA256 = '348024f11e6a106788840c1359ad8c65363914d1f1882cfe4a5f8d319d5ea1a4'
SOURCE = '0747f6acec1c61018ec99acf2efa5329c9b3523c'
RUNTIME_SOURCE = 'f6257de79148581334ee495e6e2d60ccb525457c'
ROOT = '/data/songcl/Project/Cluster_project/Cluster_nsd_20261107'
PARENT = Path('/data/songcl/Project/Cluster_project/pipeline')
UUID = 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
OWNER_KEYS = ('token', 'thread_id', 'generated_at', 'deadline_at',
              'context_sha256', 'pending_sha256')
SELECTED_IMPORTS = ('torch', 'numpy', 'gorilla', 'tools.train',
                    'framework', 'pointops', 'spconv')


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def validate_request(path):
    require(not DRAFT_DIAGNOSTIC_DISABLED, 'DRAFT_CRASH_PROBE_DISABLED')
    stage = Path(__file__).resolve().parent
    request_path = Path(path).resolve()
    require(request_path.parent == stage, 'Request must be in exact staged directory')
    request = read(request_path)
    require(request['operation'] == 'candidate_resources_fault_localization'
            and request['fault_localization_only'] is True
            and request['admission_evidence'] is False
            and request['comparable_resource_or_latency_evidence'] is False,
            'Explicit non-admitting fault-localization request required')
    owner = request['owner']
    require(set(owner) == set(OWNER_KEYS) and owner['thread_id'] == THREAD,
            'Exact current-owner provenance required')
    require(stage == PARENT / ('nde_' + owner['token'][:8] + '_gpu0'),
            'Fresh current-owner stage required')
    now = datetime.now(timezone.utc)
    generated, deadline = (datetime.fromisoformat(owner[key])
                           for key in ('generated_at', 'deadline_at'))
    require(generated <= now < deadline
            and 300 < (deadline - now).total_seconds() <= 3600,
            'Fresh unexpired original lease required')
    require(socket.gethostname() == 'dl04-MS-7E06', 'Actual server4 identity required')
    require(sys.dont_write_bytecode
            and os.environ.get('PYTHONDONTWRITEBYTECODE') == '1', 'python -B required')
    manifest_path, lease_path = stage / 'native_manifest.json', stage / 'execution_lease.json'
    manifest, lease = read(manifest_path), read(lease_path)
    require(sha(manifest_path) == request['native_manifest_sha256']
            == lease['native_manifest_sha256']
            and sha(lease_path) == request['execution_lease_sha256'],
            'Actual manifest/lease/request hashes disagree')
    require(manifest['project'] == lease['project'] == 'cluster_project'
            and manifest['server_id'] == lease['server_id'] == 'server-4'
            and manifest['root'] == ROOT and manifest['stage'] == str(stage)
            and manifest['code_commit'] == SOURCE
            and manifest['runtime_code_commit'] == RUNTIME_SOURCE
            and manifest['physical_gpu'] == lease['physical_gpu'] == 0
            and manifest['gpu_uuid'] == lease['gpu_uuid'] == UUID
            and manifest['allowed_gpus'] == lease['allowed_gpus'] == [0],
            'Original source/runtime/root/GPU0 contract required')
    require(all(lease[{'token': 'token', 'thread_id': 'thread_id',
                      'generated_at': 'generated_at', 'deadline_at': 'deadline_at',
                      'context_sha256': 'context_sha256',
                      'pending_sha256': 'pending_sha256'}[key]] == owner[key]
                for key in OWNER_KEYS), 'Lease current owner mismatch')
    require(manifest['current_token'] == owner['token']
            and manifest['tick_generated_at'] == owner['generated_at']
            and manifest['deadline_at'] == owner['deadline_at']
            and manifest['context_sha256'] == owner['context_sha256']
            and manifest['pending_sha256'] == owner['pending_sha256'],
            'Manifest current owner mismatch')
    bootstrap = Path(__file__).resolve()
    require(sha(bootstrap) == request['bootstrap_sha256']
            == manifest['diagnostic_files'][bootstrap.name]
            and sha(stage / 'worker.py') == request['worker_sha256'] == WORKER_SHA256
            == manifest['diagnostic_files']['worker.py']
            and sha(stage / 'native_runtime.py') == request['runtime_sha256'] == RUNTIME_SHA256
            == manifest['diagnostic_files']['native_runtime.py'],
            'Reviewed bootstrap and exact original worker/runtime bytes required')
    review_path = stage / request['independent_review_file']
    require(review_path.resolve().parent == stage
            and sha(review_path) == request['independent_review_sha256']
            == manifest['diagnostic_files'][review_path.name],
            'Independent reviewed diagnostic-file extension required')
    review = read(review_path)
    require(review['passed'] is True
            and review['bootstrap_sha256'] == request['bootstrap_sha256']
            and review['owner'] == owner and review['fault_localization_only'] is True,
            'Independent current-owner probe review missing')
    expected_argv = [str(stage / 'worker.py'), '--lease', str(lease_path),
                     '--mode', 'resources', '--target', 'candidate']
    require(request['original_worker_argv'] == expected_argv,
            'Original native worker candidate/resources argv required')
    return stage, request, expected_argv


def observe_entry(worker, argv, stream):
    """Passthrough instrumentation with at most64 flushed JSON markers."""
    old_import, old_profile, old_argv = builtins.__import__, sys.getprofile(), sys.argv
    require(old_profile is None, 'Do not replace an existing profiler')
    markers, selected_seen, depth = [], set(), 0

    def marker(phase, **extra):
        if len(markers) >= 64:
            return
        value = {'ordinal': len(markers), 'phase': phase,
                 'utc': datetime.now(timezone.utc).isoformat(),
                 'monotonic_ns': time.monotonic_ns(), **extra}
        markers.append(value)
        stream.write(json.dumps(value, allow_nan=False) + '\n')
        stream.flush()

    def selected(name, fromlist):
        for target in SELECTED_IMPORTS:
            if name == target or (target == 'tools.train' and name == 'tools'
                                   and fromlist and 'train' in fromlist):
                return target
        return None

    def observed_import(name, globals=None, locals=None, fromlist=(), level=0):
        nonlocal depth
        target = selected(name, fromlist)
        observe = target is not None and target not in selected_seen
        if observe:
            selected_seen.add(target)
            marker('selected_import_enter', module=target)
            depth += 1
        try:
            result = old_import(name, globals, locals, fromlist, level)
        except BaseException as error:
            if observe:
                marker('selected_import_exception', module=target,
                       error_type=type(error).__name__)
            raise
        else:
            if observe:
                marker('selected_import_return', module=target)
            return result
        finally:
            if observe:
                depth -= 1

    def profile(frame, event, arg):
        if event in ('call', 'return') and frame.f_code.co_filename == str(worker):
            if frame.f_code.co_name in ('setup', 'resources'):
                marker('original_worker_' + frame.f_code.co_name + '_' + event)
        return None

    marker('original_entry_before', instrumented=True, fault_localization_only=True,
           original_worker_resources_function_unchanged=True,
           comparable_resources_or_latency_evidence=False, technical_admission_evidence=False,
           original_worker_argv=argv,
           original_entry_sha256=sha(worker), bootstrap_sha256=sha(__file__),
           interpreter=sys.executable, interpreter_flags=str(sys.flags),
           launcher_orig_argv=getattr(sys, 'orig_argv', None),
           faulthandler_enabled=faulthandler.is_enabled(),
           use='FAULT_LOCALIZATION_ONLY_NOT_COMPARABLE_RESOURCES_OR_ADMISSION')
    try:
        builtins.__import__ = observed_import
        sys.setprofile(profile)
        sys.argv = list(argv)
        result = runpy.run_path(str(worker), run_name='__main__')
        marker('original_entry_after')
        return result
    except BaseException as error:
        marker('original_entry_exception', error_type=type(error).__name__)
        raise
    finally:
        builtins.__import__ = old_import
        sys.setprofile(old_profile)
        sys.argv = old_argv
        marker('passthrough_hooks_restored')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--diagnostic-request')
    args = parser.parse_args()
    require(args.diagnostic_request is not None, 'DEFAULT_DENY_EXPLICIT_REVIEWED_REQUEST_REQUIRED')
    stage, request, argv = validate_request(args.diagnostic_request)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(line_buffering=True)
    # Keep the native fault signal behavior: faulthandler records then re-raises.
    faulthandler.enable(file=sys.stderr, all_threads=True)
    with (stage / 'fault_localization_markers.jsonl').open('x', encoding='utf-8',
                                                         buffering=1) as markers:
        observe_entry(stage / 'worker.py', argv, markers)


if __name__ == '__main__':
    main()
