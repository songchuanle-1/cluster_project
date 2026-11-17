"""Persist fresh blocked-resource evidence without changing scientific gates."""
from datetime import datetime, timedelta, timezone
import copy
import json
from run_probe import BUNDLE, TOKEN, probe

ROOT, tick, guard = probe.ROOT, probe.tick, probe.guard
PRIMARY = 'm95-hierarchical-mask-feature-path-audit'
guard()
result = tick.load(BUNDLE / 'resource_result.json')
assert result['token'] == TOKEN and not result['ready_for_original_capture_guards']
assert result['probe_flocks_released']
assert result['cuda_allocations'] == result['native_network_forwards'] == result['optimizer_steps'] == 0
assert result['foreign_process_signals'] == result['gpu_resets'] == result['lock_deletions'] == 0
before = tick.load(BUNDLE / 'work_before.json')
work_path = ROOT / 'pipeline/research_work.json'
assert tick.load(work_path) == before
work_hash = tick.digest(work_path)
work = copy.deepcopy(before)
candidate = next(c for c in work['candidates'] if c['id'] == PRIMARY)
assert candidate['stage'] == 'blocked' and candidate['blocker_kind'] == 'gpu_context_or_lock_not_released'
assert len(work['candidates']) == 100 and all(not g['passed'] for g in candidate['gates'].values())
gates_before = copy.deepcopy(candidate['gates'])


