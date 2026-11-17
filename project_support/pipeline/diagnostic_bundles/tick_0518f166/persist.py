"""Persist actual finite diagnostic results and unchanged native resource holds."""
from datetime import datetime,timedelta,timezone
import json
from ops import guard,save,evidence,ROOT,OUT,CID,GOAL
import foreground_tick as tick

guard();now=datetime.now(timezone.utc)
result=tick.load(OUT/'continuity_result.json')
four=tick.load(OUT/'server4_live.json');three=tick.load(OUT/'server3_live.json')
resource_time=max(datetime.fromisoformat(four['observed_at']),datetime.fromisoformat(three['observed_at']))
source=tick.load(OUT/'source_verification.json')
assert result['execution_passed'] and result['cuda_initialized'] is False
assert source['unchanged'] and len(source['source_hashes'])==9
assert tick.digest(OUT/'scope_goal.json')==GOAL
assert four['occupied'] and three['occupied'] and four['pid_alive']
assert all(pids==[1995443] for pids in four['lock_owner_pids'].values())
assert result['cpu_exchange_calls']==56 and len(result['gradients'])==4
assert result['perturbation_conditions']==20 and result['nonvanishing_jump_component']==.025
assert len(result['cases'])==26
save('infrastructure_notes.json',{'observed_at':now.isoformat(),'scientific_test_failures':0,
    'events':[
        {'operation':'functions.apply_patch initialnewdirectory','result':'read-onlysandboxfailedbeforefilecreation','scientific_execution':False},
        {'operation':'escalatedapply_patch.bat','result':'Windowscommandlinetoolong;nofilescreated','scientific_execution':False},
        {'operation':'registerfirstapproval','result':'approvalreviewtimeout;notexecuted;onepermittedretryexecutedonce','scientific_execution':False},
        {'operation':'readonlyguessedoperator_cpu.py','result':'pathnotfound;actualadmittedfine_exchange.pyresolvedbyboundedrg','scientific_execution':False}],
    'resolution':'Approveddirectstandardapply_patchentrypointandoneapprovalretry;noalternativeprojectorcredentialsused'})
paths=[OUT/name for name in ('continuity_prereg.md','continuity_cpu.py','ops.py','execute.py','manifest.json',
    'source_verification.json','continuity_result.json','execution.json','server4_live.json','server3_live.json',
    'scope_goal.json','infrastructure_notes.json')]
paths += [ROOT/'pipeline/reviews/motivation_review_20261018_0518f166.md',
    ROOT/'pipeline/designs/exp_design_20261018_0518f166.md',
    ROOT/'pipeline/decisions/20261018-083102_other.md']
entries=[evidence(path) for path in paths]
summary={'observed_at':now.isoformat(),'finite_audit_status':'EXECUTED_COMPLETE_NOT_MODEL_PASS',
    'new_diagnostic_ids':1,'artificial_fixture_count':1,'geometry_conditions':13,'precision_conditions':26,
    'nonzero_perturbation_precision_conditions':20,'cpu_operator_calls':56,'cpu_feature_autograd_controls':4,
    'exact_cutoff_tie_far_donor_component_output':.025,'nonzero_exact_perturbation_output':0.,
    'far_donor_remains_outside_top32':True,'finite_jump_does_not_shrink_over_preregistered_epsilons':True,
    'coordinate_rounding_or_cutoff_content_ambiguity_required':False,
    'native_network_forwards':0,'native_backwards':0,'native_FPS_calls':0,'optimizer_steps':0,
    'checkpoint_loads':0,'new_train_preprocessing':0,'new_training_models':0,'model_revisions':0,'admissions':0,'launches':0,
    'human_holds_rechecked':0,'human_holds_unblocked':0,'native_resource_holds_reconciled':2,
    'M203_best_early_miou':max(four['validation_miou']),'M203_native_validation_count':len(four['validation_miou']),
    'M203_epoch_steps':four['epoch_steps'],'production_sources_unchanged':True,
    'scientific_limitations':'Oneartificialleaf/exactlyrepresentableconstructedfeatures;notnativeFPSincidence,trainedmaskharm,terminalefficacy,generalization,repairornovelty',
    'evidence':entries}
