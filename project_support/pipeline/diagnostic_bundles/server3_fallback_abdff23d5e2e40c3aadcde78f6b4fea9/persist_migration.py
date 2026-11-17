"""Persist a bounded user-authorized fallback without admitting a new model."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from run_remote import BUNDLE, ROOT, TOKEN, guard, tick

owner=guard()
PRIMARY='m95-hierarchical-mask-feature-path-audit'
work_path=ROOT/'pipeline/research_work.json'
memory_path=ROOT/'pipeline/codex_memory.md'
before=tick.load(BUNDLE/'work_before.json')
assert tick.load(work_path)==before, 'Concurrent research edits must be preserved.'
assert memory_path.read_bytes()==(BUNDLE/'memory_before.md').read_bytes()
assert not (BUNDLE/'persistence.json').exists()
goal=tick.load(ROOT/'pipeline/goal.json')
goal_before=tick.load(BUNDLE/'goal_before.json')
unchanged_goal=copy.deepcopy(goal)
last_constraint=unchanged_goal['constraints'].pop()
assert last_constraint.startswith('[USER-ALLOCATION 2026-10-16]')
assert unchanged_goal==goal_before
assert len(goal['constraints'])==21 and len(goal['banned'])==11
assert goal['research_mainline']['primary_axis']=='hierarchical_attention_point_feature_update'
queue_sha=tick.digest(ROOT/'pipeline/queue.json')
def ref(path):return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
def result(name):
    data=tick.load(BUNDLE/(name+'_result.json'))
    assert data['returncode']==0 and len(data['results'])==1
    return data['results'][0]
deployment=result('deploy_server3')
preparation=result('native_capture_server3_prepare_after_build')
capture=result('native_capture_server3')
analysis=result('native_capture_analysis_server3_v2')
postverify=result('postverify_server3')
build=result('extension_build_distutils_server3')
assert build['built'] and build['source_hashes_unchanged'] and not build['shared_environment_modified']
assert preparation['strict_state_load'] and preparation['model_parameter_tensors']==847
assert capture['network_forwards']==4 and capture['optimizer_steps']==0 and capture['physical_gpu']==1
assert capture['sha256']==analysis['capture_sha256']==postverify['capture_sha256']
assert analysis['unique_scenes']==4 and analysis['unique_expression_ids']==16
assert analysis['same_shape_cpu_identity_and_query_controls_passed']==4
assert analysis['expressions_with_padding']==analysis['expressions_with_message_change_above_original_1e_minus_6']==8
assert not analysis['prior_failures_reclassified'] and not analysis['task_harm_proven']
assert not postverify['compute_contexts'] and not postverify['tracked_changes']
assert all(state=='acquired_and_released' for state in postverify['flocks'].values())
assert tick.digest(ROOT/'Cluster/scripts/validate_pdc_20261009.py')=='00d58e60d96a61272d4c8719fbca85fab449252ea84311ee3af09be015b26c26'
tick.save(BUNDLE/'goal_after.json',goal)
summary={'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'user_authorization':ref(BUNDLE/'authorization.json'),'allocation':ref(BUNDLE/'allocation.json'),
    'goal_before':ref(BUNDLE/'goal_before.json'),'goal_after':ref(BUNDLE/'goal_after.json'),
    'old20constraints_and_all_other_goal_fields_unchanged':True,
    'target_server':'server-3','physical_gpu':1,'target_hostname':'sysu311-MS-7C59',
    'isolated_checkout':deployment['root'],'frozen_commit':deployment['commit'],
    'checkpoint_sha256':deployment['checkpoint_sha256'],
    'environment':'existing 3d-stmn; Python3.8.13/torch1.12.0+cu113; not modified',
    'isolated_extension_sha256':build['extension_sha256'],
    'reference_native_forwards':4,'unique_train_scenes':4,'unique_train_expressions':16,
    'two_repeat_appearances':32,'first_repeat_valid_point_rows':analysis['first_repeat_valid_point_rows'],
    'peak_allocated_bytes':capture['peak_allocated_bytes'],'peak_reserved_bytes':capture['peak_reserved_bytes'],
    'capture_sha256':capture['sha256'],'remote_capture_path':capture['path'],
    'native_same_shape_cpu_controls_passed':4,'padding_sensitive_expressions':8,
    'total_first_repeat_expressions':16,'scale_cosines':analysis['scale_cosine_expression_mean'],
    'native_cpu_gpu_message_max_delta':max(r['native_gpu_vs_cpu_message_delta'] for r in analysis['rows']),
    'native_gpu_repeat_message_max_delta':max(r['native_repeat_message_delta'] for r in analysis['rows']),
    'scientific_status':'validation; reference runtime block resolved; all six new-core admission booleans remain false',
    'migration_status':'isolated target deployed and unchanged reference native capture verified; no new-model training started',
    'new_training':0,'optimizer_steps':0,'new_core_backward':0,'new_admissions':0,
    'server4_jobs_signalled':0,'gpu_resets':0,'old_locks_deleted':0,'scheduler_changes':0,
    'postverify':ref(BUNDLE/'postverify_server3_result.json'),
    'historical_failures_preserved':True,'full_training_memory_and_efficacy':'unknown'}
tick.save(BUNDLE/'migration_summary.json',summary)
decision=subprocess.run(['C:/Program Files (x86)/Git/bin/bash.exe',
    'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh',
    'cluster_project','manual',
    'server4 remains blocked; user authorizes fallback to server3 GPU1.',
    'Use only server3 GPU1; isolated exact-commit M95 deployment and four native reference forwards verified; keep new-core training gated.',
    'Target was idle, pinned and exclusively leased. Original sources/config/weights preserved; 847 tensor strict load and native TRAIN capture succeeded. Preserve server4 jobs, M201 scope hold and all prior failures.',
    str(BUNDLE/'migration_summary.json')],text=True,encoding='utf-8',capture_output=True,timeout=30)
assert decision.returncode==0,decision.stderr
decision_path=Path(decision.stdout.rsplit('->',1)[1].strip())
assert decision_path.is_file() and decision_path.parent==ROOT/'pipeline/decisions'
evidence=[ref(p) for p in sorted(BUNDLE.glob('*.json')) if p.name not in ('work_before.json',)]
evidence.extend(ref(p) for p in sorted(BUNDLE.glob('*.py')))
evidence.extend(ref(BUNDLE/name) for name in ('port_prereg.md','extension_prereg.md','same_capture_prereg.md','memory_before.md'))
evidence.append(ref(decision_path))
work=copy.deepcopy(before)
old={c['id']:c for c in before['candidates']}
current={c['id']:c for c in work['candidates']}
assert len(current)==100
primary=current[PRIMARY]
assert primary['stage']=='blocked' and all(not g['passed'] for g in primary['gates'].values())
primary.update(stage='validation',required_server='server-3',required_gpu=1,
    next_action='Continue SAME point-feature ID using frozen native capture e4a7e636: preregister matched ancestor/uniform/support interventions against actual learned inputs before selecting the conditional hierarchy core. Match arithmetic paths under the ORIGINAL1e-6 controls and preserve all historical FAILs. New-core independent model/config, native backward, matched whole-model resources and all six admission gates remain unpassed; no queue launch or automatic M201 resume.')
for key in ('blocker','blocker_kind','retry_after','unblock_condition'):primary.pop(key,None)
primary['evidence'].extend(evidence)
primary['gates']['diagnosis']['status']='Actual frozen TRAIN capture and same-shape message-path sensitivity measured on4scenes/16expressions; causal task deficit and new-core premise remain unproved.'
primary['gates']['controls']['status']='Four native-input CPU identity/query controls pass;8of16 same-shape mean-path interventions change messages. New-core controls and prior12strictfloat32FAILs remain unresolved; no tolerance/backend/precision change.'
primary['gates']['resources']['status']='server3 GPU1 exact reference capture runs within1.31GB allocated/1.79GB reserved; no context and all3flocks released. New-core matched FLOPs/latency/peak memory and native backward remain unmeasured, not PASS.'
primary['findings']['server4_resource_before_fallback']=copy.deepcopy(primary['findings']['latest_resource_guard'])
primary['findings']['native_network_forwards']=4
primary['findings']['server3_migration']=ref(BUNDLE/'migration_summary.json')
primary['findings']['native_capture']=capture
primary['findings']['native_learned_input_controls']=ref(BUNDLE/'native_capture_analysis_server3_v2_result.json')
primary['findings']['latest_resource_guard']={'observed_at':postverify['observed_at'],
    'evidence':ref(BUNDLE/'postverify_server3_result.json'),'server':'server-3','physical_gpu':1,
    'ready_for_reference_capture':True,'ready_for_new_core_training':False,
    'scope':'Actual reference CUDA execution and released contexts/flocks; not new-core efficiency admission.'}
assert all(c==old[cid] for cid,c in current.items() if cid!=PRIMARY)
assert all(primary['gates'][name]['passed']==gate['passed'] for name,gate in old[PRIMARY]['gates'].items())
if 'design_cycle' in work:
    tick.save(BUNDLE/'previous_design_cycle.json',work.pop('design_cycle'))
work['manual_resource_migration']={'token':TOKEN,'candidate_id':PRIMARY,
    'evidence':ref(BUNDLE/'migration_summary.json'),'bounded_user_request':True,
    'science_status':'validation','resource_block_resolved':True,'new_training':False}
memory='''# Codex Research Memory
## Goal And Phase
- USER20261015 primary remains hierarchical attention/information interaction that actually updates point/superpoint inst_feats for query-mask prediction. Supervision/relations are auxiliary. Phase1 target.5100 unmet; no tuning, noN2 and all11bans preserved.
- USER20261016 resource fallback: only server-3GPU1, one slot; pinned sysu311-MS-7C59/192.168.1.194/UUID340de111-e7e4-ed2d-15c9-8ab6a253e4a0. server4/server6 new dispatch disabled; preserve their jobs and original locks. No scheduler change.
- Original20constraints/every other goal field unchanged; append allocation21 only. Goal SHA c73f9bff462e01d9294b80cadb8a04cdc045813861751bb86df1712561634fb7. Current owner01a04987-fdbe-7301-b2f0-f9b6ab60f74c, foreground only.
- Full previous memory and scientific history preserved verbatim in BUNDLE/memory_before.md; all100candidate records retained, only primary advanced.
## Champion And Baseline
- Historical M95-CTF-HCG-CSORT.5020; baseline.4894; target.5100/gap.0080. No new trained metric or efficacy this tick.
- Exact frozen M95 weights fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e and Gitf8457d3b657e66306a7fce1afb3d81d8ab874669 deployed to isolated server3 checkout; config/hierarchy hashes unchanged.
## Active Hypotheses
- SAME primary m95-hierarchical-mask-feature-path-audit now validation, NOT resource-blocked. Native TRAIN reference capture completed4forwards/groups0,60,101,124/4scenes/16uniqueexpressions/two repeats/32appearances; first-repeat valid point rows19372.
- Real learned-input same-shape mean-path intervention changes8of16expressions, all8with padding;8unpadded controls exact0. Max message changes.1685681343/.0791029930. This is module-path sensitivity, NOT causal task harm, an admitted normalization repair or trained gain.
- Four same-shape CPU identity/query-swap controls exact0 given fixed bank. Cross-scale point-readout cosines expression-balanced.814686/.619390/.828452 are descriptive, not proof of redundant/harmful scales or hierarchy benefit.
- Native-GPU vs CPU replay max8.58306884765625e-6; native-repeat max4.76837158203125e-6. Report as measured differences; no original1e-6 tolerance/backend/production-precision change or equivalence PASS.
- Conditional disjoint-support core remains prototype/not admitted. Next preregister ancestor/uniform/support interventions on this SAME native capture, retain matched arithmetic-path controls, and choose a core only after causal diagnosis; do not repeat old constructed numerical localization.
- All six NEW-core admission booleans remain false. CTF refinements/gather/gate update inst_feats; branch is query-blind GIVEN captured bank, not whole-model language independent.
## Closed Or Failed Directions
- Prior91rejected/4complete and other99records are unchanged. Four old supervision IDs remain auxiliary_scope_hold with historical gate sets unchanged; no automatic M201 recovery.
- Preserve all original12strictfloat32 prototype FAILs, random-weight cross-shape FAIL1.1920928955078125e-6, checkpoint-source constructed control and numeric-localization evidence. Native reference success does not erase or promote them.
- Original CPU prepare missing-extension failure, Ninja-wrapper failure and analyzer per-scene/per-expression indexing failure retained. Unchanged-source isolated setuptools build and corrected metadata v2 succeeded; these are environment/reporting repairs, not model revisions or hypothesis rejection.
- Banned gate/routing/residual/repeated-injection families remain closed; a masked-mean-only patch is not the user's hierarchy-attention innovation.
## Running And Queue
- Preflight SNAPSHOT/steady/running0/claiming0/waiting0/capacity1/budget1; immutable snapshot predates manual server3 fallback. Reserve5/target2/budget0. No new candidate/admission/variant/training/optimizer step.
- Isolated server3 root /sdc1/songcl/Project/Cluster_project/Cluster_hier_feature_abdff23d; existing3d-stmn Python3.8/torch1.12+cu113 not modified. Compiled ignored pointgroup extension with existingCUDA11.3/gcc7, original sources unchanged; CPU full-model strict847tensor load passed.
- GPU1 reference peak allocated1308473344bytes/reserved1786773504bytes. Postverify2026-10-16T00:30:10.723673Z total24268/free24267MiB/util0/no compute context; all3mappedflocks acquired/released; tracked checkout unchanged.
- Remote native capture269628449bytes at /sdc1/songcl/Project/Cluster_project/pipeline/server3_fallback_abdff23d/native_capture.pt SHAe4a7e63605bb60d9e9a543cd22ac2635a37627ee3db22d870122e1a254342e08. Do not recapture merely for a timer.
## Open Questions And Risks
- Full NEW-core training VRAM, native backward, FLOPs<=10G, relative memory/latency, mechanism controls, independent model/config, task harm and efficacy remain unknown/unpassed. Reference no-grad memory is NOT full-training feasibility.
- GPU use still requires fresh current whitelist/NVML/idleness and actual exclusive leases; CPU analysis can reuse capture without another GPU allocation. No resets, eviction, stale-lock deletion or server3GPU0 use.
- Sourcecode dirty validate_pdc_20261009.py SHA00d58e60d96a61272d4c8719fbca85fab449252ea84311ee3af09be015b26c26 preserved. Unrelated untracked BCCA directories were not read/modified/deployed.
- Keep fixed TRAIN/seed1999/epochs50/max_iters70/validation bounds and original strictFAILs. Do not fill an empty slot with unadmitted or renamed supervision work.
## Last Tick
- Current TOKEN, snapshotSNAPSHOT/deadlineDEADLINE unchanged, mode steady with explicit bounded user resource-migration request, not relabeled design. Primary blocked->validation; other99records and their gate sets unchanged; obsolete resource-stop cycle archived rather than faking exhaustion.
- BUNDLE/migration_summary.json binds deployment/CPU preparation/native capture/same-capture analysis and release evidence; all raw attempts retained. Four native reference forwards, zero new-core backward/training/optimizer/admission.
- Report notes preserve preflight sections0-3 and timestamp later changes in4. Finish pending; actual helper output/receipt and absent owned lease/pending state govern completion. Usage is partial local begin-to-receipt window, cachedinput included, not billing.
'''.replace('BUNDLE',BUNDLE.relative_to(ROOT).as_posix()).replace('TOKEN',TOKEN).replace('SNAPSHOT',owner['generated_at']).replace('DEADLINE',owner['deadline_at'])
assert memory.count('## ')==7 and len(memory.splitlines())<120
notes={'actions':[
    '项目cluster_project；快照'+owner['generated_at']+'、steady；此快照和真实截止均未改。用户明确授权server4阻塞时改server3/GPU1，本轮按有界人工迁移处理；不重复preflight，0-3段仍为迁移前事实。',
    'server4的既有阻塞证据保留，未发信号、重置GPU或删除旧锁。仅改资源分配：server3/GPU1一槽，server4/server6停止新分发；原20条科学约束、全部11禁令和其他goal字段保持不变，追加第21条资源授权；未改调度或恢复M201。',
    'server3固定主机/UUID核实后，隔离部署原Git提交f8457d3b和冻结M95权重；配置/层级源码/权重哈希一致。原CPU装载缺失扩展、Ninja缺失两次失败完整保留；用现有CUDA11.3/gcc7在隔离目录编译原始扩展，未改共享环境。随后CPU严格加载847个参数张量通过。',
    'GPU1独占保护下完成4次真实原模型前向：固定TRAIN组0/60/101/124，4场景、16条唯一表达、两次重复共32次表达出现，不记作32个独立样本；优化器0步。峰值已分配1308473344字节、保留1786773504字节，仅说明参考诊断可运行，非完整训练/新核心效率准入。',
    '迁移后核验时点'+postverify['observed_at']+'：GPU1总24268/空闲24267MiB、利用率0、无计算上下文；三把目标锁均重新取得并释放，代码无tracked更改。269628449字节原生特征文件哈希e4a7e63605bb60d9e9a543cd22ac2635a37627ee3db22d870122e1a254342e08。',
    '同次采集CPU对照'+analysis['observed_at']+'：保留最初场景/表达索引错误及脚本，只在v2按scenes_len展开元数据。4项身份/固定bank查询置换对照exact0；16表达中8项填充样本均在同形状均值路径干预后消息变化，另8项无填充样本exact0；首轮有效点行19372。尺度余弦均值0.814686/0.619390/0.828452仅是描述，不能推导任务伤害或新注意力收益。',
    'CPU/GPU消息差8.5831e-6、GPU重复差4.7684e-6如实保留，不修改原1e-6容差或重分类先前FAIL。主线由blocked转validation，仅解除资源等待；全部6个新核心准入布尔值仍false，其他99条记录及历史gate原样保留；新候选/准入/训练/优化器均0。',
    '本报告尚待finish后收据和释放核验。收据用量仅本地begin至receipt的部分窗口，缺失为未知；缓存属于输入、推理属于输出，不重复相加、不当账单。真实产出为1次资源迁移、1套原生特征采集及1套同次采集分析，不是精度结果。'
], 'decisions':[
    '已按用户授权把后续可用位置切为server3/GPU1；原模型原生诊断实际跑通，server4资源阻塞不再作为主线的当前blocker。未启动未准入训练，不自动恢复偏离主线的M201。',
    '后续沿同一候选、同一冻结TRAIN捕获继续预注册ancestor/uniform/support机制对照，再完成独立模型、原生backward及同口径FLOPs/延迟/显存检查。此前FAIL和所有禁令不变，不把masked-mean修补或描述性余弦直接包装成核心创新。',
    '主线科学状态validation，完整训练显存与新结构效果未知；执行是否COMPLETED以finish及锁释放为准。下次精确调度未读取，未知；不修改现有自动化。'
]}
guard()
assert tick.load(work_path)==before
assert tick.digest(ROOT/'pipeline/queue.json')==queue_sha
tick.save(work_path,work)
memory_path.write_text(memory,encoding='utf-8')
tick.save(BUNDLE/'notes.json',notes)
tick.save(BUNDLE/'persistence.json',{'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'changed_candidate_ids':[PRIMARY],'primary_stage':'validation','other99_exactly_unchanged':True,
    'all_original_admission_booleans_unchanged':True,'queue_sha256_unchanged':queue_sha,
    'goal_change':'resource-only21stconstraint; old20andallotherfieldsunchanged',
    'memory_lines':len(memory.splitlines()),'decision':ref(decision_path),
    'migration_summary':ref(BUNDLE/'migration_summary.json'),'new_training':0})
print(json.dumps({'candidate':PRIMARY,'stage':'validation','other99unchanged':True,
    'all_six_new_core_gates_passed':False,'new_training':0,'memory_lines':len(memory.splitlines()),
    'decision':str(decision_path),'summary':str(BUNDLE/'migration_summary.json')},indent=2))
