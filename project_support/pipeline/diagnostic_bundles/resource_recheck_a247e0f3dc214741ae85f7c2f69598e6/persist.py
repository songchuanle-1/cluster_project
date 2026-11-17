"""Keep fresh failed resource guards and all scientific/authorization holds."""
from datetime import datetime, timedelta, timezone
import copy
import json
from run_probe import BUNDLE, ROOT, TOKEN, guard, tick

PRIMARY = 'm95-hierarchical-mask-feature-path-audit'
guard()
result = tick.load(BUNDLE / 'resource_result.json')
assert result['token'] == TOKEN and not result['ready_for_original_capture_guards']
assert result['probe_flocks_released'] and not any(result['guards'].values())
assert result['cuda_allocations'] == result['native_network_forwards'] == result['optimizer_steps'] == 0
assert result['foreign_process_signals'] == result['gpu_resets'] == result['lock_deletions'] == 0
path = ROOT / 'pipeline/research_work.json'
before = tick.load(BUNDLE / 'work_before.json')
assert tick.load(path) == before, 'Another writer changed the ledger'
before_hash = tick.digest(path)
work = copy.deepcopy(before)
candidate = next(c for c in work['candidates'] if c['id'] == PRIMARY)
assert candidate['stage'] == 'blocked' and candidate['blocker_kind'] == 'gpu_context_or_lock_not_released'
assert len(work['candidates']) == 100 and all(not g['passed'] for g in candidate['gates'].values())
old_gates = copy.deepcopy(candidate['gates'])


def ref(file):
    return {'path': file.relative_to(ROOT).as_posix(), 'sha256': tick.digest(file)}


evidence = [ref(BUNDLE / name) for name in ('run_probe.py', 'remote_probe.py', 'attempt.json', 'resource_result.json')]
candidate['evidence'].extend(evidence)
observed = datetime.fromisoformat(result['observed_at'])
retry = (observed + timedelta(hours=1)).isoformat()
candidate['blocker'] = (
    'Actual ' + observed.astimezone(timezone(timedelta(hours=8))).isoformat() +
    ': pinned server-4 GPU0 total32607/used20107/free11994MiB, util0; NVML2634704 uses20016MiB; '
    'original training flock held. All three original resource guards failed; two probe diagnostic flocks '
    'were actually acquired and released. No GPU allocation/native forward. CPU source/input/exact-weight '
    'preparation already complete; no new independent non-GPU test justified before native learned features.')
candidate['retry_after'] = retry
candidate['findings']['latest_resource_guard'] = {
    'observed_at': result['observed_at'], 'evidence': ref(BUNDLE / 'resource_result.json'),
    'ready': False, 'native_network_forwards_this_tick': 0,
    'scope': 'Live occupancy/lock evidence only; no native mechanism efficacy or admission.'}
assert candidate['gates'] == old_gates
assert all(c == next(old for old in before['candidates'] if old['id'] == c['id'])
           for c in work['candidates'] if c['id'] != PRIMARY)
work['design_cycle'] = {
    'stop_reason': 'external_resource_blocked', 'attempted_ids': [PRIMARY],
    'evidence': evidence, 'resume_condition': candidate['unblock_condition'], 'retry_after': retry,
    'scope': 'Fresh due resource recheck only; original no-other-NVML, >=30000MiB and three-flock guards '
             'failed. Non-GPU source/input/checkpoint controls were previously completed and are not '
             'repeated without new information. Four auxiliary human-authorization holds and all '
             'other99 records unchanged. No global route-exhaustion or trained-gain assertion.'}
