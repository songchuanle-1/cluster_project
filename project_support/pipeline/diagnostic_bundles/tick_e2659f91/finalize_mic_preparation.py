"""Register actual MIC preparation/resource check and close this tick's research records."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter
import sys, copy, json
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
CID = 'hierarchy-ancestry-mobius-interaction-composition'

def main():
    if sys.argv[1:] != ['--execute-root']:
        print('DEFAULT_NOP')
        return
    guard()
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        b = u.read(HERE / 'protected_assets_before.json')
        u.protect(b)
        pins = u.read(HERE / 'closure_input.json')['pins']
        for name, h in pins.items():
            assert sha(HERE / name) == h
        peer = u.read(HERE / 'mic_native_and_operational_independent_review.json')
        assert peer['material_concerns'] == []
        version = u.read(HERE / 'mic_version_prepare/isolated_source_version.json')
        native = u.read(HERE / 'mic_native_prepare/preparation.json')
        op = u.read(HERE / 'mic_operational_prepare/preparation.json')
        assert version['code_commit'] == native['code_commit'] == op['code_commit'] == '041b63579888f2143cb9f3a5216ec4cff4ee8046' and version['parent_commit'] == b['head']
        for directory, prep in [(HERE / 'mic_native_prepare', native), (HERE / 'mic_operational_prepare', op)]:
            for name, h in prep['prepared_file_hashes'].items():
                assert sha(directory / name) == h
        assert native['draft_execution_disabled'] is op['draft_execution_disabled'] is True and native['operational_ready'] is op['operational_ready'] is False
        gpu = u.read(HERE / 'mic_gpu_precondition_observation.json')
        observed = datetime.fromisoformat(gpu['observation']['observed_at'])
        assert gpu['returncode'] == 0 and gpu['result'] == 'blocked' and (gpu['idle_gpu_ids'] == []) and (gpu['busy_gpu_ids'] == [0, 1]) and (datetime.now(timezone.utc) - observed < timedelta(minutes=5))
        assert u.read(HERE / 'mic_root_packet_integration_result.json')['passed'] is True
        work = u.read(ROOT / 'pipeline/research_work.json')
        assert sha(ROOT / 'pipeline/research_work.json') == b['research_work_sha256']
        assert {c['id']: u.digest(c) for c in work['candidates']} == b['candidate_digests']
        c = next((c for c in work['candidates'] if c['id'] == CID))
        assert c['stage'] == 'implementation' and c['code_commit'] is None and (c['source_commit'] is None)
        prior = copy.deepcopy(c)
        refs = [u.ref(HERE / name) for name in pins]
        refs.extend([native['static_validation'], native['source_version_binding'], op['metadata_validation']])
        for e in refs:
            assert sha(ROOT / e['path']) == e['sha256']
            if e not in c['evidence']:
                c['evidence'].append(e)
        c['source_version_history'] = [{'recorded_at': datetime.now(timezone.utc).isoformat(), 'prior_source_commit': None, 'prior_code_commit': None, 'prior_source_parent_commit': None, 'original_source_preparation': c['source_preparation'], 'saved_isolated_source_version': u.ref(HERE / 'mic_version_prepare/isolated_source_version.json'), 'prototype_original_NULL_metadata_unchanged': True, 'model_revision': False}]
        c.update(stage='validation', code_commit=version['code_commit'], source_commit=version['code_commit'], source_parent_commit=version['parent_commit'], future_version_parent=version['parent_commit'], source_version=u.ref(HERE / 'mic_version_prepare/isolated_source_version.json'), source_version_status='EXACT9_COMPATIBLE_ISOLATED_VERSION_SAVED_NOT_PROMOTED', independent_source_version_review=u.ref(HERE / 'mic_actual_source_version_independent_review.json'), implementation_status='SOURCE_VERSION_AND_DRAFT_DIAGNOSTIC_SOFTWARE_VERIFIED_NATIVE_NOT_RUN', native_status='NOT_RUN', resource_status='NOT_RUN', Torch_FP32_autograd='NOT_RUN', queued=False, scientific_admission=False)
        c['worker_preparation'] = {'status': 'SOURCE_BOUND_DISABLED_DRAFT_SOFTWARE_REVIEWED_NOT_NATIVE', 'preparation': u.ref(HERE / 'mic_native_prepare/preparation.json'), 'draft_execution_disabled': True, 'operational_ready': False, 'native_backward_executed': False, 'resource_profile_executed': False, 'native_backward_passed': None, 'resources_passed': None, 'active_native_manifest_or_execution_lease_created': False, 'independent_review': u.ref(HERE / 'mic_native_and_operational_independent_review.json')}
        c['execution_adapter'] = {'status': 'SOURCE_BOUND_DISABLED_OPERATIONAL_DRAFT_NOT_EXECUTED', 'preparation': u.ref(HERE / 'mic_operational_prepare/preparation.json'), 'native_preparation': u.ref(HERE / 'mic_native_prepare/preparation.json'), 'release_template': op['release_template'], 'release': None, 'draft_execution_disabled': True, 'operational_ready': False, 'remote_adapter_execution_tested': False, 'native_execution_tested': False, 'active_binding_manifest_lease_created': False, 'transport_executed': False, 'standard_summaries_created': False, 'independent_review': u.ref(HERE / 'mic_native_and_operational_independent_review.json')}
        c['implementation_test_history'] = [copy.deepcopy(prior.get('implementation_test'))]
        c['implementation_test'] = {'result': 'passed', 'command': native['static_check_command'], 'scope': '43 actual author software checks plus independently reviewed source/native/adapter draft and root default-NOP cross-integration; no native or resource pass.', 'evidence': [native['static_validation'], u.ref(HERE / 'mic_root_packet_integration_result.json'), u.ref(HERE / 'mic_native_and_operational_independent_review.json')]}
        c['native_execution_blocker'] = {'kind': 'occupied_authorized_gpus', 'server': 'server-4', 'observed_at': observed.isoformat(), 'busy_gpu_ids': [0, 1], 'original_tasks': ['M226-WFC', 'M227-LFT'], 'evidence': u.ref(HERE / 'mic_gpu_precondition_observation.json'), 'scope': 'Physical resource precondition only; not failed backward, resource budget, human permission or scientific rejection.'}
        c['retry_after'] = (observed + timedelta(hours=1)).isoformat()
        c['unblock_condition'] = 'An authorized server4 physical GPU is genuinely idle, original task/uncertain canonical reservations naturally clear, fresh owner/runtime/source/native assets and exclusive locks verify; root reviewed activation and same native protocol then allowed under existing project authorization.'
        c['next_action'] = 'When an authorized card is genuinely idle, preserve frozen drafts and materialize reviewed active copies with fresh actual owner/deadline/source/runtime/UUID and current producer hashes under existing project authorization; no extra human permission. This draft selects1; an idle0 needs only reviewed GPU metadata port, not resource expansion. Run unchanged original paired natural TRAIN2 and original full resources on source6bc only while runtime4457 remains exact; if main changes first save/rebind same9 compatibly, never blindly ff a sibling. Actual PASS plus result independence then admit/queue/dispatch this tick. No request/lease/raw/receipt exists yet; no replay or borrowed result.'
        now = datetime.now(timezone.utc).isoformat()
        oldattempt = work.get('tick_attempt')
        if oldattempt and oldattempt.get('tick_started_at') != EXPECTED['generated_at']:
            work.setdefault('tick_attempt_history', []).append(oldattempt)
        work['tick_attempt'] = {'tick_started_at': EXPECTED['generated_at'], 'candidate_id': CID, 'kind': 'resource_check', 'result': 'blocked', 'command': 'python -B -X utf8 ' + str(HERE / 'check_mic_gpu_precondition.py') + ' --execute-root', 'observation': 'Actual pinned hostname/physical0+1 UUIDs and both original PID/start identities verified; NVML has no idle card. MIC native/model/resources not entered, no signal or eviction. Source/version/software progress recorded separately.', 'evidence': [u.ref(HERE / 'mic_gpu_precondition_observation.json')]}
        work['updated_at'] = now
        assert len(work['candidates']) == 155 and all((u.digest(x) == b['candidate_digests'][x['id']] for x in work['candidates'] if x['id'] != CID))
        u.protect(b)
        u.atomic(ROOT / 'pipeline/research_work.json', work)
        sections = u.read(HERE / 'closure_input.json')['sections']
        memory = '# Codex Research Memory\n\n' + '\n\n'.join(('## ' + h + '\n' + '\n'.join(('- ' + s for s in rows)) for h, rows in sections.items())) + '\n'
        assert len(sections) == 7 and len(memory.splitlines()) < 120
        path = ROOT / 'pipeline/codex_memory.md'
        temp = path.with_name(path.name + '.e2659f91.tmp')
        assert not temp.exists()
        guard()
        temp.write_text(memory, encoding='utf8')
        guard()
        temp.replace(path)
        notes = u.read(HERE / 'closure_input.json')['notes']
        u.save(HERE / 'final_report_notes.json', notes)
        state = {'owner': EXPECTED, 'recorded_at': now, 'candidate_stage_counts': dict(Counter((x['stage'] for x in work['candidates']))), 'source_commit': version['code_commit'], 'main_HEAD_unchanged': b['head'], 'new_candidates': 0, 'model_revisions': 0, 'new_native_arms': 0, 'new_admissions': 0, 'new_formal_runs': 0, 'new_formal_terminals': 0, 'source_isolated_versions_saved': 1, 'tick_attempt': work['tick_attempt'], 'protected_other154_candidates': True, 'protected_user28_original18_source_and38_lifecycle': True, 'work_sha256': sha(ROOT / 'pipeline/research_work.json'), 'memory_sha256': sha(path), 'notes': u.ref(HERE / 'final_report_notes.json'), 'bound_artifacts': refs, 'foreground_finish': 'NOT_YET_RUN'}
        u.save(HERE / 'preclosure_actual_state.json', state)
        u.protect(b)
        print(json.dumps({'status': 'MIC_PREPARATION_AND_ACTUAL_RESOURCE_BLOCK_RECORDED_FINISH_PENDING', 'state': u.ref(HERE / 'preclosure_actual_state.json'), 'notes': state['notes'], 'stage_counts': state['candidate_stage_counts'], 'memory_lines': len(memory.splitlines())}, ensure_ascii=False))
    finally:
        lock.close()
if __name__ == '__main__':
    main()
