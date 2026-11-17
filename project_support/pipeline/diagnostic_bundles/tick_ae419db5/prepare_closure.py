"""Persist current bounded preparation and real external resource holds."""
from datetime import datetime, timedelta, timezone
import json
import os
import shutil
import subprocess
from ops import ROOT, OUT, CID, TOKEN, GOAL, guard, save, evidence, tick, now

guard(180)
cpu = tick.load(OUT / 'native_cpu_probe.json')
capability = tick.load(OUT / 'native_cpu_fps_capability.json')
binding = tick.load(OUT / 'native_backend_binding.json')
witness = tick.load(OUT / 'source_first_index_witness.json')
resources = tick.load(OUT / 'current_resources_and_training.json')
assert cpu['execution_completed'] and not cpu['cuda_initialized'] and len(cpu['cohort']) == 4
assert all(row['native_fixed_anchor_identity_equal'] and row['native_fixed_anchor_relabel_equal']
           and row['changed_fixed_anchor_assignments'] == 0 for row in cpu['cohort'])
assert not capability['cpu_fps_supported'] and capability['error'] == 'CPU not supported'
assert not capability['cuda_initialized'] and not binding['cuda_initialized']
assert witness['source_old_zero_present'] and not binding['source_binary_correspondence_proved']
cards = resources['server4']['cards']
assert cards['0']['contexts'].startswith('1085297,')
assert cards['1']['contexts'] and all(cards['1']['locks_available'].values())
assert resources['server3']['ssh_returncode'] == 255
observed = datetime.fromisoformat(resources['server4']['observed_at'])
retry = observed + timedelta(hours=1)
assert retry > datetime.now(timezone.utc)
work = tick.load(ROOT / 'pipeline/research_work.json')
primary_id = 'hierarchy-native-batch-minimum-resolution'
aux_ids = ['m95-native-relation-other-sign-conflict', 'm95-native-main-role-weight-precedence',
           'm95-native-secondary-positive-mass', 'm95-native-between-pair-support']
auth = tick.load(ROOT / 'pipeline/authorizations/server4_gpu1_20261019.json')
assert auth['source_role'] == 'human' and auth['source_message'] == '授权GPU1 可以做实验'
scope = save('scope_recheck.json', {'observed_at': now(), 'goal_sha256': GOAL,
    'resource_authorization': evidence(ROOT / 'pipeline/authorizations/server4_gpu1_20261019.json'),
    'checked_ids': aux_ids, 'source': 'Latest goal/research_mainline and direct human resource authorization in owning chat.',
    'decision': 'No new authorization restores auxiliary supervision priority. GPU1 permission remains valid but is resource-only. Preserve all original science/evidence/priority and do not recover M201/M204 or ask the same permission again.',
    'scientific_result': None, 'scope_changed': False})
aux_retry = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
for row in work['candidates']:
    if row['id'] in aux_ids:
        assert row['stage'] == 'blocked' and row['blocker_kind'] == 'human_authorization'
        row['retry_after'] = aux_retry
        row['last_scope_check_at'] = now()
        row['evidence'].append(evidence(scope))
analysis = save('analysis.json', {'observed_at': now(), 'token': TOKEN, 'candidate_id': CID,
    'cpu_fixed_anchor_control': {'scene_count': 4, 'valid_superpoints': [row['valid_superpoints'] for row in cpu['cohort']],
        'identity_passed_scenes': 4, 'inverse_relabel_passed_scenes': 4, 'changed_assignments': [0,0,0,0],
        'scope': 'Exact native partition_points CPU method and fixed first256physical-row anchors,NOTnativeFPS anchors or GPU model prefix. Geometry centroids were CPU-prepared from original TRAIN dataset transforms,not proved bitwise equal to GPU scatter means.'},
    'native_fps_cpu_capability': {'supported': False, 'observed_error': 'CPU not supported', 'cuda_initialized': False},
    'source_risk_witness': {'supplied_kernel_initial_old_index': 0, 'first_physical_row_changes_in_scenes': 4,
        'compiled_source_correspondence_proved': False, 'compiled_seed_behavior': None,
        'physical_recomputed_hierarchy_effect': None, 'mask_effect': None},
    'scientific_status': 'Bounded conditional CPU control/source evidence only. Native FPS/full hierarchy/task impact/noise/efficacy/novelty remain UNKNOWN;no mechanism admission or canonical-seed repair.',
    'resource_snapshot_at': resources['server4']['observed_at'],
    'resource_status': 'GPU0sameM204;GPU1twoforeigncomputecontexts and15GiB-classoccupation,despite3projectlocksavailable;server3SSHtimeout/255 leaves itsGPU1unknown,notoccupiedoridle.',
    'existing_primary': {'id': primary_id, 'decision': 'Keep original4-pair/fixedquery/protocol/failures;no repeated562scene census or occupied-GPUattempt. Fresh0:22resource evidence reaffirms the actual hold.'},
    'this_tick_outputs': {'new_stable_candidates': 1, 'native_cpu_fixed_anchor_scenes': 4,
        'native_cpu_fps_capability_attempts': 1, 'prepared_native_geometry_protocols': 1,
        'new_gpu_diagnostic_attempts': 0, 'native_gpu_partition_runs': 0, 'mask_readouts': 0,
        'native_backwards': 0, 'new_models': 0, 'admissions': 0, 'new_training': 0},
    'evidence': [evidence(OUT / name) for name in ('relabeling_protocol.json','native_cpu_probe.json',
        'native_cpu_fps_capability.json','native_backend_binding.json','source_first_index_witness.json',
        'native_geometry.json','native_manifest.json','native_readiness.json','current_resources_and_training.json')],
    'retry_after': retry.isoformat(),
    'stop_scope': 'Actual resource block of two prepared primary diagnoses,not exhausted independent routes/no-information-gain/expired deadline/missingpermission. Auxiliary scope rechecks are not new experiments or scientific progress.'})
