"""Classify fresh read-only hardware observations without another GPU query."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
from anchor_bfc_packet import guard

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text('utf-8'))

def ref(path):
    return {'path': path.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    owner = guard()
    expected = [('btc', 'M211-BTC', 0, 2784474, '47557208',
                 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),
                ('bcr', 'M212-BCR', 1, 1215422, '51717921',
                 'GPU-7f82edb9-f620-8045-caea-a75232265cd1')]
    evidence, cards = [], []
    tasks = read(ROOT / 'pipeline/queue.json')['gpu_queues']['server-4']
    for short, eid, gpu, pid, start, uuid in expected:
        path = HERE / (short + '_progress_observation.json')
        proof = read(path)
        task = next(t for t in tasks if t['id'] == eid)
        assert proof['experiment'] == eid
        assert proof['same_exact_registered_process_and_native_TRAIN_growth'] is True
        assert task['status'] == 'running' and task['pid'] == pid
        assert task['launch_verified'] is True and str(task['gpu']) == str(gpu)
        samples = proof['observations']
        assert len(samples) == 2
        for sample in samples:
            stamp = datetime.fromisoformat(sample['observed_at'])
            assert datetime.fromisoformat(owner['generated_at']) <= stamp <= datetime.now(timezone.utc)
            data = sample['data']
            assert data['pid'] == pid and data['start_ticks'] == start
            assert data['state'] not in ('X', 'x', 'Z') and not data['errors']
            assert uuid in data['gpu' + str(gpu)]
            assert any(line.split(',')[0].strip() == str(pid)
                       for line in data['gpu' + str(gpu) + '_contexts'].splitlines())
        a, b = [s['data']['train_progress'] for s in samples]
        assert (b[0], b[2]) > (a[0], a[2])
        evidence.append(ref(path))
        cards.append({'physical_gpu': gpu, 'uuid': uuid, 'protected_experiment': eid,
                      'pid': pid, 'original_start_ticks': start,
                      'observed_native_train_progress': [a, b],
                      'safe_native_diagnostic_slot_available': False,
                      'reason': 'Original protected training process occupies this physical card; one task per GPU.'})
    no_transport = HERE / 'bfc_actual_local_guard_integration.json'
    proof = read(no_transport)
    assert proof['current_owner_token'] == owner['token']
    assert proof['actual_transport_calls'] == 0
    assert proof['active_binding_manifest_lease_or_execution_directory_created'] is False
    evidence.append(ref(no_transport))
    guard()
    result = {'recorded_at': datetime.now(timezone.utc).isoformat(),
              'candidate_id': 'hierarchy-parent-butterfly-token-composition',
              'experiment_id': 'M213-BFC', 'owner_token': owner['token'],
              'kind': 'resource_check', 'result': 'blocked',
              'status': 'ACTUAL_AUTHORIZED_CARDS_BUSY_WITH_PROTECTED_NATIVE_TRAINING',
              'observed_cards': cards, 'evidence': evidence,
              'new_GPU_queries': 0, 'diagnostic_compute': 'NOT_RUN',
              'native_backward': 'NOT_RUN', 'native_resources_profile': 'NOT_RUN',
              'execution_binding_manifest_or_lease_created': False,
              'next_action': 'After natural completion, archive the actual outcome and freshly verify owner, source, assets, whitelist, physical UUID, idle contexts and three locks before BFC original native checks. CTS follows; M206 stays paused.',
              'scope': 'Real current resource availability only; not candidate FLOPs, accuracy or a native PASS. No additional polling, preemption, shared-GPU overlay or old-lease reuse.'}
    output = HERE / 'bfc_native_resource_availability.json'
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'result': 'blocked',
                      'path': str(output), 'sha256': ref(output)['sha256']}))

if __name__ == '__main__':
    main()
