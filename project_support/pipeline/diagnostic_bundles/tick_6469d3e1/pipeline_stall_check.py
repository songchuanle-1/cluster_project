"""Isolated policy probes; no scientific candidate or shared-code mutation."""

import ast
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path


ROOT = Path('D:/project/cluster_project')
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
HEADLESS = ROOT / 'pipeline/headless'
TOKEN = '6469d3e1de264f898cab0631a3a22146'
THREAD = '01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
GOAL_SHA = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guard():
    owner = read(HEADLESS / '.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN
    assert owner['thread_id'] == THREAD == os.environ['CODEX_THREAD_ID']
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT / 'pipeline/goal.json') == GOAL_SHA
    assert sha(HEADLESS / '.tick_context.json') == owner['context_sha256']
    assert sha(HEADLESS / '.tick_context_state.next.json') == owner['pending_sha256']
    return owner


def main():
    owner = guard()
    path = HEADLESS / '.tick_model_view.json'
    assert path.stat().st_size <= 12000
    view = read(path)
    research, queue = view['research'], view['queue']
    ledger = ROOT / 'pipeline/research_work.json'
    ledger_sha = sha(ledger)
    work = read(ledger)
    assert view['mode'] == 'design' and not research['reserve_only']
    assert queue['candidate_budget'] == 3
    assert (research['pending_count'], research['pending_limit']) == (6, 8)
    source = (SKILL / 'tick_efficiency.py').read_text(encoding='utf-8')
    function = next(n for n in ast.parse(source).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'cooldown_active')
    now = datetime.now(timezone.utc)
    hold = {'retry_after': (now + timedelta(minutes=10)).isoformat(),
            'signature': 'unchanged-project', 'stop_reason': 'no_information_gain',
            'candidate_ids': ['old-measurement-only']}
    namespace = {'Path': Path, 'datetime': datetime, 'timezone': timezone,
                 'read': lambda path, default=None: hold,
                 'research_signature': lambda project: 'unchanged-project'}
    exec(compile(ast.Module(body=[function], type_ignores=[]),
                 str(SKILL / 'tick_efficiency.py'), 'exec'), namespace)
    check = namespace['cooldown_active']
    no_gain_global = check(ROOT, now, candidate_backfill=False)
    no_gain_backfill = check(ROOT, now, candidate_backfill=True)
    hold['stop_reason'] = 'external_resource_blocked'
    external_backfill = check(ROOT, now, candidate_backfill=True)
    actual = read(HEADLESS / '.research_cooldown.json')
    hold.clear()
    hold.update(actual)
    hold['signature'] = 'unchanged-project'
    actual_expiry_result = check(ROOT, now, candidate_backfill=False)
    assert no_gain_global and no_gain_backfill
    assert not external_backfill and not actual_expiry_result
    due = [c['id'] for c in research['shown']]
    scope = [{'id': c['id'], 'stage': c['stage'],
              'blocker_kind': c.get('blocker_kind'),
              'unblock_condition': c.get('unblock_condition'),
              'priority_restored': False, 'new_scientific_test': False}
             for c in work['candidates'] if c['id'] in due]
    assert len(scope) == 4 and all(c['stage'] == 'blocked' for c in scope)
    guard()
    assert sha(ledger) == ledger_sha
    result = {
        'observed_at': now.isoformat(),
        'observed_at_shanghai': now.astimezone(timezone(timedelta(hours=8))).isoformat(),
        'token': TOKEN, 'snapshot_at': view['generated_at'],
        'snapshot_facts': {'mode': view['mode'], 'active_count': queue['active_count'],
            'candidate_budget': queue['candidate_budget'],
            'reserve_count': research['reserve_count'], 'reserve_target': research['reserve_target'],
            'reserve_budget': research['reserve_budget'], 'reserve_only': research['reserve_only'],
            'pending_count': research['pending_count'], 'pending_limit': research['pending_limit'],
            'unfinished_id_headroom': research['pending_limit'] - research['pending_count'],
            'due_ids': due,
            'bootstrap_required': view.get('design_bootstrap', {}).get('required', False)},
        'isolated_policy_cases': {
            'future_no_gain_holds_project': no_gain_global,
            'future_no_gain_still_holds_with_backfill': no_gain_backfill,
            'future_external_hold_bypassed_with_backfill': not external_backfill,
            'actual_saved_hold_expired': not actual_expiry_result,
            'actual_saved_retry_after': actual['retry_after'],
            'actual_hold_is_current_blocker': False},
        'due_scope_recheck': scope,
        'findings': [
            'This non-reserve-only design tick is not prohibited from new independent mainline work by reserve_budget=0.',
            'Two numerical/unknown blocks consume reserve; that does not prove global scientific exhaustion.',
            'The bootstrap safeguard is absent with due IDs or zero reserve budget; this is not a prohibition on new design.',
            'No-information-gain cooldown applies to the whole project despite candidate-scoped prose. Actual saved expiry is past, so it is not the present blocker.',
            'The current demonstrated failure is research progression: repeated diagnosis was not converted into a distinct structural candidate. Neither missing permission nor unavailable GPUs was established as its cause.'],
        'unverified': ['Current GPU idleness beyond preflight',
                       'A completed independent new architecture or trained efficacy',
                       'End-to-end behavior of any proposed pipeline patch'],
        'changes': {key: 0 for key in ('shared_skill_code', 'goal_or_gates', 'scheduler',
            'research_work', 'scientific_candidates', 'native_forwards', 'native_backwards', 'new_training')},
        'bindings': {'goal_sha256': GOAL_SHA, 'research_work_sha256': ledger_sha,
            'context_sha256': owner['context_sha256'],
            'source_sha256': {name: sha(SKILL / name) for name in
                ('build_tick_context.py', 'tick_efficiency.py', 'foreground_tick.py', 'closure.py')}},
        'disposition': 'Policy diagnosis only; scientific research incomplete. No fabricated closure PASS.'}
    output = Path(__file__).with_suffix('.json')
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'path': str(output), 'sha256': sha(output), 'policy_cases': 4,
                      'new_structural_candidates': 0, 'ledger_unchanged': True,
                      'actual_cooldown_expired': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
