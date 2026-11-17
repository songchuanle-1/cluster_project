"""Close only on actual mixed resource evidence after executable CPU work."""
from ops import *
guard(180)
slots=tick.load(OUT/'authorized_slots_and_fault.json')
assert slots['server-4']['idle'] is False
assert slots['server-3']['idle'] is None and slots['server-3']['gpu_query']['returncode']==255
assert tick.load(OUT/'expression_preparation_result.json')['native_task_runs']==0
now=datetime.now(timezone.utc);retry=(now+timedelta(minutes=58)).isoformat()
shared=[OUT/name for name in ('authorized_slots_and_fault.json','initial_slot_probe_failure.json','research_result.md')]
blocker='AftercompletednonGPUpreparation,server4authorizedGPU0isheldbyliveM204andall3exclusiveflocks;server3authorizedGPU1NVMLqueriesreturn255UnknownError/devicemanagementhandleunavailable,soitsUUID/occupationisUNKNOWNandcannotbeused. ThisisnotaclaimthatbothGPUscurrentlybusy. Preserveforeignjobs,noreset/restart.'
unblock='Actualresourceevidencechanges:server4GPU0opensORserver3GPU1recoversandexactfrozenruntime/assetsareverifiedthere. Requirefreshpinnedhostname/UUID/liveidleness/all3exclusiveflocksandcurrentforegroundlease;thennativeidentity/query/pointorder/targetcontrols<=1e-6beforetaskinterpretation. Timeraloneisnotavailability.'
advance(shared+[OUT/'expression_preparation_result.json',OUT/'native_manifest.json',OUT/'native_expression_protocol.json',OUT/'close_research.py'],stage='blocked',blocker_kind='external_resource',required_server='server-4',blocker=blocker,retry_after=retry,unblock_condition=unblock,non_gpu_preparation_complete=True,
 gate_result='INCONCLUSIVEtaskinformation:realM95CPUdonorvariationandidentity/indexcontrolsmeasured;nativephysicalpoint/query/target/taskmaskcontrolsnotexecuted. Allscientificgatesfalse. NonGPUcode/statisticsprepared;actualauthorizedCUDAresourcesunavailable.',
 next_action='ResumeSAMEexpressionmessageIDandfrozenmanifest. Afteractualresourceopening/recoveryandfreshownershipchecks,runpair0nativefixedrecipientquerymessage-transplantcontrols;runremainingfrozenpairsONLYifexactcontrols pass. NoM204restartornewtraining.')
scale='m95-scale-specific-boundary-responsibility'
advance(shared,cid=scale,stage='blocked',prior_blocker_kind='exclusive_gpu_slot',blocker_kind='external_resource',required_server='server-4',blocker=blocker,retry_after=retry,unblock_condition=unblock,non_gpu_preparation_complete=True,
 next_action='ResumeSAMEscale-responsibilityIDwithunchangedtick_28fc3749native_manifest/protocolafterfreshresourceverification. Firstexecutesame-devicepair0nativeidentity/permutation/taskmaskcontrols;alloldfloat32/cachedGPUstrictfailuresretained. Neverinferoldbusyserver3fromnewNVMLfailure,nogatewaiver.')
review={'observed_at':now.isoformat(),'related_closed_id':'m202-query-point-bilinear-cooperation','existing_scope':'CompletedM202Q/F2x2energyunderphysicalmessagepermutation,notM95same-sceneexpressionmessageconditionaltargeterror','new_scope':'M95same-scenedifferent-targetexpressionmessagewithfixedrecipientqueryandnativeprimarytarget','boundary_vs_scale_diagnosis':'Notfine/coarseboundarydeletion;entireexistingmessageisintervened,no newmodel','new_training':0,'new_scientific_passes':0,'fault_classification':'RealNVMLqueryfailuremixedwithserver4busy;server3occupationUNKNOWN,notbothoccupied/notidle','source_candidates_preserved':True}
save('scope_and_resource_review.json',review)
advance([OUT/'scope_and_resource_review.json'])
work=tick.load(ROOT/'pipeline/research_work.json')
work['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':[CID,scale],
 'evidence':[evidence(p) for p in shared+[OUT/'expression_cache_result.json',OUT/'expression_preparation_result.json',OUT/'native_manifest.json',OUT/'scope_and_resource_review.json']],
 'resume_condition':unblock,'retry_after':retry,'non_gpu_preparation_complete':True,
 'scope':'1newindependentprimarydiagnosiswithinreservebudget1;oldscaleIDadvancedonlywithrealchangedresourceevidence;noindependentroutesexhaustion/globalpause/fullreserveclaim','new_training':0,'new_scientific_passes':0}
