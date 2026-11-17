"""Reconcile actual outcomes, retain immutable evidence, render audit inputs."""
from datetime import datetime, timezone
import ast
import json
import shutil
from ops import guard, save, run, ssh, add, evidence, ROOT, OUT, TOKEN, CID
import foreground_tick as tick

owner = guard()
now = datetime.now(timezone.utc)
names = ['native_qf/native_diagnostic_result.json', 'capture_repeat/native_diagnostic_result.json',
         'padding_native/native_padding_result.json', 'batch2_native/native_batch2_result.json',
         'shape_native/native_batch2_result.json', 'm95_native/native_batch2_result.json']
results = [tick.load(OUT/n) for n in names]
assert not results[0]['passed'] and all(r['passed'] for r in results[1:])
assert all(max(r['controls'].values()) <= 1e-6 for r in results[3:])
qf = tick.load(OUT/'qf_analysis.json')
gradient = tick.load(OUT/'padding_gradient_result.json')
assert gradient['passed'] and not gradient['cuda_initialized']
resources = ssh('import json,subprocess,fcntl\nfrom datetime import datetime,timezone\n'
    'gpu=subprocess.check_output(["nvidia-smi","-i","0","--query-gpu=index,uuid,memory.used,utilization.gpu","--format=csv,noheader,nounits"],universal_newlines=True).strip()\n'
    'assert gpu.split(",")[1].strip()=="GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"\n'
    'contexts=subprocess.check_output(["nvidia-smi","-i","0","--query-compute-apps=pid,used_memory","--format=csv,noheader,nounits"],universal_newlines=True).strip()\n'
    'locks={}\nfor kind in ("training","diagnostic","exclusive"):\n'
    ' with open("/tmp/cluster_project_gpu0_"+kind+".lock","rb") as h:\n'
    '  try:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]="released_at_probe"\n'
    '  except BlockingIOError:locks[kind]="busy_preserved"\n'
    'print(json.dumps({"observed_at":datetime.now(timezone.utc).isoformat(),"gpu":gpu,"contexts":contexts,"locks":locks}))')
save('final_gpu0_resources.json', resources)
assert not resources['contexts'] and all(v == 'released_at_probe' for v in resources['locks'].values())
source_rows = []
for stage in ('native_qf', 'm95_native'):
    m = tick.load(OUT/stage/'native_manifest.json')
    for filename, digest in m['assets']['source_hashes'].items():
        assert tick.digest(ROOT/'Cluster/framework/model/Quard_model'/m['name']/filename) == digest
    method = next(f for c in ast.parse((ROOT/'Cluster/framework/model/Quard_model'/m['name']/'hier_postprocess.py').read_text(encoding='utf-8')).body
        if isinstance(c, ast.ClassDef) and c.name == 'C2F_ClusterAttn_CTF_HCG'
        for f in c.body if isinstance(f, ast.FunctionDef) and f.name == '_cluster_to_points')
    means = [ast.unparse(s) for s in method.body if isinstance(s, ast.Assign) and
             any(isinstance(t, ast.Name) and t.id == 'global_mean' for t in s.targets)]
    source_rows.append({'model': m['name'], 'source_sha256': m['assets']['source_hashes']['hier_postprocess.py'],
                        'global_mean_assignments': means})
assert source_rows[0]['global_mean_assignments'] == source_rows[1]['global_mean_assignments']
save('source_postcheck.json', {'production_sources_unchanged': True, 'same_legacy_unmasked_mean': True, 'models': source_rows,
    'norm_helper_unchanged': tick.digest(OUT/'native_qf/neighbor_content.py') == tick.digest(OUT/'capture_repeat/neighbor_content.py')})
progress = {'observed_at': now.isoformat(), 'snapshot_at': '2026-10-18T08:09:01.130869+00:00',
    'native_forwards': sum(r['native_forwards'] for r in results), 'suffix_replays': sum(r['suffix_replays'] for r in results),
    'native_backwards': sum(r['native_backwards'] for r in results), 'optimizer_steps': sum(r['optimizer_steps'] for r in results),
    'synthetic_cpu_backwards': gradient['synthetic_cpu_backward_calls'], 'new_training': 0, 'new_VAL': 0, 'new_admissions': 0,
    'new_diagnostic_ids': 1, 'initial_norm_failure_preserved': True, 'arithmetic_revision3': False,
    'QF_piou_point_only': qf['replication']['paired_scene_contrasts']['piou']['L00_minus_L01'],
    'QF_piou_query_only': qf['replication']['paired_scene_contrasts']['piou']['L00_minus_L10'],
    'FLE_same_shape': results[4]['same_shape_cases'], 'M95_same_shape': results[5]['same_shape_cases'],
    'scientific_status': 'No new trained gain;pointpath readout dominant in one valid replicate;sharedpadding dependence confirmed,efficacy unknown',
    'execution_status': 'report_evidence_prepared;finish_not_yet_validated',
    'evidence': [evidence(OUT/n) for n in names]}
