"""Persist the successful manual launch separately from scientific validation."""
from ops import *
import pipeline_monitor as monitor
from datetime import timedelta

guard()
auth_path=ROOT/'pipeline/authorizations/cpa_exploratory_20261019_72695a5d.json'
verification=tick.load(OUT/'progress_verification.json')
assert verification['launch_verified'] and not verification['traceback']
experiment=monitor.load_experiment(str(ROOT),'M204-CPA')
assert experiment['launch_verified'] and experiment['scientific_admission'] is False
program=r'''from pathlib import Path
import json,subprocess,re
from datetime import datetime,timezone
pid=PID
log=Path(LOG)
with log.open('rb') as f:
 f.seek(0,2)
 length=f.tell()
 f.seek(max(0,length-40000))
 text=f.read().decode('utf-8','replace')
steps=[(int(a),int(b)) for a,b in re.findall(r'Train\[(\d+)/\d+\]:[^\r\n]*?\|\s*(\d+)/\d+',text)]
rows=[x for x in text.splitlines() if 'Epoch [' in x]
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert [x.strip() for x in gpu.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'pid_alive':Path('/proc/'+str(pid)).exists(),'last_native_steps':steps[-8:],'last_training_log':rows[-1] if rows else None,'traceback':'Traceback (most recent call last)' in text,'unstable_loss_skip':'Skipping backward due to unstable loss' in text,'gpu':gpu,'contexts':contexts,'validation_metric_observed_in_window':'mIoU :' in text,'native_log_bytes':length}))
'''.replace('PID',str(experiment['pid'])).replace('LOG',repr(experiment['log']))
live=ssh(program)
assert live['pid_alive'] and not live['traceback'] and live['last_native_steps']
save('final_training_state.json',live)
evaluation={
 'recorded_at':datetime.now(timezone.utc).isoformat(),'experiment_id':'M204-CPA','kind':'prospective_post_training_evaluation',
 'timing':'Declared after startup and before observed validation results;does not change model/config or select a variant.',
 'primary':'Native ScanRefer VAL mIoU;target0.5100,reported historical M95 comparator0.5020 and no-cluster baseline0.4894.',
 'reference_caveat':'Available M95epoch16=.5024607181549072 is not verified historical champion weights;use its exact provenance for matched reevaluation,do not silently substitute it.',
 'sampling_unit':'Scene;expressions and points in the same scene are correlated.',
 'predefined_subgroups':['same-class distractor cases','relation-bearing descriptions'],
 'material_harm_rule':'For each predefined subgroup,flag potential systematic harm if a paired scene-clustered95% interval is wholly below zero;without enough independent scenes or with an interval crossing zero,label inconclusive. Do not treat a single adverse scene or untrained gradient as trained harm.',
 'noise_floor':'UNKNOWN;not estimated from independent repeats. No made-up constant or extra seed sweep.',
 'pareto':'Retain the original10G standard-counted budget and relative time/memory review;peak memory increase>15% requires>=0.003 mIoU gain. Full optimizer peak relative to original baseline remains unknown until comparably measured.',
 'validation_boundary':'No TEST-based mechanism selection,no extra datasets or labels,no numeric tuning;seed1999/batch2/workers4/epochs50/max_iters70 unchanged.',
 'scientific_status':'Efficacy and novelty unresolved;one manual exploration is not a mechanism PASS.'}
save('evaluation_plan.json',evaluation)
work=tick.load(ROOT/'pipeline/research_work.json')
holds=[c for c in work['candidates'] if c['stage']=='blocked']
assert len(holds)==4 and all(c.get('blocker_kind')=='human_authorization' for c in holds)
scope={
 'observed_at':datetime.now(timezone.utc).isoformat(),'latest_authorization':evidence(auth_path),
 'authorized_experiment_only':'M204-CPA','unchanged_scope_hold_ids':[c['id'] for c in holds],
 'actual_recheck':'The new human reply authorizes CPA-R1 only. It does not restore priority to the four auxiliary supervision candidates or recover M201.',
 'gpu_block_claim':False,'new_scientific_tests_of_auxiliaries':0,
 'resume_condition':'Explicit restoration of auxiliary scope or a separately justified auxiliary test required by the point-feature mainline;due timers or idle GPUs are not authorization.'}
save('remaining_scope_holds.json',scope)
retry=(datetime.now(timezone.utc)+timedelta(hours=4)).isoformat()
scope_evidence=evidence(OUT/'remaining_scope_holds.json')
for candidate in holds:
    candidate['retry_after']=retry
    candidate['evidence'].append(scope_evidence)