guard();tick.save(ROOT/'pipeline/research_work.json',work)
notes={'actions':[
 '本轮快照18:10:01上海，未重复预检；先登记1个不同于尺度删除的表达特异点消息诊断，再定向核对已完成M202双线性能量诊断边界。固定原query，只用同场景不同原目标表达的现有完整点消息作因果对照，不设计新门控/路由/监督或训练变体。',
 '对真实M95两场景8表达prefix执行CPU移植/撤销对照：有效接收点729/1185，padding及三尺度ID对应全部相同，identity和移植后恢复逐位一致；消息RMS差异0.147421至0.251901。仅说明介入非完全相同消息，缓存无原query/目标/物理坐标，不能当任务收益或科学PASS。',
 '冻结原8场景32表达的原生ILA/prediction_head固定query消息移植入口、原主目标匹配、坐标/索引/撤销identity严控及场景均衡读数；完成语法、donor选择、空组及不重复加权fixture。原生GPU任务执行0、新科学PASS0、准入0、新训练0；既有尺度诊断严格数值失败全部保留。',
 '18:24:41新鲜核实server4GPU0被M204及三锁占用，原生Train[9/50]4571→4575/4686；begin监控best约0.4752，仍低于历史0.5020。server3SSH/hostname正常但GPU1的nvidia-smi/contexts/inventory均返回255，报0000:4B:00.0设备句柄UnknownError，当前UUID/占用未知，不能沿用旧忙碌记录或推断空闲。原slot脚本失败与修复后的只读采集均保留，未重置/驱逐/重启或使用未授权卡。',
 '实际产出1新诊断、1真实缓存CPU测试、1统计/语法fixture及待GPU任务包；旧尺度ID仅补实际资源变化。完整用量收据待finish，本地begin到receipt部分窗口之外及最终回复不含在内，未知不记0，cache/input与reasoning/output不重复相加也不当账单。本报告保存时finish尚待核验。'],
 'decisions':[
 '新信息缺口是点侧消息是否在固定原query条件下携带有用的表达特异任务信息，不是重新包装rank、边界/冗余关联、语言路由或query选择。CPU差异只为可执行性准备；真实mask效果、创新与有效性仍未验证。',
 'server4忙与server3设备查询故障构成当前混合external_resource阻塞；两主线候选均先做完可执行非GPU准备再停放。按真实变化更新旧exclusive标签，不伪称两卡均忙、不更改skill分类器或准入规则。恢复后仍需新鲜UUID/空闲/独占锁/冻结资产及原1e-6控制，失败不放宽。',
 '保留M204现有训练及已执行授权，不重启、不迁移、不改数据/seed/schedule/模型；保留四辅助scope hold，不因定时器到期恢复监督主线或M201，不重复索要已完成的CPA恢复授权。',
 '本轮不宣称独立路线耗尽或科学设计成功。只有finish显式通过并核实上下文提交及租约/待提交状态释放，才称本轮检查完成；否则保留证据后abort。']}
save('report_notes.json',notes)
print(json.dumps({'blocked_ids':[CID,scale],'blocker_kind':'external_resource','retry_after':retry,'new_scientific_passes':0,'notes':str(OUT/'report_notes.json')},ensure_ascii=True,indent=2))