save('progress_summary.json',summary);entries.append(evidence(OUT/'progress_summary.json'))
work=tick.load(ROOT/'pipeline/research_work.json')
candidate=next(c for c in work['candidates'] if c['id']==CID)
assert candidate['stage']=='diagnosis'
candidate.update(stage='complete',failure_scope='implementation',updated_at=now.isoformat(),evidence=entries,
    next_action='Finiteconditionalcontinuityquestionanswered;donotrerununchangedfixtureorclaimmodelPASS. Preservefar-donorsupportjumpseparatefromrounding/cutoffcontentambiguity. Continueexistingnativegeometryandself/nonselfmaskdiagnosticsunderoriginalstableIDsaftergenuineauthorizedidleGPUrelease;noepsilonrepair/sourcechange/newmodel.',
    scientific_result='At an exact K32 tie whole-leaf mean admits a far donor absent from top32. All20 nonzero exact perturbation/precision conditions remove that contribution with fixed component jump.025;constant/tie-preserving/translation controls and4CPUfeaturegradients agree. Native incidence and trained harm unknown.',
    gates={'finite_operator_execution':'COMPLETE','exact_input_support':'FRACTION_AND_SOURCE_AGREE',
        'conditional_continuity':'COUNTEREXAMPLE_ARTIFICIAL_LEAF','native_incidence':'NOT_MEASURED',
        'trained_mask_harm':'UNKNOWN','model_efficacy':'UNKNOWN','production_repair':'NOT_IMPLEMENTED'})
resource_ids=['fle-self-neighbor-content-separation','fle-fixed-membership-metric-geometry-audit']
for cid in resource_ids:
    pending=next(c for c in work['candidates'] if c['id']==cid)
    assert pending['stage']=='blocked' and pending['blocker_kind']=='exclusive_gpu_slot'
    pending['evidence'] += [evidence(OUT/'server4_live.json'),evidence(OUT/'server3_live.json')]
    pending['blocker']='Non-GPU preparations remain complete and frozen,not rerun. Live08:28:48Shanghai:server4physicalGPU0 originalM203PID1995443 ownsall3locks,20685MiB/util17;server3physicalGPU1 foreignPID1453,19370MiB/util100. Bothauthorizedslotsoccupied. NoCUDA/nativeGPUtest,sharing,eviction,resetorlockdeletion. Actualcompute stillrequiresfreshidentity/idleness,assetsandexecutionlease.'
    pending['last_rechecked_at']=resource_time.isoformat();pending['retry_after']=(resource_time+timedelta(hours=1)).isoformat()
work['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':[CID,*resource_ids],
    'evidence':[evidence(OUT/'progress_summary.json'),evidence(OUT/'server4_live.json'),evidence(OUT/'server3_live.json')],
    'resume_condition':'Finiteexact-inputbranchcontinuitydiagnosticcompleted. Resumeexistingfrozennativegeometry/masktestswhenanauthorizedpinnedphysicalcardisactuallyidle,alllifetimeGPUlocksandfreshowningexecutionleaseareavailableandtargetassetsverify. Fourauxiliaryhumanholdsretaintheiroriginalconditionsandnot-dueretries;notrainingrestartorautomaticrepair.',
    'retry_after':(resource_time+timedelta(hours=1)).isoformat(),
    'scope':'RealexclusiveGPUresourceblock,notrouteexhaustion,newmechanism,epsilonrepairortrainedharmproof'}