save('progress_summary.json', progress)
work = tick.load(ROOT/'pipeline/research_work.json')
q = next(c for c in work['candidates'] if c['id'] == CID)
q.update(stage='complete', failure_scope='inconclusive',
    gate_result='FiniteQFdiagnosiscomplete:initialnormFAILED9forwards/8scenes;onevalid32replication pointonlyPiou+.0075331CIcross0,queryonly+.0002626. No efficacy;instability retained.',
    next_action='Do not restart/tune FLE or repeat-until-success/repairnorm3. Use finitepointpath observation plus retained uncertainty;futuremechanism needs independent evidence and fulladmission.')
add(q, [OUT/'qf_analysis.json', OUT/'progress_summary.json'])
c = next(c for c in work['candidates'] if c['id'] == 'hierarchical-padding-context-invariance-audit')
c.update(stage='validation', failure_scope='inconclusive',
    gate_result='NativeFLEandavailableM95 same-shape paddingdependence confirmed;allidentity/zeroscale/nonpaddednulls0. CPUsourcegradients confirmpath;not nativebackward/VALgain or novelstructure.',
    next_action='Preregister a uniform padding-contract/bugfix comparison for BOTH M95 and FLE;separate bugrepair from Phase1 structure. Next nativebackward/control+sameprotocolresources need freshlease/liveGPU3locks;no unilateral meanfix,training,or newVAL.')
add(c, [OUT/'padding_native/native_padding_result.json', OUT/'batch2_native/native_batch2_result.json',
        OUT/'shape_native/native_batch2_result.json', OUT/'m95_native/native_batch2_result.json',
        OUT/'padding_gradient_prereg.md', OUT/'padding_gradient_result.json', OUT/'source_postcheck.json', OUT/'progress_summary.json'])