for row in work['candidates']:
    if row['id'] not in (CID, primary_id):
        continue
    row.update(stage='blocked', failure_scope='inconclusive', blocker_kind='live_external_gpu_occupation',
        required_server='server-4', physical_gpu=1, retry_after=retry.isoformat(), updated_at=now(),
        blocker='At2026-10-20 00:22Shanghai GPU1 has2externalcomputecontexts,15667MiB/util97%;one-task/card andno-sharing guard applies. GPU0 is originalM204 withheldlocks. server3SSHtimeout255 means itsGPU1unknown/unavailable,not provenoccupied.',
        unblock_condition='Fresh authorizedGPU1UUID/context/idleness/all3exclusive-lockchecks pass;or fully recovered authorizedserver3GPU1 with exact native assets/runtime/source andexclusivechecks. Timer or available project locks alone never proves idleness;do notevict/reset/restart.',
        non_gpu_preparation_completed=True, scientific_admission=False)
    if row['id'] == CID:
        row['next_action'] = 'Under a NEW current-tick lease run frozen original native FPS/composedhierarchy relabeling test on actualidleauthorizedGPU1. Preserve exact identity/inverse controls and source-vs-binary uncertainty. Mask/task effects are a separate pending diagnostic,not a trained repair.'
        row['gate_result'] = '4nativeCPUfixed-anchor controls passed with0assignmentchanges;providedCUDA source firstindex0 witness recorded. Exact original binary CPUattempt returnedCPUnotsupported;0CUDA hierarchy/mask/backward runs,scientificadmissionFALSE.'
    else:
        row['next_action'] = 'When an authorizedGPU1 is trulyidle/exclusivelyleased,resume SAME original4-pair fixed-query resolution protocol atpair0 underNEWlease. Do not reuse oldlease/rerun census/changecap/tolerance/targets or count blocked attempts as completed experiments.'
    row['evidence'].extend([evidence(OUT / 'current_resources_and_training.json'), evidence(analysis)])
work['design_cycle'] = {'updated_at': now(), 'stop_reason': 'external_resource_blocked',
    'attempted_ids': [CID, primary_id], 'retry_after': retry.isoformat(),
    'evidence': [evidence(analysis), evidence(OUT / 'current_resources_and_training.json'), evidence(OUT / 'native_cpu_fps_capability.json')],
    'resume_condition': 'Actual authorizedGPU1contextrelease plus fresh UUID/idleness/runtime/asset/3exclusive-lock checks;server3alternative only after full recovery/verification. Preserve all original protocols and scopeholds.',
    'scope': 'Useful nonGPUcontrols,source/binarybinding,CPUcapability andnativeprotocol preparation completed;actualremainingtestsrequireCUDA. Noindependent-route-exhaustion or scientificPASSclaim.'}
guard()
tick.save(ROOT / 'pipeline/research_work.json', work)
shutil.copyfile(ROOT / 'pipeline/codex_memory.md', OUT / 'memory_before.md')
index = ROOT / 'pipeline/decisions/_index.md'
previous_index = index.read_bytes()
environment = os.environ.copy()
environment['TZ'] = 'CST-8'
decision = subprocess.run(['C:/Program Files (x86)/Git/bin/bash.exe',
    'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh', 'cluster_project', 'other',
    'Native relabel audit prepared; external GPU occupation.',
    'Keep two original protocols; no sharing or new training.',
    '4场景原生CPU固定中心重编号控制一致；原始FPS扩展实测CPU不支持。源码首索引0仅为风险见证，编译行为/共成员/mask未知。保留M204和原分辨率协议，GPU1实际外部占用，server3不可达；不新增训练或重复索要授权。',
    str(analysis)], capture_output=True, text=True, encoding='utf-8', errors='replace', env=environment, timeout=20)
