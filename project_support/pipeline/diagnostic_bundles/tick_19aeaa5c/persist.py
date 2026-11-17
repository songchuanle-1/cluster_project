"""Close the finite accounting question and preserve real native holds."""
from datetime import datetime,timedelta,timezone
import json,sys
from ops import guard,save,evidence,run,ROOT,OUT,CID,GOAL
import foreground_tick as tick
guard();now=datetime.now(timezone.utc)
result=tick.load(OUT/'saved_storage_result.json')
four=tick.load(OUT/'server4_live.json');three=tick.load(OUT/'server3_live.json')
resource_time=max(datetime.fromisoformat(four['observed_at']),datetime.fromisoformat(three['observed_at']))
source=tick.load(OUT/'source_verification.json')
assert result['execution_passed'] and result['cuda_initialized'] is False
assert source['unchanged'] and len(source['source_hashes'])==9
assert tick.digest(OUT/'scope_goal.json')==GOAL
assert four['occupied'] and three['occupied'] and four['pid_alive']
assert all(pids==[1995443] for pids in four['lock_owner_pids'].values())
assert result['cpu_exchange_calls']==12 and result['cpu_feature_gradient_executions']==8
cases=result['cases'];assert len(cases)==4
assert all(c['forward_bitwise_equal'] and c['gradient_max_error']==0. for c in cases)
assert [c['maximum_new_floating_saved_storage_bytes'] for c in cases]==[524288,2097152,4194304,4194304]
work=tick.load(ROOT/'pipeline/research_work.json')
scope_ids=['m95-native-relation-other-sign-conflict','m95-native-main-role-weight-precedence',
    'm95-native-secondary-positive-mass','m95-native-between-pair-support']
rechecked=[]
for cid in scope_ids:
    candidate=next(c for c in work['candidates'] if c['id']==cid)
    if datetime.fromisoformat(candidate['retry_after'])>now:continue
    fetched=run([sys.executable,'-B','C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/foreground_tick.py',
        'cluster_project','candidate','--id',cid])
    assert fetched.returncode==0
    detail=json.loads(fetched.stdout)
    assert detail['stage']=='blocked' and detail['blocker_kind']=='human_authorization' and 'auxiliary' in detail['blocker']
    rechecked.append({k:detail[k] for k in ('id','stage','blocker_kind','retry_after','unblock_condition','next_action')})
save('scope_recheck.json',{'observed_at':now.isoformat(),'goal_sha256':GOAL,'new_authorization':False,
    'scope':'Snapshotdue0;onlyoriginalhumanholdswhoseretryactuallyarrivedbythispersistencearecanonicallyrechecked. Server4twoidlequestiondoesnotrestoreauxiliarypriorityorGPU1authorization.',
    'items':rechecked})
for item in rechecked:
    candidate=next(c for c in work['candidates'] if c['id']==item['id'])
    candidate['evidence'].append(evidence(OUT/'scope_recheck.json'))
    candidate['last_rechecked_at']=now.isoformat();candidate['retry_after']=(now+timedelta(hours=4)).isoformat()
paths=[OUT/name for name in ('saved_storage_prereg.md','saved_storage_cpu.py','ops.py','execute.py','manifest.json',
    'source_verification.json','saved_storage_result.json','execution.json','server4_live.json','server3_live.json','scope_goal.json','scope_recheck.json')]
paths += [ROOT/'pipeline/reviews/motivation_review_20261018_19aeaa5c.md',ROOT/'pipeline/designs/exp_design_20261018_19aeaa5c.md',
    ROOT/'pipeline/decisions/20261018-101810_other.md']
