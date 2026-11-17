"""Persist the completed user operation without inventing GPU/scientific blocks."""
from gpu1_ops import *
guard(180)
analysis=tick.load(OUT/'native_analysis.json');observed=tick.load(OUT/'final_gpu_and_training_observation.json')
assert observed['GPU1_context_and_all_locks_released']
assert observed['M204_pid']==1085297 and len(observed['M204_native_steps'])>=2
work=tick.load(ROOT/'pipeline/research_work.json')
ids=['m95-scale-specific-boundary-responsibility','m95-expression-specific-point-message']
for cid in ids:
 c=next(c for c in work['candidates'] if c['id']==cid)
 assert c['stage']=='complete' and c['revision_history'][-1]['result']=='passed' and c['scientific_admission'] is False
 for artifact in (OUT/'final_gpu_and_training_observation.json',AUTH,ROOT/'pipeline/decisions/20261019-134533_manual.md'):
  record=evidence(artifact)
  if record not in c['evidence']:c['evidence'].append(record)
pending=[c for c in work['candidates'] if c['stage'] not in ('training','complete','rejected','closed')]
assert len(pending)==4 and all(c['stage']=='blocked' and c.get('blocker_kind')=='human_authorization' for c in pending)
save('user_operation_completion.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'authorization':evidence(AUTH),'updated_servers':evidence(ROOT/'SERVERS.yaml'),'updated_goal':evidence(ROOT/'pipeline/goal.json'),'completed_diagnostic_ids':ids,'frozen_scenes_per_diagnostic':8,'expressions_per_diagnostic':32,'same_cohort_not16_independent_scenes':True,'initial_failed_native_attempts':2,'corrected_native_pair_runs':8,'total_native_attempts':10,'new_trainable_models':0,'new_training':0,'new_scientific_admissions':0,'GPU1_cleanup_verified':True,'M204_kept_on_GPU0':True,'remaining_pending_ids':[c['id'] for c in pending],'remaining_pending_scope':'Original4auxiliarypriorityholdsONLY;NOTGPU1shortageorblanketprojectfreeze','finish_status_at_save':'Notyetvalidated;finish/receipt/lockverificationrequired'})
work['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':ids,
 'evidence':[evidence(OUT/name) for name in ('native_analysis.json','native_analysis.md','final_gpu_and_training_observation.json','resource_authorization_receipt.json','user_operation_completion.json')]+[evidence(AUTH)],
 'resume_condition':'Currenthumanresourceoperationand2predeclared8sceneTRAINdiagnosticscompleted. Remaining4auxiliaryIDskeeptheiroriginalexplicitpriorityscopeholds;actualscope/mainlineevidencerequiredtoresumethem. GPU1isnowavailable/notablock. Continuefutureevidence-backedprimarydesignwithoutduplicatingCPA/closedroutesorassumingnewtrainingadmission.',
 'stop_scope':'external_resource_blockedenumhereappliesONLYtorealremainingauxiliaryhuman-scopeholds,notGPUshortage/globalpause/zeroreservebudget/independentroutesexhaustion. User-requestedboundedGPU1experimentbundleiscomplete.',
 'new_training':0,'new_scientific_admissions':0,'model_config_changes':0,'measurement_revisions':2}
guard();tick.save(ROOT/'pipeline/research_work.json',work)
expr=analysis['families']['expression_fix'];scale=analysis['families']['scale_fix']
notes={'actions':[
 '收到本会话明确人工授权“授权GPU1 可以做实验”后，在当前前台租约内将server4 allowed_gpus改为[0,1]，追加固定UUID及goal资源约束/授权留档；保留server3GPU1、GPU0上的M204和全部科学约束。资源更新发生在begin之后，旧快照不重写、不重复preflight；更新后总名义容量3，不把新增卡授权当科学准入例外。',
 '重新实测GPU1 UUID/空闲/三独占锁，独立运行目录仅改物理GPU编号、UUID和锁名；模型、配置、checkpoint、seed1999、epochs50/max_iters70、原8场景32表达及1e-6阈值不变。原生运行按卡独占、逐对串行，未复制大型checkpoint或干扰GPU0。',
 '保留2次原始失败：尺度完整源置换误差2.86102294921875e-6未过1e-6；表达读数遇bool减法错误。先预登记两项测量层修正，再运行：原标签等值dtype转换；置换控制固定原融合logits并增加identity。完整源置换失败单独保留，不冒称原完整源置换PASS，不改实际baseline/尺度删除或模型。',
 '两组修正后各4对场景全部实际执行。表达固定query消息移植7/8场景误差升高，场景等权均值+'+format(expr['preregistered_positive_direction_mean'],'.9f')+'；尺度细/粗混合fine-cell预期正向只2/8，均值'+format(scale['preregistered_positive_direction_mean'],'.9f')+'，30/32表达可读。两组匹配原生控制最大误差0，原1e-6不放宽；保留全部反向/空分组，不把295相关query行当独立样本或编造总体区间。',
 '22:08:54上海核实GPU1计算进程为空、三锁全释放；GPU0仍为原M204 PID1085297，Train[17/50]2947→2952/4686且日志新鲜，无重启/迁移。begin的best约0.4944@16/50是21:37快照，非本轮诊断收益；server3预检报告不可达，未重探/修复或沿用旧健康说法。',
 '实际产出为2个有界原生诊断、10次原生尝试（2次原失败+8对修正后运行）、2次预登记测量修正、GPU1授权和清理证据；0新模型/准入/新训练。源码派发器旧版已按原hash归档并仅迁移源码证据路径，负结果不改。用量为begin至receipt本地部分窗口，当前完整收据待生成；cache/input和reasoning/output不重复叠加，也不是账单。'],
 'decisions':[
 '两个原稳定ID仅完成预注册的固定TRAIN cohort诊断，科学状态仍为条件性机制读数/总体与新机制效益未知，不是全模型效果或训练mIoU提升。表达特异点侧信息得到该固定样本方向支持；“细尺度相对更负责边界”预期未获本组支持，不能为故事忽略反例。',
 'GPU1已获资源授权且本轮真实执行完毕，之后仍按同一白名单/新鲜占用/独占锁/冻结资产/科学准入执行实验，无需重复索取同一GPU1授权。GPU0 M204继续原训练，不新增未经准入的长训练，不改scheduler或其他项目。',
 '遗留未完成项只剩4个原辅助scope hold；机器stop_reason的external_resource_blocked在此仅指它们，绝不表示GPU1仍被阻塞、全项目暂停、准备预算为0或所有独立路线耗尽。本次明确用户资源操作及两组有界预注册诊断已完成，不凑同义变体填空卡。',
 '本报告保存时finish待验证；只有finish显式通过、收据FINALIZED及上下文提交/所属租约和待提交状态释放均核实后才称本轮完成。所有原始失败、1e-6及历史科学门槛保留，释放后不补写项目。']}
save('report_notes.json',notes)
print(json.dumps({'manual_GPU1_operation_done':True,'bounded_native_diagnostics_completed':2,'GPU1_released':True,'remaining_pending':len(pending),'remaining_scope':'Auxiliaryhumanpriorityholdsonly;NOTGPU1block','new_training':0,'report_notes':str(OUT/'report_notes.json')},ensure_ascii=True,indent=2))
