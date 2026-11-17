"""Scoped PCE recovery and preregistration; requires the current owner lease."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys

ROOT = Path('D:/project/cluster_project')
OUT = Path(__file__).resolve().parent
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
sys.path.insert(0, str(SKILL))
import closure
spec = importlib.util.spec_from_file_location('pce_current_ops', ROOT / 'pipeline/diagnostic_bundles/tick_fefdcc2a/control.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
c.TOKEN = 'a3495e4b780741f19b3c15cf3cb3c609'
c.THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
c.OUT = OUT
c.STAGE = '/data/songcl/Project/Cluster_project/pipeline/pce_a3495e4b'


def register():
    c.guard(1200)
    work = c.tick.load(ROOT / 'pipeline/research_work.json')
    candidate = next(item for item in work['candidates'] if item['id'] == c.CID)
    before = copy.deepcopy(candidate)
    assert len(candidate['revision_history']) == 2
    r2 = candidate['revision_history'][1]
    assert r2['result'] == 'pending'
    archive = copy.deepcopy(r2['evidence'])
    actual = c.tick.load(ROOT / 'pipeline/diagnostic_bundles/tick_3259705f/combined_candidate_result.json')
    assert actual['execution_completed'] and not actual['all_full_source_controls_passed']
    r2['result_evidence'] = [entry for entry in archive if Path(entry['path']).name in
        ('combined_candidate_result.json', 'analysis.json', 'static_independence.json')]
    assert len(r2['result_evidence']) == 3
    r2['result'] = 'failed'
    closure.validate_revisions(ROOT, candidate, before)
    assert r2['evidence'] == archive
    repaired = c.save('archival_classification.json', {
        'recorded_at': c.now(), 'candidate_id': c.CID,
        'previous_result_field': 'pending; actual tests failed', 'actual_result': 'failed',
        'all_archive_entries_preserved': True, 'timestamps_or_hashes_changed': False,
        'archive': archive, 'result_evidence': r2['result_evidence'],
        'maximum_full_source_error': actual['maximum_full_source_control_error'],
        'frozen_tolerance': 1e-6})
    permission = c.save('human_authorization.json', {
        'recorded_at': c.now(), 'scope': 'implementation_revision', 'authorization_granted': True,
        'candidate_id': c.CID, 'owner_thread_id': c.THREAD,
        'original_authorizing_thread_id': '01a04987-fdbe-7301-b2f0-f9b6ab60f74c',
        'original_user_turn_id': '01a1598b-5a9e-7b12-bac1-669ba9e2c6da',
        'human_reply': '你继续', 'human_reply_at': '2026-10-20T21:41:07+08:00',
        'verification': 'Original user turn inspected with read_thread; recovery handoff explicitly preserves this scoped authorization. Current user also requested continuation.',
        'request_evidence': c.evidence(ROOT / 'pipeline/diagnostic_bundles/tick_3259705f/pending_archival_repair_request.json'),
        'handoff': c.evidence(ROOT / 'pipeline/recovery_handoffs/20261020-224349/cluster-recovery.md'),
        'base_revision_count': 2, 'additional_revisions': 1,
        'goal_sha256': c.GOAL,
        'base_revision_history_sha256': closure.revision_digest(candidate['revision_history']),
        'allowed_changes': ['Contact-graph integer deduplication', 'Fixed feature aggregation reduction order'],
        'unchanged': ['FPS and memberships', 'attention formula', 'dtype/precision', '1e-6 control threshold',
            'all prior failures', 'seed1999/epochs50/max_iters70', 'scientific and resource gates'],
        'grants_commit_push_or_training_exception': False})
    candidate['implementation_revision_authorization'] = c.evidence(permission)
    package = ROOT / 'Cluster/framework/model/Quard_model' / (c.NAME + '_pce')
    expected = c.tick.load(ROOT / 'pipeline/diagnostic_bundles/tick_3259705f/native_manifest.json')['candidate_source_hashes']
    assert {p.name: c.tick.digest(p) for p in package.glob('*.py')} == expected
    archived = OUT / 'source_r2'
    archived.mkdir()
    for path in package.glob('*.py'):
        shutil.copyfile(path, archived / path.name)
    protocol = c.save('implementation_revision3.json', {
        'preregistered_at': c.now(), 'candidate_id': c.CID, 'revision': 3,
        'failure_scope': 'implementation',
        'reason': 'R2 full-source identity and transported-row controls fail at2.86102294921875e-6>1e-6; atomic hierarchy means can vary with schedule/order. R2 exact graph still expensive.',
        'change': 'Replace ONLY integer pair deduplication with checked int64 scalar keys; use deterministic segmented means for SharedClusterBank feature pooling, ordering level0 by physical xyz within each fixed cluster and coarser inputs by their existing token order; fix readback global mean order by physical xyz with original padded-width denominator. Pass current positions from encoder to the bank. Leave partitioner/FPS, attention, exchange operator, precision, cohort and thresholds unchanged.',
        'prediction': 'Integer graph arrays and original exchange outputs/input gradients remain exact. Full-bank repeats become stable; transported-row full encoder and deleted-contact parent controls must still satisfy frozen1e-6. Full predict median should decrease versusR2 without memory violation.',
        'known_risk': 'Encoder LIA attention also reduces over reordered point rows before the bank. Its unchanged floating-order behavior can still fail the full-source threshold; bank repair does not waive or explain away that failure.',
        'failure_evidence': [c.evidence(ROOT / 'pipeline/diagnostic_bundles/tick_3259705f/combined_candidate_result.json')],
        'authorization': c.evidence(permission), 'source_r2_hashes': expected,
        'tests': ['Exact native and cooccupied/multiowner/two-scene graphs',
            'Same8-expression original operator outputs/input gradients/row/delete/rotate controls',
            'Same two-scene/eight-expression full native hierarchy+encoder repeats/transported rows/deleted-parent controls',
            'Full native criterion backward; no optimizer step',
            'Same-standard M95 and candidate predict bs1 warmup20 repeat100 median/P90/FVCore/peak memory'],
        'tolerance': 1e-6, 'new_training': 0, 'optimizer_steps': 0,
        'no_further_revision_if_failed': True,
        'method_reference': 'https://pytorch-scatter.readthedocs.io/en/latest/functions/segment_csr.html'})
    p = c.tick.load(protocol)
    candidate['revision_history'].append({key: p[key] for key in
        ('revision', 'failure_scope', 'reason', 'change', 'prediction', 'preregistered_at', 'failure_evidence')})
    candidate['revision_history'][-1].update(result='pending', evidence=[c.evidence(protocol)])
    for path in (repaired, permission, protocol, Path(__file__)):
        candidate['evidence'].append(c.evidence(path))
    candidate['stage'] = 'implementation'
    candidate['next_action'] = 'Execute exactly the authorized final local revision3; preserve every original failed control; no additional revision or training exception.'
    candidate['scientific_admission'] = False
    for key in ('blocker', 'blocker_kind', 'retry_after', 'unblock_condition'):
        candidate.pop(key, None)
    closure.validate_revisions(ROOT, candidate, before)
    c.tick.save(ROOT / 'pipeline/research_work.json', work)
    print(json.dumps({'registered': 3, 'r2_actual_result': 'failed', 'authorization_bound': True}))


if __name__ == '__main__':
    register()