entries=[evidence(path) for path in paths]
summary={'observed_at':now.isoformat(),'finite_diagnostic_status':'EXECUTED_COMPLETE_NOT_MODEL_PASS',
    'new_diagnostic_ids':1,'artificial_input_conditions':4,'cpu_exchange_calls':12,'cpu_feature_gradient_executions':8,
    'maximum_new_floating_saved_storage_bytes':[c['maximum_new_floating_saved_storage_bytes'] for c in cases],
    'N128_small_leaves_valid_edges':1024,'N128_small_leaves_allocated_neighbor_slots':4096,
    'N128_new_floating_unique_saved_storage_bytes_including_diagnostic_readout':4456448,
    'forward_bitwise_equal':True,'matching_gradient_max_error':0.,'cuda_initialized':False,
    'new_training_models':0,'model_revisions':0,'admissions':0,'launches':0,'source_changed':False,
    'native_network_forwards':0,'native_backwards':0,'native_FPS_calls':0,'optimizer_steps':0,'checkpoint_loads':0,'train_preprocessing':0,
    'human_holds_rechecked':len(rechecked),'human_holds_unblocked':0,'native_resource_holds_reconciled':2,
    'M203_best_early_miou':max(four['validation_miou']),'M203_native_validation_count':len(four['validation_miou']),
    'M203_epoch_steps':four['epoch_steps'],
    'measurement_limits':'CPUretaineduniquestorageincludingdiagnosticsquare-meanreadout;notallocatorpeak,CUDAmemory,TRAINdistribution,trainedefficacy,memorysavingsorresourcegate',
    'evidence':entries}
save('progress_summary.json',summary);entries.append(evidence(OUT/'progress_summary.json'))
candidate=next(c for c in work['candidates'] if c['id']==CID)
assert candidate['stage']=='diagnosis'
candidate.update(stage='complete',failure_scope='inconclusive',updated_at=now.isoformat(),evidence=entries,
    next_action='FiniteCPUretained-storagequestionanswered;donotrerunidenticalprofileorcallGPUpeak/savings/PASS. AnyfuturememoryrealizationneedsprespecifiedequivalenceandmatchednativeGPUmeasurementunderoriginalstablemechanismgates;noneimplemented. Continueexistingnativegeometry/self-nonselfdiagnosticswhenactuallyidleauthorizedresourcesexist. PreserveM203/source/seed/scheduleandGPU1permission.',
    scientific_result='Actualunchangedsource savesN*K*Cfloat32gatherstorageforbackward:0.5/2/4MiBforN16/64/128. Sixteen8pointleavesatN128retain4MiBwith1024validedges/4096allocatedslots. All4hook/plain/no_gradcontrolsagree,8CPUfeaturegradientsmatch. NoGPUmemoryorbenefitclaim.',
    gates={'finite_storage_accounting':'COMPLETE4CONDITIONS','CPU_control_matching':'PASS_BITWISE_FORWARD_ZERO_GRADIENT_DIFFERENCE',
        'CUDA_peak_memory':'NOT_MEASURED','memory_saving_implementation':'NOT_IMPLEMENTED','native_mask_effect':'UNKNOWN','model_efficacy':'UNKNOWN'})
resource_ids=['fle-self-neighbor-content-separation','fle-fixed-membership-metric-geometry-audit']
for cid in resource_ids:
    pending=next(c for c in work['candidates'] if c['id']==cid)
    assert pending['stage']=='blocked' and pending['blocker_kind']=='exclusive_gpu_slot'
    pending['evidence'] += [evidence(OUT/'server4_live.json'),evidence(OUT/'server3_live.json')]
    pending['blocker']='Non-GPUpreparationscomplete/frozen,notrerun. Live10:15:51-52Shanghai:server4physicalGPU0M203PID1995443ownsall3locks,20685MiB/util30;server3physicalGPU1foreignPID1453,18130MiB/util100. Bothauthorizedslotsoccupied. Server4GPU1wasidleatprior10:01readonlyquerybutstillunauthorized;notusedorcountedasprojectcapacity. NoCUDA/nativeGPUtest,sharing,eviction,resetorlockdeletion.'
    pending['last_rechecked_at']=resource_time.isoformat();pending['retry_after']=(resource_time+timedelta(hours=1)).isoformat()
work['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':[CID,*resource_ids,*[item['id'] for item in rechecked]],
    'evidence':[evidence(OUT/'progress_summary.json'),evidence(OUT/'server4_live.json'),evidence(OUT/'server3_live.json'),evidence(OUT/'scope_recheck.json')],
    'resume_condition':'FiniteCPUstorageaccountingcomplete. Resumeoriginalfrozennativegeometry/masktestswhenacurrentlyauthorizedpinnedcardistrulyidleandfreshowningexecutionlease,lifetimeGPUlocksandasset/runtimechecksallpass. Keepauxiliaryscopeholdsandunconfirmedserver4GPU1permission;nonewmodelorrestart.',
    'retry_after':(resource_time+timedelta(hours=1)).isoformat(),'scope':'RealnativeGPUresourceblock,notrouteexhaustion,memoryrepair,GPUpeakmeasurementortrainedharm/benefitproof'}