guard();tick.save(ROOT/'pipeline/research_work.json',work)
save('report_notes.json',{'actions':[
    '本轮不可变快照为上海时间2026-10-18 08:11:35/design，原截止09:11:35不改；已核实实际会话身份、前台归属、旧后台禁用及原目标24约束/11禁止。第0-3段保留preflight时点，后续证据在此注明。bootstrap要求先登记一个诊断，已先登记fle-cutoff-tie-far-donor-continuity-audit后执行，不是训练变体。收尾待finish。',
    '08:28:48只读确认M203-FLE在server4物理GPU0第17/50轮，原生步3370至3380/4686增长，已有16次原生VAL，早期最佳0.48853155970573425。仍低于baseline0.4894、历史M95 0.5020及目标0.5100；历史目标差距0.0080不变。未加跑VAL、选择新checkpoint或改变原训练。',
    '实际执行一个新有限连续性诊断：40点dyadic人工叶，recipient及两个并列cutoff供体特征均0，严格远于top32的供体特征1。原源码在精确并列时取整叶均值，每分量0.025；两符号五个预注册精确微扰均取消并列、排除远点，输出0。20个微扰/精度条件的跳变不随微扰缩小而下降；不是只靠坐标舍入或并列候选内容不同才能发生。',
    '共13种几何、float64/float32两口径26条件，56次CPU算子调用含4项CPU特征梯度检查。Fraction精确支持、独立NumPy、常值特征、保持并列的远点移动和公共平移对照一致；远点特征梯度在并列时每分量1/40，取消并列后为0。数据是构造特征与人工固定叶，不是原生FPS成员、训练mask伤害、泛化收益或新颖性证据。',
    '已核实9个生产源文件及部署配置哈希未变；单线程server4 CPU执行，CUDA隐藏且未初始化。没有重跑旧旋转/精确距离数组，没有TRAIN预处理、checkpoint加载、FPS、原生网络前后向、optimizer步、模型修订、epsilon修复、准入或新启动。',
    '08:28:48两张授权卡均占用：server4原M203持有training/diagnostic/exclusive三锁，server3 GPU1为外部任务。复用一次真实资源表续记两个既有原生诊断的等待，保留原冻结清单、checkpoint、cohort及容差；不共享、驱逐、reset或删锁。四个辅助授权hold本轮未到期，没有重复复查或因空槽重开。',
    '初次沙箱apply_patch失败、批处理命令行过长、一次自动审批超时和只读猜测文件缺失均在科学执行前，已按实际编排情况保留；标准直接apply_patch入口及允许的一次审批重试解决。不是模型或科学测试失败，没有隐藏改门槛。',
    '本轮产出为一个有限条件算子诊断及哈希证据、13几何/26精度条件、4项CPU特征梯度检查、两项资源等待核实和文档。收据用量窗口仅本轮begin至收据，排除更早读取、晚到记录和最终答复；生成前总量未知。缓存是输入子集、推理是输出子集，不重复相加、不作为账单或科学收益。'],
    'decisions':[
    '有限问题标记complete仅表示该诊断已执行，不表示M203或新设计PASS。该结果细化既知synthetic分支风险，没有证明原生发生率或mask有害；不擅自改源、选择epsilon、停止或重启M203。',
    '继续两个既有稳定ID的原生FPS/fine核及自身/非自身内容mask诊断；实际空闲授权卡、正确身份、目标资产、当前执行租约及三锁满足后沿用原协议执行。server3备选仍需目标运行时/数据核验。',
    '本轮可执行有限控制均已实际完成，下一项原生测试有真实外部资源阻塞，以external_resource_blocked留档，不宣称路线耗尽，不凑新变体，不修改四个辅助hold、目标、授权或调度。',
    '完整六段留档后执行finish并核实FINALIZED、context提交和租约/待提交文件释放；失败则按具体证据修复或abort，不提前声称收尾。当前无原生损害、终态收益、资源释放或用户动作需求等实质变化，保持例行心跳安静。']})
print(json.dumps({'candidate':CID,'stage':'complete','finite_question_only':True,'cpu_exchange_calls':56,
    'cpu_feature_autograd_controls':4,'native_tests_resource_blocked':2,'human_holds_rechecked':0,'M203_best_early':summary['M203_best_early_miou']}))