work['design_cycle']={
 'recorded_at':datetime.now(timezone.utc).isoformat(),'stop_reason':'external_resource_blocked',
 'blocker_kind':'human_authorization','actual_reason':'All remaining pending IDs are existing auxiliary-scope human authorization holds,NOT GPU resource blocks. The sole newly authorized mainline experiment is now training.',
 'attempted_ids':[CID,*scope['unchanged_scope_hold_ids']],
 'evidence':[evidence(auth_path),evidence(OUT/'progress_verification.json'),scope_evidence],
 'resume_condition':scope['resume_condition']+' Continue monitoring the already-running CPA experiment independently.',
 'retry_after':retry}
guard();tick.save(ROOT/'pipeline/research_work.json',work)
advance([OUT/'final_training_state.json',OUT/'evaluation_plan.json',OUT/'remaining_scope_holds.json',OUT/'prepare_authorization.py',OUT/'launch_exploration.py'],
 next_action='Monitor M204-CPA native training/ScanReferVAL and the recorded evaluation plan;scientific gates stay unresolved;no duplicate launch or automatic restart')
decision=monitor.log_decision(str(ROOT),'manual','CPA-R1单次探索性训练是否已经真实运行？',
 'M204-CPA已在server4物理GPU0启动，原生迭代增长已验证并登记；本轮仅释放编排租约，远端训练继续持有GPU锁。',
 '用户明确授权、限定九文件提交c31f459、安全快进、原始backbone/标注/源码哈希与独占锁均已核验；科学diagnosis/semantic controls及revision1状态未改写。',
 'pipeline/diagnostic_bundles/tick_72695a5d/progress_verification.json;pipeline/diagnostic_bundles/tick_72695a5d/final_training_state.json')
advance([Path(decision)])
notes={
 'actions':[
 '本轮快照北京时间2026-10-19 09:17:16，design，原始表格的运行0/队列0仅指该preflight时点；以下记录随后发生的授权和启动。',
 '用户在所属会话明确回复授权：仅CPA-R1一次固定配置探索性训练。授权绑定八个已测模型文件及一个配置、server4物理GPU0、seed1999/batch2/workers4/epochs50/max_iters70；不是科学PASS或通用门槛放宽。',
 '限定提交c31f45994f8d68b78dfe8bb4fef3f9aaefabe86e，九个Git blob与已测字节哈希逐项一致；远端采用安全快进，不reset/clean/stash，不带入PDC/BCCA脏文件。只适配候选自身部署路径。',
 'M204-CPA于北京时间09:29:58单次启动，09:30:53已验证原生Train[1/50]从0增长至107，进程存活、目标UUID正确、无Traceback或不稳定损失跳步；最新状态见final_training_state.json。没有重跑上轮诊断和资源测试。',
 '训练使用原始backbone而非M95头部，原生AdamW/PolyLR和训练循环不变；外层运行时在任何CUDA初始化前核对主机/GPU空闲，并全程持有training/diagnostic/exclusive三锁，禁止共享、驱逐、reset及重复启动。',
 '训练已登记queue/running/experiments并标注人工探索授权、launch_verified=true、scientific_admission=false。旧diagnosis/semantic controls未通过及revision1 inconclusive全部保留。当前没有新验证集mIoU结果，提升未知。',
 '其余四个候选到期只核对授权作用域：此次授权未恢复旧监督主线，维持原有人工作用域冻结并按四小时窗口复查；不是显卡阻塞，不为填槽复活旧路线或生成替代变体。收尾枚举external_resource_blocked在本轮具体指人工授权冻结，明细已留档。',
 '收据用量为begin至收据写入的本地可见窗口，排除前置读取和最终回复；当前统计未知，以收据为准，不把缓存重复相加或用量当账单。实际产出为一份限定授权、一项九文件提交、一次安全同步和一次已核实训练启动，不是新增科学结论。',
 '报告生成时尚未声称本轮收尾完成。finish及租约释放另行核验；远端训练获准跨tick继续，不在编排收尾时终止。'],
 'decisions':[
 '仅执行已获授权的M204-CPA；所有其他候选的准入、禁止路线、资源卡号、调度和全局目标不变，不改共享checker。',
 '按原生ScanReferVAL观察首次验证和后续收敛，再按既有baseline/champion、场景相关性和相对资源条件评价；在足够证据前不声称新颖性或收益。',
 '正常收尾只表示操作记录完整，不表示科学验证通过；若真实校验失败，保存证据并abort，不停止已授权远端训练。']}
save('report_notes.json',notes)
print(json.dumps({'state':live,'decision':decision,'scope_holds':len(holds),'notes':str(OUT/'report_notes.json')},ensure_ascii=False,indent=2))
