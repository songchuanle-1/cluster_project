"""Persist due resource and authorization checks, not scientific progress."""
from datetime import datetime, timedelta, timezone
import copy
import json
from run_probe import BUNDLE, TOKEN, probe

ROOT, tick, guard = probe.ROOT, probe.tick, probe.guard
PRIMARY = 'm95-hierarchical-mask-feature-path-audit'
AUXILIARY = ('m95-native-relation-other-sign-conflict', 'm95-native-main-role-weight-precedence',
             'm95-native-secondary-positive-mass', 'm95-native-between-pair-support')
guard()
result = tick.load(BUNDLE / 'resource_result.json')
assert result['token'] == TOKEN and not result['ready_for_original_capture_guards']
assert result['probe_flocks_released'] and not any(result['guards'].values())
assert result['cuda_allocations'] == result['native_network_forwards'] == result['optimizer_steps'] == 0
assert result['foreign_process_signals'] == result['gpu_resets'] == result['lock_deletions'] == 0
before = tick.load(BUNDLE / 'work_before.json')
path = ROOT / 'pipeline/research_work.json'
assert tick.load(path) == before
before_hash = tick.digest(path)
work = copy.deepcopy(before)
prior = {c['id']: c for c in before['candidates']}
current = {c['id']: c for c in work['candidates']}
assert len(current) == 100
context = tick.load(ROOT / 'pipeline/headless/.tick_model_view.json')
assert context['mode'] == 'design' and context['research']['due_count'] == 5
goal_path = ROOT / 'pipeline/goal.json'
goal = tick.load(goal_path)
assert goal['research_mainline']['primary_axis'] == 'hierarchical_attention_point_feature_update'
assert '不自动恢复 M201' in goal['research_mainline']['legacy_work_policy']


def ref(file):
    return {'path': file.relative_to(ROOT).as_posix(), 'sha256': tick.digest(file)}


observed = datetime.fromisoformat(result['observed_at'])
zone = timezone(timedelta(hours=8))
local = observed.astimezone(zone)
retry = observed + timedelta(hours=1)
checked = datetime.now(timezone.utc)
auth_retry = checked + timedelta(hours=4)
gpu = result['gpu']
contexts = '; '.join('PID{} uses{}MiB'.format(p['pid'], p['used_memory_mib']) for p in result['nvml_compute_processes'])
resource = '{} total{}/used{}/free{}MiB/util{}%; {}'.format(local.isoformat(), gpu['total_mib'], gpu['used_mib'], gpu['free_mib'], gpu['utilization_percent'], contexts)
evidence = [ref(BUNDLE / name) for name in ('run_probe.py', 'remote_probe.py', 'attempt.json', 'resource_result.json')]
primary = current[PRIMARY]
assert primary['stage'] == 'blocked' and all(not gate['passed'] for gate in primary['gates'].values())
primary['evidence'].extend(evidence)
primary['blocker'] = ('Actual pinned server-4 GPU0 ' + resource +
    '; original training flock held, two diagnostic flocks acquired/released. '
    'All original guards false; no GPU allocation/native forward. CPU source/input/checkpoint '
    'preparation complete; learned-feature diagnosis still awaits exclusive native capture.')
primary['retry_after'] = retry.isoformat()
primary['findings']['latest_resource_guard'] = {
    'observed_at': result['observed_at'], 'evidence': ref(BUNDLE / 'resource_result.json'),
    'ready': False, 'native_network_forwards_this_tick': 0,
    'scope': 'Fresh occupancy/lock evidence; not learned feature, task efficacy or admission.'}
assert primary['gates'] == prior[PRIMARY]['gates']
auth = {
    'token': TOKEN, 'checked_at': checked.isoformat(), 'goal': ref(goal_path),
    'candidate_ids': list(AUXILIARY), 'primary_axis': goal['research_mainline']['primary_axis'],
    'legacy_work_policy': goal['research_mainline']['legacy_work_policy'],
    'superseding_user_authorization_in_this_turn': False,
    'mechanism_matched_auxiliary_need_established': False,
    'automatic_resume_authorized': False, 'scientific_tests': 0,
    'result': 'Four due timers rechecked against unchanged explicit mainline; retain auxiliary scope holds, not scientific rejection.',
    'retry_after': auth_retry.isoformat()}
tick.save(BUNDLE / 'authorization_check.json', auth)
auth_ref = ref(BUNDLE / 'authorization_check.json')
for candidate_id in AUXILIARY:
    candidate = current[candidate_id]
    assert candidate['stage'] == 'blocked' and candidate['blocker_kind'] == 'human_authorization'
    assert candidate['research_role'] == 'auxiliary_scope_hold'
    assert datetime.fromisoformat(candidate['retry_after']) <= checked
    candidate['retry_after'] = auth_retry.isoformat()
    candidate['evidence'].append(auth_ref)
    for key in ('stage', 'gates', 'blocker_kind', 'blocker', 'research_role', 'next_action', 'unblock_condition'):
        assert candidate[key] == prior[candidate_id][key]
changed_ids = [PRIMARY, *AUXILIARY]
assert all(candidate == prior[candidate_id] for candidate_id, candidate in current.items() if candidate_id not in changed_ids)
work['design_cycle'] = {
    'stop_reason': 'external_resource_blocked', 'attempted_ids': changed_ids,
    'evidence': evidence + [auth_ref], 'resume_condition': primary['unblock_condition'],
    'retry_after': retry.isoformat(),
    'scope': 'One due actual GPU/context/flock recheck failed; four due auxiliary authorization checks '
             'retained holds with four-hour fallback, without scientific retests, gate changes or rejections. '
             'Previously completed CPU preparation not repeated; reserve5/target2/budget0; no route-exhaustion claim.'}
