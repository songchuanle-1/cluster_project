"""Close research records honestly: new PSBR static preparation, no native run."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/project/cluster_project')
P = ROOT / 'pipeline'
B = P / 'diagnostic_bundles/tick_8fafa3d4'
S = B / 'psbr_prepare'
N = B / 'psbr_native_prepare'
A = B / 'psbr_execution_adapter'
REPO = ROOT / 'Cluster'
TOKEN = '8fafa3d4ebcb48e7ba3436e084f6ee9f'
CID = 'hierarchy-parent-segmented-bidirectional-token-state'
COMMIT = '74fcd21df0af9a971792038ffe251af1ffea2604'
NOW = dt.datetime.now(dt.timezone.utc).isoformat()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


owner = load(P / 'headless/.foreground.lockdir/owner.json')
assert owner['token'] == TOKEN and owner['thread_id'] == os.environ['CODEX_THREAD_ID']
assert load(P / 'execution_mode.json')['target_thread_id'] == owner['thread_id']
assert owner['generated_at'] == '2026-10-22T02:12:05.347438+00:00'
assert owner['deadline_at'] == '2026-10-22T03:12:05.347438+00:00'
assert dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(owner['deadline_at'])
assert sha(P / 'headless/.tick_context.json') == owner['context_sha256']
assert sha(P / 'headless/.tick_context_state.next.json') == owner['pending_sha256']
assert sha(P / 'goal.json') == '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
assert sha(S / 'preparation.json') == 'f1973052931bb76bb8a4087e1d1aff5d6e5051f2859227d4fbc74a7827020128'
assert sha(N / 'preparation.json') == '1e1de105f34ce4f6f87fe862bf35ee2c7c0bf26bf7404b0550559534a0e7472e'
assert sha(A / 'preparation.json') == '9d6c98a4c406d052c5ae1d420053103b0ec08bf71fb0ce5c32de88dd49b5bb4b'
for directory in [N, A]:
    for name, expected in load(directory / 'preparation.json')['prepared_file_hashes'].items():
        assert sha(directory / name) == expected, name
for name in ['independent_worker_review.json', 'resources_safety_review.json']:
    assert (N / name).is_file()
for name in ['independent_adapter_review.json', 'source_result_boundary_review.json']:
    assert (A / name).is_file()
tests = load(A / 'fixture_validation_run1.json')
assert tests['tests_run'] == 31 and tests['successful'] and not tests['failures'] and not tests['errors']
for directory, count in [(S, 50), (N, 48), (A, 34)]:
    static = load(directory / 'static_validation.json')
    assert static['check_count'] == count and all(x is True for x in static['checks'].values())
integration = load(B / 'psbr_actual_guard_integration.json')
assert integration['remote_calls'] == 0 and not integration['native_GPU_tested']
assert all(o['real_prepare'] == 'refused_registered_running_slot_before_transport' for o in integration['observations'])
assert not (B / 'psbr_execution').exists() and not (B / 'hrc_execution').exists()

git = lambda *args: subprocess.check_output(['git', *args], cwd=REPO, text=True, encoding='utf-8').strip()
assert git('rev-parse', 'HEAD') == COMMIT and not git('diff', '--cached', '--name-only')
version = load(S / 'version.json')
assert version['code_commit'] == COMMIT and version['parent_commit'] == '9e543af623acd7fa9bd4a3f81ce79c932e98774a'
for name, expected in version['source_hashes'].items():
    assert sha(REPO / name) == expected
    blob = subprocess.check_output(['git', 'show', f'{COMMIT}:{name}'], cwd=REPO)
    assert hashlib.sha256(blob).hexdigest() == expected
protected = load(P / 'diagnostic_bundles/tick_16b87793/protected_worktree_before.json')['protected_existing_worktree']
for item in protected:
    assert sha(REPO / item['path']) == item['sha256']
actual_status = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=REPO, text=True, encoding='utf-8')
assert {(line[:2], line[3:]) for line in actual_status.splitlines()} == {(item['status'], item['path']) for item in protected}
hrc_prep = load(P / 'diagnostic_bundles/tick_16b87793/hrc_prepare/preparation.json')
for name, expected in hrc_prep['source_hashes'].items():
    assert sha(REPO / name) == expected
for relative in ['tick_86e41faa/hrc_native_prepare', 'tick_9b40ab74/hrc_execution_adapter']:
    old = P / 'diagnostic_bundles' / relative
    for name, expected in load(old / 'preparation.json')['prepared_file_hashes'].items():
        assert sha(old / name) == expected
save(B / 'final_source_integrity.json', {
    'recorded_at': NOW, 'candidate_id': CID, 'local_HEAD': COMMIT,
    'new_commit_only_nine_reviewed_additions': True, 'nine_PSBR_files_match_commit_and_review': True,
    'nine_HRC_files_unchanged_at_old_commit_identity': True,
    'old_HRC_native_and_execution_adapter_preparations_unchanged': True,
    'all_PSBR_native_and_adapter_prepared_file_hashes_match': True,
    'all_28_existing_file_bytes_and_status_unchanged': True, 'git_index_empty': True,
    'remote_HEAD': 'NOT_QUERIED_THIS_TICK; f51823bb remains historical last observation',
    'no_sync_or_push': True, 'native_PSBR': 'NOT_RUN', 'native_HRC': 'NOT_RUN'
})

probe_path = B / 'psbr_native_resource_check.json'
probe = load(probe_path)
data = probe['data']
assert probe['returncode'] == 0 and data['hostname'] == 'dl04-MS-7E06'
assert data['read_only'] and not data['gpu_computation_started']
for item in data['experiments'].values():
    assert item['pid_exists'] and item['exact_argv_cwd_match']
    assert item['native_progress'][1]['step'] > item['native_progress'][0]['step']
observed = data['observed_at']
retry = (dt.datetime.fromisoformat(observed) + dt.timedelta(hours=1)).isoformat()
command = 'python -B D:/project/cluster_project/pipeline/diagnostic_bundles/tick_8fafa3d4/observe_resources.py --output psbr_native_resource_check.json'
save(B / 'psbr_resource_block.json', {
    'recorded_at': NOW, 'candidate_id': CID, 'experiment_id': 'M209-PSBR',
    'kind': 'resource_check', 'result': 'blocked', 'command': command,
    'evidence': ref(probe_path), 'observed_at': observed,
    'allowed_server': 'server-4', 'allowed_physical_gpus': [0, 1], 'max_tasks_per_gpu': 1,
    'actual_contexts': data['contexts'],
    'native_progress': {k: v['native_progress'] for k, v in data['experiments'].items()},
    'authorized_empty_slot_available': False, 'slot_status_changed_since_previous_tick': False,
    'local_prepare_refusal_before_transport': ref(B / 'psbr_actual_guard_integration.json'),
    'native_PSBR': 'NOT_RUN', 'standard_resources_PSBR': 'NOT_RUN',
    'active_binding_manifest_lease_or_remote_stage_created': False,
    'important_boundary': 'Worker and execution adapter are prepared, not executed; native semantics, common parameter/batch/resource pairing and standard summaries/admission still require true results. No one-click launch claim.',
    'next_action': 'Keep both original runs. A future actual idle authorized slot permits fresh root execution binding and staged PSBR native checks; validate four real results before canonical admission and queue.'
})

w = load(P / 'research_work.json')
c = next(x for x in w['candidates'] if x['id'] == CID)
assert c['stage'] == 'validation' and c['code_commit'] == COMMIT
c.update(stage='blocked', resume_stage='validation', blocker_kind='exclusive_gpu_slot',
    blocked_at=observed, retry_after=retry,
    blocker='Both authorized server4 physical GPUs still contain their exact original increasing-step training contexts (GPU0 M207-HAP PID979955, GPU1 M206-CGCA PID732137); max1 task/card. Actual local prepare refuses both before transport.',
    unblock_condition='A canonical current server4GPU0/1 opening plus fresh live UUID/idleness/exclusive locks and current owner/policy/deadline binding. Preserve original and foreign jobs; old prepared provenance is never execution permission.',
    native_status='NOT_RUN_waiting_authorized_idle_gpu', resource_status='NOT_RUN_waiting_authorized_idle_gpu',
    native_adapter_status='PREPARED_UNEXECUTED')
paths = [B / 'observe_resources.py', probe_path, B / 'psbr_resource_block.json', B / 'final_source_integrity.json', B / 'source_evidence_reuse_check.json', B / 'held_route_boundary_check.json']
for path in paths:
    if not any(e['path'] == ref(path)['path'] for e in c['evidence']):
        c['evidence'].append(ref(path))
c['next_action'] = 'After a real authorized server4 physical0/1 opening, externally compare exact candidate.execution_adapter preparation/release/source anchors and worker_preparation hashes before invoking code. Use current owner/context/pending/goal/whitelist/GPU UUID and original deadline for fresh execution_binding/manifest/lease/isolated psbr stage. Run two genuine original TRAIN2 smokes (M95/PSBR) plus original resource pair within remaining time; actual non-singleton Wh state/finite WxWhWo gradients and optimizer updates, raw-CSORT/HCG/inst path, common initialized-parameter hash and both TRAIN batch fingerprints must be inspected from true results. Compare standard original resource input/handlers/bs1/warm20/repeat100 and unsupported operators; smoke observer memory is not pure TRAIN peak. Raw completion and offline tests are not admission. Build authentic standard smoke/resource summaries, then closure.admission/original YAML queue/canonical gated dispatch. Offdiagonal/reset-state diagnostics remain unimplemented support, not fabricated native proof or a new gate. Reconcile exact request/stage/PID/startticks/argv/result after uncertainty; never replay/kill/renew old deadlines. Efficacy UNKNOWN.'
h = next(x for x in w['candidates'] if x['id'] == 'hierarchy-bottom-up-refined-token-composition')
assert h['stage'] == 'blocked' and h['code_commit'] == '9e543af623acd7fa9bd4a3f81ce79c932e98774a'
h['blocked_at'] = observed
h['retry_after'] = retry
for path in [B / 'observe_resources.py', B / 'native_resource_check.json', B / 'hrc_resource_block.json', probe_path, B / 'source_evidence_reuse_check.json', B / 'final_source_integrity.json']:
    if not any(e['path'] == ref(path)['path'] for e in h['evidence']):
        h['evidence'].append(ref(path))
w['tick_attempt'] = {
    'tick_started_at': owner['generated_at'], 'candidate_id': CID,
    'kind': 'resource_check', 'result': 'blocked', 'command': command,
    'observation': '10:35:12 Shanghai exact pinned server4 hostname/physical UUIDs/original PID/starttime/argv/cwd and increasing native steps confirmed: HAP17/50 2011→2012 onGPU0, original full-resume CGCA24/50 3937→3938 onGPU1. Both cards occupied under max1/card. PSBR independent source/native YAML, local commit74f, candidate-specific worker and execution adapter prepared/offline checked; actual current prepare refuses both before transport. No PSBR or HRC native/resource computation, active binding/lease/stage/admission/queue/launch.',
    'evidence': [ref(probe_path), ref(B / 'psbr_resource_block.json'), ref(B / 'psbr_actual_guard_integration.json'), ref(B / 'final_source_integrity.json')]
}
w['next_action'] = 'Monitor and preserve original HAP/CGCA native runs, handle exact terminal evidence canonically; prioritize prepared HRC native checks on an actual authorized opening, then PSBR. True native/resource checks and real result review precede admission/queue/launch. Existing scope/numerical/revision holds stay parked; no new human operation approval is needed.'
w['updated_at'] = NOW
save(P / 'research_work.json', w)

memory = (P / 'codex_memory.md').read_text(encoding='utf-8')
replacements = {
    '- owner01': '- owner01a159c5-29ab-7a22-ba7f-e79174757253实际环境/execution_mode一致。前轮9b40ab74894049cda10820d24f3bcc97 FINALIZED/released及headless lock/pending消失已核验。当前8fafa3d4ebcb48e7ba3436e084f6ee9f DESIGN，上海10-22 10:12:05快照/原deadline11:12:05（UTC02:12:05.347438/03:12:05.347438）；begin先监控派发，2running/0waiting，无新terminal/operational issue。',
    '- M206-CGCA GPU1原full-resume保持': '- M206-CGCA GPU1原full-resume保持：10:35:12 PID732137/starttime21298582/--resume argv/cwd匹配，native24/50 3937→3938、log新鲜.111s；10:12 monitor当前epoch24/Best.4953/noimprove6/10（序列.4902/.4909/.4899/.4868/.4869），不把当前epoch当best产生epoch。例行在训进度，终态待测，原恢复best.4751223027706146历史分开。',
    '- M207-HAP GPU0原进程保持': '- M207-HAP GPU0原进程保持：10:35:12 PID979955/starttime21613920/cwd/argv匹配，native17/50 2011→2012、log新鲜.567s；10:12 monitor缓存epoch16/Best.4919/noimprove0/10（序列.4813/.4897/.4887/.4880/.4919）。采样时间/当前epoch不冒作best产生epoch；不依中途验证改机制或选参。',
    '- M208-HRC stable': '- M208-HRC stable hierarchy-bottom-up-refined-token-composition，codecommit9e543af623acd7fa9bd4a3f81ce79c932e98774a（8独立model源+1原生YAML）保持；localHEAD后增PSBR9文件至74f但HRC9hash未变。h0=μ0+F0(LNμ0)，u1=mean_ids1(h0)，h1=u1+F1(LNu1)，u2=mean_ids2(h1)，h2=u2+F2(LNu2)；原3FFN各一次/rawbanks/FPS/IDs/CSORT/HCG/最后inst保持。native/资源NOT_RUN，blocked/resumevalidation/exclusive_gpu_slot，10:35:12双卡占用实证，retry UTC03:35:12.090022或真实空卡事件，不延长本轮deadline。',
    '- 三账保持': '- 三账保持M205 complete/done_earlystop，M207-HAP running/GPU0/PID979955与M206-CGCA running/GPU1/PID732137，launch_verifiedtrue。10:35:12两卡各仅原context、总显存19805/19811MiB，原步数递增。HRC/PSBR是未准入candidate，queue waiting0；不能把候选准备数当就绪训练数。',
    '- server3/server6仍禁用；localHEAD': '- server3/server6仍禁用；localHEAD新增9个PSBR文件至74fcd21df0af9a971792038ffe251af1ffea2604，parent9e543af；remoteHEAD沿用f518历史（本轮未查询/sync/切换），既有M206/M207运行不改。HRC9hash、旧worker/adapter及28既有脏/未跟踪文件字节/status保持、index空，无reset/clean/stash/force/sudo/密码读取。',
}
lines = memory.splitlines()
for i, line in enumerate(lines):
    for prefix, replacement in replacements.items():
        if line.startswith(prefix):
            lines[i] = replacement
            break
memory = '\n'.join(lines) + '\n'
memory = memory.replace('本轮9旧blocked均notdue未重开', '本轮8旧hold到期有界复查，stage/blocker/revision与旧摘要相同，655直接引用hash均匹配；无新解封/追加修订授权')
memory = memory.replace('本轮未改模型或为填额度制造新candidate；只准备现有HRC执行adapter并做其离线/本地guard检查。', '本轮定向历史审后新增PSBR单一结构候选；不重开MDC/C2C/旧hold，不称全历史或文献新颖性已证。')
active = '''- M209-PSBR stable hierarchy-parent-segmented-bidirectional-token-state，commit74fcd21df0af9a971792038ffe251af1ffea2604，仅8独立源+1原字节YAML。middle真实support=ids1[ids0]，原ids2粗父组内按detached原per_layer_coords[2]的xyz+tokenID排序；共享Wx/无biasWh双向tanh状态每组/batch归零，Wo拼接输出逆散回原ID，整体替换middle residual FFN（旧参数Identity移除），fine/coarse原FFN/LN/rawbanks/CSORT/HCG/末层单inst更新保持。
- PSBR无新gate/QKV/残差支路/纯分布缩放/数值改参；native YAML全部字节同M95、seed1999/50epochs/maxiters70。50项源码静态+独立24项检查及约束审无确定阻断；262656新middle参数对原525568（delta−262912）仅静态算术，真实总资源/训练效益UNKNOWN，不声称减少MAC就是更快或创新。
- PSBR sourceprep tick_8fafa3d4/psbr_prepare SHA f1973052931bb76bb8a4087e1d1aff5d6e5051f2859227d4fbc74a7827020128是提交前冻结历史；version.json绑定真实74f九文件localcommit。nativeprep SHA1e1de105f34ce4f6f87fe862bf35ee2c7c0bf26bf7404b0550559534a0e7472e，worker05ab6ac1…/runtimeb6698c77…/templatef90e2662…；48项静态+独立14项核，资源函数及7runtime函数AST原样，模板unbound，native/resources仍NOT_RUN。
- PSBR executionadapter prepSHA9d6c98a4c406d052c5ae1d420053103b0ec08bf71fb0ce5c32de88dd49b5bb4b/releaseb17d424e493bcd49e1858bc6fc4b897d6fab5970a25240cea143e826f40e20d7，adapterc8aee02b…/remote9ea6f90d…；只常量/path移植HRC原逻辑，31离线mock+34静态通过，mdc/pce独立审；root先外部锚candidate后实测当前owner/guard通过，prepare两卡均在transport前拒绝，0remote/无active binding/manifest/lease/stage。blocked/resumevalidation/exclusive_gpu_slot、retry03:35:12UTC或真实空卡。
'''
memory = memory.replace('## Active Hypotheses\n', '## Active Hypotheses\n' + active)
risks = '''- PSBR geometry序有轴/顺序偏置，双向不保证旋转或ties换ID不变；tanh长链梯度/无middle identity自细节/跨父组关系受限及串行小GEMM延迟风险均未知。constructor仅新模块fork_rng(devices=[])保留后续CPU RNG位置、不manual_seed/改默认init/扫初始化；可能重用随机序列形成相关，真实common初始化参数与两TRAIN批配对仍须四真结果核，不以静态推定。
- PSBR专属worker无aux backward/autograd.grad，计划真实native criterion一次backward与每步Wx/Wh/Wo非零finite weightgrad/weight更新、非单例父组/双向零边界/inverse/raw-CSORT/HCG/inst→ILA→mask观察；全部尚未执行。common参数name/count/整体fingerprint为未来真实单target记录，尚未配对。offdiagonal/reset-state probe未实现未测，不冒作依赖证据，不新加准入门；smoke含observer开销、纯TRAIN峰值UNKNOWN支持项。原标准resources单独无observer。
- HRC/PSBR的adapter都只产生raw四结果，无标准smoke/resource语义与配对formatter、receipt或queue。未来root须先用各candidate保存的精确prep/release/source外锚核代码，再用当前owner/context/pending/goal/资源/原deadline新绑定；实际loss/backward/path、初始化/两批指纹、原资源输入/handler/unsupported与memory范围核后另生成真实标准汇总，canonical准入后才入队派发。疑似超时只核原stage/request/PID/startticks/argv/result，不盲重放/续旧lease/kill/删现场。
'''
memory = memory.replace('## Open Questions And Risks\n', '## Open Questions And Risks\n' + risks)
memory = memory.split('## Last Tick\n')[0] + '''## Last Tick
- 本轮8fafa3d4先begin监控/派发，上海10:13:14与PSBR静态准备后10:35:12两次strict known-host/pinned hostname/UUID/NVML/原PID/starttime/argv/cwd有界资源检查；最新GPU0 HAP17/50 2011→2012、GPU1原CGCA full-resume24/50 3937→3938，原任务保持，无新终态/失败。
- 新增1个PSBR独立结构：8源+原YAML实现、50+独立24静态核与约束审，9文件localcommit74f；专属worker48+独立14静态核，执行adapter31离线mock+34静态核、来源/guard/结果边界独立审。root外锚后实际本地prepare两卡占槽拒绝，0transport；这均不是native/资源/训练效果PASS。
- 到期8旧hold仅有界摘要/655原证据hash及授权界限复查，未重开/重测；HRC/旧worker/adapter和28既有脏源保持。1新candidate/0模型修订/1本地commit/0sync/0准入/0queue/0launch/0terminal，HRC和PSBR native/resources全部NOT_RUN，未造全局穷尽或冷却。
- tick_attempt绑定generated_at2026-10-22T02:12:05.347438+00:00、PSBR真实resource_check/blocked及最新资源/占槽拒绝/源完整性证据。下一步先守护原运行与canonical终态，实际授权空卡优先HRC再PSBR；fresh binding执行真实双target TRAIN2+原资源pair、审真实结果才生成标准汇总/准入/入队。操作授权已足够，无需再审批。
- 当前8fafa3d4收尾以实际report/finish/receipt为准，不预写PASS；核FINALIZED/released及headless锁/pending消失，释放后不再写项目。本轮新独立变体实现与可执行检查准备属实质进展，NOTIFY；两卡例行在训进度本身不作为通知原因。
'''
assert len(memory.splitlines()) < 120
assert sum(line.startswith('## ') for line in memory.splitlines()) == 7
(P / 'codex_memory.md').write_text(memory, encoding='utf-8')

notes = {
    'actions': [
        '10:13:14与新PSBR静态准备后10:35:12上海时间两次有界资源核：server4 strict known-host/pinned hostname/物理UUID匹配，原PID/starttime/argv/cwd及native日志步增；最新GPU0 HAP17/50 2011→2012、GPU1 CGCA原full-resume24/50 3937→3938，各仅原context，max1任务/卡，无可用空槽。未更动任何现有/外部训练。10:12监控缓存Best为HAP.4919/CGCA.4953，不把当前epoch或三位小数尾日志当最佳发生epoch/新精确Best。',
        '新增M209-PSBR单一独立结构：保留原FPS/IDs/rawbanks/CSORT/fine-coarse FFN/LN/HCG及单末层inst更新；middle在原coarse父组内按detached原centroid xyz+ID固定序，共享Wx/Wh双向tanh状态经concat Wo输出，移除整个旧middle residual FFN。真实support=ids1[ids0]，空ID/padding不进入状态、结果逆散回原ID，每父组/batch/方向边界零状态。未改YAML数值/seed1999/50epochs/maxiters70，原生检查与效果仍未测。',
        '作者50项源/AST/compile/原YAML一致性检查、独立24项静态核与约束审均无确定阻断；已仅9个新增模型源/配置文件本地提交74fcd21df，parent9e543af。原28脏/未跟踪文件字节和status保持、index空，HRC9源和所有已冻结包未改；无push/sync/远端HEAD切换。',
        'PSBR专属native worker/template/runtime已冻结：48项静态与独立14项检查；新Wx/Wh/Wo真实native梯度/更新、非单例组、原loss.backward、HCG/CSORT/inst→ILA→mask路径及两批/共同参数fingerprint均为未来执行观测，当前NOT_RUN。原resources函数及7runtime函数AST保持；没有torch/SSH/GPU/activelease执行。',
        'PSBR执行adapter仅从已测HRC程序替换候选常量/路径，完整文本/AST差异受限；31离线mock和34静态检查通过，来源/安全/结果边界独立复核。root先将精确prep/release/source外锚入候选，再实际本地guard/prepare集成：当前owner/context/授权通过，GPU0/1均因登记原任务在transport前拒绝；0transport、无生产binding/manifest/lease/staging。',
        '8个到期旧hold有界复核：摘要中的stage/blocker/revision保持、655直接引用hash匹配，无新的解封/追加修订授权。PCE3次/RSTR2次额度耗尽及旧失败、4监督辅助scope/2测量实现hold保持；不把到期当解除权限。保存7段memory、next_batch决策和本轮真实resource_check/blocked证据。'
    ],
    'decisions': [
        '选PSBR为一个真实新计算图假设，不为额度凑数：其跨middle sibling的非线性共享状态边不同于MDC一跳方向卷积、HRC逐层mean组合、HAP仿射传播或CGCA coarse Gram。有限源/历史索引核查未见直接重开禁用，不宣称文献/全史新颖性或已证任务瓶颈。新middle262656对旧525568参数只是静态算术，serial延迟/全部资源与效益UNKNOWN。',
        '保留原构造序，只有新增recurrence构造使用CPU fork_rng(devices=[])恢复后续随机数位置，不manual_seed、改默认init或做初始化搜索；随机序列重用相关性已披露，实际共同参数/两批loader配对不能用静态控制代签。',
        'HRC与PSBR保持blocked/exclusive_gpu_slot/resumevalidation，实证retry为UTC03:35:12.090022或真实队列空槽事件，不延长本轮原UTC03:12:05.347438 deadline。先推进已准备HRC，再PSBR；有实际授权空槽后各用当前root新binding/manifest/lease/独立stage，保留原运行。',
        '所有新native/资源仍NOT_RUN。适配器四个raw completed结果不是准入；真实loss/backward/参数更新/新路径、共同初始化与两批指纹、原资源协议与unsupported/内存范围核后，另生成真实标准smoke/资源汇总，closure准入后才原YAML入队并当轮canonical派发。offdiagonal/reset-state诊断未实现未测；smoke含observer内存，纯TRAIN峰值UNKNOWN支持项，不新加门槛。超时只精确reconcile旧stage/request/PID/startticks/argv/result，不续租/重放/kill/删证据。',
        '本轮1新候选/0模型修订/1仅本地9文件提交/0同步/0准入/0入队/0启动/0终态，standing项目授权已覆盖，无新用户审批。新独立变体及原生执行准备是本轮通知理由；例行在训进度本身不是新科学结论。'
    ]
}
save(B / 'notes.json', notes)
print(json.dumps({'persisted': True, 'candidate': CID, 'stage': c['stage'], 'local_commit': COMMIT,
    'native_status': c['native_status'], 'tick_attempt': w['tick_attempt']['kind'],
    'source_integrity': ref(B / 'final_source_integrity.json'), 'resource_block': ref(B / 'psbr_resource_block.json'),
    'notes': str(B / 'notes.json'), 'memory_lines': len(memory.splitlines()),
    'original_deadline': owner['deadline_at']}, ensure_ascii=False))