def ref(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': tick.digest(path)}


evidence = [ref(BUNDLE / name) for name in ('run_probe.py', 'remote_probe.py', 'attempt.json', 'resource_result.json')]
observed = datetime.fromisoformat(result['observed_at'])
local = observed.astimezone(timezone(timedelta(hours=8)))
retry = observed + timedelta(hours=1)
gpu = result['gpu']
contexts = '; '.join('PID{} uses{}MiB'.format(p['pid'], p['used_memory_mib']) for p in result['nvml_compute_processes'])
locks = '; '.join(p['path'].rsplit('/', 1)[-1] + ':' + p['status'] for p in result['flocks'])
detail = ('Actual {}: pinned server-4 GPU0 total{}/used{}/free{}MiB, util{}%; {}; {}. '
          'Probe-owned flocks released; no GPU allocation/native forward. CPU source/input/checkpoint '
          'preparation already complete; native learned features still require original guards.').format(
              local.isoformat(), gpu['total_mib'], gpu['used_mib'], gpu['free_mib'], gpu['utilization_percent'], contexts, locks)
candidate['evidence'].extend(evidence)
candidate['blocker'] = detail
candidate['retry_after'] = retry.isoformat()
candidate['findings']['latest_resource_guard'] = {
    'observed_at': result['observed_at'], 'evidence': ref(BUNDLE / 'resource_result.json'),
    'ready': False, 'native_network_forwards_this_tick': 0,
    'scope': 'Live occupancy and lock evidence only; actual learned feature/task effects remain unknown.'}
assert candidate['gates'] == gates_before
assert all(c == next(old for old in before['candidates'] if old['id'] == c['id'])
           for c in work['candidates'] if c['id'] != PRIMARY)
work['design_cycle'] = {
    'stop_reason': 'external_resource_blocked', 'attempted_ids': [PRIMARY],
    'evidence': evidence, 'resume_condition': candidate['unblock_condition'], 'retry_after': retry.isoformat(),
    'scope': 'One due fresh pinned-resource probe. Original guards unchanged and failed; CPU preparation '
             'and same-shape/source controls already complete, not repeated. Reserve5/target2/budget0. '
             'Other99 candidates, including four auxiliary human-authorization holds, unchanged; '
             'no fabricated independent alternatives, route-exhaustion claim, new model or admission.'}
memory_path = ROOT / 'pipeline/codex_memory.md'
memory = memory_path.read_text(encoding='utf-8')
assert memory == (BUNDLE / 'memory_before.md').read_text(encoding='utf-8')
context = tick.load(ROOT / 'pipeline/headless/.tick_model_view.json')
assert context['mode'] == 'design' and context['research']['due_count'] == 1
snapshot, deadline = context['generated_at'], context['deadline_at']
lines = memory.splitlines()
for index, line in enumerate(lines):
    if line.startswith('- Current preflight'):
        lines[index] = '- Current preflight{}: design/running0/claiming0/waiting0/capacity1/budget1; reserve5/target2/budget0. No new training/M201 restore.'.format(snapshot)
    elif line.startswith('- Fresh pinned server4 resource'):
        lines[index] = '- Fresh pinned server4 resource{}: total{}/used{}/free{}MiB/util{}%; {}; original training flock held, diagnostic flocks acquired/released. Three original guards false; no allocation/signals/reset/deletion.'.format(local.isoformat(), gpu['total_mib'], gpu['used_mib'], gpu['free_mib'], gpu['utilization_percent'], contexts)
    elif line.startswith('- Primary retry'):
        lines[index] = '- Primary retry{} or actual resource/goal/authorization change; not next scheduler time or allocation permission. Four auxiliary scope/authorization holds unchanged; timer alone cannot reactivate them.'.format(retry.astimezone(timezone(timedelta(hours=8))).isoformat())
    elif line.startswith('- Currenta247e0f3dc214741ae85f7c2f69598e6 '):
        lines[index] = line.replace('- Current', '- Prior', 1)
memory = '\n'.join(lines) + '\n'
memory = memory.replace('## Last Tick\n', '## Last Tick\n- Current{} design snapshot{}/deadline{} immutable. One due original resource/lock test failed; only primary evidence/retry updated, other99/all6gates unchanged.0newcandidate/variant/admission/nativeforward/backward/training/optimizer. Finish not yet run; true resource block, not hypothesis rejection.\n'.format(TOKEN, snapshot, deadline), 1)
assert memory.count('## ') == 7 and len(memory.splitlines()) < 120
notes = {'actions': [
    '快照{}，design；仅续做到期主线m95-hierarchical-mask-feature-path-audit。begin已做一次监控和目标检查；没有重复预检。归属核实，Pipeline-cluster_project为Disabled，目标20约束/11禁令和server-4唯一GPU0授权未改。'.format(snapshot),
    '{}新鲜资源复查：GPU0总{}、已用{}、空闲{}MiB、利用率{}%；{}。原训练锁仍被持有，另两诊断锁实际取得并释放；无其他NVML上下文、至少30000MiB余量、三锁全取得三项原守卫均false，未分配GPU。'.format(local.isoformat(), gpu['total_mib'], gpu['used_mib'], gpu['free_mib'], gpu['utilization_percent'], contexts),
    '相对18:14历史观察，现有资源证据显示两个NVML上下文、空闲显存更少；这没有解除主线原生捕获阻塞，也不证明本项目训练运行。未读取占用进程的作业内容，未发信号/reset/删锁。',
    '源码/固定TRAIN输入/严格checkpoint装载及构造对照此前已完成，未重复制造同等证据。真实学习特征的层级互补/冗余、padding任务伤害及新机制收益仍未知。保留此前两次严格数值控制FAIL。',
    '同一主线候选追加4条哈希证据，科学状态blocked/inconclusive，六项准入仍false；其余99记录及4个辅助监督范围暂停原样保留。储备5/目标2/预算0，不增加储备、重启M201或改监督主线。',
    '新增候选/训练变体/准入/GPU分配/原生forward/backward/优化器步数均0。执行状态待finish及实际释放核验。收据仅统计begin至receipt可见的本地部分用量，缺失记未知；缓存已包含在输入、推理已包含在输出，不重复相加、不作账单。'
], 'decisions': [
    '依据原始资源和锁的实际失败，以external_resource_blocked有界收尾；不放宽独占/30000MiB/科学准入门槛，不为填槽制造调参、归一化或监督候选。历史M95仍0.5020，目标0.5100，本轮没有新的性能结果。',
    '原生特征捕获仅在新鲜固定身份、无其他NVML上下文、显存及原三锁全部通过后执行。下一候选复查条件为{}或真实资源/目标/授权变化；这不是保存的自动化触发时间，准确调度时间未知。'.format(retry.astimezone(timezone(timedelta(hours=8))).isoformat())
]}
guard()
assert tick.digest(work_path) == work_hash
tick.save(work_path, work)
memory_path.write_text(memory, encoding='utf-8')
tick.save(BUNDLE / 'notes.json', notes)
tick.save(BUNDLE / 'persistence.json', {
    'token': TOKEN, 'recorded_at': datetime.now(timezone.utc).isoformat(),
    'changed_candidate_ids': [PRIMARY], 'other_99_unchanged': True, 'six_gates_unchanged_and_false': True,
    'new_candidates': 0, 'native_forwards': 0, 'new_training': 0,
    'retry_after': retry.isoformat(), 'memory_lines': len(memory.splitlines())})
print(json.dumps({'changed_candidate_ids':[PRIMARY], 'other99_unchanged':True,
                  'six_gates_passed':0, 'stop_reason':'external_resource_blocked',
                  'retry_after':retry.isoformat(), 'memory_lines':len(memory.splitlines())}, indent=2))