memory_path = ROOT / 'pipeline/codex_memory.md'
memory = memory_path.read_text(encoding='utf-8')
assert memory == (BUNDLE / 'memory_before.md').read_text(encoding='utf-8')
lines = memory.splitlines()
for index, line in enumerate(lines):
    if line.startswith('- Current preflight'):
        lines[index] = '- Current preflight{}: design/running0/claiming0/waiting0/capacity1/budget1; due5; reserve5/target2/budget0. No new training/M201 restore.'.format(context['generated_at'])
    elif line.startswith('- Fresh pinned server4 resource'):
        lines[index] = '- Fresh pinned server4 resource{}; training flock held, diagnostic flocks acquired/released. Original no-other-context/headroom/all-three-flock guards false; no allocation/signals/reset/deletion.'.format(resource)
    elif line.startswith('- Primary retry'):
        lines[index] = '- Primary retry{}; four auxiliary authorization fallback{}; only real resource/goal/authorization evidence wakes earlier. Neither time is saved scheduler time; timers alone grant no GPU or scientific permission.'.format(retry.astimezone(zone).isoformat(), auth_retry.astimezone(zone).isoformat())
    elif line.startswith('- Current3d7186b64ab1409fbdedd66b58f5a00b '):
        lines[index] = line.replace('- Current', '- Prior', 1)
memory = '\n'.join(lines) + '\n'
memory = memory.replace('## Last Tick\n', '## Last Tick\n- Current{} snapshot{}/deadline{} unchanged. Due primary original guardsFAIL; four due auxiliary scope checks retain original gates/evidence/holds, only append authorization binding and bounded retry. Other95records unchanged.0newcandidate/variant/admission/GPUallocation/nativeforward/backward/training/optimizer. Finish not yet run.\n'.format(TOKEN, context['generated_at'], context['deadline_at']), 1)
assert memory.count('## ') == 7 and len(memory.splitlines()) < 120
notes = {'actions': [
    '快照{}，design；running/claiming/waiting均0，容量1、准入预算1；储备5/目标2/准备预算0。begin的监控/目标检查各一次。归属已核实，旧后台Disabled，目标20约束/11禁令与唯一server-4 GPU0授权不变。'.format(context['generated_at']),
    '主线到期资源实测：{}。固定主机dl04-MS-7E06及GPU UUID一致；原训练锁持有，另两诊断锁取得后释放。无其他NVML上下文、至少30000MiB及原三锁全部取得三项守卫均false，未执行GPU捕获或触碰现有进程。'.format(resource),
    '按ID及分页核对全部5个due候选。四个旧监督候选仍为human_authorization/auxiliary_scope_hold；当前goal仍明确点云特征更新优先，没有新的用户恢复授权或已证实的机制匹配辅助需求。仅追加授权核验绑定并将fallback设为四小时；历史科学门槛、失败证据、恢复条件和next_action原样保留，尤其不清除BPS历史通过项。',
    '同一主线追加4条真实资源证据，primary六项准入仍false，科学状态blocked/inconclusive。CPU源码/固定TRAIN输入/严格checkpoint装载及构造对照前轮已完成，未重复；实际学习特征的层级互补/冗余、任务伤害、独立新颖性及训练收益仍未知。',
    '其余95条记录不变；本轮新增候选/变体/准入/GPU分配/原生forward/backward/训练/优化器步数均0。5个既有记录的资源或授权核验更新不代表5个科学进展。执行状态待finish及实际释放核验。',
    '收据仅为begin至receipt之间可见的本地部分用量，缺失记未知；缓存已包含于输入、推理已包含于输出，不重复相加或作账单。产出为一次到期资源测试与四项范围核验，不是新性能结果。'
], 'decisions': [
    '按真实external_resource_blocked收尾，不等到截止凑时长、不降独占/显存/科学准入门槛、不为填槽制造监督或归一化变体，也不恢复M201。历史M95仍0.5020，目标0.5100，本轮无新增性能结果。',
    '主线资源fallback为{}，辅助授权fallback为{}；新鲜资源/目标/授权证据可提前唤醒，但定时到期不能解除范围暂停。原生特征捕获仍须原始身份/显存/NVML/三锁全部通过。上述为候选条件，不是保存的自动化触发时间，准确下轮调度未知。'.format(retry.astimezone(zone).isoformat(), auth_retry.astimezone(zone).isoformat())
]}
guard()
assert tick.digest(path) == before_hash
tick.save(path, work)
memory_path.write_text(memory, encoding='utf-8')
tick.save(BUNDLE / 'notes.json', notes)
tick.save(BUNDLE / 'persistence.json', {
    'token': TOKEN, 'recorded_at': datetime.now(timezone.utc).isoformat(),
    'changed_candidate_ids': changed_ids, 'other_95_unchanged': True,
    'all_five_original_gate_sets_unchanged': True, 'new_candidates': 0, 'new_training': 0,
    'resource_retry_after': retry.isoformat(), 'authorization_retry_after': auth_retry.isoformat(),
    'memory_lines': len(memory.splitlines())})
print(json.dumps({'changed_candidate_ids':changed_ids, 'other95_unchanged':True,
                  'all_original_gates_unchanged':True, 'primary_six_gates_passed':0,
                  'stop_reason':'external_resource_blocked', 'resource_retry':retry.isoformat(),
                  'authorization_retry':auth_retry.isoformat(), 'memory_lines':len(memory.splitlines())}, indent=2))
