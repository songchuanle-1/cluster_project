# cluster_project 决策索引

| 时间 | 类型 | 问题 | 决策 |
|------|------|------|------|
| 2026-07-17 06:49:12 | [other](20260717T064912_other.md) | 决策日志功能自测：写入是否正常？ | 本条为功能验证记录，可保留 |
| 2026-07-17 06:56:46 | [route_change](20260717T065646_route_change.md) | A3 true_route 已 kill (0.4922, 差于 A1 0.4951 和 B1 0.5012)，gpu0 | 推送 B4 refine 变体 model_base1_quard2_c2f_enc_lite_posA_l1_refi |
| 2026-07-17 15:23:35 | [next_batch](20260717T152335_next_batch.md) | refine(0.4914@ep16 4/10)/detail(0.4779@ep10) 均在跑，下一批变体设计什么？ | 已实现 B5 ResidualAttnRefine (cluster_mode=residual)，并写入 pipeli |
| 2026-07-17 16:24:30 | [next_batch](20260717T162430_next_batch.md) | 队列深度不足(1 waiting/2 GPU=0.5x<3x)，补齐到 ≥可用卡+1=3 | 分别入队 PosA seed=2026 和 seed=3407 多 seed 稳定性验证(只改 seed, config |
| 2026-07-17 16:34:53 | [next_batch](20260717T163453_next_batch.md) | GPU1 waiting=0, GPU0排队3任务全在gpu:0 (B5-residual+2seed) — 卡浪费，需 | GPU1队列：C1-layerscale (LayerScale gate, signed near-identity) |
| 2026-07-17 20:55:42 | [queue_push](20260717T205542_queue_push.md) | server-4 gpu0 空闲，推送哪个排队实验？ | 尝试启动 [B5 ResidualAttnRefine (补Q/K/V梯度)] configs/Quard/model_ |
| 2026-07-17 20:55:58 | [queue_push](20260717T205558_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [C1 LayerScale gate (signed near-identity vs sigmoid)] co |
| 2026-07-18 09:22:38 | [queue_push](20260718-092238_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [C2 位置编码类型C消融] configs/Quard/model_base1_quard2_c2f_enc_l |
| 2026-07-18 12:53:55 | [manual](20260718-125355_manual.md) | 队列中 PosA-seed2026 + PosA-seed3407 多 seed 验证占 2 | 移除 PosA-seed2026 和 PosA-seed3407，队列改为聚焦� |
| 2026-07-18 12:58:07 | [manual_batch](20260718-125807_manual_batch.md) | 基于当前结果设计新变体: champion 0.5012, gap=-0.0 | 入队 C3-refine (MultiScale_Gather_Refine) + D1-detail (det |
| 2026-07-18 15:36:26 | [queue_push](20260718-153626_queue_push.md) | layerscale 终态后 GPU0 空闲, monitor 推 B5 被 check_c | 手动 pl.sh train server-4 B5-residual gpu0, 启动成功 P |
| 2026-07-18 15:36:26 | [question](20260718-153626_question.md) | check_code_sync 误比对外层仓库致所有自动推送� | 留待用户确认(后台会话被 bg 隔离守卫阻止编� |
| 2026-07-18 16:03:17 | [manual](20260718-160317_manual.md) | 用户授权修复 3 个基建 bug (15:36 question 的后续 | 已修: check_goal.py __main__ / check_code_sync 嵌套仓� |
| 2026-07-18 16:13:19 | [next_batch](20260718-161319_next_batch.md) | waiting=2<3 队列缺口1, 机制轴已满仓(B5/C3/D1), 补 | 入队 E1-cosine (champion唯一变量换CosineAnnealingLR T |
| 2026-07-18 16:43:43 | [route_change](20260718-164343_route_change.md) | E1-cosine(16:13入队)与 roadmap §5 冲突: 'epochs/max_it | 撤回 E1-cosine (用户确认); schedule 修正留待'新� |
| 2026-07-18 16:53:15 | [manual](20260718-165315_manual.md) | roadmap 接入方式: 软链 vs 独立整理版?  | 取消软链, 按 goal 蒸馏 20260715 计划为 pipeline/ro |
| 2026-07-18 17:12:18 | [route_change](20260718-171218_route_change.md) | 文档架构: goal+roadmap 双层 vs goal.json 单文件契� | 取消 roadmap 层(用户确认); 硬约束7条+禁区8条� |
| 2026-07-18 18:40:19 | [next_batch](20260718-184019_next_batch.md) | 队列深度不足(waiting=2 < 可用卡数2+1=3), 机制轴 | 入队 E2-finer (cluster_layer_nums=[512,128,16]) + E3-wider |
| 2026-07-18 19:23:46 | [route_change](20260718-192346_route_change.md) | 18:40 越权入队的 E2-finer/E3-wider 是否保留?  | 删除 E2-finer + E3-wider (用户确认): 移出 queue.json |
| 2026-07-18 20:10:26 | [next_batch](20260718-201026_next_batch.md) | 队列深度不足(waiting=2 < 可用卡数2+1=3), 机制轴 | 入队 F1-2layer (cluster_att_num_layers=2+L1) + F2-init00 ( |
| 2026-07-18 20:51:13 | [route_change](20260718-205113_route_change.md) | 20:03 tick 第三次越权入队 F1-2layer/F2-init00, 如何 | 删除 F1/F2 (用户确认'处理越权入队'); 保留升� |
| 2026-07-18 21:04:30 | [route_change](20260718-210430_route_change.md) | 队列深度不足(waiting=2 < 可用卡2+1=3)但活跃保� | 跳过自主设计。等待B5/C3/D1任一终态出结果或� |
| 2026-07-19 08:04:22 | [route_change](20260719-080422_route_change.md) | 队列深度不足(waiting=2 < 可用卡2+1=3)但活跃保� | 跳过自主设计。等待机制三候选(B5/C3/D1)任一� |
| 2026-07-19 09:04:51 | [route_change](20260719-090451_route_change.md) | 队列深度不足(waiting=2 < 可用卡2+1=3)但活跃保� | 跳过自主设计。继续监控B5/C3/D1，等待任一终� |
| 2026-07-19 10:04:47 | [route_change](20260719-100447_route_change.md) | 队列深度不足(waiting=2 < 可用卡2+1=3)但活跃保� | 跳过自主设计。等待机制三候选(B5/C3/D1)任一� |
| 2026-07-19 11:04:34 | [route_change](20260719-110434_route_change.md) | 队列深度不足(waiting=0 < 可用卡2+1=3)但活跃保� | 跳过自主设计。等待机制三候选(C3/D1)任一终� |
| 2026-07-19 11:34:03 | [next_batch](20260719-113403_next_batch.md) | 自主分析: champion 0.5012 gap=-0.0088, 队列空, B5/C1/ | 入队 E4(residual+detail组合) + F1(2层cluster_attn) + F2 |
| 2026-07-19 12:04:48 | [route_change](20260719-120448_route_change.md) | Queue depth OK (3 waiting ≥ 3 = 2 GPU + 1), 活跃保留� | 跳过自主设计。继续监控 C3-refine(ep4, 0.4072) 和 |
| 2026-07-19 13:04:45 | [route_change](20260719-130445_route_change.md) | Queue depth 3/2 OK (≥3); 活跃保留持续: B5 done_early | 跳过自主设计。队列已有 3 waiting (E4/F1/F2, 20260 |
| 2026-07-19 14:04:49 | [route_change](20260719-140449_route_change.md) | Queue depth 3/2 OK (≥3), 活跃保留持续 (B5 done_early | 跳过自主设计。队列深度 3 waiting ≥ 3 阈值, C3 |
| 2026-07-19 15:05:27 | [skip_design](20260719-150527_skip_design.md) | Queue depth 3/2 OK (≥3, E4/F1/F2 waiting). Active retentio | 跳过自主设计。继续监控 C3/D1 进度，等待任� |
| 2026-07-19 16:05:35 | [skip_design](20260719-160535_skip_design.md) | Queue depth 3/2 OK (≥3, E4/F1/F2 waiting). Active retentio | 跳过自主设计。继续监控 C3/D1 进度。C3 序列� |
| 2026-07-19 17:04:19 | [skip_design](20260719-170419_skip_design.md) | Queue depth 3/2 OK (≥3, E4/F1/F2 waiting). Active retentio | 跳过自主设计。继续监控 C3/D1 进度, 等待任一 |
| 2026-07-19 18:04:58 | [skip_design](20260719-180458_skip_design.md) | Queue depth 3/2 OK (≥3, E4/F1/F2 waiting). Active retentio | 跳过自主设计。C3 序列震荡(D1 持续上升), 继� |
| 2026-07-19 19:05:36 | [skip_design](20260719-190536_skip_design.md) | Queue depth 3/2 OK (≥3, E4/F1/F2 waiting). Active retentio | 跳过自主设计。继续监控 C3-refine(ep17,0.4931 刷� |
| 2026-07-19 20:06:03 | [skip_design](20260719-200603_skip_design.md) | Queue depth 3/2 OK (≥3, E4/F1/F2 waiting). Active retentio | 跳过自主设计。继续监控 C3/D1 进度，等待任� |
| 2026-07-19 21:05:58 | [skip_design](20260719-210558_skip_design.md) | Queue depth 3/2 OK (≥3, E4/F1/F2 waiting). Active retentio | 跳过自主设计。继续监控 C3/D1 进度。C3 no_impr= |
| 2026-07-19 22:04:20 | [skip_design](20260719-220420_skip_design.md) | Queue depth 3/2 OK (≥3, E4/F1/F2 waiting). Active retentio | 跳过自主设计。继续监控 C3/D1, 等待 C3/D1 任一 |
| 2026-07-19 23:03:24 | [queue_push](20260719-230324_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [E4 residual mode + detail message_type (组合协同)] configs/Q |
| 2026-07-19 23:03:39 | [queue_push](20260719-230339_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [F1 cluster_att_num_layers=2 (增强 token 交互)] configs/Quard |
| 2026-07-19 23:04:56 | [manual](20260719-230456_manual.md) | 手动kill C3-refine(ep25, 0.4931, 8/10接近早停); D1-det | C3→done_earlystop(0.4931); D1→stopped_unknown(0.4975, � |
| 2026-07-19 23:07:08 | [skip_design](20260719-230708_skip_design.md) | 队列深度不足 (waiting=1 < 可用卡2+1=3), 是否自� | 跳过自主设计。仅由 monitor 对既有 waiting 任务 |
| 2026-07-19 23:08:40 | [question](20260719-230840_question.md) | D1-detail 被意外中断(ep14, 0.4975 仍单调上升, 机� | 留待用户确认。本轮不自主重跑 D1 亦不补位� |
| 2026-07-19 23:21:36 | [early_stop](20260719-232136_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_detail] 连续 23 次验证未刷 | kill PID=1369862 on server-4 gpu=1 |
| 2026-07-19 23:39:00 | [route_change](20260719-233900_route_change.md) | goal.json 活跃保留约束(B5/C3/D1出结果前禁止自� | 解除保留: 从 goal.json constraints 删除活跃保留� |
| 2026-07-19 23:40:09 | [next_batch](20260719-234009_next_batch.md) | 保留已解除, 深度1<可用卡2+1=3 触发设计. 基于 | 重新入队F1-2layer(2layer on champion) + 新增G1-detail_ |
| 2026-07-19 23:44:09 | [route_change](20260719-234409_route_change.md) | 用户: 回到机制研究, 不要调参. F1/F2/G1(num_layer | 移除F1-2layer/F2-init00/G1-detail_2layer (调参批次); � |
| 2026-07-19 23:50:46 | [manual_batch](20260719-235046_manual_batch.md) | 回到机制研究: 实现A4-shuffle控制组 + M1-QGC新机 | 入队A4-shuffle(TrueRoute+随机索引,论文内容路由� |
| 2026-07-20 00:06:13 | [skip_design](20260720-000613_skip_design.md) | 队列深度 waiting=2 < 可用卡2+1=3 触发自主设计� | 跳过自主补位. 原因: (1)exp_design_20260719-234500 � |
| 2026-07-20 00:06:17 | [question](20260720-000617_question.md) | 队列深度持续 2<3, 但下一批机制变体 M2-DCR(deta | 留待用户确认. 选项: (a)授权现在入队 M2-DCR 打 |
| 2026-07-20 00:10:32 | [route_change](20260720-001032_route_change.md) | goal.json 机制声称与实际实验矛盾(description说� | 更新goal.json: description改'multi-scale cluster context' |
| 2026-07-20 01:04:33 | [skip_design](20260720-010433_skip_design.md) | 队列深度 waiting=2 < 可用卡2+1=3 触发自主设计� | 跳过自主补位. 保留依据: decisions/20260720-000617_ |
| 2026-07-20 02:04:44 | [skip_design](20260720-020444_skip_design.md) | 队列深度 waiting=2 < 可用卡2+1=3 触发自主设计� | 跳过自主补位. 保留依据: decisions/20260720-000617_ |
| 2026-07-20 03:04:18 | [skip_design](20260720-030418_skip_design.md) | 队列深度 waiting=2 < 可用卡2+1=3 触发自主设计� | 跳过自主补位. 保留依据: decisions/20260720-000617_ |
| 2026-07-20 04:05:08 | [skip_design](20260720-040508_skip_design.md) | 队列深度 waiting=2 < 可用卡2+1=3 触发自主设计,  | 跳过自主补位。继续监控 E4-res_detail(ep8,0.4584� |
| 2026-07-20 05:04:00 | [skip_design](20260720-050400_skip_design.md) | 队列深度 waiting=2 < 可用卡2+1=3 触发自主设计,  | 跳过自主补位。继续监控 E4-res_detail(ep9,0.4628� |
| 2026-07-20 06:04:04 | [skip_design](20260720-060404_skip_design.md) | 队列深度 waiting=2 < 可用卡2+1=3 触发自主设计,  | 跳过自主补位。继续监控 E4-res_detail(ep11,0.4833  |
| 2026-07-20 07:04:18 | [skip_design](20260720-070418_skip_design.md) | 队列深度 waiting=2 < 可用卡2+1=3 触发自主设计� | 跳过自主补位. Phase 0.5 活跃保留未解除: questio |
| 2026-07-20 08:04:28 | [skip_design](20260720-080428_skip_design.md) | 队列深度 waiting=2 < 可用卡2+1=3 触发自主设计� | 跳过自主补位. Phase 0.5 活跃保留未解除: questio |
| 2026-07-20 09:04:26 | [skip_design](20260720-090426_skip_design.md) | 队列深度 waiting=2 < 可用卡2+1=3 触发自主设计� | 跳过自主补位。继续监控 E4-res_detail(ep15,Best0.4 |
| 2026-07-20 10:04:49 | [skip_design](20260720-100449_skip_design.md) | 队列深度 waiting=2 < 可用卡2+1=3 触发自主设计� | 跳过自主补位。继续监控 E4-res_detail(ep17,Best0.4 |
| 2026-07-20 11:06:48 | [skip_design](20260720-110648_skip_design.md) | 队列深度 waiting=2 < 可用卡2+1=3 触发自主设计� | 跳过自主补位. Phase 0.5 活跃保留未解除(question |
| 2026-07-20 12:04:49 | [skip_design](20260720-120449_skip_design.md) | 队列深度 waiting=2 < 可用卡2+1=3 触发自主设计� | 跳过自主补位. Phase 0.5 活跃保留未解除(question |
| 2026-07-20 13:03:46 | [queue_push](20260720-130346_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [A4 TrueRoute+随机路由索引 (控制组: 内容路由 vs 稀疏正则)] configs/Quard/t |
| 2026-07-20 13:07:50 | [skip_design](20260720-130750_skip_design.md) | 队列深度不足(waiting=1 < 可用卡2+1=3)触发自主� | 跳过自主补位. 不入队 M2-DCR/M3-XSRes, 不自主决� |
| 2026-07-20 13:08:02 | [question](20260720-130802_question.md) | 待决 question 20260720-000617 更新: 本 tick D1-detail(r | 留待用户确认. 选项: (a)授权入队 M2-DCR — D1-de |
| 2026-07-20 13:38:42 | [next_batch](20260720-133842_next_batch.md) | depth=1(M1) < 可用卡2+1=3 触发自主设计; 补什么� | 入队M6-QSF(query进尺度融合gate) + M16-CSR(cluster tok |
| 2026-07-20 16:03:28 | [queue_push](20260720-160328_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M1 Query-Gated Context (用丢弃的attn给cluster token加门控)] conf |
| 2026-07-20 16:15:54 | [next_batch](20260720-161554_next_batch.md) | depth=2(M6+M16) < 可用卡2+1=3 触发自主设计; 补什� | 入队M17-ORT(cluster orthogonality regularization, coarse t |
| 2026-07-21 13:43:07 | [manual](20260721-134307_manual.md) | 手动kill M1-QGC(30ep 0.4939 7/10) + A4-shuffle(23ep 0.4941 | kill → 终态分析 → 推 M6-QSF(GPU0) + M16-CSR(GPU1);  |
| 2026-07-21 14:09:31 | [next_batch](20260721-140931_next_batch.md) | 队列深度不足(waiting=1 < 可用卡2+1=3), 触发自主 | 入队 M18-S2FM (2-scale fine+medium [256,64] drop coarse) + |
| 2026-07-21 14:11:38 | [queue_push](20260721-141138_queue_push.md) | 代码同步: 新模型包 s2fm/s2fc + configs sync 到 serv | sync_model.sh → server-4:/data/songcl/Project/Cluster_proj |
| 2026-07-21 15:04:25 | [skip_design](20260721-150425_skip_design.md) | Queue depth sufficient (3 waiting >= 3=2可用卡数+1), bot | 跳过自主设计。继续监控 M6-QSF(ep3,0.3605) + M16-C |
| 2026-07-21 18:05:11 | [skip_design](20260721-180511_skip_design.md) | Queue depth sufficient (3 waiting >= 3=2可用卡数+1), bot | 跳过自主设计。继续监控 M6-QSF + M16-CSR 进度， |
| 2026-07-21 19:06:17 | [skip_design](20260721-190617_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M17-ORT/M18-S2FM/M19- | 跳过自主设计。继续监控 M6-QSF + M16-CSR 进度， |
| 2026-07-21 20:06:28 | [skip_design](20260721-200628_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M17-ORT/M18-S2FM/M19- | 跳过自主补位。继续监控 M6-QSF(ep12, 0.4808↑) +  |
| 2026-07-21 21:04:35 | [skip_design](20260721-210435_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M17-ORT/M18-S2FM/M19- | 跳过自主补位。继续监控 M6-QSF(ep14, 0.4844↑, no |
| 2026-07-21 22:04:54 | [skip_design](20260721-220454_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1), M17-ORT/M18-S2FM/M19 | 跳过自主设计。继续监控 M6-QSF(ep15, 0.4848↑) +  |
| 2026-07-21 23:04:14 | [skip_design](20260721-230414_skip_design.md) | Queue depth sufficient (3 waiting ≥ 3=2可用卡+1), both  | 跳过自主设计。继续监控 M6-QSF + M16-CSR 进度， |
| 2026-07-22 00:04:30 | [skip_design](20260722-000430_skip_design.md) | Queue depth sufficient (3 waiting ≥ 3=2可用卡+1), both  | 跳过自主设计。继续监控 M6-QSF(ep19, 0.4848, 4/10) |
| 2026-07-22 02:05:35 | [skip_design](20260722-020535_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M17-ORT/M18-S2FM/M19- | 跳过自主设计。继续监控 M6-QSF(ep22, 0.4866↑, no |
| 2026-07-22 03:04:43 | [skip_design](20260722-030443_skip_design.md) | Queue depth 3/2 OK (M17-ORT/M18-S2FM/M19-S2FC waiting, ≥ 2 | 跳过自主设计。继续监控 M6-QSF(ep24, 0.4866↑, no |
| 2026-07-22 04:04:46 | [skip_design](20260722-040446_skip_design.md) | Queue depth 3/2 OK (M17-ORT/M18-S2FM/M19-S2FC waiting, ≥ 2 | 跳过自主设计。继续监控 M6-QSF + M16-CSR 进度， |
| 2026-07-22 05:04:46 | [skip_design](20260722-050446_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M17-ORT/M18-S2FM/M19- | 跳过自主设计。继续监控 M6-QSF(ep28, 0.4866, 7/10  |
| 2026-07-22 06:04:42 | [skip_design](20260722-060442_skip_design.md) | Queue depth 3/2 OK (M17-ORT/M18-S2FM/M19-S2FC waiting, ≥ 2 | 跳过自主设计。继续监控 M6-QSF(ep29, 0.4866, 8/10) |
| 2026-07-22 07:03:27 | [queue_push](20260722-070327_queue_push.md) | server-4 gpu0 空闲，推送哪个排队实验？ | 尝试启动 [M17 Cluster Orthogonality Regularization (coarse token |
| 2026-07-22 07:04:49 | [queue_push](20260722-070449_queue_push.md) | M6-QSF stopped_unknown @GPU0 (0.4866), M17-ORT 之前 monito | 手动 remote_train.sh server-4 M17-ORT gpu0 → 启动成� |
| 2026-07-22 07:09:07 | [next_batch](20260722-070907_next_batch.md) | Queue depth 2 waiting < 3 (2可用卡+1), M6-QSF stopped_unk | 入队 M20-DET: D1-detail clean rerun (configs/Quard/model_b |
| 2026-07-22 07:12:55 | [queue_push](20260722-071255_queue_push.md) | server-4 gpu0 空闲，推送哪个排队实验？ | 尝试启动 [M18 Scale Ablation: 2-scale fine+medium [256,64] drop  |
| 2026-07-22 08:03:27 | [queue_push](20260722-080327_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M18 Scale Ablation: 2-scale fine+medium [256,64] drop co |
| 2026-07-22 08:12:06 | [next_batch](20260722-081206_next_batch.md) | Queue depth 2<3 (M19-S2FC+M20-DET waiting), M6-QSF/M17-ORT s | 入队 M21-HYB (hybrid context+detail message): 新model包  |
| 2026-07-22 09:03:29 | [queue_push](20260722-090329_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M19 Scale Ablation: 2-scale fine+coarse [256,8] drop med |
| 2026-07-22 09:10:39 | [terminal](20260722-091039_terminal.md) | M16-CSR early-stopped at epoch 30/50, Best=0.4875 < baseline | M16-CSR → done_earlystop in queue.json; 生成 pipeline/an |
| 2026-07-22 09:10:42 | [bugfix](20260722-091042_bugfix.md) | M17-ORT crash x2: DEC.__init__() got unexpected keyword argu | Phase 3b 修复 #1: 加 orth_weight=0.01 到 DEC.__init__; � |
| 2026-07-22 09:10:45 | [queue_update](20260722-091045_queue_update.md) | Queue depth after updates: M17-ORT(re-queued)+M20-DET+M21-HY | 跳过自主设计本 tick. 队列深度达标, 活跃实验 |
| 2026-07-22 10:05:26 | [skip_design](20260722-100526_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M17-ORT/M20-DET/M21-H | 跳过自主设计。继续监控 M18-S2FM/M19-S2FC 进度� |
| 2026-07-22 11:04:39 | [skip_design](20260722-110439_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M17-ORT/M20-DET/M21-H | 跳过自主设计。继续监控 scale ablation 进度，� |
| 2026-07-22 12:05:12 | [skip_design](20260722-120512_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M17-ORT/M20-DET/M21-H | 跳过自主设计。继续监控 scale ablation (M18/M19) � |
| 2026-07-22 13:04:45 | [skip_design](20260722-130445_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M17-ORT/M20-DET/M21-H | 跳过自主设计。继续监控 scale ablation (M18/M19) � |
| 2026-07-22 14:06:00 | [skip_design](20260722-140600_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M17-ORT/M20-DET/M21-H | 跳过自主设计。继续监控 scale ablation (M18/M19) � |
| 2026-07-22 15:04:57 | [skip_design](20260722-150457_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M17-ORT/M20-DET/M21-H | 跳过自主设计。继续监控 scale ablation 进度，� |
| 2026-07-22 16:05:30 | [skip_design](20260722-160530_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M17-ORT/M20-DET/M21-H | 跳过自主设计。继续监控 scale ablation 进度，� |
| 2026-07-22 18:05:10 | [skip_design](20260722-180510_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M17-ORT/M20-DET/M21-H | 跳过自主设计。继续监控 scale ablation (M18/M19) � |
| 2026-07-22 19:04:33 | [skip_design](20260722-190433_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M17-ORT/M20-DET/M21-H | 跳过自主设计。继续监控 scale ablation (M18/M19) � |
| 2026-07-22 20:07:11 | [skip_design](20260722-200711_skip_design.md) | Queue depth 3 waiting ≥ 3 (2可用卡+1), M17-ORT/M20-DET/ | 跳过自主设计。Phase 0.5 双闸门通过 (goal.json � |
| 2026-07-22 21:04:59 | [skip_design](20260722-210459_skip_design.md) | Queue depth 3 waiting ≥ 3 (2可用卡+1), M17-ORT/M20-DET/ | 跳过自主设计。队列深度达标(3≥3), 双卡均忙 |
| 2026-07-22 22:08:42 | [skip_design](20260722-220842_skip_design.md) | Queue depth 3 waiting ≥ 3 (2可用卡+1)，M17-ORT/M20-DET | 跳过自主设计。队列深度达标(3≥3=可用卡2+1)� |
| 2026-07-22 23:05:37 | [skip_design](20260722-230537_skip_design.md) | Queue depth 3 waiting ≥ 3 (可用卡数2+1)，M17-ORT/M20- | 跳过自主设计。队列深度达标(3≥3)，无需补� |
| 2026-07-23 00:06:07 | [early_stop](20260723-000607_early_stop.md) | M18-S2FM epoch 24 验证 mIoU=0.4763, no_improve=10/10, Best | M18-S2FM → done_earlystop(0.4933), 释放 server-4 GPU0; � |
| 2026-07-23 00:06:07 | [queue_push](20260723-000607_queue_push.md) | M18-S2FM done_earlystop 释放 server-4 GPU0 (0% util, 41MB) | 启动 M17-ORT (orthogonality regularization, FIXED orth_wei |
| 2026-07-23 00:11:22 | [next_batch](20260723-001122_next_batch.md) | Queue depth 2<3 after M18-S2FM done_earlystop+M17-ORT pushed | 入队 M22-XCA: Cross-Scale Cluster Attention — 3-scale cl |
| 2026-07-23 02:03:28 | [queue_push](20260723-020328_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M20 D1-detail clean rerun: reproduce detail message_type |
| 2026-07-23 02:09:24 | [next_batch](20260723-020924_next_batch.md) | Queue depth insufficient (waiting=2 < 可用卡2+1=3). Champ | 入队 M23-CMX (max-pool cluster aggregation): 修改 champi |
| 2026-07-23 02:09:24 | [terminal](20260723-020924_terminal.md) | M19-S2FC stopped_unknown (process disappeared @ ep26, Best=0 | M19-S2FC → stopped_unknown, 生成 terminal analysis. Scal |
| 2026-07-23 04:04:19 | [skip_design](20260723-040419_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M21-HYB/M22-XCA/M23-C | 跳过自主设计。队列深度达标(3≥3=可用卡2+1)� |
| 2026-07-23 07:05:25 | [skip_design](20260723-070525_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M21-HYB/M22-XCA/M23-C | 跳过自主补位。继续监控 M17-ORT(ep11, 0.4837↑)+M |
| 2026-07-23 08:04:14 | [skip_design](20260723-080414_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M21-HYB/M22-XCA/M23-C | 跳过自主补位。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-23 09:05:05 | [skip_design](20260723-090505_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M21-HYB/M22-XCA/M23-C | 跳过自主补位。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-23 11:04:22 | [skip_design](20260723-110422_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M21-HYB/M22-XCA/M23-C | 跳过自主补位。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-23 12:04:42 | [skip_design](20260723-120442_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M21-HYB/M22-XCA/M23-C | 跳过自主补位。继续监控 M17-ORT(ep18, 0.4931, no_i |
| 2026-07-23 13:04:15 | [skip_design](20260723-130415_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M21-HYB/M22-XCA/M23-C | 跳过自主补位。继续监控 M17-ORT(ep19, Best=0.5005, |
| 2026-07-23 14:04:52 | [skip_design](20260723-140452_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M21-HYB/M22-XCA/M23-C | 跳过自主补位。继续监控 M17-ORT + M20-DET 进度� |
| 2026-07-23 15:05:05 | [skip_design](20260723-150505_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M21-HYB/M22-XCA/M23-C | 跳过自主补位。继续监控 M17-ORT + M20-DET 进度� |
| 2026-07-23 16:05:18 | [skip_design](20260723-160518_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M21-HYB/M22-XCA/M23-C | 跳过自主补位。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-23 17:05:52 | [skip_design](20260723-170552_skip_design.md) | Queue depth 3/2 OK (≥3=可用卡2+1, M21-HYB/M22-XCA/M23-C | 跳过自主补位。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-23 19:04:54 | [skip_design](20260723-190454_skip_design.md) | Queue depth 3/2 OK (≥3=可用卡2+1, M21-HYB/M22-XCA/M23-C | 跳过自主补位。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-23 20:04:35 | [skip_design](20260723-200435_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1), M17-ORT(ep23 0.5005  | 跳过自主补位。继续监控 M17-ORT/M20-DET 进度，� |
| 2026-07-23 21:05:05 | [skip_design](20260723-210505_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M21-HYB/M22-XCA/M23-C | 跳过自主补位。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-23 22:04:41 | [skip_design](20260723-220441_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1), M17-ORT/M20-DET 双� | 跳过自主补位。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-23 23:05:05 | [skip_design](20260723-230505_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1), M17-ORT(ep24, 0.5005 | 跳过自主补位。继续监控 M17-ORT (距 champion 0.50 |
| 2026-07-24 04:04:22 | [skip_design](20260724-040422_skip_design.md) | Queue depth 3/2 OK (≥3=可用卡2+1, M21-HYB/M22-XCA/M23-C | 跳过自主设计。继续监控 M17-ORT/M20-DET 进度，� |
| 2026-07-24 05:05:25 | [skip_design](20260724-050525_skip_design.md) | Queue depth 3/2 OK (≥3=可用卡2+1). M17-ORT ep28 no_impr | 跳过自主设计。继续监控 M17-ORT 早停临界点(� |
| 2026-07-24 06:07:52 | [queue_push](20260724-060752_queue_push.md) | M17-ORT done_earlystop(0.5005@ep28) 释放 server-4 GPU0; � | 启动 M21-HYB (hybrid context+detail message) on server-4 G |
| 2026-07-24 06:10:57 | [next_batch](20260724-061057_next_batch.md) | Queue depth不足 (waiting=2 < 可用卡2+1=3). Champion 0.5 | 入队 M24-ORT-D: ORT orthogonality + detail message_type, c |
| 2026-07-24 06:11:16 | [terminal](20260724-061116_terminal.md) | M17-ORT second run stopped_unknown→应为done_earlystop: l | M17-ORT→done_earlystop(0.5005), 生成 terminal analysis,  |
| 2026-07-24 10:05:15 | [skip_design](20260724-100515_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M22-XCA/M23-CMX/M24-O | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-24 12:04:37 | [skip_design](20260724-120437_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M22-XCA/M23-CMX/M24-O | 跳过自主设计. 队列深度达标(3≥3=可用卡2+1),  |
| 2026-07-24 13:04:11 | [skip_design](20260724-130411_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M22-XCA/M23-CMX/M24-O | 跳过自主设计. 继续监控 M20-DET 早停临界点(7/1 |
| 2026-07-24 14:04:10 | [skip_design](20260724-140410_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M22-XCA/M23-CMX/M24-O | 跳过自主设计。继续监控 M20-DET (ep21, Best=0.4955 |
| 2026-07-24 15:04:39 | [skip_design](20260724-150439_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M22-XCA/M23-CMX/M24-O | 跳过自主设计。继续监控 M20-DET + M21-HYB 进度� |
| 2026-07-24 16:04:19 | [skip_design](20260724-160419_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M22-XCA/M23-CMX/M24-O | 跳过自主设计. 继续监控 M20-DET(ep22,0.4955,8/10) + |
| 2026-07-24 17:04:50 | [skip_design](20260724-170450_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M22-XCA/M23-CMX/M24-O | 跳过自主补位。继续监控 M20-DET (8/10 no_impr, 预 |
| 2026-07-24 18:06:11 | [skip_design](20260724-180611_skip_design.md) | 队列深度达标(waiting=3 ≥ 可用卡2+1=3), M20-DET(ep | 跳过自主补位。继续监控 M20-DET 早停临界点(8/ |
| 2026-07-24 20:04:57 | [skip_design](20260724-200457_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M22-XCA/M23-CMX/M24-O | 跳过自主补位。队列深度当前达标(3≥3), 双卡 |
| 2026-07-24 21:04:25 | [skip_design](20260724-210425_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M22-XCA/M23-CMX/M24-O | 跳过自主补位。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-24 22:04:28 | [skip_design](20260724-220428_skip_design.md) | 队列深度达标(waiting=3 ≥ 可用卡2+1=3), M20-DET(ep | 跳过自主设计。队列深度达标(3≥3)，双卡均� |
| 2026-07-24 23:07:25 | [queue_push](20260724-230725_queue_push.md) | M20-DET stopped_unknown(0.4955@ep23)释放GPU1, M22-XCA待� | 启动 M22-XCA (Cross-Scale Cluster Attention) on server-4 G |
| 2026-07-24 23:10:50 | [next_batch](20260724-231050_next_batch.md) | Queue depth after M22-XCA push: waiting=2 < 可用卡2+1=3,  | 入队 M25-REF: cluster_mode=refine (MultiScale_Gather_Refin |
| 2026-07-24 23:10:50 | [terminal](20260724-231050_terminal.md) | M20-DET detail clean rerun #3 stopped_unknown (0.4955@ep23)  | 生成终态分析 M20-DET_stopped_unknown_20260724-230301.m |
| 2026-07-25 05:06:05 | [status_check](20260725-050605_status_check.md) | M22-XCA launched 2026-07-24 23:05, monitor shows '无日志' | 确认正常运行: epoch 3/50 (~1480/4686 iters), 0.52s/ite |
| 2026-07-25 07:06:08 | [skip_design](20260725-070608_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M23-CMX/M24-ORT-D/M25 | 跳过自主设计。继续监控 M21-HYB (Best=0.4836, no_i |
| 2026-07-25 08:05:07 | [skip_design](20260725-080507_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1), M21-HYB(gpu0 ep13 0. | 跳过自主设计. 队列深度达标(3≥3=可用卡2+1),  |
| 2026-07-25 08:05:11 | [route_change](20260725-080511_route_change.md) | 旧 question 20260720-000617/130802 (M2-DCR 待用户确认) | 判定 question 上下文已演进为已失效: M1-QGC 已� |
| 2026-07-25 10:06:27 | [skip_design](20260725-100627_skip_design.md) | Queue depth sufficient (3 waiting >= 3=2可用卡+1), both G | 跳过自主设计。继续监控 M21-HYB (Best=0.4836, no_i |
| 2026-07-25 11:06:41 | [skip_design](20260725-110641_skip_design.md) | Queue depth sufficient (3 waiting >= 3=2可用卡+1), both G | 跳过自主设计。继续监控 M21-HYB (no_impr=3/10 appr |
| 2026-07-25 12:05:37 | [skip_design](20260725-120537_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M23-CMX/M24-ORT-D/M25 | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-25 15:06:48 | [skip_design](20260725-150648_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1), M21-HYB(gpu0 ep15 0. | 跳过自主设计。M22-XCA Best=0.4954仍在上升(距cham |
| 2026-07-25 15:06:59 | [question](20260725-150659_question.md) | M22-XCA config work_dir 路径缺 /Project/ (写为 /data/so | 留待用户确认: (a)让M22-XCA跑完不改(手动监控)  |
| 2026-07-25 16:06:13 | [status_check](20260725-160613_status_check.md) | Tick 2026-07-25 16:03: 队列深度 3≥3 达标, M21-HYB(0. | 跳过自主设计, 生成 A4-shuffle 缺失终态分析。� |
| 2026-07-25 17:04:58 | [skip_design](20260725-170458_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1), M21-HYB(gpu0 ep16 Be | 跳过自主设计。继续监控 M21-HYB/M22-XCA 进度。M |
| 2026-07-25 18:05:54 | [skip_design](20260725-180554_skip_design.md) | Queue depth 3/2 OK (≥3=可用卡2+1, M23-CMX/M24-ORT-D/M25 | 跳过自主设计。继续监控 M21-HYB 收敛(刚刷Best  |
| 2026-07-25 19:06:13 | [skip_design](20260725-190613_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M23-CMX/M24-ORT-D/M25 | 跳过自主设计。继续监控 M21-HYB/M22-XCA 进度。M |
| 2026-07-25 21:03:26 | [queue_push](20260725-210326_queue_push.md) | server-4 gpu1 空闲，推送哪个排队实验？ | 尝试启动 [M23 Cluster Max-Pool: max-pool aggregation for cluster |
| 2026-07-25 21:07:59 | [bugfix](20260725-210759_bugfix.md) | M23-CMX push失败: ModuleNotFoundError model_base2_quard1 � | 创建 model_base1_quard2_c2f_enc_lite_posA_l1_cmx/__init__. |
| 2026-07-25 21:08:02 | [terminal](20260725-210802_terminal.md) | M22-XCA monitor误判stopped_unknown, 实际done_earlystop B | M22-XCA → done_earlystop; 生成终态分析; 更新 exper |
| 2026-07-25 22:07:32 | [bugfix](20260725-220732_bugfix.md) | M23-CMX push 失败第2次: ModuleNotFoundError model_base2_ | 提交 _DEFAULT_MODEL fix + CMX model 包到 Cluster 仓库  |
| 2026-07-25 23:04:33 | [queue_push](20260725-230433_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M23 Cluster Max-Pool: max-pool aggregation for cluster b |
| 2026-07-25 23:10:34 | [next_batch](20260725-231034_next_batch.md) | 队列深度不足(waiting=2 < 可用卡2+1=3), 触发自主 | 入队 M26-ORT-HYB (ORT orthogonality + HYB hybrid context+d |
| 2026-07-26 02:05:14 | [skip_design](20260726-020514_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M24-ORT-D/M25-REF/M26 | 跳过自主设计。队列深度达标(3≥3)，双卡均� |
| 2026-07-26 03:05:17 | [skip_design](20260726-030517_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1). M21-HYB GPU0 ep20 Be | 跳过自主设计. 队列深度达标(3 waiting = M24-ORT-D |
| 2026-07-26 04:05:47 | [skip_design](20260726-040547_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1), M21-HYB(GPU0 ep21 0. | 跳过自主设计. 队列深度达标(3≥3=可用卡2+1),  |
| 2026-07-26 05:05:36 | [skip_design](20260726-050536_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M24-ORT-D/M25-REF/M26 | 跳过自主补位. 继续监控 M21-HYB (Best=0.4898, no_im |
| 2026-07-26 06:04:35 | [terminal_analysis](20260726-060435_terminal_analysis.md) | A4-shuffle done_earlystop (Best=0.4941, ~19/50) 缺失终态 | 生成 pipeline/analyses/A4-shuffle_done_earlystop_20260726- |
| 2026-07-26 07:04:38 | [skip_design](20260726-070438_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M24-ORT-D/M25-REF/M26 | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-26 08:03:28 | [queue_push](20260726-080328_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M24 ORT+detail: orthogonality regularization + detail me |
| 2026-07-26 08:10:56 | [next_batch](20260726-081056_next_batch.md) | Queue depth insufficient (waiting=2 < 可用卡2+1=3). Champ | 入队 M27-ORT-W5 (orth_weight=0.05, stronger ORT) + M28-ORT |
| 2026-07-26 09:05:12 | [skip_design](20260726-090512_skip_design.md) | Queue depth 4/2 OK (≥3=2可用卡+1, M25-REF/M26-ORT-HYB/M | 跳过自主设计。队列深度 4≥3 达标, 双卡均被 |
| 2026-07-26 10:04:29 | [skip_design](20260726-100429_skip_design.md) | Queue depth 4/2 OK (≥3=2可用卡+1), 双卡均忙 (M24-OR | 跳过自主设计。继续监控 M24-ORT-D (ORT+detail 极� |
| 2026-07-26 11:04:56 | [skip_design](20260726-110456_skip_design.md) | Queue depth 4/2 OK (≥3=2可用卡+1), M24-ORT-D(GPU0 ep5 0 | 跳过自主设计。队列深度达标(4≥3=可用卡2+1), |
| 2026-07-26 12:04:04 | [skip_design](20260726-120404_skip_design.md) | Queue depth 4/2 OK (≥3=2可用卡+1, M25-REF/M26-ORT-HYB/M | 跳过自主设计。队列深度达标(4≥3=可用卡2+1), |
| 2026-07-26 16:04:30 | [skip_design](20260726-160430_skip_design.md) | Tick #145: queue depth 4≥3 (M25-REF/M26-ORT-HYB/M27-ORT-W5 | 跳过自主设计。继续监控 M24-ORT-D (ort+detail 早� |
| 2026-07-26 17:04:13 | [skip_design](20260726-170413_skip_design.md) | Tick #146: queue depth 4≥3 (M25-REF/M26-ORT-HYB/M27-ORT-W5 | 跳过自主设计。继续监控 M24-ORT-D (ORT+detail 极� |
| 2026-07-26 18:05:10 | [skip_design](20260726-180510_skip_design.md) | Queue depth 4≥3 (M25-REF/M26-ORT-HYB/M27-ORT-W5/M28-ORT-W1 | 跳过自主设计。队列深度达标(4≥3=可用卡2+1), |
| 2026-07-26 19:04:21 | [skip_design](20260726-190421_skip_design.md) | Tick #148: 队列深度 4≥3 达标, M24-ORT-D(GPU0 ep14 Be | 跳过自主设计。队列深度达标(4≥3=2可用卡+1), |
| 2026-07-26 20:04:29 | [skip_design](20260726-200429_skip_design.md) | Tick #149: 队列深度 4≥3 达标 (M25-REF/M26-ORT-HYB/M2 | 跳过自主设计。队列深度达标(4≥3=2可用卡+1), |
| 2026-07-26 21:05:46 | [skip_design](20260726-210546_skip_design.md) | Queue depth 4/2 OK (≥3=2可用卡+1, M25-REF/M26-ORT-HYB/M | 跳过自主设计。队列深度达标(4≥3=可用卡2+1), |
| 2026-07-26 22:04:37 | [skip_design](20260726-220437_skip_design.md) | Tick #151: 队列深度 4≥3 OK, 双卡均忙 (M24-ORT-D ep | 跳过自主实验设计, 仅监控+报告  |
| 2026-07-26 23:04:11 | [skip_design](20260726-230411_skip_design.md) | Queue depth 4≥3 (≥可用卡2+1), M23-CMX(GPU1 ep27 Best= | 跳过自主设计。队列深度达标(4≥3=可用卡2+1), |
| 2026-07-27 00:03:27 | [queue_push](20260727-000327_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M25 Cluster Refine: MultiScale_Gather_Refine instead of  |
| 2026-07-27 00:04:34 | [queue_push](20260727-000434_queue_push.md) | server-4 GPU1 空闲 (util 0%, mem 1747MiB < 1GB 阈值边� | 推送 M25 Cluster Refine: MultiScale_Gather_Refine 到 serv |
| 2026-07-27 01:05:05 | [terminal](20260727-010505_terminal.md) | M23-CMX stopped_unknown (Best=0.4910@28/50, process disappea | M23-CMX→终态分析: max-pool vs champion mean-pool γ=-0 |
| 2026-07-27 02:04:56 | [skip_design](20260727-020456_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M26-ORT-HYB/M27-ORT-W | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-27 03:04:32 | [skip_design](20260727-030432_skip_design.md) | Queue depth 3/2 OK (≥3=可用卡2+1). M26-ORT-HYB/M27-ORT- | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-27 04:04:26 | [skip_design](20260727-040426_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M26-ORT-HYB/M27-ORT-W | 跳过自主设计。继续监控 M24-ORT-D (ort+detail) + M |
| 2026-07-27 05:03:26 | [queue_push](20260727-050326_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M26 ORT+HYB: orthogonality regularization + hybrid conte |
| 2026-07-27 05:10:40 | [next_batch](20260727-051040_next_batch.md) | Queue depth insufficient (waiting=2 < 可用卡2+1=3). Champ | 入队 M29-DCA: Dual-branch Cluster Aggregation (mean+max co |
| 2026-07-27 06:04:13 | [skip_design](20260727-060413_skip_design.md) | Tick #156: 队列深度 3/2 OK (≥3=可用卡2+1). M25-REF( | 跳过自主设计。队列深度达标(3≥3=可用卡2+1)� |
| 2026-07-27 07:04:42 | [skip_design](20260727-070442_skip_design.md) | Tick #157: Queue depth 3/2 OK (≥3=2可用卡+1, M27-ORT-W5 | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-27 08:04:49 | [skip_design](20260727-080449_skip_design.md) | Tick #158: 队列深度 3≥3=2可用卡+1 达标, M25-REF(G | 跳过自主设计。继续监控 M25-REF 和 M26-ORT-HYB � |
| 2026-07-27 09:04:39 | [skip_design](20260727-090439_skip_design.md) | Tick #159: 队列深度 3≥3=2可用卡+1 达标, M25-REF(G | 跳过自主设计。继续监控 M25-REF 和 M26-ORT-HYB � |
| 2026-07-27 11:04:38 | [skip_design](20260727-110438_skip_design.md) | Tick #161: queue depth 3/2 OK (≥3=2可用卡+1). M25-REF(G | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-27 13:03:39 | [skip_design](20260727-130339_skip_design.md) | Tick #162 (2026-07-27 13:03): queue depth 3/2 OK (≥3=2可� | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-27 14:05:08 | [skip_design](20260727-140508_skip_design.md) | Tick #163 (2026-07-27 14:03): queue depth 3/2 OK (≥3=2可� | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-27 15:04:57 | [skip_design](20260727-150457_skip_design.md) | Tick #164 (2026-07-27 15:03): queue depth 3/2 OK (≥3=2可� | 跳过自主设计。队列深度达标(3≥3=2可用卡+1), |
| 2026-07-27 16:03:27 | [queue_push](20260727-160327_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M27 ORT weight=0.05: stronger orthogonality regularizati |
| 2026-07-27 16:17:35 | [next_batch](20260727-161735_next_batch.md) | Queue depth 2<3 (M28-ORT-W1+M29-DCA waiting, need 3≥2GPU+1 | 入队 M30-ITK: Increased TopK — per_layer_topk_list=[64,3 |
| 2026-07-27 16:17:41 | [terminal](20260727-161741_terminal.md) | M25-REF refine stopped_unknown: process disappeared during e | M25-REF→stopped_unknown(0.4892). 生成终态分析 pipeli |
| 2026-07-27 17:05:12 | [skip_design](20260727-170512_skip_design.md) | Tick #166 (2026-07-27 17:03): queue depth 3/2 OK (≥3=2可� | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-27 20:05:13 | [skip_design](20260727-200513_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1), M26-ORT-HYB(GPU0 ep1 | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-27 21:04:43 | [skip_design](20260727-210443_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M28-ORT-W1+M29-DCA+M3 | 跳过自主设计。继续监控 M26-ORT-HYB (ep15 0.4916,  |
| 2026-07-28 01:05:11 | [skip_design](20260728-010511_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1), M26-ORT-HYB(GPU0 ep2 | 跳过自主实验设计。继续监控 M26-ORT-HYB 收敛 ( |
| 2026-07-28 04:04:33 | [skip_design](20260728-040433_skip_design.md) | Queue depth 3/2 OK (≥3=2可用卡+1, M28-ORT-W1+M29-DCA+M3 | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-28 05:03:32 | [queue_push](20260728-050332_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M28 ORT weight=0.001: weaker orthogonality regularizatio |
| 2026-07-28 05:08:03 | [terminal](20260728-050803_terminal.md) | M26-ORT-HYB stopped_unknown (Best=0.4998@ep26/50, process di | 生成终态分析 pipeline/analyses/M26-ORT-HYB_stopped_unk |
| 2026-07-28 05:09:48 | [next_batch](20260728-050948_next_batch.md) | 队列深度不足(waiting=2 < 可用卡2+1=3), 触发自主 | 入队 M31-NH4: configs/Quard/nh4/model_base1_quard2_c2f_enc |
| 2026-07-28 07:04:28 | [skip_design](20260728-070428_skip_design.md) | Queue depth 3 ≥ 3 (2可用卡+1), 无需触发自主实验 | 跳过自主设计, 仅监控。M27-ORT-W5(ep19,0.4946)/M28- |
| 2026-07-28 08:10:23 | [next_batch](20260728-081023_next_batch.md) | Queue depth insufficient (waiting=1 < 可用卡2+1=3). Champ | 入队 M35-DOA (dropout=0.1) + M36-GELU (activation_fn=gelu) |
| 2026-07-28 08:10:23 | [queue_push](20260728-081023_queue_push.md) | Code sync: 新 configs doa/gelu/dg 同步到 server-4  | rsync configs/Quard/{doa,gelu,dg}/ → server-4:/data/songcl |
| 2026-07-28 13:07:58 | [terminal_analysis](20260728-130758_terminal_analysis.md) | M27-M31 (ORT-W5/ORT-W1/DCA/ITK/NH4) 终态分析自 tick #18 | 补全 M27-ORT-W5(0.4959@ep19 stopped_unknown) + M28-ORT-W1( |
| 2026-07-28 14:10:46 | [queue_prune](20260728-141046_queue_prune.md) | M35-DOA(dropout=0.1)/M36-GELU(activation_fn=gelu)/M37-DG(dro | 移除 M35/M36/M37 从 queue.json。Queue depth 从 4→1, � |
| 2026-07-28 14:10:46 | [next_batch](20260728-141046_next_batch.md) | Queue depth 1<3 (可用卡2+1), champion 0.5012 gap +0.0088. | 入队 M38-FLM (FiLM multiplicative modulation: cluster→γ |
| 2026-07-28 14:12:52 | [code_sync](20260728-141252_code_sync.md) | M38-FLM + M39-C2C 模型代码/config YAML 需同步到 serv | rsync via pl.sh sync: Cluster repo push + working tree updat |
| 2026-07-28 15:04:36 | [skip_design](20260728-150436_skip_design.md) | Tick #184 (2026-07-28 15:03): queue depth 3/2 OK (≥3=2可� | 跳过自主设计。队列深度达标(3≥3=2可用卡+1), |
| 2026-07-28 16:04:28 | [skip_design](20260728-160428_skip_design.md) | Tick #185 (2026-07-28 16:03): queue depth 3≥3 (2可用卡+ | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-28 17:04:47 | [skip_design](20260728-170447_skip_design.md) | Tick #186: Queue depth 3/2 OK (≥3=2可用卡+1), M32-DRP(e | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-28 19:05:27 | [skip_design](20260728-190527_skip_design.md) | Tick #188 (2026-07-28 19:03): Queue depth 3/2 OK (≥3=2可� | 跳过自主实验设计。仅监控+生成 tick 报告。� |
| 2026-07-28 20:04:58 | [skip_design](20260728-200458_skip_design.md) | Tick #189 (2026-07-28 20:03): Queue depth 3/2 OK (≥3=2可� | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-07-28 21:04:10 | [skip_design](20260728-210410_skip_design.md) | Tick #190 (2026-07-28 21:03): Queue depth 3/2 OK (≥3=2可� | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-07-28 22:04:27 | [skip_design](20260728-220427_skip_design.md) | Tick #191 (2026-07-28 22:03): Queue depth 3/2 OK (≥3=2可� | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-07-28 23:04:11 | [skip_design](20260728-230411_skip_design.md) | Tick #192 (2026-07-28 23:03): Queue depth 3/2 OK (≥3=2可� | 跳过自主实验设计。队列深度达标(3≥3=可用� |
| 2026-07-29 00:04:39 | [skip_design](20260729-000439_skip_design.md) | Tick #193: Queue depth 3/2 OK (≥3=2可用卡+1), M32-DRP(e | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-07-29 02:03:26 | [queue_push](20260729-020326_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M34 Query-to-Point: query全局均值projected直接加到inst_feats] co |
| 2026-07-29 02:13:37 | [next_batch](20260729-021337_next_batch.md) | Queue depth 2<3 (可用卡2+1). M33-DTW 0.4968 终态, 再� | 入队 M40-SWI: Sigmoid-Weighted Injection — _cluster_to_p |
| 2026-07-29 06:05:09 | [skip_design](20260729-060509_skip_design.md) | Tick #196: Queue depth 3≥3=2可用卡+1 (M38-FLM/M39-C2C/M | 跳过自主设计。仅监控+生成 tick 报告。  |
| 2026-07-29 07:04:25 | [skip_design](20260729-070425_skip_design.md) | Tick #197: Queue depth 3/2 OK (≥3=2可用卡+1). M32-DRP(e | 跳过自主设计。队列深度达标(3≥3=可用卡2+1)� |
| 2026-07-29 08:04:29 | [skip_design](20260729-080429_skip_design.md) | Tick #198 (2026-07-29 08:03): Queue depth 3/2 OK (≥3=2可� | 跳过自主设计。队列深度达标(3≥3=2可用卡+1), |
| 2026-07-29 09:04:30 | [skip_design](20260729-090430_skip_design.md) | Tick #199 (2026-07-29 09:03): Queue depth 3/2 OK (≥3=2可� | 跳过自主设计。队列深度达标(3≥3=2可用卡+1), |
| 2026-07-29 10:04:06 | [skip_design](20260729-100406_skip_design.md) | Tick #200: Queue depth 3/2 OK (≥3=2可用卡+1). M32-DRP e | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-29 12:05:50 | [skip_design](20260729-120550_skip_design.md) | Tick #201: Queue depth 3/2 OK (≥3=2可用卡+1). M32-DRP(G | 跳过自主设计。队列深度达标(3≥3=可用卡2+1), |
| 2026-07-29 13:04:20 | [skip_design](20260729-130420_skip_design.md) | Tick #202 (2026-07-29 13:03): Queue depth 3/2 OK (≥3=2可� | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-07-29 14:05:19 | [skip_design](20260729-140519_skip_design.md) | Tick #203 (2026-07-29 14:03): Queue depth 3/2 OK (≥3=2可� | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-07-29 15:04:44 | [skip_design](20260729-150444_skip_design.md) | Tick #204 (2026-07-29 15:03): Queue depth 3/2 OK (≥3=2可� | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-07-29 16:03:29 | [queue_push](20260729-160329_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M38 FiLM Modulation: cluster context→(gamma,beta)→gamma* |
| 2026-07-29 16:11:56 | [terminal](20260729-161156_terminal.md) | M32-DRP stopped_unknown (Best=0.5012@ep28 TIES CHAMPION). Ro | 生成 pipeline/analyses/M32-DRP_stopped_unknown_20260729-16 |
| 2026-07-29 16:11:56 | [queue_push](20260729-161156_queue_push.md) | M32-DRP stopped_unknown 释放 server-4 GPU0, 推送哪个� | 启动 M38-FLM (FiLM multiplicative modulation) on server-4  |
| 2026-07-29 16:11:56 | [next_batch](20260729-161156_next_batch.md) | Queue depth 2<3 (可用卡2+1), DRP 终态后队列收缩. C | 入队 M41-CTF: Cluster Token FFN — per-scale 2-layer FFN  |
| 2026-07-29 16:21:40 | [queue_push](20260729-162140_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M39 Cluster-to-Cluster: intra-scale self-attention refin |
| 2026-07-29 17:14:35 | [terminal](20260729-171435_terminal.md) | M34-Q2P stopped_unknown Best=0.4904. Direct query-to-point i | Generated pipeline/analyses/M34-Q2P_stopped_unknown_20260729 |
| 2026-07-29 17:14:38 | [next_batch](20260729-171438_next_batch.md) | Queue depth 2<3 (2GPU+1=3). Champion 0.5012 gap +0.0088. M34 | Enqueued M42-WCA (Weighted Cluster Aggregation, pool_type=we |
| 2026-07-29 17:14:40 | [code_sync](20260729-171440_code_sync.md) | M42-WCA + M43-CLN model code/config YAML need sync to server | rsync via pl.sh sync: Cluster HEAD e80974f..e563ee2. New wca |
| 2026-07-29 18:04:25 | [skip_design](20260729-180425_skip_design.md) | Tick #207 (2026-07-29 18:03): Queue depth 4/2 OK (≥3=2可� | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-07-29 19:04:38 | [skip_design](20260729-190438_skip_design.md) | Queue depth 4/2 OK (≥3=2可用卡+1, M40-SWI/M41-CTF/M42-W | 跳过自主实验设计。仅监控+生成 tick 报告。  |
| 2026-07-30 03:05:21 | [skip_design](20260730-030521_skip_design.md) | Queue depth 4≥3 OK (≥可用卡2+1). M29-DCA/M30-ITK/M31- | 跳过自主设计。仅监控+生成 tick 报告。M38-FLM( |
| 2026-07-30 04:04:17 | [skip_design](20260730-040417_skip_design.md) | Queue depth 4≥3 OK (≥可用卡2+1). M38-FLM(ep18,0.4849, | 跳过自主设计。仅监控+生成 tick 报告。Queue de |
| 2026-07-30 05:04:43 | [skip_design](20260730-050443_skip_design.md) | Queue depth 4≥3 OK (≥可用卡2+1). M38-FLM(ep20,0.4849, | 跳过自主设计。仅监控+生成 tick 报告。Queue de |
| 2026-07-30 06:04:11 | [skip_design](20260730-060411_skip_design.md) | Tick #214: Queue depth 4≥3 OK (≥可用卡2+1). Both GPUs | 跳过自主设计。仅监控+生成 tick 报告。Queue de |
| 2026-07-30 10:04:02 | [skip_design](20260730-100402_skip_design.md) | Tick #215: Queue depth 4/2 OK (≥3=2可用卡+1), M38-FLM(G | 跳过自主设计。仅监控+生成 tick 报告。Queue de |
| 2026-07-30 11:05:31 | [skip_design](20260730-110531_skip_design.md) | Queue depth 4/2 OK (≥3=2可用卡+1, M40-SWI/M41-CTF/M42-W | 跳过自主设计。仅监控+生成 tick 报告。Queue de |
| 2026-07-30 12:05:56 | [skip_design](20260730-120556_skip_design.md) | Tick #217: Queue depth 4≥3 OK (≥可用卡2+1). M38-FLM e | 跳过自主设计。队列深度达标(4≥3=可用卡2+1), |
| 2026-07-30 13:05:50 | [skip_design](20260730-130550_skip_design.md) | Queue depth 4≥3(可用卡2+1), 两卡全被 running 占用 | 跳过自主补位。M38-FLM ep31 Best=0.4865 no_impr=8/10 � |
| 2026-07-30 14:03:38 | [queue_push](20260730-140338_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M40 Sigmoid-Weighted Injection: scale fusion sigmoid(ind |
| 2026-07-30 14:03:58 | [queue_push](20260730-140358_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M41 Cluster Token FFN: per-scale 2-layer FFN+residual+La |
| 2026-07-30 14:16:34 | [terminal](20260730-141634_terminal.md) | M38-FLM stopped_unknown Best=0.4865 (FiLM), M39-C2C done_ear | Generated pipeline/analyses/ for both. FiLM confirms gate/mo |
| 2026-07-30 14:16:34 | [next_batch](20260730-141634_next_batch.md) | Queue depth 2<3 (2GPU+1=3). Champion 0.5012 gap +0.0088. C2C | Enqueued M44-CSF: Cross-Scale Fusion — pairwise cross-atte |
| 2026-07-30 17:05:48 | [skip_design](20260730-170548_skip_design.md) | Tick #222: Queue depth 3/2 OK (≥3=2可用卡+1, M42-WCA/M4 | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-07-30 21:05:51 | [bugfix](20260730-210551_bugfix.md) | GPU0 上发现 M40-SWI 双进程 (pid 1799178/1849933) 争� | kill pid 1799178 (旧进程, 14:03 启动), 保留 pid 18499 |
| 2026-07-31 04:04:33 | [skip_design](20260731-040433_skip_design.md) | Queue depth 3≥3 (2可用卡+1), M40-SWI(ep5, 0.4134↑早� | 跳过自主设计. 队列深度达标(3≥3=可用卡2+1),  |
| 2026-07-31 05:04:30 | [skip_design](20260731-050430_skip_design.md) | Queue depth 3≥3 (2可用卡+1, M42-WCA/M43-CLN/M44-CSF wai | 跳过自主设计。仅监控+生成 tick 报告。  |
| 2026-07-31 06:04:17 | [skip_design](20260731-060417_skip_design.md) | Queue depth 3≥3 (2可用卡+1, M42-WCA/M43-CLN/M44-CSF wai | 跳过自主设计。仅监控+生成 tick 报告(#222)。  |
| 2026-07-31 07:05:25 | [skip_design](20260731-070525_skip_design.md) | Tick#223: M40-SWI(gpu0 ep5 Best=0.4134) + M41-CTF(gpu1 ep16  | 跳过自主设计。仅监控+生成 tick 报告#223。  |
| 2026-07-31 09:05:13 | [skip_design](20260731-090513_skip_design.md) | Queue depth 3≥3 (2可用卡+1). Phase 0.5 双源检查通� | 跳过自主实验设计。仅监控+生成 tick 报告#225� |
| 2026-07-31 10:05:23 | [skip_design](20260731-100523_skip_design.md) | Queue depth 3≥3 (2可用卡+1). Phase 0.5 双源检查通� | 跳过自主实验设计。仅监控+生成 tick 报告#226� |
| 2026-07-31 11:05:39 | [skip_design](20260731-110539_skip_design.md) | 队列深度 3≥3 OK (2可用卡+1), M40-SWI+M41-CTF runnin | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-07-31 12:04:13 | [skip_design](20260731-120413_skip_design.md) | 队列深度 3≥3 OK (2可用卡+1), M40-SWI+M41-CTF runnin | 跳过自主实验设计。仅监控+生成 tick 报告#228� |
| 2026-07-31 13:06:12 | [skip_design](20260731-130612_skip_design.md) | 队列深度 3≥3 OK (2可用卡+1), M40-SWI(ep7,0.4442)+M4 | 跳过自主实验设计。仅监控+生成 tick 报告#229� |
| 2026-07-31 14:05:11 | [skip_design](20260731-140511_skip_design.md) | 队列深度 3≥3 OK (2可用卡+1), M40-SWI(ep9,0.4681↑� | 跳过自主实验设计。仅监控+生成 tick 报告#230� |
| 2026-07-31 15:04:59 | [skip_design](20260731-150459_skip_design.md) | 队列深度3≥3达标(2可用卡+1=3), M40-SWI(ep10,0.4789 | 跳过自主实验设计, 仅监控双卡运行。M42-WCA/M4 |
| 2026-07-31 16:06:05 | [skip_design](20260731-160605_skip_design.md) | 队列深度 3≥3 OK (2可用卡+1), M40-SWI(ep12,0.4831↑ | 跳过自主实验设计。队列深度达标, 无新触发� |
| 2026-07-31 19:05:26 | [skip_design](20260731-190526_skip_design.md) | 队列深度 3≥3 OK (2可用卡+1), M40-SWI(ep16,0.4970↑ | 跳过自主实验设计。队列深度达标(3≥3=可用� |
| 2026-07-31 20:04:33 | [skip_design](20260731-200433_skip_design.md) | 队列深度达标(waiting=3 ≥ 可用卡2+1=3)，M40-SWI(e | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-07-31 21:09:19 | [terminal](20260731-210919_terminal.md) | M41-CTF (Cluster Token FFN) process disappeared from GPU1, d | M41-CTF → done_earlystop (0.4995). Generated pipeline/anal |
| 2026-07-31 21:09:27 | [bugfix](20260731-210927_bugfix.md) | GPU0 has 7 SWI processes: 1 active (pid 1849933, 19.6GB GPU  | Killed 6 zombie processes. Active pid 1849933 preserved (run |
| 2026-07-31 21:11:46 | [terminal](20260731-211146_terminal.md) | M40-SWI (Sigmoid-Weighted Injection) process silently died d | M40-SWI → stopped_unknown (0.4970). Generated pipeline/ana |
| 2026-07-31 21:15:39 | [queue_push](20260731-211539_queue_push.md) | GPU0 idle after SWI crash, GPU1 occupied by other user (lyb/ | Pushed M42-WCA (Weighted Cluster Aggregation) to server-4 GP |
| 2026-07-31 21:16:53 | [skip_design](20260731-211653_skip_design.md) | Queue depth 2<3 (2GPU+1=3 threshold). M42-WCA just launched  | Skip autonomous design this tick. Practical capacity = 1 GPU |
| 2026-07-31 22:13:58 | [next_batch](20260731-221358_next_batch.md) | Queue depth 2<3 (2GPU+1=3). Champion 0.5012, gap +0.0088. CT | Designed M45-NCR: Neighborhood Cluster Readback — top-K (K |
| 2026-07-31 22:14:07 | [queue_push](20260731-221407_queue_push.md) | M45-NCR enqueue decision: add to server-4 queue at tail  | Enqueued M45-NCR to server-4 queue tail (position 3). Config |
| 2026-07-31 23:05:35 | [skip_design](20260731-230535_skip_design.md) | Tick #237: Queue depth 3≥3 OK (≥可用卡2+1). M42-WCA r | 跳过自主实验设计。队列深度达标(3≥3=可用� |
| 2026-08-01 01:03:55 | [queue_update](20260801-010355_queue_update.md) | M43-CLN status sync: queue.json shows waiting but pipeline_m | Update queue.json: M43-CLN status waiting→running  |
| 2026-08-01 01:11:30 | [next_batch](20260801-011130_next_batch.md) | Queue depth insufficient (waiting=2 < 可用卡2+1=3). Champ | Design M46-SHC: Split-Head Cluster readback — split point  |
| 2026-08-01 02:06:25 | [skip_design](20260801-020625_skip_design.md) | Tick #240: 队列深度 3≥3 OK (2可用卡+1=3). M42-WCA(e | 跳过自主实验设计。队列深度达标, 仅监控+生 |
| 2026-08-01 04:06:16 | [skip_design](20260801-040616_skip_design.md) | Tick #242: 队列深度 3≥3 OK (2可用卡+1=3). M42-WCA(G | 跳过自主实验设计。队列深度达标(3≥3=可用� |
| 2026-08-01 05:04:53 | [skip_design](20260801-050453_skip_design.md) | Tick #243: Queue depth 3≥3 OK (2可用卡+1=3). M42-WCA(GP | 跳过自主实验设计。队列深度达标(3≥3=可用� |
| 2026-08-01 06:04:58 | [skip_design](20260801-060458_skip_design.md) | Tick #244: Queue depth 3≥3 OK (2可用卡+1=3). M42-WCA(GP | 跳过自主实验设计。队列深度达标(3≥3=可用� |
| 2026-08-01 10:16:32 | [queue_push](20260801-101632_queue_push.md) | server-4 gpu0 空闲，推送哪个排队实验？ | 尝试启动 [M44 Cross-Scale Fusion: pairwise cross-attention betwe |
| 2026-08-01 11:03:43 | [queue_push](20260801-110343_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M45 Neighborhood Cluster Readback: soft cluster assignme |
| 2026-08-01 11:17:49 | [next_batch](20260801-111749_next_batch.md) | Queue depth insufficient: waiting=2 < 3=2卡+1. Champion=0.5 | Design M47-FILM: FiLM-conditioned cluster readback. Replaces |
| 2026-08-01 12:05:40 | [skip_design](20260801-120540_skip_design.md) | Queue depth sufficient (waiting=3 ≥ 3=2可用卡+1). M43-C | 跳过自主实验设计。仅监控双卡运行, 不补队� |
| 2026-08-01 15:05:40 | [skip_design](20260801-150540_skip_design.md) | Tick #250: Queue depth 3/2 OK (≥3=2可用卡+1, M44-CSF/M4 | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-08-01 16:06:04 | [skip_design](20260801-160604_skip_design.md) | Tick #251: Queue depth 3/2 OK (≥3=2可用卡+1, M44-CSF/M4 | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-08-01 17:03:46 | [_gpu_query](20260801-170346__gpu_query.md) | tick GPU utilization query  | query  |
| 2026-08-01 17:05:14 | [skip_design](20260801-170514_skip_design.md) | Tick #252: Queue depth 3/3 OK (≥3=2可用卡+1). Both GPUs | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-08-01 21:04:07 | [skip_design](20260801-210407_skip_design.md) | Tick #253: Queue depth 3≥3 (2可用卡+1). Both GPUs busy  | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-08-01 22:05:46 | [skip_design](20260801-220546_skip_design.md) | Tick #254: 队列深度达标(waiting=3 ≥ 2可用卡+1=3), | 跳过自主实验设计。队列深度达标(3≥3=可用� |
| 2026-08-01 23:05:22 | [skip_design](20260801-230522_skip_design.md) | Tick #255: 队列深度达标(waiting=3 ≥ 2可用卡+1=3), | 跳过自主实验设计。仅监控+生成 tick 报告。� |
| 2026-08-02 00:05:23 | [skip_design](20260802-000523_skip_design.md) | Queue depth 3≥3 (2可用卡+1). M43-CLN(GPU1 ep18, Best=0. | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-02 02:03:53 | [skip_design](20260802-020353_skip_design.md) | Queue depth 3≥3 (2可用卡+1). M43-CLN(GPU1 ep19, Best=0. | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-02 04:04:34 | [skip_design](20260802-040434_skip_design.md) | Queue depth 3≥3 (2可用卡+1). M43-CLN(GPU1 ep23 Best=0.4 | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-02 05:04:59 | [skip_design](20260802-050459_skip_design.md) | Tick #259: Queue depth 3≥3 (2可用卡+1=3). M43-CLN(GPU1  | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-02 06:03:28 | [queue_push](20260802-060328_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M44 Cross-Scale Fusion: pairwise cross-attention between |
| 2026-08-02 06:12:07 | [next_batch](20260802-061207_next_batch.md) | Queue depth insufficient (waiting=2 < 3=2 available GPUs+1). | Design M48-BIL (Bilinear Readback: feat+=gate*(W_p(feat)*W_c |
| 2026-08-02 08:03:29 | [queue_push](20260802-080329_queue_push.md) | server-4 gpu0 空闲，推送哪个排队实验？ | 尝试启动 [M46 Split-Head Cluster] configs/Quard/shc/model_base1_ |
| 2026-08-02 08:08:16 | [crash_fix](20260802-080816_crash_fix.md) | M46-SHC push failed: FileNotFoundError for configs/Quard/shc | Fix: copied configs/Quard/shc/ + framework/model/Quard_model |
| 2026-08-02 08:08:19 | [terminal](20260802-080819_terminal.md) | M43-CLN (Cluster LayerNorm): early-stopped at epoch 25, Best | M43-CLN → stopped_unknown. Generated pipeline/analyses/M43 |
| 2026-08-02 08:08:22 | [terminal](20260802-080822_terminal.md) | M45-NCR (Neighborhood Cluster Readback): early-stopped at ep | M45-NCR → stopped_unknown. Generated pipeline/analyses/M45 |
| 2026-08-02 08:08:50 | [queue_push](20260802-080850_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M46 Split-Head Cluster] configs/Quard/shc/model_base1_qu |
| 2026-08-02 10:05:10 | [skip_design](20260802-100510_skip_design.md) | Tick #263: Queue depth 3≥3 (2可用卡+1). M46-SHC(GPU0 ep | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-02 11:05:15 | [skip_design](20260802-110515_skip_design.md) | Tick #264 (2026-08-02 11:03): Queue depth 3≥3 (2可用卡+ | 跳过自主实验设计。队列深度达标(3≥3=可用� |
| 2026-08-02 12:04:06 | [recovery](20260802-120406_recovery.md) | 上次 tick (2026-08-02 12:03) 不健康: .tick_unhealthy � | 补齐 tick 报告 summary_20260802-120328.md。检查遗漏 |
| 2026-08-02 13:04:27 | [skip_design](20260802-130427_skip_design.md) | Tick #266 (2026-08-02 13:03): Queue depth 3≥3 (2 available | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-02 14:04:19 | [skip_design](20260802-140419_skip_design.md) | Tick#267: M46-SHC(ep12 B=0.4775) + M44-CSF(ep9 B=0.4700) 均 | 队列深度 3 ≥ 2+1 达标，跳过自主实验设计。� |
| 2026-08-02 15:04:24 | [skip_design](20260802-150424_skip_design.md) | Tick #268: Queue depth 3≥3 (2可用卡+1=3), M46-SHC(ep14  | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-08-02 16:05:01 | [skip_design](20260802-160501_skip_design.md) | Tick #269: Queue depth 3≥3 (2可用卡+1=3), M46-SHC(ep16  | 跳过自主实验设计。仅监控+生成 tick 报告。Qu |
| 2026-08-02 17:04:48 | [skip_design](20260802-170448_skip_design.md) | Tick #270: Queue depth 3≥3 (2可用卡+1=3), M46-SHC(ep18  | 跳过自主实验设计。队列深度达标(3≥3=可用� |
| 2026-08-02 18:04:44 | [skip_design](20260802-180444_skip_design.md) | Tick #271: Queue depth 3/2 OK (≥3=2可用卡+1). M46-SHC(e | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-02 19:04:48 | [skip_design](20260802-190448_skip_design.md) | Tick #272: Queue depth 3/2 OK (≥3=2可用卡+1). M46-SHC(e | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-02 20:04:34 | [skip_design](20260802-200434_skip_design.md) | Tick #273: Queue depth 3≥3 (2可用卡+1=3). M46-SHC(GPU0  | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-02 21:03:29 | [queue_push](20260802-210329_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M47 FiLM Readback: FiLM-conditioned cluster context inje |
| 2026-08-02 21:15:11 | [next_batch](20260802-211511_next_batch.md) | Queue depth insufficient: waiting=2 < 3=2 available GPUs+1.  | Design M50-DGC (Difference-Gated Context): dual-path readbac |
| 2026-08-02 22:06:05 | [terminal](20260802-220605_terminal.md) | M46-SHC (Split-Head Context) process vanished — Best=0.494 | M46-SHC confirmed terminal (stopped_unknown). Abandon split- |
| 2026-08-03 02:05:12 | [skip_design](20260803-020512_skip_design.md) | Tick #279 (2026-08-03 02:03): Queue depth 3≥3 OK (2 availa | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-03 03:03:58 | [skip_design](20260803-030358_skip_design.md) | Tick #280 (2026-08-03 03:03): Queue depth 3≥3 OK (2 availa | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-03 04:04:53 | [skip_design](20260803-040453_skip_design.md) | Tick #281 (2026-08-03 04:03): Queue depth 3≥3 OK (2 availa | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-03 05:03:52 | [skip_design](20260803-050352_skip_design.md) | Tick #282 (2026-08-03 05:03): Queue depth 3≥3 OK (2可用� | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-03 06:05:22 | [skip_design](20260803-060522_skip_design.md) | Tick #283 (2026-08-03 06:03): Queue depth 3≥3 (2可用卡+ | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-03 07:04:46 | [skip_design](20260803-070446_skip_design.md) | Tick #284 (2026-08-03 07:03): Queue depth 3≥3 (2可用卡+ | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-03 08:05:38 | [skip_design](20260803-080538_skip_design.md) | Tick #285 (2026-08-03 08:03): Queue depth 3≥3 (2可用卡+ | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-03 09:04:29 | [skip_design](20260803-090429_skip_design.md) | Tick #286 (2026-08-03 09:03): Queue depth 3≥3 (2可用卡+ | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-03 10:04:26 | [skip_design](20260803-100426_skip_design.md) | Tick #287 (2026-08-03 10:03): Queue depth 3≥3 OK (2 availa | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-03 10:52:57 | [queue_push](20260803-105257_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M48 Bilinear Readback: point-conditional multiplicative  |
| 2026-08-03 12:13:48 | [terminal](20260803-121348_terminal.md) | M44-CSF (0.4958@ep20) 与 M47-FILM (0.4936@ep16) 均 done_ea | 确认 M44-CSF 与 M47-FILM 终态 (done_earlystop)。逐通 |
| 2026-08-03 12:13:48 | [queue_push](20260803-121348_queue_push.md) | 11:03 tick 超时前 M44-CSF 早停释放 server-4 gpu1, M49 | 确认 M49-NLR (Nonlinear Readback) 已启动于 server-4 gp |
| 2026-08-03 12:13:48 | [next_batch](20260803-121348_next_batch.md) | 队列深度不足: waiting=1 (M50-DGC) < 3 (2可用卡+1)� | 设计并入队 M51-DCA (dual mean+max 聚合) + M52-CCR (� |
| 2026-08-03 13:03:55 | [skip_design](20260803-130355_skip_design.md) | Tick #289 (2026-08-03 13:03): Queue depth 3≥3 (2可用卡+ | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-03 14:04:03 | [skip_design](20260803-140403_skip_design.md) | Tick #290 (2026-08-03 14:03): Queue depth 3≥3 (2可用卡+ | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-03 15:03:51 | [skip_design](20260803-150351_skip_design.md) | Tick #291 (2026-08-03 15:03): Queue depth 3≥3 (2可用卡+ | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-03 16:04:14 | [skip_design](20260803-160414_skip_design.md) | Tick #292 (2026-08-03 16:03): Queue depth 3≥3 (2可用卡+ | 跳过自主实验设计。队列深度达标(3≥3=2可用� |
| 2026-08-03 17:03:58 | [skip_design](20260803-170358_skip_design.md) | Tick #293 (2026-08-03 17:03): Queue depth 3≥3 (2 available | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-03 18:05:10 | [skip_design](20260803-180510_skip_design.md) | Tick #294 (2026-08-03 18:03): 队列深度 3≥3 达标 (2� | 跳过自主实验设计. 继续监控 M48/M49; 等待 M50-D |
| 2026-08-03 19:04:28 | [skip_design](20260803-190428_skip_design.md) | Tick #295 (2026-08-03 19:03): Queue depth 3≥3 (2 available | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-03 20:04:32 | [skip_design](20260803-200432_skip_design.md) | Tick #296 (2026-08-03 20:03): Queue depth 3≥3 (2可用卡+ | 跳过自主实验设计. 继续监控双卡运行+生成 ti |
| 2026-08-03 21:04:28 | [skip_design](20260803-210428_skip_design.md) | Tick #297 (2026-08-03 21:03): Queue depth 3≥3 (2 available | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-03 22:04:26 | [skip_design](20260803-220426_skip_design.md) | Tick #298 (2026-08-03 22:03): Queue depth 3≥3 (2 available | 跳过自主实验设计. 仅监控双卡运行+生成 tick  |
| 2026-08-03 23:05:38 | [skip_design](20260803-230538_skip_design.md) | Tick #299 (2026-08-03 23:03): Queue depth 3≥3 (2 available | 跳过自主实验设计. 仅监控双卡运行+生成 tick  |
| 2026-08-04 00:04:12 | [skip_design](20260804-000412_skip_design.md) | Tick #300 (2026-08-04 00:03): Queue depth 3≥3 (2 available | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-04 01:03:58 | [skip_design](20260804-010358_skip_design.md) | Tick #301 (2026-08-04 01:03): Queue depth 3>=3 (2 available  | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-04 02:04:00 | [skip_design](20260804-020400_skip_design.md) | Tick #302 (2026-08-04 02:03): 队列深度 3>=3 (2可用卡+ | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-04 03:04:30 | [skip_design](20260804-030430_skip_design.md) | Tick #303 (2026-08-04 03:03): Queue depth 3>=3 (2 available  | 跳过自主实验设计。队列深度达标(3>=3=2可用� |
| 2026-08-04 04:03:34 | [queue_push](20260804-040334_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M50 Difference-Gated Context] configs/Quard/dgc/model_ba |
| 2026-08-04 04:03:48 | [queue_push](20260804-040348_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M51 Dual-branch Cluster Aggregation (mean+max)] configs/ |
| 2026-08-04 04:26:15 | [next_batch](20260804-042615_next_batch.md) | 队列深度不足: waiting=1 (M52-CCR) < 3 (2可用卡+1);  | 设计并入队 M53-VAC (cluster_pool_type=var, 簇token携� |
| 2026-08-04 04:26:16 | [terminal](20260804-042616_terminal.md) | M48-BIL 与 M49-NLR 进程消失 (deathwatch 1/3), 需判定 | 确认 M48-BIL (best=0.4919@ep19, early-stop ep29) 与 M49-N |
| 2026-08-04 05:03:45 | [skip_design](20260804-050345_skip_design.md) | Tick #305 (2026-08-04 05:03): Queue depth 3>=3 (2可用卡+1 | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-04 06:04:05 | [skip_design](20260804-060405_skip_design.md) | Tick #306 (2026-08-04 06:03): Queue depth 3>=3 (2可用卡+1 | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-04 07:04:05 | [skip_design](20260804-070405_skip_design.md) | Tick #307 (2026-08-04 07:03): Queue depth 3>=3 (2可用卡+1 | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-04 08:04:33 | [skip_design](20260804-080433_skip_design.md) | Tick #308 (2026-08-04 08:03): Queue depth 3>=3 (2可用卡+1 | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-04 09:04:44 | [skip_design](20260804-090444_skip_design.md) | Tick #309 (2026-08-04 09:03): Queue depth 3>=3 (2可用卡+1 | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-04 10:03:59 | [skip_design](20260804-100359_skip_design.md) | Tick #310 (2026-08-04 10:03): Queue depth 3>=3 (2可用卡+1 | 跳过自主实验设计. 仅监控双卡运行+生成 tick  |
| 2026-08-04 11:04:12 | [skip_design](20260804-110412_skip_design.md) | Tick #311 (2026-08-04 11:03): Queue depth 3>=3 (2可用卡+1 | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-04 12:04:09 | [skip_design](20260804-120409_skip_design.md) | Tick #312 (2026-08-04 12:03): Queue depth 3>=3 (2可用卡+1 | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-04 13:06:19 | [skip_design](20260804-130619_skip_design.md) | Tick #313 (2026-08-04 13:06): Queue depth 3>=3 (2可用卡+1 | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-04 14:04:27 | [skip_design](20260804-140427_skip_design.md) | Tick #314 (2026-08-04 14:03): Queue depth 3>=3 (2 available+ | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-04 15:04:37 | [skip_design](20260804-150437_skip_design.md) | Tick #315 (2026-08-04 15:03): 队列深度 3>=3 (2可用卡+ | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-04 16:05:07 | [skip_design](20260804-160507_skip_design.md) | Tick #316 (2026-08-04 16:03): 队列深度 3>=3 (2可用卡+ | 跳过自主实验设计。仅监控双卡运行+生成 tick |
| 2026-08-04 17:13:11 | [next_batch](20260804-171311_next_batch.md) | 队列深度不足: waiting=3 < 可用卡数3+1=4 (本 tick  | 设计并入队 M55-SCF (per-point 内容注意力替代静� |
| 2026-08-04 17:13:14 | [question](20260804-171314_question.md) | server-6 (H100, allowed_gpus=[3]) 本 tick 首次被 pipelin | 本轮按 SERVERS.yaml 容量计入可用卡数=3, 补设计 |
| 2026-08-04 17:34:34 | [next_batch](20260804-173434_next_batch.md) | 单卡多任务上线后可用槽=5, 需waiting≥6, 当前� | 设计5个组合变体: M56-DOT(DRP+ORT) + M57/58/59/60(X+de |
| 2026-08-04 18:03:39 | [queue_push](20260804-180339_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M56 DRP+ORT 组合 (去路由 + 正交正则)] configs/Quard/dot/model_bas |
| 2026-08-04 18:11:37 | [next_batch](20260804-181137_next_batch.md) | 队列深度不足: waiting=5 (M55/M59/M60 srv4 + M57/M58 sr | 设计并入队 M61-SCT (Sequential Coarse-then-Fine Readbac |
| 2026-08-04 18:11:41 | [other](20260804-181141_other.md) | M56-DOT 已推送运行 (18:03), 但 dot 包 dec.py 中 orth | 经读代码确认: drp_ort 模式下 forward 不调用 rese |
| 2026-08-04 18:26:24 | [queue_push](20260804-182624_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M57 ORT + detail message_type] configs/Quard/det_ort/mod |
| 2026-08-04 20:09:14 | [other](20260804-200914_other.md) | M17-ORT(0.5005)/M56-DOT/M57-DET-ORT 的 ORT 正则是否有� | 确认 ORT 梯度断流 bug 并修复: hier_postprocess 中  |
| 2026-08-04 20:09:19 | [next_batch](20260804-200919_next_batch.md) | 队列深度不足: waiting=5 < 5可用槽+1=6 (tick#319 超 | 设计并入队 M62-ORTG (DRP + 真梯度 ORT, 修复 orth � |
| 2026-08-04 20:10:14 | [question](20260804-201014_question.md) | server-6 GPU7 已满 (M52/M53/M54 = max_tasks_per_gpu=3), � | 本轮 M62-ORTG 明确排 server-4 规避; 推送逻辑修� |
| 2026-08-04 21:27:38 | [next_batch](20260804-212738_next_batch.md) | 队列深度不足: waiting=5 < 可用槽 5+1=6 (tick #321), | 设计并入队 M63-PSR (per-scale point-cluster residual re |
| 2026-08-04 22:03:57 | [queue_push](20260804-220357_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M59 QSF + detail message_type] configs/Quard/det_qsf/mod |
| 2026-08-04 22:12:09 | [next_batch](20260804-221209_next_batch.md) | 队列深度不足: waiting=5 < 可用槽 5+1=6 (tick #322)� | 设计并入队 M64-SSP (per-scale 独立投影 readback): � |
| 2026-08-05 07:04:38 | [skip_design](20260805-070438_skip_design.md) | Tick #331 (2026-08-05 07:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。继续监控 5 个 running (M55/M |
| 2026-08-05 08:05:15 | [skip_design](20260805-080515_skip_design.md) | Tick #332 (2026-08-05 08:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。仅监控+生成 tick 报告。  |
| 2026-08-05 09:04:19 | [skip_design](20260805-090419_skip_design.md) | Tick #333 (2026-08-05 09:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。仅监控 5 个 running (M55-SCF/ |
| 2026-08-05 10:05:44 | [skip_design](20260805-100544_skip_design.md) | Tick #334 (2026-08-05 10:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。仅监控 5 个 running (M55-SCF/ |
| 2026-08-05 11:05:16 | [skip_design](20260805-110516_skip_design.md) | Tick #335 (2026-08-05 11:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。仅监控 5 个 running (M55-SCF/ |
| 2026-08-05 11:26:07 | [queue_push](20260805-112607_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M60 CSF + detail message_type] configs/Quard/det_csf/mod |
| 2026-08-05 12:11:13 | [next_batch](20260805-121113_next_batch.md) | 队列深度不足: waiting=5 < 可用槽 5+1=6 (M55-SCF 终 | 设计并入队 M65-HCG (Hierarchical Composition Gather): � |
| 2026-08-05 13:04:47 | [skip_design](20260805-130447_skip_design.md) | Tick #337 (2026-08-05 13:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。继续监控 5 个 running (M59-D |
| 2026-08-05 14:04:14 | [skip_design](20260805-140414_skip_design.md) | Tick #338 (2026-08-05 14:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。仅监控+生成 tick 报告。� |
| 2026-08-05 15:04:17 | [skip_design](20260805-150417_skip_design.md) | Tick #339 (2026-08-05 15:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。仅监控 5 个 running (M59-DET- |
| 2026-08-05 16:04:28 | [skip_design](20260805-160428_skip_design.md) | Tick #340 (2026-08-05 16:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。仅监控 5 个 running (M59-DET- |
| 2026-08-05 17:03:30 | [queue_push](20260805-170330_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M61 Sequential Coarse-then-Fine Readback] configs/Quard/ |
| 2026-08-05 17:12:13 | [next_batch](20260805-171213_next_batch.md) | 队列深度不足: waiting=5 (M62/63/64/65 srv4 + M58 srv6) | 设计并入队 M66-DET-HCG (configs/Quard/det_hcg/..._det_h |
| 2026-08-05 18:05:30 | [route_change](20260805-180530_route_change.md) | M59-DET-QSF (detail message + query尺度门控) 终态 stop | 关闭 detail+QSF 组合线。M59 结果 < detail 单独 (D1 |
| 2026-08-05 19:05:46 | [skip_design](20260805-190546_skip_design.md) | Tick #343 (2026-08-05 19:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。仅监控 5 个 running (M60-DET- |
| 2026-08-05 20:05:48 | [skip_design](20260805-200548_skip_design.md) | Tick #344 (2026-08-05 20:05): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。继续监控 5 个 running (M60-D |
| 2026-08-05 21:05:42 | [skip_design](20260805-210542_skip_design.md) | Tick #345 (2026-08-05 21:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。仅监控+生成 tick 报告。  |
| 2026-08-05 22:04:39 | [skip_design](20260805-220439_skip_design.md) | Tick #346 (2026-08-05 22:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。仅监控+生成 tick 报告。� |
| 2026-08-05 23:04:41 | [skip_design](20260805-230441_skip_design.md) | Tick #347 (2026-08-05 23:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。仅监控+生成 tick 报告  |
| 2026-08-06 00:06:32 | [skip_design](20260806-000632_skip_design.md) | Tick #348 (2026-08-06 00:04): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计。仅监控+生成 tick 报告  |
| 2026-08-06 01:04:36 | [skip_design](20260806-010436_skip_design.md) | Tick #349 (2026-08-06 01:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计, 仅监控+生成 tick 报告。等 |
| 2026-08-06 02:07:00 | [skip_design](20260806-020700_skip_design.md) | Tick #350 (2026-08-06 02:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计, 仅监控+生成 tick 报告。等 |
| 2026-08-06 03:05:05 | [skip_design](20260806-030505_skip_design.md) | Tick #351 (2026-08-06 03:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计, 仅监控+生成 tick 报告。等 |
| 2026-08-06 04:06:59 | [skip_design](20260806-040659_skip_design.md) | Tick #352 (2026-08-06 04:03): 队列深度 6>=6 (5 可用槽 | 跳过自主实验设计, 仅监控+生成 tick 报告。等 |
| 2026-08-06 05:05:02 | [skip_design](20260806-050502_skip_design.md) | 队列深度 6 waiting ≥ 可用槽 5+1=6 达标; 5 个 run | 跳过自主设计。继续监控 5 个 running (M60-DET-CSF |
| 2026-08-06 06:06:52 | [skip_design](20260806-060652_skip_design.md) | Tick #354 (2026-08-06 06:03): 队列深度 6 waiting ≥ 5 � | 跳过自主设计。仅监控+生成 tick 报告。等待 M |
| 2026-08-06 07:03:21 | [queue_push](20260806-070321_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M62 DRP + 真梯度 ORT (修复 orth 梯度断流后重测 token 多样性)] configs/Q |
| 2026-08-06 07:09:40 | [route_change](20260806-070940_route_change.md) | M60-DET-CSF (detail+CSF) 终态 early-stopped ep25 best=0.49 | 归档 M60 终态分析 (pipeline/analyses/M60-DET-CSF_done_ |
| 2026-08-06 07:09:44 | [next_batch](20260806-070944_next_batch.md) | M60 终态后队列深度 waiting=5 < 可用槽 5+1=6, 下� | 设计并入队 M67-PSR-HCG (configs/Quard/psr_hcg/..._psr_h |
| 2026-08-06 08:05:22 | [skip_design](20260806-080522_skip_design.md) | Tick #356 (2026-08-06 08:03): 队列深度 6 waiting ≥ 可 | 跳过自主实验设计, 仅监控+生成 tick 报告。继 |
| 2026-08-06 09:04:30 | [skip_design](20260806-090430_skip_design.md) | Tick #357 (2026-08-06 09:03): 队列深度 6 waiting ≥ 可 | 跳过自主实验设计, 仅监控+生成 tick 报告。等 |
| 2026-08-06 10:04:54 | [skip_design](20260806-100454_skip_design.md) | Tick #358 (2026-08-06 10:03): 队列深度 6 waiting ≥ 5 � | 跳过自主实验设计。仅监控+生成 tick 报告。M6 |
| 2026-08-06 11:03:23 | [queue_push](20260806-110323_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M63 per-scale point-cluster residual readback (message 构 |
| 2026-08-06 11:12:00 | [next_batch](20260806-111200_next_batch.md) | M61-SCT 终态 (0.4854 < baseline) 后队列深度 waiting=5 | 设计并入队 M68-SSP-HCG (configs/Quard/ssp_hcg/..._ssp_h |
| 2026-08-06 12:05:05 | [skip_design](20260806-120505_skip_design.md) | Tick #360 (2026-08-06 12:03): 队列深度 6 waiting ≥ 可 | 跳过自主实验设计。仅监控+生成 tick 报告。  |
| 2026-08-06 13:04:12 | [skip_design](20260806-130412_skip_design.md) | Tick #361 (2026-08-06 13:03): 队列深度 6 waiting ≥ 可 | 跳过自主实验设计。仅监控+生成 tick 报告。  |
| 2026-08-06 14:05:05 | [skip_design](20260806-140505_skip_design.md) | Tick #362 (2026-08-06 14:03): 队列深度 6 waiting 是否� | 跳过自主实验设计。仅监控+生成 tick 报告。5  |
| 2026-08-06 15:04:33 | [skip_design](20260806-150433_skip_design.md) | Tick #363 (2026-08-06 15:03): 队列深度 6 waiting ≥ 可 | 跳过自主实验设计, 仅监控+生成 tick 报告。5 r |
| 2026-08-06 16:05:44 | [skip_design](20260806-160544_skip_design.md) | Tick #364 (2026-08-06 16:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计, 仅监控+生成 tick 报告。继续观 |
| 2026-08-06 17:05:00 | [skip_design](20260806-170500_skip_design.md) | Tick #365 (2026-08-06 17:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计, 仅监控+生成 tick 报告 summary_202 |
| 2026-08-06 18:05:08 | [skip_design](20260806-180508_skip_design.md) | Tick #366 (2026-08-06 18:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计, 仅监控+生成 tick 报告 summary_202 |
| 2026-08-06 19:15:01 | [question](20260806-191501_question.md) | server-4 被外部 fineweb-edu preprocess 任务挤爆: load | 不 kill 不重启(外部负载下重启仍会停, 且 swap  |
| 2026-08-06 19:15:05 | [skip_design](20260806-191505_skip_design.md) | Tick #367 (2026-08-06 19:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计, 仅监控+生成 tick 报告; server-4 � |
| 2026-08-06 20:17:19 | [other](20260806-201719_other.md) | server-4 外部负载已消退(load 218→1.2, 内存172GB� | kill 停滞的 M62-ORTG(3239622)/M63-PSR(291660) 全进程� |
| 2026-08-06 21:05:55 | [skip_design](20260806-210555_skip_design.md) | Tick #369 (2026-08-06 21:03): 队列深度 6 waiting ≥ 可 | 跳过自主实验设计, 仅监控+生成 tick 报告; 继� |
| 2026-08-06 22:06:45 | [skip_design](20260806-220645_skip_design.md) | Tick #370 (2026-08-06 22:03): 队列深度 6 waiting ≥ 可 | 跳过自主实验设计, 仅监控+生成 tick 报告; 重� |
| 2026-08-06 22:22:15 | [next_batch](20260806-222215_next_batch.md) | 20+变体在0.49-0.50平台未超champion(0.5012), 单次rea | 设计M69-ITER(同层2轮回写门控融合) + M70-REAGG(迭 |
| 2026-08-06 23:05:52 | [skip_design](20260806-230552_skip_design.md) | Tick #371 (2026-08-06 23:03): 队列深度 8 waiting ≥ 可 | 跳过自主实验设计。仅监控+生成 tick 报告 summ |
| 2026-08-07 00:03:23 | [queue_push](20260807-000323_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M64 per-scale projection readback (投影放置轴补格)] configs/Qua |
| 2026-08-07 00:07:17 | [other](20260807-000717_other.md) | M62-ORTG 进程消失 (deathwatch 1/3), 是 crash 还是正� | 确认为正常 early-stop 终态: Early stopping at epoch 2 |
| 2026-08-07 00:07:19 | [skip_design](20260807-000719_skip_design.md) | Tick #372 (2026-08-07 00:03): 队列深度 7 waiting ≥ 可 | 跳过自主实验设计, 仅监控+生成 tick 报告. 本  |
| 2026-08-07 01:05:14 | [skip_design](20260807-010514_skip_design.md) | Tick #373 (2026-08-07 01:03): 队列深度 7 waiting ≥ 可 | 跳过自主实验设计, 仅监控+生成 tick 报告. 队� |
| 2026-08-07 02:05:34 | [skip_design](20260807-020534_skip_design.md) | Tick #374 (2026-08-07 02:03): 队列深度 7 waiting ≥ 5 � | 跳过自主实验设计, 仅监控+生成 tick 报告. 5/5  |
| 2026-08-07 03:05:46 | [skip_design](20260807-030546_skip_design.md) | Tick #375 (2026-08-07 03:03): 队列深度 7 waiting ≥ 5 � | 跳过自主实验设计, 仅监控+生成 tick 报告. 队� |
| 2026-08-07 04:06:33 | [skip_design](20260807-040633_skip_design.md) | Tick #376 (2026-08-07 04:03): 队列深度 7 waiting ≥ 5 � | 跳过自主设计。仅监控+生成 tick 报告 summary_20 |
| 2026-08-07 05:04:39 | [skip_design](20260807-050439_skip_design.md) | Tick #377 (2026-08-07 05:03): 队列深度 7 waiting ≥ 5 � | 跳过自主设计。仅监控+生成 tick 报告 summary_20 |
| 2026-08-07 06:06:17 | [skip_design](20260807-060617_skip_design.md) | Tick #378 (2026-08-07 06:03): 队列深度 7 waiting ≥ 5 � | 跳过自主设计。仅监控+生成 tick 报告 summary_20 |
| 2026-08-07 07:03:23 | [queue_push](20260807-070323_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M65 Hierarchical Composition Gather (逐级组合点→簇映射, 修复粗尺度 re |
| 2026-08-07 07:06:07 | [early_stop](20260807-070607_early_stop.md) | M63-PSR 日志判定终态: Early stopping at epoch 24 (best | 标记 M63-PSR → done_earlystop, 写入终态分析 pipeli |
| 2026-08-07 07:07:34 | [skip_design](20260807-070734_skip_design.md) | 队列深度 6 waiting ≥ 可用槽 5+1=6 达标, 是否自 | 跳过自主设计. 继续监控 M64-SSP/M65-HCG (server-4)  |
| 2026-08-07 08:07:11 | [skip_design](20260807-080711_skip_design.md) | 队列深度 6 waiting ≥ 可用槽 5+1=6 达标, 是否自 | 跳过自主设计. 继续监控 M64-SSP/M65-HCG (server-4)  |
| 2026-08-07 09:05:41 | [skip_design](20260807-090541_skip_design.md) | 队列深度 6 waiting ≥ 可用槽 5+1=6 达标, 是否自 | 跳过自主设计. 继续监控 M64-SSP/M65-HCG (server-4), |
| 2026-08-07 10:07:57 | [skip_design](20260807-100757_skip_design.md) | 队列深度 6 waiting ≥ 可用槽 5+1=6 达标, 是否自 | 跳过自主设计. 继续监控 M64-SSP/M65-HCG (server-4), |
| 2026-08-07 11:05:27 | [skip_design](20260807-110527_skip_design.md) | Tick #383 (2026-08-07 11:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 继续监控 M64-SSP/M65-HCG (server-4), |
| 2026-08-07 12:04:48 | [skip_design](20260807-120448_skip_design.md) | 队列深度 6 waiting ≥ 可用槽 5+1=6 达标, 是否自 | 跳过自主设计. 继续监控 M64-SSP/M65-HCG (server-4), |
| 2026-08-07 13:05:41 | [skip_design](20260807-130541_skip_design.md) | Tick #385 (2026-08-07 13:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 继续监控 M64-SSP/M65-HCG (server-4), |
| 2026-08-07 14:06:13 | [skip_design](20260807-140613_skip_design.md) | 队列深度 6 waiting ≥ 可用槽 5+1=6, 是否触发自� | 跳过自主设计, 继续监控 5 个 running 实验 (M64-S |
| 2026-08-07 15:06:00 | [skip_design](20260807-150600_skip_design.md) | 队列深度 6 waiting vs 5 可用槽(server-4:2+server-6 GP | 跳过自主设计, 继续监控 5 运行实验 (M64-SSP/M65 |
| 2026-08-07 16:07:08 | [early_stop](20260807-160708_early_stop.md) | M64-SSP 进程消失 (deathwatch 1/3) — crash 还是正常 | 确认为正常 early-stop 终态: 标记 M64-SSP → done_e |
| 2026-08-07 16:07:09 | [queue_push](20260807-160709_queue_push.md) | M64-SSP 终态后 server-4 gpu0 空闲 (util 0% 且显存 94 | 启动 [M66 HCG + detail message (正确多尺度交付 × � |
| 2026-08-07 16:14:55 | [next_batch](20260807-161455_next_batch.md) | 队列深度 5 waiting < 可用槽 5+1=6 (M64-SSP 终态 + M | 设计 M71-CCP (coarse-to-fine cluster context propagation,  |
| 2026-08-07 17:03:31 | [queue_push](20260807-170331_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M58 DRP + detail message_type] configs/Quard/det_drp/mod |
| 2026-08-07 17:05:16 | [early_stop](20260807-170516_early_stop.md) | M54-SAC 进程消失 (deathwatch 1/3) — crash 还是正常 | 确认为正常早停终态: 标记 M54-SAC → done_earlyst |
| 2026-08-07 17:08:46 | [skip_design](20260807-170846_skip_design.md) | 队列深度 6 waiting ≥ 可用槽 5+1=6 达标, 是否触 | 跳过自主设计, 继续监控 5 个 running 实验 (M65-H |
| 2026-08-07 18:11:49 | [other](20260807-181149_other.md) | server-6 队列空 (0 waiting) 而 server-4 队列 6 waiting | 将 M67-PSR-HCG + M68-SSP-HCG 从 server-4 队首移至 serv |
| 2026-08-07 18:11:51 | [skip_design](20260807-181151_skip_design.md) | 队列深度 6 waiting ≥ 可用槽 5+1=6 达标, 是否触 | 跳过自主设计. 仅监控 5 个 running (M65-HCG 17/50 0 |
| 2026-08-07 19:07:33 | [skip_design](20260807-190733_skip_design.md) | Tick #391 (2026-08-07 19:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 继续监控 5 个 running 实验 (M65-H |
| 2026-08-07 20:07:17 | [skip_design](20260807-200717_skip_design.md) | 队列深度 6 waiting ≥ 5+1=6 达标，是否进行自主 | 跳过自主设计。本 tick 仅监控: M65-HCG 0.4982@ep20 |
| 2026-08-07 20:26:22 | [queue_push](20260807-202622_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M67 PSR+HCG (正确多尺度交付 × 逐尺度残差 message, 3×2 补格)] configs/Q |
| 2026-08-07 21:19:44 | [next_batch](20260807-211944_next_batch.md) | 队列深度 5 waiting < 可用槽 5+1=6 (M67-PSR-HCG 20:26  | 设计 M73-CCP-DET (cluster_mode ccp + cluster_message_type  |
| 2026-08-07 22:09:54 | [queue_push](20260807-220954_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M68 per-scale projection × 正确多尺度交付 (2×2 投影放置补格)] configs |
| 2026-08-07 22:10:45 | [other](20260807-221045_other.md) | M53-VAC 进程消失 deathwatch 3/3 确认, 远端日志拉� | 判定 M53-VAC → stopped_unknown (best 0.4889@ep28), 不� |
| 2026-08-07 22:10:45 | [queue_push](20260807-221045_queue_push.md) | M53-VAC 终态后 server-6 gpu7 释放 1 槽 (capacity 3), � | 推送 [M68 per-scale projection × 正确多尺度交付 (2 |
| 2026-08-07 22:10:45 | [skip_design](20260807-221045_skip_design.md) | 队列深度 6 waiting ≥ 可用槽 5+1=6 达标 (M68 推� | 跳过自主设计. 继续监控 M65-HCG(0.5002@ep23 距 cha |
| 2026-08-07 23:05:14 | [other](20260807-230514_other.md) | M52-CCR 进程消失 deathwatch 3/3 确认, 远端日志拉� | 判定 M52-CCR → stopped_unknown (best 0.4948@ep29), 不� |
| 2026-08-07 23:06:12 | [skip_design](20260807-230612_skip_design.md) | 队列深度 6 waiting ≥ 可用槽 5+1=6 达标 (M52-CCR � | 跳过自主设计. 继续监控 M65-HCG(0.5002@ep24 距 cha |
| 2026-08-08 00:03:59 | [skip_design](20260808-000359_skip_design.md) | 队列深度 6 waiting ≥ 可用槽 5+1=6 达标, 是否触 | 跳过自主设计. 继续监控 M65-HCG(0.5002@ep26 no_impr |
| 2026-08-08 01:06:18 | [skip_design](20260808-010618_skip_design.md) | 队列深度 6 waiting ≥ 可用槽 5+1=6 达标, 是否触 | 跳过自主设计. 继续监控 M65-HCG(0.5002@ep27 no_impr |
| 2026-08-08 02:05:23 | [skip_design](20260808-020523_skip_design.md) | Tick #398 (2026-08-08 02:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 仅监控 5 个 running 实验 + 生成  |
| 2026-08-08 03:05:59 | [skip_design](20260808-030559_skip_design.md) | Tick #399 (2026-08-08 03:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 继续监控 5 个 running 实验 (M65-H |
| 2026-08-08 04:03:21 | [queue_push](20260808-040321_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M69 迭代 readback (2轮回写门控融合)] configs/Quard/iter/model_bas |
| 2026-08-08 04:17:24 | [next_batch](20260808-041724_next_batch.md) | M65-HCG 终态 0.5002≈champion 闭合交付轴后, 队列� | 设计 M75-DET-ITER (iter×detail) + M76-DET-REAGG (reag×de |
| 2026-08-08 05:04:50 | [skip_design](20260808-050450_skip_design.md) | 队列深度 7 waiting ≥ 可用槽 5+1=6 达标, 是否触 | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-08 06:05:48 | [skip_design](20260808-060548_skip_design.md) | Tick #402 (2026-08-08 06:03): 队列深度 7 waiting ≥ 可 | 跳过自主设计. 继续监控 5 个 running 实验 (M66-D |
| 2026-08-08 07:04:50 | [skip_design](20260808-070450_skip_design.md) | Tick #403 (2026-08-08 07:03): 队列深度 7 waiting ≥ 可 | 跳过自主设计. 继续监控 5 个 running 实验 (M66-D |
| 2026-08-08 08:06:19 | [skip_design](20260808-080619_skip_design.md) | Queue depth 7/5 OK (≥6), 5 running 全部存活推进 (M66 | 跳过自主设计。继续监控 5 running, 等 M66-DET-HCG |
| 2026-08-08 08:21:19 | [queue_push](20260808-082119_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M70 迭代+重新聚合 cluster token] configs/Quard/reag/model_base |
| 2026-08-08 08:26:08 | [queue_push](20260808-082608_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M71 Coarse-to-Fine cluster context propagation (粗簇全局上下文逐 |
| 2026-08-08 09:07:32 | [queue_push](20260808-090732_queue_push.md) | M70-REAGG 08:21 推送后 crash (ImportError: C2F_ClusterAtt | 修复类名 REAGG→REAG (reag + det_reag 两包), 已 sync |
| 2026-08-08 09:08:28 | [early_stop](20260808-090828_early_stop.md) | M66-DET-HCG 进程消失 ×3 确认终态 (deathwatch), best | 标记 M66-DET-HCG → stopped_unknown, 生成终态分析 M |
| 2026-08-08 09:08:28 | [skip_design](20260808-090828_skip_design.md) | 队列深度 6 waiting ≥ 可用槽 5+1=6 (M70-REAGG 修复 | 跳过自主设计. 继续监控 5 running (M69-ITER/M71-CCP |
| 2026-08-08 10:05:21 | [skip_design](20260808-100521_skip_design.md) | tick#406 队列深度: 6 waiting (M70-REAGG/M72-CCP-HCG/M73- | 跳过自主设计, 本 tick 仅监控; 队列深度 6 ≥ 5 |
| 2026-08-08 11:06:39 | [skip_design](20260808-110639_skip_design.md) | Tick #407 (2026-08-08 11:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控: M69-ITER 0.4889@11 � |
| 2026-08-08 12:05:13 | [skip_design](20260808-120513_skip_design.md) | Tick #408 (2026-08-08 12:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控 5 个 running 实验  |
| 2026-08-08 13:05:15 | [skip_design](20260808-130515_skip_design.md) | Tick #409 (2026-08-08 13:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控 5 个 running 实验  |
| 2026-08-08 14:06:46 | [skip_design](20260808-140646_skip_design.md) | Tick #410 (2026-08-08 14:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控 5 个 running 实验  |
| 2026-08-08 15:04:42 | [skip_design](20260808-150442_skip_design.md) | Tick #411 (2026-08-08 15:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控 5 个 running 实验  |
| 2026-08-08 16:05:09 | [skip_design](20260808-160509_skip_design.md) | Tick #412 (2026-08-08 16:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控 5 个 running 实验  |
| 2026-08-08 17:05:41 | [skip_design](20260808-170541_skip_design.md) | Tick #413 (2026-08-08 17:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-08 18:04:40 | [skip_design](20260808-180440_skip_design.md) | Tick #414 (2026-08-08 18:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-08 19:06:10 | [skip_design](20260808-190610_skip_design.md) | Tick #415 (2026-08-08 19:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-08 20:05:32 | [skip_design](20260808-200532_skip_design.md) | Tick #416 (2026-08-08 20:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-08 21:05:36 | [skip_design](20260808-210536_skip_design.md) | Tick #417 (2026-08-08 21:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-08 22:05:17 | [skip_design](20260808-220517_skip_design.md) | Tick #418 (2026-08-08 22:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-08 23:05:39 | [skip_design](20260808-230539_skip_design.md) | Tick #419 (2026-08-08 23:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-09 00:03:21 | [queue_push](20260809-000321_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M70 迭代+重新聚合 cluster token] configs/Quard/reag/model_base |
| 2026-08-09 00:10:42 | [early_stop](20260809-001042_early_stop.md) | M69-ITER 进程消失 (deathwatch 1/3), 远端日志确认� | 标记 M69-ITER → done_earlystop, 生成终态分析 M69-I |
| 2026-08-09 00:14:33 | [next_batch](20260809-001433_next_batch.md) | 队列深度 5 waiting < 可用槽 5+1=6 (M69-ITER 终态 +  | 设计 M77-ITER-HCG + M78-REAGG-HCG ({迭代}×{交付 HCG}  |
| 2026-08-09 01:03:25 | [queue_push](20260809-010325_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M72 CCP × HCG 正确交付 (token质量×交付 2×2 补格)] configs/Quard/cc |
| 2026-08-09 01:05:19 | [early_stop](20260809-010519_early_stop.md) | M71-CCP 进程 PID=1222849 DEAD (死亡检查发现), 判定 | 标记 M71-CCP → done_earlystop, best=0.4934@ep28, 生成� |
| 2026-08-09 03:04:23 | [skip_design](20260809-030423_skip_design.md) | Tick #423 (2026-08-09 03:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-09 04:04:05 | [skip_design](20260809-040405_skip_design.md) | Tick #424 (2026-08-09 04:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-09 05:06:56 | [skip_design](20260809-050656_skip_design.md) | Tick #425 (2026-08-09 05:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-09 06:04:45 | [skip_design](20260809-060445_skip_design.md) | Tick #426 (2026-08-09 06:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-09 07:05:07 | [skip_design](20260809-070507_skip_design.md) | Tick #427 (2026-08-09 07:03): 队列深度 6 waiting ≥ 可 | 跳过自主设计. 本 tick 仅监控 5 个 running 实验  |
| 2026-08-09 08:04:19 | [skip_design](20260809-080419_skip_design.md) | 队列深度判定: waiting=6 (M73-M78 on server-4), 可用� | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-09 09:05:19 | [skip_design](20260809-090519_skip_design.md) | 队列深度判定: waiting=6 (M73-M78 on server-4), 可用� | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-09 10:04:44 | [skip_design](20260809-100444_skip_design.md) | 队列深度判定: waiting=6 (M73-M78 on server-4), 可用� | 跳过自主设计, 本 tick 仅监控  |
| 2026-08-09 11:07:10 | [skip_design](20260809-110710_skip_design.md) | Tick #431 (2026-08-09 11:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-09 12:12:05 | [skip_design](20260809-121205_skip_design.md) | Tick #432 (2026-08-09 12:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控; 附 server-6 时区� |
| 2026-08-09 13:04:43 | [skip_design](20260809-130443_skip_design.md) | Tick #433 (2026-08-09 13:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控; 记录 M70-REAGG ep1 |
| 2026-08-09 14:05:30 | [skip_design](20260809-140530_skip_design.md) | Tick #434 (2026-08-09 14:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控; 记录 M70-REAGG ep1 |
| 2026-08-09 15:04:36 | [skip_design](20260809-150436_skip_design.md) | Tick #435 (2026-08-09 15:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-09 16:03:56 | [skip_design](20260809-160356_skip_design.md) | Tick #436 (2026-08-09 16:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-09 17:03:21 | [queue_push](20260809-170321_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M73 CCP × detail message (token质量×message构造 2×2 补格)] con |
| 2026-08-09 17:12:34 | [early_stop](20260809-171234_early_stop.md) | M72-CCP-HCG 进程消失 (deathwatch 1/3), 远端日志确� | 标记 M72-CCP-HCG → done_earlystop, best=0.4950@ep27 (log |
| 2026-08-09 17:12:36 | [next_batch](20260809-171236_next_batch.md) | 队列深度 5 waiting < 可用槽 5+1=6 (M72-CCP-HCG 终态 | 设计 M79-REAG-CASC (REAGG + 级联正确重聚合, 修复  |
| 2026-08-09 18:04:48 | [skip_design](20260809-180448_skip_design.md) | Tick #438 (2026-08-09 18:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-09 19:04:31 | [skip_design](20260809-190431_skip_design.md) | tick #439 (2026-08-09 19:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-09 20:03:22 | [queue_push](20260809-200322_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M74 CCP × HCG × detail 三维满格 (源质量×正确交付×残差 message)] confi |
| 2026-08-09 20:18:54 | [early_stop](20260809-201854_early_stop.md) | M70-REAGG 进程消失 (deathwatch 1/3), 远端日志确认  | 标记 M70-REAGG → done_earlystop, best=0.4983@ep28, 生� |
| 2026-08-09 20:18:58 | [next_batch](20260809-201858_next_batch.md) | 队列深度 5 waiting < 可用槽 5+1=6 (M70-REAGG 终态 + | 设计 M80-REAG-CASC-HCG (REAGG + 级联正确重聚合 × H |
| 2026-08-09 21:04:24 | [skip_design](20260809-210424_skip_design.md) | tick #441 (2026-08-09 21:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控 (5 running: M73-CCP-D |
| 2026-08-09 22:04:44 | [skip_design](20260809-220444_skip_design.md) | tick #442 (2026-08-09 22:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-09 23:04:44 | [skip_design](20260809-230444_skip_design.md) | tick #443 (2026-08-09 23:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-10 00:04:57 | [skip_design](20260810-000457_skip_design.md) | Tick #444 (2026-08-10 00:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-10 01:04:39 | [skip_design](20260810-010439_skip_design.md) | Tick #445 (2026-08-10 01:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-10 02:05:43 | [skip_design](20260810-020543_skip_design.md) | Tick #446 (2026-08-10 02:03): 队列深度判定 waiting=6 � | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-10 04:05:37 | [skip_design](20260810-040537_skip_design.md) | Tick #448 (2026-08-10 04:03): 队列深度判定 waiting=6 � | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-10 05:08:20 | [skip_design](20260810-050820_skip_design.md) | Tick #449 (2026-08-10 05:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-10 06:06:01 | [skip_design](20260810-060601_skip_design.md) | Tick #450 (2026-08-10 06:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-10 07:05:26 | [skip_design](20260810-070526_skip_design.md) | tick #451 (2026-08-10 07:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控 (5 running: M73-CCP-D |
| 2026-08-10 08:05:04 | [skip_design](20260810-080504_skip_design.md) | Tick #452 (2026-08-10 08:03): 队列深度判定 waiting=6 ( | 跳过自主设计, 本 tick 仅监控 (5 running: M73-CCP-D |
| 2026-08-10 10:00:17 | [queue_push](20260810-100017_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M78 reag × HCG 正确多尺度交付 (cluster 进化 × 正确交付)] configs/Quar |
| 2026-08-10 10:08:17 | [early_stop](20260810-100817_early_stop.md) | M73-CCP-DET 进程消失 (deathwatch 2/3), 队列仍标 runn | 标记 done_earlystop best=0.4952@ep27 (日志确认: Early  |
| 2026-08-10 10:10:02 | [next_batch](20260810-101002_next_batch.md) | 队列深度 waiting=2 < 可用槽5+1=6 (M73 早停释放槽 | 实现 M81-CTF-HCG/M82-DET-CTF/M83-DET-REAG-CASC/M84-DET-CTF |
| 2026-08-10 10:11:01 | [next_batch](20260810-101101_next_batch.md) | 23变体穷尽readback/message轴, 未探索loss侧cluster� | 设计M81-CONS(intra-cluster一致性,loss侧) + M84-DET-CON |
| 2026-08-10 10:37:10 | [next_batch](20260810-103710_next_batch.md) | 23变体在'单层只更新inst_feats'约束内穷尽(全≤ | 解除goal.json约束(用户定向), 设计M85-QMOD(query调 |
| 2026-08-10 11:04:44 | [skip_design](20260810-110444_skip_design.md) | Tick #454 (2026-08-10 11:03): 队列深度 waiting=10 ≥ � | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-10 12:05:17 | [skip_design](20260810-120517_skip_design.md) | Tick #455 (2026-08-10 12:03): 队列深度 waiting=10 ≥ � | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-10 13:04:25 | [skip_design](20260810-130425_skip_design.md) | Tick #456 (2026-08-10 13:03): 队列深度 waiting=10 ≥ � | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-10 14:04:34 | [skip_design](20260810-140434_skip_design.md) | Tick #457 (2026-08-10 14:03): 队列深度 waiting=10 ≥ � | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-10 15:05:10 | [skip_design](20260810-150510_skip_design.md) | Tick #458 (2026-08-10 15:03): 队列深度 waiting=10 ≥ � | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-10 15:46:13 | [queue_push](20260810-154613_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M79 REAGG + 级联正确重聚合 (修复 _reaggregate lvl>0 缺陷, 单一变量对照 M7 |
| 2026-08-10 16:04:52 | [early_stop](20260810-160452_early_stop.md) | M74-CCP-HCG-DET 进程消失 (deathwatch 2/3), 远端日志� | 标记 M74-CCP-HCG-DET → done_earlystop, best=0.4948@ep27, |
| 2026-08-10 16:05:43 | [skip_design](20260810-160543_skip_design.md) | Tick #459 (2026-08-10 16:03): 队列深度判定 waiting=9 � | 跳过自主设计, 本 tick 仅监控 (5 running: M78-REAGG |
| 2026-08-10 17:04:17 | [skip_design](20260810-170417_skip_design.md) | Tick #460 (2026-08-10 17:03): 队列深度判定 waiting=9 � | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-10 18:05:38 | [skip_design](20260810-180538_skip_design.md) | Tick #461 (2026-08-10 18:03): 队列深度判定 waiting=9 � | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-10 19:04:48 | [skip_design](20260810-190448_skip_design.md) | tick #462 (2026-08-10 19:03): 队列深度判定 waiting=9 � | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-10 20:05:15 | [skip_design](20260810-200515_skip_design.md) | Tick #463 (2026-08-10 20:03): 队列深度判定 waiting=9 � | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-10 21:04:59 | [skip_design](20260810-210459_skip_design.md) | Tick #464 (2026-08-10 21:03): 队列深度判定 waiting=9 � | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-10 22:04:39 | [skip_design](20260810-220439_skip_design.md) | Tick #465 (2026-08-10 22:03): 队列深度判定 waiting=9 � | 跳过自主设计. 本 tick 仅监控: 5 running 全部存� |
| 2026-08-10 23:04:15 | [skip_design](20260810-230415_skip_design.md) | Tick #466 (2026-08-10 23:03): 队列深度判定 waiting=9 � | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-11 00:04:25 | [skip_design](20260811-000425_skip_design.md) | Tick #467 (2026-08-11 00:03): 队列深度判定 waiting=9 � | 跳过自主设计, 本 tick 仅监控 (5 running: M78-REAGG |
| 2026-08-11 01:06:18 | [skip_design](20260811-010618_skip_design.md) | Tick #468 (2026-08-11 01:03): 队列深度判定 waiting=9 � | 跳过自主设计, 本 tick 仅监控 (5 running: M78-REAGG |
| 2026-08-11 02:03:29 | [queue_push](20260811-020329_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M80 REAGG + 级联正确重聚合 × HCG 正确多尺度交付 (修复链 2×2 满格, 零新增参数)] c |
| 2026-08-11 02:06:59 | [early_stop](20260811-020659_early_stop.md) | M78-REAGG-HCG (reag × HCG) 进程消失 (deathwatch 1/3), � | 标记 M78-REAGG-HCG → done_earlystop, best=0.5008@ep14, e |
| 2026-08-11 03:05:23 | [skip_design](20260811-030523_skip_design.md) | tick #470 (2026-08-11 03:03): 队列深度判定 waiting=8 � | 跳过自主设计, 本 tick 仅监控 (5 running: M80-REAG- |
| 2026-08-11 04:04:52 | [skip_design](20260811-040452_skip_design.md) | tick #471 (2026-08-11 04:03): 队列深度判定 waiting=8 � | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-11 05:04:59 | [skip_design](20260811-050459_skip_design.md) | tick #472 (2026-08-11 05:03): 队列深度判定 waiting=8 � | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-11 06:04:12 | [skip_design](20260811-060412_skip_design.md) | tick #473 (2026-08-11 06:03): 队列深度判定 waiting=8 � | 跳过自主设计, 本 tick 仅监控 (5 running: M80-REAG- |
| 2026-08-11 07:05:55 | [skip_design](20260811-070555_skip_design.md) | tick #474 (2026-08-11 07:03): 队列深度判定 waiting=8 � | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-11 08:05:09 | [skip_design](20260811-080509_skip_design.md) | tick #475 (2026-08-11 08:03): 队列深度判定 waiting=8 � | 跳过自主设计, 本 tick 仅监控 (5 running: M80-REAG- |
| 2026-08-11 09:07:16 | [skip_design](20260811-090716_skip_design.md) | tick #476 (2026-08-11 09:03): 队列深度判定 waiting=8 � | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-11 10:04:52 | [skip_design](20260811-100452_skip_design.md) | tick #477 (2026-08-11 10:03): 队列深度判定 waiting=8 � | 跳过自主设计, 本 tick 仅监控 (5 running: M80-REAG- |
| 2026-08-11 11:04:57 | [skip_design](20260811-110457_skip_design.md) | Tick #478 (2026-08-11 11:03): 队列深度判定 waiting=8,  | 跳过自主设计. 本 tick 仅监控: 5/5 槽位满, M79-R |
| 2026-08-11 11:27:00 | [queue_push](20260811-112700_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M81 CTF token FFN精炼 × HCG 正确多尺度交付 ({token质量}×{交付} 正交格, 零 |
| 2026-08-11 12:08:29 | [early_stop](20260811-120829_early_stop.md) | M79-REAG-CASC (reag_casc) 进程消失且日志确认自然� | 标记 M79-REAG-CASC → done_earlystop, best=0.4919@ep28, � |
| 2026-08-11 12:09:14 | [skip_design](20260811-120914_skip_design.md) | Tick #479 (2026-08-11 12:03): 队列深度判定 waiting=7,  | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-11 13:05:54 | [skip_design](20260811-130554_skip_design.md) | tick#480: 队列深度判定 waiting=7(server-4 7 + server-6 | 跳过自主设计, 本 tick 仅监控 (5/5 running 全部� |
| 2026-08-11 14:04:26 | [skip_design](20260811-140426_skip_design.md) | tick#481: 队列深度判定 waiting=7(server-4 7 + server-6 | 跳过自主设计, 本 tick 仅监控 (5/5 running 全部� |
| 2026-08-11 15:04:54 | [skip_design](20260811-150454_skip_design.md) | tick#482 (2026-08-11 15:04): 队列深度判定 waiting=7(se | 跳过自主设计, 本 tick 仅监控 (5/5 running 全部� |
| 2026-08-11 16:04:24 | [skip_design](20260811-160424_skip_design.md) | tick#483 (2026-08-11 16:04): 队列深度判定 waiting=7(se | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-11 17:04:07 | [skip_design](20260811-170407_skip_design.md) | tick#484: 队列深度判定 waiting=7(server-4 7 + server-6 | 跳过自主设计, 本 tick 仅监控 (5 running 全部存� |
| 2026-08-11 18:22:38 | [skip_design](20260811-182238_skip_design.md) | Tick #485 (2026-08-11 18:06): 队列深度判定 waiting=7(s | 跳过自主设计. 本 tick 仅监控: 确认 5 running 存 |
| 2026-08-11 18:22:52 | [question](20260811-182252_question.md) | server-6 (100.64.3.28) 直连 18:06 不可达 (ping 100% 丢 | 留待用户确认. 本 tick 已用 server-4 跳板 (ssh -J  |
| 2026-08-11 21:16:02 | [queue_push](20260811-211602_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M82 CTF × detail 残差 message ({token质量}×{message} 补格)] co |
| 2026-08-12 09:00:40 | [queue_push](20260812-090040_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M83 级联正确重聚合 × detail (修复链 message 轴补格)] configs/Quard/de |
| 2026-08-12 10:42:24 | [unhealthy_recovery](20260812-104224_unhealthy_recovery.md) | 上次 tick (~Aug 11 18:22) 不健康, .tick_unhealthy 存� | 补齐 5 个终态分析(M75/M76/M77/M80/M81) + 修复 queue |
| 2026-08-12 10:47:57 | [next_batch](20260812-104757_next_batch.md) | 队列深度 3 waiting < 可用槽 5+1=6 (tick #486 unhealth | 设计 M89-CTF-HCG-R2 (seed=42) + M90-CTF-HCG-S3 (seed=123)  |
| 2026-08-12 10:49:48 | [skip_design](20260812-104948_skip_design.md) | Queue depth 6 waiting >= 5+1=6 OK. All 5 GPU slots occupied  | 跳过自主设计。队列深度充足，所有卡在跑， |
| 2026-08-12 10:54:13 | [next_batch](20260812-105413_next_batch.md) | 队列深度不足: waiting=3 < 可用卡数+1=6, 需补 ≥ | 设计并实现 3 个新结构变体: M89-CTF-HCG-ORT (三� |
| 2026-08-12 10:54:31 | [queue_push](20260812-105431_queue_push.md) | 3 个新实验已实现并入队: M89-CTF-HCG-ORT / M90-CTF- | 入队 server-4: [M89-CTF-HCG-ORT] ctf_hcg_ort, [M90-CTF-SEF |
| 2026-08-12 11:00:51 | [skip_design](20260812-110051_skip_design.md) | Queue depth=9 waiting >= 6 (5 slots+1), all 5 GPU slots occu | 跳过自主设计, 本 tick 仅监控  |
| 2026-08-12 11:00:57 | [question](20260812-110057_question.md) | M89-CTF-HCG-R2 / M90-CTF-HCG-S3 / M91-HCG-R2 三个 seed re- | 留待用户确认. 选项: (a) 从远程 server-4 拉取 ct |
| 2026-08-12 11:02:12 | [queue_push](20260812-110212_queue_push.md) | M89/M90/M91 config YAMLs 缺失 — 从 server-4 拉取原� | 创建 configs/Quard/ctf_hcg_r2/...ctf_hcg_s42.yaml (seed=42 |
| 2026-08-12 16:16:33 | [queue_push](20260812-161633_queue_push.md) | server-4 gpu0 空闲，推送哪个排队实验？ | 尝试启动 [M84 CTF×HCG×detail 三维满格 (M74 先例, token精炼×正确交付×残差messag |
| 2026-08-12 18:51:40 | [queue_push](20260812-185140_queue_push.md) | M84 推送失败第8次(16:16起6次自动+2次本tick诊断 | 修复 scripts/remote_train.sh+sync.sh 的 PROJECT_DIR 解� |
| 2026-08-12 18:56:13 | [skip_design](20260812-185613_skip_design.md) | Tick #20260812-B: 队列深度 9 waiting vs 容量槽位 4 ( | 跳过自主设计。本 tick 仅监控: 4 running 全部存 |
| 2026-08-12 18:59:27 | [skip_design](20260812-185927_skip_design.md) | Tick #20260812-C: 队列深度 9 waiting vs 容量槽位 4 ( | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-12 19:08:32 | [skip_design](20260812-190832_skip_design.md) | Tick #20260812-D: 队列深度 9 waiting vs 容量槽位 4 ( | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-12 22:09:35 | [skip_design](20260812-220936_skip_design.md) | Tick #20260812-E: 队列深度 9 waiting vs 容量 4 (≥4+1 | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-12 22:09:37 | [unhealthy_recovery](20260812-220937_unhealthy_recovery.md) | .tick_unhealthy 存在 (count=2): 20:07/21:07/21:48 三 tick | 确认 4 running 全部存活无新增终态/崩溃, 队列� |
| 2026-08-12 23:08:59 | [skip_design](20260812-230859_skip_design.md) | Tick #20260812-F (2026-08-12 23:08): 队列深度判定 wait | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 00:08:40 | [skip_design](20260813-000840_skip_design.md) | Tick #20260813-00:07: 队列深度判定 waiting=9 vs 容量 | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 01:10:02 | [skip_design](20260813-011002_skip_design.md) | Tick #20260813-01:07: 队列深度判定 waiting=9 vs 容量 | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 02:07:26 | [early_stop](20260813-020726_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_det_reag_casc] 连续 1 | kill PID=3132581 on server-4 gpu=1 |
| 2026-08-13 02:11:06 | [queue_push](20260813-021106_queue_push.md) | server-4 gpu1 空闲（M83-DET-REAG-CASC 早停 kill 释放� | 启动 [M81-CONS intra-cluster 一致性正则] configs/Quar |
| 2026-08-13 02:12:38 | [skip_design](20260813-021238_skip_design.md) | Tick #20260813-02:12: 队列深度判定 waiting=8 vs 容量 | 跳过自主设计. 本 tick 监控+推送: M83 早停 kill, |
| 2026-08-13 03:09:56 | [skip_design](20260813-030956_skip_design.md) | Tick #20260813-03:09: 队列深度判定 waiting=8 vs 容量 | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 04:09:39 | [skip_design](20260813-040939_skip_design.md) | Tick #20260813-04:08: 队列深度判定 waiting=8 (server-4 | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 05:09:30 | [skip_design](20260813-050930_skip_design.md) | Tick #20260813-05:08: 队列深度判定 waiting=8 (server-4 | 跳过自主设计. 本 tick 仅监控: M84 no_impr=3/10, M8 |
| 2026-08-13 06:09:22 | [skip_design](20260813-060922_skip_design.md) | Tick #20260813-06:09: 队列深度判定 waiting=8 (server-4 | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 07:08:59 | [skip_design](20260813-070859_skip_design.md) | Tick #20260813-07:08: 队列深度判定 waiting=8 (server-4 | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 08:09:25 | [skip_design](20260813-080925_skip_design.md) | Tick #20260813-08:07: 队列深度判定 waiting=8 (server-4 | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 09:10:15 | [skip_design](20260813-091016_skip_design.md) | Tick #20260813-09:07: 队列深度判定 waiting=8 (server-4 | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 10:09:27 | [skip_design](20260813-100927_skip_design.md) | Tick #20260813-10:07: 队列深度判定 waiting=8 (server-4 | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 11:09:23 | [skip_design](20260813-110924_skip_design.md) | Tick #20260813-11:07: 队列深度判定 waiting=8 (server-4 | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 12:07:27 | [early_stop](20260813-120727_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_det_ctf_hcg] 连续 13  | kill PID=143660 on server-4 gpu=0 |
| 2026-08-13 12:10:39 | [queue_push](20260813-121039_queue_push.md) | server-4 gpu0 空闲（M84-DET-CTF-HCG 早停 kill 释放） | 启动 [M87-DET-CONS] configs/Quard/det_cons/model_base1_qua |
| 2026-08-13 12:12:01 | [skip_design](20260813-121201_skip_design.md) | Tick #20260813-12: 队列深度判定 waiting=7 vs 容量 4  | 跳过自主设计。本 tick 监控+推送: M84-DET-CTF-HCG |
| 2026-08-13 13:09:21 | [skip_design](20260813-130921_skip_design.md) | Tick #20260813-13: 队列深度判定 waiting=7 (server-4 6  | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 14:10:06 | [skip_design](20260813-141006_skip_design.md) | Tick #20260813-14 (2026-08-13 14:09): 队列深度判定 wai | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 15:08:51 | [skip_design](20260813-150851_skip_design.md) | Tick #20260813-15 (2026-08-13 15:08): 队列深度判定 wai | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 16:09:32 | [skip_design](20260813-160932_skip_design.md) | Tick #20260813-16 (2026-08-13 16:08): 队列深度判定 wai | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 17:08:34 | [skip_design](20260813-170834_skip_design.md) | Tick #20260813-17 (2026-08-13 17:08): 队列深度判定 wai | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 18:09:25 | [skip_design](20260813-180925_skip_design.md) | Tick #20260813-18 (2026-08-13 18:09): 队列深度判定 wai | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 19:09:46 | [skip_design](20260813-190946_skip_design.md) | Tick #20260813-19 (2026-08-13 19:09): 队列深度判定 wai | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 20:09:23 | [skip_design](20260813-200924_skip_design.md) | Tick #20260813-20 (2026-08-13 20:09): 队列深度判定 wai | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-13 21:09:06 | [skip_design](20260813-210906_skip_design.md) | Tick #20260813-21: 队列深度判定 waiting=7 vs 容量 4  | 跳过自主设计。本 tick 仅监控: 4 running 全部存 |
| 2026-08-13 22:09:25 | [skip_design](20260813-220925_skip_design.md) | Tick #20260813-22: 队列深度判定 waiting=7 vs 容量4 ( | 跳过自主设计。本 tick 仅监控: 4 running 全部存 |
| 2026-08-13 23:07:36 | [early_stop](20260813-230736_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_qmod] 连续 11 次验证未刷新  | kill PID=2166760 on server-6 gpu=7 |
| 2026-08-13 23:13:41 | [queue_push](20260813-231341_queue_push.md) | server-6 gpu7 空闲（M85-QMOD 早停 kill 释放 1 槽位, | 启动 [M86-MLAY] configs/Quard/mlay/model_base1_quard2_c2f_ |
| 2026-08-13 23:14:29 | [skip_design](20260813-231429_skip_design.md) | Tick #20260813-23: 队列深度判定 waiting=6 vs 容量4+1 | 跳过自主设计. 本 tick 动作: M85-QMOD 早停 kill, M |
| 2026-08-13 23:16:29 | [early_stop](20260813-231629_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_qmod_mlay] 连续 11 次验 | kill PID=2165232 on server-6 gpu=7 |
| 2026-08-14 00:10:57 | [queue_push](20260814-001057_queue_push.md) | server-6 GPU7 空闲 1 槽位 (M88-QMOD-MLAY 早停 kill 释 | 启动 [M89-CTF-HCG-R2] configs/Quard/ctf_hcg_r2/model_base1 |
| 2026-08-14 00:12:32 | [skip_design](20260814-001232_skip_design.md) | 队列深度判定: waiting=5 (M90-M94 on server-4) vs 容� | 跳过自主设计. 本 tick 仅监控+推送: M89 补推 se |
| 2026-08-14 00:12:33 | [terminal](20260814-001233_terminal.md) | M88-QMOD-MLAY done_earlystop (best 0.4930@22/50), 缺终态� | 生成 pipeline/analyses/M88-QMOD-MLAY_done_earlystop_202608 |
| 2026-08-14 01:09:22 | [skip_design](20260814-010922_skip_design.md) | Tick #20260814-01: 队列深度判定 waiting=5 (M90-M94 on  | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-14 02:10:15 | [skip_design](20260814-021015_skip_design.md) | Tick #20260814-02: 队列深度判定 waiting=5 (M90-M94 on  | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-14 03:07:22 | [early_stop](20260814-030722_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_cons] 连续 11 次验证未刷新  | kill PID=1340649 on server-4 gpu=1 |
| 2026-08-14 03:14:57 | [queue_push](20260814-031457_queue_push.md) | server-4 gpu1 空闲 (M81-CONS 早停 kill 释放, util<10%) | 启动 [M90-CTF-HCG-S3] configs/Quard/ctf_hcg_s3/model_base1 |
| 2026-08-14 03:22:23 | [next_batch](20260814-032223_next_batch.md) | 队列深度不足 (M90 入队后 waiting=4 < 容量4+1=5),  | 设计 M95-CTF-HCG-CSORT (跨尺度正交 loss) + M96-CTF-HC |
| 2026-08-14 03:22:25 | [route_change](20260814-032225_route_change.md) | ORT 多样性轴机制存疑: 老实现 (ort 包 + ctf_hcg_o | 判定 ORT 轴从未被真正测试, M17-ORT 0.5005 归因� |
| 2026-08-14 04:09:59 | [skip_design](20260814-040959_skip_design.md) | Tick #20260814-04: 队列深度判定 waiting=6 vs 容量4 ( | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-14 05:09:52 | [skip_design](20260814-050952_skip_design.md) | Tick #20260814-05: 队列深度判定 waiting=6 vs 容量4 ( | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-14 06:07:25 | [early_stop](20260814-060725_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_det_cons] 连续 11 次验证 | kill PID=2941817 on server-4 gpu=0 |
| 2026-08-14 06:09:58 | [queue_push](20260814-060958_queue_push.md) | server-4 gpu0 空闲 (M87-DET-CONS 早停 kill 释放, util< | 启动 [M91-HCG-R2] configs/Quard/hcg_r2/model_base1_quard2_ |
| 2026-08-14 06:10:26 | [terminal](20260814-061026_terminal.md) | M87-DET-CONS done_earlystop (best 0.4930@24/50), 缺终态� | 生成 pipeline/analyses/M87-DET-CONS_done_earlystop_2026081 |
| 2026-08-14 06:11:02 | [skip_design](20260814-061102_skip_design.md) | Tick #20260814-06: M91 入队后 waiting=5 vs 容量4 (serve | 跳过自主设计. 本 tick 动作: 早停 M87-DET-CONS + � |
| 2026-08-14 07:09:32 | [skip_design](20260814-070932_skip_design.md) | Tick #20260814-07: 队列深度判定 waiting=5 vs 容量4 ( | 跳过自主设计. 本 tick 仅监控: 4 running 全部健� |
| 2026-08-14 08:09:56 | [skip_design](20260814-080956_skip_design.md) | Tick #20260814-08: 队列深度判定 waiting=5 vs 容量4 ( | 跳过自主设计. 本 tick 仅监控: 4 running 全部健� |
| 2026-08-14 09:09:09 | [skip_design](20260814-090909_skip_design.md) | 队列深度判定 waiting=5 vs 容量4 (server-4 5 waiting  | 跳过自主设计, 本 tick 仅监控: 4/4 槽位满, M90@1 |
| 2026-08-14 10:10:03 | [skip_design](20260814-101003_skip_design.md) | Tick #20260814-10: 队列深度判定 waiting=5 vs 容量4 ( | 跳过自主设计. 本 tick 仅监控: 队列深度 5>=5(� |
| 2026-08-14 11:08:39 | [skip_design](20260814-110839_skip_design.md) | Tick #20260814-11: 队列深度判定 waiting=5 vs 容量4 ( | 跳过自主设计. 本 tick 仅监控: 无早停/无推送/ |
| 2026-08-14 12:08:44 | [skip_design](20260814-120844_skip_design.md) | Tick #20260814-12: 队列深度判定 waiting=5 (server-4 M9 | 跳过自主设计. 队列深度 5 >= 容量4+1=5 达标; 4/ |
| 2026-08-14 13:08:56 | [skip_design](20260814-130856_skip_design.md) | Tick #20260814-13: 队列深度判定 waiting=5 vs 容量4 ( | 跳过自主设计. 队列深度 5 >= 容量4+1=5 达标; 4/ |
| 2026-08-14 14:09:46 | [skip_design](20260814-140946_skip_design.md) | Tick #20260814-14: 队列深度判定 waiting=5 (server-4 M9 | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-14 15:08:48 | [skip_design](20260814-150848_skip_design.md) | Tick #20260814-15: 队列深度判定 waiting=5 (server-4 M9 | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-14 16:09:04 | [skip_design](20260814-160904_skip_design.md) | Tick #20260814-16: 队列深度 waiting=5 vs 容量4+1=5 (se | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-14 17:10:44 | [skip_design](20260814-171044_skip_design.md) | 队列深度判定: waiting=5 vs 容量4+1=5 (server-4 2卡  | 跳过自主设计。本 tick 仅监控: 4 running 全部健 |
| 2026-08-14 18:08:38 | [skip_design](20260814-180838_skip_design.md) | Tick #20260814-18: 队列深度判定 waiting=5 (server-4 M9 | 跳过自主设计. 本 tick 仅监控: 4 running 全部健� |
| 2026-08-14 19:09:12 | [skip_design](20260814-190912_skip_design.md) | Tick #20260814-19: 队列深度判定 waiting=5 (server-4 M9 | 跳过自主设计. 本 tick 仅监控: 4 running 全部存� |
| 2026-08-14 20:07:21 | [early_stop](20260814-200721_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_s123] 连续 11 | kill PID=825216 on server-4 gpu=1 |
| 2026-08-14 20:12:07 | [queue_push](20260814-201207_queue_push.md) | server-4 gpu1 空闲 (M90-CTF-HCG-S3 早停 kill 释放, uti | 启动 [M92-CTF-HCG-ORT] configs/Quard/ctf_hcg_ort/model_bas |
| 2026-08-14 20:12:08 | [terminal](20260814-201208_terminal.md) | M90-CTF-HCG-S3 done_earlystop (best 0.4940@25/50), 缺终态 | 生成 pipeline/analyses/M90-CTF-HCG-S3_done_earlystop_20260 |
| 2026-08-14 20:12:14 | [route_change](20260814-201214_route_change.md) | M90-CTF-HCG-S3 (seed=123) best 0.4940 低于 M81-CTF-HCG (se | CTF×HCG 复现性存疑, 判定为'部分有效'基准; 等 |
| 2026-08-14 20:20:38 | [next_batch](20260814-202038_next_batch.md) | M92 推送后 waiting=4<容量4+1=5 且 server-6 队列空,  | 设计 M97-CHAMP-ORT: 复制 ortg 包→champ_ort (C2F_Clust |
| 2026-08-14 21:07:21 | [early_stop](20260814-210721_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_hcg_s42] 连续 11 次验证未 | kill PID=1225821 on server-4 gpu=0 |
| 2026-08-14 21:16:27 | [queue_push](20260814-211627_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M94 HCGxORT simplified combo] configs/Quard/hcg_ort/mode |
| 2026-08-14 21:21:45 | [queue_push](20260814-212145_queue_push.md) | M91-HCG-R2 早停释放 server-4 GPU0, 推送哪个排队实 | 启动 M93-CTF-SEF (FIFO 队首) → server-4 gpu0 (PID=3381 |
| 2026-08-14 21:21:45 | [bugfix](20260814-212145_bugfix.md) | M93-CTF-SEF 启动 crash (Unknown cluster_mode: ctf_sef), M9 | Phase 3b 修复: ctf_sef 注册模式+接线 SE; hcg_ort 加 |
| 2026-08-14 21:21:52 | [next_batch](20260814-212152_next_batch.md) | 队列深度 4<5 (容量4+1), 多样性轴 champion 基底� | 设计 M98-CHAMP-CSORT: 复制 champ_ort→champ_csort, 尺� |
| 2026-08-14 21:21:52 | [terminal](20260814-212152_terminal.md) | M91-HCG-R2 (seed42 HCG) 终态后是否生成分析?  | M91 → done_earlystop (0.4963@ep24), 生成 pipeline/analys |
| 2026-08-14 21:21:52 | [route_change](20260814-212152_route_change.md) | M91 (seed42) 0.4963 vs M65 (seed1999) 0.5002, M90 (seed123)  | 判定 seed 方差 ~±0.004-0.007 属实; '破顶'标准从� |
| 2026-08-14 22:09:41 | [skip_design](20260814-220941_skip_design.md) | 队列深度判定: waiting=5 vs 容量4 (server-4 3 waiting | 跳过自主设计. 本 tick 仅监控+报告: 4 running 全 |
| 2026-08-14 23:09:14 | [skip_design](20260814-230914_skip_design.md) | 队列深度判定: waiting=5 vs 容量4+1=5 (容量=server- | 跳过自主设计. 本 tick 仅监控+报告: 4 running 全 |
| 2026-08-15 00:10:20 | [skip_design](20260815-001020_skip_design.md) | Tick #20260815-00: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计. 本 tick 仅监控+报告: 无空闲槽� |
| 2026-08-15 01:10:03 | [skip_design](20260815-011003_skip_design.md) | Tick #20260815-01: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计. 本 tick 仅监控+报告: 无空闲槽� |
| 2026-08-15 02:09:18 | [skip_design](20260815-020918_skip_design.md) | 队列深度判定: waiting=5 vs 容量4+1=5 (server-4 3 wai | 跳过自主设计. 队列深度 5≥5 达标, 4/4 容量槽 |
| 2026-08-15 03:09:01 | [skip_design](20260815-030901_skip_design.md) | 队列深度判定 waiting=5 vs 容量4+1=5 (server-4 3 wait | 跳过自主设计. 队列深度 5≥5 达标, 4/4 容量槽 |
| 2026-08-15 04:09:02 | [skip_design](20260815-040902_skip_design.md) | Tick #20260815-04 (04:07): 队列深度判定 waiting=5 vs � | 跳过自主设计. 队列深度 5≥5 达标, 4/4 容量槽 |
| 2026-08-15 05:08:42 | [skip_design](20260815-050842_skip_design.md) | Tick #20260815-05: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计. 队列深度 5>=5 达标, 4/4 容量槽� |
| 2026-08-15 06:08:44 | [skip_design](20260815-060844_skip_design.md) | Tick #20260815-06: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计. 本 tick 仅监控+报告: 4 running 全 |
| 2026-08-15 07:09:27 | [skip_design](20260815-070927_skip_design.md) | Tick #20260815-07: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计. 本 tick 仅监控+报告: 4 running 全 |
| 2026-08-15 07:16:19 | [early_stop](20260815-071619_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_sef] 连续 11 次验证未 | kill PID=3381263 on server-4 gpu=0 |
| 2026-08-15 08:07:24 | [early_stop](20260815-080724_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_sef] 连续 11 次验证未 | kill PID=3382141 on server-4 gpu=0 |
| 2026-08-15 08:08:46 | [queue_push](20260815-080846_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M94 HCGxORT simplified combo] configs/Quard/hcg_ort/mode |
| 2026-08-15 08:16:31 | [queue_push](20260815-081631_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M95 CTF-HCG + cross-scale orth loss (csort_weight=0.01)] |
| 2026-08-15 08:26:43 | [next_batch](20260815-082643_next_batch.md) | 队列深度 waiting=4 < 容量4+1=5, 且 08-14 route_change | 设计 M99-CHAMP-S42 + M100-CHAMP-S123 (champion posA_l1 see |
| 2026-08-15 08:26:45 | [other](20260815-082645_other.md) | M94-HCG-ORT 启动 NameError (orth_weight 未定义) + M95-C | Phase 3b 修复: hcg_ort dec.py 加 orth_weight=0.01 参数; |
| 2026-08-15 08:26:49 | [early_stop](20260815-082649_early_stop.md) | M93-CTF-SEF 终态 (best 0.4910@18/50, no_improve=11/10), � | done_earlystop — 已 kill (PID=3382141), 生成终态分� |
| 2026-08-15 09:07:33 | [queue_push](20260815-090733_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M94 HCGxORT simplified combo] configs/Quard/hcg_ort/mode |
| 2026-08-15 09:09:34 | [skip_design](20260815-090934_skip_design.md) | Tick #20260815-09: 队列深度 waiting=6 vs 容量4+1=5 (se | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-15 10:07:27 | [early_stop](20260815-100727_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_ort] 连续 11  | kill PID=3221876 on server-4 gpu=1 |
| 2026-08-15 10:10:13 | [queue_push](20260815-101013_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M95 CTF-HCG + cross-scale orth loss (csort_weight=0.01)] |
| 2026-08-15 10:12:26 | [route_change](20260815-101227_route_change.md) | M92-CTF-HCG-ORT 三轴组合早停 Best=0.4930 (22/50, no_im | M92 判定为失败 (γ=-0.0082 vs champion 0.5012)；保留 |
| 2026-08-15 11:11:20 | [skip_design](20260815-111120_skip_design.md) | Tick #20260815-11: 队列深度 waiting=5 vs 容量4+1=5 (se | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-15 12:08:49 | [skip_design](20260815-120849_skip_design.md) | Tick #20260815-12: 队列深度 waiting=5 vs 容量4+1=5 (se | 跳过自主设计. 队列深度 5>=5 达标, 4/4 容量槽� |
| 2026-08-15 13:10:11 | [skip_design](20260815-131011_skip_design.md) | Tick #20260815-13: 队列深度 waiting=5 vs 容量4+1=5 (se | 跳过自主设计. 队列深度 5>=5 达标, 4/4 容量槽� |
| 2026-08-15 14:09:06 | [skip_design](20260815-140906_skip_design.md) | Tick #20260815-14: 队列深度 waiting=5 vs 容量4+1=5, � | 跳过自主设计. 队列深度 5>=5 达标, 4/4 容量槽� |
| 2026-08-15 15:09:39 | [skip_design](20260815-150940_skip_design.md) | Tick #20260815-15: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-15 16:27:25 | [next_batch](20260815-162725_next_batch.md) | 队列深度不足 (waiting=5 < 可用槽5+1=6), champion 0. | 入队 M101-CHAMP-S2026 + M102-CTF-HCG-S2026 (均 seed=2026, |
| 2026-08-15 17:08:47 | [skip_design](20260815-170847_skip_design.md) | Tick #20260815-17: 队列深度判定 waiting=7 vs 容量4+1 | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-15 18:09:26 | [skip_design](20260815-180926_skip_design.md) | Tick #20260815-18 (18:07): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告  |
| 2026-08-15 19:09:42 | [skip_design](20260815-190942_skip_design.md) | Tick #20260815-19 (19:08): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告  |
| 2026-08-15 20:07:22 | [early_stop](20260815-200722_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_hcg_ort] 连续 11 次验证未 | kill PID=805731 on server-4 gpu=0 |
| 2026-08-15 20:11:23 | [terminal](20260815-201123_terminal.md) | M94-HCG-ORT done_earlystop (best 0.4930@19/50, no_improve=11 | 生成 pipeline/analyses/M94-HCG-ORT_done_earlystop_20260815 |
| 2026-08-15 20:11:26 | [skip_design](20260815-201126_skip_design.md) | Tick #20260815-20 (20:07): 队列深度判定 waiting=7 vs � | 跳过自主设计. 队列深度 7>=6 达标, 本 tick 仅� |
| 2026-08-15 21:10:39 | [skip_design](20260815-211040_skip_design.md) | Tick #20260815-21 (21:07): 队列深度判定 waiting=7 (ser | 跳过自主设计. 队列深度 7>=5 达标, 本 tick 仅� |
| 2026-08-15 22:07:35 | [queue_push](20260815-220735_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M96 CTF-HCG + 2-layer injection (cluster_att_num_layers= |
| 2026-08-15 22:09:10 | [skip_design](20260815-220911_skip_design.md) | Tick #20260815-22 (22:07): 队列深度判定 waiting=6 vs � | 跳过自主设计. 队列深度 6>=5 达标, 本 tick 仅� |
| 2026-08-15 23:09:28 | [skip_design](20260815-230928_skip_design.md) | Tick #20260815-23 (23:07): 队列深度判定 waiting=6 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-16 00:10:08 | [skip_design](20260816-001008_skip_design.md) | Tick #20260816-00 (00:07): 队列深度判定 waiting=6 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-16 01:08:42 | [skip_design](20260816-010842_skip_design.md) | Tick #20260816-01: 队列深度判定 waiting=6 vs 容量4+1 | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-16 02:07:32 | [early_stop](20260816-020732_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_s42] 连续 11  | kill PID=1672532 on server-6 gpu=7 |
| 2026-08-16 02:07:49 | [queue_push](20260816-020749_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M97 champion-base true-gradient ORT (isolate ORT diversi |
| 2026-08-16 02:17:29 | [next_batch](20260816-021729_next_batch.md) | M95 CTF×HCG×CSORT (seed1999)=0.5020 首个>champion 观测 | 入队 M103-CTF-HCG-CSORT-S2026 + M104-CTF-HCG-CSORT-S42 (� |
| 2026-08-16 02:17:56 | [terminal](20260816-021756_terminal.md) | M89-CTF-HCG-R2 (seed42) 早停 kill Best=0.4980, 是否判� | 生成 pipeline/analyses/M89-CTF-HCG-R2_done_earlystop_20260 |
| 2026-08-16 03:07:24 | [early_stop](20260816-030724_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort] 连续 1 | kill PID=949721 on server-4 gpu=1 |
| 2026-08-16 03:10:04 | [queue_push](20260816-031004_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M99 champion posA_l1 seed=42 (跨 seed 破顶基线控制)] configs/Qu |
| 2026-08-16 03:12:39 | [terminal](20260816-031239_terminal.md) | M95-CTF-HCG-CSORT done_earlystop (Best=0.5020@22/50, no_impr | 判定 done_earlystop — 生成 pipeline/analyses/M95-CTF-H |
| 2026-08-16 03:12:41 | [skip_design](20260816-031241_skip_design.md) | Tick #20260816-03 (03:07): 队列深度判定 waiting=6 vs � | 跳过自主设计. 本 tick 仅监控+报告+终态分析:  |
| 2026-08-16 04:08:55 | [skip_design](20260816-040855_skip_design.md) | Tick #20260816-04: 队列深度判定 waiting=6 vs 容量4+1 | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-16 05:09:32 | [skip_design](20260816-050932_skip_design.md) | Tick #20260816-05 (05:07): 队列深度判定 waiting=6 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-16 06:09:07 | [skip_design](20260816-060907_skip_design.md) | Tick #20260816-06 (06:07): 队列深度判定 waiting=6 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-16 07:09:41 | [skip_design](20260816-070941_skip_design.md) | Tick #20260816-07 (07:07): 队列深度判定 waiting=6 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-16 08:08:43 | [skip_design](20260816-080843_skip_design.md) | Tick #20260816-08 (08:07): 队列深度判定 waiting=6 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-16 09:09:09 | [skip_design](20260816-090910_skip_design.md) | Tick #20260816-09: 队列深度判定 waiting=6 vs 容量4+1 | 跳过自主设计. 本 tick 仅监控+报告: 4 running (M9 |
| 2026-08-16 10:07:23 | [early_stop](20260816-100723_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_2lay] 连续 11 | kill PID=2668352 on server-4 gpu=0 |
| 2026-08-16 10:10:43 | [queue_push](20260816-101043_queue_push.md) | server-4 gpu0 空闲（M96-CTF-HCG-2LAY 早停 kill 释放� | 启动 [M100 champion posA_l1 seed=123 (跨 seed 破顶基� |
| 2026-08-16 10:11:20 | [terminal](20260816-101120_terminal.md) | M96-CTF-HCG-2LAY done_earlystop (Best=0.4940@22/50, no_impr= | 判定 done_earlystop — 生成 pipeline/analyses/M96-CTF-H |
| 2026-08-16 10:11:54 | [skip_design](20260816-101154_skip_design.md) | Tick #20260816-10: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计. 本 tick 监控+早停+推送+终态分� |
| 2026-08-16 11:09:18 | [skip_design](20260816-110918_skip_design.md) | Tick #20260816-11 (11:07): 队列深度判定 waiting=5 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4 running (M1 |
| 2026-08-16 12:18:19 | [next_batch](20260816-121819_next_batch.md) | 队列深度不足 (waiting=5 < 可用槽5+1=6), CSORT 是� | 入队 M105-CTF-HCG-CSORT-S123 + M106-CHAMP-CSORT-S42 (commi |
| 2026-08-16 13:08:31 | [skip_design](20260816-130831_skip_design.md) | Tick #20260816-13 (13:07): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4 running (M1 |
| 2026-08-16 14:08:50 | [skip_design](20260816-140850_skip_design.md) | Tick #20260816-14 (14:07): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4 running (M9 |
| 2026-08-16 15:09:32 | [skip_design](20260816-150932_skip_design.md) | Tick #20260816-15 (15:07): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4 running (M9 |
| 2026-08-16 16:09:02 | [skip_design](20260816-160902_skip_design.md) | Tick #20260816-16 (16:07): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4/5 容量槽 |
| 2026-08-16 17:09:37 | [skip_design](20260816-170937_skip_design.md) | Tick #20260816-17: 队列深度 waiting=7 vs 容量5+1=6 达 | 跳过自主设计. 本 tick 仅监控+报告. 队列已有  |
| 2026-08-16 18:09:14 | [skip_design](20260816-180914_skip_design.md) | Tick #20260816-18 (18:07): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告. 队列已有  |
| 2026-08-16 19:10:40 | [skip_design](20260816-191040_skip_design.md) | Tick #20260816-19 (19:07): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告. 队列已有  |
| 2026-08-16 20:10:07 | [skip_design](20260816-201007_skip_design.md) | Tick #20260816-20 (20:07): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告. 队列已有  |
| 2026-08-16 21:09:22 | [skip_design](20260816-210922_skip_design.md) | Tick #20260816-21 (21:07): 队列深度 waiting=7 vs 容量5 | 跳过自主设计. 本 tick 仅监控+报告. 队列已有  |
| 2026-08-16 22:09:26 | [skip_design](20260816-220926_skip_design.md) | Tick #20260816-22: 队列深度 waiting=7 vs 容量4+1=5 (se | 跳过自主设计. 本 tick 仅监控+报告. 队列已有  |
| 2026-08-16 23:08:37 | [skip_design](20260816-230837_skip_design.md) | Tick #20260816-23 (23:07): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4 running (M9 |
| 2026-08-17 00:09:01 | [skip_design](20260817-000901_skip_design.md) | Tick #20260817-00 (00:08): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-17 01:07:24 | [early_stop](20260817-010724_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_champ_s42] 连续 11 次验 | kill PID=3314894 on server-4 gpu=1 |
| 2026-08-17 01:11:40 | [queue_push](20260817-011140_queue_push.md) | server-4 gpu1 空闲（M99-CHAMP-S42 早停释放），推� | 启动 M101-CHAMP-S2026 configs/Quard/champ_s2026/model_base |
| 2026-08-17 01:11:43 | [terminal](20260817-011143_terminal.md) | M99-CHAMP-S42 (champion 基底 seed=42) 早停终态 Best=0. | 判定 done_earlystop, 生成 analyses/M99-CHAMP-S42_done_ea |
| 2026-08-17 01:11:48 | [skip_design](20260817-011148_skip_design.md) | Tick #20260817-01: 队列深度判定 waiting=? vs 容量5+1 | 跳过自主设计. 本 tick 仅监控+早停+推送+终态� |
| 2026-08-17 01:16:16 | [early_stop](20260817-011616_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_champ_s123] 连续 11 次 | kill PID=61486 on server-4 gpu=0 |
| 2026-08-17 02:07:34 | [queue_push](20260817-020734_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M102 CTF×HCG seed=2026 (唯一 tie 机制第三 seed 点, 破顶真实性判定)] co |
| 2026-08-17 02:13:53 | [next_batch](20260817-021353_next_batch.md) | 队列深度不足 (waiting=5 < 可用槽5+1=6); champion-ba | 入队 M107-CHAMP-CSORT-S123 + M108-CHAMP-CSORT-S2026 (confi |
| 2026-08-17 02:14:36 | [terminal](20260817-021436_terminal.md) | M100-CHAMP-S123 早停终态 (Best=0.4982@16/22), 是否生� | 判定 done_earlystop, 生成 pipeline/analyses/M100-CHAMP-S |
| 2026-08-17 03:09:30 | [skip_design](20260817-030930_skip_design.md) | Tick #20260817-03: 队列深度判定 waiting=7 vs 可用槽 | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-17 04:09:13 | [skip_design](20260817-040913_skip_design.md) | Tick #20260817-04 (04:08): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-17 05:08:59 | [skip_design](20260817-050859_skip_design.md) | Tick #20260817-05 (05:07): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-17 06:09:45 | [skip_design](20260817-060945_skip_design.md) | Tick #20260817-06: 队列深度判定 waiting=7 vs 容量4+1 | 跳过自主设计. 本 tick 仅监控+报告: 无新终态/ |
| 2026-08-17 07:08:47 | [skip_design](20260817-070847_skip_design.md) | Tick #20260817-07 (07:07): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-17 08:09:30 | [skip_design](20260817-080930_skip_design.md) | Tick #20260817-08 (08:08): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4/4 容量槽 |
| 2026-08-17 09:09:38 | [skip_design](20260817-090938_skip_design.md) | Tick #20260817-09 (09:09): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4 running (M1 |
| 2026-08-17 10:09:07 | [skip_design](20260817-100907_skip_design.md) | Tick #20260817-10 (10:07): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告. 队列已有  |
| 2026-08-17 11:09:13 | [skip_design](20260817-110913_skip_design.md) | Tick #20260817-11 (11:08): 队列深度判定 waiting=7 vs � | 跳过自主设计. 本 tick 仅监控+报告: 4 running (M1 |
| 2026-08-17 12:08:43 | [skip_design](20260817-120843_skip_design.md) | Tick #20260817-12 (12:07): 队列深度判定 waiting=7 vs � | 跳过自主设计。继续监控 4 running (M101/M102/M86/M |
| 2026-08-17 13:07:25 | [early_stop](20260817-130725_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_s2026] 连续 1 | kill PID=2199215 on server-4 gpu=0 |
| 2026-08-17 13:10:22 | [terminal](20260817-131022_terminal.md) | M102-CTF-HCG-S2026 早停终态 Best=0.4920@21/50 (no_improv | 判定 done_earlystop, 生成 pipeline/analyses/M102-CTF-HCG |
| 2026-08-17 13:10:24 | [queue_push](20260817-131024_queue_push.md) | server-4 GPU0 空闲 (M102 早停释放, util=0% mem=41MiB), | 启动 [M103-CTF-HCG-CSORT-S2026] configs/Quard/ctf_hcg_csor |
| 2026-08-17 13:10:51 | [skip_design](20260817-131051_skip_design.md) | Tick #20260817-13: 队列深度判定 waiting=6 vs 容量4+1 | 跳过自主设计 (Phase 0-4). 本 tick 仅监控+早停(M1 |
| 2026-08-17 14:08:56 | [skip_design](20260817-140856_skip_design.md) | Tick #20260817-14 (14:08): 队列深度判定 waiting=6 vs � | 跳过自主设计 (Phase 0-4). 本 tick 仅监控+报告: 4 |
| 2026-08-17 15:08:37 | [skip_design](20260817-150837_skip_design.md) | Tick #20260817-15 (15:07): 队列深度判定 waiting=6 vs � | 跳过自主设计 (Phase 0-4). 本 tick 仅监控+报告: 4 |
| 2026-08-17 16:10:44 | [skip_design](20260817-161044_skip_design.md) | Tick #20260817-16: 队列深度判定 waiting=6 vs 容量4+1 | 跳过自主设计 (Phase 0-4). 本 tick 仅监控+报告+� |
| 2026-08-17 17:08:26 | [skip_design](20260817-170826_skip_design.md) | Tick #20260817-17 (17:08): 队列深度判定 waiting=6 vs � | 跳过自主设计 (Phase 0-4). 本 tick 仅监控+报告. � |
| 2026-08-17 18:08:49 | [skip_design](20260817-180849_skip_design.md) | Tick #20260817-18: 队列深度判定 waiting=6 vs 容量4+1 | 跳过自主设计 (Phase 0-4). 本 tick 仅监控+报告. � |
| 2026-08-17 19:09:03 | [skip_design](20260817-190903_skip_design.md) | Tick #20260817-19 (19:07): 队列深度判定 waiting=6 vs � | 跳过自主设计 (Phase 0-4). 本 tick 仅监控+报告. � |
| 2026-08-17 20:08:38 | [skip_design](20260817-200838_skip_design.md) | Tick #20260817-20 (20:07): 队列深度判定 waiting=6 vs � | 跳过自主设计 (Phase 0-4). 本 tick 仅监控+报告. � |
| 2026-08-17 21:08:59 | [skip_design](20260817-210859_skip_design.md) | Tick #20260817-21 (21:07): 队列深度判定 waiting=6 vs � | 跳过自主设计. 本 tick 仅监控+报告. 队列已有  |
| 2026-08-17 22:09:23 | [skip_design](20260817-220923_skip_design.md) | Tick #20260817-22 (22:07): 队列深度判定 waiting=6 vs � | 跳过自主设计. 本 tick 仅监控+报告. 队列已有  |
| 2026-08-17 22:16:18 | [early_stop](20260817-221618_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_champ_s2026] 连续 11  | kill PID=2081272 on server-4 gpu=1 |
| 2026-08-17 23:07:42 | [queue_push](20260817-230742_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M104 CTF×HCG×CSORT seed=42 (同 seed 对照 vs M89=0.4980, 测 C |
| 2026-08-17 23:10:52 | [terminal](20260817-231052_terminal.md) | M101-CHAMP-S2026 早停终态 Best=0.4920@17/22 (no_improve= | 判定 done_earlystop, 生成 pipeline/analyses/M101-CHAMP-S |
| 2026-08-17 23:11:33 | [skip_design](20260817-231133_skip_design.md) | Tick #20260817-23 (23:07): 队列深度判定 waiting=5 vs � | 跳过自主设计 (Phase 0-4). 本 tick 仅监控+报告+� |
| 2026-08-18 00:17:45 | [next_batch](20260818-001745_next_batch.md) | 队列深度不足 (waiting=5 < 可用槽5+1=6), CSORT 跨 s | 设计并入队 M109-CSORT-MSG (configs/Quard/csort_msg/, cl |
| 2026-08-18 00:17:50 | [code_sync](20260818-001750_code_sync.md) | M109-CSORT-MSG 新 model 包+config 需同步到哪些服务 | git commit 9e7ad85 → sync.sh server-4 + server-6 (rsync � |
| 2026-08-18 01:09:42 | [skip_design](20260818-010942_skip_design.md) | Tick #20260818-01 (01:07): 队列深度判定 waiting=6 vs � | 跳过自主设计 (Phase 0-4). 本 tick 仅监控+报告: 4 |
| 2026-08-18 02:08:56 | [skip_design](20260818-020856_skip_design.md) | Tick #20260818-02 (02:07): 队列深度判定 waiting=6 vs � | 跳过自主设计 (Phase 0-4). 本 tick 仅监控+报告: 4 |
| 2026-08-18 08:37:28 | [queue_push](20260818-083728_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M105 CTF×HCG×CSORT seed=123 (同 seed 对照 vs M90=0.4940, 测  |
| 2026-08-18 08:38:18 | [queue_push](20260818-083818_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M98 champion-base cross-scale ORT (isolate CSORT on cham |
| 2026-08-18 16:38:32 | [early_stop](20260818-163832_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_s42]  | kill PID=1041778 on server-4 gpu=1 |
| 2026-08-18 18:38:39 | [queue_push](20260818-183839_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M106 champion-base CSORT seed=42 (同 seed 对照 vs M99 champ |
| 2026-08-18 20:38:24 | [early_stop](20260818-203824_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_s123] | kill PID=2466308 on server-4 gpu=0 |
| 2026-08-18 20:38:39 | [queue_push](20260818-203839_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M107 champion-base CSORT seed=123 (同 seed 对照 vs M100 cha |
| 2026-08-18 22:38:37 | [queue_push](20260818-223837_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M108 champion-base CSORT seed=2026 (同 seed 对照 vs M101 ch |
| 2026-08-18 22:38:50 | [queue_push](20260818-223850_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M109 readback message-level cross-scale decorrelation (v |
| 2026-08-19 08:37:12 | [early_stop](20260819-083712_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_csort_msg] 连续 11 次验 | kill PID=394754 on server-4 gpu=1 |
| 2026-08-19 11:35:14 | [next_batch](20260819-113514_next_batch.md) | 队列深度0<6, CSORT跨seed证伪(3/4负), 需新结构方 | 设计M110-CTF-HCG-MEMBANK(memory bank跨batch记忆)+M111-C |
| 2026-08-19 11:35:17 | [route_change](20260819-113517_route_change.md) | CSORT跨4个seed验证: s1999=0.5020(+0.004), s2026=0.4902(- | CSORT轴正式关闭, M95=0.5020归因seed1999有利性, 非 |
| 2026-08-19 11:35:31 | [other](20260819-113531_other.md) | M103/M104/M105/M109缺失终态分析  | 生成4个终态分析: M103(CSORT-s2026=0.4902), M104(CSORT |
| 2026-08-19 11:39:12 | [queue_push](20260819-113912_queue_push.md) | server-4 gpu0 空闲，推送哪个排队实验？ | 尝试启动 [M110 CTF-HCG + Cluster Memory Bank (cross-batch EMA pr |
| 2026-08-19 11:39:32 | [queue_push](20260819-113932_queue_push.md) | server-4 gpu1 空闲，推送哪个排队实验？ | 尝试启动 [M111 CTF-HCG + Spatial Reconstruction Loss (cluster to |
| 2026-08-19 11:39:41 | [next_batch](20260819-113941_next_batch.md) | 队列深度0<5(可用卡4+1), CSORT跨seed证伪后队列� | 补完M110-MEMBANK+M111-SRL实现, 新增M112-MEMBANK-S42+M1 |
| 2026-08-19 11:43:56 | [other](20260819-114356_other.md) | M110+M111代码同步到server-4和server-6  | git commit 6dbdd25 → sync.sh server-4 + server-6 (rsync vi |
| 2026-08-19 11:44:53 | [queue_push](20260819-114453_queue_push.md) | server-4 GPU0+GPU1 idle, queue has M110-MEMBANK+M111-SRL wai | Launch M110-CTF-HCG-MEMBANK on server-4 GPU0 + M111-CTF-HCG- |
| 2026-08-19 11:44:56 | [code_sync](20260819-114456_code_sync.md) | M110-MEMBANK+M111-SRL+seed variants committed (b2805f3), nee | sync.sh server-4 + server-6, HEAD=b2805f3, 40 files (5 confi |
| 2026-08-19 11:52:19 | [next_batch](20260819-115219_next_batch.md) | 队列深度0<6, M110/M111刚启动, 需新结构方向补� | 设计M112-CCL(cluster contrastive loss)+M113-CGA(cluster gr |
| 2026-08-19 11:52:22 | [other](20260819-115222_other.md) | M110/M111 crash自修复(retry #2): config文件存在但前 | 手动启动M110-membank(server-4 GPU0 PID=2370356)+M111-srl |
| 2026-08-19 11:55:16 | [code_sync](20260819-115516_code_sync.md) | M112-CCL+M113-CGA 新 model 包+config 需同步到哪些服 | git commit e469082 → sync.sh server-4 + server-6 (rsync vi |
| 2026-08-19 11:58:36 | [next_batch](20260819-115836_next_batch.md) | 队列深度不足(3<5=可用槽4+1), 上一tick设计了CCL | 入队M115-CCL+M116-CGA+M117-BCF到server-4 queue, 复用CCL |
| 2026-08-19 12:02:59 | [code_sync](20260819-120259_code_sync.md) | M115-CCL+M116-CGA+M117-BCF model包+config需同步到server | git commit 9b7a147 → sync.sh server-4 + server-6 (HEAD=9b7 |
| 2026-08-19 12:05:30 | [monitor](20260819-120530_monitor.md) | 队列6 waiting ≥ 4+1=5, 4个running正常, 是否需要� | 跳过自主设计, 无终态分析. 继续监控M110/M111(� |
| 2026-08-19 14:10:30 | [monitor](20260819-141030_monitor.md) | 队列6 waiting vs 可用槽5+1=6, M110/M111 running正常,  | 跳过自主设计(Phase 0-4), 继续监控running实验  |
| 2026-08-19 15:09:20 | [skip_design](20260819-150920_skip_design.md) | Queue depth 6≥5(4槽+1), 4 running experiments active, all | Skip autonomous design. Continue monitoring M86-MLAY(0.4960, |
| 2026-08-19 16:10:12 | [skip_design](20260819-161012_skip_design.md) | Queue depth 6≥5(4 capacity+1), 4 running experiments activ | Skip autonomous design. Continue monitoring M86-MLAY(0.4960, |
| 2026-08-19 17:09:14 | [monitor](20260819-170914_monitor.md) | Queue 6 waiting vs capacity 5+1, 4 running active, any new t | Skip autonomous design (Phase 0-4), continue monitoring. No  |
| 2026-08-19 18:09:36 | [skip_design](20260819-180936_skip_design.md) | Queue depth 6≥6 (5 capacity+1), 4 running experiments acti | Skip autonomous design (Phase 0-4), continue monitoring runn |
| 2026-08-19 19:09:34 | [skip_design](20260819-190934_skip_design.md) | Queue depth 6>=6 (5 capacity+1), 4 running experiments activ | Skip autonomous design (Phase 0-4), continue monitoring runn |
| 2026-08-19 20:09:38 | [skip_design](20260819-200938_skip_design.md) | Queue depth 6>=6 (5 capacity+1), 4 running experiments activ | Skip autonomous design (Phase 0-4). Continue monitoring M110 |
| 2026-08-19 21:10:15 | [skip_design](20260819-211015_skip_design.md) | Queue depth 6>=5 (4 capacity+1), 4 running experiments activ | Skip autonomous design (Phase 0-4). Continue monitoring M110 |
| 2026-08-19 22:09:06 | [skip_design](20260819-220906_skip_design.md) | Queue depth 6>=6 (5 capacity+1), 4 running experiments activ | Skip autonomous design (Phase 0-4). Continue monitoring M110 |
| 2026-08-19 23:09:23 | [skip_design](20260819-230923_skip_design.md) | Queue depth 6≥6 (5 capacity+1), 4 running active, Phase 1  | Skip autonomous design, continue monitoring  |
| 2026-08-20 00:09:11 | [skip_design](20260820-000911_skip_design.md) | Tick #20260820-00: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4). 继续监控4个running实� |
| 2026-08-20 01:09:21 | [skip_design](20260820-010921_skip_design.md) | Tick #20260820-01: 队列深度判定 waiting=6 vs 容量4+1 | 跳过自主设计 (Phase 0-4). 继续监控4个running实� |
| 2026-08-20 02:07:32 | [early_stop](20260820-020732_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_membank] 连续 | kill PID=2370356 on server-4 gpu=0 |
| 2026-08-20 02:09:41 | [early_stop](20260820-020941_early_stop.md) | M110-CTF-HCG-MEMBANK 连续13次验证未刷新Best (0.4950@ | monitor kill PID=2370356 on server-4 gpu=0, 标记done_early |
| 2026-08-20 02:09:45 | [skip_design](20260820-020945_skip_design.md) | Tick #20260820-02: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4). 继续监控3个running实� |
| 2026-08-20 02:37:28 | [queue_push](20260820-023728_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M112 MEMBANK seed=42 control (vs M110 seed=1999)] config |
| 2026-08-20 03:09:39 | [skip_design](20260820-030939_skip_design.md) | Tick #20260820-03: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4). 继续监控4个running实� |
| 2026-08-20 04:10:23 | [skip_design](20260820-041023_skip_design.md) | Tick #20260820-04: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4). 继续监控4个running实� |
| 2026-08-20 05:09:33 | [skip_design](20260820-050933_skip_design.md) | Tick #20260820-05: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4). 继续监控4个running实� |
| 2026-08-20 06:09:52 | [monitor](20260820-060952_monitor.md) | Tick #20260820-06: 队列深度判定 waiting=5 vs 容量5,  | 跳过自主设计 (Phase 0-4). 继续监控running实验. M |
| 2026-08-20 07:18:46 | [next_batch](20260820-071846_next_batch.md) | 队列深度5=4+1(刚好达标), 需补1个新方向  | 设计并入队 M118-CTF-HCG-LCC (Language-Conditioned Clust |
| 2026-08-20 07:18:54 | [code_sync](20260820-071854_code_sync.md) | M118-LCC model包+config需同步到server-4+server-6  | git commit 9ed59d4 → rsync server-4(本地)+server-6 (fram |
| 2026-08-20 08:07:39 | [early_stop](20260820-080739_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_champ_ort] 连续 11 次验 | kill PID=1934356 on server-6 gpu=7 |
| 2026-08-20 08:12:02 | [skip_design](20260820-081202_skip_design.md) | Tick #20260820-08: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4). 继续监控M112-MEMBANK-S42 |
| 2026-08-20 09:11:04 | [skip_design](20260820-091104_skip_design.md) | Tick #20260820-09: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4). 继续监控3个running实� |
| 2026-08-20 11:09:58 | [skip_design](20260820-110958_skip_design.md) | Tick #20260820-11: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4). 继续监控3个running实� |
| 2026-08-20 12:09:33 | [skip_design](20260820-120933_skip_design.md) | Tick 20260820-12: 队列深度6≥6(5容量+1), 3 running ac | 跳过自主设计。M86-MLAY(0.5010)距champion 0.5020仅0. |
| 2026-08-20 13:09:57 | [skip_design](20260820-130957_skip_design.md) | 队列深度判定 waiting=6 vs 容量5+1=6, 3 running activ | 跳过自主设计 (Phase 0-4). 继续监控3个running实� |
| 2026-08-20 14:07:35 | [early_stop](20260820-140735_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_srl] 连续 11  | kill PID=2366241 on server-4 gpu=1 |
| 2026-08-20 14:21:44 | [queue_push](20260820-142144_queue_push.md) | server-4 gpu1 空闲 (M111-SRL 早停后释放), 推送哪� | 启动 M113-SRL-S42 (SRL seed=42 对照) configs/Quard/ctf_h |
| 2026-08-20 14:22:05 | [next_batch](20260820-142205_next_batch.md) | M110-MEMBANK(0.4954) 和 M111-SRL(0.4912) 均早停完成, � | 生成 M110 和 M111 的终态分析文档; M110: memory ban |
| 2026-08-20 15:11:38 | [skip_design](20260820-151138_skip_design.md) | 队列深度判定 waiting=5 vs 容量5+1=6, 3 running activ | 跳过自主设计 (Phase 0-4). 继续监控3个running实� |
| 2026-08-20 15:13:06 | [other](20260820-151306_other.md) | 队列深度 borderline: waiting=5 vs capacity+1=6, 差1但� | 跳过补第6个变体: 队列5个实验(M114-M118)覆盖see |
| 2026-08-20 16:07:28 | [early_stop](20260820-160728_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_membank_s42 | kill PID=119387 on server-4 gpu=0 |
| 2026-08-20 17:42:57 | [next_batch](20260820-174257_next_batch.md) | 队列深度 waiting=4 < 可用卡5+1=6, Phase 1 NOT YET (ch | 设计并入队 M119-CTF-HCG-MFP (masked feature prediction) |
| 2026-08-20 17:43:02 | [code_sync](20260820-174302_code_sync.md) | M119-MFP 新model包+config需同步到哪些服务器? 注� | rebase MFP commit到FETCH_HEAD(含LCC 9ed59d4), branch -f ma |
| 2026-08-20 18:07:30 | [early_stop](20260820-180730_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_mlay] 连续 11 次验证未刷新  | kill PID=1580735 on server-6 gpu=7 |
| 2026-08-20 18:15:19 | [next_batch](20260820-181519_next_batch.md) | 队列深度 waiting=5 ≤ 可用卡5, M86-MLAY(2层legacy)= | 设计并入队 M120-MLAY-S42(seed=42对照验证稳健性)  |
| 2026-08-20 18:15:20 | [code_sync](20260820-181520_code_sync.md) | M120 mlay_s42 新model包+config需同步到哪些服务器? | git commit 6c196fc → sync.sh server-4(已验文件存在)  |
| 2026-08-20 18:37:33 | [queue_push](20260820-183733_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M120 MLay(2层legacy) seed=42 control — 验证 M86=0.5010 seed |
| 2026-08-20 18:37:50 | [queue_push](20260820-183750_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M121 MLay(2层) x detail message — 2条独立有效机制叠加测试 (2层=0.5010 |
| 2026-08-20 19:34:02 | [next_batch](20260820-193402_next_batch.md) | 队列深度 waiting=5 < 容量5+1=6, MLay(2层legacy) 单 s | 设计并入队 M122-MLAY-S123 (MLay seed=123 对照) 到 se |
| 2026-08-20 19:34:06 | [code_sync](20260820-193406_code_sync.md) | M122-MLAY-S123 新model包+config需同步到哪些服务器 | git commit 93d82f6 → sync.sh server-4(已验文件存在)  |
| 2026-08-20 20:09:39 | [skip_design](20260820-200939_skip_design.md) | tick#4 队列深度 6 waiting (server-4: M115-M119 x5; serve | 跳过设计, 保持队列 6 waiting 不变, 本轮仅监控 |
| 2026-08-20 21:08:34 | [skip_design](20260820-210834_skip_design.md) | Tick #20260820-21: 队列深度 6 waiting (server-4: M115-M1 | 跳过设计, 保持队列 6 waiting 不变, 本轮仅监控 |
| 2026-08-20 22:10:25 | [skip_design](20260820-221025_skip_design.md) | Tick #20260820-22: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4). 继续监控 4 个 running � |
| 2026-08-20 23:09:23 | [skip_design](20260820-230923_skip_design.md) | 队列深度判定 waiting=6 vs 容量5+1=6, 4 running activ | 跳过自主设计 (Phase 0-4). 继续监控 4 个 running � |
| 2026-08-21 00:09:00 | [skip_design](20260821-000900_skip_design.md) | 队列深度判定 waiting=6 vs 容量5+1=6, 4 running activ | 跳过自主设计 (Phase 0-4). 继续监控 4 个 running � |
| 2026-08-21 01:10:17 | [skip_design](20260821-011018_skip_design.md) | Tick #20260821-01: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4). 继续监控 4 个 running � |
| 2026-08-21 02:09:19 | [skip_design](20260821-020919_skip_design.md) | Tick #20260821-02: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4). 保持队列 6 waiting 不� |
| 2026-08-21 03:10:06 | [skip_design](20260821-031006_skip_design.md) | Tick #20260821-03: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4). 继续监控 4 个 running � |
| 2026-08-21 04:10:14 | [skip_design](20260821-041014_skip_design.md) | Tick #20260821-04: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4). 继续监控 4 个 running � |
| 2026-08-21 04:37:12 | [early_stop](20260821-043712_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_membank_s12 | kill PID=1758872 on server-4 gpu=0 |
| 2026-08-21 05:07:36 | [queue_push](20260821-050736_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M115 CTF-HCG + Cluster Contrastive Loss (InfoNCE cross-s |
| 2026-08-21 05:30:48 | [next_batch](20260821-053048_next_batch.md) | 队列深度 waiting=5 < 容量5+1=6, 触发自主设计; ~0 | 设计并入队 M123-CTF-HCG-DCA (configs/Quard/ctf_hcg_dca/ |
| 2026-08-21 05:30:54 | [terminal](20260821-053054_terminal.md) | M114-MEMBANK-S123 early-stopped @22/50 Best=0.5010 (no_impro | 判定 done_earlystop, 生成 pipeline/analyses/M114-MEMBANK |
| 2026-08-21 05:30:55 | [queue_push](20260821-053055_queue_push.md) | server-4 gpu0 空闲 (M114-MEMBANK-S123 early-stop 释放),  | monitor 自动推送 [M115-CTF-HCG-CCL] configs/Quard/ctf_hc |
| 2026-08-21 06:10:37 | [skip_design](20260821-061037_skip_design.md) | Tick 20260821-06: 队列深度 waiting=6 vs 可用卡数4-5+ | 跳过自主设计 (Phase 0-4)。仅监控 4 个 running 实 |
| 2026-08-21 06:37:10 | [early_stop](20260821-063710_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_srl_s42] 连续 | kill PID=1535099 on server-4 gpu=1 |
| 2026-08-21 07:07:37 | [queue_push](20260821-070737_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M116 CTF-HCG + Cluster Graph Attention (KNN graph over c |
| 2026-08-21 07:18:45 | [next_batch](20260821-071845_next_batch.md) | 队列深度 waiting=5 < 容量5+1=6, 触发自主设计; M1 | 设计并入队 M124-CTF-HCG-DCM (configs/Quard/ctf_hcg_dcm/ |
| 2026-08-21 07:18:49 | [code_sync](20260821-071849_code_sync.md) | M124-DCM 新model包+config需同步到哪些服务器?  | git commit f01d3b0 → sync.sh server-4(192.168.1.137)+serve |
| 2026-08-21 07:19:27 | [terminal](20260821-071927_terminal.md) | M113-SRL-S42 early-stopped @25/50 Best=0.4920 (no_improve=11 | 判定 done_earlystop, 生成 pipeline/analyses/M113-SRL-S42 |
| 2026-08-21 07:25:51 | [bugfix](20260821-072551_bugfix.md) | M116-CGA 启动即 crash (fill_diagonal_ 3D tensor, torch 2. | 修复 _build_adj_mask: fill_diagonal_ → eye-mask masked_f |
| 2026-08-21 08:08:15 | [skip_design](20260821-080815_skip_design.md) | Tick #20260821-08: 队列深度判定 waiting=6 (server-4: M | 跳过自主设计 (Phase 0-4). 保持队列 6 waiting 不� |
| 2026-08-21 09:10:51 | [skip_design](20260821-091051_skip_design.md) | Tick #20260821-09: 队列深度判定 waiting=6 (server-4: M | 跳过自主设计 (Phase 0-4). 保持队列 6 waiting 不� |
| 2026-08-21 10:11:39 | [skip_design](20260821-101139_skip_design.md) | Tick 20260821-10: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4). 继续监控 4 个 running � |
| 2026-08-21 11:08:37 | [skip_design](20260821-110837_skip_design.md) | 队列深度判定 waiting=6 vs 容量4+1=5, 是否触发自 | 跳过自主设计 (Phase 0-4)。继续监控 4 个 running  |
| 2026-08-21 12:08:29 | [queue_push](20260821-120829_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M122 MLay(2层legacy) seed=123 control — 补 MLay seed 矩阵第3点 |
| 2026-08-21 12:16:52 | [skip_design](20260821-121652_skip_design.md) | Tick #20260821-12: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4). 深度恰好达标 waiting=5 |
| 2026-08-21 13:13:20 | [other](20260821-131320_other.md) | server-6 GPU7 3任务超容量2 (M120/M121/M122 并发), ite | kill M122-MLAY-S123 (PID 1792703+workers), 重置 queue.json |
| 2026-08-21 13:13:21 | [skip_design](20260821-131321_skip_design.md) | Tick #20260821-13: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4). 队列深度恰好达标 wai |
| 2026-08-21 14:17:58 | [skip_design](20260821-141758_skip_design.md) | Tick #20260821-14: 队列深度判定 waiting=6 (server-4 M1 | 跳过自主设计 (Phase 0-4). 队列深度充足 waiting=6 |
| 2026-08-21 14:18:00 | [other](20260821-141800_other.md) | Tick #20260821-14: M120/M121 (server-6 GPU7 2并跑) 日志  | 判定非 wedge: 服务器时区为 UTC, 日志 mtime 06:16  |
| 2026-08-21 14:18:24 | [question](20260821-141824_question.md) | server-6 GPU7 2任务并跑 iter_time 6.27/6.53 s/it (ETA 16 | 留待用户确认. 本轮不改配置: 维持 max_tasks_per |
| 2026-08-21 15:09:58 | [skip_design](20260821-150958_skip_design.md) | Tick 20260821-15: 队列深度 waiting=6 vs 容量4+1=5, 4� | 跳过自主设计 (Phase 0-4). 队列深度充足 (6≥5),  |
| 2026-08-21 16:09:14 | [skip_design](20260821-160915_skip_design.md) | 队列深度判定 waiting=6 vs 容量4+1=5, 4 running activ | 跳过自主设计 (Phase 0-4). 队列深度充足 (6≥5),  |
| 2026-08-21 17:07:26 | [early_stop](20260821-170726_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_ccl] 连续 11  | kill PID=3382466 on server-4 gpu=0 |
| 2026-08-21 17:09:36 | [queue_push](20260821-170936_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M117 CTF-HCG + Bidirectional Context Flow (point→cluster |
| 2026-08-21 17:11:07 | [terminal](20260821-171107_terminal.md) | M115-CTF-HCG-CCL (Cluster Contrastive Loss) early-stopped @2 | M115 → done_earlystop, 生成 terminal analysis (analyses/ |
| 2026-08-21 17:11:33 | [skip_design](20260821-171133_skip_design.md) | Tick #20260821-17: 队列深度判定 waiting=5 (server-4: M | 跳过自主设计 (Phase 0-4). 队列深度恰好达标 (wa |
| 2026-08-21 17:17:10 | [bugfix](20260821-171710_bugfix.md) | M117-BCF 推送 server-4 gpu0 首步训练 CUDA OOM (31.30/3 | 根因=BCF 逐簇 padding MHA (1500 次带图调用); 修复 |
| 2026-08-21 17:17:34 | [queue_push](20260821-171734_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M117 CTF-HCG + Bidirectional Context Flow (point→cluster |
| 2026-08-21 18:14:26 | [skip_design](20260821-181426_skip_design.md) | 队列深度判定 waiting=5 vs 容量4+1=5 (server-4: M118- | 跳过自主设计 (Phase 0-4). 深度恰好达标 (waiting= |
| 2026-08-21 18:14:35 | [other](20260821-181435_other.md) | Tick #20260821-18 检查 4 个 running 是否有 crash/early | 无需处理: M116-CGA(13/50), M117-BCF(2/50), M120-MLAY-S42 |
| 2026-08-21 19:11:32 | [skip_design](20260821-191132_skip_design.md) | 队列深度判定 waiting=5 vs 容量4+1=5 (server-4: M118/ | 跳过自主设计 (Phase 0-4). 深度恰好达标 (waiting= |
| 2026-08-21 19:11:33 | [other](20260821-191133_other.md) | Tick #20260821-19 检查 4 个 running 是否有 crash/early | 无需处理: M116-CGA(14/50,0.4840), M117-BCF(4/50,0.4160), |
| 2026-08-21 20:09:20 | [other](20260821-200920_other.md) | Tick #20260821-20: 4 running 健康推进? 有无 crash/earl | 无需处理: M116-CGA(15/50,0.4850), M117-BCF(6/50,0.4600), |
| 2026-08-21 21:09:57 | [skip_design](20260821-210957_skip_design.md) | Tick #20260821-21: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 4 个 |
| 2026-08-21 22:09:02 | [skip_design](20260821-220902_skip_design.md) | Tick #20260821-22: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 4 个 |
| 2026-08-21 23:09:09 | [skip_design](20260821-230909_skip_design.md) | Tick #20260821-23: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M116/ |
| 2026-08-22 00:10:48 | [skip_design](20260822-001048_skip_design.md) | Tick #20260822-00: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 4 个 |
| 2026-08-22 01:10:22 | [skip_design](20260822-011022_skip_design.md) | Tick #20260822-01: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 4 个 |
| 2026-08-22 02:13:41 | [skip_design](20260822-021341_skip_design.md) | Tick #20260822-02: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 4 个 |
| 2026-08-22 03:07:24 | [early_stop](20260822-030724_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_bcf] 连续 11  | kill PID=805930 on server-4 gpu=0 |
| 2026-08-22 03:07:29 | [early_stop](20260822-030729_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_cga] 连续 11  | kill PID=3692574 on server-4 gpu=1 |
| 2026-08-22 03:13:21 | [queue_push](20260822-031321_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M118 CTF-HCG + Language-Conditioned Cluster Context (clu |
| 2026-08-22 03:13:35 | [queue_push](20260822-031335_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M119 CTF-HCG + Masked Feature Prediction (feature-level  |
| 2026-08-22 03:27:21 | [next_batch](20260822-032721_next_batch.md) | 队列深度 waiting=3 (M123/M124/M122) < 容量4+1=5, 需� | 设计 M125-MLAY-DCA (2层legacy×DCA专用分支) + M126-ML |
| 2026-08-22 04:09:49 | [skip_design](20260822-040949_skip_design.md) | Tick 20260822-04: 队列深度 waiting=5 vs 容量4+1=5, 是 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M118/ |
| 2026-08-22 05:10:08 | [skip_design](20260822-051008_skip_design.md) | Tick 20260822-05: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M118/ |
| 2026-08-22 06:08:33 | [queue_push](20260822-060833_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M122 MLay(2层legacy) seed=123 control — 补 MLay seed 矩阵第3点 |
| 2026-08-22 06:17:19 | [other](20260822-061719_other.md) | server-6 GPU7 已满(M120/M121 running, max_tasks_per_gpu=2) | kill M122 (PID 3242143) 并重置 waiting; GPU7 恢复 M120/ |
| 2026-08-22 06:19:34 | [other](20260822-061934_other.md) | monitor 06:07 对 server-6 报告'无训练进程'并将 M12 | 确认 false negative: M120(mlay_s42 PID4038426) 与 M121(de |
| 2026-08-22 07:16:24 | [next_batch](20260822-071624_next_batch.md) | 队列深度 waiting=5 < 可用槽5+1=6 触发自主设计;  | 入队 M127-DET-DCA + M128-DET-DCM (cluster_message_type=det |
| 2026-08-22 08:08:34 | [skip_design](20260822-080834_skip_design.md) | Tick 20260822-08: 队列深度判定 waiting=7 vs 容量5+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 4 个 |
| 2026-08-22 09:08:58 | [skip_design](20260822-090858_skip_design.md) | Tick 20260822-09: 队列深度判定 waiting=7 vs 容量5+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 4 个 |
| 2026-08-22 10:11:35 | [skip_design](20260822-101135_skip_design.md) | Tick 20260822-10: 队列深度判定 waiting=7 vs 容量5+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M118/ |
| 2026-08-22 11:11:55 | [skip_design](20260822-111155_skip_design.md) | Tick #20260822-11: 队列深度判定 waiting=7 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 队列深度充足 |
| 2026-08-22 12:11:02 | [skip_design](20260822-121102_skip_design.md) | Tick 20260822-12: 队列深度 waiting=7 vs 容量4+1=5, 是 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M118/ |
| 2026-08-22 13:10:24 | [skip_design](20260822-131024_skip_design.md) | Tick 20260822-13: 队列深度判定 waiting=7 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 队列深度充足 |
| 2026-08-22 14:13:21 | [skip_design](20260822-141321_skip_design.md) | Tick #20260822-14: 队列深度判定 waiting=7 (server-4: M | 跳过自主设计 (Phase 0-4 不触发). 队列深度充足 |
| 2026-08-22 15:11:21 | [skip_design](20260822-151121_skip_design.md) | 队列深度判定 waiting=7 vs 容量4+1=5, 是否触发自 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M118/ |
| 2026-08-22 16:08:46 | [early_stop](20260822-160846_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_lcc] 连续 11  | kill PID=2060615 on server-4 gpu=0 |
| 2026-08-22 16:11:08 | [queue_push](20260822-161108_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M123 Decoder Cluster Cross-Attention (decoder query dire |
| 2026-08-22 16:13:11 | [skip_design](20260822-161311_skip_design.md) | Tick #20260822-16: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 runni |
| 2026-08-22 16:13:18 | [terminal](20260822-161318_terminal.md) | M118-LCC 早停完成 (Best=0.4950@ep~13, no_improve=11/10,  | 手动生成 pipeline/analyses/M118-CTF-HCG-LCC_done_earlyst |
| 2026-08-22 17:08:25 | [early_stop](20260822-170825_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_mfp] 连续 11  | kill PID=2062141 on server-4 gpu=1 |
| 2026-08-22 17:13:37 | [queue_push](20260822-171337_queue_push.md) | M119-MFP 早停 kill 释放 server-4 gpu1 (0%, 15MiB), 推� | 启动 [M124 Decoder Cluster Memory: decoder qla KV extended |
| 2026-08-22 17:16:28 | [terminal](20260822-171628_terminal.md) | M119-MFP 早停完成 (Best=0.5020@ep~15, no_improve=11/10)  | 判定 done_earlystop, 生成 terminal analysis; MFP 持平  |
| 2026-08-22 17:22:04 | [next_batch](20260822-172204_next_batch.md) | 队列深度不足 (waiting=5 < 可用卡5+1=6); M119-MFP � | 入队 M129-MFP-S42 + M130-MFP-S123 (config-only seed 对照 |
| 2026-08-22 17:22:08 | [code_sync](20260822-172208_code_sync.md) | M129-MFP-S42 + M130-MFP-S123 新 model 包+config 需同步� | git commit c12e1fc → sync.sh server-4 + server-6 (rsync � |
| 2026-08-22 18:10:17 | [skip_design](20260822-181017_skip_design.md) | Tick 20260822-18: 队列深度判定 waiting=7 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M123/ |
| 2026-08-22 19:11:57 | [skip_design](20260822-191157_skip_design.md) | Tick 20260822-19: 队列深度判定 waiting=7 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M123/ |
| 2026-08-22 20:10:15 | [skip_design](20260822-201015_skip_design.md) | 队列深度判定 waiting=7 (server-4: M125-M130, server-6: | 跳过自主设计 (Phase 0-4 不触发). 队列深度充足 |
| 2026-08-22 21:09:21 | [skip_design](20260822-210921_skip_design.md) | Tick #20260822-21: 队列深度判定 waiting=7 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 4 个 |
| 2026-08-22 22:09:06 | [skip_design](20260822-220906_skip_design.md) | Tick 20260822-22: 队列深度判定 waiting=7 (server-4: M1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M123/ |
| 2026-08-22 23:09:51 | [skip_design](20260822-230951_skip_design.md) | Tick 20260822-23: 队列深度判定 waiting=7 (server-4: M1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M123/ |
| 2026-08-23 00:12:50 | [skip_design](20260823-001250_skip_design.md) | Tick 20260823-00: 队列深度判定 waiting=7 (server-4: M1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M123/ |
| 2026-08-23 01:11:06 | [skip_design](20260823-011106_skip_design.md) | Tick 20260823-01: 队列深度判定 waiting=7 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M123- |
| 2026-08-23 02:11:09 | [skip_design](20260823-021109_skip_design.md) | Tick 20260823-02: 队列深度判定 waiting=7 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M123/ |
| 2026-08-23 03:11:47 | [skip_design](20260823-031147_skip_design.md) | Tick 20260823-03: 队列深度判定 waiting=7 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M123/ |
| 2026-08-23 04:13:14 | [skip_design](20260823-041314_skip_design.md) | Tick 20260823-04: 队列深度判定 waiting=7 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M123( |
| 2026-08-23 05:08:41 | [early_stop](20260823-050841_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_dca] 连续 11  | kill PID=3698302 on server-4 gpu=0 |
| 2026-08-23 05:12:52 | [skip_design](20260823-051252_skip_design.md) | Tick 20260823-05: 队列深度判定 waiting=7 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 队列深度充足 |
| 2026-08-23 06:08:56 | [queue_push](20260823-060856_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M127 detail message x DCA decoder dedicated branch — {co |
| 2026-08-23 06:10:50 | [skip_design](20260823-061050_skip_design.md) | Tick 20260823-06: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 队列深度充足 |
| 2026-08-23 07:10:20 | [skip_design](20260823-071020_skip_design.md) | Tick 20260823-07: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 仅监控+生成 t |
| 2026-08-23 08:10:45 | [skip_design](20260823-081045_skip_design.md) | Tick 20260823-08: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 队列深度充足 |
| 2026-08-23 09:10:51 | [skip_design](20260823-091051_skip_design.md) | Tick 20260823-09: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 队列深度充足 |
| 2026-08-23 10:08:56 | [early_stop](20260823-100856_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_dcm] 连续 11  | kill PID=3825693 on server-4 gpu=1 |
| 2026-08-23 10:12:54 | [terminal](20260823-101254_terminal.md) | M124-CTF-HCG-DCM 早停终态 (Best=0.5010@ep26/50, no_impro | 生成 pipeline/analyses/M124-CTF-HCG-DCM_done_earlystop_202 |
| 2026-08-23 10:13:01 | [skip_design](20260823-101301_skip_design.md) | 队列深度判定: waiting=6 vs 容量4+1=5, 是否触发� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M127/ |
| 2026-08-23 10:37:27 | [queue_push](20260823-103727_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M128 detail message x DCM decoder shared pathway — {cont |
| 2026-08-23 11:17:16 | [next_batch](20260823-111716_next_batch.md) | 队列深度不足 (waiting=5 < 可用卡5+1=6); champion 0. | 设计并入队 M131-MFP-DCM (configs/Quard/ctf_hcg_mfp_dcm/ |
| 2026-08-23 11:17:32 | [code_sync](20260823-111732_code_sync.md) | M131-MFP-DCM 新 model 包+config 需同步到哪些服务� | git commit 49ab047 → sync.sh server-4 (192.168.1.137) + se |
| 2026-08-23 12:11:26 | [skip_design](20260823-121126_skip_design.md) | Tick 20260823-12: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M127/ |
| 2026-08-23 13:10:52 | [skip_design](20260823-131052_skip_design.md) | Tick 20260823-13: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M127/ |
| 2026-08-23 14:13:29 | [skip_design](20260823-141329_skip_design.md) | 队列深度 waiting=6 vs 容量4+1=5 (server-4 2槽 + serve | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M127/ |
| 2026-08-23 15:11:46 | [skip_design](20260823-151146_skip_design.md) | Tick 20260823-15: 队列深度 waiting=6 vs 容量4+1=5, 是 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 4 个 |
| 2026-08-23 16:11:15 | [skip_design](20260823-161115_skip_design.md) | Tick 20260823-16: 队列深度 waiting=6 vs 容量4+1=5, 是 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 4 个 |
| 2026-08-23 17:09:53 | [skip_design](20260823-170953_skip_design.md) | Tick 20260823-17: 队列深度 waiting=6 vs 容量4+1=5, 是 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 4 run |
| 2026-08-23 18:10:55 | [skip_design](20260823-181055_skip_design.md) | Tick 20260823-18: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M127/ |
| 2026-08-23 18:37:12 | [early_stop](20260823-183712_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_det_dca] 连续 11 次验证未 | kill PID=1207678 on server-4 gpu=0 |
| 2026-08-23 19:08:42 | [queue_push](20260823-190842_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M129 MFP seed=42 control — 判定 M119 0.5020 tie 是否机制性 vs s |
| 2026-08-23 19:11:19 | [terminal](20260823-191119_terminal.md) | M127-DET-DCA 早停终态 (Best=0.4870@22/50, no_improve=11/ | 生成 pipeline/analyses/M127-DET-DCA_done_earlystop_2026082 |
| 2026-08-23 19:11:27 | [skip_design](20260823-191127_skip_design.md) | 队列深度判定 waiting=5 vs 容量4+1=5, 是否触发自 | 跳过自主设计 (Phase 0-4 不触发): 容量=server-4 2� |
| 2026-08-23 20:09:42 | [skip_design](20260823-200942_skip_design.md) | 队列深度判定 waiting=5 vs 容量4+1=5, 是否触发自 | 跳过自主设计 (Phase 0-4 不触发): 容量=server-4 2� |
| 2026-08-23 21:09:48 | [skip_design](20260823-210948_skip_design.md) | Tick #20260823-21: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M128/ |
| 2026-08-23 22:12:30 | [skip_design](20260823-221230_skip_design.md) | 队列深度判定 waiting=5 vs 容量4+1=5, 是否触发自 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M128- |
| 2026-08-23 23:10:41 | [skip_design](20260823-231041_skip_design.md) | Tick 20260823-23: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M128/ |
| 2026-08-24 00:10:05 | [skip_design](20260824-001005_skip_design.md) | Tick #20260824-00: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M128/ |
| 2026-08-24 01:13:37 | [next_batch](20260824-011337_next_batch.md) | 队列深度不足 (waiting=5 ≤ 容量5); champion 0.5020  | 设计并入队 M132-MFP-MLAY (configs/Quard/ctf_hcg_mfp_mla |
| 2026-08-24 01:13:41 | [code_sync](20260824-011341_code_sync.md) | M132-MFP-MLAY 新 model 包+config 需同步到哪些服务� | git commit 86b0d8e → sync.sh server-4 (192.168.1.137) + se |
| 2026-08-24 02:07:28 | [early_stop](20260824-020728_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_det_dcm] 连续 11 次验证未 | kill PID=1794680 on server-4 gpu=1 |
| 2026-08-24 02:10:38 | [terminal](20260824-021038_terminal.md) | M128-DET-DCM 早停终态 (Best=0.4990@23/50, no_improve=11/ | 生成 pipeline/analyses/M128-DET-DCM_done_earlystop_2026082 |
| 2026-08-24 02:10:41 | [skip_design](20260824-021041_skip_design.md) | Tick #20260824-02: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M129/ |
| 2026-08-24 02:37:23 | [queue_push](20260824-023723_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M130 MFP seed=123 control — 3-seed 矩阵补全 (1999/42/123)] c |
| 2026-08-24 03:16:47 | [next_batch](20260824-031647_next_batch.md) | 队列深度不足 (waiting=5 ≤ 容量5); champion 0.5020  | 设计并入队 M133-DCMV (configs/Quard/ctf_hcg_dcmv/, clus |
| 2026-08-24 03:16:49 | [code_sync](20260824-031649_code_sync.md) | M133-DCMV 新 model 包+config 需同步到哪些服务器?  | git commit d53129f → sync.sh server-4 (192.168.1.137) + se |
| 2026-08-24 04:09:30 | [skip_design](20260824-040930_skip_design.md) | Tick #20260824-04: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M129/ |
| 2026-08-24 05:09:17 | [skip_design](20260824-050917_skip_design.md) | Tick #20260824-05: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M129/ |
| 2026-08-24 06:07:24 | [early_stop](20260824-060724_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_mfp_s42] 连续 | kill PID=2852575 on server-4 gpu=0 |
| 2026-08-24 06:10:01 | [terminal](20260824-061001_terminal.md) | M129-MFP-S42 早停终态 (Best=0.4869@ep20, 低于 baseline | M129→done_earlystop, 生成终态分析; MFP 轴标记'疑 |
| 2026-08-24 06:10:03 | [skip_design](20260824-061003_skip_design.md) | 队列深度判定 waiting=6 vs 容量5+1=6, 是否触发自 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M130- |
| 2026-08-24 06:11:01 | [other](20260824-061101_other.md) | running.json server-6 GPU7 残留 M122-MLAY-S123 (08-22 kill | 从 running.json server-6.7 移除 M122-MLAY-S123; 队列保 |
| 2026-08-24 06:37:23 | [queue_push](20260824-063723_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M133 DCMV (decoder visual/instance pathway cluster KV ac |
| 2026-08-24 07:15:54 | [next_batch](20260824-071554_next_batch.md) | 队列深度不足 (waiting=5 ≤ 可用卡5, 要求≥6); c | 设计并入队 M134-DUAL (DCM+DCMV 双解码通路, 补 {ql |
| 2026-08-24 07:15:55 | [code_sync](20260824-071555_code_sync.md) | M134-DUAL + M135-DCM-S42 新 model 包+config 需同步到� | git commit 2964e0c → sync.sh server-4 (192.168.1.137) + se |
| 2026-08-24 08:09:09 | [skip_design](20260824-080909_skip_design.md) | Tick 20260824-08: 队列深度判定 waiting=7 vs 容量5+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M130- |
| 2026-08-24 09:10:46 | [skip_design](20260824-091046_skip_design.md) | Tick 20260824-09: 队列深度判定 waiting=7 vs 容量5+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M130- |
| 2026-08-24 10:09:08 | [skip_design](20260824-100908_skip_design.md) | Tick 20260824-10: 队列深度判定 waiting=7 vs 容量5+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M130- |
| 2026-08-24 11:09:56 | [skip_design](20260824-110956_skip_design.md) | Tick 20260824-11: 队列深度判定 waiting=7 vs 容量(按 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M130- |
| 2026-08-24 11:14:46 | [skip_design](20260824-111446_skip_design.md) | Tick 20260824-11: 队列深度 waiting=7 vs 容量+1 判定, | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M130- |
| 2026-08-24 14:09:52 | [skip_design](20260824-140952_skip_design.md) | Tick 20260824-14: 队列深度判定 waiting=7 vs 容量+1=6 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M130- |
| 2026-08-24 15:09:33 | [skip_design](20260824-150934_skip_design.md) | Tick #20260824-15: 队列深度判定 waiting=7 vs 容量+1  | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M133/ |
| 2026-08-24 16:07:29 | [early_stop](20260824-160729_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_mfp_s123] 连 | kill PID=3755306 on server-4 gpu=1 |
| 2026-08-24 16:13:20 | [route_change](20260824-161320_route_change.md) | MFP 3-seed 矩阵完整: s1999=0.5020 (M119), s42=0.4869<bas | 关闭 MFP 轴 (CSORT 先例), 撤回 M131-MFP-DCM / M132-MF |
| 2026-08-24 16:14:16 | [queue_push](20260824-161416_queue_push.md) | M130-MFP-S123 早停释放 server-4 gpu1 (16:07 kill), 推� | 启动 M125-MLAY-DCA (configs/Quard/mlay_dca/..._mlay_dca.ya |
| 2026-08-24 16:16:22 | [next_batch](20260824-161622_next_batch.md) | MFP 轴关闭 (M131/M132 撤回) + M125 推送后 waiting=4  | 设计并入队 M136-MLAY-DCMV (configs/Quard/mlay_dcmv/, 2� |
| 2026-08-24 16:16:23 | [code_sync](20260824-161623_code_sync.md) | M136-MLAY-DCMV + M137-DCMV-S42 新 model 包+config 需同� | git commit 1315736 → sync server-4 (192.168.1.137) + serve |
| 2026-08-24 17:07:25 | [early_stop](20260824-170725_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_dcmv] 连续 11 | kill PID=46634 on server-4 gpu=0 |
| 2026-08-24 17:12:50 | [queue_push](20260824-171251_queue_push.md) | M133-DCMV 早停释放 server-4 gpu0 (17:07 kill PID=46634), | 启动 M126-MLAY-DCM (configs/Quard/mlay_dcm/..._mlay_dcm.ya |
| 2026-08-24 17:13:36 | [terminal](20260824-171336_terminal.md) | M133-DCMV 早停终态 (Best=0.4950@19/50), qia 通路 vs DC | M133→done_earlystop, 生成终态分析; DCMV qia 轴标� |
| 2026-08-24 17:19:20 | [next_batch](20260824-171920_next_batch.md) | M126 推送后 waiting=5 < 容量5+1=6, 深度不足; M133 � | 设计并入队 M138-MLAY-DUAL (configs/Quard/mlay_dual/, cl |
| 2026-08-24 17:19:22 | [code_sync](20260824-171922_code_sync.md) | M138-MLAY-DUAL 新 model 包+config 需同步到所有可用 | git commit 34c4086 → sync.sh server-4 (192.168.1.137) + se |
| 2026-08-24 18:09:30 | [skip_design](20260824-180930_skip_design.md) | Tick #20260824-18: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-24 19:10:08 | [skip_design](20260824-191008_skip_design.md) | Tick #20260824-190939: 队列深度判定 waiting=6 vs 容� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-24 20:08:36 | [skip_design](20260824-200836_skip_design.md) | Tick #20260824-2007: 队列深度判定 waiting=6 vs 容量5 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-24 21:09:47 | [skip_design](20260824-210947_skip_design.md) | Tick #20260824-21: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-24 22:10:01 | [skip_design](20260824-221001_skip_design.md) | Tick #20260824-22: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125- |
| 2026-08-24 23:09:34 | [skip_design](20260824-230934_skip_design.md) | Tick #20260824-23: 队列深度判定 waiting=6 vs 容量+1  | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-25 00:08:58 | [skip_design](20260825-000858_skip_design.md) | Tick #20260825-00: 队列深度判定 waiting=6 vs 容量+1, | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-25 01:10:11 | [skip_design](20260825-011011_skip_design.md) | Tick #20260825-01: 队列深度判定 waiting=6 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-25 02:08:53 | [skip_design](20260825-020853_skip_design.md) | Tick #20260825-02: 队列深度判定 waiting=6 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-25 03:09:03 | [skip_design](20260825-030903_skip_design.md) | Tick #20260825-03: 队列深度判定 waiting=6 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-25 04:08:58 | [skip_design](20260825-040858_skip_design.md) | Tick 20260825-04: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125- |
| 2026-08-25 05:08:56 | [skip_design](20260825-050856_skip_design.md) | Tick 20260825-05: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125- |
| 2026-08-25 06:09:14 | [skip_design](20260825-060914_skip_design.md) | Tick #20260825-06: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125- |
| 2026-08-25 07:08:36 | [skip_design](20260825-070836_skip_design.md) | Tick #20260825-07: 队列深度判定 waiting=6 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125- |
| 2026-08-25 08:08:45 | [skip_design](20260825-080845_skip_design.md) | Tick #20260825-08: 队列深度判定 waiting=6 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-25 09:09:39 | [skip_design](20260825-090939_skip_design.md) | 队列深度 waiting=6 vs 容量5+1=6, 是否触发自主设 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-25 10:08:55 | [skip_design](20260825-100855_skip_design.md) | 队列深度 waiting=6 vs 容量5+1=6, 是否触发自主设 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-25 11:08:25 | [skip_design](20260825-110825_skip_design.md) | Tick 20260825-11: 队列深度 waiting=6 vs 容量5+1=6, 是 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-25 12:10:15 | [skip_design](20260825-121015_skip_design.md) | Tick 20260825-12: 队列深度判定 waiting=6 vs 容量5+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-25 13:07:25 | [early_stop](20260825-130725_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_mlay_dcm] 连续 11 次验证 | kill PID=1435903 on server-4 gpu=0 |
| 2026-08-25 13:09:59 | [skip_design](20260825-131000_skip_design.md) | Tick 20260825-13: 队列深度判定 waiting=6 vs 容量5+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M125/ |
| 2026-08-25 13:11:38 | [queue_push](20260825-131138_queue_push.md) | M126-MLAY-DCM 早停释放 server-4 gpu0 (13:07 kill PID=143 | 启动 M134-DUAL (configs/Quard/ctf_hcg_dual/..._ctf_hcg_dua |
| 2026-08-25 13:24:01 | [next_batch](20260825-132401_next_batch.md) | M134 推送后 waiting=5 < 容量5+1=6; M126-MLAY-DCM 终态 | 设计并入队 M139-MLAY-DUAL-LEGACY (configs/Quard/mlay_du |
| 2026-08-25 13:24:03 | [code_sync](20260825-132403_code_sync.md) | M139-MLAY-DUAL-LEGACY 新 model 包+config 需同步到所� | git commit 86b5d5b → sync.sh server-4 (192.168.1.137) + se |
| 2026-08-25 14:07:28 | [early_stop](20260825-140728_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_mlay_dca] 连续 11 次验证 | kill PID=1312169 on server-4 gpu=1 |
| 2026-08-25 14:09:54 | [queue_push](20260825-140954_queue_push.md) | M125-MLAY-DCA 早停释放 server-4 gpu1 (14:07 kill PID=131 | 启动 M135-DCM-S42 (configs/Quard/ctf_hcg_dcm_s42/..._ctf_h |
| 2026-08-25 14:10:33 | [terminal](20260825-141033_terminal.md) | M125-MLAY-DCA 早停终态 (Best=0.4970@20/50), MLay x DCA � | M125→done_earlystop, 生成终态分析; {DCA,DCM}xMLay � |
| 2026-08-25 14:19:44 | [next_batch](20260825-141944_next_batch.md) | M135 推送后 waiting=5 < 容量5+1=6; M125 终态确认 {D | 设计并入队 M140-CTF-HCG-CLICA (configs/Quard/ctf_hcg_cl |
| 2026-08-25 14:19:45 | [code_sync](20260825-141945_code_sync.md) | M140-CTF-HCG-CLICA 新 model 包+config+loss 需同步到所 | git commit 77e3315 → sync.sh server-4 (192.168.1.137) + se |
| 2026-08-25 15:09:11 | [skip_design](20260825-150911_skip_design.md) | Tick #20260825-15: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M134/ |
| 2026-08-25 16:09:05 | [skip_design](20260825-160905_skip_design.md) | Tick 20260825-16: 队列深度判定 waiting=6 vs 容量5+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M134/ |
| 2026-08-25 17:08:58 | [skip_design](20260825-170858_skip_design.md) | Tick 20260825-17: 队列深度判定 waiting=6 vs 容量5+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M134/ |
| 2026-08-25 18:08:58 | [skip_design](20260825-180858_skip_design.md) | Tick #20260825-18: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M134/ |
| 2026-08-25 19:10:11 | [skip_design](20260825-191011_skip_design.md) | Tick #20260825-19: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M134/ |
| 2026-08-25 20:09:15 | [skip_design](20260825-200915_skip_design.md) | Tick #20260825-20: 队列深度判定 waiting=6 vs 容量5+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M134- |
| 2026-08-25 21:09:47 | [skip_design](20260825-210947_skip_design.md) | Tick #20260825-21: 队列深度判定 waiting=6 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M134- |
| 2026-08-25 22:09:02 | [skip_design](20260825-220902_skip_design.md) | Tick 20260825-22: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M134- |
| 2026-08-25 23:09:35 | [skip_design](20260825-230935_skip_design.md) | Tick 20260825-23: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M134- |
| 2026-08-26 00:09:28 | [skip_design](20260826-000928_skip_design.md) | Tick 20260826-00: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M134/ |
| 2026-08-26 01:07:24 | [early_stop](20260826-010724_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_dual] 连续 11 | kill PID=163627 on server-4 gpu=0 |
| 2026-08-26 01:10:19 | [queue_push](20260826-011019_queue_push.md) | M134-DUAL 早停释放 server-4 gpu0 (01:07 kill PID=163627) | 启动 M136-MLAY-DCMV (configs/Quard/mlay_dcmv/..._mlay_dcmv |
| 2026-08-26 01:10:42 | [route_change](20260826-011042_route_change.md) | M134-DUAL (qla+qia 双通路直读 cluster KV) 终态 0.4970 | 关闭 {qla,qia}×{cluster KV} 双通路轴 — 矩阵 4 格 |
| 2026-08-26 02:13:37 | [skip_design](20260826-021337_skip_design.md) | Tick 20260826-02: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M135/ |
| 2026-08-26 03:15:24 | [next_batch](20260826-031524_next_batch.md) | 队列深度不足 (waiting=5 < 容量5+1=6); champion 0.502 | 入队 M141-CTF-HCG-CSIC (cross-scale instance consistency l |
| 2026-08-26 03:15:25 | [code_sync](20260826-031525_code_sync.md) | M141-CTF-HCG-CSIC 新 model 包 + config 需同步到哪些� | git commit 0b05971 → pl.sh sync server-4 (192.168.1.137) + |
| 2026-08-26 04:08:41 | [skip_design](20260826-040841_skip_design.md) | Tick 20260826-04: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 仅监控+生成 t |
| 2026-08-26 05:09:32 | [skip_design](20260826-050932_skip_design.md) | Tick 20260826-05: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 仅监控+生成 t |
| 2026-08-26 06:08:30 | [skip_design](20260826-060830_skip_design.md) | Tick 20260826-06: 队列深度判定 waiting=6 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 仅监控+生成 t |
| 2026-08-26 07:07:23 | [early_stop](20260826-070723_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_dcm_s42] 连续 | kill PID=308412 on server-4 gpu=1 |
| 2026-08-26 07:09:34 | [queue_push](20260826-070934_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M137 DCMV seed=42 control — validate M133 qia 通路结果 is me |
| 2026-08-26 07:11:18 | [skip_design](20260826-071119_skip_design.md) | Tick 20260826-07: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M136/ |
| 2026-08-26 08:10:52 | [skip_design](20260826-081052_skip_design.md) | Tick 20260826-08: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M136/ |
| 2026-08-26 09:10:35 | [skip_design](20260826-091035_skip_design.md) | Tick 20260826-09: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M136/ |
| 2026-08-26 10:09:08 | [skip_design](20260826-100908_skip_design.md) | Tick 20260826-10: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M136- |
| 2026-08-26 11:08:41 | [skip_design](20260826-110841_skip_design.md) | Tick 20260826-11: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M136/ |
| 2026-08-26 12:09:10 | [skip_design](20260826-120910_skip_design.md) | Tick 20260826-12: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M136/ |
| 2026-08-26 13:07:23 | [early_stop](20260826-130723_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_mlay_dcmv] 连续 11 次验 | kill PID=1884963 on server-4 gpu=0 |
| 2026-08-26 13:09:39 | [queue_push](20260826-130939_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M138 MLay(2层) x DUAL(qla+qia 双通路) — 方向①x② 满强度正交组合天花板格] c |
| 2026-08-26 13:14:54 | [next_batch](20260826-131455_next_batch.md) | M138-MLAY-DUAL 推送后 waiting=4 < 容量4+1=5; champion 0 | 入队 M142-CTF-HCG-CLICA-CSIC (双监督 combo): champion c |
| 2026-08-26 13:14:58 | [code_sync](20260826-131458_code_sync.md) | M142-CTF-HCG-CLICA-CSIC 新 model 包+config 需同步到哪 | git commit e0a0862 → pl.sh sync server-4 (192.168.1.137) + |
| 2026-08-26 14:09:42 | [skip_design](20260826-140942_skip_design.md) | 队列深度判定 waiting=5 vs 容量4+1=5 (server-4 2槽 + | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M137/ |
| 2026-08-26 15:09:27 | [skip_design](20260826-150927_skip_design.md) | Tick 20260826-15: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M137/ |
| 2026-08-26 16:08:44 | [skip_design](20260826-160844_skip_design.md) | Tick #20260826-16: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M137- |
| 2026-08-26 18:10:46 | [skip_design](20260826-181046_skip_design.md) | Tick 20260826-18: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M137/ |
| 2026-08-26 19:10:40 | [skip_design](20260826-191041_skip_design.md) | Tick #20260826-19: 队列深度判定 waiting=5 vs 容量4+1 | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M137/ |
| 2026-08-26 20:09:36 | [skip_design](20260826-200936_skip_design.md) | Tick 20260826-20: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M137/ |
| 2026-08-26 21:09:28 | [skip_design](20260826-210928_skip_design.md) | Tick 20260826-21: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M137/ |
| 2026-08-26 22:08:59 | [skip_design](20260826-220859_skip_design.md) | Tick 20260826-22: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M137- |
| 2026-08-26 23:07:24 | [early_stop](20260826-230724_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_dcmv_s42] 连 | kill PID=2799039 on server-4 gpu=1 |
| 2026-08-26 23:13:19 | [queue_push](20260826-231319_queue_push.md) | server-4 gpu1 空闲 (M137-DCMV-S42 23:07 早停 kill PID=27 | 启动 M139-MLAY-DUAL-LEGACY → server-4 gpu1 (PID 1126555) |
| 2026-08-26 23:19:18 | [next_batch](20260826-231918_next_batch.md) | M139 推送后 waiting=4 < 容量4+1=5; champion 0.5020, 平 | 入队 M143-CTF-HCG-OBJG (cluster-token 目标对象感知 a |
| 2026-08-26 23:19:19 | [code_sync](20260826-231919_code_sync.md) | M143-CTF-HCG-OBJG 新 model 包 + config 需同步到哪些� | git commit 178362c → pl.sh sync server-4 (192.168.1.137) + |
| 2026-08-27 00:09:08 | [skip_design](20260827-000908_skip_design.md) | Tick 20260827-00: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M138- |
| 2026-08-27 01:08:56 | [skip_design](20260827-010856_skip_design.md) | Tick 20260827-01: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M138- |
| 2026-08-27 02:09:18 | [skip_design](20260827-020918_skip_design.md) | Tick 20260827-02: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M138- |
| 2026-08-27 03:09:54 | [skip_design](20260827-030954_skip_design.md) | Tick 20260827-03: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M138/ |
| 2026-08-27 04:07:27 | [early_stop](20260827-040727_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_mlay_dual] 连续 13 次验 | kill PID=3737535 on server-4 gpu=0 |
| 2026-08-27 04:09:26 | [queue_push](20260827-040926_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M140 CTF-HCG x CLICA (cluster-instance contrastive align |
| 2026-08-27 04:20:35 | [next_batch](20260827-042035_next_batch.md) | M140-CLICA 推送后 waiting=4 < 容量4+1=5; champion 0.502 | 入队 M144-CTF-HCG-LQA (cluster-token 语言查询语义对 |
| 2026-08-27 04:20:38 | [code_sync](20260827-042039_code_sync.md) | M144-CTF-HCG-LQA 新 model 包+config 需同步到哪些服� | git commit d04917f → pl.sh sync server-4 (192.168.1.137) + |
| 2026-08-27 04:25:58 | [queue_push](20260827-042558_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M140 CTF-HCG x CLICA (cluster-instance contrastive align |
| 2026-08-27 04:27:06 | [other](20260827-042706_other.md) | M140-CLICA 启动 15s 即 crash (IndexError: mask[1586] vs t | 修复 cluster_ids 层级组合映射 (lvl>0 簇→父簇映 |
| 2026-08-27 06:09:39 | [skip_design](20260827-060939_skip_design.md) | Tick 20260827-06: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M139- |
| 2026-08-27 07:09:37 | [skip_design](20260827-070937_skip_design.md) | Tick 20260827-07: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M139- |
| 2026-08-27 08:08:58 | [skip_design](20260827-080858_skip_design.md) | Tick 20260827-08: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M139/ |
| 2026-08-27 09:08:48 | [skip_design](20260827-090848_skip_design.md) | Tick 20260827-09: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M139/ |
| 2026-08-27 10:09:29 | [skip_design](20260827-100929_skip_design.md) | Tick 20260827-10: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M139/ |
| 2026-08-27 11:08:42 | [skip_design](20260827-110842_skip_design.md) | Tick #233: 队列深度 waiting=5 vs 容量4+1=5 (server-4 2 | 跳过自主设计. 队列深度达标(5≥5); 4/4 槽全占 |
| 2026-08-27 12:11:32 | [skip_design](20260827-121132_skip_design.md) | Tick 20260827-12: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M139/ |
| 2026-08-27 13:09:53 | [skip_design](20260827-130953_skip_design.md) | Tick 20260827-13: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M139/ |
| 2026-08-27 14:09:55 | [skip_design](20260827-140955_skip_design.md) | Tick 20260827-14: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M139/ |
| 2026-08-27 15:10:02 | [skip_design](20260827-151003_skip_design.md) | Tick 20260827-15: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M139/ |
| 2026-08-27 16:08:56 | [skip_design](20260827-160856_skip_design.md) | Tick 20260827-16: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M139/ |
| 2026-08-27 17:07:26 | [early_stop](20260827-170726_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_clica] 连续 1 | kill PID=1906005 on server-4 gpu=0 |
| 2026-08-27 17:10:47 | [queue_push](20260827-171047_queue_push.md) | M140-CTF-HCG-CLICA 早停 kill 后 server-4 gpu0 空闲（ut | 启动 [M141 CTF-HCG x CSIC (cross-scale instance consistenc |
| 2026-08-27 17:20:21 | [next_batch](20260827-172021_next_batch.md) | M141 推送后 waiting=4 < 容量4+1=5; champion 0.5020 (M95 | 入队 M145-CTF-HCG-CSORT-ALL (cross-scale orth 全尺度对 |
| 2026-08-27 17:20:24 | [code_sync](20260827-172024_code_sync.md) | M145-CTF-HCG-CSORT-ALL 新 model 包+config 需同步到哪� | git commit 6442ec1 → pl.sh sync server-4 (192.168.1.137) + |
| 2026-08-27 18:09:10 | [skip_design](20260827-180910_skip_design.md) | Tick 20260827-18: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M139/ |
| 2026-08-27 19:08:24 | [skip_design](20260827-190824_skip_design.md) | Tick 20260827-19: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M139/ |
| 2026-08-27 20:08:51 | [skip_design](20260827-200851_skip_design.md) | Tick 20260827-20: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M139/ |
| 2026-08-27 21:07:24 | [early_stop](20260827-210724_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_mlay_dual_legacy] 连 | kill PID=1126555 on server-4 gpu=1 |
| 2026-08-27 21:10:09 | [queue_push](20260827-211009_queue_push.md) | M139-MLAY-DUAL-LEGACY 早停 kill (21:07 PID=1126555) 释放 | 启动 M142-CTF-HCG-CLICA-CSIC (双监督 combo) 到 server- |
| 2026-08-27 21:16:46 | [next_batch](20260827-211646_next_batch.md) | M142 推送后 waiting=4 < 容量4+1=5; M139-MLAY-DUAL-LEGAC | 设计并入队 M146-CTF-HCG-CSORT-DET (champion + cluster_m |
| 2026-08-27 21:16:47 | [code_sync](20260827-211647_code_sync.md) | M146-CTF-HCG-CSORT-DET 新 model 包 + config 需同步到� | git commit 059f2d7 → sync.sh server-4 (192.168.1.137) + se |
| 2026-08-27 22:09:08 | [skip_design](20260827-220908_skip_design.md) | Tick 20260827-22: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计. 继续监控 M141-CSIC(10/50,0.4800) + M |
| 2026-08-27 23:09:08 | [skip_design](20260827-230908_skip_design.md) | Tick 20260827-23: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M141- |
| 2026-08-28 00:09:17 | [skip_design](20260828-000917_skip_design.md) | Tick 20260828-00: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M141- |
| 2026-08-28 01:09:28 | [skip_design](20260828-010928_skip_design.md) | 队列深度判定: waiting=5 vs 容量4+1=5, 是否触发� | 跳过自主设计. 队列深度达标(5≥5=容量4+1), 继 |
| 2026-08-28 02:09:58 | [skip_design](20260828-020958_skip_design.md) | 队列深度判定: waiting=5 vs 容量4+1=5, 是否触发� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M141- |
| 2026-08-28 03:08:44 | [skip_design](20260828-030844_skip_design.md) | 队列深度判定: waiting=5 vs 容量4+1=5, 是否触发� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M141- |
| 2026-08-28 04:08:47 | [skip_design](20260828-040847_skip_design.md) | Tick 20260828-04: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M141- |
| 2026-08-28 05:08:32 | [skip_design](20260828-050832_skip_design.md) | Tick 20260828-05: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M141- |
| 2026-08-28 06:07:25 | [early_stop](20260828-060725_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csic] 连续 11 | kill PID=3971094 on server-4 gpu=0 |
| 2026-08-28 06:10:05 | [queue_push](20260828-061005_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M143 cluster-token 目标对象感知 aux loss (OBJG) — 监督簇 token 识别 |
| 2026-08-28 06:18:57 | [next_batch](20260828-061857_next_batch.md) | M143 推送后 waiting=4 < 容量4+1=5; loss 监督轴 2 连 | 设计并入队 M147-MLAY-CSORT (legacy 2层注入 + cross-s |
| 2026-08-28 06:19:00 | [code_sync](20260828-061900_code_sync.md) | M147-MLAY-CSORT 新 model 包+config 需同步到哪些服� | git commit 44435ba → pl.sh sync server-4 (192.168.1.137) + |
| 2026-08-28 07:08:59 | [skip_design](20260828-070859_skip_design.md) | Tick 20260828-07: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M142- |
| 2026-08-28 08:07:33 | [early_stop](20260828-080733_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_det_mlay] 连续 11 次验证 | kill PID=4040343 on server-6 gpu=7 |
| 2026-08-28 08:07:55 | [queue_push](20260828-080755_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M122 MLay(2层legacy) seed=123 control — 补 MLay seed 矩阵第3点 |
| 2026-08-28 08:15:37 | [next_batch](20260828-081537_next_batch.md) | M122 推送后 waiting=4 < 容量4+1=5; champion 0.5020 gap+ | 入队 M148-CTF-HCG-CSORT-DCM (champion ctf_hcg_csort + use_ |
| 2026-08-28 09:09:47 | [skip_design](20260828-090947_skip_design.md) | Tick 20260828-09: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M142- |
| 2026-08-28 10:09:35 | [skip_design](20260828-100935_skip_design.md) | Tick 20260828-10: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M142- |
| 2026-08-28 11:07:25 | [early_stop](20260828-110725_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_clica_csic] | kill PID=485998 on server-4 gpu=1 |
| 2026-08-28 11:09:36 | [queue_push](20260828-110936_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M144 cluster-token 语言查询语义对齐 aux loss (LQA) — 目标簇 token 与 |
| 2026-08-28 11:15:58 | [next_batch](20260828-111558_next_batch.md) | M144 推送后 waiting=4 < 容量4+1=5, 队列深度不足;  | 设计并入队 M149-CTF-HCG-CSORT-SG (champion + fine-refer |
| 2026-08-28 11:16:02 | [code_sync](20260828-111602_code_sync.md) | M149-CTF-HCG-CSORT-SG 新 model 包 + config 需同步到哪 | git commit a6e6f2c → sync.sh server-4 (192.168.1.137) + se |
| 2026-08-28 12:08:55 | [skip_design](20260828-120855_skip_design.md) | Tick 20260828-12: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计. 队列深度达标(5≥5=容量4+1). 继 |
| 2026-08-28 13:09:54 | [skip_design](20260828-130954_skip_design.md) | Tick 20260828-13: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M143/ |
| 2026-08-28 14:09:48 | [skip_design](20260828-140948_skip_design.md) | Tick 20260828-14: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M143/ |
| 2026-08-28 15:08:41 | [skip_design](20260828-150841_skip_design.md) | Tick 20260828-15: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M143- |
| 2026-08-28 16:09:29 | [skip_design](20260828-160929_skip_design.md) | Tick 20260828-16: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M143- |
| 2026-08-28 17:09:15 | [skip_design](20260828-170915_skip_design.md) | Tick 20260828-17: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M143- |
| 2026-08-28 18:07:20 | [early_stop](20260828-180720_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_objg] 连续 13 | kill PID=1705485 on server-4 gpu=0 |
| 2026-08-28 18:11:42 | [queue_push](20260828-181142_queue_push.md) | M143-OBJG 早停 kill (18:07, PID=1705485) 释放 server-4 g | 启动 M145-CTF-HCG-CSORT-ALL (cross-scale orth 全尺度对 |
| 2026-08-28 18:20:10 | [next_batch](20260828-182010_next_batch.md) | M145 推送后 waiting=4 < 容量4+1=5; 交互机制全灭 ( | 设计并入队 M150-CTF-HCG-CSORT-OWC (champion CSORT + ort |
| 2026-08-28 18:20:11 | [code_sync](20260828-182011_code_sync.md) | M150-CTF-HCG-CSORT-OWC 新 model 包+config 需同步到哪� | git commit 093f8cc → sync.sh server-4 (192.168.1.137) + se |
| 2026-08-28 19:09:12 | [skip_design](20260828-190912_skip_design.md) | Tick 20260828-19: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M144- |
| 2026-08-28 20:11:34 | [skip_design](20260828-201134_skip_design.md) | Tick 20260828-20: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M144- |
| 2026-08-28 21:09:24 | [skip_design](20260828-210924_skip_design.md) | Tick 20260828-21: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M144- |
| 2026-08-28 22:09:08 | [skip_design](20260828-220908_skip_design.md) | Tick 20260828-22: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计. 队列深度达标(5≥5=容量4+1). 继 |
| 2026-08-28 23:09:28 | [skip_design](20260828-230928_skip_design.md) | Tick 20260828-23: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M144/ |
| 2026-08-29 00:09:06 | [skip_design](20260829-000906_skip_design.md) | Tick 20260829-00: 队列深度判定 waiting=5 vs 容量4+1= | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M144- |
| 2026-08-29 01:07:27 | [early_stop](20260829-010727_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_lqa] 连续 13  | kill PID=2399815 on server-4 gpu=1 |
| 2026-08-29 01:09:50 | [queue_push](20260829-010950_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M146 CSORT x detail message (champion + cluster_message_ |
| 2026-08-29 01:18:26 | [other](20260829-011826_other.md) | M149-SG dec.py 两处 endswith('_csort') 守卫对 cluster_m | 修复 M149 dec.py 两处守卫为 '_csort' in cluster_mode, |
| 2026-08-29 01:21:27 | [next_batch](20260829-012128_next_batch.md) | M146 推送后 waiting=4 < 容量4+1=5; 去相关轴操作� | 设计并入队 M151-CTF-HCG-CSORT-ODW (champion csort + Gra |
| 2026-08-29 01:21:28 | [code_sync](20260829-012128_code_sync.md) | M151-ODW 新 model 包 + config + M149-SG loss 守卫修复, | git commit 8876145 → pl.sh sync server-4 + server-6 (已� |
| 2026-08-29 02:09:36 | [skip_design](20260829-020936_skip_design.md) | Tick #26 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M145- |
| 2026-08-29 03:09:26 | [skip_design](20260829-030926_skip_design.md) | Tick #27 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M145- |
| 2026-08-29 04:09:07 | [skip_design](20260829-040907_skip_design.md) | Tick #28 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M145/ |
| 2026-08-29 05:09:02 | [skip_design](20260829-050902_skip_design.md) | Tick #29 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M145- |
| 2026-08-29 06:09:07 | [skip_design](20260829-060907_skip_design.md) | Tick #30 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M145/ |
| 2026-08-29 07:08:58 | [skip_design](20260829-070858_skip_design.md) | Tick #31 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M145/ |
| 2026-08-29 08:09:12 | [skip_design](20260829-080912_skip_design.md) | Tick #32 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M145/ |
| 2026-08-29 09:09:08 | [skip_design](20260829-090908_skip_design.md) | Tick #33 队列深度判定: waiting=5 vs 容量4+1=5; champ | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M145- |
| 2026-08-29 10:07:32 | [early_stop](20260829-100732_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_all]  | kill PID=3323582 on server-4 gpu=0 |
| 2026-08-29 10:11:09 | [queue_push](20260829-101109_queue_push.md) | M145-CSORT-ALL 早停 kill 后 server-4 gpu0 空闲 (0% util | 启动 M147-MLAY-CSORT (CSORT x MLay legacy@2, champion CSOR |
| 2026-08-29 10:16:17 | [next_batch](20260829-101617_next_batch.md) | M147 推送后 waiting=4 < 容量4+1=5; M145-CSORT-ALL 本ti | 入队 M152-CTF-HCG-CSORT-F1 (champion CSORT 仅最细对 25 |
| 2026-08-29 11:09:42 | [skip_design](20260829-110942_skip_design.md) | Tick #35 队列深度判定: waiting=5 vs 容量4+1=5; champ | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M146- |
| 2026-08-29 12:09:40 | [skip_design](20260829-120940_skip_design.md) | Tick #36 队列深度判定: waiting=5 vs 容量4+1=5; champ | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M146- |
| 2026-08-29 13:09:54 | [skip_design](20260829-130954_skip_design.md) | Tick #37 队列深度判定: waiting=5 vs 容量4+1=5; champ | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M146- |
| 2026-08-29 14:07:26 | [early_stop](20260829-140726_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_det]  | kill PID=41457 on server-4 gpu=1 |
| 2026-08-29 14:10:02 | [queue_push](20260829-141002_queue_push.md) | M146-CSORT-DET 早停 kill 后 server-4 gpu1 空闲 (util=0% | 启动 M148-CTF-HCG-CSORT-DCM (champion CSORT × DCM decoder |
| 2026-08-29 14:18:12 | [next_batch](20260829-141812_next_batch.md) | M148 推送后 waiting=4 < 容量4+1=5; M146 本tick 终态  | 设计并入队 M153-CTF-HCG-CSORT-MFP (champion CSORT × MF |
| 2026-08-29 14:18:13 | [code_sync](20260829-141813_code_sync.md) | M153 新 model 包 + config 已实现, 是否同步到所有 | git commit 76793cd → sync.sh server-4 + server-6 (已确� |
| 2026-08-29 15:10:03 | [skip_design](20260829-151003_skip_design.md) | Tick #39 队列深度判定: waiting=5 vs 容量4+1=5; champ | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147- |
| 2026-08-29 16:08:42 | [skip_design](20260829-160842_skip_design.md) | Tick #40 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计. 队列深度达标(5≥5=容量4+1), 4/4 |
| 2026-08-29 17:08:42 | [skip_design](20260829-170842_skip_design.md) | Tick #41 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147/ |
| 2026-08-29 18:08:58 | [skip_design](20260829-180858_skip_design.md) | Tick #42 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147/ |
| 2026-08-29 19:08:55 | [skip_design](20260829-190855_skip_design.md) | Tick #43 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147/ |
| 2026-08-29 20:08:40 | [skip_design](20260829-200840_skip_design.md) | Tick #44 队列深度判定: waiting=5 vs 容量4+1=5, 满� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147/ |
| 2026-08-29 21:08:37 | [skip_design](20260829-210838_skip_design.md) | Tick #45 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147/ |
| 2026-08-29 22:10:14 | [skip_design](20260829-221014_skip_design.md) | Tick #46 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147/ |
| 2026-08-29 23:09:00 | [skip_design](20260829-230900_skip_design.md) | Tick #47 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147/ |
| 2026-08-30 00:09:35 | [skip_design](20260830-000935_skip_design.md) | Tick #48 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147/ |
| 2026-08-30 01:09:05 | [skip_design](20260830-010905_skip_design.md) | Tick #49 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147- |
| 2026-08-30 02:09:36 | [skip_design](20260830-020936_skip_design.md) | 队列深度判定: waiting=5 vs 容量4+1=5, 是否触发� | 跳过自主设计。队列深度达标(5≥5=容量4+1)。� |
| 2026-08-30 03:07:28 | [early_stop](20260830-030728_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_dcm]  | kill PID=1774462 on server-4 gpu=1 |
| 2026-08-30 03:09:33 | [queue_push](20260830-030933_queue_push.md) | M148-CTF-HCG-CSORT-DCM 早停 kill 后 server-4 gpu1 空闲  | 启动 M149-CTF-HCG-CSORT-SG (champion CSORT + fine-referenc |
| 2026-08-30 03:15:41 | [next_batch](20260830-031541_next_batch.md) | M149 推送后 waiting=4 < 容量4+1=5; M148-CSORT-DCM 本ti | 入队 M154-CTF-HCG-CSORT-GSC (champion + 全局场景尺度 |
| 2026-08-30 03:15:42 | [code_sync](20260830-031542_code_sync.md) | M154 新 model 包 + config 已实现, 是否同步到所有 | git commit db9aab3 → sync server-4 + server-6 (已确认)  |
| 2026-08-30 04:09:36 | [skip_design](20260830-040936_skip_design.md) | Tick #52 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147- |
| 2026-08-30 05:08:22 | [skip_design](20260830-050822_skip_design.md) | Tick #53 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147- |
| 2026-08-30 06:08:29 | [skip_design](20260830-060829_skip_design.md) | Tick #54 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147- |
| 2026-08-30 07:09:16 | [skip_design](20260830-070916_skip_design.md) | Tick #55 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147/ |
| 2026-08-30 08:08:53 | [skip_design](20260830-080853_skip_design.md) | Tick #56 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147/ |
| 2026-08-30 09:09:04 | [skip_design](20260830-090904_skip_design.md) | Tick #57 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147/ |
| 2026-08-30 10:09:44 | [skip_design](20260830-100944_skip_design.md) | Tick #58 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147/ |
| 2026-08-30 11:10:21 | [skip_design](20260830-111021_skip_design.md) | Tick #59 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M147- |
| 2026-08-30 11:32:45 | [early_stop](20260830-113245_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_mlay_csort] 连续 11 次 | kill PID=1228742 on server-4 gpu=0 |
| 2026-08-30 12:07:40 | [queue_push](20260830-120740_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M150 champion CSORT x orthogonal write-back context loss |
| 2026-08-30 12:16:45 | [next_batch](20260830-121645_next_batch.md) | M150 推送后 waiting=4 < 容量4+1=5, server-6 M120 即将 | 入队 M155-CTF-HCG-CSORT-RF (server-4 队尾, CSORT 移到  |
| 2026-08-30 12:17:05 | [terminal](20260830-121705_terminal.md) | M147-MLAY-CSORT 早停 (11/10 no-improve, PID=1228742), Best | M147 → done_earlystop; 生成 pipeline/analyses/M147-MLAY- |
| 2026-08-30 13:07:30 | [early_stop](20260830-130730_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_mlay_s42] 连续 11 次验证 | kill PID=4038426 on server-6 gpu=7 |
| 2026-08-30 13:07:52 | [queue_push](20260830-130752_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M156 CSORT coarse-pair-only (仅粗对 64↔8 去相关) — 与 M152-F1 对 |
| 2026-08-30 13:09:58 | [terminal](20260830-130958_terminal.md) | M120-MLAY-S42 早停 (Best=0.4950@24, 11/10 no-improve), 是 | M120 → done_earlystop; 生成 pipeline/analyses/M120-CTF-H |
| 2026-08-30 14:09:34 | [skip_design](20260830-140935_skip_design.md) | Tick #63 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M149- |
| 2026-08-30 15:07:27 | [early_stop](20260830-150727_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_sg] 连 | kill PID=3494698 on server-4 gpu=1 |
| 2026-08-30 15:11:15 | [queue_push](20260830-151115_queue_push.md) | M149-SG 早停 kill 后 server-4 gpu1 空闲 (0% util, 15MiB | 启动 [M151 CTF×HCG×CSORT-ODW (champion + orthogonal-deco |
| 2026-08-30 15:15:11 | [terminal](20260830-151511_terminal.md) | M149-CTF-HCG-CSORT-SG early-stop (Best=0.4940@20, 11/10 no-i | M149-SG → done_earlystop; 生成 pipeline/analyses/M149-CT |
| 2026-08-30 15:20:35 | [next_batch](20260830-152035_next_batch.md) | M151 推送后 waiting=4 < 容量4+1=5; M149-SG=0.4940 证� | 设计并入队 M157-CTF-HCG-CSORT-PMD (server-4 队尾, rec |
| 2026-08-30 15:20:37 | [code_sync](20260830-152037_code_sync.md) | M157/M158 新 model 包 + config 已实现, 是否同步到� | git commit 5f8e8b4 → sync.sh server-4 + server-6 (均确� |
| 2026-08-30 16:08:26 | [skip_design](20260830-160826_skip_design.md) | Tick #65 队列深度判定: waiting=6 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M150- |
| 2026-08-30 17:09:15 | [skip_design](20260830-170915_skip_design.md) | Tick #66 队列深度判定: waiting=6 vs 容量4+1=5, 深� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M150- |
| 2026-08-30 18:09:22 | [skip_design](20260830-180922_skip_design.md) | Tick #67 队列深度判定: waiting=6 vs 容量4+1=5, 深� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M150- |
| 2026-08-30 19:10:20 | [skip_design](20260830-191020_skip_design.md) | Tick #68 队列深度判定: waiting=6 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M150/ |
| 2026-08-30 20:10:03 | [skip_design](20260830-201003_skip_design.md) | Tick #69 队列深度判定: waiting=6 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M150- |
| 2026-08-30 21:08:55 | [skip_design](20260830-210855_skip_design.md) | Tick #70 队列深度判定: waiting=6 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M150- |
| 2026-08-30 22:10:08 | [skip_design](20260830-221008_skip_design.md) | Tick #71 队列深度判定: waiting=6 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M150- |
| 2026-08-30 23:09:14 | [skip_design](20260830-230914_skip_design.md) | Tick #72 队列深度判定: waiting=6 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M150( |
| 2026-08-30 23:38:59 | [early_stop](20260830-233859_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_owc]  | kill PID=503744 on server-4 gpu=0 |
| 2026-08-31 00:07:44 | [queue_push](20260831-000744_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M152 CSORT fine-scale-pair only (仅最细对 256↔64 去相关, 移除粗对 6 |
| 2026-08-31 00:11:50 | [terminal](20260831-001150_terminal.md) | M150-CTF-HCG-CSORT-OWC 早停 (Best=0.4920@ep20, 11/10 no-im | M150 → done_earlystop; 生成 pipeline/analyses/M150-CTF-H |
| 2026-08-31 00:11:53 | [skip_design](20260831-001153_skip_design.md) | Tick #73 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M151( |
| 2026-08-31 01:09:05 | [skip_design](20260831-010905_skip_design.md) | Tick #74 队列深度判定: waiting=5 vs 容量4+1=5, 是� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M151- |
| 2026-08-31 02:09:11 | [skip_design](20260831-020911_skip_design.md) | Tick #75 队列深度判定: waiting=5 vs 容量4+1=5 (SERVE | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M151- |
| 2026-08-31 03:08:36 | [skip_design](20260831-030836_skip_design.md) | Tick #76 队列深度判定: waiting=5 vs 容量4+1=5 (SERVE | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M151- |
| 2026-08-31 04:09:21 | [skip_design](20260831-040921_skip_design.md) | Tick #77 队列深度判定: waiting=5 vs 容量4+1=5 (SERVE | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M151( |
| 2026-08-31 05:09:08 | [skip_design](20260831-050908_skip_design.md) | Tick #78 队列深度判定: waiting=5 vs 容量4+1=5 (SERVE | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M151( |
| 2026-08-31 06:08:53 | [skip_design](20260831-060853_skip_design.md) | Tick #79 队列深度判定: waiting=5 vs 容量4+1=5 (SERVE | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M151- |
| 2026-08-31 07:07:24 | [early_stop](20260831-070724_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_odw]  | kill PID=906859 on server-4 gpu=1 |
| 2026-08-31 07:10:18 | [skip_design](20260831-071018_skip_design.md) | Tick #80 队列深度判定: waiting=5 vs 容量4+1=5 (serve | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M152- |
| 2026-08-31 07:11:02 | [terminal](20260831-071102_terminal.md) | M151-CTF-HCG-CSORT-ODW 早停 (Best=0.4970@21, 11/10 no-impr | M151 → done_earlystop; 生成 pipeline/analyses/M151-CTF-H |
| 2026-08-31 07:45:52 | [queue_push](20260831-074552_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M153 CSORT x MFP masked reconstruction (dual-mechanism o |
| 2026-08-31 08:46:08 | [next_batch](20260831-084608_next_batch.md) | M151-ODW 终态 0.4970 关闭写回正交轴; 队列深度 4 | 设计并入队 M159-GEO (champion+簇 centroid/radius 注� |
| 2026-08-31 09:10:22 | [skip_design](20260831-091022_skip_design.md) | Tick #82 队列深度判定: waiting=6 vs 容量4+1=5, 深� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M152- |
| 2026-08-31 10:09:12 | [skip_design](20260831-100912_skip_design.md) | Tick #83 队列深度判定: waiting=6 vs 容量4+1=5, 深� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M152- |
| 2026-08-31 11:09:26 | [skip_design](20260831-110926_skip_design.md) | Tick #84 队列深度判定: waiting=6 vs 容量4+1=5, 深� | 跳过自主设计 (Phase 0-4 不触发). 继续监控 M152- |
| 2026-08-31 17:49:47 | [early_stop](20260831-174947_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_f1] 连 | kill PID=2083767 on server-4 gpu=0 |
| 2026-08-31 19:50:32 | [queue_push](20260831-195032_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M154 CSORT + Global Scale Context (champion + 全局场景尺度 tok |
| 2026-08-31 23:50:28 | [early_stop](20260831-235028_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mfp]  | kill PID=3088506 on server-4 gpu=1 |
| 2026-09-01 01:50:12 | [queue_push](20260901-015012_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M155 CSORT on refined post-CTF tokens — 约束交付消息非原始质心, 与 M |
| 2026-09-01 03:51:06 | [early_stop](20260901-035106_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cp] 连 | kill PID=1472182 on server-6 gpu=7 |
| 2026-09-01 03:51:30 | [queue_push](20260901-035130_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M158 PMD-SH (shuffled control) — lvl+1 side rolled by N/ |
| 2026-09-01 09:53:36 | [early_stop](20260901-095336_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_gsc]  | kill PID=477396 on server-4 gpu=0 |
| 2026-09-01 11:55:02 | [queue_push](20260901-115502_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M157 PMD (receiver-side point-level message decorrelatio |
| 2026-09-02 02:00:05 | [early_stop](20260902-020005_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pmd]  | kill PID=2648810 on server-4 gpu=0 |
| 2026-09-02 04:00:41 | [queue_push](20260902-040041_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M159 champion + cluster token geometric enrichment (cent |
| 2026-09-02 10:02:18 | [early_stop](20260902-100218_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rf] 连 | kill PID=1276791 on server-4 gpu=1 |
| 2026-09-02 14:06:15 | [early_stop](20260902-140615_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_geo]  | kill PID=717717 on server-4 gpu=0 |
| 2026-09-02 17:37:31 | [next_batch](20260902-173731_next_batch.md) | Queue depth is 1 waiting versus required 6; M152-M157 and M1 | Implement and enqueue M161-M165 mask-conditioned recurrent q |
| 2026-09-02 17:39:51 | [early_stop](20260902-173951_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pmd_s | kill PID=3789625 on server-6 gpu=7 |
| 2026-09-02 17:40:17 | [queue_push](20260902-174017_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M160 GEO shuffled control — 固定偏移重排几何, 隔离几何内容 vs 结构注入] co |
| 2026-09-02 17:44:42 | [next_batch](20260902-174442_next_batch.md) | Post-enqueue monitor launched M160 and reduced waiting depth | Add M166-CTF-HCG-CSORT-MPF to server-4 queue after M163: pre |
| 2026-09-02 19:09:31 | [skip_design](20260902-190931_skip_design.md) | Tick 2026-09-02 19:07: waiting=6 versus contract capacity=5; | Skip experiment design; continue monitoring M122/M160 and pr |
| 2026-09-02 20:07:58 | [queue_push](20260902-200758_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M161 Mask-conditioned query foreground retrieval — previ |
| 2026-09-02 20:12:21 | [question](20260902-201221_question.md) | M161 launched and waiting fell to 5, equal to contract capac | Await user selection among A exclusive query ownership, B cr |
| 2026-09-02 20:40:49 | [next_batch](20260902-204049_next_batch.md) | M161 launch reduced waiting depth to 5, while the headless c | Autonomously select and enqueue M167-CTF-HCG-CSORT-MQX on se |
| 2026-09-03 00:08:57 | [skip_design](20260903-000857_skip_design.md) | Tick 2026-09-03 00:07: waiting=6 versus contract capacity=5; | Skip new experiment design and preserve the M162-M167 queue  |
| 2026-09-03 01:08:28 | [skip_design](20260903-010828_skip_design.md) | Tick 2026-09-03 01:07: waiting=6 versus contract capacity=5; | Skip new experiment design; continue M161/M122/M160 and pres |
| 2026-09-03 02:08:27 | [skip_design](20260903-020827_skip_design.md) | Tick 2026-09-03 02:07: waiting=6 versus contract capacity=5; | Skip new experiment design; continue M161/M122/M160 and pres |
| 2026-09-03 03:08:34 | [skip_design](20260903-030834_skip_design.md) | Tick 2026-09-03 03:07: waiting=6 versus contract capacity=5; | Skip new experiment design; continue M161/M122/M160 and pres |
| 2026-09-03 04:08:29 | [skip_design](20260903-040829_skip_design.md) | Tick 2026-09-03 04:07: waiting=6 versus contract capacity=5; | Skip new experiment design; continue M161/M122/M160 and pres |
| 2026-09-03 05:08:37 | [skip_design](20260903-050837_skip_design.md) | Tick 2026-09-03 05:07: waiting=6 versus contract capacity=5; | Skip new experiment design; continue M161/M122/M160 and pres |
| 2026-09-03 06:08:03 | [queue_push](20260903-060803_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M162 MQF shuffled-mask semantic control — preserves mask |
| 2026-09-03 06:14:18 | [next_batch](20260903-061418_next_batch.md) | M162 launched and reduced waiting depth from 6 to 5; which s | Implement and enqueue M168-CTF-HCG-CSORT-MQD on server-4 aft |
| 2026-09-03 07:08:39 | [skip_design](20260903-070839_skip_design.md) | Tick 2026-09-03 07:07: waiting=6 versus contract capacity=5; | Skip new experiment design; continue M161/M162/M122/M160 and |
| 2026-09-03 08:08:42 | [skip_design](20260903-080842_skip_design.md) | Tick 2026-09-03 08:07: waiting=6 versus contract capacity=5; | Skip new experiment design; continue M161/M162/M122/M160 and |
| 2026-09-03 10:16:49 | [early_stop](20260903-101649_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqf]  | kill PID=2909716 on server-4 gpu=0 |
| 2026-09-03 11:08:25 | [queue_push](20260903-110825_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M163 Mask-conditioned foreground-minus-background query  |
| 2026-09-03 11:17:49 | [next_batch](20260903-111749_next_batch.md) | M163 launched after M161 early stop and reduced waiting dept | Implement and enqueue M169-CTF-HCG-CSORT-MQB on server-4 aft |
| 2026-09-03 12:10:16 | [skip_design](20260903-121016_skip_design.md) | Tick 2026-09-03 12:09: waiting=6 versus capacity=5; should a | Skip new experiment design; continue monitoring M122/M160/M1 |
| 2026-09-03 13:08:37 | [skip_design](20260903-130837_skip_design.md) | Tick 2026-09-03 13:07: waiting=6 versus capacity=5; should a | Skip new design and preserve the existing M164-M169 reserve  |
| 2026-09-03 14:08:45 | [skip_design](20260903-140845_skip_design.md) | Tick 2026-09-03 14:07: waiting=6 versus capacity=5; should a | Skip new design and preserve the M164-M169 reserve while mon |
| 2026-09-03 15:08:44 | [skip_design](20260903-150844_skip_design.md) | Tick 2026-09-03 15:08: waiting=6 versus capacity=5; should a | Skip new design and preserve the M164-M169 reserve while mon |
| 2026-09-03 17:08:49 | [skip_design](20260903-170849_skip_design.md) | Tick 2026-09-03 17:08: waiting=6 versus capacity=5; should a | Skip new design and preserve the M164-M169 reserve while mon |
| 2026-09-03 18:08:59 | [skip_design](20260903-180859_skip_design.md) | Tick 2026-09-03 18:08: waiting=6 versus capacity=5; should a | Skip new design and preserve the M164-M169 reserve while mon |
| 2026-09-03 19:08:46 | [skip_design](20260903-190846_skip_design.md) | Tick 2026-09-03 19:07: waiting=6 versus capacity=5; should a | Skip new design and preserve the M164-M169 reserve while mon |
| 2026-09-03 20:10:02 | [early_stop](20260903-201002_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqf_s | kill PID=23756 on server-4 gpu=1 |
| 2026-09-03 20:11:41 | [queue_push](20260903-201141_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M166 Mask-conditioned query-to-point feedback — previous |
| 2026-09-03 20:19:42 | [next_batch](20260903-201942_next_batch.md) | M162 shuffled-mask control ended at 0.4980 versus aligned M1 | Implement and enqueue M170-CTF-HCG-CSORT-MQR after M169 on s |
| 2026-09-03 21:11:41 | [skip_design](20260903-211141_skip_design.md) | Tick 2026-09-03 21:10: waiting=6 versus capacity=5; should a | Skip new design and preserve the M164-M170 reserve while mon |
| 2026-09-03 22:12:34 | [skip_design](20260903-221234_skip_design.md) | Tick 2026-09-03 22:11: waiting=6 versus capacity=5; should a | Skip new design and preserve the M164-M170 reserve while mon |
| 2026-09-04 13:45:37 | [manual](20260904-134537_manual.md) | Codex gateway previously failed three consecutive ticks with | Validated gpt-5.6-sol with an independent codex exec probe r |
| 2026-09-04 13:57:43 | [queue_push](20260904-135743_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M167 Exclusive query ownership retrieval — suppress cont |
| 2026-09-04 13:57:58 | [queue_push](20260904-135758_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M168 Cross-layer mask-delta retrieval — gained support c |
| 2026-09-04 13:58:08 | [early_stop](20260904-135808_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_mlay_s123] 连续 11 次验 | kill PID=3475494 on server-6 gpu=7 |
| 2026-09-04 13:59:23 | [queue_push](20260904-135923_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M164 Mask-uncertainty query retrieval — focus recurrent  |
| 2026-09-04 14:03:07 | [manual](20260904-140307_manual.md) | User requested immediate experiment dispatch after gateway r | Reconciled stale terminal states, launched M167-MQX on serve |
| 2026-09-04 16:16:42 | [next_batch](20260904-161642_next_batch.md) | M122/M163/M166 terminal results closed MLay, foreground-back | Implement and enqueue M171-MQCC, M172-MQS, and M173-MQCI on  |
| 2026-09-04 19:09:15 | [skip_design](20260904-190915_skip_design.md) | Tick 2026-09-04 19:08: waiting=6 versus capacity=5; should a | Skip new design and preserve the M165/M169-M173 reserve whil |
| 2026-09-04 20:10:32 | [skip_design](20260904-201032_skip_design.md) | Tick 2026-09-04 20:09: waiting=6 versus capacity=5; should a | Skip new design and preserve the M165/M169-M173 reserve whil |
| 2026-09-04 21:08:07 | [early_stop](20260904-210807_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_geo_s | kill PID=543843 on server-6 gpu=7 |
| 2026-09-04 21:08:31 | [queue_push](20260904-210831_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M165 Hierarchical mask-to-cluster occupancy query retrie |
| 2026-09-04 21:14:41 | [next_batch](20260904-211441_next_batch.md) | M160 geometry shuffled control ended at 0.4910 and M165 laun | Implement and enqueue M174-CTF-HCG-CSORT-MQHC after M173 on  |
| 2026-09-04 22:09:42 | [skip_design](20260904-220942_skip_design.md) | Tick 2026-09-04 22:07: waiting=6 versus capacity=5; should a | Skip new design and preserve the M169-M174 reserve while mon |
| 2026-09-04 23:09:03 | [skip_design](20260904-230903_skip_design.md) | Tick 2026-09-04 23:07: waiting=6 versus capacity=5; should a | Skip new design and preserve the M169-M174 reserve while mon |
| 2026-09-05 00:08:57 | [skip_design](20260905-000857_skip_design.md) | Tick 2026-09-05 00:07: waiting=6 versus capacity=5; should a | Skip new design and preserve the M169-M174 reserve while mon |
| 2026-09-05 01:09:34 | [skip_design](20260905-010934_skip_design.md) | Tick 2026-09-05 01:08: waiting=6 versus capacity=5; should a | Skip new design and preserve the M169-M174 reserve while mon |
| 2026-09-05 02:10:37 | [skip_design](20260905-021037_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design this tick; preserve the six waiting e |
| 2026-09-05 03:08:33 | [skip_design](20260905-030833_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M169-M174 as the six-task res |
| 2026-09-05 04:08:34 | [skip_design](20260905-040834_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M169-M174 as the six-task res |
| 2026-09-05 05:08:39 | [skip_design](20260905-050839_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M169-M174 as the six-task res |
| 2026-09-05 06:07:59 | [early_stop](20260905-060759_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqx]  | kill PID=4018486 on server-4 gpu=0 |
| 2026-09-05 06:09:48 | [queue_push](20260905-060948_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M169 Dominant hierarchy-branch retrieval — select one fi |
| 2026-09-05 06:18:29 | [next_batch](20260905-061829_next_batch.md) | M167-MQX early-stopped at 0.4910 and M169 launch reduced wai | Add M175-CTF-HCG-CSORT-MQHF to the server-4 FIFO tail after  |
| 2026-09-05 06:19:43 | [other](20260905-061943_other.md) | M175 remote gradient smoke failed because hierarchy ID indic | Move fine and parent hierarchy ID tensors to probs_b.device  |
| 2026-09-05 07:08:04 | [early_stop](20260905-070804_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqd]  | kill PID=4019992 on server-4 gpu=1 |
| 2026-09-05 07:08:50 | [queue_push](20260905-070850_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M170 Mask counterfactual residual — aligned context minu |
| 2026-09-05 07:13:31 | [next_batch](20260905-071331_next_batch.md) | M168-MQD early-stopped at 0.4900 and M170 launch reduced wai | Add M176-CTF-HCG-CSORT-MQSD to the server-4 FIFO tail after  |
| 2026-09-05 08:08:46 | [skip_design](20260905-080846_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 09:08:38 | [skip_design](20260905-090838_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 10:08:40 | [skip_design](20260905-100840_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 11:08:36 | [skip_design](20260905-110836_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 12:08:26 | [skip_design](20260905-120826_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 13:08:35 | [skip_design](20260905-130835_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 14:08:49 | [skip_design](20260905-140849_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 15:08:29 | [skip_design](20260905-150829_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 16:08:31 | [skip_design](20260905-160831_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 17:08:37 | [skip_design](20260905-170837_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 18:08:49 | [skip_design](20260905-180849_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 19:10:33 | [skip_design](20260905-191033_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 20:13:07 | [skip_design](20260905-201307_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 21:12:06 | [skip_design](20260905-211206_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 22:09:15 | [skip_design](20260905-220915_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M171-M176 as the six-task res |
| 2026-09-05 23:07:51 | [early_stop](20260905-230751_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqr]  | kill PID=1816559 on server-4 gpu=1 |
| 2026-09-05 23:08:31 | [queue_push](20260905-230831_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M171 Query-context competition — own mask context minus  |
| 2026-09-05 23:22:21 | [next_batch](20260905-232221_next_batch.md) | M170-MQR early-stopped at 0.4970 and M171 launch reduced wai | Add M177-CTF-HCG-CSORT-MQBC to the server-4 FIFO tail after  |
| 2026-09-05 23:23:26 | [other](20260905-232326_other.md) | M177 remote smoke test showed zero mask gradient because har | Keep a hard one-hot branch in the forward pass and add a coe |
| 2026-09-06 00:07:46 | [early_stop](20260906-000746_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqb]  | kill PID=1692999 on server-4 gpu=0 |
| 2026-09-06 00:08:50 | [queue_push](20260906-000850_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M172 Stable support retrieval — consecutive-mask soft in |
| 2026-09-06 00:16:53 | [next_batch](20260906-001653_next_batch.md) | M169-MQB early-stopped at 0.5000 and M172 launch reduced wai | Add M178-CTF-HCG-CSORT-MQTD to the server-4 FIFO tail after  |
| 2026-09-06 01:09:46 | [skip_design](20260906-010946_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M173-M178 as the six-task res |
| 2026-09-06 02:10:42 | [skip_design](20260906-021042_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M173-M178 as the six-task res |
| 2026-09-06 03:08:04 | [skip_design](20260906-030804_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M173-M178 as the six-task res |
| 2026-09-06 14:34:25 | [early_stop](20260906-143425_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqs]  | kill PID=3852631 on server-4 gpu=0 |
| 2026-09-06 14:35:15 | [queue_push](20260906-143515_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M173 Cluster-inconsistency retrieval — point mask disagr |
| 2026-09-06 14:51:42 | [next_batch](20260906-145142_next_batch.md) | M172-MQS early-stopped at 0.4966 and M173 launch reduced wai | Add M179-CTF-HCG-CSORT-MQST to the server-4 FIFO tail after  |
| 2026-09-07 09:44:09 | [queue_push](20260907-094409_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M174 Hierarchy-consensus retrieval — minimum occupancy a |
| 2026-09-07 09:45:43 | [manual](20260907-094543_manual.md) | M171/M173/M164/M165 were reconciled as stopped_unknown; serv | Move the first two waiting tasks M175-MQHF and M176-MQSD fro |
| 2026-09-07 09:48:11 | [queue_push](20260907-094811_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M175 Hierarchy-flow retrieval — coarse-to-fine occupancy |
| 2026-09-07 09:48:32 | [queue_push](20260907-094832_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M176 Sibling-discrimination retrieval — child occupancy  |
| 2026-09-07 12:18:58 | [next_batch](20260907-121858_next_batch.md) | Waiting depth is 3 against the required reserve of 6; M169 h | Append M180-MQPP, M181-MQHT, and M182-MQFC to the server-4 F |
| 2026-09-07 13:09:34 | [skip_design](20260907-130934_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M177-M182 as the six-task res |
| 2026-09-07 13:14:54 | [skip_design](20260907-131454_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M177-M182 as the six-task res |
| 2026-09-07 14:08:10 | [skip_design](20260907-140810_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M177-M182 as the six-task res |
| 2026-09-07 15:08:53 | [skip_design](20260907-150853_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M177-M182 as the six-task res |
| 2026-09-07 16:08:40 | [skip_design](20260907-160840_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M177-M182 as the six-task res |
| 2026-09-07 17:08:44 | [skip_design](20260907-170844_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M177-M182 as the six-task res |
| 2026-09-07 18:12:46 | [skip_design](20260907-181246_skip_design.md) | Phase 1 remains below target and waiting depth is 6 against  | Skip autonomous design; retain M177-M182 as the six-task res |
| 2026-09-07 19:08:58 | [skip_design](20260907-190858_skip_design.md) | At 2026-09-07 19:07, waiting=6 and Phase 1 champion=0.5020 b | Retain M177-M182 FIFO without adding experiments; continue M |
| 2026-09-07 20:08:54 | [skip_design](20260907-200854_skip_design.md) | At the 2026-09-07 20:07 tick, Phase 1 is below target and wa | Retain M177-M182 FIFO and continue M174-M176 under existing  |
| 2026-09-07 21:10:40 | [skip_design](20260907-211040_skip_design.md) | At the 2026-09-07 21:08 monitor, waiting=6 and GPU7 briefly  | Retain M177-M182 FIFO and continue M174-M176 without restart |
| 2026-09-07 21:22:52 | [skip_design](20260907-212252_skip_design.md) | At 2026-09-07 21:21, waiting=6 and champion=0.5020 below tar | Retain M177-M182 FIFO and continue M174-M176 with unchanged  |
| 2026-09-07 22:14:36 | [skip_design](20260907-221436_skip_design.md) | At 2026-09-07 22:12 monitor, waiting=6 and M174 improved to  | Retain M177-M182 in server-4 FIFO; continue M174 on GPU0 and |
| 2026-09-07 23:09:40 | [skip_design](20260907-230940_skip_design.md) | At 2026-09-07 23:07 monitor, three jobs progress and waiting | Retain M177-M182 server-4 FIFO. Continue M174 on server-4 GP |
| 2026-09-08 01:07:43 | [early_stop](20260908-010743_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqhc] | kill PID=123614 on server-4 gpu=0 |
| 2026-09-08 01:08:51 | [queue_push](20260908-010851_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M177 Bottleneck-consistent hierarchy branch — select by  |
| 2026-09-08 01:10:47 | [other](20260908-011047_other.md) | M174 was stopped with monitor no_improve=11, but the precise | Fix the shared monitor fallback token boundary to exclude sp |
| 2026-09-08 01:12:23 | [skip_design](20260908-011223_skip_design.md) | After M177 launch, waiting=5; prompt nominal capacity=5 but  | Keep M178-M182 FIFO without adding a variant this tick; use  |
| 2026-09-08 01:12:23 | [question](20260908-011223_question.md) | Should previously early-stopped experiments affected by mixe | Leave retrospective rerun policy open; preserve M174 checkpo |
| 2026-09-08 02:08:40 | [skip_design](20260908-020840_skip_design.md) | At 2026-09-08 02:07 monitor, waiting=5 and all three active  | Retain M178-M182 server-4 FIFO; continue M177 on GPU0 and M1 |
| 2026-09-08 03:08:28 | [skip_design](20260908-030828_skip_design.md) | At 2026-09-08 03:07 monitor, waiting=5 and M177 improved to0 | Retain M178-M182 server-4 FIFO; continue M177 on GPU0 and M1 |
| 2026-09-08 04:10:18 | [skip_design](20260908-041018_skip_design.md) | At 2026-09-08 04:08 monitor, three jobs advanced and five ex | Retain M178-M182 server-4 FIFO; continue M177 on GPU0 and M1 |
| 2026-09-08 05:08:49 | [skip_design](20260908-050849_skip_design.md) | At 2026-09-08 05:07 monitor, waiting=5 and M177 advanced to  | Retain M178-M182 server-4 FIFO; continue M177 on GPU0 and M1 |
| 2026-09-08 06:09:01 | [skip_design](20260908-060901_skip_design.md) | At 2026-09-08 06:07 monitor, five tasks wait and M177/M176 i | Retain M178-M182 server-4 FIFO. Continue M177 on GPU0 and M1 |
| 2026-09-08 07:08:51 | [skip_design](20260908-070851_skip_design.md) | At 2026-09-08 07:07 monitor, five tasks wait and M177/M175 i | Retain M178-M182 server-4 FIFO. Continue M177 on GPU0 and M1 |
| 2026-09-08 08:09:32 | [skip_design](20260908-080932_skip_design.md) | At 2026-09-08 08:07 monitor, five tasks wait and M177 improv | Retain M178-M182 server-4 FIFO. Continue M177 on GPU0 and M1 |
| 2026-09-08 09:09:23 | [skip_design](20260908-090923_skip_design.md) | At 2026-09-08 09:07 monitor, all three experiments advanced  | Retain M178-M182 server-4 FIFO. Continue M177 on GPU0 and M1 |
| 2026-09-08 11:14:08 | [other](20260908-111409_other.md) | M177 saved a new precise best 0.4962787926 while stdout fall | Repair monitor metric selection using the matching logger fi |
| 2026-09-08 11:18:34 | [skip_design](20260908-111834_skip_design.md) | After corrected monitor11:17: three active jobs and five wai | Retain M178-M182 server-4 FIFO and M175-M177 running. No new |
| 2026-09-08 12:09:45 | [skip_design](20260908-120945_skip_design.md) | At12:07 monitor M175 improved to0.48511744, M177 current19 b | Keep M178-M182 server-4 FIFO. Continue M177 on GPU0 and M175 |
| 2026-09-08 13:09:44 | [skip_design](20260908-130944_skip_design.md) | At13:07 monitor M177 current21 best0.49627879 no_improve3/10 | Retain M178-M182 server-4 FIFO. Continue M177 on GPU0 and M1 |
| 2026-09-08 14:12:53 | [skip_design](20260908-141253_skip_design.md) | At14:09 monitor M175/M176 improved to0.48661110/0.48623621 a | Retain M178-M182 server-4 FIFO. Continue M177 on GPU0 and M1 |
| 2026-09-08 15:10:08 | [skip_design](20260908-151008_skip_design.md) | At15:07 monitor M177 current24 best0.49627879 no_improve6/10 | Retain M178-M182 server-4 FIFO. Continue M177 on GPU0 and M1 |
| 2026-09-08 16:10:33 | [skip_design](20260908-161033_skip_design.md) | At16:07 monitor M176 improved to0.49115670 at12/current13; M | Retain M178-M182 server-4 FIFO. Continue M177 on GPU0 and M1 |
| 2026-09-08 17:10:20 | [skip_design](20260908-171020_skip_design.md) | At17:08 monitor M177 current27 best0.49627879 no_improve9/10 | Retain M178-M182 server-4 FIFO. Continue M177 on GPU0 and M1 |
| 2026-09-08 18:09:35 | [queue_push](20260908-180935_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M178 Top-down hierarchy branch — coarse-to-medium-to-fin |
| 2026-09-08 18:12:25 | [other](20260908-181225_other.md) | M177 ended normally at17:21:15 but deathwatch leaves it runn | Archive M177 as done_earlystop using its explicit early-stop |
| 2026-09-08 18:23:56 | [question](20260908-182356_question.md) | M177 and newly started M178 startup profiles report10.1791G/ | Record the legacy MQ resource violation for audit; do not cl |
| 2026-09-08 18:23:56 | [next_batch](20260908-182356_next_batch.md) | After M177 normal early stop and M178 launch, waiting4 equal | Implement M183-CTF-HCG-CSORT-HQI from isolated M95: concaten |
| 2026-09-08 18:26:09 | [other](20260908-182610_other.md) | HQI topology passed but paired full-model validation failed  | Run topology, M95 and HQI in separate subprocesses. Commit a |
| 2026-09-08 18:29:49 | [next_batch](20260908-182949_next_batch.md) | M183-HQI passed independent CUDA topology tests and matched  | Append M183-CTF-HCG-CSORT-HQI to server-4 FIFO after M182; r |
| 2026-09-08 18:32:23 | [other](20260908-183223_other.md) | M175/M176 startup profiles11.1752G/10.3790G and M177/M17810. | Keep M179-M182 waiting but set per-task dispatch_hold pendin |
| 2026-09-08 19:11:43 | [other](20260908-191143_other.md) | Four held MQ configs have no measured full-model compliance; | Audit unchanged M179-M182 plus M95 with bs1 warmup20 repeat1 |
| 2026-09-08 19:15:59 | [route_change](20260908-191559_route_change.md) | All held M179-M182 measured10.1673-10.1791G and violate the1 | Withdraw never-started M179-M182 for resource noncompliance, |
| 2026-09-08 19:20:08 | [next_batch](20260908-192008_next_batch.md) | Withdrawal leaves only M183 eligible while capacity4 require | Implement M184-MQST-TR, M185-MQPP-TR, M186-MQHT-TR, M187-MQF |
| 2026-09-08 19:25:23 | [other](20260908-192523_other.md) | Pre-enqueue CUDA test found inherited MQ padding mismatch4 v | Repair active pooling methods in only the four new terminal- |
| 2026-09-08 19:30:39 | [next_batch](20260908-193039_next_batch.md) | All four terminal-readout replacements passed CUDA topology, | Mark unstarted M179-M182 withdrawn_resource in notes with st |
| 2026-09-08 20:15:39 | [other](20260908-201539_other.md) | At20:14 three runs remain live, M178 best0.4159519672 at3/cu | Keep M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-TR, |
| 2026-09-08 21:09:51 | [other](20260908-210951_other.md) | At21:09 M178 best0.4397424459 at4/current5; M175/M176 remain | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-08 21:10:39 | [other](20260908-211039_other.md) | Reconciliation found M183-HQI waiting in queue.json but its  | Backfill only M183-CTF-HCG-CSORT-HQI.json from the existing  |
| 2026-09-08 22:09:49 | [other](20260908-220949_other.md) | At22:09 M176 improved0.4935617447 at14/current15, M178 impro | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-08 23:12:08 | [other](20260908-231208_other.md) | At23:10 M178 improved0.4599725902 at6/current7; M175/M176 ar | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 00:10:17 | [other](20260909-001017_other.md) | At00:09 Sep9 M178 improved0.4635328650 at7/current8; M176 ep | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 01:10:17 | [other](20260909-011017_other.md) | At01:09 Sep9 M178 improved0.4696552455 at8/current9; M175 co | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 02:12:23 | [other](20260909-021223_other.md) | At02:11 Sep9 M178 completed9=0.4617949724/current10; M175 cu | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 03:09:48 | [other](20260909-030948_other.md) | At03:09 Sep9 M178 improved0.4702329338 at10/current11; M175/ | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 04:09:54 | [other](20260909-040954_other.md) | At04:09 Sep9 M178 improved0.4826719761 at11/current12; M175/ | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 05:12:53 | [other](20260909-051253_other.md) | At05:11 Sep9 M178 improved0.4865343273 at12/current13; M176  | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 06:10:18 | [other](20260909-061019_other.md) | At06:09 Sep9 M175 improved0.4967526197 at17/current18; M178  | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 07:10:29 | [other](20260909-071029_other.md) | At07:09 Sep9 M178 improved0.4882169664 at14/current15; M175  | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 08:12:20 | [other](20260909-081220_other.md) | At08:10 Sep9 M178 improved0.4905349910 at15/current16; M175  | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 09:10:53 | [other](20260909-091053_other.md) | At09:09 Sep9 M178 completed16=0.4841669202/current17; M175/M | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 10:10:29 | [other](20260909-101029_other.md) | At10:09 Sep9 M178 completed17=0.4888104498/current18; M176 c | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 11:12:06 | [other](20260909-111206_other.md) | At11:10 Sep9 M178 completed18=0.4859090745/current19; M175 c | Retain M183-HQI then M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 12:08:50 | [queue_push](20260909-120850_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M183 Hierarchy-informed query initialization - concatena |
| 2026-09-09 12:15:02 | [next_batch](20260909-121502_next_batch.md) | M183 launched on server-4 GPU1; eligible waiting4 is below m | Implement independent M188-CTF-HCG-CSORT-MQB-TR from M169: r |
| 2026-09-09 12:23:23 | [next_batch](20260909-122323_next_batch.md) | M188 CUDA checks passed; matched full-model9.832737324G and8 | Admit M188-CTF-HCG-CSORT-MQB-TR behind M184-M187 on server-4 |
| 2026-09-09 12:23:35 | [other](20260909-122335_other.md) | M183 registry is running but gpu null while launch history,  | Update only M183 actual server/gpu metadata under lock, pres |
| 2026-09-09 13:09:38 | [other](20260909-130938_other.md) | At13:08 Sep9 M183 completed first validation0.3361252546 and | Retain server-4 FIFO M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 14:12:51 | [other](20260909-141251_other.md) | At14:11 Sep9 M183 completed validation2=0.3734094203/current | Retain server-4 FIFO M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 15:09:53 | [other](20260909-150953_other.md) | At15:08 Sep9 M178 improved0.4930404425 at24/current25; M183  | Retain server-4 FIFO M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 16:10:45 | [question](20260909-161045_question.md) | Server-4 GPU1 now contains lyb PID3495914 started15:19:30 Se | Record the shared-GPU ownership issue for later coordination |
| 2026-09-09 16:11:05 | [other](20260909-161105_other.md) | At16:08 Sep9 M178 completed26 without best/current27; M175 c | Retain server-4 FIFO M184-MQST-TR, M185-MQPP-TR, M186-MQHT-T |
| 2026-09-09 17:12:09 | [other](20260909-171209_other.md) | At17:10 Sep9 M178 completed27=.4875552952/current28; M183 cu | Retain server-4 FIFO M184-MQST-TR,M185-MQPP-TR,M186-MQHT-TR, |
| 2026-09-09 18:10:38 | [other](20260909-181038_other.md) | At18:09 Sep9 M183 improved to.4473682344@5/current6; M178 co | Retain server-4 FIFO M184-MQST-TR,M185-MQPP-TR,M186-MQHT-TR, |
| 2026-09-09 19:10:19 | [other](20260909-191019_other.md) | At19:08 Sep9 M183 improved.4599533379@6/current7; M178 compl | Retain server-4 FIFO M184-MQST-TR,M185-MQPP-TR,M186-MQHT-TR, |
| 2026-09-09 20:13:34 | [other](20260909-201334_other.md) | At20:12 Sep9 M176 completed23=.4813112319/current24/no_impro | Retain server-4 FIFO M184-MQST-TR,M185-MQPP-TR,M186-MQHT-TR, |
| 2026-09-09 20:17:59 | [other](20260909-201759_other.md) | Final retention scan crossed20:17:22 onSep9; summary20260908 | Delete only summary20260908-201722.md using verified Literal |
| 2026-09-09 21:10:43 | [other](20260909-211043_other.md) | At21:09 Sep9 M183 improved.4754271507@8/current9; M178 compl | Retain server-4 FIFO M184-MQST-TR,M185-MQPP-TR,M186-MQHT-TR, |
| 2026-09-10 00:12:47 | [other](20260910-001247_other.md) | M176 is absent in two real monitor ticks and its immutable l | Reconcile M176 as done_earlystop using the verified exact lo |
| 2026-09-10 00:16:15 | [other](20260910-001615_other.md) | Sep9 23:07 turn.failed auth_unavailable was mislabeled busy  | Capture invocation-local stderr separately and allow busy-sk |
| 2026-09-10 00:18:45 | [other](20260910-001845_other.md) | After M176 normal termination,3 jobs remain live and5 eligib | Retain M184-M188 server-4 FIFO and existing measured admissi |
| 2026-09-10 07:52:36 | [other](20260910-075236_other.md) | Nightly reconcile-only fallback recorded M178/M175 stopped_u | Correct the two existing ledger rows and registries to done_ |
| 2026-09-10 07:55:51 | [other](20260910-075551_other.md) | M175/M178 corrected to normal early stop; eligible reserve5  | Keep five pre-approved server-4 FIFO tasks and HQI running;  |
| 2026-09-10 07:55:52 | [question](20260910-075552_question.md) | Cross-server admission and generic log collection remain inc | Record placement follow-up without changing SERVERS.yaml, ov |
| 2026-09-10 08:08:53 | [manual](20260910-080853_manual.md) | User requested immediate experiment dispatch. | Migrate FIFO M184 and M185 to server-6 GPU7, two slots; laun |
| 2026-09-10 08:09:05 | [queue_push](20260910-080905_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M184 MQST terminal-readout structural ablation] configs/ |
| 2026-09-10 08:09:15 | [queue_push](20260910-080915_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M185 MQPP terminal-readout structural ablation] configs/ |
| 2026-09-10 08:27:00 | [manual](20260910-082700_manual.md) | User asks to push on server-4 because sufficient memory rema | One-shot M186 launch on server-4 GPU0 alongside existing ext |
| 2026-09-10 08:27:11 | [queue_push](20260910-082711_queue_push.md) | server-4 gpu0 有外部任务但剩余显存>24000MB，是否叠加本项目实验？ | 启动 [M186 MQHT terminal-readout structural ablation] configs/ |
| 2026-09-10 11:18:51 | [next_batch](20260910-111851_next_batch.md) | Waiting2 below capacity4 plus one reserve; which bounded str | Implement M189 MQBC-TR, M190 MQTD-TR, M191 MQSD-TR; enqueue  |
| 2026-09-10 11:20:34 | [next_batch](20260910-112034_next_batch.md) | Three terminal recurrence ablations passed measured resource | Enqueue M189 MQBC-TR, M190 MQTD-TR, M191 MQSD-TR behind M187 |
| 2026-09-10 11:23:41 | [other](20260910-112341_other.md) | Close tick artifacts and apply summary retention after reser | Retain4 active jobs and5 eligible waiting; delete only verif |
| 2026-09-10 12:11:46 | [other](20260910-121146_other.md) | At12:09 Sep10 four jobs are alive; M183 is epoch24 with9 rea | Retain M183-M186 and FIFO M187-M191; no premature stop, extr |
| 2026-09-10 13:12:15 | [other](20260910-131215_other.md) | M183 has an explicit normal-stop marker and24 exact validati | Archive M183 done_earlystop and release only server-4GPU1 ow |
| 2026-09-10 13:12:16 | [queue_push](20260910-131216_queue_push.md) | GPU1 free after verified M183 normal stop; dispatch FIFO suc | Launch admitted M187-MQFC-TR on server-4GPU1 using scoped no |
| 2026-09-10 13:13:17 | [other](20260910-131317_other.md) | M187 launcher failed before SSH at missing conda_source; rec | Restore only M187 claiming to waiting, then retry with full  |
| 2026-09-10 13:13:19 | [queue_push](20260910-131319_queue_push.md) | GPU1 free after verified M183 normal stop; dispatch FIFO suc | Launch admitted M187-MQFC-TR on server-4GPU1 using scoped no |
| 2026-09-10 13:13:29 | [queue_push](20260910-131329_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M187 MQFC terminal-readout structural ablation] configs/ |
| 2026-09-10 13:17:58 | [next_batch](20260910-131758_next_batch.md) | M187 launch reduced waiting5 to4; which single bounded mecha | Implement independent M192-MQHF-TR from M175, deleting inter |
| 2026-09-10 13:22:46 | [route_change](20260910-132246_route_change.md) | M192 terminal hierarchy flow passes CUDA correctness but mea | Reject M192 before enqueue/training; preserve code and resou |
| 2026-09-10 13:28:25 | [next_batch](20260910-132826_next_batch.md) | M192 rejected10.045G and waiting4 below required5; which ind | Implement M193-MQHC-TR from M174 with four intermediate feed |
| 2026-09-10 13:33:46 | [next_batch](20260910-133346_next_batch.md) | M193 CUDA and full-model admission passed; restore waiting4  | Enqueue M193-MQHC-TR behindM191 on server-4 FIFO, gpu=null;  |
| 2026-09-10 13:35:20 | [other](20260910-133520_other.md) | Final tick audit: M183 archived, M187 running, M192 rejected | Retain4 running and5 waiting; write six-section report and r |
| 2026-09-10 14:10:23 | [other](20260910-141023_other.md) | Sep10 14:09 four trainers progressing, waiting5 meets actual | Preserve M184-M187 and FIFO M188/M189/M190/M191/M193. No sto |
| 2026-09-10 15:10:51 | [other](20260910-151051_other.md) | Sep10 15:09 four active trainers, M186.476983@9 and M187 fir | Preserve M184-M187 and FIFO M188/M189/M190/M191/M193; no pre |
| 2026-09-10 16:11:25 | [other](20260910-161125_other.md) | Sep10 16:09 four trainers are progressing; M186.483680@10, M | Preserve M184-M187 and server-4 FIFO M188/M189/M190/M191/M19 |
| 2026-09-10 17:11:48 | [other](20260910-171148_other.md) | Sep10 17:09 four trainers progress; M187.400714@3, M186.4836 | Preserve M184-M187 and server-4 FIFO M188/M189/M190/M191/M19 |
| 2026-09-10 18:10:25 | [other](20260910-181025_other.md) | Sep10 18:09 all four runs improved best; M186.486216@12 with | Preserve M184-M187 and server-4 FIFO M188/M189/M190/M191/M19 |
| 2026-09-10 19:12:36 | [other](20260910-191236_other.md) | Sep10 19:11 four runs progressing; M187.441255778@5 improved | Preserve M184-M187 and server-4 FIFO M188/M189/M190/M191/M19 |
| 2026-09-10 20:10:20 | [other](20260910-201020_other.md) | Sep10 20:09 all four runs refreshed best: M186.488806456@15  | Preserve M184-M187 and server-4 FIFO M188/M189/M190/M191/M19 |
| 2026-09-10 21:11:13 | [other](20260910-211113_other.md) | Sep10 21:10 M186 improved.494499683@17 with1 no-improvement  | Preserve M184-M187 and server-4 FIFO M188/M189/M190/M191/M19 |
| 2026-09-10 21:57:56 | [route_change](20260910-215756_route_change.md) | User requests research centered on novelty, a concrete probl | Require evidence and derivation for future new designs; reco |
| 2026-09-10 22:02:45 | [route_change](20260910-220245_route_change.md) | User requests changing the scope of subsequent experiments a | Update goal description and four binding constraints: six co |
| 2026-09-11 00:10:27 | [other](20260911-001027_other.md) | Sep11 00:07 tick after two busy-thread skips: four live trai | Preserve four trainers and original FIFO; no stop, launch, n |
| 2026-09-11 01:10:06 | [other](20260911-011006_other.md) | Sep11 01:07 tick: M186 no_improve7/10, all four trainers pro | Preserve trainers and FIFO; no early stop, launch, design or |
| 2026-09-11 02:09:20 | [other](20260911-020920_other.md) | Sep11 02:07 tick: M186 no_improve8/10, M1871/10, four live t | Preserve all trainers and FIFO; no stop, launch, new design  |
| 2026-09-11 03:13:55 | [other](20260911-031355_other.md) | M188 deployment work_dir still points at old host path; repa | Apply one-line server-4-only work_dir deployment patch befor |
| 2026-09-11 03:13:59 | [other](20260911-031359_other.md) | M186 normal stop verified at27; finalize?  | Archive M186 done_earlystop and release only server-4GPU0.  |
| 2026-09-11 03:14:00 | [queue_push](20260911-031400_queue_push.md) | GPU0 free after M186 normal stop; dispatch FIFO?  | Launch admitted legacy M188 on server-4GPU0 with non-destruc |
| 2026-09-11 03:14:09 | [queue_push](20260911-031409_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送 | 启动 [M188 MQB terminal-only dominant ancestor branch stru |
| 2026-09-11 03:15:59 | [other](20260911-031559_other.md) | Waiting4 at capacity4 triggers review; scientific prerequisi | Perform D0 read-only asset inventory and freeze scene-separa |
| 2026-09-11 03:18:02 | [other](20260911-031802_other.md) | D0 v1 separates scan IDs but repeated scans may share a phys | Supersede v1 with v2 grouped by ScanNet scene prefix; preser |
| 2026-09-11 03:20:16 | [other](20260911-032016_other.md) | Tick closeout: M186 finalized, M188 running, D0 manifest fro | Retain4 trainers and4 waiting legacy tasks; save six-section |
| 2026-09-11 04:09:06 | [other](20260911-040906_other.md) | Waiting4 is below reserve target5; D0 checkpoint identity re | Continue CPU-only checkpoint metadata, exact log and explici |
| 2026-09-11 04:12:14 | [other](20260911-041214_other.md) | Both CPU audits differ only by two text embedding buffers; e | Check those buffers against current runtime and permit only  |
| 2026-09-11 04:15:10 | [other](20260911-041510_other.md) | CPU provenance audit complete, no new terminal, waiting4; cl | Preserve4running/4waiting; record exact historical metrics w |
| 2026-09-11 05:11:50 | [other](20260911-051150_other.md) | Waiting4 below reserve5; D0 checkpoints audited but D1 mask  | Implement an isolated evaluation-only D1 collector; preregis |
| 2026-09-11 05:19:14 | [other](20260911-051914_other.md) | D1 pilot completed 16 banks on fixed8descriptions/2scenes; w | Accept collector correctness with exact original predictions |
| 2026-09-11 06:08:29 | [other](20260911-060829_other.md) | Four trainers remain active and waiting4 below reserve5; D1  | Run isolated grouping and repeatability audit on the existin |
| 2026-09-11 06:14:38 | [other](20260911-061438_other.md) | Both grouping audits pass CPU readback; are singleton pilot  | Record no binary-bank, selected-index or IoU changes across  |
| 2026-09-11 07:11:10 | [other](20260911-071110_other.md) | Waiting4 below reserve5; only8 of284 frozen diagnostic IDs m | Extend baseline and M95 diagnostics to all284 frozen IDs wit |
| 2026-09-11 07:31:23 | [other](20260911-073123_other.md) | CPU readback absolute-only probability check failed after su | Repair only verifier to restore established pilot tolerance  |
| 2026-09-11 07:35:32 | [other](20260911-073532_other.md) | All568banks verified on284matched IDs/71scenes: what conclus | Finish D1 expansion with explicit exploratory results, prese |
| 2026-09-11 07:37:31 | [other](20260911-073731_other.md) | Local closeout hit Windows implicit GBK decoding before writ | Use explicit UTF-8 reads; renderer retry1 succeeded, report  |
| 2026-09-11 08:09:05 | [other](20260911-080905_other.md) | Waiting4 at capacity4 and568banks measured, but selected err | Freeze CPU-only D1 instance-overlap protocol on all284IDs an |
| 2026-09-11 08:17:38 | [other](20260911-081738_other.md) | All568instance joins verified; M95recoverable111 includes63s | Record descriptive instance-substitution evidence and fixed1 |
| 2026-09-11 09:11:26 | [other](20260911-091126_other.md) | Waiting4 at capacity4; fixed12 errors and9 controls still la | Run isolated CPU D1 identity and geometry audit on the froze |
| 2026-09-11 09:14:47 | [other](20260911-091447_other.md) | D1 identity CPU worker failed before data load: remote Pytho | Repair helper hashing with portable chunked SHA256; preserve |
| 2026-09-11 09:17:59 | [other](20260911-091759_other.md) | D1 identity audit verified445object masks on11scenes and42pa | Accept annotation-identity evidence only: fixed12M95 errors  |
| 2026-09-11 10:09:51 | [other](20260911-100951_other.md) | Waiting4/capacity4 and identity-audited12errors do not yet e | Perform bounded text-only applicability audit on21frozen des |
| 2026-09-11 10:16:44 | [other](20260911-101644_other.md) | 21fixed descriptions do not confirm narrow same-pair shared- | Do not adopt shared-witness proposal as main mechanism now;  |
| 2026-09-11 11:12:21 | [other](20260911-111221_other.md) | Waiting4/capacity4; usable mask banks exist but seed-based d | Freeze CPU-only assignment replay on all284 diagnostic IDs p |
| 2026-09-11 11:18:51 | [other](20260911-111851_other.md) | Assignment audit synthetic check failed before banks: origin | Repair audit only to float32 production input; verify analyt |
| 2026-09-11 11:23:28 | [other](20260911-112328_other.md) | Verified568 assignment replays: M95 recoverable111 includes9 | Reject absence-of-positive-supervision as dominant explanati |
| 2026-09-11 12:08:45 | [other](20260911-120845_other.md) | M95 has usable positives in99 of111 recoverable errors; curr | Freeze CPU ranking audit on568 banks plus source-extracted s |
| 2026-09-11 12:15:36 | [other](20260911-121536_other.md) | 568 ranks verified; M95recoverable usable-positive medianran | Archive ranking and padding non-invariance as bounded diagno |
| 2026-09-11 13:09:05 | [other](20260911-130905_other.md) | Synthetic semantic padding non-invariance verified but real  | Freeze21 existing identity cases in original language groups |
| 2026-09-11 13:21:17 | [other](20260911-132117_other.md) | CPU padding audit stopped at prior-bank mask-logit compariso | Repair1 audit reporting only: retain frozen threshold, recor |
| 2026-09-11 13:24:21 | [other](20260911-132421_other.md) | 42real projection audits pass; mean query gradient change ra | Archive small selected-evaluation padding exposure; depriori |
| 2026-09-11 14:09:14 | [other](20260911-140914_other.md) | Waiting4 at capacity4;99of111 M95 recoverable cases retain u | Freeze CPU-only discriminator margin and infinitesimal indep |
| 2026-09-11 14:16:03 | [other](20260911-141603_other.md) | 568margin audits pass;M95recoverable99of111haveH and97select | Reject missing corrective score supervision as dominant expl |
| 2026-09-11 14:18:53 | [other](20260911-141853_other.md) | Tick renderer failed before report write: defaultGBK cannot  | Repair1 explicitUTF8 queue read and rerun report renderer on |
| 2026-09-11 15:08:56 | [other](20260911-150856_other.md) | Source inspection shows baseline add_module(shared head) ver | Run isolated CPU checkpoint head-ownership audit and synthet |
| 2026-09-11 17:25:41 | [other](20260911-172541_other.md) | Exact head ownership and synthetic cross-layer coupling are  | Record the ownership contract as a diagnostic fact only; mak |
| 2026-09-11 18:20:10 | [other](20260911-182010_other.md) | D1 calibration shows score/IoU rank collapse on recoverable  | Record selection-first scope revision and LMEC as an unadmit |
| 2026-09-11 19:13:39 | [other](20260911-191339_other.md) | LMEC N1 novelty vs four primary sources and T0 closed-form a | N1 CONDITIONAL PASS with narrow claim; T0 REJECT current for |
| 2026-09-11 20:09:44 | [other](20260911-200944_other.md) | T0 rejected the LMEC evidence term; can a parameter-free rep | LMEC-v2 = sqrt(|S||S^c|/N) * (g(v+,l)-g(v-,l)) passes all T1 |
| 2026-09-11 21:13:32 | [other](20260911-211332_other.md) | M187 normal early stop verified at27; finalize?  | Archive M187 done_earlystop and release only the registry sl |
| 2026-09-11 21:13:33 | [question](20260911-211333_question.md) | server-4 GPU1 has no project trainer but a foreign process h | Hold M189 in waiting FIFO; do not force overlay on server-4  |
| 2026-09-11 21:15:32 | [route_change](20260911-211532_route_change.md) | LMEC-v2 standardized two-sample contrast: keep developing or | Close LMEC and LMEC-v2; do not train, config, checkpoint or  |
| 2026-09-11 22:10:50 | [route_change](20260911-221050_route_change.md) | Which measured error must the next main mechanism target?  | Target same-category instance competition/selection evidence |
| 2026-09-11 22:10:56 | [route_change](20260911-221056_route_change.md) | Is a per-bank ranking/competition loss admissible as the cor | Reject the plain ranking/competition-loss class as the core  |
| 2026-09-11 23:10:04 | [route_change](20260911-231004_route_change.md) | What geometry does the wrong-instance selection error have,  | Eliminate part-whole, merge-suppression, dedup and overlap-b |
| 2026-09-11 23:10:09 | [route_change](20260911-231009_route_change.md) | Does the hierarchy-derived competitor-set space clear novelt | Record as an unresolved negative screen; admit nothing; the  |
| 2026-09-12 00:31:52 | [route_change](20260912-003152_route_change.md) | Does the trained semantic-alignment projection provide langu | Close the current semantic-projection reranking/readout fami |
| 2026-09-12 00:34:15 | [route_change](20260912-003415_route_change.md) | Does the quality head or any current language/support eviden | Close quality-head reranking and the current language/suppor |
| 2026-09-12 01:11:48 | [route_change](20260912-011148_route_change.md) | The M95 score-coupling audit: is the selection score mask-co | Close the static score-coupling audit: selection is query-on |
| 2026-09-12 03:07:33 | [queue_push](20260912-030733_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M189-CTF-HCG-CSORT-MQBC-TR terminal recurrence structura |
| 2026-09-12 03:15:11 | [route_change](20260912-031511_route_change.md) | Does the frozen M95 checkpoint show useful local coupling be | Close the local query-state coupling audit; no model/config/ |
| 2026-09-12 04:09:56 | [route_change](20260912-040956_route_change.md) | M188 terminal-only dominant-ancestor branch ended at 0.4916: | Close the legacy terminal-only MQB branch with no successor; |
| 2026-09-12 04:11:10 | [route_change](20260912-041111_route_change.md) | Queue depth is 3 waiting versus 5 allowed-GPU capacity; M188 | Do not generate a replacement batch solely to satisfy queue  |
| 2026-09-12 05:08:08 | [queue_push](20260912-050808_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M190-CTF-HCG-CSORT-MQTD-TR terminal recurrence structura |
| 2026-09-12 05:12:37 | [route_change](20260912-051237_route_change.md) | Does mask-conditioned candidate scoring remain admissible as | Close the simple mask-conditioned selector/reranker at the n |
| 2026-09-12 06:15:09 | [route_change](20260912-061509_route_change.md) | Final decoder layer audit completed; should it admit a mask- | Close the one-layer upstream coupling audit and admit no mec |
| 2026-09-12 07:17:05 | [route_change](20260912-071705_route_change.md) | Does the layerwise audit admit a simple early-decoder layer  | Close simple early-layer selection/ensembling at the admissi |
| 2026-09-12 08:17:24 | [route_change](20260912-081724_route_change.md) | Does the multilayer decoder audit identify a layer-specific  | Close the multilayer decoder coupling audit as a negative di |
| 2026-09-12 09:13:51 | [route_change](20260912-091352_route_change.md) | Does the upstream parameter-group audit identify a robust sh | Close the upstream parameter-locus audit as uncertain/negati |
| 2026-09-12 10:09:12 | [route_change](20260912-100912_route_change.md) | Queue remains 2 waiting / 5 allowed-GPU capacity with no fre | Do not refill or mutate the queue; preserve FIFO M191 then M |
| 2026-09-12 11:13:52 | [route_change](20260912-111352_route_change.md) | Queue remains 2 waiting / 5 allowed-GPU capacity; does the c | Admit no mechanism and preserve FIFO M191 then M193; continu |
| 2026-09-12 12:13:33 | [route_change](20260912-121333_route_change.md) | The full-text N1 screen found established candidate matching | Close the broad candidate-specific score-field derivation; a |
| 2026-09-12 13:10:46 | [route_change](20260912-131046_route_change.md) | Queue depth is 2 waiting versus 5 allowed-GPU capacity; do a | Admit no mechanism, preserve FIFO M191-MQSD-TR then M193-MQH |
| 2026-09-12 14:10:55 | [route_change](20260912-141055_route_change.md) | Queue depth is 2 waiting versus 5 allowed-GPU capacity; M185 | Admit no mechanism; preserve FIFO M191-CTF-HCG-CSORT-MQSD-TR |
| 2026-09-12 15:09:34 | [route_change](20260912-150934_route_change.md) | Queue depth is 2 waiting versus 5 declared capacity; M184 is | Admit no mechanism; preserve FIFO M191-CTF-HCG-CSORT-MQSD-TR |
| 2026-09-12 16:12:06 | [route_change](20260912-161206_route_change.md) | Do the 21 fixed relation/attribute readings support narrow s | Close the fixed-case shared-anchor applicability check as ne |
| 2026-09-12 16:15:26 | [other](20260912-161526_other.md) | M185 normal early stop verified at epoch 23; finalize termin | Archive M185 done_earlystop and release only its server-6 GP |
| 2026-09-12 17:11:44 | [other](20260912-171144_other.md) | M184 has explicit normal early stop at epoch25; finalize dur | Archive M184 done_earlystop; release only its server-6 GPU7  |
| 2026-09-12 17:15:04 | [route_change](20260912-171504_route_change.md) | Five terminal controls M184-M188 are complete; does their ev | Close completed variants without successors; admit no new me |
| 2026-09-12 18:11:45 | [other](20260912-181145_other.md) | Can the missing M188 raw log be recovered without repeating  | Archive verified M188 log; supplement exact metrics and log_ |
| 2026-09-12 18:12:06 | [route_change](20260912-181206_route_change.md) | Does exact M188 log recovery change scientific admission or  | Admit no new mechanism or successor; preserve live M189/M190 |
| 2026-09-12 19:14:20 | [route_change](20260912-191420_route_change.md) | Do the four remaining legacy parent-child comparisons isolat | Admit no new mechanism or successor; preserve M189/M190 and  |
| 2026-09-12 20:11:12 | [route_change](20260912-201112_route_change.md) | Do fresh remote parent-log hashes and full validation denomi | Admit no new mechanism or successor; preserve M189/M190 and  |
| 2026-09-12 21:10:15 | [route_change](20260912-211015_route_change.md) | Do common-epoch parent-child trajectories justify stopping l | Preserve live M189/M190 at existing patience and FIFO M191 t |
| 2026-09-12 22:09:41 | [route_change](20260912-220941_route_change.md) | M189 has 26 validations and seven stale epochs; does the 2/5 | Preserve M189/M190 at original patience and server-4 FIFO M1 |
| 2026-09-12 23:09:13 | [route_change](20260912-230913_route_change.md) | M189 has 27 validations and eight stale epochs; does the 2/5 | Preserve M189/M190 at original patience and server-4 FIFO M1 |
| 2026-09-13 00:08:01 | [queue_push](20260913-000801_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M191-CTF-HCG-CSORT-MQSD-TR terminal recurrence structura |
| 2026-09-13 00:12:48 | [other](20260913-001248_other.md) | M189 ended normally at29 while GPU1 already belongs to M191; | Archive M189 done_earlystop; preserve M191 GPU1 and M190 GPU |
| 2026-09-13 00:12:52 | [route_change](20260913-001252_route_change.md) | M189 terminal best .4908618331 leaves six controls below M95 | Close M189 without successor; preserve M190/M191 and waiting |
| 2026-09-13 01:12:34 | [route_change](20260913-011234_route_change.md) | M190 remains live with8 stale validations and M191 has one v | Preserve M190/M191 patience10 and original M193 FIFO; admit  |
| 2026-09-13 02:07:55 | [queue_push](20260913-020755_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M193 MQHC terminal recurrence structural ablation] confi |
| 2026-09-13 02:11:27 | [other](20260913-021127_other.md) | M190 ended normally at24 while GPU0 already belongs to M193; | Archive M190 done_earlystop; preserve M193 GPU0 and M191 GPU |
| 2026-09-13 02:11:32 | [route_change](20260913-021132_route_change.md) | M190 best .4890006185 leaves seven controls below M95 and0/5 | Close M190 without successor; preserve M191/M193 patience10; |
| 2026-09-13 03:10:34 | [route_change](20260913-031034_route_change.md) | Does zero waiting capacity justify successors while M191/M19 | Preserve M191/M193 patience10; no unadmitted refill; record  |
| 2026-09-13 04:10:27 | [route_change](20260913-041027_route_change.md) | Does zero waiting and early M191/M193 progress justify a new | Preserve M191/M193 patience10; no unadmitted refill; disting |
| 2026-09-13 05:10:13 | [route_change](20260913-051013_route_change.md) | Does zero waiting or frozen label-outcome disagreement justi | Preserve M191/M193 patience10; no unadmitted refill; retain  |
| 2026-09-13 06:11:10 | [route_change](20260913-061110_route_change.md) | Does the positive-label IoU-failure fixture justify supervis | No label repair or unadmitted refill; preserve M191/M193 pat |
| 2026-09-13 07:10:26 | [route_change](20260913-071026_route_change.md) | Does nearest-query assignment prevalence justify relabeling  | No relabeling or unadmitted refill; preserve M191/M193 patie |
| 2026-09-13 08:10:28 | [route_change](20260913-081028_route_change.md) | Do paired frozen-bank outcomes and zero waiting justify new  | Preserve M191/M193 patience10; no unadmitted refill or relab |
| 2026-09-13 09:10:26 | [route_change](20260913-091026_route_change.md) | Do scene-grouped frozen-bank gains/losses justify refill wit | Preserve M191/M193 patience10; no unadmitted refill or legac |
| 2026-09-13 10:12:37 | [route_change](20260913-101237_route_change.md) | Does a verified frozen-bank error budget justify refill at z | Preserve M191/M193 patience10; no unadmitted refill or selec |
| 2026-09-13 11:10:37 | [route_change](20260913-111037_route_change.md) | Does paired oracle feasibility permit refill at zero waiting | Preserve M191/M193 patience10; no unadmitted refill or selec |
| 2026-09-13 12:10:41 | [route_change](20260913-121041_route_change.md) | Does acceptable-candidate multiplicity justify refill with z | Preserve M191/M193 patience10; no unadmitted refill or selec |
| 2026-09-13 14:10:55 | [route_change](20260913-141055_route_change.md) | Does leave-one-scene-out bank sensitivity justify new traini | Preserve M191/M193 patience10; no unadmitted refill; recover |
| 2026-09-13 15:10:46 | [route_change](20260913-151046_route_change.md) | Does scene-level oracle and regret decomposition justify ref | Preserve M191/M193 patience10; no unadmitted refill or legac |
| 2026-09-13 16:10:40 | [route_change](20260913-161040_route_change.md) | Do paired scene bootstrap intervals justify training refill  | Preserve M191/M193 patience10; no unadmitted refill or legac |
| 2026-09-13 17:10:37 | [route_change](20260913-171037_route_change.md) | Does independent bootstrap reproducibility justify refill at | Preserve M191/M193 patience10; no unadmitted refill or legac |
| 2026-09-13 18:12:25 | [route_change](20260913-181225_route_change.md) | Do zero waiting and unchanged admitted control artifacts jus | Preserve M191/M193 patience10; no unadmitted refill or legac |
| 2026-09-13 19:10:31 | [route_change](20260913-191032_route_change.md) | Do zero waiting and consistent resource admission justify ne | Preserve M191/M193 patience10; no unadmitted refill or legac |
| 2026-09-13 19:47:30 | [other](20260913-194730_other.md) | Does actual multi-positive CE reverse usable-candidate corre | Run preregistered 284-bank CPU-only source-head audit on ser |
| 2026-09-13 19:53:45 | [other](20260913-195345_other.md) | M191 completed 25 validations and normal patience10 stop; re | Archive M191 done_earlystop and release only its server-4 GP |
| 2026-09-13 19:56:34 | [route_change](20260913-195634_route_change.md) | Did real source CE show rest-bank reversal in observed recov | Reject this head-only explanation on the captured failures:  |
| 2026-09-13 20:10:05 | [route_change](20260913-201005_route_change.md) | Does M95 checkpoint permit historical total-loss optimizer r | No training refill. Historical exact replay is unsupported;  |
| 2026-09-13 21:11:30 | [route_change](20260913-211130_route_change.md) | M193 normally stopped at27 with best .490611434; does zero w | Close M193 scientifically, preserve deathwatch1/3 registry f |
| 2026-09-13 21:56:52 | [other](20260913-215652_other.md) | Fixed TRAIN manifest and current optimizer mapping verified; | Execute D2-TRAIN-STATE on idle server-4 GPU1 with frozen8 ex |
| 2026-09-13 21:59:58 | [other](20260913-215958_other.md) | One-step TRAIN update changes query indices; is this permuta | Run seed-ID alignment and fixed-original-seed diagnostic on  |
| 2026-09-13 22:03:36 | [route_change](20260913-220336_route_change.md) | Do the fixed TRAIN loss and Adam experiment justify a new op | No: both informative failures are corrected by actual update |
| 2026-09-13 22:09:34 | [route_change](20260913-220934_route_change.md) | Does the closed TRAIN reversal test or unused decoder positi | No refill or optimizer/sampling/legacy successors. Preserve  |
| 2026-09-13 23:09:49 | [other](20260913-230949_other.md) | M193 confirmed terminal at23:08 but monitor log pull failed; | Verify existing captured raw log against remote SHA256, arch |
| 2026-09-13 23:10:53 | [route_change](20260913-231054_route_change.md) | All admitted legacy controls terminal and waiting0; does com | Close M193 archive reconciliation; no training refill or opt |
| 2026-09-14 00:08:43 | [route_change](20260914-000843_route_change.md) | Waiting0 and no running experiments; what evidence is requir | Keep training queue unchanged. Formalize paired-input depend |
| 2026-09-14 01:08:26 | [other](20260914-010826_other.md) | Waiting0, Phase1 .5020 versus .5100, and no new terminal eve | Keep queue unchanged under scientific admission constraints; |
| 2026-09-14 02:08:35 | [other](20260914-020835_other.md) | Waiting0 and Phase1 below .5100; does newly idle server-4 GP | Keep queue unchanged: no scientifically admitted mechanism.  |
| 2026-09-14 03:08:31 | [other](20260914-030831_other.md) | All three allowed GPUs idle, waiting0 and Phase1 below .5100 | Keep queue unchanged under scientific admission. Record GPU0 |
| 2026-09-14 04:08:26 | [other](20260914-040826_other.md) | Waiting0, all allowed GPUs idle and Phase1 below target: is  | Keep queue unchanged under scientific admission; no closed d |
| 2026-09-14 05:08:24 | [other](20260914-050824_other.md) | Waiting0 and all allowed GPUs idle; does current evidence ad | Keep queue unchanged under scientific admission; preserve no |
| 2026-09-14 06:08:26 | [other](20260914-060826_other.md) | Waiting0, Phase1 below .5100 and all allowed GPUs idle: is t | Keep queue unchanged under scientific admission. Continue no |
| 2026-09-14 07:08:30 | [other](20260914-070830_other.md) | Waiting0, Phase1 below .5100, and allowed GPUs idle: is a ne | Keep queue unchanged under scientific admission; preserve no |
| 2026-09-14 08:08:29 | [other](20260914-080829_other.md) | Waiting0, Phase1 below .5100 and all allowed GPUs idle: admi | Keep queue unchanged under scientific admission; continue no |
| 2026-09-14 09:08:39 | [other](20260914-090839_other.md) | Waiting0, Phase1 below .5100 and allowed GPUs idle: admit tr | Keep queue unchanged under scientific admission; continue no |
| 2026-09-14 09:34:26 | [manual](20260914-093426_manual.md) | 用户要求恢复因科学准入门槛导致的空队列  | 允许在连续2个健康tick无新终态证据或可执行� |
| 2026-09-14 09:45:48 | [next_batch](20260914-094548_next_batch.md) | User requests a concrete experiment design; M95=.5024607182, | Write SCM single-candidate training DRAFT and two conditiona |
| 2026-09-14 10:21:27 | [next_batch](20260914-102127_next_batch.md) | Design budget4 with active0: which mechanisms pass admission | Retain SCM draft after nine isolated Torch checks; reject co |
| 2026-09-14 11:02:27 | [next_batch](20260914-110227_next_batch.md) | SCM continuation: budget4; actual sparse-op resource admissi | Reject SCM launch at measured lower bound76.479G; develop bo |
| 2026-09-14 12:47:45 | [route_change](20260914-124745_route_change.md) | Changed C1 invalidates candidate-only sparse FLOPs veto; bud | Supersede 1102 resource rejection; reopen SCM admission only |
| 2026-09-14 12:59:13 | [next_batch](20260914-125913_next_batch.md) | SCM resource admission: historical timing differs from C8; b | Separate first-VAL historical FLOPs from goal20/100 latency  |
| 2026-09-14 14:05:38 | [next_batch](20260914-140538_next_batch.md) | SCM unified-profile admission passed with active0/capacity4; | Admit and launch M194-CTF-HCG-CSORT-SCM on server-4 GPU1; ke |
| 2026-09-14 14:09:26 | [queue_push](20260914-140926_queue_push.md) | M194 direct SSH launch returned late and local state rolled  | Verified main PID 2172354 and active training log on server- |
| 2026-09-14 16:10:11 | [next_batch](20260914-161011_next_batch.md) | Budget3 active1: does a lower SCM objective guarantee better | Retain M194 unchanged; admit0/3. Add explicit soft-hard disa |
| 2026-09-14 16:56:32 | [other](20260914-165632_other.md) | Continue M194 and quantify real frozen-bank SCM soft-hard ri | Retain M194 at normal schedule/patience; completed CPU-only2 |
| 2026-09-14 17:24:20 | [next_batch](20260914-172420_next_batch.md) | User requests new admissible designs; active1/capacity4, CPS | Admit M195-CTF-HCG-CSORT-CPS as one independent M95 structur |
| 2026-09-14 19:11:24 | [next_batch](20260914-191124_next_batch.md) | Design budget2 with active2/4; do frozen CPS margins justify | Admit0/2: hold boundary-distance and adjacency proposals for |
| 2026-09-14 19:42:15 | [manual](20260914-194215_manual.md) | User requests immediate M195 training; server4GPU0 occupied, | Move only waiting M195 to server6GPU7 and launch under pipel |
| 2026-09-14 20:08:54 | [other](20260914-200854_other.md) | M195 duplicate physical seed ValueError at step18  | No blind restart or loss-semantic patch; preserve deathwatch |
| 2026-09-14 20:09:39 | [next_batch](20260914-200939_next_batch.md) | User requests actual boundary/adjacency verification  | Complete284-bank71-scene CPU contact audit; retain no new tr |
| 2026-09-14 20:20:00 | [manual](20260914-202000_manual.md) | CPS crash root cause reproduced on native249-SP scene with25 | Repair1: average native logits within identical physical see |
| 2026-09-14 22:34:59 | [next_batch](20260914-223459_next_batch.md) | User requests complete new experiment design-to-training loo | Admit M196-CTF-HCG-CSORT-BCA;commit independent M95 branch,s |
| 2026-09-14 22:51:26 | [manual](20260914-225126_manual.md) | User requests server4 first  | Relocate only M196 BCA from server6 GPU7 to server4 GPU0;res |
| 2026-09-15 00:12:42 | [next_batch](20260915-001242_next_batch.md) | Design budget1 active3/4: is joint boundary count restoratio | Reject joint count-plus-assignment as exact boundary BCE; ad |
| 2026-09-15 02:12:14 | [next_batch](20260915-021214_next_batch.md) | Budget1 active3/4: can count-only likelihood correct boundar | Reject count-only inversion rationale; admit0/1; preserve al |
| 2026-09-15 04:15:35 | [next_batch](20260915-041535_next_batch.md) | Budget1 active3/4: does unsigned contact-edge loss identify  | Reject orientation rationale; admit0/1; retain SCM CPS BCA a |
| 2026-09-15 06:10:20 | [next_batch](20260915-061020_next_batch.md) | Active3/4 budget1: is oriented contact conditional assignmen | Admit0/1; reject pairwise primitive as independent core; ret |
| 2026-09-15 08:10:27 | [next_batch](20260915-081027_next_batch.md) | Budget1: admit independently component-conditioned boundary  | Admit0/1; reject unsupported component regrouping; retain M1 |
| 2026-09-15 11:13:08 | [next_batch](20260915-111309_next_batch.md) | Budget1: does the 0808 homogeneous-component objection apply | Correct rejection rationale; admit0 new variants; retain M19 |
| 2026-09-15 13:10:19 | [next_batch](20260915-131019_next_batch.md) | Budget1: does component conditioning add assignment supervis | Admit0/1; retain all3 runs. Component conditioning removes c |
| 2026-09-15 15:10:30 | [next_batch](20260915-151030_next_batch.md) | Budget1: can saved whole-mask component counts satisfy the n | Admit0/1; retain all3 runs. Native boundary-component incide |
| 2026-09-15 16:09:03 | [manual](20260915-160903_manual.md) | User requests executable pipeline closure optimization  | Enable cluster-only closure policy,persistent candidate cont |
| 2026-09-15 16:11:43 | [next_batch](20260915-161143_next_batch.md) | Does native TRAIN contain disconnected induced boundaries?  | Capture complete; continue matched full-loss validation, no  |
| 2026-09-15 16:21:26 | [next_batch](20260915-162126_next_batch.md) | Component conditioning native full-loss gate  | Retain validation, admit zero. Native paired gradients and c |
| 2026-09-15 17:16:06 | [next_batch](20260915-171606_next_batch.md) | Component parameter-step pairing control  | Retain validation; shared-forward gradient comparison next;  |
| 2026-09-15 18:11:41 | [next_batch](20260915-181142_next_batch.md) | Component shared-forward parameter validation disposition  | FP32 paired updates and duplicate-gradient control PASS; ret |
| 2026-09-15 19:11:57 | [next_batch](20260915-191157_next_batch.md) | Does matched AMP validate component conditioning?  | Retain validation: finite scaled backward and updates pass;  |
| 2026-09-15 20:12:28 | [next_batch](20260915-201228_next_batch.md) | Fixed-state AMP outcome comparison admissible?  | Retain validation; query-index outcomes invalid; next fixed- |
| 2026-09-15 21:02:04 | [early_stop](20260915-210204_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cps]  | kill PID=3496122 on server-6 gpu=7 |
| 2026-09-15 21:12:46 | [next_batch](20260915-211246_next_batch.md) | Fixed support AMP residual persists; M195 terminal event  | Keep component validation; isolate U-Net next. No enqueue or |
| 2026-09-15 21:12:46 | [question](20260915-211246_question.md) | M195 registry done_earlystop versus native mid-epoch stop  | Reconcile exact PID/log monitor termination provenance on ne |
| 2026-09-15 22:12:47 | [next_batch](20260915-221247_next_batch.md) | Component repeatability: aligned U-Net localization  | Keep validation; next replay backbone outputs with fixed sup |
| 2026-09-15 22:27:49 | [route_change](20260915-222749_route_change.md) | User restricts all future cluster execution to server4  | Restrict training and native diagnostics to server4 GPU0/1;d |
| 2026-09-15 22:35:07 | [next_batch](20260915-223507_next_batch.md) | Execute pending fixed-backbone full-loss control on server4  | Completed FP32 batch1 replay;continue candidate validation,n |
| 2026-09-15 22:46:16 | [next_batch](20260915-224616_next_batch.md) | Continue candidate native verification on server4  | Two FP32 end-to-end gradient batches completed with diagnost |
| 2026-09-15 23:12:48 | [next_batch](20260915-231248_next_batch.md) | Component free-sampling native validation resource availabil | Block pending free server-4 GPU; retry after 2026-09-16T00:0 |
| 2026-09-15 23:14:41 | [other](20260915-231441_other.md) | Existing fixed-E2E evidence hash mismatch in postflight  | Correct manifest hash only; preserve artifact and scientific |
| 2026-09-15 23:21:54 | [route_change](20260915-232154_route_change.md) | Capacity gap must trigger research every tick  | Enable research_on_capacity_gap without steady/cooldown wait |
| 2026-09-15 23:29:07 | [next_batch](20260915-232907_next_batch.md) | Continue admission work while server4 GPUs occupied  | Verified recursive-cardinality disjoint-subset prior art;gro |
| 2026-09-15 23:33:22 | [route_change](20260915-233322_route_change.md) | User adds server6 GPU7 two slots  | Restore server6 allowed_gpus7 max_tasks2;retain server4GPU0/ |
| 2026-09-16 00:00:44 | [route_change](20260916-000044_route_change.md) | Does complete native validation support pushing component co | Reject current standalone BCCA proposal for admission;retain |
| 2026-09-16 00:11:21 | [next_batch](20260916-001121_next_batch.md) | Same-forward TRAIN coverage:33 recoverable versus5 mask-limi | Execute fixed16batch QLA anchor-access deletion diagnostic w |
| 2026-09-16 00:15:04 | [next_batch](20260916-001505_next_batch.md) | QLA anchor deletion complete:118eligible32scenes,repeat delt | No admission;inspect scene0220 ann21 role spans and selected |
| 2026-09-16 00:15:44 | [next_batch](20260916-001544_next_batch.md) | Does same-forward coverage justify filling three training sl | Continue semantic error diagnosis;admit zero new variants;pr |
| 2026-09-16 00:25:16 | [route_change](20260916-002516_route_change.md) | Identity capture reveals anchor deletion included target rem | Do not interpret anchor deletion as pure anchor intervention |
| 2026-09-16 00:30:02 | [next_batch](20260916-003002_next_batch.md) | Native semantic gradient audit complete20expressions205repea | Continue role-ambiguity mechanism derivation and original-so |
| 2026-09-16 00:38:13 | [next_batch](20260916-003813_next_batch.md) | Does removing repeated-head other tags improve full-paramete | Do not admit tag-removal variant. Preserve completed16batch  |
| 2026-09-16 00:48:26 | [route_change](20260916-004826_route_change.md) | Can bare latent-role marginalization or binary graph constra | Reject independent binary marginal,shared binary-role likeli |
| 2026-09-16 00:49:54 | [next_batch](20260916-004954_next_batch.md) | Same-forward selected instance semantic names now verified  | Do not assume anchor-object confusion:scene0220ann21 wrongin |
| 2026-09-16 01:00:27 | [next_batch](20260916-010027_next_batch.md) | Does decoder inverse coordinate transport outperform mismatc | Do not admit inverse-coordinate variant;record actual frame  |
| 2026-09-16 01:13:38 | [route_change](20260916-011338_route_change.md) | Resume due work using physical instance collision evidence  | Close unsupported frame and role proposals;continue coverage |
| 2026-09-16 01:23:39 | [next_batch](20260916-012339_next_batch.md) | Does native instance feature evidence justify a new training | Continue same-forward coverage work;record within-scene feat |
| 2026-09-16 01:32:31 | [next_batch](20260916-013231_next_batch.md) | Do five fixed collision pairs lose language evidence or only | Complete native shared-support collision capture;retain cove |
| 2026-09-16 01:37:26 | [next_batch](20260916-013726_next_batch.md) | Does uniform token-instance preference imply harmful languag | Completed native layerwise geometry;do not admit rank regula |
| 2026-09-16 01:48:18 | [next_batch](20260916-014818_next_batch.md) | Does lexical identity degradation justify static-key dynamic | Record native lexical retrieval and sixbranch QLA controls;n |
| 2026-09-16 02:02:17 | [route_change](20260916-020217_route_change.md) | Is static lexical-key memory novel and are M95 errors baseli | Reject bare static lexical-key dynamic-value proposal for co |
| 2026-09-16 02:08:14 | [next_batch](20260916-020814_next_batch.md) | Do M95 regressions arise at final cluster message injection? | Close immediate-message explanation for these regressions;do |
| 2026-09-16 02:12:24 | [next_batch](20260916-021224_next_batch.md) | Resolve cached/native metric convention before mechanism att | Keep strict >0.5 cached TRAIN classification; preserve concu |
| 2026-09-16 02:20:25 | [next_batch](20260916-022025_next_batch.md) | Can visual-only paired description-difference reconstruction | Reject bare paired squared reconstruction; preserve M196 and |
| 2026-09-16 02:33:54 | [next_batch](20260916-023354_next_batch.md) | Does fixed-scene same-target wording produce grounding disag | Advance same-target diagnosis:128expressions64pairs32TRAINsc |
| 2026-09-16 02:39:19 | [next_batch](20260916-023919_next_batch.md) | Are same-target grounding discrepancies explained by differe | Complete four-branch native support control:all8disagreement |
| 2026-09-16 02:46:58 | [next_batch](20260916-024658_next_batch.md) | Does physical same-target scene-state interchange have a dis | Keep candidate provisional:matched128TRAIN same-target swap  |
| 2026-09-16 02:57:22 | [next_batch](20260916-025722_next_batch.md) | Is native same-target interchange trainable without regroupi | Complete coverage and two full-backward probes;specify unifo |
| 2026-09-16 03:07:13 | [route_change](20260916-030713_route_change.md) | Does the proposed scene-state interchange address query-cont | Reject current physical-scene-state-interchange admission. M |
| 2026-09-16 03:19:27 | [route_change](20260916-031927_route_change.md) | Does same-target marginal likelihood repair hard-description | Reject bare marginal-likelihood aggregation after analytic g |
| 2026-09-16 03:19:29 | [next_batch](20260916-031929_next_batch.md) | Identifying controls after interchange rejection  | Preserve concurrent native rejection; require controls separ |
| 2026-09-16 03:33:11 | [next_batch](20260916-033311_next_batch.md) | Does input modality addition erase same-class distinguishing | Complete native123TRAIN decomposition;retain descriptive fin |
| 2026-09-16 03:38:52 | [next_batch](20260916-033852_next_batch.md) | Does either projected input modality fail to affect groundin | Complete native fivebranch mean-exchange control;both modali |
| 2026-09-16 03:48:07 | [next_batch](20260916-034807_next_batch.md) | Can generic reconstruction or relation prediction qualify as | Do not admit generic masked reconstruction or relation class |
| 2026-09-16 03:52:47 | [route_change](20260916-035248_route_change.md) | Can target displacement cycle or consensus be a distinct gro | Reject bare offset-cycle-consensus proposal before model imp |
| 2026-09-16 03:56:32 | [next_batch](20260916-035632_next_batch.md) | Are same-class errors explained by missing attribute supervi | Complete native123TRAIN token-map audit;do not admit missing |
| 2026-09-16 04:07:26 | [next_batch](20260916-040726_next_batch.md) | Can entity ownership explain a concrete semantic-supervision | Continue repeated-mention ownership as a distinct diagnostic |
| 2026-09-16 04:17:22 | [next_batch](20260916-041722_next_batch.md) | Does a binary latent mention-role mixture identify repeated  | Reject unidentified role-mixture formula;retain mention-owne |
| 2026-09-16 04:19:07 | [next_batch](20260916-041907_next_batch.md) | Recipient dependence identifying control and corrected pair  | Continue observable task-specific derivation; preserve concu |
| 2026-09-16 04:23:06 | [next_batch](20260916-042307_next_batch.md) | Does mention-role draft repeat previously closed anchor-toke | Record overlap explicitly;do not reopen independent/shared r |
| 2026-09-16 04:31:16 | [next_batch](20260916-043116_next_batch.md) | Can existing scene geometry provide observable relation evid | Complete strict vertical-relation bounds on native TRAIN geo |
| 2026-09-16 04:39:30 | [next_batch](20260916-043930_next_batch.md) | Does distributional direction preserve geometry lost by cent | Implement and verify sorted O(NlogN) ordered-mass primitive  |
| 2026-09-16 04:44:05 | [next_batch](20260916-044405_next_batch.md) | Is strict vertical relation applicability limited to the one | Complete fullTRAIN annotationgraph inventory;retain1717candi |
| 2026-09-16 04:58:17 | [next_batch](20260916-045817_next_batch.md) | Does native anchor attention respond to noun identity on fix | Complete107 matched-length noun interventions; retain identi |
| 2026-09-16 05:11:10 | [next_batch](20260916-051110_next_batch.md) | Does the completed anchor perturbation identify a usable rel | Complete10of11 fixedgeometry relation controls;do not admit  |
| 2026-09-16 05:14:36 | [next_batch](20260916-051437_next_batch.md) | Does saved noun sensitivity identify relation output or repe | Require actual relation-node targeting and signed support-al |
| 2026-09-16 05:19:19 | [next_batch](20260916-051919_next_batch.md) | Can existing target labels and parameter sharing identify a  | Record CoT3DRef and NS3D overlap plus sharedcontext countere |
| 2026-09-16 05:23:45 | [next_batch](20260916-052345_next_batch.md) | Does modality consumer indexing provide a concrete new-varia | Complete SPindex contract;no mismatch claim or visibilitygat |
| 2026-09-16 05:31:04 | [next_batch](20260916-053104_next_batch.md) | Does missing negation span explain native same-class failure | CompleteTRAINinventory and onecase no-to-a native control;do |
| 2026-09-16 05:37:25 | [next_batch](20260916-053725_next_batch.md) | Can negative-existence be implemented as inverted normalized | Record EaSe priorart and static existence countermodels;no n |
| 2026-09-16 05:41:21 | [next_batch](20260916-054121_next_batch.md) | Can existing semantic labels identify the observed anchors?  | Complete32TRAINsemantic support audit;retain ignoredlabels a |
| 2026-09-16 05:46:45 | [next_batch](20260916-054645_next_batch.md) | Are ignored20class nouns actually missing from existing supe | Correct absenceclaim;rawlabels verified on5522145points and  |
| 2026-09-16 05:58:23 | [next_batch](20260916-055823_next_batch.md) | Can raw-category spatial fields resolve instance binding wit | Do not admit category-union-only integration; retain active  |
| 2026-09-16 06:08:42 | [other](20260916-060842_other.md) | Does semantic alignment depend on invalid padding?  | Archive confirmed native loss padding leak and masked diagno |
| 2026-09-16 06:15:22 | [next_batch](20260916-061522_next_batch.md) | Can existing language-conditioned masks serve as an instance | Require explicit non-target instance representation in a com |
| 2026-09-16 06:16:21 | [next_batch](20260916-061621_next_batch.md) | Does directed graph evidence identify repeated-noun roles?  | Retain diagnosis; derive visual correspondence next. No admi |
| 2026-09-16 06:22:24 | [next_batch](20260916-062225_next_batch.md) | Can all-instance seed-mask supervision be added to current t | Require separate physical-instance and referent mask semanti |
| 2026-09-16 06:29:08 | [next_batch](20260916-062908_next_batch.md) | Does the complete instance-distribution read pass beyond mat | Keep prototype not admitted:sevenCUDAchecks pass,but generic |
| 2026-09-16 06:38:00 | [next_batch](20260916-063800_next_batch.md) | Does the proposed distributional read transport geometry ind | Do not admit current value-only relation read; preserve inst |
| 2026-09-16 06:43:29 | [route_change](20260916-064329_route_change.md) | Does fixed TRAIN evidence support replacing centroid geometr | Shelve draft0626 on its present motivation; retain instance- |
| 2026-09-16 06:52:00 | [next_batch](20260916-065200_next_batch.md) | Can current noun LIA weights be treated as instance correspo | Keep current attention as context read,not verified anchor p |
| 2026-09-16 06:58:05 | [next_batch](20260916-065805_next_batch.md) | Can separate physical-instance outputs receive native superv | Retain verified component interface only;no standalone varia |
| 2026-09-16 07:01:13 | [early_stop](20260916-070113_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bca]  | kill PID=3237667 on server-4 gpu=0 |
| 2026-09-16 07:02:24 | [next_batch](20260916-070224_next_batch.md) | Does the independent instance branch fit historical inferenc | Retain component feasibility,not full resource admission;com |
| 2026-09-16 07:06:27 | [question](20260916-070627_question.md) | Why was M196 killed with monitor no_improve11 while exact an | Archive terminal evidence;do not restart or claim patience-c |
| 2026-09-16 07:11:09 | [other](20260916-071109_other.md) | Can M196 erroneous count11 be reproduced without changing va | Archive regression:unbounded substring conflates mIOU and sp |
| 2026-09-16 07:13:27 | [next_batch](20260916-071327_next_batch.md) | Does category-set supervision identify the retained instance | Do not admit bare category-set loss as instance-identity rat |
| 2026-09-16 07:22:53 | [next_batch](20260916-072253_next_batch.md) | Can instance-boundary cues justify a qualified new variant?  | Retain stable coverage diagnosis; reject target-wide boundar |
| 2026-09-16 07:29:34 | [next_batch](20260916-072934_next_batch.md) | Does missing anchor annotation universally prevent a trainab | Correct the overbroad admission inference; retain novelty an |
| 2026-09-16 07:37:28 | [other](20260916-073728_other.md) | Can the status automation execute a stale mutating monitor a | Route legacy project-agents cluster CLI to canonical Codex r |
| 2026-09-16 07:59:07 | [next_batch](20260916-075907_next_batch.md) | Does same-name misselection come from the FPS cluster partit | Refute the strong form;record cluster contamination as a sta |
| 2026-09-16 09:17:07 | [next_batch](20260916-091707_next_batch.md) | Which ownership controls are required before a full relation | Require owned-endpoint, relocated-endpoint and predicate-dis |
| 2026-09-16 09:23:42 | [route_change](20260916-092342_route_change.md) | Does the multi-scale cluster context carry non-redundant evi | Close the multi-scale cluster/scale/pooling/readback axis on |
| 2026-09-16 09:32:02 | [next_batch](20260916-093202_next_batch.md) | Is the33-case referent-selection failure a calibration probl | Classify it as missing evidence,not miscalibration:refuse an |
| 2026-09-16 09:40:07 | [next_batch](20260916-094007_next_batch.md) | Do any existing per-query scores separate the correct query  | Record that all three existing scores rank the correct query |
| 2026-09-16 09:58:23 | [route_change](20260916-095823_route_change.md) | Does any existing trained signal already carry the referent  | Close existing-evidence recombination as a route on evidence |
| 2026-09-16 10:14:04 | [route_change](20260916-101404_route_change.md) | Does OHRS establish supervision as the cause?  | Return OHRS to diagnosis; reject current causal and novelty  |
| 2026-09-16 10:15:06 | [route_change](20260916-101506_route_change.md) | Is OHRS (object-hypothesis referent supervision) admissible  | Reject OHRS as the contribution and do not enqueue it;record |
| 2026-09-16 10:15:12 | [question](20260916-101512_question.md) | The only evidence-supported fix for the diagnosed bottleneck | Log for user awareness;continue autonomous search inside the |
| 2026-09-16 10:23:31 | [next_batch](20260916-102331_next_batch.md) | Does the deployed referent score follow the training positiv | Confirm the operational root cause as seed-driven scoring;re |
| 2026-09-16 10:33:36 | [next_batch](20260916-103336_next_batch.md) | What do the encoder instance features actually encode for sa | Record that the encoder encodes category not identity,and th |
| 2026-09-16 10:43:35 | [route_change](20260916-104335_route_change.md) | Is the deployed referent failure caused by a wrong positive  | Correct the diagnosis:the positive set is NOT the problem(it |
| 2026-09-16 10:50:35 | [next_batch](20260916-105035_next_batch.md) | Is the 2D modality (clip_feat -> superpoint) indexing correc | Close the modality provenance question:no indexing defect;do |
| 2026-09-16 11:00:09 | [next_batch](20260916-110009_next_batch.md) | Does the paired 2D modality carry instance-level identity th | Record a positive asymmetry as the first constructive lead:t |
| 2026-09-16 11:10:52 | [route_change](20260916-111052_route_change.md) | Does lower target-to-wrong neighbour rank identify preserved | Retract identity-loss inference from neighbour ranks; retain |
| 2026-09-16 11:15:17 | [route_change](20260916-111517_route_change.md) | Does the 2D identity lead cash out under the language, i.e.  | Close the 2D identity lead as a route and record an impasse: |
| 2026-09-16 11:21:00 | [next_batch](20260916-112100_next_batch.md) | Does judging recoverability by the single maximum-IoU query  | Adopt best-rank-over-ALL-acceptable-masks as the recoverabil |
| 2026-09-16 11:23:52 | [next_batch](20260916-112352_next_batch.md) | Do the corrected selection metrics survive scene clustering, | Harden the evidence base with scene-clustered CIs and record |
| 2026-09-16 11:31:15 | [route_change](20260916-113115_route_change.md) | The 09-13 decisions refused relabeling because descriptive a | Run the missing causal intervention;establish causality;sepa |
| 2026-09-16 11:37:57 | [next_batch](20260916-113757_next_batch.md) | Is the referent identity needed by the causal fix present in | Close the readout axis properly:even a nonlinear scene-gener |
| 2026-09-16 11:40:47 | [question](20260916-114047_question.md) | Is the objective reachable without a user scope decision? (a | Declare an impasse and hold the slots empty per goal.json ru |
| 2026-09-16 11:45:32 | [manual](20260916-114532_manual.md) | User selected option B: amend goal.json to open a specific n | Open the referent-supervision axis via an append-only goal.j |
| 2026-09-16 12:12:22 | [next_batch](20260916-121222_next_batch.md) | Can the existing PIRS implementation proceed to admission af | Hold current PIRS at design: seven static tests expose targe |
| 2026-09-16 12:19:48 | [next_batch](20260916-121948_next_batch.md) | Does PIRS pass the mechanical gates and should M197-PIRS be  | Admit and enqueue M197-PIRS on server6 gpu7:independent mode |
| 2026-09-16 12:22:11 | [queue_push](20260916-122211_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M197 PIRS provenence-invariant referent supervision (ref |
| 2026-09-16 12:26:33 | [queue_push](20260916-122633_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M197 PIRS provenence-invariant referent supervision (ref |
| 2026-09-16 12:31:04 | [other](20260916-123104_other.md) | M197-PIRS launch died with torch_shm_manager socket error; i | Repair the launcher environment rather than the candidate:pr |
| 2026-09-16 13:11:24 | [route_change](20260916-131124_route_change.md) | How should due diagnosis records follow scope B and the runn | Preserve M197 training and all bans; supersede old scope-blo |
| 2026-09-16 13:44:51 | [manual](20260916-134451_manual.md) | User instruction 2026-09-16: change the project allocation t | Apply it as an append-only goal.json constraint(15->16;banne |
| 2026-09-16 13:47:03 | [other](20260916-134703_other.md) | The allocation edit changed goal.json, so M197-PIRS's admiss | Refresh the receipt's goal_sha256 to the current value and k |
| 2026-09-16 14:12:28 | [other](20260916-141228_other.md) | Postflight rejects a verified training experiment whose hypo | Resolve explicit experiment_id with unique verified queue ma |
| 2026-09-16 15:15:49 | [other](20260916-151549_other.md) | Resume shared native capture work before new design  | Completed two-batch M95 TRAIN support capture on authorized  |
| 2026-09-16 16:18:03 | [other](20260916-161803_other.md) | Does support-bound feature retrieval justify a second mechan | Retain diagnosis only: four-scene all-instance retrieval doe |
| 2026-09-16 17:14:46 | [other](20260916-171447_other.md) | How should recoverable same-class errors be identified in th | Require an oracle-acceptable query, failed selected query, u |
| 2026-09-16 18:11:29 | [other](20260916-181129_other.md) | How should unresolved native superpoints enter physical endp | Bind classes through exact sampled point instance provenance |
| 2026-09-16 19:11:00 | [other](20260916-191100_other.md) | Native capture retry and paired evaluation contract  | Defer native capture while GPU7 has PIRS and a foreign train |
| 2026-09-16 19:16:57 | [question](20260916-191657_question.md) | Closure ID linkage failure  | Record unhealthy postflight; preserve stable research ID and |
| 2026-09-16 20:11:53 | [other](20260916-201153_other.md) | Exact input identity for paired captures  | Require transformed native-input and checkpoint hashes in a  |
| 2026-09-16 21:11:08 | [other](20260916-211108_other.md) | Paired sampling eligibility  | Require identical recorded FPS support and order; validate b |
| 2026-09-16 22:10:56 | [other](20260916-221056_other.md) | Hierarchical sampling missing from matched capture  | Require hierarchical partition outputs in addition to entry  |
| 2026-09-16 23:13:50 | [other](20260916-231350_other.md) | How should the next native M95/PIRS hierarchy comparison be  | Require versioned capture of entry FPS plus hierarchical FPS |
| 2026-09-17 04:11:06 | [other](20260917-041106_other.md) | Shared frozen paired-capture gate remains blocked by authori | Mark all eight due diagnosis candidates blocked; retry after |
| 2026-09-17 05:11:40 | [question](20260917-051140_question.md) | PIRS core novelty after direct VarifocalNet check  | Keep M197 running and mark novelty unresolved; require direc |
| 2026-09-17 06:15:21 | [route_change](20260917-061521_route_change.md) | Direct 3D-RES source audit for PIRS core novelty  | Freeze PIRS as prior-art evidence, let M197 terminate, admit |
| 2026-09-17 08:15:55 | [route_change](20260917-081555_route_change.md) | Does an expression-level top-1/listwise referent loss define | Reject decision-aligned referent supervision before design;  |
| 2026-09-17 09:11:39 | [other](20260917-091139_other.md) | Closure ID linkage and due-capture capacity retry  | Resolved the literal closure ID mismatch by adding explicit  |
| 2026-09-17 11:13:39 | [other](20260917-111339_other.md) | Terminal PIRS evaluator identity and hierarchy binding  | Advance the overdue static contract while GPU7 remains full: |
| 2026-09-17 12:18:19 | [route_change](20260917-121819_route_change.md) | Does same-target alternate-description consistency define a  | Reject same-target-description-consistency before design, ad |
| 2026-09-17 13:12:34 | [route_change](20260917-131234_route_change.md) | Should same-forward coverage remain a pending native retry a | Reject same-forward coverage as a pending retry route; retai |
| 2026-09-17 14:12:41 | [route_change](20260917-141241_route_change.md) | Should paired baseline/candidate captures be accepted withou | Tighten the frozen paired-capture contract: bind the config  |
| 2026-09-17 15:18:58 | [route_change](20260917-151858_route_change.md) | Does paired factual/counterfactual 3D scene evidence supervi | Reject counterfactual-evidence supervision before design and |
| 2026-09-17 16:16:03 | [other](20260917-161603_other.md) | Can a paired M95/PIRS capture be accepted when model-package | Require a model_source_sha256 for every bound capture, rejec |
| 2026-09-17 17:12:40 | [route_change](20260917-171240_route_change.md) | May paired terminal captures use arbitrary config/model-sour | Require each capture config hash and model-source hash to ma |
| 2026-09-17 18:14:45 | [route_change](20260917-181445_route_change.md) | Does language-guided text-conditioned candidate selection de | Reject language-guided query selection before design; admit  |
| 2026-09-17 22:15:54 | [route_change](20260917-221554_route_change.md) | Does an identity-exclusivity score target define a new core  | Reject referent-exclusivity supervision before design; admit |
| 2026-09-18 05:18:02 | [route_change](20260918-051802_route_change.md) | Does relation-conditioned transport of raw 2D identity evide | Reject relation-conditioned identity transport before design |
| 2026-09-18 13:39:06 | [other](20260918-133906_other.md) | No new task has been pushed for hours: is that a scientific  | Both,fixed the operational half first:research_work.json had |
| 2026-09-18 16:20:16 | [other](20260918-162016_other.md) | What control design follows from the 33-failure referent met | Keep native capture blocked; stratify exact same-class and r |
| 2026-09-18 18:12:01 | [other](20260918-181201_other.md) | Which failure-control strata are admissible for the next pai | Use 31 exact same-class observed-control pairs as the primar |
| 2026-09-18 21:15:44 | [route_change](20260918-211544_route_change.md) | Should the 31 observed-failure pairs be promoted as the prim | Reject promotion; retain them only as failure-local diagnost |
| 2026-09-18 23:12:23 | [route_change](20260918-231223_route_change.md) | Which registry should anchor the population-level referent t | Freeze the archived 123-expression seed-1999 TRAIN cohort be |
| 2026-09-19 00:16:51 | [route_change](20260919-001651_route_change.md) | Can the open design slot be filled with a novel, admissible  | Admit no new training variant and keep the slot empty; pre-r |
| 2026-09-19 01:30:55 | [route_change](20260919-013055_route_change.md) | Which executable boundary should advance the blocked referen | Add and pre-register a seed-membership object-capture adapte |
| 2026-09-19 02:12:06 | [route_change](20260919-021206_route_change.md) | Which executable boundary remains after the native-to-evalua | Add a fail-closed native-expression producer that projects f |
| 2026-09-19 03:16:51 | [route_change](20260919-031651_route_change.md) | Design mode has one candidate slot, but the native-capture r | Keep the slot empty; do not admit a new variant. Retry the s |
| 2026-09-19 05:13:10 | [route_change](20260919-051310_route_change.md) | Design mode has one open slot, but M197-PIRS is preterminal  | Admit no new training candidate; keep the slot empty, preser |
| 2026-09-19 07:11:48 | [route_change](20260919-071148_route_change.md) | GPU7 remained at the two-process cap after the due retry. Sh | Keep the seven referent diagnostics blocked and launch nothi |
| 2026-09-19 08:13:31 | [route_change](20260919-081332_route_change.md) | GPU7 remained at the two-process cap after the 08:07 due ret | Keep all seven due stages blocked and launch nothing; persis |
| 2026-09-19 09:13:37 | [route_change](20260919-091337_route_change.md) | GPU7 remained at the two-process cap after the 09:07 retry.  | Keep all seven due stages blocked and launch nothing; add fa |
| 2026-09-19 10:15:08 | [route_change](20260919-101508_route_change.md) | GPU7 remained at the two-process cap after the 10:07 retry.  | Keep all seven due stages blocked and launch nothing; add a  |
| 2026-09-19 11:11:15 | [route_change](20260919-111115_route_change.md) | Can the GPU-blocked native referent capture chain advance by | Keep the seven due stages blocked and launch nothing; requir |
| 2026-09-19 12:11:13 | [route_change](20260919-121113_route_change.md) | Does the frozen permutation control have calibrated false-po | Promote permutation p-values to calibrated diagnostics only  |
| 2026-09-19 13:08:45 | [route_change](20260919-130845_route_change.md) | Should the seven due native-capture stages be retried despit | Keep all seven stages blocked and retry at 2026-09-19T14:07: |
| 2026-09-19 14:11:32 | [route_change](20260919-141132_route_change.md) | Should the seven due stages remain blocked while advancing n | Keep all seven stages blocked and retry at 2026-09-19T15:07: |
| 2026-09-19 16:12:36 | [route_change](20260919-161236_route_change.md) | How should the interrupted 15:07 native-chain validation be  | Persist the interrupted 15:07 self-test as recovered evidenc |
| 2026-09-19 17:19:51 | [route_change](20260919-171951_route_change.md) | Does the frozen adapter preserve native query ownership?  | Require FPS-to-superpoint composition and strict expression  |
| 2026-09-19 18:13:14 | [route_change](20260919-181314_route_change.md) | Can target-mask IoU serve as the native objectness negative  | Reject target-IoU fallback; require explicit independently j |
| 2026-09-19 19:14:08 | [route_change](20260919-191408_route_change.md) | Can available native axes provide an independent object-rank | Reject any-instance membership as a rank control because see |
| 2026-09-19 20:15:09 | [other](20260919-201509_other.md) | How to bind geometry to exact native support without changin | Adopt separate criterion_geometry_nuisance_v1; compose local |
| 2026-09-19 21:16:53 | [other](20260919-211653_other.md) | How should runtime geometry observations preserve native ide | Use a separate criterion runtime observer with transitive lo |
| 2026-09-19 22:12:11 | [other](20260919-221211_other.md) | How should geometry sidecars join the failure registry witho | Require full physical identity bindings; retain missing and  |
| 2026-09-19 23:13:31 | [other](20260919-231332_other.md) | How can the fixed failure registry bind native observations  | Add a separate explicit metadata-plus-physical binding expor |
| 2026-09-20 00:14:51 | [other](20260920-001451_other.md) | How to connect fixed registry bindings to native geometry ca | Use a separate bounded registry-aware runner with original d |
| 2026-09-20 01:13:28 | [other](20260920-011328_other.md) | Can partial registry-runner output be mistaken for completed | Publish JSON atomically without overwrite and require a comp |
| 2026-09-20 02:15:57 | [other](20260920-021557_other.md) | Does the fixed registry resolve against actual remote TRAIN  | Accept 31 unique source-derived metadata plans as planning e |
| 2026-09-20 03:14:56 | [other](20260920-031456_other.md) | Missing remote diagnostic sources prevented the due native a | Stage immutable diagnostic-only bundle and validate actual T |
| 2026-09-20 04:14:35 | [other](20260920-041435_other.md) | Physical item readiness and manifest mismatch  | Retain exact native inputs and three physical joins; fix CRL |
| 2026-09-20 05:12:24 | [other](20260920-051224_other.md) | Can the saved TRAIN inputs be replayed without changing phys | Preserve verified saved inputs and CPU-collated batches as e |
| 2026-09-20 06:15:52 | [other](20260920-061552_other.md) | How to resume saved geometry capture without changing physic | Accept separately hashed exact-batch adapter as CPU-verified |
| 2026-09-20 07:13:02 | [other](20260920-071302_other.md) | Advance missing physical coverage and exact saved replay exe | Accept two additional CPU physical bindings and separate sav |
| 2026-09-20 08:13:49 | [other](20260920-081349_other.md) | Accept native saved-input replay readiness for groups2690/30 | Accept exact CPU collation and replay identity checks plus s |
| 2026-09-20 09:15:14 | [other](20260920-091515_other.md) | Accept recovered CPU replay and four new physical bindings?  | Recover interrupted0815 replay evidence without rerunning sa |
| 2026-09-20 09:43:30 | [manual](20260920-094330_manual.md) | 将 cluster 后续训练与原生诊断改到 server-4 两� | server-4 GPU0/1 各一槽作为唯一新任务调度容量� |
| 2026-09-20 09:54:10 | [other](20260920-095410_other.md) | M197-PIRS 在迁移到 server-4 双卡期间进程消失，� | 将 M197 归档为 stopped_unknown；禁止在 dispatch-disa |
| 2026-09-20 10:13:24 | [route_change](20260920-101324_route_change.md) | Saved diagnostic continuation still targets dispatch-disable | Suspend native CPU and GPU continuation on server-6; retain  |
| 2026-09-20 12:14:14 | [other](20260920-121414_other.md) | How should saved3040/3893 loading progress after server-4 SS | Implement a separate source-preserving relocated loader and  |
| 2026-09-20 13:14:46 | [other](20260920-131446_other.md) | Resume relocated saved-input collation while server-4 SSH is | Use existing SavedPhysicalLocation through separately tested |
| 2026-09-20 14:17:12 | [other](20260920-141712_other.md) | Continue due saved-input validation with authorized host unr | Use native field validator and existing FrozenDataset callba |
| 2026-09-20 15:15:59 | [other](20260920-151559_other.md) | How to bind immutable producer imports for the existing CPU  | Use byte-pinned producer imports in a fresh child process; r |
| 2026-09-20 16:15:01 | [other](20260920-161501_other.md) | How should the existing CPU diagnostic bootstrap proceed whi | Keep production CLI preflight-only; integrate byte-pinned im |
| 2026-09-20 17:12:00 | [other](20260920-171200_other.md) | How to resume diagnostic isolation while server-4 SSH is ref | Implement a fail-closed bubblewrap probe launcher; keep nati |
| 2026-09-20 18:12:42 | [other](20260920-181242_other.md) | How should the existing diagnostic boundary join probe and c | Use one isolated CPU child for probe, pinned imports, existi |
| 2026-09-20 19:16:20 | [other](20260920-191621_other.md) | How to assemble relocated saved inputs without changing capt | Use real BindingExporter factory assembly with original regi |
| 2026-09-20 20:16:04 | [other](20260920-201604_other.md) | How to construct the existing relocated saved-data diagnosti | Add a pinned zero-argument factory; require constructor asse |
| 2026-09-20 21:15:08 | [other](20260920-211508_other.md) | Does the pinned native factory integrate with the same-child | Accept the eleven synthetic integration checks as engineerin |
| 2026-09-20 22:15:08 | [other](20260920-221508_other.md) | How to hand off the scratch sandbox command to the existing  | Use a separately pinned stdlib bootstrap and producer manife |
| 2026-09-20 23:13:26 | [other](20260920-231326_other.md) | What remains before accepting saved collation output?  | Add read-only host receipt and batch-byte verification to th |
| 2026-09-21 00:14:11 | [other](20260921-001411_other.md) | How should saved collation completion remain bounded before  | Wire an internal bounded process adapter to existing receipt |
| 2026-09-21 01:12:36 | [other](20260921-011236_other.md) | Prepare the saved diagnostic host handoff without premature  | Add pinned host-input and private-scratch preparation; retai |
| 2026-09-21 02:17:14 | [other](20260921-021714_other.md) | What dependencies remain before the saved-only native handof | Record bounded direct dependency and constructor requirement |
| 2026-09-21 03:14:11 | [other](20260921-031411_other.md) | How should the prepared saved-only diagnostic connect to ver | Use one internal adapter with frozen independent expectation |
| 2026-09-21 04:12:18 | [other](20260921-041218_other.md) | How should relocated saved batches enter exact diagnostic re | Use a separate location-aware replay adapter with independen |
| 2026-09-21 05:14:10 | [other](20260921-051410_other.md) | How to connect relocated saved batches to existing geometry  | Add a separate internal server-4 saved geometry driver with  |
| 2026-09-21 06:13:08 | [other](20260921-061308_other.md) | Can the saved model diagnostic use CPU collation inventory a | No. Require separate verified model weights, strict M95 chec |
| 2026-09-21 07:13:07 | [other](20260921-071307_other.md) | How should the saved GPU diagnostic validate device identity | Require full physical GPU UUID mapped to sole logical0, shar |
| 2026-09-21 08:13:05 | [other](20260921-081305_other.md) | How should the existing diagnostic collect physical GPU evid | Reuse bounded process and host validation; parse selected fu |
| 2026-09-21 09:12:38 | [other](20260921-091238_other.md) | How should the saved diagnostic verify child GPU identity?  | Use independently observed CUDA property UUID after trusted  |
| 2026-09-21 10:12:46 | [other](20260921-101246_other.md) | Which imports may precede logical CUDA identity validation?  | Use verified Torch only before logical identity; defer model |
| 2026-09-21 11:16:26 | [other](20260921-111626_other.md) | How should the pre-identity Torch dependency boundary execut | Use independent explicit dependency paths and hashes, a sing |
| 2026-09-21 12:12:44 | [other](20260921-121244_other.md) | How should the blocked pre-identity dependency verification  | Implement a single-use, hash-pinned handoff that verifies de |
| 2026-09-21 13:16:09 | [other](20260921-131609_other.md) | How should launcher bootstrap bytes and whole-child bounds b | Use a produced bundle with an independently pinned isolated  |
| 2026-09-21 14:14:48 | [other](20260921-141448_other.md) | Server-4 remains unavailable; what executable work advances  | Implement and test a synthetic production execution guard/dr |
| 2026-09-21 15:12:19 | [other](20260921-151219_other.md) | Server-4 remains unavailable; what executable work advances dependency provenance? | Add a strict static provenance-receipt validator for roots, bootstrap, packages, ELF declarations and cache candidates; assert no ABI or runtime proof. |
| 2026-09-21 17:48:16 | [other](20260921-174816_other.md) | Server-4 still refuses SSH; how can the next reachable obser | Implement a stdlib-only dependency observation collector tha |
| 2026-09-21 18:14:09 | [other](20260921-181409_other.md) | What executable validation can resolve the collector/validat | Add and run a POSIX-shaped end-to-end fixture that crosses c |
| 2026-09-21 19:15:26 | [other](20260921-191526_other.md) | How can the next server-4 collection run be materialized wit | Add a target-runtime seed materializer that derives environm |
| 2026-09-21 19:56:45 | [other](20260921-195645_other.md) | Which server allocation should the project use after the ser | Switch all NEW training and native diagnostics to server-6 G |
| 2026-09-21 21:27:33 | [route_change](20260921-212733_route_change.md) | Server-6 runtime is now observable; should the native diagno | Advance only the saved-only dependency and runtime diagnosti |
| 2026-09-21 21:39:59 | [route_change](20260921-213959_route_change.md) | Server-6 saved-only diagnostics advanced: are the three arti | Yes: the 3 artifact and 6 data hashes match exactly on serve |
| 2026-09-21 22:01:11 | [route_change](20260921-220111_route_change.md) | Champion instantiation and the backbone native forward/backw | Advance the runtime/resource chain only: constructor, assets |
| 2026-09-21 22:01:21 | [other](20260921-220121_other.md) | Pending candidates pinned pipeline/headless/.tick_context.js | Yes: purge the transient per-tick context snapshot from all  |
| 2026-09-22 02:25:46 | [route_change](20260922-022546_route_change.md) | Does the champion pass a full-model native backward through  | Advance the runtime gate: the production text-encoder, decod |
| 2026-09-22 03:24:24 | [route_change](20260922-032424_route_change.md) | Does the calibrated paired baseline/champion resource gate p | No: both exceed the hard absolute FLOPs limit. Keep resource |
| 2026-09-22 04:23:52 | [route_change](20260922-042352_route_change.md) | Does the corrected historical predict-mode resource gate pas | Yes. Resources are verified: baseline 9.700876364 G and cham |
| 2026-09-22 05:19:26 | [route_change](20260922-051927_route_change.md) | Do the eight due referent axes still require active event-mo | No. Close three axes, block four on server-6 native evidence |
| 2026-09-22 05:21:26 | [route_change](20260922-052126_route_change.md) | Does the due-axis resolution satisfy the closure blocker con | Yes. Four blocked axes now persist blocker, timezone-aware r |
| 2026-09-22 06:27:28 | [route_change](20260922-062729_route_change.md) | Why did closure postflight reject the prior event tick?  | Normalize referent-supervision-axis from open_no_candidate t |
| 2026-09-22 06:59:03 | [route_change](20260922-065903_route_change.md) | Can the four blocked due native diagnostics resume now that  | Keep all four candidates blocked; replace the stale host-unr |
| 2026-09-22 07:20:02 | [route_change](20260922-072002_route_change.md) | Can the frozen M95 capture routes advance without the exact  | Advance capture deployment only: deploy and verify the froze |
| 2026-09-22 08:12:57 | [route_change](20260922-081257_route_change.md) | Can the four blocked due native diagnostics resume at the 08 | Keep all four blocked, keep referent-supervision-axis in des |
| 2026-09-22 09:21:03 | [route_change](20260922-092104_route_change.md) | Can the four blocked native diagnostics resume at the 09:20  | Keep all four native capture routes blocked solely on exact  |
| 2026-09-22 09:35:30 | [route_change](20260922-093530_route_change.md) | Why were the four native capture routes blocked on an exact  | Locate and bind the byte-exact M95 payload at server-6:/data |
| 2026-09-22 09:50:04 | [route_change](20260922-095004_route_change.md) | Does the completed same-forward capture justify enqueueing a | Keep all four routes in diagnosis; do not enqueue or launch  |
| 2026-09-22 10:19:37 | [route_change](20260922-101937_route_change.md) | Does the paired M95 feature diagnosis justify queueing an id | Keep all four routes diagnosis-only; do not enqueue. Six of  |
| 2026-09-22 10:32:19 | [route_change](20260922-103219_route_change.md) | Does the latest M95 control justify a training design or req | Correct the unavailable any-seed fallback and supersede the  |
| 2026-09-22 10:55:14 | [route_change](20260922-105514_route_change.md) | Does native semantic recovery resolve the six M95 unresolved | Correct the six failures to same-class identity confusions;  |
| 2026-09-22 13:14:29 | [route_change](20260922-131430_route_change.md) | Does the larger M95 identity-control design pass pre-registr | Freeze a 256-expression, outcome-independent cohort with 128 |
| 2026-09-22 14:20:11 | [route_change](20260922-142011_route_change.md) | How should the five due identity-control candidates advance  | Deploy and validate the manifest-bound capture implementatio |
| 2026-09-22 16:14:31 | [route_change](20260922-161431_route_change.md) | How should the five due identity candidates advance while GP | Implement and deploy the missing CPU-only manifest identity  |
| 2026-09-22 17:17:08 | [route_change](20260922-171708_route_change.md) | Should the five identity candidates launch at the 17:15 retr | Keep all five candidates at implementation, launch nothing,  |
| 2026-09-22 18:13:57 | [route_change](20260922-181357_route_change.md) | Should the five identity candidates remain blocked or start  | Start the frozen native manifest capture as a detached diagn |
| 2026-09-22 20:33:10 | [route_change](20260922-203310_route_change.md) | Should the shared M95 identity validation continue through a | Record the shared validation as temporarily blocked at the t |
| 2026-09-22 20:33:31 | [route_change](20260922-203332_route_change.md) | Should the shared M95 identity validation continue through a | Record the shared validation as temporarily blocked at the t |
| 2026-09-22 22:39:23 | [route_change](20260922-223923_route_change.md) | Should the five identity candidates remain transport-blocked | Resume the existing server-6 validation stage without replac |
| 2026-09-23 00:18:44 | [route_change](20260923-001844_route_change.md) | What follows the completed frozen 256-row identity capture?  | Complete shared validation and return the five existing axes |
| 2026-09-23 03:22:33 | [route_change](20260923-032233_route_change.md) | What survives the completed failure and prototype audit?  | Keep the five existing axes in diagnosis and leave both trai |
| 2026-09-23 05:35:55 | [route_change](20260923-053555_route_change.md) | What remains after matched-support and supervision follow-up | Complete the registered-pair causality audit without claimin |
| 2026-09-23 08:11:58 | [route_change](20260923-081158_route_change.md) | How should recovered follow-up and label-direction evidence  | Complete the bounded referent-causality audit; retain four m |
| 2026-09-23 09:17:59 | [route_change](20260923-091759_route_change.md) | What follows from shared-disjoint-support feasibility and th | Complete joint support audit; retain unknown object8 class;  |
| 2026-09-23 10:15:23 | [route_change](20260923-101523_route_change.md) | How do exact-mask labels and shared-support stage transition | Complete the bounded modality diagnostic without admitting a |
| 2026-09-23 11:14:59 | [route_change](20260923-111459_route_change.md) | What explains saved exact-mask label discordance?  | Retain supervision/discrimination/identity as diagnosis; rej |
| 2026-09-23 12:12:12 | [route_change](20260923-121212_route_change.md) | Can saved geometry attribute six outside-seed positives?  | Exact nearest-GT replay is impossible from frozen capture: n |
| 2026-09-23 13:12:41 | [route_change](20260923-131241_route_change.md) | Does exact-mask label discordance imply indicator conflict?  | Keep three axes in diagnosis; binary-mask equivalence alone  |
| 2026-09-23 14:12:07 | [route_change](20260923-141207_route_change.md) | Does same physical seed identity explain exact-mask label di | Keep three axes in diagnosis; four matched classes have posi |
| 2026-09-23 15:18:33 | [route_change](20260923-151833_route_change.md) | Can captured hierarchy positions replay native nearest-GT as | No: hierarchy FPS coordinates are partitioner inputs, not bo |
| 2026-09-23 16:11:41 | [route_change](20260923-161141_route_change.md) | Can the frozen M95 capture attribute native positive labels  | No; require criterion-bound coordinates and per-GT matcher o |
| 2026-09-23 17:11:48 | [route_change](20260923-171148_route_change.md) | Is native matcher-cause attribution ready for the frozen M95 | Opt-in producer and CPU binding tests ready; defer native ca |
| 2026-09-23 18:10:59 | [route_change](20260923-181059_route_change.md) | Is the opt-in native matcher-cause capture correctly bound t | Corrected native argument ordering; defer the 256-row captur |
| 2026-09-23 19:13:57 | [route_change](20260923-191357_route_change.md) | Does same-physical-ID mask discordance establish representat | No; add source-bound opt-in query-state capture and predecla |
| 2026-09-23 20:25:44 | [route_change](20260923-202544_route_change.md) | Is the frozen same-ID discordance enough to admit identity s | No; require native source-bound query-state and matcher-caus |
| 2026-09-23 23:14:42 | [route_change](20260923-231442_route_change.md) | Does the fixed 256-row partition distinguish a new supervisi | No; retain three diagnosis IDs and empty queue pending nativ |
| 2026-09-24 00:15:32 | [route_change](20260924-001532_route_change.md) | Does source-bound matching explain six excluded acceptable-q | No: retain diagnosis; distinguish target-seed availability f |
| 2026-09-24 01:12:12 | [route_change](20260924-011212_route_change.md) | Does the exclusion partition now establish native matcher ca | No; keep three stable IDs at diagnosis and queue empty; nati |
| 2026-09-24 02:11:24 | [route_change](20260924-021124_route_change.md) | Does a native positive-set edit isolate referent supervision | No; require component-isolated and coupled controls on match |
| 2026-09-24 03:10:39 | [route_change](20260924-031039_route_change.md) | Can matched positive-set controls assume GT mask bindings ar | No; audit repeated-GT mask indexing on native capture before |
| 2026-09-24 14:21:20 | [route_change](20260924-142120_route_change.md) | How to repair closure hash drift without falsifying historic | Archive superseded source/test hashes with explicit not-curr |
| 2026-09-24 15:11:39 | [route_change](20260924-151140_route_change.md) | Can collision and GT-mask misbinding be attributed separatel | Keep the three diagnosis IDs; add partitioned overlap counts |
| 2026-09-24 16:11:32 | [route_change](20260924-161132_route_change.md) | Can the frozen 256-row native cause audit accept a capture f | Require the exact producer SHA256 in the all-row checker; re |
| 2026-09-24 17:13:02 | [route_change](20260924-171302_route_change.md) | Can the all-row native matcher audit trust a valid but subst | Require each captured target object ID to match the hash-fro |
| 2026-09-24 17:17:25 | [route_change](20260924-171725_route_change.md) | Does the exclusion checker accept the actual preregistered m | Correct the capture-header guard to the preregistered manife |
| 2026-09-24 18:11:02 | [route_change](20260924-181102_route_change.md) | Which source-bound control separates GT-mask binding from na | Keep three due IDs blocked and queue empty; predefine mask-o |
| 2026-09-24 19:10:18 | [route_change](20260924-191018_route_change.md) | Can same-forward mask component controls be prepared while G | Keep the three due IDs blocked and queue empty; add an offli |
| 2026-09-24 20:09:31 | [route_change](20260924-200931_route_change.md) | Can the score-head component be isolated while GPU7 remains  | Keep three due IDs blocked and queue empty; extend frozen sa |
| 2026-09-24 21:13:03 | [route_change](20260924-211303_route_change.md) | Can the native indicator-loss component be isolated from mas | Keep the three due IDs blocked and queue empty; extend the f |
| 2026-09-24 21:17:36 | [route_change](20260924-211736_route_change.md) | Can closure pass while two terminal diagnostics still use th | Map referent-causality-audit and modality-identity-preservat |
| 2026-09-24 22:13:36 | [route_change](20260924-221336_route_change.md) | Can the native capture advance the repeated-GT component dia | Add a fail-closed four-arm CPU replay: original, mask-only,  |
| 2026-09-24 23:19:53 | [route_change](20260924-231953_route_change.md) | Does the complete 256-row M95 control identify an admissible | Keep the queue empty and do not admit a variant. Persist the |
| 2026-09-25 00:00:58 | [route_change](20260925-000058_route_change.md) | Can the manifest-only 256-row replay serve as an exact compa | Reject the subset replay as an exact comparator. Keep the ex |
| 2026-09-25 01:09:55 | [route_change](20260925-010955_route_change.md) | The exact capture is still running; should the pipeline deri | Hold all three due IDs at validation. Verify the exact-captu |
| 2026-09-25 01:17:25 | [route_change](20260925-011725_route_change.md) | The exact full-scan capture is still running; what executabl | Add and verify a fail-closed postprocess runner that validat |
| 2026-09-25 01:50:18 | [route_change](20260925-015018_route_change.md) | Can frozen instance representations distinguish target from  | Keep all three due candidates at validation and reject repre |
| 2026-09-25 02:00:00 | [route_change](20260925-020000_route_change.md) | Does the frozen identity-vs-score advantage survive exclusio | Correct the prior identity interpretation: the self-support- |
| 2026-09-25 02:26:29 | [route_change](20260925-022629_route_change.md) | Did the query-support-excluded identity advantage survive co | Supersede the 20260925-0200 null result: use all 1833 common |
| 2026-09-25 03:12:14 | [route_change](20260925-031214_route_change.md) | Does the final-stage support-excluded identity advantage per | Record aggregate stratum stability but not uniform generaliz |
| 2026-09-25 03:38:17 | [route_change](20260925-033817_route_change.md) | Does the corrected expression-level identity advantage survi | Keep all three due IDs at validation. The 1833-pair common s |
| 2026-09-25 03:41:33 | [route_change](20260925-034133_route_change.md) | Does the identity-score advantage survive clustering by targ | Keep all three due IDs at validation. The registered 1833-pa |
| 2026-09-25 03:52:59 | [route_change](20260925-035259_route_change.md) | Does the identity-score disagreement select higher-IoU queri | Keep all three due IDs at validation. On 389 non-tied score- |
| 2026-09-25 04:05:36 | [route_change](20260925-040536_route_change.md) | Does support-excluded identity margin preserve its pair-leve | Keep the due candidates at validation, reject identity-margi |
| 2026-09-25 05:10:05 | [route_change](20260925-051005_route_change.md) | Exact match-cause capture is still running at 3917/4663; sho | Hold all three due candidates at validation and keep both de |
| 2026-09-25 05:18:33 | [route_change](20260925-051833_route_change.md) | Does the identity-score pair advantage come from target attr | Reject peer-rejection and standalone identity-margin routes. |
| 2026-09-25 05:29:52 | [route_change](20260925-052952_route_change.md) | Does the target-positive selection advantage survive cardina | Keep referent-supervision-axis in validation and record targ |
| 2026-09-25 05:40:32 | [route_change](20260925-054032_route_change.md) | Can the exact native capture answer which target-positive ca | Stage a fail-closed CPU analyzer for 256-expression nearest- |
| 2026-09-25 07:15:05 | [route_change](20260925-071505_route_change.md) | Can referent-specific positive-set binding or its mask-co-su | Close referent-supervision-axis. Reject the co-support-posit |
| 2026-09-25 07:31:42 | [route_change](20260925-073142_route_change.md) | Does native-negative query intrusion define an independent M | Reject it as a renamed referent classification/ranking route |
| 2026-09-25 07:39:20 | [route_change](20260925-073920_route_change.md) | Does query-seed/mask binding define an independent M95 mecha | Reject seed-mask binding consistency before design; admit no |
| 2026-09-25 08:25:10 | [route_change](20260925-082510_route_change.md) | Are low-IoU M95 selections caused by a high-score wrong-inst | Reject duplicate-mask dominance as a new route. Admit no can |
| 2026-09-25 10:17:16 | [route_change](20260925-101716_route_change.md) | Does the failed M95 exact-capture gate reveal a new admissio | No admission or launch; keep server-6 GPU7 queue slots empty |
| 2026-09-25 10:32:11 | [route_change](20260925-103211_route_change.md) | Does the M95 capture drift support an admitted independent m | No. Preserve strict failure, leave both slots empty; native  |
| 2026-09-25 11:18:49 | [route_change](20260925-111849_route_change.md) | Does M95 row174 partition drift justify a model admission or | No admission or queue change; retain strict failure and resu |
| 2026-09-25 12:12:20 | [route_change](20260925-121220_route_change.md) | Does M95 hierarchy geometry drift resolve native reproducibi | No admission or queue change; retain strict 28/65 failure an |
| 2026-09-25 13:11:23 | [route_change](20260925-131123_route_change.md) | Can M95 partition boundary be resolved and admitted this tic | No native repeat or admission; preserve strict 28/65 failure |
| 2026-09-25 14:20:29 | [route_change](20260925-142029_route_change.md) | Can the M95 partition boundary be admitted after this retry? | No native repeat or admission; retain strict 28/65 failure a |
| 2026-09-25 15:14:09 | [route_change](20260925-151409_route_change.md) | Does frozen M95 drift localize to the changed assignment?  | No: drift extends outside the affected old/new clusters; nat |
| 2026-09-25 16:21:24 | [route_change](20260925-162124_route_change.md) | Can the M95 boundary audit proceed with GPU7 at 0% but 19991 | Keep two slots empty; isolate changed-producer trace, preser |
| 2026-09-25 17:49:13 | [route_change](20260925-174913_route_change.md) | Does the completed M95 subset boundary trace admit a model o | Keep both slots empty; retain m95-repro-drift-boundary as bl |
| 2026-09-25 18:12:24 | [route_change](20260925-181224_route_change.md) | Does the matched M95 subset divergence justify model admissi | Keep two slots empty; retain provenance diagnosis blocked un |
| 2026-09-25 19:13:44 | [route_change](20260925-191344_route_change.md) | Does matched subset FPS divergence justify model admission o | Keep both slots empty; preserve blocked M95 provenance diagn |
| 2026-09-25 20:13:02 | [route_change](20260925-201302_route_change.md) | Does matching pre-forward fingerprints identify entry FPS RN | Keep both slots empty and stable M95 provenance diagnosis bl |
| 2026-09-25 21:47:49 | [route_change](20260925-214749_route_change.md) | Do matched M95 native inputs prove FPS randomness or strict  | Keep both model slots empty; continue exact-contract full TR |
| 2026-09-26 03:36:44 | [route_change](20260926-033644_route_change.md) | Does the fixed ila operator establish the M95 layer5 cause o | Keep two server-6 GPU7 model slots empty; retain m95-repro-d |
| 2026-09-26 03:51:13 | [route_change](20260926-035113_route_change.md) | Can M95 trained layer5 replay proceed, and does observed sco | Keep both server-6 GPU7 model slots empty; block m95-repro-d |
| 2026-09-26 05:05:39 | [route_change](20260926-050539_route_change.md) | Does trained fixed-item M95 drift originate at cluster-token | Exact M95 checkpoint recovered; fixed-item cluster-bank CPU  |
| 2026-09-26 07:03:47 | [route_change](20260926-070347_route_change.md) | Frozen M95 target binding passed; can the matched cluster-ba | Keep both queue slots empty. Persist exact binding and start |
| 2026-09-26 08:25:11 | [route_change](20260926-082511_route_change.md) | Do exact frozen two-scene cluster-scatter controls repair th | Keep both slots empty; exact item binding passed, but matche |
| 2026-09-26 09:04:24 | [route_change](20260926-090424_route_change.md) | Does bound row83 superpoint-reduction variability justify a  | Keep both server-6 GPU7 slots empty; resume hash-bound origi |
| 2026-09-26 10:22:07 | [route_change](20260926-102207_route_change.md) | Does recovered original-order row83 trace pass mechanism adm | No admission: keep server-6 GPU7 slots empty; original-order |
| 2026-09-26 10:31:54 | [route_change](20260926-103154_route_change.md) | Does one matched row174 warm-up reproduce row83 sparse-bound | No: cold and primed row83 are byte-identical at sparse input |
| 2026-09-26 12:27:24 | [route_change](20260926-122724_route_change.md) | Can the step3137 same-process row83 diagnostic or another me | No admission or launch; stop only our interrupted probe, pre |
| 2026-09-26 13:16:21 | [route_change](20260926-131621_route_change.md) | Can interrupted step3000/600 M95 first-stage traces resume e | No: retain m95-repro-drift-boundary as externally blocked; d |
| 2026-09-26 14:43:49 | [route_change](20260926-144349_route_change.md) | GPU7 is idle; can the exact M95 row83 first-stage comparison | Launch hash-bound guarded full-order diagnostic on server-6  |
| 2026-09-26 15:24:56 | [route_change](20260926-152456_route_change.md) | Does the completed step3137 same-process row83 replay or two | No admission or queue launch. Archive exact replay; close ex |
| 2026-09-26 15:32:37 | [route_change](20260926-153237_route_change.md) | Does the same-support FN/FP partition of 16 limited M95 case | No. Keep 0/2 training admissions; preserve the closed two-ma |
| 2026-09-26 15:56:52 | [route_change](20260926-155652_route_change.md) | Does the preregistered selected-mask centroid-graph boundary | Reject this target-blind centroid-graph boundary/component r |
| 2026-09-26 16:35:59 | [route_change](20260926-163559_route_change.md) | Does explicit contact language identify target-specific phys | Reject strict named-anchor/contact-distance realization unde |
| 2026-09-26 16:44:04 | [route_change](20260926-164404_route_change.md) | Do explicit color words or target-blind RGB dispersion expla | Reject m95-explicit-color-scene-contrast and m95-visible-chr |
| 2026-09-26 16:48:09 | [route_change](20260926-164809_route_change.md) | Does explicit comparative size language support an independe | Reject m95-explicit-size-comparison on frozen TRAIN cohort;  |
| 2026-09-26 16:50:47 | [route_change](20260926-165047_route_change.md) | Does explicit exclusion language identify a recurring M95 fa | Reject m95-explicit-exclusion-binding; no model, receipt or  |
| 2026-09-26 16:52:14 | [route_change](20260926-165214_route_change.md) | Does explicit material language identify an independent targ | Reject m95-explicit-material-evidence on its preregistered d |
| 2026-09-26 16:57:31 | [route_change](20260926-165731_route_change.md) | Does explicit between-language furnish two grounded anchors  | Reject m95-explicit-two-anchor-order strict realization; do  |
| 2026-09-26 17:05:54 | [route_change](20260926-170554_route_change.md) | Does the 9-row ambiguous ordinal signal pass native target-o | Keep m95-explicit-ordinal-count at diagnosis, not admitted;  |
| 2026-09-26 17:18:47 | [route_change](20260926-171847_route_change.md) | Does frozen native ordinal ordering on M95 indices 7,10,44 y | Reject m95-explicit-ordinal-count strict three-row realizati |
| 2026-09-26 17:19:48 | [route_change](20260926-171948_route_change.md) | Does frozen selected-mask feature-edge contrast in 16 mask-l | Reject m95-feature-boundary-contrast-screen; do not train or |
| 2026-09-26 17:35:51 | [route_change](20260926-173551_route_change.md) | Does original superpoint partition irreducibly cap the 16 fr | Extend rejected cluster-instance-purity with point-level ora |
| 2026-09-26 17:43:04 | [route_change](20260926-174304_route_change.md) | Does explicit object-part language reveal an independent M95 | Reject m95-explicit-part-evidence lexical realization; no pa |
| 2026-09-26 18:00:59 | [route_change](20260926-180059_route_change.md) | Does explicit orientation language supply a target-bound geo | Reject m95-explicit-orientation-geometry lexical realization |
| 2026-09-26 19:01:00 | [route_change](20260926-190100_route_change.md) | Do frozen scene-region words identify an M95 failure mechani | Reject m95-explicit-scene-region-evidence lexical realizatio |
| 2026-09-26 19:01:46 | [route_change](20260926-190147_route_change.md) | Do frozen explicit object-state words indicate M95 failures? | Reject m95-explicit-object-state lexical realization; no mod |
| 2026-09-26 19:01:56 | [route_change](20260926-190156_route_change.md) | Can explicit repeated-object group wording justify a new mec | Keep stable ID m95-explicit-group-topology at diagnosis, not |
| 2026-09-26 19:53:49 | [route_change](20260926-195349_route_change.md) | Does m95-explicit-group-topology pass target-blind local-gro | Retain stable ID at diagnosis; no receipt, sync, queue or tr |
| 2026-09-26 20:45:29 | [route_change](20260926-204529_route_change.md) | Does m95-explicit-group-topology native predicted-mask local | Reject this stable ID realization; no receipt, sync, queue o |
| 2026-09-26 20:49:29 | [route_change](20260926-204930_route_change.md) | Does cross-scale L1/L2 redundancy distinguish M95 failures a | Reject m95-cross-scale-evidence-redundancy as an admission r |
| 2026-09-26 21:00:07 | [route_change](20260926-210007_route_change.md) | Does explicit-other reference-role ownership merit a native  | Retain stable ID m95-reference-role-ownership at diagnosis;  |
| 2026-09-26 21:17:41 | [route_change](20260926-211741_route_change.md) | Does exact explicit-other role marker intervention pass nati | Reject stable ID m95-reference-role-ownership as this realiz |
| 2026-09-26 21:30:41 | [route_change](20260926-213041_route_change.md) | Does explicit target-bound shape language identify an indepe | Reject stable ID m95-explicit-shape-evidence at diagnosis; n |
| 2026-09-26 21:33:50 | [route_change](20260926-213350_route_change.md) | Can explicit texture or pattern words explain a distinct M95 | Reject stable ID m95-explicit-texture-pattern-evidence at di |
| 2026-09-26 21:59:13 | [route_change](20260926-215913_route_change.md) | Does native TRAIN token-span reachability explain M95 failur | Reject m95-token-span-integrity realization; do not build a  |
| 2026-09-26 22:02:33 | [route_change](20260926-220234_route_change.md) | Does target-rooted two-hop relation composition reveal an in | Reject m95-relation-composition-depth realization; do not cr |
| 2026-09-26 22:33:50 | [route_change](20260926-223350_route_change.md) | Does parsed target lemma disagree with annotated target cate | Reject m95-target-label-alignment as a mechanism diagnosis.  |
| 2026-09-26 22:33:59 | [route_change](20260926-223359_route_change.md) | Did graph utterance lose task-bearing source words in frozen | Reject m95-utterance-provenance realization; no text repair  |
| 2026-09-26 22:34:08 | [route_change](20260926-223408_route_change.md) | Do identical same-scene TRAIN descriptions assigned to disti | Reject m95-description-label-collision realization; do not l |
| 2026-09-26 22:36:20 | [route_change](20260926-223620_route_change.md) | Is parsed target lemma absent from its own native graph targ | Reject m95-target-span-lemma-contract realization; no span/l |
| 2026-09-26 22:43:35 | [route_change](20260926-224335_route_change.md) | Does exact class-word context support expose a distinct M95  | Reject m95-sample-context-support realization; no lexical co |
| 2026-09-26 22:50:25 | [route_change](20260926-225025_route_change.md) | Do same-instance TRAIN expressions assign contradictory obje | Reject m95-object-category-conflict realization; no category |
| 2026-09-26 22:52:20 | [route_change](20260926-225220_route_change.md) | Do native target-positive and other-object-negative token ma | Reject m95-cross-role-token-overlap realization; no cross-ro |
| 2026-09-26 23:39:54 | [route_change](20260926-233955_route_change.md) | Does frozen physical target semantic class contradict exact  | Reject m95-physical-target-semantic-conflict; no class-label |
| 2026-09-26 23:40:05 | [route_change](20260926-234005_route_change.md) | Does native repeated-GT mask indexing affect the frozen M95  | Reject m95-multigt-mask-index as this cohort mechanism; no b |
| 2026-09-26 23:51:41 | [route_change](20260926-235141_route_change.md) | Does physical non-target class-context support survive nativ | Keep m95-sample-context-support at diagnosis; execute exact  |
| 2026-09-27 00:41:06 | [route_change](20260927-004106_route_change.md) | Does post-overwrite native seed context support justify a ne | Keep m95-sample-context-support in diagnosis; no admission o |
| 2026-09-27 01:26:03 | [route_change](20260927-012603_route_change.md) | Does exact-input seed context exposure permit an instance-ma | Keep m95-sample-context-support at diagnosis; same-instance  |
| 2026-09-27 01:34:43 | [route_change](20260927-013443_route_change.md) | Does cross-expression same-instance seed-label contrast clea | No; 180 mixed-role instances provide diagnostic support, but |
| 2026-09-27 01:51:38 | [route_change](20260927-015138_route_change.md) | Does physical-instance noisy-OR bag supervision with target  | Reject that bag formulation under the stable candidate ID; r |
| 2026-09-27 02:11:49 | [route_change](20260927-021149_route_change.md) | Does the frozen M95 seed-in-mask diagnostic use the correct  | Correct the read-only diagnostic mapping; invalidate old 1/4 |
| 2026-09-27 02:22:11 | [route_change](20260927-022211_route_change.md) | Does corrected selected-query seed-in-mask containment disti | No. Keep sample-context-support in diagnosis; do not admit a |
| 2026-09-27 02:32:22 | [route_change](20260927-023222_route_change.md) | Does corrected native query-seed mapping reverse the old see | Supersede the old 354/32768 and 1/49 containment diagnosis w |
| 2026-09-27 03:01:50 | [next_batch](20260927-030150_next_batch.md) | Does same-scene target-to-context role transition justify an | No admission yet. Keep m95-sample-context-support in diagnos |
| 2026-09-27 03:21:43 | [route_change](20260927-032143_route_change.md) | Do same-physical-position native gradients support target-co | Reject role-gradient conflict realization under m95-sample-c |
| 2026-09-27 03:40:00 | [next_batch](20260927-034000_next_batch.md) | After preregistered role-conflict reversal and scalar/Jacobi | No. Keep m95-sample-context-support in diagnosis; next test  |
| 2026-09-27 03:47:09 | [route_change](20260927-034709_route_change.md) | Do the scalar-unexplained target-zero vector conflicts expos | No. Keep the residual as localized diagnosis under m95-sampl |
| 2026-09-27 03:51:47 | [route_change](20260927-035147_route_change.md) | Are suppressive native focal gradients on physical target se | No. Do not turn the current focal-label sign or target-seed  |
| 2026-09-27 04:21:59 | [route_change](20260927-042159_route_change.md) | 目标物理超点归一化的原生 focal 梯度质量是� | 否；关闭 m95-sample-context-support 的目标监督质� |
| 2026-09-27 04:43:06 | [route_change](20260927-044306_route_change.md) | 同一目标 seed 的正反 focal 得分导数是否在失� | 否；按 m95-sample-context-support 稳定 ID 关闭该得� |
| 2026-09-27 05:15:37 | [route_change](20260927-051537_route_change.md) | 小物体的物理目标归一化 focal 梯度不足是否� | 否；保留 m95-sample-context-support 的质量不足解� |
| 2026-09-27 05:59:50 | [route_change](20260927-055950_route_change.md) | Does frozen target/zero physical gradient conflict distingui | No admission; paired scene direction mixed and cohort sparse |
| 2026-09-27 06:31:38 | [route_change](20260927-063138_route_change.md) | Can the target/zero conflict screen generalize from its sele | No; keep m95-sample-context-support at diagnosis and do not  |
| 2026-09-27 07:18:32 | [route_change](20260927-071833_route_change.md) | Can existing exact-capture cause partition be joined to nati | No; fail closed and do not infer selection-recoverability fr |
| 2026-09-27 08:28:20 | [route_change](20260927-082820_route_change.md) | Do same-population native target/context gradients specifica | No; reject this conflict realization under m95-sample-contex |
| 2026-09-27 08:36:42 | [route_change](20260927-083642_route_change.md) | Is the M95 selected wrong-context phenotype reproducible acr | Keep it as a reproducible observational error phenotype, not |
| 2026-09-27 08:40:09 | [route_change](20260927-084009_route_change.md) | Does persistent wrong-context error uniquely preserve a part | No context-specific identity signature; retain observational |
| 2026-09-27 08:50:43 | [route_change](20260927-085043_route_change.md) | Does same-capture selected context seed-to-mask physical ove | No admission; retain the observed seed/mask association but  |
| 2026-09-27 09:21:17 | [route_change](20260927-092117_route_change.md) | Do persistent target-seeded mask failures imply a distinct a | No admission; preserve target-seed error stratum as diagnosi |
| 2026-09-27 09:30:00 | [route_change](20260927-093000_route_change.md) | Do same-scene target-seed success controls isolate mask fail | No; keep target-seed branch diagnostic-only. Four of five/fo |
| 2026-09-27 09:35:34 | [route_change](20260927-093534_route_change.md) | Does the independent 256-expression full native capture supp | No; retain diagnosis only, no same-target matched causal con |
| 2026-09-27 09:41:11 | [route_change](20260927-094112_route_change.md) | Are full-population target-seeded mask failures a uniform mi | No; retain error partition only, without extending PIRS or m |
| 2026-09-27 09:50:12 | [route_change](20260927-095012_route_change.md) | Can target-seeded mask failures be attributed uniformly to a | No. Four of eight have adequate same-target-seeded alternati |
| 2026-09-27 09:55:00 | [route_change](20260927-095500_route_change.md) | Are the four target-seeded mask-limited rows actually limite | No; none of the four has an adequate non-target-seeded alter |
| 2026-09-27 10:06:29 | [route_change](20260927-100629_route_change.md) | Do the four mask-limited target-seed rows lack native matche | No; all four selected queries are native positive and neares |
| 2026-09-27 11:06:46 | [route_change](20260927-110647_route_change.md) | Four mask-limited target-seeded M95 failures: is native targ | Reject those narrow explanations; continue stable diagnosis  |
| 2026-09-27 12:11:51 | [route_change](20260927-121151_route_change.md) | Can M95 frozen target-feature oracle gains justify a predict | No admission: deployed-mask and all-query-union supports fai |
| 2026-09-27 12:57:47 | [route_change](20260927-125747_route_change.md) | Do frozen M95 query-union reachability and support frequency | No admission: union overlaps all 16 limited targets but fixe |
| 2026-09-27 13:01:38 | [route_change](20260927-130138_route_change.md) | Does the frozen 256-expression M95 capture support same-targ | Reject this capture-specific same-target route for admission |
| 2026-09-27 13:15:12 | [route_change](20260927-131512_route_change.md) | Does additional target recall from other M95 queries show mi | No. All four have native matched-positive queries with corre |
| 2026-09-27 13:48:48 | [route_change](20260927-134848_route_change.md) | Does fragmented target recall reflect only positive-count no | No count-only claim: at matched count=2, fragmented query-gr |
| 2026-09-27 14:10:19 | [route_change](20260927-141019_route_change.md) | Do fragmented M95 query masks reveal a native cross-positive | No admission. Corrected native per-positive target-feature c |
| 2026-09-27 14:15:49 | [route_change](20260927-141549_route_change.md) | Is fragmentation caused by conflicting native positive-query | Not supported as an independent supervision mechanism. Misse |
| 2026-09-27 15:01:47 | [route_change](20260927-150147_route_change.md) | Does native-positive query union reveal a distinct target-su | No new candidate admission. Positive union adds target recal |
| 2026-09-27 15:04:16 | [route_change](20260927-150416_route_change.md) | Do matcher-negative masks covering the four fragmented targe | No general same-class relation-binding route: only 1 of 5 re |
| 2026-09-27 15:09:48 | [route_change](20260927-150948_route_change.md) | Does native-positive mask union improve M95 mask-limited spe | No deployable union. Of four fragmented rows one retrospecti |
| 2026-09-27 15:17:04 | [route_change](20260927-151704_route_change.md) | Is M95 unseen target support in the fragmented cohort primar | No. All four fragmented expressions have target-seeded queri |
| 2026-09-27 16:13:58 | [route_change](20260927-161358_route_change.md) | Do uncovered M95 target superpoints expose an independent pr | Five frozen TRAIN controls: deep-negative logits and fused-f |
| 2026-09-27 16:36:25 | [route_change](20260927-163625_route_change.md) | Does valid same-category support isolate M95 fragmented unde | No: -100 invalidates 7/8 earlier other-limited pairs; 0/2 fr |
| 2026-09-27 17:18:55 | [route_change](20260927-171855_route_change.md) | Do same-class annotated peers explain M95 fragmented missed  | Correct the absent-peer interpretation: both fragmented miss |
| 2026-09-27 17:26:28 | [route_change](20260927-172628_route_change.md) | Is same-class peer leakage a failure-specific positive-mask  | No admission: among 26 valid-class, missed-target, annotated |
| 2026-09-27 17:37:17 | [route_change](20260927-173717_route_change.md) | 同类 peer 与漏检目标的 final-layer BCE 梯度冲突� | 保持诊断、不准入；26/26 均为负余弦且不同类 |
| 2026-09-27 17:43:27 | [route_change](20260927-174327_route_change.md) | LayerNorm 反传后是否出现碎片漏检特异梯度冲� | 不准入；同类 peer 梯度与目标冲突在 26/26，异 |
| 2026-09-27 17:46:31 | [route_change](20260927-174631_route_change.md) | 原生 BCE+Dice 是否在碎片漏检中反向抑制 target� | 不支持该缺陷；两例碎片组完整 mask-loss query � |
| 2026-09-27 18:20:17 | [route_change](20260927-182017_route_change.md) | 独立的 2D/3D 特征分歧是否揭示碎片漏检的预� | 暂不准入；碎片 2/2 满足预注册正向，但覆盖� |
| 2026-09-27 18:29:54 | [route_change](20260927-182954_route_change.md) | 2D/3D 同位置对齐分歧是否在碎片样本相对 hard- | 两例碎片样本正向（hard-peer 均值 +0.0368、原始 |
| 2026-09-27 18:35:42 | [route_change](20260927-183542_route_change.md) | 模态分歧是否在同一目标的漏检片段相对覆盖 | 未通过预注册局部性判据：碎片 1/2 正向，覆� |
| 2026-09-27 19:00:59 | [route_change](20260927-190059_route_change.md) | 原生训练的CLIP超点索引在采样后是否错位？  | 四种源路径约束下的合成索引对照均保持原物 |
| 2026-09-27 19:04:23 | [route_change](20260927-190423_route_change.md) | 本轮CLIP超点索引四例是否是独立新证据？  | 否。复核发现2026-09-16既有modality_index_contract已 |
| 2026-09-27 21:54:54 | [route_change](20260927-215454_route_change.md) | 原生CLIP零特征及实例首点语义是否形成可准� | 否；64场景首点语义差异0/1981；CLIP零行虽存在 |
| 2026-09-27 22:31:30 | [route_change](20260927-223130_route_change.md) | 零特征几何与首点训练顺序是否提供可准入诊 | 不准入；保留稳定候选diagnosis。64场景893个零C |
| 2026-09-27 23:23:12 | [route_change](20260927-232312_route_change.md) | 原生superpoint软上下文支持是否构成新的可准� | 尚不能。64个TRAIN场景4087标注中0个二值目标超 |
| 2026-09-27 23:31:48 | [route_change](20260927-233148_route_change.md) | 同一物理实例跨表达上下文开关是否支持新的 | 保留m95-sample-context-support为diagnosis，不准入。6 |
| 2026-09-27 23:49:47 | [route_change](20260927-234947_route_change.md) | 严格类词最小对是否真的改变原生上下文支持 | 纠正误报，候选保留诊断，未准入。唯一严格 |
| 2026-09-28 00:23:17 | [route_change](20260928-002317_route_change.md) | 物理目标少数超点造成的原生GT遗漏是否与M95� | 64场景输入诊断显示少数超点存在，但固定M95  |
| 2026-09-28 00:26:13 | [route_change](20260928-002613_route_change.md) | 目标少数超点GT遗漏是否连接到部署所选失败� | 仅3条暴露失败/2个物理目标；其中只有1条所� |
| 2026-09-28 00:45:08 | [route_change](20260928-004508_route_change.md) | shower curtain多词类键在原生物理上下文标签中� | 源级错误真实但不准入。64场景4087表达中28含� |
| 2026-09-28 00:51:22 | [route_change](20260928-005122_route_change.md) | 同目标短语缺席描述能否作为shower curtain上下� | 仅冻结诊断清单，不准入。11个暴露表达对应2 |
| 2026-09-28 00:53:45 | [route_change](20260928-005346_route_change.md) | 多词类键漏标是否与显式参照物提及吻合？  | 图谱角色审查显示11暴露表达中10条的每个showe |
| 2026-09-28 00:58:36 | [route_change](20260928-005836_route_change.md) | shower curtain多词类键遗漏在完整TRAIN源中的物� | 全562场景36665表达中短语281条/46场景；102条/28� |
| 2026-09-28 01:01:29 | [route_change](20260928-010129_route_change.md) | 完整TRAIN多词类键物理遗漏是否都属于他物参� | 否，102条物理非目标curtain暴露中仅65条表达的 |
| 2026-09-28 01:15:57 | [route_change](20260928-011557_route_change.md) | Graph target-node phrase span 能否绑定物理 curtain 参 | 不能：102 条物理非目标 curtain 表达中，36 条� |
| 2026-09-28 02:13:29 | [route_change](20260928-021329_route_change.md) | 冻结31表达原生诊断能否直接复用256表达M95 pro | 不能直接复用：旧 producer 锁定 256 条、m95_prere |
| 2026-09-28 02:20:43 | [route_change](20260928-022043_route_change.md) | 31表达原生M95诊断适配器能否在不改旧256生产� | 已独立实现受哈希绑定的两场景31表达只读捕� |
| 2026-09-28 03:14:01 | [route_change](20260928-031401_route_change.md) | 31表达原生捕获在训练loader随机及drop_last契约� | 改为单场景有序不丢尾批的原生collate适配器� |
| 2026-09-28 04:14:32 | [route_change](20260928-041432_route_change.md) | 冻结31表达是否对应31个原生TRAIN loader单位？  | 核实其散布于21个四表达原生组；保留全部原� |
| 2026-09-28 05:14:08 | [route_change](20260928-051408_route_change.md) | 冻结31表达原生捕获后如何防止复用对照与两� | 预注册按同一物理目标的全部对照计算暴露差 |
| 2026-09-28 06:10:58 | [route_change](20260928-061058_route_change.md) | 冻结31表达的同物理目标对照是否共享原生TRAI | 按原生lang_num_max=4映射发现30/30对照边均跨loade |
| 2026-09-28 07:16:27 | [route_change](20260928-071627_route_change.md) | 冻结31表达的同物理目标对照是否隔离词法cont | 结果盲30边仅2边有相同完整类词集合，且共属 |
| 2026-09-28 07:21:05 | [route_change](20260928-072105_route_change.md) | 词法同目标描述对照失配后，下一步如何在固 | 预注册同一原生前向的支持干预及同量安慰剂 |
| 2026-09-28 08:18:31 | [route_change](20260928-081831_route_change.md) | 同前向支持/安慰剂如何避免原生匹配覆盖造� | 冻结最终FPS focal目标的严格等量准入检查：处 |
| 2026-09-28 09:16:27 | [route_change](20260928-091627_route_change.md) | 冻结31表达物理支持能否在原生生产边界重建� | 加入原生sp_ref_mask重建与物理实例一致性失败� |
| 2026-09-28 10:59:33 | [route_change](20260928-105933_route_change.md) | 原生31表达与同次前向支持干预是否足以准入� | 保留m95-sample-context-support为diagnosis；原生支持/ |
| 2026-09-28 12:07:08 | [route_change](20260928-120708_route_change.md) | 全TRAIN物理支持与分数匹配安慰剂是否足以准� | 保持m95-sample-context-support为diagnosis，不准入、� |
| 2026-09-28 12:10:43 | [route_change](20260928-121043_route_change.md) | 分数匹配支持干预是否对原生定位失败具有特 | 否：保留稳定ID为diagnosis，不将旧M95弱监督支� |
| 2026-10-02 15:23:03 | [route_change](20261002-152303_route_change.md) | 原生多任务冲突能否支持新的结构机制？  | 关闭本轮普遍原生梯度冲突实现；不准入PCGrad |
| 2026-10-02 15:23:03 | [other](20261002-152303_other.md) | 不同目标联合占用是否产生独立BCE没有的纠正 | 否决本次普通categorical ownership实现；不入队不 |
| 2026-10-09 08:52:41 | [route_change](20261009-085241_route_change.md) | 质量监督遗漏与层间重匹配是否提供独立结构 | 关闭受测缺信息/阈值补丁与层间重匹配实现� |
| 2026-10-09 08:52:41 | [other](20261009-085241_other.md) | 如何恢复旧宿主退出后遗留的研究租约？  | 按原token正式abort保存INCOMPLETE收据并核验释放� |
| 2026-10-09 09:54:42 | [next_batch](20261009-095443_next_batch.md) | 是否准入均值守恒原生点级掩码新实验  | 准入M198-PDC，仅server6 GPU7，seed1999及既有schedule |
| 2026-10-09 09:56:06 | [queue_push](20261009-095606_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M198 Mean-constrained native point detail field; seed199 |
| 2026-10-09 10:44:18 | [next_batch](20261009-104418_next_batch.md) | 是否准入定向原生边界事件 M199-BEI  | 按六项真实准入证据仅准入一个 M199-BEI；保持 |
| 2026-10-09 10:46:30 | [queue_push](20261009-104630_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M199 Directed native boundary incidence; seed1999; froze |
| 2026-10-11 23:45:02 | [route_change](20261011-234502_route_change.md) | PDC and BEI ended; two fresh core candidates tested.  | Archive native early stops; reject duplicate cores; no launc |
| 2026-10-12 01:33:31 | [route_change](20261012-013331_route_change.md) | Can the vertical witness sign or exact-caption allowed-set N | Reject these two tested realizations only; retain relational |
| 2026-10-12 03:25:13 | [route_change](20261012-032513_route_change.md) | Does missing physical anchoring or observed FPS drift explai | Reject the two tested concrete explanations only; preserve n |
| 2026-10-12 05:22:16 | [route_change](20261012-052216_route_change.md) | Do exact multiscale target-distractor aliases or a support-f | Reject only the exact-allscale-alias and bare-support-map re |
| 2026-10-12 08:58:04 | [route_change](20261012-085804_route_change.md) | 原生根节点将垃圾桶目标监督误绑到窗户，可 | 六项执行准入证据已审查；仅推进一个TMR首筛 |
| 2026-10-12 09:00:36 | [queue_push](20261012-090036_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M200-TMR target mention role supervision] configs/Quard/ |
| 2026-10-12 09:26:33 | [route_change](20261012-092633_route_change.md) | 单目标联合标签或多数票完全抹除是否支持新 | 两个独立原生前提均被反证；只对这两条路线 |
| 2026-10-12 11:22:36 | [route_change](20261012-112236_route_change.md) | Do native instance sentinel collision or normalized caption  | Reject the two tested prerequisites; scoped no_information_g |
| 2026-10-12 13:36:16 | [route_change](20261012-133616_route_change.md) | Can native directional transport or postfix token drift just | Preserve actual directional transport; reject only bare prio |
| 2026-10-12 17:13:39 | [route_change](20261012-171339_route_change.md) | Do native support expressibility or first-point semantic ord | Reject only the forced-support-failure and mixed-semantic-or |
| 2026-10-12 19:38:03 | [route_change](20261012-193803_route_change.md) | Do native graph keys or multiword context licensing justify  | Reject graph-key collision premise and bare literal matching |
| 2026-10-12 23:20:16 | [route_change](20261012-232016_route_change.md) | Do native target-name category conflicts or cropped empty su | Reject only comparable category conflict and sampled direct  |
| 2026-10-13 01:28:18 | [route_change](20261013-012818_route_change.md) | Do unresolved physical-class context coverage or short nativ | Reject only known-class exclusion in the unresolved subset a |
| 2026-10-13 03:18:40 | [route_change](20261013-031840_route_change.md) | Do native target/other token intersections or absent main-to | Reject only actual main/other role-token collision and empty |
| 2026-10-13 05:27:33 | [route_change](20261013-052733_route_change.md) | Do actual nested relation span omission or spatial mask padd | M200 completes23/50,best.4952795207500458@13 below champion; |
| 2026-10-13 07:26:35 | [route_change](20261013-072635_route_change.md) | Do native relation-other intersections or later-root-span om | Retain relation sign stableID with220actual intersections/co |
| 2026-10-13 09:30:30 | [route_change](20261013-093030_route_change.md) | 两个独立损失契约诊断已复现，但GPU7占用76279 | 保留main-role-weight-precedence与secondary-positive-mass� |
| 2026-10-13 10:26:50 | [route_change](20261013-102650_route_change.md) | Prior precedence control altered unmatched EOS as well as ac | Keep stable IDs, preserve legacy failure and use the preregi |
| 2026-10-14 01:52:02 | [route_change](20261014-015202_route_change.md) | Native calibration and task responses measured; is an indepe | Preserve three validation IDs and failures; no bare normaliz |
| 2026-10-14 03:10:58 | [next_batch](20261014-031058_next_batch.md) | BETWEEN centroid prototype is no-op; does a coherent physica | Keep m95-native-between-pair-support at validation for indep |
| 2026-10-14 04:20:00 | [next_batch](20261014-042000_next_batch.md) | BPS独立实现与原生回归后是否直接启动长训练 | 继续V2语义回归与训练耗时定位，暂不准入或� |
| 2026-10-14 05:14:26 | [question](20261014-051426_question.md) | BPS scoped commit permission  | 等待限定范围提交授权；保留证据，不自动提 |
| 2026-10-14 09:55:28 | [manual](20261014-095528_manual.md) | 用户确认仅提交已验证BPS包和配置并启动GPU7训练 | 已按明确授权提交10个已测试文件，commit=f8457d3b657e66306a7fce1afb3d81d8ab87 |
| 2026-10-14 09:59:29 | [queue_push](20261014-095929_queue_push.md) | server-6 gpu7 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M201 coherent physical BETWEEN pair support loss] config |
| 2026-10-14 11:39:23 | [other](20261014-113923_other.md) | 原生TRAIN随机剪切改变BPS几何读数，是否停止当前训练或启动修复变体？ | 保留M201-BPS正常训练，补充几何/数值边界证据；不据此新建affine或标量修复变体 |
| 2026-10-14 13:02:46 | [other](20261014-130246_other.md) | 扩展BPS理想物体掩码总体及配对控制，是否能外推全零或据此新增训练？ | 撤回全局全零外推；保留同一BPS科学边界和现有训练。原生捕获适配失败仅保留证据，不新增变体或放宽加载/重复门槛；本轮精确 |
| 2026-10-14 13:31:29 | [other](20261014-133129_other.md) | 新冻结BPS检查点能否承接关系与旧标量诊断？ | 原生捕获、固定旧样本和完整掩码库只作诊断；保留M201训练和旧标量未通过门槛，不启动分母/优先级变体。 |
| 2026-10-14 13:39:17 | [other](20261014-133917_other.md) | GT最小配对使原生低IoU掩码损失变正，是否保证更好的目标质量排序？ | 否定该普遍保证；不把GT配对oracle直接变成训练修复。保留原生反例和原M201训练。 |
| 2026-10-14 14:31:13 | [other](20261014-143113_other.md) | 语义吸引/GT配对oracle活动是否意味着一致的原生任务更新？ | 保留局部方向不一致及有限差分FAIL；不从局部组件外推完整语义更新伤害，不启动PCGrad/权重/分母/优先级或裸ora |
| 2026-10-14 15:51:08 | [manual](20261014-155108_manual.md) | 用户要求移动到server4上训练 | M201-BPS保留原科学准入并从epoch8完整检查点在server4唯一GPU0续训，精确停源，更新队列/运行映射/ |
| 2026-10-14 16:32:20 | [other](20261014-163220_other.md) | 局部角色方向是否能直接外推参数方向，且迁移后进程枚举缺失是否意味着死亡？ | 核验既有参数梯度仪器，保留三条原有ID及六门槛false；用精确PID/原生日志纠正本实验一次误记，不重启训练。 |
| 2026-10-14 18:00:11 | [other](20261014-180011_other.md) | 冻结原生参数梯度实验是否已完成非GPU准备，迁移监控能否可靠识别现有训练？ | 完成server4资产/AST/检查点/真实输入准备；三条原ID转为真实exclusive_gpu_slot阻塞，保留六 |
| 2026-10-15 03:09:48 | [early_stop](20261015-030948_early_stop.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps]  | kill PID=2634704 on server-4 gpu=0 |
| 2026-10-15 03:35:14 | [other](20261015-033514_other.md) | M201监控早停是否符合原生patience，队列开槽是否等于显存与独占锁释放？ | 纠正同一M201记录为stopped_unknown/协议中断；只修cluster/server4原生精度与续训计数；四 |
| 2026-10-15 15:27:50 | [route_change](20261015-152750_route_change.md) | USER20261015: restore point-feature-update mainline  | Primary: hierarchical point-feature updates  |
| 2026-10-15 16:47:56 | [other](20261015-164756_other.md) | M95 feature path: CPU/native-input diagnosis  | Hold GPU capture; supervision is auxiliary  |
| 2026-10-15 17:19:40 | [other](20261015-171940_other.md) | M95 checkpoint-source CPU control  | Keep primary resource retry and auxiliary holds  |
| 2026-10-15 18:16:47 | [other](20261015-181647_other.md) | Due primary resource guard on pinned server-4 GPU0  | Keep hierarchical point-feature diagnostic blocked; no nativ |
| 2026-10-15 20:14:02 | [other](20261015-201403_other.md) | Due hierarchical point-feature diagnostic resource check  | Keep same mainline candidate resource-blocked; no native lau |
| 2026-10-15 21:20:43 | [other](20261015-212043_other.md) | Five due records: primary resources and four auxiliary scope | Primary remains blocked by original GPU/flock guards; retain |
| 2026-10-15 23:11:24 | [other](20261015-231124_other.md) | Due hierarchical point-feature native-capture resource guard | Keep primary candidate resource-blocked under original guard |
| 2026-10-16 00:46:59 | [manual](20261016-004659_manual.md) | User requested research design; clarified VRAM is a referenc | Prepare one conditional hierarchical disjoint-support point- |
| 2026-10-16 02:17:57 | [other](20261016-021757_other.md) | Localize the preserved hierarchical prototype float32 failur | Keep all original FAILs and gates; wait for guarded native c |
| 2026-10-16 08:39:03 | [manual](20261016-083904_manual.md) | server4 remains blocked; user authorizes fallback to server3 | Use only server3 GPU1; isolated exact-commit M95 deployment  |
| 2026-10-16 09:12:48 | [manual](20261016-091248_manual.md) | User confirms all future work on server3 GPU1.  | Pin all future training and GPU diagnostics to server3 GPU1. |
| 2026-10-16 10:37:28 | [question](20261016-103728_question.md) | 独立候选完整原生反向和显存已通过，但同口 | 不入队不训练，不放宽10G或数值阈值；等待明 |
| 2026-10-16 04:21:03 | [manual](20261016-042103_manual.md) | 按最新用户授权使用server4 GPU0，并继续沿用ser | 已配置server3 GPU1与server4 GPU0各1槽，总容量2；� |
| 2026-10-16 13:18:06 | [other](20261016-131806_other.md) | 完成server4项目独立环境入口；核心模型仍缺� | 入口部署、远端哈希、Conda加载通过后绑定serv |
| 2026-10-16 13:51:52 | [manual](20261016-135152_manual.md) | 用户明确接受当前实现略超10G，是否继续同一 | 仅对冻结十项源码哈希的M202-HDS接受10.034588748G |
| 2026-10-16 13:54:03 | [queue_push](20261016-135403_queue_push.md) | server-3 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M202-HDS hierarchical disjoint-support point-feature upd |
| 2026-10-16 13:59:39 | [manual](20261016-135939_manual.md) | 原生入口晚设CUDA可见性导致零步启动落到GPU0� | 精确停止本次3660/5129/5196，外部23959保持；前� |
| 2026-10-16 14:00:23 | [queue_push](20261016-140023_queue_push.md) | server-3 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M202-HDS hierarchical disjoint-support point-feature upd |
| 2026-10-16 14:05:59 | [manual](20261016-140559_manual.md) | 原环境共享内存管理器无执行位，如何保持原 | 保留并停止第二次零步故障；只在项目目录复 |
| 2026-10-16 14:09:47 | [manual](20261016-140947_manual.md) | 新增GPU守卫零尺寸分配不出NVML上下文，是否� | 配对控制证实empty0无NVML记录，zeros1加同步正� |
| 2026-10-16 14:11:05 | [queue_push](20261016-141105_queue_push.md) | server-3 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M202-HDS hierarchical disjoint-support point-feature upd |
| 2026-10-16 17:29:12 | [manual](20261016-172912_manual.md) | 用户要求将同一 M202-HDS 从 server3 移动到 server4 | 授权保持原模型、revision2、seed1999、batch2、epoc |
| 2026-10-16 17:35:01 | [queue_push](20261016-173501_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M202-HDS hierarchical disjoint-support point-feature upd |
| 2026-10-16 18:20:04 | [other](20261016-182005_other.md) | 首轮训练验证后，现有产物能否支持原生恢复 | 保持当前 M202-HDS 训练不变；checkpoint 恢复字段 |
| 2026-10-17 00:32:17 | [other](20261017-003217_other.md) | M202原进程TypeError中断；同源码原生resume及固定TRAIN反向已核验，是否恢复同一实验？ | 归档原故障后，仅在server4物理GPU0对同一M202执行一次epoch7检查点原生resume；不改模型、协议、修 |
| 2026-10-17 00:34:08 | [queue_push](20261017-003408_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M202-HDS hierarchical disjoint-support point-feature upd |
| 2026-10-17 12:25:44 | [other](20261017-122544_other.md) | 续做原生逐表达证据导出器，当前可否进入GPU | 13项CPU测试、源码契约及冻结资产准备通过；� |
| 2026-10-17 14:48:08 | [other](20261017-144808_other.md) | M202已正常早停，完整配对验证与TRAIN点特征诊 | 归档SAME M202于29轮原生早停，best0.494656未超历� |
| 2026-10-17 16:38:54 | [other](20261017-163854_other.md) | HDS各尺度是否都有益，先前零消息对照能否隔 | 固定4TRAIN场景8子集原生诊断完成；保留偏置� |
| 2026-10-17 20:58:27 | [other](20261017-205827_other.md) | 32TRAIN场景的内容对照与Q/F归因后，能否开始� | 完成8pilot+24独立内容复核及32场景Q/F诊断；正� |
| 2026-10-17 22:59:19 | [next_batch](20261017-225919_next_batch.md) | 细层逐点交换是否达到一次结构首筛的执行准 | 仅准入一个新实验 M203-FLE，先安全同步再由现 |
| 2026-10-17 23:01:35 | [queue_push](20261017-230135_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M203 FLE fine-recipient point exchange with M95 larger-s |
| 2026-10-18 00:54:05 | [other](20261018-005405_other.md) | What remains executable for FLE self/nonself diagnostic?  | CPU prepared; native replay waits for exclusive GPU.  |
| 2026-10-18 04:29:59 | [other](20261018-042959_other.md) | Does fixed-leaf metric exchange survive rigid coordinates?  | Keep M203; confirm native scope before any source repair.  |
| 2026-10-18 06:22:14 | [other](20261018-062214_other.md) | Is cutoff equality consistent with exact represented input?  | Keep source frozen; audit is not a model repair.  |
| 2026-10-18 08:31:02 | [other](20261018-083102_other.md) | 精确并列回退是否产生独立于舍入与并列邻居 | 有限CPU对照确认人工叶中的分支支持不连续； |
| 2026-10-18 10:18:10 | [other](20261018-101810_other.md) | 零新增参数的FLE是否仍保留按N*K*C分配的邻域� | 完成有限CPU存储核对；保留M203原训练，原生ma |
| 2026-10-18 15:03:39 | [other](20261018-150339_other.md) | What did valid terminal point-content controls establish?  | Keep failed M203 stopped;valid controls do not prove benefit |
| 2026-10-18 17:02:06 | [other](20261018-170206_other.md) | 点云与query贡献及层级融合是否受padding污染？ | 保留首轮范数失败及32场景有效复现；确认FLE/ |
| 2026-10-18 19:07:17 | [other](20261018-190717_other.md) | 统一padding参考是否技术可行，训练前缀能否� | 双模型正确性、接口反向及真实train模式反向� |
| 2026-10-18 21:11:38 | [other](20261018-211138_other.md) | 原生前缀重复性与方法收益应如何区分？  | FLE局部行序原因已有严格对照，M95具体原因未 |
| 2026-10-18 23:09:03 | [other](20261018-230903_other.md) | 条件跨粗簇通道秩是否足以支持新结构训练？ | 有限数值审计收束；主线条件秩诊断有实测， |
| 2026-10-19 00:31:09 | [other](20261019-003109_other.md) | Native rank/null diagnostic resource stop  | Preserve strict failed native gate; no GPU sharing or scope  |
| 2026-10-19 02:59:41 | [other](20261019-025941_other.md) | Finite conditional channel audit and scientific admission  | Close only the bounded diagnostic;preserve failed1e-6 gate;n |
| 2026-10-19 04:42:32 | [other](20261019-044232_other.md) | 点云特征位置对应与父子映射诊断能否支持一 | 保留两项有限诊断，不新增模型、不准入训练 |
| 2026-10-19 07:07:36 | [other](20261019-070736_other.md) | 粗层语义到点特征的独立结构是否达到科学准 | 保留同一CPA候选validation及一次key连接修订；� |
| 2026-10-19 09:05:00 | [question](20261019-090500_question.md) | 用户要求启动CPA-R1，但科学准入仍有未通过项 | 不伪造准入或启动；请求仅对此候选的明确探 |
| 2026-10-19 09:23:51 | [manual](20261019-092351_manual.md) | 用户明确回复授权，是否执行CPA-R1单次探索性训练？ | 仅为M204-CPA在server4GPU0执行限定提交、安全同步与一次原生训练；保留diagnosis/semanti |
| 2026-10-19 09:36:15 | [manual](20261019-093615_manual.md) | CPA-R1单次探索性训练是否已经真实运行？ | M204-CPA已在server4物理GPU0启动，原生迭代增长已验证并登记；本轮仅释放编排租约，远端训练继续持有GPU |
| 2026-10-19 14:39:42 | [question](20261019-143942_question.md) | M204-CPA original process disappeared after the server4 rebo | Record stopped_unknown and preserve epoch5 full checkpoint/n |
| 2026-10-19 16:36:08 | [manual](20261019-163608_manual.md) | Human authorized the exact same M204 checkpoint resume after | Restored same M204 on server4 physicalGPU0 from epoch5 last. |
| 2026-10-19 13:45:33 | [manual](20261019-134533_manual.md) | Explicit human authorization: server4 GPU1 experiments  | Add server4 GPU1 to project allocation; preserve GPU0 M204;  |
| 2026-10-19 23:25:50 | [other](20261019-232550_other.md) | Native batch-minimum incidence; GPU1 externally occupied.  | Keep frozen paired audit and M204; wait for legal GPU slot.  |
| 2026-10-20 00:37:50 | [other](20261020-003750_other.md) | Native relabel audit prepared; external GPU occupation.  | Keep two original protocols; no sharing or new training.  |
| 2026-10-20 02:21:55 | [other](20261020-022155_other.md) | Due native diagnostics remain resource-blocked.  | Keep frozen protocols; no sharing, restart or new training.  |
| 2026-10-20 04:38:18 | [other](20261020-043818_other.md) | M204 natural earlystop; native tests expose numerical contro | Preserve strict gates and measured hierarchy sensitivity; co |
| 2026-10-20 08:33:35 | [other](20261020-083335_other.md) | Native replay variation localized; no new structural design. | Preserve strict failures; distinguish diagnostics from archi |
| 2026-10-20 10:30:48 | [other](20261020-103048_other.md) | 用户询问流水线是否异常及为何不设计新实验 | 确认非reserve-only缺口设计仍允许推进；承认独 |
| 2026-10-20 13:08:27 | [next_batch](20261020-130827_next_batch.md) | 主线停滞后如何推进真实的新结构实验  | 登记并实现独立PCE跨细叶物理接触特征交互原 |

| 20261020-151332 | next_batch | PCE-R2已测试但未准入 | 图/算子等价与反向通过，源码数值失败，待有范围的额外实现修订确认 |
| 2026-10-20 22:56:15 | [other](20261020-225615_other.md) | PCE额外一次局部修订完成但完整数值控制仍失 | 保留R1/R2/R3全部失败；R3停止追加修改，未准� |
| 2026-10-20 23:12:09 | [other](20261020-231209_other.md) | 8场景32表达的独立层级特征诊断完成  | 粗尺度特异污染和纯常数偏移两个预注册解释 |
| 2026-10-20 23:18:33 | [other](20261020-231834_other.md) | 实际ILA输入路径与层级尺度来源的两条独立解 | 保留三项局部诊断及混合方向；尺度特异污染 |
| 2026-10-21 00:29:19 | [next_batch](20261021-002919_next_batch.md) | Can committed RSTR pass the frozen conservation control?  | Hold RSTR; preserve commit and all failed controls.  |
| 2026-10-21 01:09:41 | [next_batch](20261021-010941_next_batch.md) | Admit M205 MDC native YAML experiment  | Admit the tested MDC version under approved experiment-first |
| 2026-10-21 05:08:00 | [queue_push](20261021-050800_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M205-MDC middle directional convolution] configs/Quard/c |
| 2026-10-21 05:15:06 | [next_batch](20261021-051506_next_batch.md) | Admit M206 CGCA and use server4 second GPU  | Admit tested CGCA native YAML under experiment-first; safe s |
| 2026-10-21 05:15:56 | [queue_push](20261021-051556_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M206-CGCA coarse conditioned fine channel attention] con |
| 2026-10-21 05:29:12 | [next_batch](20261021-052912_next_batch.md) | Prepare M207 HAP reserve while both server4 GPUs train  | Save independent HAP static version; native checks wait for  |
| 2026-10-21 06:15:26 | [other](20261021-061526_other.md) | Both server4 GPUs busy; HAP native smoke is still pending.  | Preserve runs; prepare HAP worker and wait for an idle GPU.  |
| 2026-10-21 07:15:54 | [other](20261021-071554_other.md) | HAP bundle staged; both server4 GPUs remain occupied.  | Keep runs; wait for idle GPU before HAP native checks.  |
| 2026-10-21 11:26:36 | [manual](20261021-112636_manual.md) | User requests GPU0 only and queue GPU1 task for resume.  | Stop M206 GPU1; queue full-state resume on GPU0.  |
| 2026-10-21 23:27:09 | [manual](20261021-232709_manual.md) | Re-enable server4 GPU1  | Resume SAME M206 on GPU1  |
| 2026-10-21 23:28:11 | [queue_push](20261021-232811_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M206-CGCA coarse conditioned fine channel attention] con |
| 2026-10-22 00:16:20 | [next_batch](20261022-001620_next_batch.md) | M205 terminal; admit tested HAP  | Train M207-HAP on free GPU0  |
| 2026-10-22 00:20:30 | [queue_push](20261022-002030_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M207-HAP hierarchy affine coarse-to-fine prolongation] c |
| 2026-10-22 02:16:49 | [next_batch](20261022-021649_next_batch.md) | Prepare HRC while both GPUs train?  | Keep HRC native-pending; preserve both runs  |
| 2026-10-22 04:22:52 | [next_batch](20261022-042252_next_batch.md) | How to advance HRC on occupied GPUs?  | Freeze worker; wait for one authorized slot  |
| 2026-10-22 08:27:06 | [next_batch](20261022-082706_next_batch.md) | HRC adapter preparation while both GPUs are busy  | Freeze reviewed adapter; await real idle slot  |
| 2026-10-22 10:29:34 | [next_batch](20261022-102934_next_batch.md) | Prepare an independent middle sibling-state structure  | Select M209-PSBR; native checks remain required  |
| 2026-10-22 10:59:13 | [manual](20261022-105913_manual.md) | Pause M206 on GPU1 and release that card to others  | Preserve epoch24 checkpoint; allow project GPU0 only  |
| 2026-10-22 12:27:48 | [question](20261022-122748_question.md) | HAP crashed; exact full-state resume?  | Await HAP GPU0 resume grant and free GPU0  |
| 2026-10-22 15:25:44 | [manual](20261022-152544_manual.md) | Human authorizes exact HAP GPU0 full resume | Queue same HAP epoch18 full-state resume on GPU0 |
| 2026-10-22 15:26:21 | [queue_push](20261022-152621_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M207-HAP hierarchy affine coarse-to-fine prolongation] c |
| 2026-10-22 20:24:58 | [other](20261022-202458_other.md) | HRC fresh-dispatch HEAD mismatch  | Bind same HRC source to HEAD74f; keep native pending  |
| 2026-10-22 22:22:42 | [queue_push](20261022-222242_queue_push.md) | Admit HRC after real native and resource checks  | Queue tested HRC74f on authorized GPU0  |
| 2026-10-22 22:28:28 | [queue_push](20261022-222828_queue_push.md) | Admit PSBR after real native and resource checks  | Queue tested PSBR74f on authorized GPU0  |
| 2026-10-22 22:32:08 | [queue_push](20261022-223208_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [HRC refined-token hierarchy] configs/Quard/ctf_hcg_csort |
| 2026-10-23 00:25:01 | [next_batch](20261023-002501_next_batch.md) | Prepare independent parent spectral token coupling  | Prepare PSNC outside repo; preserve admitted PSBR74f  |
| 2026-10-23 02:25:58 | [other](20261023-022558_other.md) | Prepare PSNC native-check draft  | Prepare disabled draft; protect PSBR74f FIFO  |
| 2026-10-23 04:26:42 | [other](20261023-042642_other.md) | Finish PSNC guarded native adapter  | Anchor reviewed adapter; wait for idle GPU0  |
| 2026-10-23 14:10:32 | [queue_push](20261023-141032_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [PSBR parent-segmented bidirectional state] configs/Quard |
| 2026-10-24 06:24:25 | [queue_push](20261024-062425_queue_push.md) | Admit PSNC43 after actual paired native and resource review  | Queue exact tested M210-PSNC on authorized GPU0  |
| 2026-10-24 06:25:10 | [queue_push](20261024-062510_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [PSNC parent spectral nonlinear token coupling] configs/Q |
| 2026-10-25 00:19:59 | [queue_push](20261025-001959_queue_push.md) | Admit BTC00e after actual paired native and resource review  | Queue exact tested M211-BTC on authorized GPU0  |
| 2026-10-25 00:24:18 | [queue_push](20261025-002418_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [BTC parent binary tree complement composition] configs/Q |
| 2026-10-25 11:31:14 | [manual](20261025-113114_manual.md) | Reauthorize server4 GPU1 from direct human instruction  | Add physicalGPU1 to allowed_gpus, preserve BTC GPU0 and M206 |
| 2026-10-25 11:54:59 | [queue_push](20261025-115459_queue_push.md) | Admit BCR11a after actual paired native and resource review  | Queue exact tested M212-BCR on authorized GPU1  |
| 2026-10-25 11:57:49 | [queue_push](20261025-115749_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [BCR exclusive bidirectional complement recurrence] confi |
| 2026-10-25 12:30:51 | [next_batch](20261025-123051_next_batch.md) | 双卡训练占满且待跑储备不足  | 准备M213-BFC同父组多阶段双输出交互，仅保存� |
| 2026-10-25 14:28:12 | [other](20261025-142812_other.md) | 继续M213-BFC验证准备，两张卡仍在训练  | 完成受审BFC编排工具及结果审核草稿；两卡忙 |
| 2026-10-25 16:37:18 | [next_batch](20261025-163718_next_batch.md) | 已有BFC等待空卡且储备缺一  | 准备M214-CTS源代码与固定原YAML，完成本地生产 |
| 2026-10-25 18:29:01 | [other](20261025-182901_other.md) | 两卡持续训练、现有2项储备已满且CTS原生工� | 继续原BTC0/BCR1；保存CTS禁用原生检查包与实际 |
| 2026-10-26 00:31:49 | [queue_push](20261026-003149_queue_push.md) | Admit BFC48fc after actual paired native and resource review | Queue exact tested M213-BFC on its actual selected authorize |
| 2026-10-26 00:35:50 | [queue_push](20261026-003550_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [BFC simultaneous two-output butterfly token composition] |
| 2026-10-26 02:30:26 | [next_batch](20261026-023026_next_batch.md) | 两原训练占卡时如何推进本轮唯一准备额度？ | 保留BFC0/BCR1和M206暂停，CTS完成受审4e8版本静� |
| 2026-10-26 04:34:32 | [other](20261026-043432_other.md) | 两个既有准备名额已满且两原训练占卡，本轮 | 不增模型候选；完成CTS原四结果只读语义checke |
| 2026-10-26 06:29:24 | [other](20261026-062924_other.md) | 两原训练仍增长，但两张授权卡出现额外未登 | 保留BFC、BCR及不明PID1565126，不驱逐/暂停/迁卡 |
| 2026-10-26 06:43:58 | [other](20261026-064358_other.md) | GPU验证受阻时推进既有BEC的哪个合法本地步骤 | 已将原2d06精确9blob保存为隔离源9b6782/单父实� |
| 2026-10-26 08:34:55 | [other](20261026-083455_other.md) | 两项既有准备储备已满且GPU仍忙时如何推进BEC | 已完成对应source9b678/parent-live48fc的新native/opera |
| 2026-10-26 13:36:51 | [manual](20261026-133651_manual.md) | User requests 不用gpu1  | Disable future server4GPU1 computation and dispatch; only ph |
| 2026-10-26 13:45:54 | [queue_push](20261026-134555_queue_push.md) | Admit exact testedCTS4e8 after actual twoTRAIN steps and pai | Create actual experiment-first receipt and FIFO waiting CTS  |
| 2026-10-26 14:05:15 | [queue_push](20261026-140515_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [CTS parent cyclic triadic state composition] configs/Qua |
| 2026-10-26 18:14:58 | [other](20261026-181458_other.md) | BEC R1已审026c工具是否可作待测准备  | 接受同一R1的静态版本绑定；等待唯一GPU0原CTS |
| 2026-10-26 23:18:06 | [queue_push](20261026-231806_queue_push.md) | Admit exact testedBEC026c R1 after actual twoTRAIN steps and | Create actual experiment-first receipt and FIFO waiting BEC  |
| 2026-10-26 23:18:49 | [queue_push](20261026-231849_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [BEC cross-level bipartite edge composition R1] configs/Q |
| 2026-10-27 12:40:21 | [queue_push](20261027-124021_queue_push.md) | Admit exact AEF56 after actual matched original TRAIN2 and r | Create actual experiment-first receipt and FIFO GPU0 waiting |
| 2026-10-27 12:41:01 | [queue_push](20261027-124101_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [AEF parent antisymmetric edge flux] configs/Quard/ctf_hc |
| 2026-10-27 14:45:01 | [next_batch](20261027-144501_next_batch.md) | 如何补充现有层级point-feature储备而不打断GPU0训练？ | 登记一个HPC全树非线性组合原型；保留CRE兼容d585与当前AEF训练，原生与资源检查等待合法空槽。 |
| 2026-10-28 00:42:41 | [next_batch](20261028-004241_next_batch.md) | AEF正常早停后，两条独立储备的原M95导入检查 | 保留AEF正常终态和两条原始失败；先定位依赖 |
| 2026-10-28 02:39:08 | [queue_push](20261028-023908_queue_push.md) | Admit exact CRE56 after actual matched original TRAIN2 and r | Create actual experiment-first receipt and FIFO GPU0 waiting |
| 2026-10-28 02:41:47 | [queue_push](20261028-024147_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [CRE cross-root directed edge broadcast] configs/Quard/ct |
| 2026-10-28 02:57:18 | [next_batch](20261028-025718_next_batch.md) | 接续已测CRE并补本轮唯一独立储备缺口  | CRE四项真实检查通过后以精确d585准入并唯一� |
| 2026-10-28 18:31:43 | [queue_push](20261028-183144_queue_push.md) | Admit exact HPC6282 after actual matched original TRAIN2 and | Create actual experiment-first receipt and FIFO GPU0 waiting |
| 2026-10-28 18:32:59 | [queue_push](20261028-183259_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [HPC hierarchy tree resolvent nonlinear composition] conf |
| 2026-10-28 20:38:53 | [queue_push](20261028-203853_queue_push.md) | Admit exact compatible APF after actual matched original TRA | Create actual experiment-first receipt and FIFO GPU0 waiting |
| 2026-10-28 20:39:37 | [queue_push](20261028-203937_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [APF ancestry path factor composition] configs/Quard/ctf_ |
| 2026-10-28 22:44:42 | [queue_push](20261028-224442_queue_push.md) | Admit exact compatible DCE after actual matched original TRA | Create actual experiment-first receipt and FIFO GPU0 waiting |
| 2026-10-28 22:45:30 | [queue_push](20261028-224530_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [DCE directed hierarchy cavity composition] configs/Quard |
| 2026-10-29 17:50:08 | [queue_push](20261029-175008_queue_push.md) | Admit exact compatible PES after actual matched original TRA | Create actual experiment-first receipt and FIFO GPU0 waiting |
| 2026-10-29 17:50:54 | [queue_push](20261029-175054_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [PES persistent palindromic Euler node-state composition] |
| 2026-10-29 22:25:10 | [queue_push](20261029-222510_queue_push.md) | Admit exact compatible AOC after actual matched original TRA | Create actual experiment-first receipt and FIFO GPU0 waiting |
| 2026-10-29 22:25:55 | [queue_push](20261029-222555_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [AOC ancestral-order shared-cell commutator composition]  |
| 2026-10-30 14:40:00 | [queue_push](20261030-144000_queue_push.md) | Admit exact compatible FCB after actual matched original TRA | Create actual experiment-first receipt and FIFO GPU0 waiting |
| 2026-10-30 14:40:33 | [queue_push](20261030-144033_queue_push.md) | server-4 gpu0 空闲，推送哪个排队实验？ | [FCB fine-coarse complete-bipartite composition] 启动待核验，保留认领名 |
| 2026-10-30 15:55:15 | [manual](20261030-155515_manual.md) | Re-enable server4 GPU1 for cluster_project  | Allow server4 GPU0 and GPU1, one task per card  |
| 2026-10-30 16:32:03 | [queue_push](20261030-163203_queue_push.md) | Admit exact compatible SFC after actual matched original TRA | Create actual experiment-first receipt and FIFO GPU1 waiting |
| 2026-10-30 16:32:51 | [queue_push](20261030-163251_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [SFC synchronous full-neighbor state composition] configs |
| 2026-10-30 16:51:34 | [queue_push](20261030-165134_queue_push.md) | Admit exact compatible ELC after actual matched original TRA | Create actual experiment-first receipt and FIFO GPU0 waiting |
| 2026-10-30 16:52:25 | [queue_push](20261030-165225_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [ELC undirected edge-state line-graph composition] config |
| 2026-10-31 18:35:26 | [queue_push](20261031-183526_queue_push.md) | Admit exact compatible WFC after actual matched original TRA | Create actual experiment-first receipt and FIFO GPU0 waiting |
| 2026-10-31 18:36:14 | [queue_push](20261031-183614_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [WFC unordered-wedge factor incidence composition] config |
| 2026-10-31 20:52:00 | [queue_push](20261031-205200_queue_push.md) | Admit exact compatible LFT after actual matched original TRA | Create actual experiment-first receipt and FIFO GPU1 waiting |
| 2026-10-31 20:52:53 | [queue_push](20261031-205253_queue_push.md) | server-4 gpu1 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [LFT nonlinear lifting analysis and synthesis] configs/Qu |
| 2026-11-01 12:06:09 | [manual](20261101-120609_manual.md) | 用户要求暂停WFC/LFT并停止两卡使用  | 已精确停止两个原任务；禁用server4双卡派发� |
| 2026-11-04 11:31:28 | [manual](20261104-113128_manual.md) | 用户重新开放server4 GPU0  | 仅开放GPU0，GPU1禁用，保留独立暂停实验hold  |
| 2026-11-04 11:45:42 | [queue_push](20261104-114542_queue_push.md) | server-4 gpu0 空闲，推送哪个排队实验？ | [WFC unordered-wedge factor incidence composition] 启动待核验，保留认 |
| 2026-11-04 11:47:50 | [queue_push](20261104-114750_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [WFC unordered-wedge factor incidence composition] config |
| 2026-11-04 11:50:55 | [manual](20261104-115055_manual.md) | 用户要求GPU0启动实验  | WFC从完整第25轮检查点续训，第26轮步数已增� |
| 2026-11-04 22:11:58 | [manual](20261104-221158_manual.md) | 用户明确允许GPU0叠加现有任务且显存足够 | 仅server4物理GPU0启用allow_external_overlay=true，项目max1与原task_mem |
| 2026-11-04 23:01:55 | [queue_push](20261104-230155_queue_push.md) | Admit exact compatible NEC after actual matched original TRA | Create actual experiment-first receipt and FIFO GPU0 waiting |
| 2026-11-04 23:09:10 | [queue_push](20261104-230910_queue_push.md) | server-4 gpu0 有外部任务但剩余显存>20000MB，是否叠加本项目实验？ | 启动 [NEC persistent node-edge state composition] configs/Quar |
| 2026-11-06 03:07:32 | [queue_push](20261106-030732_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [MIC ancestry Mobius interaction composition] configs/Qua |
| 2026-11-06 19:52:30 | [queue_push](20261106-195230_queue_push.md) | server-4 gpu0 空闲，推送哪个排队实验？ | [HVD] 启动待核验，保留认领名额，禁止自动重试 |
| 2026-11-06 21:00:35 | [other](20261106-210035_other.md) | HVD已单次真实启动并由canonical核实，但实际direct Popen未继承三协作锁；旧owner的纠正启动在过 | 当前owner另存审查绑定并只启动一次CPU guardian3024669，为现有trainer2829477补持tr |
| 2026-11-06 22:06:59 | [other](20261106-220659_other.md) | HVD训练运行时崩溃，如何保护状态并推进已有候选？ | 精确归档crashed、保留完整epoch4及原日志，不自动resume；PSC软件缺项完成，NSD隔离储备登记，下一轮 |
| 2026-11-07 00:05:16 | [other](20261107-000516_other.md) | PSC原生两步已通过但本轮资源检查不完整，是否准入？ | 保留validation与3臂部分实测，不准入/入队/启动；下轮新owner补资源。CPU PATH隔离实证与生产绑定分 |
| 2026-11-07 02:04:06 | [queue_push](20261107-020406_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M231-PSC] configs/Quard/ctf_hcg_csort_psc/model_base1_qu |
| 2026-11-08 01:57:10 | [other](20261108-015710_other.md) | M232-NSD 原生检查已完整通过，是否技术准入  | 准入本轮真实测试的M232-NSD/source f625；仅四tech |
| 2026-11-08 03:55:59 | [queue_push](20261108-035559_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [NSD hierarchy native spatial Dirichlet composition] conf |
| 2026-11-08 23:47:22 | [next_batch](20261108-234722_next_batch.md) | M233-NDE revision1 real native TRAIN2, original paired resou | Grant technical experiment-first admission for exact source0 |
| 2026-11-09 01:52:04 | [queue_push](20261109-015204_queue_push.md) | server-4 gpu0 有外部任务但剩余显存>20000MB，是否叠加本项目实验？ | 启动 [M233-NDE] configs/Quard/ctf_hcg_csort_nde/model_base1_qu |
| 2026-11-09 17:58:29 | [queue_push](20261109-175829_queue_push.md) | server-4 gpu0 有外部任务但剩余显存>20000MB，是否叠加本项目实验？ | 启动 [M234-RVE receiver-conditioned fine-leaf vector exchange] |

| 2026-11-10T07:59:05.034381+00:00 | next_batch | M235-SINC 技术准入；生产入口待完成，保留hold | 20261110-075905_M235_admission.md |
| 2026-11-10 19:47:58 | [queue_push](20261110-194758_queue_push.md) | server-4 gpu0 空闲（util<10% 且显存<1024MB），推送哪个排队实验？ | 启动 [M235 SINC native fine-leaf geometric simplex incidence;  |
| 2026-11-10 23:15:51 | [question](20261110-231551_question.md) | [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_sinc] | 标记 crashed；checkpoint 留远端，日志已拉取，留待用户决定 |
| 2026-11-10 23:25:01 | [other](20261110-232501_other.md) | M235自然崩溃后，是否重启或借外部占用插入M236测试？ | 归档M235并保留运行失败/机制未定；不重启。M236复用已审包，当前仅按GPU0原20GB预算等待。 |
| 2026-11-11 07:18:52 | [other](20261111-071852_other.md) | M236启动前显存变化导致原生验证拒绝，是否重试同一意图或把源码整合算作准入？ | 保留已消费阶段和真实零步拒绝；当前显存19494<20000，不重放、不准入。整合5413102仅保留版本，原生/资源仍 |
