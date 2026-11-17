"""Read-only reconciliation and durable account of this tick's native work."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess

HERE = Path(__file__).resolve().parent
ADAPTER = HERE.parent / 'tick_42ce600b/psnc_operational_prepare/adapter.py'
EXECUTION = HERE / 'psnc_execution'

def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def main():
    assert os.environ['CODEX_THREAD_ID'] == '01a159c5-29ab-7a22-ba7f-e79174757253'
    owner = json.loads((HERE.parents[1] / 'headless/.foreground.lockdir/owner.json').read_text())
    assert owner['token'] == 'a4f7314098ed4dbd8351aa005661583d'
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    command = ['python', '-B', '-X', 'utf8', str(ADAPTER), 'status', '--execution-dir', str(EXECUTION)]
    process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=90)
    assert process.returncode == 0, process.stderr
    observation = json.loads(process.stdout)
    save(HERE / 'psnc_four_requests_readonly_reconcile.json', observation)
    requests = observation['remote']['requests']
    summary = []
    for name in ('smoke_champion', 'smoke_candidate', 'resources_champion', 'resources_candidate'):
        path = EXECUTION / (name + '_execution.json')
        result = json.loads(path.read_text())
        assert result['certainty'] == 'terminal' and result['returncode'] == 0
        assert result['result']['execution_completed'] is True
        summary.append({'arm': name, 'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'request_identity': result['identity'], 'certainty': result['certainty'],
                        'returncode': result['returncode']})
    record = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'token': owner['token'],
              'original_deadline_at': owner['deadline_at'], 'actual_operation_sequence': [
                  'probe GPU0; prepare fresh binding; stage verified',
                  'run_pair completed smoke_champion, then refused busy at next-arm probe before candidate request',
                  'read-only reconcile original champion request ad14828cebb34d00b3ac4b03d313840e: terminal/identity matched, workers empty and compute contexts empty',
                  'fresh probe 22:16:34UTC: GPU0 41MiB/util0/no contexts/three locks available',
                  'run only missing smoke_candidate; terminal/rc0, then fresh GPU0 probe',
                  'run only missing resources_champion; terminal/rc0, then fresh GPU0 probe',
                  'run only missing resources_candidate; terminal/rc0',
                  'read-only reconcile all original requests'],
              'completed_arms': summary, 'replayed_requests': False, 'busy_guard_bypassed': False,
              'signals_sent': False, 'GPU1': 'NOT_QUERIED_NOT_USED', 'deadline_extended': False,
              'reconcile_command': command,
              'current_remote_workers': observation['remote'].get('workers'),
              'current_compute_contexts': observation['remote'].get('compute_contexts'),
              'scientific_scope': 'Actual native smoke/resource executions; independent semantics and admission still separate.'}
    save(HERE / 'psnc_native_operation_history.json', record)
    print(json.dumps({'completed_arms': len(summary), 'original_request_records': len(requests),
                      'workers': record['current_remote_workers'], 'contexts': record['current_compute_contexts'],
                      'requests_replayed': False}, ensure_ascii=False))

if __name__ == '__main__':
    main()