assert decision.returncode == 0, decision.stderr
assert index.read_bytes().startswith(previous_index)
save('decision_record_receipt.json', {'observed_at': now(), 'returncode': decision.returncode,
    'stdout': decision.stdout, 'stderr': decision.stderr, 'existing_index_bytes_preserved': True,
    'time_zone': 'Asia/Shanghai(UTC+08:00)'})
notes = save('report_notes.json', {'actions': [
    '本轮2026-10-20 00:11:09上海快照，design；归属和旧调度Disabled已核对，仅一次成功begin，首次审批超时未执行。目标0.5100/历史最佳0.5020/差0.0080；GPU1已有授权，资源/科学约束均未改。',
    '本轮监控M204 best约0.4993，21/50、no_improve2/10；相对上轮约0.4944有本实验内的新best，但未超历史M95、未到目标，也不是终态匹配效益。00:22:02原PID1085297原生日志Train21/50的1914至1918/4686增长且mtime新鲜，无近期Traceback；未重启/迁移/改代码。',
    'bootstrap先登记1个稳定diagnosis候选hierarchy-native-superpoint-relabeling-audit，再执行4个固定TRAIN场景的原生partition_points CPU方法。固定前256个物理行作条件中心，身份和重编号逆变换均一致，改变归属数为0/0/0/0。它不是FPS中心、GPU模型prefix或全层级PASS；CPU准备的超点均值也未证明与GPU scatter逐位一致。',
    '查明原生导入绑定：工程Python wrapper加当前安装的二进制扩展，均已哈希冻结；提供的CUDA源码old=0/idxs[0]只有源码级风险见证，未证明当前二进制行为、完整物理共成员变化或mask损伤。另实际调用原始FPS扩展CPU分支一次，返回RuntimeError:CPU not supported；CUDA未初始化，不是模型科学失败。',
    '已冻结4场景几何、原始FPS/组合层级/身份及逆置换/簇标签无关共成员测试代码和manifest，语法核对通过；因实际资源占用，本轮0GPU诊断尝试、0原生GPU分区/掩码重放/backward，0新模型/准入/队列项/训练，不把准备或CPU控制称为GPU测试成功。',
    '00:22:02上海只读核实：server4GPU0为原M204，19863MiB/17%；GPU1为两项外部计算，15667MiB/97%，项目三锁可用但计算上下文非空，仍不得共享。00:22:12 server3SSH255连接超时，其GPU1占用未知，不当作空闲或已占用。未读取密码、抢卡、reset、停他人进程或改其他项目/调度。',
    '原分辨率稳定ID已到复查点：复用原4对固定query协议及旧562场景证据，只增加本次实际占用证据，不重复全场景普查或在占用GPU上再次启动。4个辅助监督ID按到期scope检查仍无优先级恢复证据，仅保留原科学状态并做有界回查，不算本轮4项实验，也不反复索要相同确认。',
    '本轮实际产出为1新稳定诊断、4场景原生CPU条件控制、1次原始扩展CPU能力测试、源/二进制及几何协议冻结和资源复查；所有mask效果/训练效益/新颖性仍未知。用量窗口仅本轮begin(2026-10-19T16:11:09Z)至finish收据，排除之前读取/晚到记录/末尾回复；具体用量此处未知，以收据为准，缓存属输入、reasoning属输出，不重复相加、不当账单。本报告保存时finish尚未执行。'
], 'decisions': [
    '本轮科学状态为有限CPU控制及源码风险证据，不是新机制有效、FPS缺陷已证明或训练准入。保留旧全部严格数值失败，不用新0归属变化覆盖旧full-source置换1e-6失败，不实现canonical-seed单算子修补、调参或改名重开FLE/HDS/routing。',
    '两项主线诊断的非GPU准备已完成，下一项实际测试需要原生CUDA；按真实live_external_gpu_occupation保留，复查时间见账本，计时器不等于GPU释放。不称独立路线穷尽/no_information_gain/全局暂停或拖到deadline，不凑第二个变体。',
    '待真实合法空闲后，优先原固定query分辨率pair0，再原生重编号几何控制，均用新的当前租约和UUID/上下文/三锁检查。server3只有连接、原生资产与独占资源全面恢复才可替代。M204现有训练自然继续；不自动恢复M201/M204，不需要新的GPU1授权。'
]})
print(json.dumps({'candidate_id': CID, 'stage': 'blocked', 'resource_retry_after': retry.isoformat(),
    'aux_scope_retry_after': aux_retry, 'analysis': evidence(analysis), 'notes': evidence(notes),
    'finish_still_required': True}, indent=2))
