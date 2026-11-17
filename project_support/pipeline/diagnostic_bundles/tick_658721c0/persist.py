"""Evidence-led notes and six-section report inputs before lease release."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import json
from statistics import mean
from ops import ROOT, OUT, ID, TOKEN, THREAD, NAME, guard, evidence, remote, save, tick, now

owner, _ = guard(90)
native = tick.load(OUT / 'native_contact_result.json')
backward = tick.load(OUT / 'native_backward_result.json')
standalone = tick.load(OUT / 'native_standalone_result_r1.json')
assert native['execution_completed'] and backward['execution_completed'] and standalone['execution_completed']
code = '''
import fcntl,json,subprocess
from datetime import datetime,timezone
cards={}
for i,uuid in ((0,'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),(1,'GPU-7f82edb9-f620-8045-caea-a75232265cd1')):
 row=subprocess.check_output(['nvidia-smi','-i',str(i),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 assert [x.strip() for x in row.split(',')][:2]==[str(i),uuid]
 contexts=subprocess.check_output(['nvidia-smi','-i',str(i),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 locks={}
 for kind in ('training','diagnostic','exclusive'):
  with open('/tmp/cluster_project_gpu'+str(i)+'_'+kind+'.lock','a+b') as handle:
   try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True
   except BlockingIOError:locks[kind]=False
 cards[str(i)]={'gpu':row,'contexts':contexts,'locks_available':locks}
assert not cards['0']['contexts'] and all(cards['0']['locks_available'].values())
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'cards':cards}))
'''
resources = remote(code)
resource_path = save('final_resources.json', resources)
assert resources['returncode'] == 0, 'Must verify native GPU release before closure'
groups = defaultdict(list)
for row in native['readouts']:
    groups[row['scene_id']].append(row)
scene_rows = [{'scene_id': scene, 'expressions': len(rows),
    'contact_minus_baseline_probability_mae': mean(r['contact_minus_baseline_probability_mae'] for r in rows),
    'contact_minus_rotated_probability_mae': mean(r['contact_minus_rotated_probability_mae'] for r in rows)}
    for scene, rows in groups.items()]
analysis = save('analysis.json', {'observed_at': now(), 'candidate_id': ID,
    'new_structural_candidates': 1, 'independent_model_and_config_implemented': True,
    'source_and_native_controls': native['controls'], 'distinct_scenes': 2, 'unique_expressions': 8,
    'scene_readouts': scene_rows, 'scene_balanced_contact_minus_baseline_probability_mae': mean(r['contact_minus_baseline_probability_mae'] for r in scene_rows),
    'scientific_interpretation': 'Direct cross-leaf feature path and native loss gradients verified. Task error changes are mixed, not a trained improvement or population effect. Same target-label contact counts are dominated by background and do not establish same-object continuation.',
    'native_loss_forwards': 4, 'native_criterion_backwards': 3, 'native_cut_path_backwards': 1,
    'independent_model_native_backwards': 1, 'optimizer_steps': 0, 'new_training': 0,
    'resources': {'single_batch_peak_ratio': backward['candidate_to_baseline_peak_allocated_ratio'],
        'peak_increment_bytes': backward['candidate_minus_baseline_peak_allocated_bytes'],
        'formal_efficiency_admission': False, 'caution': 'Single fixed-order batch2 probes; cold/warm timing and unequal pre-forward allocations preclude a speedup claim or formal Pareto decision.'},
    'integration_failure': evidence(OUT / 'native_standalone_result.json'),
    'fresh_process_repair': evidence(OUT / 'native_standalone_result_r1.json'),
    'literature': 'Primary-source lookups attempted; inspectable complete original-paper comparison remains incomplete. No claim that contact graphs or graph attention are novel.',
    'missing_gates': ['Formal total standard FLOPs<=10G and bs1 warmup20/repeat100 uniform latency/memory',
        'Full-source numerical/permutation controls; old strict failures remain',
        'Broader prediction-blind scene-level task evidence, uncertainty and whole-mechanism novelty comparison'],
    'model': 'Cluster/framework/model/Quard_model/' + NAME + '_pce',
    'config': 'Cluster/configs/Quard/ctf_hcg_csort_pce/' + NAME + '_pce.yaml',
    'scientific_admission': False, 'final_resource_evidence': evidence(resource_path)})
goal = tick.load(ROOT / 'pipeline/goal.json')
design = ROOT / 'pipeline/designs/exp_design_20261020_658721c0_pce.md'
design.write_text('# Experiment Design - PCE / cluster_project\n\n## 1. Motivation\n' + goal['description']
    + '\n\n## 2. Current Best Results\nHistorical M95 .5020; baseline .4894; target .5100; gap .0080. M203/FLE and M204/CPA are terminal and not reopened. Frozen M95 epoch16 used for diagnosis is not a new trained candidate.\n'
    + '\n## 3. Analysis And Direction\nFine-leaf FLE excludes cross-leaf donors. PCE tests a distinct geometry-only contact path; source differentiation and native causal masks/gradients are observed, task improvement is not. Prior selected-mask feature contrast/anchor relation/BCCA supervision are not resumed.\n'
    + '\n## 4. Experiment Plan\nLet E be all co-occupied/six-face voxel superpoint contacts and E_cross={(i,j) in E:leaf(i)!=leaf(j)}. For each existing head, a_ij=softmax_j(x_i^T x_j/sqrt(d)); fine_i=sum_j a_ij*x_j when cross-leaf donors exist, otherwise the original fine FFN bank value. Preserve middle/coarse readback, original scale fusion/projection/normalization and outer inst_feats update. Final native mask uses query and the updated inst_feats. No new gate, large QKV projection, residual branch, top-k/radius/seed/schedule sweep.\n'
    + 'Source graph identity, row relabeling and deleted-contact controls; native fixed-query masks with original selected query versus one-position donor-value rotation; original native criterion backwards; independent-package integration. All fixed controls remain 1e-6.\n'
    + '\n## 5. GPU Allocation Plan\nOnly authorized idle/exclusively leased server4GPU0 used. GPU1 foreign jobs preserved; server3GPU1 unreachable/occupation unknown. No new training queue.\n'
    + '\n## 6. Implementation Checklist\nIndependent _pce package and unique config exist; eight Python files parse and no cross-variant import is used. Independent native Network/criterion forward/backward ran without forward-replacement hooks. No optimizer step, commit, push, production sync, admission or training. Uniform total FLOPs, bs1 warmup20/repeat100 efficiency and full-source numerical controls remain pending.\n'
    + '\n## 7. Risk Assessment\nTwo scenes/eight unique expressions only; mixed task errors, no generalization claim. Binary same-label contacts mostly background, not proof of same-instance donors. CPU graph construction/inference cost and autograd E*C storage require uniform tests; sparse observed E is not a worst-case bound. Work O(V+P+E+E_cross*C), storage O(V+P+E+E_cross*C) for this unoptimized autograd implementation. Degenerate/coincident-donor and full-source controls remain risks. Native full-loss gradient and finite parameters establish feasibility, not efficacy. Post-training comparison, if admitted: fixed ScanRefer split, M95/baseline, scene-cluster uncertainty, preregistered boundary/error subsets and original Pareto rule; no test-selected tuning.\n'
    + '\n## 8. Smell And Literature Check\nNew directed information path is demonstrated; zero new learned parameters is not a numerical-only tweak. Existing nhead/scale/schedule remain unchanged. Basic graph attention/contact adjacency must not be called new research by themselves. Complete original-paper whole-mechanism comparison and novelty are unverified; preserve that limitation. Status: IMPLEMENTED PROTOTYPE, NOT ADMITTED.\n', encoding='utf-8')
work = tick.load(ROOT / 'pipeline/research_work.json')
candidate = next(c for c in work['candidates'] if c['id'] == ID)
candidate['evidence'].extend([evidence(analysis), evidence(design), evidence(resource_path)])
candidate['stage'] = 'validation'
candidate['failure_scope'] = 'inconclusive'
candidate['next_action'] = 'First freeze the uniform full-model resource protocol and full-source numerical/permutation control for independent PCE; then broaden outcome-blind TRAIN scene controls. Keep mixed two-scene task evidence and publication novelty unproved. Admit/train only if every original gate passes; never replay old unchanged reductions or reopen old routes.'
remaining = (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds()
if remaining <= 180:
    work['design_cycle'] = {'stop_reason': 'tick_deadline_near', 'attempted_ids': [ID],
        'evidence': [evidence(analysis)], 'resume_condition': candidate['next_action'], 'updated_at': now()}
tick.save(ROOT / 'pipeline/research_work.json', work)
notes = save('report_notes.json', {'actions': [
    '快照2026-10-20 12:11:19上海，design，活动/排队0、准入预算3，pending6/8且非reserve-only。真实所属任务、目标和GPU授权、旧调度Disabled均已核实；仅一次begin。上轮6469按INCOMPLETE释放，不能当科学完成。',
    '先复查六个到期旧候选：四项监督只作辅助保留，两项数值测量没有新的保持门槛的修复，不重复相同归约、不恢复M201/M204。它们不是所有点云结构研究的全局冻结，旧证据/账本条目原样保留。',
    '新增稳定ID hierarchy-cross-leaf-physical-contact-exchange。先动机审查、预注册源图/原生对照，再进行实际测试；细层采用跨FPS叶的物理接触内容交互，中粗层保留M95 context。合成图区别于FLE叶内交互，恒等/重标号误差0，跨叶donor梯度原FLE为0、新路径非零；不当作任务效益。',
    '两固定TRAIN场景8条表达原生捕获：1426/1663条物理边中967/990条跨细叶，596/667及623/710个receiver获得新路径。五项严格原生/删边/重标号控制均0，新的inst_feats确实影响固定query的mask。任务误差有升有降，scene-balanced概率MAE变化=' + str(mean(r['contact_minus_baseline_probability_mae'] for r in scene_rows)) + '，不称提升或总体伤害；两场景不能证明泛化。',
    '原始native criterion匹配前后向已执行；独立model/config也实现并在不替换forward的独立包中执行原生loss前后向，642组观测参数梯度有限、无新增学习参数。实际4次native loss forward、3次完整criterion backward及1次原生截断路径backward，重复同一2场景/8表达，不当多个独立样本。0optimizer更新、0新准入/排队/训练。',
    '两次本地编排错误分别为源码归档字节还原及Windows命令长度，均在原生计算前停止并保留，修正为原始字节归档和SSH标准输入。独立导入首次Criterion重名保留；干净进程仅导入新包修正后通过，没有force覆盖注册表或改变模型算术。',
    '单次同批GPU峰值候选相对baseline约+' + str(round((backward['candidate_to_baseline_peak_allocated_ratio']-1)*100, 3)) + '%，不是正式bs1 warmup20/repeat100、完整optimizer峰值或统一FLOPs准入；冷/热耗时不能声称加速。正式效率、完整源码数值/重标号控制、更多场景证据与完整原始文献对照仍未通过。',
    '所有GPU子进程已结束并复核GPU0上下文为空、三锁可用。GPU1实际占用以本轮final_resources时间为准，未触碰外部任务；server3预检不可达，占用未知。不改调度、目标/门槛、seed1999、50/70计划，不提交/推送/生产部署，不重启旧训练。',
    '用量仅begin2026-10-20T04:11:19Z至收据前本地可见窗口，具体值在本报告保存时未知，以收据为准；不含此前读取、晚到记录与最终回复。cache包含在input、reasoning包含在output，不重复累加，也不当账单。报告保存时finish尚未执行，科学状态为未准入原型。'],
    'decisions': ['保留一个有实际测试与独立代码的新结构候选，pending变7/8；不是监督/路由/FLE/HDS旧路线重开。关键增量是跨细叶物理donor进入inst_feats，基础图注意力与训练收益、新颖性仍不能宣称已证明。',
    '下一步在同稳定ID先完成统一资源与完整源码数值控制，再扩展预测盲场景对照；科学缺口不伪造为外部资源阻塞。真实deadline接近时保留validation工作续做，不放宽准入或靠重复数值重放填轮次。']})
memory = f'''# Codex Research Memory
## Goal And Phase
- Current {TOKEN}, DESIGN, begin2026-10-20T04:11:19Z/deadline05:11:19Z (12:11/13:11Shanghai). Actual owner {THREAD}; Pipeline Disabled. One begin only.
- Prior6469 INCOMPLETE/abort/released10:34:36; priorc121 FINALIZED/PASS/released08:36:43. Never reuse expired tokens/controllers or treat old prefinish wording as current status.
- Goal SHA{GOAL if False else '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'},25constraints/11bans,target.5100. Primary real hierarchical point/inst_feats updates, not supervision. Seed1999/epochs50/max_iters70/default10G/Pareto and all bans unchanged.
- Authorize server4GPU0/1 and server3GPU1 only, one task/card; no automatic M201/M204 recovery, migration, reset, eviction, scheduler changes or new server6 work. Use strict known-host keys; passwords unread.
## Champion And Baseline
- Historical M95 .5020, baseline .4894,target .5100,gap .0080. Frozen diagnostic M95 epoch16=.502460718 is not verified historical champion weights.
- M204CPA-R1 terminal done_earlystop28/50,archived08:10Shanghai,best~.4993(exact .49925217@18 cached04:30); no restart. M203FLE terminal .4885315597, no reopened variants. Prior HDS/FLE/PDC/BCCA evidence/dirty files preserved.
## Active Hypotheses
- NEW {ID},validation,scientific_admissionFALSE. Independent model/config suffix_pce exists; direct physical cross-leaf contacts replace fine readback on eligible receivers; original fallback/middle/coarse/fusion/writeback retained. No new learned params/gates/QKV/residual/seed/topk/radius tuning.
- First synthetic source graph controls0, FLE offleaf donor gradient0 vs PCE nonzero. Native 2scenes/8unique expressions:967/1426 and990/1663crossleafedges,596/667 and623/710receivers. Binary same-target-label edges mostly background, NOT same-object proof.
- Native readback/head/frozen-bank encoder/deleted-edge/operator-row-permutation controls ALL0. Native inst_feats change max .5668866; direct offleaf gradient1.047386. These are frozen-bank causal diagnostics, NOT original full-source numerical admission.
- Scene MAE deltas and uncertainty in analysis.json: mixed, scene-balanced delta {mean(r['contact_minus_baseline_probability_mae'] for r in scene_rows)}; no trained gain or population harm claim.
- 4native loss forwards,3fullcriterion backwards+1cut backward; 1fullbackward independent package without replacement hooks. All observed642parameter grads finite,new learned params0,optimizer steps0,new training0. Same2scenes reused,not new population samples.
- Two old numerical IDs remain blocked implementation-only: hierarchy-native-batch-minimum-resolution and hierarchy-native-superpoint-relabeling-audit. Exact same-pointer native reduction variation1.9073486328125e-6 fails frozen1e-6; no unchanged replay/gate/precision/operator waiver. Core mechanisms not falsified; keep candidate-specific.
- Old562scene census and original mask pairs remain preserved; old fixture hashes09c72c.../a436f3... in c121 artifacts. New true-native contact fixture remote .../pipeline/contact_658721c0/native_contact_fixture.pt SHA93a4c4ef26668ffdf2c37141b1667906456142ee853b8459e110d91879d59a7b.
## Closed Or Failed Directions
- Preserve all rank/meanmoment/ancestry/padding/prefix/QF/HDS/FLE rejections and bans. No renamed routing/gating/residual/largeQKV/N2/tuning/canonicalseed repair/HDSrevision3/FLErestart/M201recovery.
- Four old supervision IDs remain auxiliary priority holds, not scientific rejection; timer/current question/freeGPU does not restore priority. Six due old IDs rechecked without unchanged native reruns.
- Prior8scene expression/scale studies complete, not admitted. Original full-source permutation2.861e-6>1e-6 and CPU/GPU reconstruction failures preserved; frozen-bank PASS is not full-source PASS.
## Running And Queue
- 12:11snapshotactive0/target3,waiting0,budget3,reserve2/2,nonreserve-only,pending6/8. Current new PCE pending7/8,0new queue/training/admission. New model/config not committed/pushed/deployed to production.
- 12:24server4GPU0 idle41MiB/0%,GPU1busyforeign; live end resources in final_resources.json confirm GPU0 no contexts/all3locks available after children exit. Server3preflight unreachable,GPU1occupationUNKNOWN. No foreign process touched.
- Single fixed-order batch2 allocated peak ratio {backward['candidate_to_baseline_peak_allocated_ratio']},increment {backward['candidate_minus_baseline_peak_allocated_bytes']}bytes. Not calibrated total-resource/Pareto PASS or speedup; baseline cold/candidate warm and allocations differ.
## Open Questions And Risks
- Next: uniform full-model standard FLOPs/bs1 warmup20repeat100 latency/memory; full-source numerical/permutation controls; broader outcome-blind scene task evidence and complete original-paper whole-mechanism comparison. Novelty/gain not established; no training from prototype controls.
- Initial archive byte-normalization and Win206 staging failures occurred before native execution; preserved and repaired. Standalone harness initially loaded parent then candidate and collided Criterion registration; fresh-process single-package repair passed without forcing registry or changing candidate model arithmetic.
- Prior pipeline diagnosis proved reserve_budget0 does not forbid nonreserve-only independent designs; local numerical blocks must not freeze whole mainline. No shared pipeline code or scheduler patch in this tick.
## Last Tick
- Bundle pipeline/diagnostic_bundles/tick_658721c0: protocol, source/native/cut/backward/standalone-r1 evidence, independent source/config hashes, analysis, final resource observations and notes. One real new structural candidate/implemented prototype,not a trained result.
- At this save finish NOT yet executed; render full six-section report, finish only on actual valid near-deadline disposition, verify FINALIZED/PASS and lease+pending absence. If checker cannot accept honest state, preserve and abort. No writes after release.
- Usage partial begin04:11:19Z->receipt local window,unknown until receipt; cache already ininput/reasoning already inoutput,notbilling. Old controllers including this tick expire after release.
'''
(ROOT / 'pipeline/codex_memory.md').write_text(memory, encoding='utf-8')
assert len(memory.splitlines()) < 120
print(json.dumps({'analysis': evidence(analysis), 'design': evidence(design), 'notes': str(notes),
    'remaining_seconds': remaining, 'resources': resources['data'], 'scene_rows': scene_rows}, ensure_ascii=False))
