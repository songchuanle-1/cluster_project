"""Persist this owned tick's real resource block and offline adapter preparation."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/project/cluster_project')
P = ROOT / 'pipeline'
B = P / 'diagnostic_bundles/tick_9b40ab74'
A = B / 'hrc_execution_adapter'
TOKEN = '9b40ab74894049cda10820d24f3bcc97'
THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
CID = 'hierarchy-bottom-up-refined-token-composition'
COMMIT = '9e543af623acd7fa9bd4a3f81ce79c932e98774a'
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
assert owner['token'] == TOKEN and owner['thread_id'] == THREAD
assert os.environ['CODEX_THREAD_ID'] == THREAD == load(P / 'execution_mode.json')['target_thread_id']
assert dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(owner['deadline_at'])
assert sha(P / 'headless/.tick_context.json') == owner['context_sha256']
assert sha(P / 'goal.json') == '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
assert sha(A / 'preparation.json') == '1ab29434e5a1e4f0144fd38e22d83f1ae561813973ed0468e64f65aac6c9a568'
assert sha(A / 'adapter_release.json') == 'f2b3cdfe7a63cacf65e0d38837c4df1211715a31320f4d808d569c855a9e6d83'
prep = load(A / 'preparation.json')
for name, expected in prep['prepared_file_hashes'].items():
    assert sha(A / name) == expected, name
release = load(A / 'adapter_release.json')
for name, expected in release['source_hashes'].items():
    assert sha(A / name) == expected, name
tests = load(A / 'independent_review/final_validation_r2.json')
assert tests['tests_run'] == 31 and tests['successful'] and tests['failures'] == tests['errors'] == 0
assert tests['source_stable'] and tests['source_hashes_before'] == tests['source_hashes_after']
for name, expected in tests['source_hashes_after'].items():
    assert sha(A / name) == expected
assert not tests['torch_imported'] and not tests['real_ssh_calls'] and not tests['real_gpu_or_native_calls']
integration = load(B / 'adapter_actual_guard_integration.json')
assert integration['adapter_sha256'] == sha(A / 'adapter.py') and integration['remote_calls'] == 0
assert all(v['current_owner_context_authorization_guard'] == 'passed' and v['local_reserved_slot_check'] == 'blocked' for v in integration['observations'])
assert not (B / 'hrc_execution').exists()

repo = ROOT / 'Cluster'
run = lambda args: subprocess.check_output(args, cwd=repo, text=True, encoding='utf-8').strip()
assert run(['git', 'rev-parse', 'HEAD']) == COMMIT
assert not run(['git', 'diff', '--cached', '--name-only'])
model_prep = load(P / 'diagnostic_bundles/tick_16b87793/hrc_prepare/preparation.json')
for name, expected in model_prep['source_hashes'].items():
    assert sha(repo / name) == expected, name
native_dir = P / 'diagnostic_bundles/tick_86e41faa/hrc_native_prepare'
assert sha(native_dir / 'preparation.json') == release['frozen_preparation_sha256']
native_prep = load(native_dir / 'preparation.json')
for name, expected in native_prep['prepared_file_hashes'].items():
    assert sha(native_dir / name) == expected, name
protected = load(P / 'diagnostic_bundles/tick_16b87793/protected_worktree_before.json')['protected_existing_worktree']
assert len(protected) == 28
for item in protected:
    assert sha(repo / item['path']) == item['sha256'], item['path']

save(B / 'adapter_independent_review.json', {
    'recorded_at': NOW, 'reviewer': '/root', 'candidate_id': CID,
    'status': 'OFFLINE_ORCHESTRATION_PREPARATION_CHECKED_NOT_NATIVE',
    'preparation': ref(A / 'preparation.json'), 'release': ref(A / 'adapter_release.json'),
    'source_hashes': release['source_hashes'],
    'independent_orchestration_tests': ref(A / 'independent_review/final_validation_r2.json'),
    'tests_run': 31, 'failures': 0, 'errors': 0,
    'actual_workspace_guard_integration': ref(B / 'adapter_actual_guard_integration.json'),
    'all_prepared_file_hashes_verified': True, 'all_frozen_native_worker_hashes_unchanged': True,
    'nine_model_YAML_hashes_unchanged': True, 'protected_28_existing_files_unchanged': True,
    'local_HEAD': COMMIT, 'git_index_empty': True,
    'earlier_negative_evidence': [ref(A / 'independent_review/initial_snapshot_failure_reproduction.json'), ref(A / 'independent_review/intermediate_log_classification.json')],
    'fixed_tooling_findings': ['canonical string GPU assignment now equals integer assignment', 'all six original owner binding fields required', 'ordinary/dependency waiting does not reserve; canonical uncertain launch still reserves'],
    'scientific_implementation_revisions': 0,
    'external_review_anchor_required': 'Compare exact candidate execution_adapter preparation/release SHA externally before importing/invoking source. Internal consistent hashes alone do not prove review.',
    'formatter_implemented': False, 'native_semantic_pairing_reviewed': False,
    'new_adapter_ssh_executed': False, 'production_binding_manifest_lease_created': False,
    'native_smoke': 'NOT_RUN', 'resources': 'NOT_RUN', 'efficacy': 'UNKNOWN',
    'remaining': 'Actual empty authorized slot; fresh binding/manifest/lease/stage; four genuine worker results; semantic/pair audit; standard summaries; canonical admission/queue/dispatch.'
})

probe = load(B / 'native_resource_check.json')
data = probe['data']
assert probe['returncode'] == 0 and data['hostname'] == 'dl04-MS-7E06' and not data['gpu_computation_started']
for e in data['experiments'].values():
    assert e['pid_exists'] and e['exact_argv_cwd_match']
    assert e['native_progress'][1]['step'] > e['native_progress'][0]['step']
observed = data['observed_at']
retry = (dt.datetime.fromisoformat(observed) + dt.timedelta(hours=1)).isoformat()
command = 'python -B D:/project/cluster_project/pipeline/diagnostic_bundles/tick_9b40ab74/observe_resources.py --output native_resource_check.json'
save(B / 'hrc_resource_block.json', {
    'recorded_at': NOW, 'candidate_id': CID, 'experiment_id': 'M208-HRC',
    'kind': 'resource_check', 'result': 'blocked', 'command': command,
    'evidence': ref(B / 'native_resource_check.json'), 'observed_at': observed,
    'allowed_server': 'server-4', 'allowed_physical_gpus': [0, 1], 'max_tasks_per_gpu': 1,
    'actual_contexts': data['contexts'],
    'native_progress': {k: v['native_progress'] for k, v in data['experiments'].items()},
    'authorized_empty_slot_available': False, 'slot_status_changed_since_previous_tick': False,
    'important_observation': 'Both physical UUIDs contain the exact original training contexts with increasing native steps. Low utilization is not an idle slot.',
    'native_HRC': 'NOT_RUN', 'resources_HRC': 'NOT_RUN',
    'no_staging_worker_GPU_queue_or_running_mutation': True,
    'adapter_preparation_only': ref(B / 'adapter_independent_review.json'),
    'next_action': 'Preserve both original runs; externally verify frozen adapter/worker hashes before future fresh-owner authorized idle-slot execution and actual four-result review.'
})

env = os.environ.copy()
env['PROJECT_ROOT'] = 'D:/project'
before = set((P / 'decisions').glob('*_next_batch.md'))
decision_cmd = ['C:/Program Files (x86)/Git/bin/bash.exe', 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh', 'cluster_project', 'next_batch', 'HRC adapter preparation while both GPUs are busy', 'Freeze reviewed adapter; await real idle slot',
    '两卡原生训练正常且每卡限1任务；先补齐HRC当前owner绑定、独立stage、四结果编排和精确跨轮只读reconcile。31项离线mock及实际本地owner/占槽拒绝通过，不是原生/资源/准入PASS；负测试与旧版本保留，模型修订0。',
    'pipeline/diagnostic_bundles/tick_9b40ab74/adapter_independent_review.json; pipeline/diagnostic_bundles/tick_9b40ab74/native_resource_check.json; preparation SHA1ab29434e5a1e4f0144fd38e22d83f1ae561813973ed0468e64f65aac6c9a568']
decision = subprocess.run(decision_cmd, env=env, capture_output=True, text=True, encoding='utf-8', check=True)
created = set((P / 'decisions').glob('*_next_batch.md')) - before
assert len(created) == 1
decision_path = created.pop()

w = load(P / 'research_work.json')
cs = w['candidates'].values() if isinstance(w['candidates'], dict) else w['candidates']
c = next(x for x in cs if x['id'] == CID)
assert c['stage'] == 'blocked' and c['blocker_kind'] == 'exclusive_gpu_slot' and c['code_commit'] == COMMIT
paths = [B / 'observe_resources.py', B / 'native_resource_check.json', B / 'hrc_resource_block.json', B / 'source_evidence_reuse_check.json', B / 'adapter_actual_guard_integration.json', B / 'adapter_independent_review.json', A / 'preparation.json', A / 'adapter_release.json', A / 'adapter.py', A / 'remote_ops.py', A / 'README.md', A / 'static_validation_r2.json', A / 'independent_review/final_validation_r2.json', A / 'final_result_boundary_review_r2.json', A / 'independent_review/initial_snapshot_failure_reproduction.json', decision_path]
existing = {e['path'] for e in c['evidence']}
for path in paths:
    if ref(path)['path'] not in existing:
        c['evidence'].append(ref(path))
c['blocked_at'] = observed
c['retry_after'] = retry
c['blocker'] = 'Both authorized server-4 physical GPUs remain occupied by exact verified original native runs (GPU0 M207-HAP PID979955, GPU1 M206-CGCA PID732137) with increasing native steps; max1 task/card.'
c['execution_adapter'] = {
    'status': 'PREPARED_UNEXECUTED', 'preparation': ref(A / 'preparation.json'),
    'release': ref(A / 'adapter_release.json'), 'adapter': ref(A / 'adapter.py'),
    'remote_ops': ref(A / 'remote_ops.py'), 'README': ref(A / 'README.md'),
    'independent_tests': ref(A / 'independent_review/final_validation_r2.json'),
    'root_review': ref(B / 'adapter_independent_review.json'),
    'actual_local_guard_integration': ref(B / 'adapter_actual_guard_integration.json'),
    'external_anchor_required': True, 'standard_result_formatter_implemented': False,
    'native_execution_tested': False, 'remote_adapter_execution_tested': False,
    'active_binding_manifest_lease_created': False,
    'provenance': 'Exact saved preparation/release/source hashes are external review anchors. Old preparation timestamps are historical; create current execution_binding instead of altering old provenance.'
}
c['next_action'] = 'Preserve original runs. After an actual current authorized server4GPU0/1 opening, first externally verify candidate.execution_adapter exact preparation/release/source hashes, frozen worker hashes and current policy/owner/context/deadline. Use fresh execution_binding/manifest/lease/isolated stage and live idle/UUID/3flocks checks for four real runs: M95/HRC native TRAIN2 smokes and original-resource pair. Budget all four within original deadline; reconcile exact original request/stage/PID/startticks/argv/result after uncertainty, no blind replay or deadline renewal. Raw completion is not admission: audit real losses/gradients/path/mean control, both batch fingerprints, original resource input/handlers/bs1/warm20/repeat100/unsupported/memory scopes; then build standard native_smoke/resource summaries and satisfy closure.admission before original-YAML queue/canonical gated dispatch. Efficacy UNKNOWN.'
w['tick_attempt'] = {
    'tick_started_at': owner['generated_at'], 'candidate_id': CID,
    'kind': 'resource_check', 'result': 'blocked', 'command': command,
    'observation': '08:08:58 Shanghai pinned server4/physical UUIDs/NVML/exact original PID/starttime/argv/cwd matched. GPU0 HAP native13/50 steps2540→2541, GPU1 original full-resume CGCA native21/50 steps1844→1845. Both cards occupied, max1 task/card. Prepared and independently checked offline adapter (31 mocks plus actual local owner guards/busy-slot refusal), no HRC native/resource computation, remote staging, active execution lease, admission or queue operation.',
    'evidence': [ref(B / 'native_resource_check.json'), ref(B / 'hrc_resource_block.json'), ref(B / 'adapter_independent_review.json')]
}
w['updated_at'] = NOW
save(P / 'research_work.json', w)

memory = (P / 'codex_memory.md').read_text(encoding='utf-8')
lines = memory.splitlines()
replacements = {
    '- owner01': '- owner01a159c5-29ab-7a22-ba7f-e79174757253实际环境/execution_mode一致。前轮4059b69cca96469683d45a04a4517067 FINALIZED/released与headless lock/pending消失已核验。当前9b40ab74894049cda10820d24f3bcc97 DESIGN，上海10-22 08:08:03快照/原deadline09:08:03（UTC00:08:03.828030/01:08:03.828030）；begin先监控派发，2running/0waiting，无新terminal/operational issue。',
    '- M206-CGCA GPU1原full-resume保持': '- M206-CGCA GPU1原full-resume保持：08:08:58 PID732137/starttime21298582/--resume argv/cwd匹配，native21/50 1844→1845、log新鲜.160s；08:08 monitor当前epoch21/Best.4953/noimprove3/10（序列.4939/.4953/.4916/.4902/.4909），不把当前epoch当best产生epoch。例行在训进度，效益待终态；原恢复best.4751223027706146历史分开。',
    '- M207-HAP GPU0原进程保持': '- M207-HAP GPU0原进程保持：08:08:58 PID979955/starttime21613920/cwd/argv匹配，native13/50 2540→2541、log新鲜.375s；08:08 monitor当前epoch13/Best.4897/noimprove0/10（序列.4801/.4789/.4772/.4813/.4897），当前epoch不代表最佳产生epoch。完整训练效益待终态，不依早期验证改机制/选参。',
    '- M208-HRC stable': '- M208-HRC stable hierarchy-bottom-up-refined-token-composition，localcommit9e543af623acd7fa9bd4a3f81ce79c932e98774a（仅8独立model源+1原生YAML）。h0=μ0+F0(LNμ0)，u1=mean_ids1(h0)，h1=u1+F1(LNu1)，u2=mean_ids2(h1)，h2=u2+F2(LNu2)；原3FFN各一次、rawbanks/FPS/IDs/CSORT/HCG/最后inst保持。9hash及冻结worker11hash本轮再核不变，native/资源NOT_RUN，blocked/resumevalidation/exclusive_gpu_slot；08:08:58双卡占用实证，retry UTC01:08:58.169288或真实空卡事件（重试时间不延长本轮deadline）。',
    '- 三账保持': '- 三账保持M205 complete/done_earlystop，M207-HAP running/GPU0/PID979955与M206-CGCA running/GPU1/PID732137，launch_verifiedtrue。08:08:58两卡各仅原context，显存GPU0 19805MiB/GPU1 19811MiB、原生步数递增；GPU0 util18%仍有19752MiB原context，不是空卡。HRC仅candidate资源hold，queue waiting0。',
    '- server4 pinned': '- server4 pinned192.168.1.115/dl04-MS-7E06，allowed[0,1]/max1card；GPU0 UUIDGPU-958e741a-e5cf-127e-ffe8-9b984e1f404c，GPU1 UUIDGPU-7f82edb9-f620-8045-caea-a75232265cd1。root=/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1；remoteHEADf51823bb为历史实测（本轮未查询/同步/切换），common/M206既有源码保持。',
    '- 未来HRC执行adapter缺项': '- HRC执行adapter已在tick_9b40ab74/hrc_execution_adapter冻结：preparation SHA1ab29434e5a1e4f0144fd38e22d83f1ae561813973ed0468e64f65aac6c9a568，release SHAf2b3cdfe7a63cacf65e0d38837c4df1211715a31320f4d808d569c855a9e6d83，adapter0f0663ec…/remote_ops3b914701…。未来root先核candidate.execution_adapter中这组外部锚，再核code；内部自洽hash不能证明被审。原冻结worker不改，用当前新execution_binding/manifest/lease/stage；四进程总体预算仍受原deadline约束，无active binding/manifest/lease或远端stage。',
}
for i, line in enumerate(lines):
    for prefix, replacement in replacements.items():
        if line.startswith(prefix):
            lines[i] = replacement
            break
memory = '\n'.join(lines) + '\n'
memory = memory.replace('本轮tick86e41faa/held_route_boundary_check.json仅有界程序核8旧记录逐项保持', '最近tick86e41faa/held_route_boundary_check.json已有界核8旧记录保持；本轮9旧blocked均notdue未重开')
memory = memory.replace('本轮未重复概念/静态审查或为填额度制造新candidate。', '本轮未改模型或为填额度制造新candidate；只准备现有HRC执行adapter并做其离线/本地guard检查。')
memory = memory.replace('当前未写adapter或执行lease。', 'adapter已准备，原生/标准formatter仍待真实结果。')
insert = '- adapter的31项独立离线mock与静态检查通过，root对实际owner/context/授权guard通过且两卡已登记运行被拒，0transport；pce核raw-result边界。初版字符串GPU/缺owner字段两缺陷及普通waiting过严保护修正，旧source/失败/27PASS均保留；属于工具QA，model修订0。普通waiting/依赖hold不占卡，running/claiming及canonical启动未确认仍占槽。\n- adapter只返回raw四结果，未实现标准smoke/resource语义与配对formatter、receipt/queue/dispatch；不能以raw completed或31mock代签native/准入。真实两批指纹、路径/grad/control、原profiling输入/handler/unsupported及memory范围须核后另建标准汇总。跨tick status/reconcile可精确只读旧stage/request/PID/startticks/argv/result，疑似超时不重放/kill/删现场。\n'
memory = memory.replace('## Open Questions And Risks\n', '## Open Questions And Risks\n' + insert)
memory = memory.split('## Last Tick\n')[0] + '''## Last Tick
- 本轮tick_9b40ab74先begin监控/派发；08:08:58 strict known-host/pinned hostname/physicalUUID/NVML/原PID/starttime/argv/cwd实证，GPU0 HAP13/50 2540→2541、GPU1 CGCA21/50 1844→1845；双卡原运行健康，未占用新计算/更动运行。
- 新准备现有HRC execution adapter与31项离线mock；初版负证据和旧版本完整保留，final preparation/release/source已外部锚入候选，root actual localguard/占槽拒绝通过，模型9源、worker11hash及28既有脏文件保持、index空。无新SSH adapter执行/stage/activelease/native/resource/标准formatter。
- tick_attempt绑定本轮generated_at2026-10-22T00:08:03.828030+00:00及HRC fresh resource_check/blocked；0新candidate/0model修订/0commit/0准入/0queue/0launch/0terminal，1现有候选执行工具准备。9旧hold notdue未重开；不是路线穷尽、停止研究或新的科学结论。
- 实际空卡后先外部核候选adapter prep/release/code锚+不变worker，当前owner新binding/manifest/lease/stage与live idle/3flocks，再真实双target TRAIN2及原资源配对；语义与配对核完生成标准smoke/资源汇总，closure准入后当轮入队/派发。权限足够，无新审批。
- 当前9b40ab74收尾以实际report/finish/receipt为准，不预写PASS；核FINALIZED/released及headless锁/pending消失，释放后不写项目。例行在训/资源等候状态未变，内部工具准备不构成须用户通知的状态变化，本轮DONT_NOTIFY。
'''
assert len(memory.splitlines()) < 120
assert sum(1 for line in memory.splitlines() if line.startswith('## ')) == 7
(P / 'codex_memory.md').write_text(memory, encoding='utf-8')

notes = {
    'actions': [
        '08:08:58上海时间，经strict known-host、pinned hostname和物理UUID核server4：GPU0原HAP13/50步2540→2541，GPU1原CGCA full-resume21/50步1844→1845，原PID/starttime/argv/cwd及新鲜日志匹配；每卡1任务已满，不运行HRC原生检查。',
        '复用HRC原9e543af的8源+1原生YAML和冻结worker：逐字节hash一致，28个既有脏/未跟踪文件保持、index空，未同步/提交/切换远端源码。HRC native/resource仍NOT_RUN，训练效益UNKNOWN。',
        '为现有HRC新增并冻结执行adapter：当前owner/context/deadline/goal/授权/白名单和物理UUID绑定、独立stage、四真实worker请求编排、跨轮精确只读status/reconcile。31项独立离线mock和静态检查通过；root在真实本地账上验证当前guard通过、两卡运行占槽被拒，0transport。未创建生产binding/manifest/lease或远端stage，未执行新adapter SSH/GPU/torch。',
        '保留初版字符串GPU/缺owner字段两缺陷失败重现、mock fixture分类、旧source与27PASS；再修普通waiting不应占卡的问题，最终31PASS仅绑定0f0663ec adapter/3b914701 remote_ops，属执行工具QA、模型实现修订0。pce独立核结果/准入边界不变。',
        '候选追加prep1ab29434、releasef2b3cdfe及source外部锚、根审阅/实际资源证据、明确NOT_RUN和下一步；更新7段memory及next_batch决策，未重开9个notdue旧hold，未改goal/资源边界/调度/既有运行。'
    ],
    'decisions': [
        '两卡实测仍被原训练占用，HRC保持blocked/exclusive_gpu_slot、resume_stage=validation；retry为实测资源时间加1h，真实空卡事件可提前唤醒，不延长本轮原deadline。',
        'adapter内部一致hash不是审阅授权；未来root先以候选中的精确preparation/release/source作为外部锚，再建立当前绑定。四进程须服从原deadline；超时只核精确旧stage/request/PID/startticks/argv/result，不盲重放/删除/kill。',
        '当前adapter无standard formatter、native语义/配对验证、receipt或queue动作；原始execution_completed与31mock不得代签准入。获得真实四结果并核两TRAIN批指纹、finite loss/backward/新路径/control和原资源协议后，另建标准汇总，按现有closure准入/原YAML队列/派发。smoke内存含observer/probe，纯TRAIN峰值UNKNOWN仅支持项，不加新门。',
        '本轮0新候选/0模型修订/0commit/0准入/0入队/0启动/0终态；1现有候选工具准备。没有新科学结论或用户处理项；例行训练/资源等待未变，遵循静默通知。'
    ]
}
save(B / 'notes.json', notes)
print(json.dumps({'persisted': True, 'candidate': CID, 'adapter_preparation': ref(A / 'preparation.json'), 'root_review': ref(B / 'adapter_independent_review.json'), 'resource_block': ref(B / 'hrc_resource_block.json'), 'decision': ref(decision_path), 'notes': str(B / 'notes.json'), 'memory_lines': len(memory.splitlines()), 'original_deadline_at': owner['deadline_at']}, ensure_ascii=False))
