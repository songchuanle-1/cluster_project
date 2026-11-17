"""Explicit, lease-bound reuse of a frozen resource probe and blocked closeout."""
import argparse
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path('D:/project/cluster_project')
PRIMARY = 'm95-hierarchical-mask-feature-path-audit'
SOURCE = ROOT / 'pipeline/diagnostic_bundles/resource_recheck_a247e0f3dc214741ae85f7c2f69598e6/run_probe.py'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == 'a3306db89f6c7067c01b2236e3ecb9c7e1863e96462b3b4c752e8a8aae7b242f'
spec = importlib.util.spec_from_file_location('frozen_resource_probe', SOURCE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
tick = probe.tick


def persist_blocked(bundle, token):
    probe.guard()
    result = tick.load(bundle / 'resource_result.json')
    assert result['token'] == token and not result['ready_for_original_capture_guards']
    assert result['probe_flocks_released']
    assert result['cuda_allocations'] == result['native_network_forwards'] == result['optimizer_steps'] == 0
    assert result['foreign_process_signals'] == result['gpu_resets'] == result['lock_deletions'] == 0
    context = tick.load(ROOT / 'pipeline/headless/.tick_model_view.json')
    assert context['mode'] in ('design', 'event')
    assert context['research']['due_count'] == 1 and context['research']['shown'][0]['id'] == PRIMARY
    work_path = ROOT / 'pipeline/research_work.json'
    before = tick.load(bundle / 'work_before.json')
    assert tick.load(work_path) == before
    before_hash = tick.digest(work_path)
    work = copy.deepcopy(before)
    candidate = next(c for c in work['candidates'] if c['id'] == PRIMARY)
    assert candidate['stage'] == 'blocked' and candidate['blocker_kind'] == 'gpu_context_or_lock_not_released'
    assert all(not gate['passed'] for gate in candidate['gates'].values())
    observed = datetime.fromisoformat(result['observed_at'])
    assert observed >= datetime.fromisoformat(candidate['retry_after'])
    retry = observed + timedelta(hours=1)
    zone = timezone(timedelta(hours=8))
    gpu = result['gpu']
    contexts = '; '.join('PID{} uses{}MiB'.format(p['pid'], p['used_memory_mib']) for p in result['nvml_compute_processes']) or 'no NVML compute context'
    locks = '; '.join(p['path'].rsplit('/', 1)[-1] + ':' + p['status'] for p in result['flocks'])
    resource = '{} total{}/used{}/free{}MiB/util{}%; {}; {}'.format(observed.astimezone(zone).isoformat(), gpu['total_mib'], gpu['used_mib'], gpu['free_mib'], gpu['utilization_percent'], contexts, locks)

    def ref(path):
        return {'path': path.relative_to(ROOT).as_posix(), 'sha256': tick.digest(path)}

    evidence = [ref(Path(__file__).resolve())] + [ref(bundle / name) for name in ('remote_probe.py', 'attempt.json', 'resource_result.json')]
    candidate['evidence'].extend(evidence)
    candidate['blocker'] = ('Actual pinned server-4 GPU0 ' + resource +
        '. Original resource/flock guards not satisfied. Probe-owned locks released; no GPU allocation '
        'or native network forward. CPU source/input/checkpoint preparation already complete; learned '
        'feature/task effects remain unknown pending exclusive native capture.')
    candidate['retry_after'] = retry.isoformat()
    candidate['findings']['latest_resource_guard'] = {
        'observed_at': result['observed_at'], 'evidence': ref(bundle / 'resource_result.json'),
        'ready': False, 'native_network_forwards_this_tick': 0,
        'scope': 'Live occupancy/lock evidence only, not a new mechanism or trained benefit.'}
    old = {c['id']: c for c in before['candidates']}
    assert candidate['gates'] == old[PRIMARY]['gates']
    assert all(c == old[c['id']] for c in work['candidates'] if c['id'] != PRIMARY)
    work['design_cycle'] = {
        'stop_reason': 'external_resource_blocked', 'attempted_ids': [PRIMARY],
        'evidence': evidence, 'resume_condition': candidate['unblock_condition'], 'retry_after': retry.isoformat(),
        'scope': 'One due live resource/flock check under unchanged original guards. CPU preparation and '
                 'constructed controls already complete, not repeated. Other candidates including '
                 'four not-due auxiliary authorization holds unchanged; no route-exhaustion claim.'}
    memory_path = ROOT / 'pipeline/codex_memory.md'
    memory = memory_path.read_text(encoding='utf-8')
    assert memory == (bundle / 'memory_before.md').read_text(encoding='utf-8')
    replacements = {
        '- Current preflight': '- Current preflight{}: {}/running0/claiming0/waiting0/capacity1/budget1; due1; reserve5/target2/budget0. No new training/M201 restore.'.format(context['generated_at'], context['mode']),
        '- Fresh pinned server4 resource': '- Fresh pinned server4 resource{}; probe-owned locks released; original guards {}. No allocation/signals/reset/deletion.'.format(resource, json.dumps(result['guards'], sort_keys=True)),
        '- Primary retry': '- Primary retry{}; four auxiliary authorization holds/retries unchanged. Timers alone grant no allocation/scientific permission; saved scheduler time not read.'.format(retry.astimezone(zone).isoformat())}
    lines = memory.splitlines()
    for index, line in enumerate(lines):
        for prefix, replacement in replacements.items():
            if line.startswith(prefix):
                lines[index] = replacement
                break
    memory = '\n'.join(lines) + '\n'
    memory = re.sub(r'(?m)^- Current(?=[0-9a-f]{32} )', '- Prior', memory)
    memory = memory.replace('## Last Tick\n', '## Last Tick\n- Current{} snapshot{}/deadline{} immutable. One due resource/flock test blocked; only primary evidence/retry updated, all original gate sets and other99records unchanged.0newcandidate/variant/admission/GPUallocation/nativeforward/backward/training/optimizer. Finish not yet run.\n'.format(token, context['generated_at'], context['deadline_at']), 1)
    assert memory.count('## ') == 7 and len(memory.splitlines()) < 120
    notes = {'actions': [
        '快照{}，{}；仅续做到期主线m95-hierarchical-mask-feature-path-audit。begin监控/目标检查各一次；归属匹配、旧后台Disabled；目标20约束/11禁令、server-4唯一GPU0授权及主线优先级不变。'.format(context['generated_at'], context['mode']),
        '新鲜固定主机/GPU身份资源复查：{}。原始守卫结果{}；探针取得的锁已释放，未分配GPU、发信号、reset或删除锁。该占用证据不等于本项目训练运行。'.format(resource, json.dumps(result['guards'], ensure_ascii=False, sort_keys=True)),
        '源码路径/固定TRAIN输入/严格checkpoint装载及构造对照已完成；本轮不重复无新增信息的CPU测试。真实学习特征的层级互补/冗余、padding任务伤害、新颖性与训练收益仍未知，既有数值FAIL原样保留。',
        '主线追加4条证据引用并保留blocked/inconclusive、六项准入false；其余99条记录及四个尚未到期的辅助监督范围暂停不改。不恢复M201，不为填槽构造监督/归一化/纯调参变体。',
        '新增候选/训练变体/准入/GPU分配/原生forward/backward/训练/优化器步数均0；实际产出仅一次到期资源/锁复查。执行状态待finish和实际释放核验，科学状态blocked。',
        '收据用量仅begin至receipt的可见本地部分窗口；缺失记未知。缓存已包含于输入、推理已包含于输出，不重复相加或作为账单；记录变更数不等于科学收益。'
    ], 'decisions': [
        '依据真实资源守卫失败，以external_resource_blocked有界收尾；不放宽独占/显存或科学准入门槛、不等待截止凑时长。M95历史仍0.5020，目标0.5100，本轮无新性能结果。',
        '主线候选复查条件为{}或真实资源/目标/授权变化；到期不能替代新鲜身份/NVML/显存/原三锁核验。辅助授权冻结与既定复查条件保持；准确的下一自动化触发时间未知，上述不是调度时间。'.format(retry.astimezone(zone).isoformat())
    ]}
    probe.guard()
    assert tick.digest(work_path) == before_hash
    tick.save(work_path, work)
    memory_path.write_text(memory, encoding='utf-8')
    tick.save(bundle / 'notes.json', notes)
    outcome = {'token': token, 'changed_candidate_ids': [PRIMARY],
               'other99_unchanged': True, 'all_original_gates_unchanged': True,
               'new_candidates': 0, 'native_forwards': 0, 'new_training': 0,
               'retry_after': retry.isoformat(), 'memory_lines': len(memory.splitlines())}
    tick.save(bundle / 'persistence.json', outcome)
    print(json.dumps(outcome, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', required=True)
    parser.add_argument('action', choices=('probe', 'persist-blocked'))
    args = parser.parse_args()
    assert re.fullmatch('[0-9a-f]{32}', args.token)
    bundle = ROOT / 'pipeline/diagnostic_bundles' / ('resource_recheck_' + args.token)
    probe.TOKEN, probe.BUNDLE = args.token, bundle
    probe.guard()
    if args.action == 'probe':
        bundle.mkdir(exist_ok=True)
        probe.main()
    else:
        persist_blocked(bundle, args.token)


if __name__ == '__main__':
    main()