remaining = (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
if remaining <= 180:
    work['design_cycle'] = {'stop_reason': 'tick_deadline_near', 'attempted_ids': [CID, c['id']],
        'evidence': [evidence(OUT/'progress_summary.json')],
        'resume_condition': c['next_action'], 'observed_remaining_seconds': remaining}
guard()
tick.save(ROOT/'pipeline/research_work.json', work)
shutil.copyfile(ROOT/'pipeline/codex_memory.md', OUT/'previous_memory.md')
goal = tick.load(ROOT/'pipeline/goal.json')
review = '# Motivation Review - cluster_project\n\n'
review += 'Consolidated after tests;pre-execution protocol timing is recorded in the individual immutable preregistrations,not claimed by this document.\n\n'
review += '## 1. Goal\n```json\n'+json.dumps(goal, ensure_ascii=False, indent=2)+'\n```\nTarget.5100;historicalM95.5020;gap.0080.\n\n'
review += '## 2. Story Status\n|Hypothesis|Status|Evidence|Gap|\n|---|---|---|---|\n|Point features affect native masks|Observed in valid32TRAINreplication|qf_analysis.json|Benefit CI crosses0;initial strictnormfailure|\n|Masked padding should not change valid hierarchy output|Disconfirmed in exact FLE/M95interfaces|shape_native,m95_native|Uniform repair efficacy unknown|\n\n'
review += '## 3. Experiment Assessment\n|Experiment|mIoU|Relation|Contribution|\n|---|---|---|---|\n|M203-FLE cached|.4885315597|Negative trained realization|Not restarted|\n|Current diagnostics|Unknown newVAL|Same checkpoint TRAINmechanisms|Point/Q separation and sharederror diagnosis|\n\n'
review += '## 4. Gap Analysis\nFull training memory,repeat training noise,generalization,uniformrepairbenefit and materialnovelty remain UNKNOWN. Masked padding enters level_gate through an unmasked globalmean. M95 shares this implementation;the available M95epoch16 is not verified historicalchampionweights.\n\n'
review += '## 5. Design Rationale\nTwo independent diagnoses,not queuevariants. QF factorization preserves actual out_norm;identity/null/source tests retain1e-6. Padding controls preserve shape and validfeatures;sourceCPUgradient fixtures are not native admission. No newliterature search or novelty claim. No single-op maskedmean is presented as an innovation or Phase1admission.\n\n'
review += '## 6. Next Batch\nNo training candidate admitted. Continue stablepaddingID with uniformcontrol protocol before any productionfix;fullchecks and resourceauthority remain unchanged. See exp_design_20261018_6a3484ad.md.\n'
review_path = ROOT/'pipeline/reviews/motivation_review_20261018_6a3484ad.md'
assert not review_path.exists()
review_path.write_text(review, encoding='utf-8')
design = '# Experiment Design - cluster_project\n\nDiagnostic consolidation only;not an architecture/admission request.\n\n'
design += '## 1. Motivation\n'+goal['description']+'\nPreserve actual hierarchical inst_feats->query/mask path.\n\n'
design += '## 2. Current Best Results\n|ID|State|Best mIoU|Epochs|\n|---|---|---|---|\n|HistoricalM95|Cached|.5020|Unknown|\n|M203-FLE|Cached earlystop|.4885315597|23/50|\n\n'
design += '## 3. Analysis & Direction\nQF point-only Piou effect+.0075331 with CI crossing0;query-only+.0002626. Initial normcontrollerfailure retained. Both native models have masked-context dependence. This is a reliability defect,not a novel attention mechanism or proven source of the training gap.\n\n'
design += '## 4. Experiment Plan\n|ID|Protocol|Purpose|Expected criterion|Status|\n|---|---|---|---|---|\n|'+CID+'|qf_native_prereg.md,repeat_capture_prereg.md|Separate point/Q readouts|Native1e-6reconstruction|Finitecomplete/inconclusive|\n|'+c['id']+'|padding/nativebatch2/same_shape/m95 preregs|Test masked invariance|Identity/null<=1e-6|Dependenceconfirmed;repairnotrun|\n\n'
design += '## 5. GPU Allocation Plan\n|Server|PhysicalGPU|Assignment|\n|---|---|---|\n|server4|0|Boundeddiagnosticscompleted,freshlocksrequiredagain|\n|server3|1|Authorized but not used by these diagnostics|\nOther GPUs/projects/schedules untouched.\n\n'
design += '## 6. Implementation Checklist\n- [x] Frozen assets,actual source head and controls.\n- [x] Native experiments and retained initialfailure.\n- [x] Both existing counterpoints,CPUsourcegradient fixture.\n- [ ] Uniform repair protocol/nativebackward/resources.\n- [ ] Core structural mechanism derivation/literature/independentadmission.\nNo model/config/codepush/queue/train/VAL change.\n\n'
design += '## 7. Risk Assessment\nStrictnormcontrollerinstability,smallTRAINscope,multi-comparison exploratory associations,cropGEMMroundoff (removed by same-shape controls),different trainedweights,unknown efficacy/novelty. All original failures/revisions/bans retained. Followups require freshdeadline and safety checks.\n'
design_path = ROOT/'pipeline/designs/exp_design_20261018_6a3484ad.md'
assert not design_path.exists()
design_path.write_text(design, encoding='utf-8')
decision = run(['C:/Program Files (x86)/Git/bin/bash.exe',
    'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh', 'cluster_project', 'other',
    '点云与query贡献及层级融合是否受padding污染？',
    '保留首轮范数失败及32场景有效复现；确认FLE/M95共享padding依赖，禁止把单点均值修复冒充结构创新或自动重训。',
    '真实原生batch2、同形状masked值对照、非padding行及零消息对照均已测；收益和修复效果仍未知。',
    'pipeline/diagnostic_bundles/tick_6a3484ad/progress_summary.json'])
save('decision_log_execution.json', {'returncode': decision.returncode, 'stdout': decision.stdout, 'stderr': decision.stderr})
assert decision.returncode == 0
notes = {'actions': [
    '快照2026-10-18 16:09:01上海/design；0训练0排队。后续观测时间与快照分开留档；未重跑预检。',
    '同源QF首轮9次原生前向/8完整场景因原严格范数检查失败；一次冻结复现32场景128表达式通过，首轮失败不覆盖，不做数值修订3。',
    '有效复现实际out_norm与mask_feats重建误差0。点单侧Piou差+.0075331，CI[-.0001237,.0218365]跨0；query单侧+.0002626，不构成训练提升。',
    '新稳定padding诊断：2场景人工masked扩展、真实batch2、同BNC仅masked值改变、现成M95同口径对照；证明共享未屏蔽global_mean影响有效点和最终mask，未修模型。',
    'FLE/M95同形状零masked值时mask logits最大变化4.69856/1.11267；有效点逐位不变，非padding行/零消息/原生重建对照误差均0。原始裁剪GEMM舍入混杂已单列并以同形状测试排除。',
    'CPU精确源AST梯度夹具4次反传，仅合成CPU不是原生backward准入；原生backward/optimizer/新训练/新VAL/入队均0。实际原生前向'+str(progress['native_forwards'])+'，后缀回放'+str(progress['suffix_replays'])+'；历史缓存不重复计数。',
    '用量收据窗口为本轮begin到生成收据，仅涵盖可见本地日志，当前收据未生成数值未知；缓存属输入子集、推理属输出子集，不重复相加、不当账单。',
    'GPU0最终实时无计算上下文，training/diagnostic/exclusive三锁均已释放；生产源哈希、目标、资源白名单、调度和外部进程未改。科学状态：无新训练提升；本轮执行状态：等待finish校验，不预称完成。'],
    'decisions': ['先把共享padding污染与结构贡献分开，再预注册M95/FLE统一处理对照；单个masked均值修复不是Phase1核心创新，不能单边削弱基线。',
        'QF有限诊断完成但科学收益不确定；同一padding稳定ID继续validation。保留4个未到期scope holds，不伪造阻塞、耗时或第二条失败路线，不硬凑训练变体。',
        'finish成功并核实FINALIZED/context_committed及租约释放后才称本轮完成；否则保留全部证据并abort，报告真实未完成原因。']}
save('report_notes.json', notes)
print(json.dumps({'progress': {k:v for k,v in progress.items() if k not in ('evidence','FLE_same_shape','M95_same_shape')},
                  'resources': resources, 'remaining_seconds': remaining, 'decision': decision.stdout}))
