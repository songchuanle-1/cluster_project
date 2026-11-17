"""Current-owner read-only server4 byte, identity, process, lock and resource proof."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OWNER = json.loads((HERE / 'current_owner_binding.json').read_text(encoding='utf-8'))
assert OWNER['token'] == 'c1fe217800894083b65baac45f79aa83'
assert OWNER['thread_id'] == '01a159c5-29ab-7a22-ba7f-e79174757253'
assert datetime.now(timezone.utc) < datetime.fromisoformat(OWNER['deadline_at'])
assert sys.dont_write_bytecode

def digest(data):
    return hashlib.sha256(data).hexdigest()

paths = {
    'previous_observation': 'pipeline/diagnostic_bundles/tick_7caf419d/runtime_readiness.actual.json',
    'previous_producer': 'pipeline/diagnostic_bundles/tick_7caf419d/runtime_readiness_probe.py.txt',
    'environment': 'pipeline/diagnostic_bundles/tick_91c85c42/cso_native_bound/environment_binding.json',
    'source_binding': 'pipeline/diagnostic_bundles/tick_91c85c42/cso_native_bound/source_binding.template.json',
    'manifest': 'pipeline/diagnostic_bundles/tick_91c85c42/cso_native_bound/manifest_template.json',
}
sources = {key: (ROOT / value).read_bytes() for key, value in paths.items()}
references = {key: {'path': value, 'sha256': digest(sources[key])} for key, value in paths.items()}
previous = json.loads(sources['previous_observation'])
for binding in previous['historical_binding_inputs']:
    assert digest((ROOT / binding['path']).read_bytes()) == binding['sha256']

body = sources['previous_producer'].decode('utf-8').replace(
    "assert owner['token'] == '7caf419d15d145459592faa2810e3776'",
    "assert owner['token'] == 'c1fe217800894083b65baac45f79aa83'\nassert owner['thread_id'] == '01a159c5-29ab-7a22-ba7f-e79174757253'"
)
# Preserve the reviewed read-only producer, but make current packet cardinality explicit.
body = body.replace('files = []\n', "assert len(expected) == 18\nfiles = []\n")
body = body.replace("'runtime_HEAD':head,'source_environment_assets_verified':True,'files':files,", "'runtime_HEAD':head,'source_environment_assets_verified':True,'source_environment_assets_verified_count':len(files),'files':files,")
assert body.count('c1fe217800894083b65baac45f79aa83') == 1
assert '7caf419d15d145459592faa2810e3776' not in body
assert 'torch' not in sys.modules
body_bytes = body.encode('utf-8')
(HERE / 'runtime_readiness_probe.py.txt').write_bytes(body_bytes)
packet = {
    'owner': OWNER,
    'environment': json.loads(sources['environment']),
    'manifest': json.loads(sources['manifest']),
}
packet_bytes = json.dumps(packet, sort_keys=True).encode('utf-8')
(HERE / 'runtime_readiness.packet.json').write_bytes(packet_bytes)
ssh = [
    'ssh', '-T', '-o', 'BatchMode=yes', '-o', 'PasswordAuthentication=no',
    '-o', 'KbdInteractiveAuthentication=no', '-o', 'StrictHostKeyChecking=yes',
    '-o', 'ConnectTimeout=8', '-o', 'ConnectionAttempts=1',
    '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=2',
    'songcl@192.168.1.115',
    '/usr/bin/python3 -I -B -c ' + shlex.quote(body),
]
record = {
    'owner': OWNER,
    'kind': 'READ_ONLY_RUNTIME_SOURCE_ENVIRONMENT_RESOURCE_READINESS',
    'started_at': datetime.now(timezone.utc).isoformat(),
    'producer': {'path': str(Path(__file__).resolve().relative_to(ROOT)).replace('\\', '/'),
                 'sha256': digest(Path(__file__).read_bytes())},
    'body_sha256': digest(body_bytes),
    'packet_sha256': digest(packet_bytes),
    'historical_binding_inputs': previous['historical_binding_inputs'],
    'historical_provenance': references,
    'previous_owner_preserved': previous['owner'],
    'current_observation_claim': 'Fresh remote byte hashes and current read-only resource/process/lock observations; historical success is not carried forward.',
    'Torch_imported': False,
    'GPU_compute': False,
    'signals_sent': False,
    'remote_mutations': False,
    'passed': False,
    'certainty': 'unknown',
}
stdout = b''
stderr = b''
try:
    process = subprocess.Popen(ssh, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    record['local_ssh_pid'] = process.pid
    try:
        stdout, stderr = process.communicate(packet_bytes, timeout=90)
    except subprocess.TimeoutExpired as error:
        record['error'] = 'Read-only SSH uncertain; process preserved without signal; no automatic retry.'
        record['preserved_local_ssh_pid'] = process.pid
        stdout = error.output or b''
        stderr = error.stderr or b''
    else:
        record['returncode'] = process.returncode
        if process.returncode == 0:
            observation = json.loads(stdout)
            assert observation['owner'] == OWNER
            assert observation['source_environment_assets_verified_count'] == 18
            assert len(observation['files']) == len(previous['observation']['files']) == 18
            assert {(f['path'], f['expected_sha256']) for f in observation['files']} == {
                (f['path'], f['expected_sha256']) for f in previous['observation']['files']}
            assert all(f['matches'] and f['read_stable'] for f in observation['files'])
            record['observation'] = observation
            record['certainty'] = 'terminal'
            record['passed'] = observation['readiness_passed'] is True
        else:
            record['error'] = 'Fresh read-only remote probe failed; no readiness PASS inferred.'
except Exception as error:
    record['error'] = type(error).__name__ + ': ' + str(error)
finally:
    record['stdout_sha256'] = digest(stdout)
    record['stderr_sha256'] = digest(stderr)
    record['stderr_tail'] = stderr.decode('utf-8', 'replace')[-3000:]
    record['completed_at'] = datetime.now(timezone.utc).isoformat()
    record['completed_before_deadline'] = datetime.now(timezone.utc) < datetime.fromisoformat(OWNER['deadline_at'])
    if not record['completed_before_deadline']:
        record['passed'] = False
        record['certainty'] = 'expired'
    (HERE / 'runtime_readiness.transport.stdout').write_bytes(stdout)
    (HERE / 'runtime_readiness.transport.stderr').write_bytes(stderr)
    output = HERE / 'runtime_readiness.actual.json'
    output.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'path': str(output), 'sha256': digest(output.read_bytes()), 'passed': record['passed'],
                      'certainty': record['certainty'], 'error': record.get('error'),
                      'completed_at': record['completed_at']}))

