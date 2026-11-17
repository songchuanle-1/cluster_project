"""Persist an evidenced native-GPU hold, not an invented scientific rejection."""
from ops import *
guard(120)
slots=tick.load(OUT/'authorized_slots_final.json')
assert all(slots[s]['idle'] is False for s in ('server-4','server-3'))
training=tick.load(OUT/'training_final_observation.json')
assert training['alive'] and len(training['latest_native_train_steps'])>1
retry=(datetime.now(timezone.utc)+timedelta(minutes=55)).isoformat()
paths=[OUT/name for name in ('research_result.md','authorized_slots_final.json','native_manifest.json','native_scale_protocol.json','native_preparation_result.json','cached_scale_cpu_result.json','native_scale_precision.json','training_final_observation.json','observe_training_final.py','close_research.py')]
advance(paths,stage='blocked',blocker_kind='exclusive_gpu_slot',required_server='server-4',
 blocker='Non-GPU preparation and strict numeric investigation completed. Exact frozen M95 native CUDA capture requires an exclusive authorized slot:server4physicalGPU0 is held by live M204and all3flocks;alternate server3physicalGPU1 has an active foreign context. No complete fixed-query/target suffix in examined savedprefix;CPU strict reconstruction failures remain preserved.',
 retry_after=retry,
 unblock_condition='Actual authorized slot opens,then fresh identity/UUID/liveoccupation+all3exclusiveflocks and frozenasset hashes verify;first native same-device identity/permutation/target-index controls must pass unchanged1e-6 before interpreting fixed-query task contrasts. Timer alone is not release.',
 gate_result='INCONCLUSIVE. Original float32 numeric failures retained;float64 internal algebra/permutation consistent but cachedGPU reconstruction still fails1e-6. Real task masks not measured;all scientific gates remain false.',
 next_action='Resume SAME stable ID with frozen native_manifest/protocol:verify fresh authorized idle exclusiveGPU,stage exact diagnostic files,bind current foreground lease,and run pair0native task controls. Only if they pass run remaining3frozen pairs. Keep original query/targets/fusion and all negative evidence;do not train a variant or restart M204.',
 non_gpu_preparation_complete=True)
work=tick.load(ROOT/'pipeline/research_work.json')
work['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':[CID],
 'evidence':[evidence(p) for p in paths],
 'resume_condition':'Resume prepared primary scale-responsibility native task only after actual authorized exclusiveGPU availability and fresh integrity controls. Other4auxiliary routes retain independent human-scopeholds;no global project pause,zeroreservebudget or independent-route-exhaustion claim.',
 'retry_after':retry,'non_gpu_work_completed':True,'new_candidates':1,'new_training':0,'new_scientific_passes':0,
 'preparation_budget_note':'At begin actionable reserve0,target2,budget2,pending4/8;1realdiagnosis created. No secondsame-route copy made. Block concerns nativeGPU tests after executableCPUpreparation,not denial of other independentauthorizedpreparation.'}
guard();tick.save(ROOT/'pipeline/research_work.json',work)
notes={'actions':[
 '本轮快照16:48:39上海；在本轮租约内创建1个点特征层级责任诊断，并先做原生源合成CPU契约。重建/query独立性/padding误差0，但float32置换1.0728836059570312e-6未过原1e-6；保留原失败。',
 '事前登记同fixture提升float64精度鉴别：置换误差0。另实际回放真实M95两场景8表达缓存：float32源重建/置换3.814697265625e-6、删除代数最大2.4318695068359375e-5，均未过；float64内部置换0、代数误差约4.44e-14，但对GPU缓存仍7.48e-6未过。不覆盖任何原失败，不冒充科学PASS。',
 '核实保存prefix缺原目标/最终query/完整后缀，执行可做的真实缓存CPU测试；冻结8场景32表达、原生fixed-query prediction_head任务入口、原配对/目标、组分母及场景均衡统计，完成语法/统计fixture。原生GPU任务次数0，尚无实际mask诊断。',
 '17:32:27核实原M204在server4GPU0持续训练，原生Train[8/50]676→679/4686；恢复日志新增mIoU0.457和0.461（3位小数，精确新best未知）。仍低于历史0.5020，不能称完整训练收益。server3GPU1在本轮17:05:39被外部作业占用；未迁移、共享、驱逐或重启。',
 '本轮实际产出：1新诊断、3类CPU数值/缓存测试、1统计fixture及待GPU原生任务包；0新增科学PASS/准入/训练。用量收据窗口为本轮begin至receipt，当前用量未知，不重复叠加缓存/推理，也不当账单。完整六段报告待渲染、finish待验证。'],
 'decisions':[
 '主线仍是不同层级消息如何真实更新点/超点特征并影响mask；显存只是资源约束，不把图活性/高精度代数/早期VAL当机制有效性。保持原1e-6、原目标0.5100及冻结方向。',
 '本轮新诊断按真实exclusive_gpu_slot停放server4；GPU任务前已完成可执行非GPU准备。1小时内或真实资源变化后以原稳定ID续跑原生同设备控制；失败继续如实保留，不能放宽阈值。',
 '四个辅助human-scope hold原retry18:39:42上海未到，不重复复查或索取已执行的CPA恢复授权。仍有准备预算，不伪称储备满/预算0，也不造第二个同义变体；未声称所有独立路线耗尽。',
 '本轮执行完成与科学有效性分开；仅finish显式通过且核实租约/待提交状态释放后才称完成。新M204结果仅为早期恢复进展，不替代最终配对评估。']}
save('report_notes.json',notes)
print(json.dumps({'candidate':CID,'stage':'blocked','required_server':'server-4','retry_after':retry,'report_notes':str(OUT/'report_notes.json'),'new_scientific_passes':0},ensure_ascii=True,indent=2))