guard()
assert tick.digest(path) == before_hash
tick.save(path, work)
memory_path = ROOT / 'pipeline/codex_memory.md'
memory = memory_path.read_text(encoding='utf-8')
assert memory == (BUNDLE / 'memory_before.md').read_text(encoding='utf-8')
start = memory.index('## Running And Queue\n')
end = memory.index('## Open Questions And Risks\n', start)
memory = memory[:start] + (
    '## Running And Queue\n'
    '- Current preflight2026-10-15T10:11:26.153874Z: design/running0/claiming0/waiting0/capacity1/budget1; reserve5/target2/budget0. No training launch or automatic M201 restore.\n'
    '- Fresh pinned server4 resource2026-10-15T18:14:17.639216+08:00: GPU0total32607/used20107/free11994MiB/util0; NVML2634704uses20016MiB; original training flock held. Original no-other-context/headroom/all-three-flock guards allfalse. Diagnostic flocks acquired/released; no GPU allocation/signals/reset/deletion.\n'
    '- Primary retry2026-10-15T19:14:17.639216+08:00 or actual resource evidence change; retry is not next saved scheduler time or permission to allocate. Four auxiliary authorization/scope holds unchanged, retry20:46:54+08 does not restore authorization.\n'
    '- Prior73d9 native dataset4TRAIN groups0/60/101/124,4scenes/16uniqueexpressions,two exact repeats;8getitem/32appearances NOT32unique. Pair lengths667/2329 and406/1441 infer padding; no learned network capture.\n'
    '- Prior73d9 CPU full M95 strict load847parameter tensors/two serialized buffers; prior1e29 control30cluster-module state entries. Prepared native_feature_capture.py/prereg unchanged; native networkforward/backward/training/optimizer_this_tick0.\n'
) + memory[end:]
memory = memory.replace('## Last Tick\n',
    '## Last Tick\n'
    '- Current'+TOKEN+' design snapshot2026-10-15T10:11:26.153874Z/deadline11:11:26.153874Z immutable. One due primary resource test returned original guardsFAIL; fresh evidence appended to same ID; other99records/all6gates unchanged.0newcandidate/variant/admission/nativeforward/backward/training/optimizer. External-resource stop, not hypothesis rejection.\n'
    '- Script-generated six-section report updated from notes; actual finish/receipt and absent owned lease/pending must be verified in task. Usage is local begin-to-receipt partial window, cachedinput included, not billing.\n', 1)
memory = memory.replace('- Current1e29997a8967493c85410db3d0ee54b6 design', '- Prior1e29997a8967493c85410db3d0ee54b6 design', 1)
assert len(memory.splitlines()) < 120 and memory.count('## ') == 7
memory_path.write_text(memory, encoding='utf-8')
notes = {'actions': [
    '快照2026-10-15T10:11:26.153874Z（北京时间18:11:26），design；仅续做到期主线候选m95-hierarchical-mask-feature-path-audit。begin的监控/目标检查各一次，未重复预检。归属匹配、旧后台Disabled，目标20约束/11禁令不变。',
    '18:14:17+08通过已知密钥固定主机dl04-MS-7E06及唯一GPU UUID复查：RTX5090总32607、已用20107、空闲11994MiB、util0；NVML2634704占20016MiB。原训练flock仍持有，另两诊断flock实际取得后已释放。无其他NVML上下文/至少30000MiB/全部三锁三项守卫均未通过，util0不代表可用。',
    '原生捕获需要的CPU源码路径、固定TRAIN输入、checkpoint严格装载和构造对照前轮已准备；本轮未重复这些无新增信息的测试。真实学习特征的层级冗余/互补及任务影响仍未知，未把构造样本或padding长度当作任务伤害。',
    '本轮新增证据为一次到期的真实资源/锁复查，保留原候选blocked/inconclusive、六项准入全部false；其余99记录与4个辅助监督范围暂停未改。主线继续为分层交互更新参与mask的inst_feats，不恢复M201或旧监督主线。',
    '新增候选/变体/准入/GPU分配/原生forward/backward/训练/优化器步数均0。科学状态blocked；执行状态等待finish核验。收据用量仅begin至receipt的可见本地窗口，缺失记未知，缓存已在输入内、推理已在输出内，不重复相加或当账单。'
], 'decisions': [
    '按external_resource_blocked真实收尾；不降显存或独占门槛、不驱逐或检查其他项目作业内容、不发信号/reset/删除锁，不为填槽制造归一化或监督变体。没有新的任务指标，历史M95仍0.5020，距0.5100差0.0080。',
    '主线资源条件复查不早于2026-10-15T19:14:17.639216+08:00，或实际资源/目标/授权证据发生变化；只有新鲜上下文、显存和三锁全部通过才执行既定原生捕获。此为候选retry而非下一自动化触发时间，保存的调度未读取、准确下轮时间未知。'
]}
tick.save(BUNDLE / 'notes.json', notes)
tick.save(BUNDLE / 'persistence.json', {
    'token': TOKEN, 'recorded_at': datetime.now(timezone.utc).isoformat(),
    'changed_candidate_ids': [PRIMARY], 'other_99_candidates_unchanged': True,
    'all_six_gates_unchanged_and_false': True, 'new_candidates': 0, 'new_training': 0,
    'retry_after': retry, 'memory_lines': len(memory.splitlines())})
print(json.dumps({'changed_candidate_ids':[PRIMARY],'other99_unchanged':True,
                  'six_gates_passed':0,'stop_reason':'external_resource_blocked','retry_after':retry,
                  'memory_lines':len(memory.splitlines())}, indent=2))
