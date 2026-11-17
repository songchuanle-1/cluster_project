# 本轮研究结果与资源故障

- 本轮87d50f0c；快照2026-10-19 18:10:01上海，真实截止19:10:01；只执行一次begin/preflight，实际任务ID匹配，旧后台调度禁用。
- 快照：运行1/目标2，准入预算1，储备1/2、准备预算1，总待续5/8；4个辅助human hold与1个旧exclusive_gpu_slot未分类项。未改目标、调度、准入或任何旧失败；未把累计122条候选当本轮成果。

## 新诊断及实际CPU测试

- 先登记m95-expression-specific-point-message，按bootstrap要求开始诊断，再审查相关历史。问题是已有层级点消息是否携带对最终mask有用的表达特异信息，而不只是同场景公共context。
- 预注册：固定接收表达的原始最终query、点特征、语言后缀、位置、权重及原生目标/正例配对，仅移植同场景不同原始object_id表达的完整posthierarchy消息。Donor按原表达顺序取下一个不同目标，不按损失或特征择优。预测donor相对own原生mask概率绝对误差上升；先query在表达内平均、再表达在场景内平均，场景等权。
- 这不是新模型或训练变体，不等同M95混合fine-cell的细/粗删除，不是M202点/query双线性能量分解，不恢复语言路由/门控/残差或query选择。仅定向检查最相关旧ID m202-query-point-bilinear-cooperation：其已完成M202空间消息置换的局部能量问题，不能作为本次M95表达移植任务证据。

| 实际测试 | 数据与结果 | 边界 |
|---|---|---|
| 已冻结真实M95 prefix的不同表达消息移植/撤销 | 2场景、8相关表达；每表达729或1185有效接收点；padding与三尺度ID对应全部相同，原样复制和移植后恢复逐位相等 | 缓存不含物理坐标、最终query和目标；不能仅凭ID相同声称原生物理点顺序对照已通过 |
| 真实消息变化读数 | 8组donor的消息RMS差异0.1474212316至0.2519009876，最大绝对差异1.3009877205至2.3721022606 | 说明介入并非完全相同消息；不是任务mask收益、瓶颈、显著性或诊断PASS |
| 原生入口非GPU准备 | 冻结原先8场景32表达、M95epoch16及原source/config/checkpoint/data哈希；native_expression_task.py/runtime/metrics已做语法与donor/空组/场景均衡fixture检查 | 未部署、未运行原生GPU任务；新科学PASS、准入、训练均0 |

- 原生入口必须校验donor与recipient的原生物理superpoint坐标、padding与三尺度assignment完全对应；从原生Criterion正例中只读原annotation主目标的原配对，缺正例记未知，不另挑query。
- 只重放原生ILA和prediction_head，固定原始最终query，保留原gate/fusion/loss；own/原生mask及score/复制identity/移植再恢复的原1e-6对照先通过，才解释任务效果。旧尺度诊断所有float32、CPU/GPU严格失败原样保留，没有借新诊断放宽它们。

## 实际资源变化

- 18:24:41，server4身份dl04-MS-7E06及GPU0预期UUID核实，19849MiB、87%，现有M204 PID1085297占用19796MiB，三独占锁均持有。原生Train[9/50]4571→4575/4686，有实际步数增长；近期日志未见Traceback。
- 同时，server3的SSH及hostname核实，但GPU1的nvidia-smi查询、compute-apps查询及inventory均返回255；原始信息为设备0000:4B:00.0句柄Unknown Error。GPU1当前UUID/显存/占用无法确认，明确为未知，不再沿用17:05的忙碌记录，也不声称空闲或断言具体硬件原因。
- 初始slot脚本在server3抛出CalledProcessError、未保存局部server4结果；原脚本/错误已保留，随后只读采集了返回码和完整设备错误。不是旧Python3.6兼容问题，也未假称原slot脚本成功。
- server4有现有训练，server3授权卡当前不可可靠查询，故没有可安全执行本轮原生CUDA任务的已核实独占卡。未使用server3GPU0/server4GPU1，未共享、驱逐、重置、重启、sudo或更改驱动。
- 旧尺度候选的资源证据实际变化，续写其原稳定ID并改记external_resource以反映“server4忙+server3查询故障”；不是把未知占用伪称exclusive的“两卡均忙”，更不是人为改计数以制造空间。原exclusive_gpu_slot证据/失败仍保留，科学门槛不变。

## 训练与后续

- 本轮begin监控18:10记录M204 best约0.4752，native恢复日志18:24最近3项为0.457/0.461/0.475（仅3位小数）；仍低于历史M95 0.5020与目标0.5100。原实验早期推进，不是新champion或终态配对效能证明。
- 两个主线诊断均完成各自可执行非GPU工作；在同一稳定ID下等待真实资源恢复/开放后，先跑原生pair0的严控，再决定剩余冻结场景。Server3句柄恢复本身不是空闲许可，仍需UUID/实时占用/锁/资产检查；本轮不尝试重置或重启该机。
- 4个旧辅助监督候选保持原scope hold；其18:39:42重试点在本轮快照之后，不把定时器当恢复主线优先级或CPA额外重启授权。
- 本轮只有1个新可区分诊断、1个真实prefix CPU测试和1份待GPU原生任务包；未伪造独立路线耗尽，不凑同义变体，不改变源模型/配置/seed/schedule。
- 本文保存时完整六段report和finish待核验。收据用量为begin至receipt的本地部分窗口，完整用量当前未知；cache属于input、reasoning属于output，不重复相加，不当账单。finish成功并核实提交/租约释放才称本轮完成；释放后不补写项目。
