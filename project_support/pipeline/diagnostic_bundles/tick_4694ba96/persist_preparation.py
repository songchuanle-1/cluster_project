"""Persist reviewed CTS preparation and fresh protected-job resource evidence."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import ast
import copy
import hashlib
import json
import os
import subprocess
import sys
from anchor_bfc_packet import guard

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
CTS = 'hierarchy-parent-cyclic-triadic-state-composition'
BFC = 'hierarchy-parent-butterfly-token-composition'
TOKEN = '4694ba96c2da476291160b2883ce3c7a'

def read(path):
    return json.loads(Path(path).read_text('utf-8'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def ref(path):
    path = Path(path).resolve()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}

def atomic(path, value):
    tmp = path.with_name(path.name + '.' + TOKEN + '.tmp')
    with tmp.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(tmp, path)

def add(candidate, paths):
    for path in paths:
        entry = ref(path)
        if entry not in candidate['evidence']:
            candidate['evidence'].append(entry)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', required=True)
    parser.add_argument('--review-sha', required=True)
    args = parser.parse_args()
    owner = guard()
    packet = HERE / 'cts_native_prepare'
    preparation = packet / 'preparation.json'
    review_path = Path(args.review).resolve()
    assert review_path.is_relative_to(HERE) and sha(review_path) == args.review_sha
    review = read(review_path)
    assert review['material_concerns'] == []
    assert review['anchors']['preparation'] == ref(preparation)
    guard_review_path = HERE / 'cts_native_guard_review.json'
    guard_review = read(guard_review_path)
    assert guard_review['material_concerns'] == []
    assert guard_review['anchors']['preparation'] == ref(preparation)
    prep = read(preparation)
    assert prep['candidate_id'] == CTS and prep['experiment_id'] == 'M214-CTS'
    assert prep['code_commit'] is None and prep['source_commit'] is None
    assert prep['draft_execution_disabled'] is True
    assert prep['native'] == prep['resources'] == 'NOT_RUN'
    assert all(value is None for value in prep['manifest_execution_fields'].values())
    validation_ref = prep['static_validation']
    validation_path = Path(validation_ref['path'])
    if not validation_path.is_absolute():
        validation_path = (ROOT if validation_ref['path'].startswith('pipeline/') else packet) / validation_path
    validation_path = validation_path.resolve()
    assert validation_path.is_relative_to(packet) and sha(validation_path) == validation_ref['sha256']
    validation = read(validation_path)
    assert validation['status'] == 'STATIC_CHECKS_PASSED_NATIVE_NOT_RUN' and validation['failed_checks'] == []
    for name, digest in prep['prepared_file_hashes'].items():
        path = (packet / name).resolve()
        assert path.is_relative_to(packet) and sha(path) == digest
    runtime = ast.parse((packet / 'native_runtime.py').read_text('utf-8'))
    switches = [node.value.value for node in runtime.body
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                and any(isinstance(t, ast.Name) and t.id == 'DRAFT_EXECUTION_DISABLED' for t in node.targets)]
    assert switches == [True]
    assert not any((packet / name).exists() for name in ['native_manifest.json', 'execution_lease.json', 'execution_binding.json'])
    source = ROOT / 'pipeline/diagnostic_bundles/tick_3824d9c9/new_candidate_prepare/preparation.json'
    assert sha(source) == 'bfab01a31a0fc7a0d679156d5e0e6fcfa987e56e5f3bb1bdf6bded9e2208f76e'
    sp = read(source)
    for entry in sp['source_files']:
        assert sha(source.parent / entry['prepared_path']) == entry['sha256']
    availability = HERE / 'bfc_native_resource_availability.json'
    assert read(availability)['owner_token'] == TOKEN
    assert read(availability)['result'] == 'blocked'
    boundary = HERE / 'progress_and_boundary_review.json'
    assert read(boundary)['material_concerns'] == []
    assert not any((ROOT / 'pipeline/admissions' / (eid + '.json')).exists() for eid in ['M213-BFC', 'M214-CTS'])
    git = ['git', '-C', str(ROOT / 'Cluster')]
    assert subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip() == '11a811618179ab1ddc0cee299194667413b7fdb9'
    before_status = subprocess.check_output(git + ['status', '--porcelain=v1', '--untracked-files=all'])
    assert len(before_status.splitlines()) == 28
    assert not subprocess.check_output(git + ['diff', '--cached', '--name-only']).strip()
    sys.path.insert(0, str(SKILL))
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        protected = ['queue.json', 'running.json', 'experiments/M211-BTC.json', 'experiments/M212-BCR.json', 'experiments/M206-CGCA.json', 'admissions/M211-BTC.json', 'admissions/M212-BCR.json']
        before = {name: sha(ROOT / 'pipeline' / name) for name in protected}
        work = read(ROOT / 'pipeline/research_work.json')
        cts = next(c for c in work['candidates'] if c['id'] == CTS)
        bfc = next(c for c in work['candidates'] if c['id'] == BFC)
        assert cts['stage'] == 'implementation' and cts['code_commit'] is None and cts['future_version_parent'] is None
        assert bfc['stage'] == 'validation' and bfc['code_commit'] == '48fc302c3c02ffef0b241be3593c386b6b65a72e'
        assert cts['native_execution_code_commit'] is None and bfc['native_execution_code_commit'] is None
        cts.setdefault('execution_preparation_history', []).append(copy.deepcopy(cts['worker_preparation']))
        cts['worker_preparation'] = {'status': 'PREPARED_DISABLED_INDEPENDENTLY_REVIEWED_VERSION_AND_NATIVE_PENDING',
            'preparation': ref(preparation), 'worker': ref(packet / 'worker.py'), 'runtime': ref(packet / 'native_runtime.py'),
            'manifest_template': ref(packet / 'manifest_template.json'), 'independent_review': ref(review_path),
            'independent_guard_review': ref(guard_review_path),
            'source_commit': None, 'source_parent_commit': None,
            'native_backward_executed': False, 'resource_profile_executed': False,
            'native_backward_passed': False, 'resources_passed': False,
            'active_native_manifest_or_execution_lease_created': False}
        cts['implementation_status'] = 'FROZEN_SOURCE_AND_DISABLED_NATIVE_TOOLS_REVIEWED_VERSION_AND_ACTUAL_NATIVE_PENDING'
        cts['native_status'] = 'NOT_RUN_VERSION_AND_GUARDED_OPERATIONAL_BINDING_PENDING_BOTH_CARDS_BUSY'
        cts['next_action'] = 'BFC remains first for native validation. Preserve exact CTS9/model/YAML and reviewed disabled worker. At native readiness choose compatible actual current main parent and bind the exact frozen source version; independently review a guarded operational copy with fresh owner/context/original deadline, whitelist/UUID/idle/three locks/assets/runtime. Run original paired M95/CTS TRAIN2 with actual three-distinct/multi-round/dilation and all3 W input-block original-loss gradients and updates, then original resource pair. Real passing results alone permit receipt/queue/safe sync/verified training. Never reuse preparation as a lease or alter data/seed/schedule/thresholds, oldholds, protected jobs or M206 pause.'
        fresh_paths = [HERE / 'btc_progress_observation.json', HERE / 'bcr_progress_observation.json', boundary, availability]
        for candidate in [bfc, cts]:
            add(candidate, fresh_paths)
            candidate['resource_wait']['current_observation'] = ref(availability)
            candidate['resource_wait']['observed_at'] = read(availability)['recorded_at']
        add(bfc, [HERE / 'bfc_actual_local_guard_integration.json'])
        add(cts, [preparation, review_path, guard_review_path, validation_path, HERE / 'cts_protocol_mapping_review.json'])
        for short, eid in [('btc', 'M211-BTC'), ('bcr', 'M212-BCR')]:
            candidate = next(c for c in work['candidates'] if c.get('experiment_id') == eid)
            add(candidate, [HERE / (short + '_progress_observation.json'), boundary])
        work['tick_attempt'] = {'tick_started_at': owner['generated_at'], 'candidate_id': CTS,
            'kind': 'implementation_test', 'result': 'passed',
            'command': 'python -B -X utf8 ' + str(packet / 'static_check.py') + ' --output ' + validation_path.name,
            'observation': 'Actual local disabled-native packet checks and independent review completed. This tests syntax, observers and fail-closed execution controls only; no Torch/native data/backward/resource profile, source version, admission or training occurred. Both authorized cards are occupied by protected original jobs.',
            'evidence': [ref(validation_path), ref(review_path), ref(guard_review_path)]}
        work['updated_at'] = datetime.now(timezone.utc).isoformat()
        work['next_action'] = bfc['next_action']
        guard(); atomic(ROOT / 'pipeline/research_work.json', work)
        assert before == {name: sha(ROOT / 'pipeline' / name) for name in protected}
        assert subprocess.check_output(git + ['status', '--porcelain=v1', '--untracked-files=all']) == before_status
        with (HERE / 'native_preparation_registration.json').open('x', encoding='utf-8') as stream:
            json.dump({'recorded_at': datetime.now(timezone.utc).isoformat(), 'token': TOKEN,
                       'candidate_id': CTS, 'new_candidates': 0, 'new_admissions': 0, 'new_launches': 0,
                       'preparation': ref(preparation), 'independent_review': ref(review_path),
                       'resource_availability': ref(availability), 'source_and_future_parent_null': True,
                       'protected_tasks_receipts_and_pause_unchanged': True, 'native_resources': 'NOT_RUN',
                       'postflight': 'NOT_YET_CALLED'}, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        print(json.dumps({'status': 'REVIEWED_DISABLED_CTS_NATIVE_TOOLS_REGISTERED_NO_NEW_CANDIDATE_OR_TRAINING', 'preparation': ref(preparation)}))
    finally:
        lock.close()

if __name__ == '__main__':
    main()