guard();tick.save(ROOT/'pipeline/research_work.json',work)
save('report_notes.json',{'actions':[
    '本轮不可变快照为上海时间2026-10-18 10:09:47/design，原截止11:09:47不改；核实实际会话身份与前台归属、后台调度禁用、24约束/11禁止及原资源授权。第0-3段保留preflight时点。已先登记fle-backward-saved-neighbor-storage-audit，再执行有限诊断；不是新增模型或参数搜索。收尾待finish。',
    '10:15:51只读确认M203-FLE在server4物理GPU0第20/50轮，原生步4140至4150/4686增长；19次原生VAL，早期best0.48853155970573425，仍低于baseline0.4894、历史M95 0.5020及目标0.5100，历史目标差距0.0080不变。没有额外VAL、checkpoint选择、训练变更或终态结论。',
    '实际执行一个不同于旧几何/连续性测试的有限效率诊断：K32/H8/C256/float32保持生产值，4种预注册人工输入。按底层storage指针去重并单列输入别名后，最大新增浮点gather存储在N16/64/128分别为524288/2097152/4194304字节，随N线性增长；N128分16个8点叶虽仅1024有效边，仍分配4096槽且最大gather仍4MiB。',
    '12次CPU exchange及8次CPU特征梯度执行；hook/普通/no_grad前向逐位一致，匹配梯度最大差0且有限非零。N128的新浮点保存总量4456448字节包含诊断square-mean读出，不能当作完整原生激活、分配峰值或CUDA显存。没有已实现的显存节省或资源PASS；参数减少与激活成本不能混为一谈。',
    '9个生产源文件和部署配置哈希未变；server4 CPU单线程，CUDA隐藏且未初始化。无旧测试重跑、TRAIN预处理、checkpoint加载、FPS、原生网络前后向、optimizer步、分块/checkpointing实现、模型修订、准入、部署或新启动。',
    '10:15:51-52两张授权卡均占用：server4 GPU0由M203及三锁持有，server3 GPU1是外部任务。两项原生诊断保留原冻结资产、checkpoint、cohort及1e-6容差，以真实资源表续等。此前10:01只读看到server4 GPU1空闲，但用户仅询问空闲情况、尚未同意扩大授权；本轮未使用或计入容量，不共享/驱逐/reset/删锁。',
    '本轮留档时实际到期并按ID核对的辅助授权hold数量为'+str(len(rechecked))+'；只核对原解除条件，未出现新优先级恢复授权或主线必需的辅助证据，原范围与科学门槛保留，已到期者按原四小时界限再查。不因到期或空槽重开、恢复M201或派生变体。',
    '实际产出为一个有限CPU存储诊断、4条件/12算子调用/8特征梯度执行、两项资源核实、实际到期的授权复查及审查/设计/记忆/报告。收据用量窗口仅本轮begin至收据，不含先前读取、晚到记录及最终答复；生成前总量未知。缓存属于输入、推理属于输出，不重复相加、不当账单或科学收益。'],
    'decisions':[
    '有限诊断complete只表示源算子的该记账问题已执行，不表示新机制有效、峰值显存更低或模型通过准入。效率仍是主线约束，不替代不同层级真实点特征更新的核心贡献；M203原训练保持。',
    '后续先完成两个既有原生几何及自身/非自身内容mask诊断；真实空闲授权卡、固定身份、目标资产、当前租约和三锁满足才执行原协议。server4 GPU1未授权，server3备选仍需目标运行时/数据验证。',
    '可执行有限CPU核对已实际完成；剩余原生工作有真实外部资源阻塞，以external_resource_blocked收尾，不宣称路线耗尽、为deadline凑变体或放宽科学门槛，不修改目标/授权/调度。',
    '完整六段留档后执行finish，核实收据FINALIZED、context提交及租约/待提交文件释放；否则保留证据并具体修复或abort。当前没有训练终态、原生新结论、资源释放或新增用户动作需求，例行心跳保持安静。']})
print(json.dumps({'candidate':CID,'stage':'complete','finite_question_only':True,'cases':4,'cpu_exchange_calls':12,
    'cpu_feature_gradient_executions':8,'native_tests_resource_blocked':2,'human_holds_rechecked':len(rechecked),'new_training_models':0}))
