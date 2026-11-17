# cluster_project 决策记录

- **时间**: 2026-07-28 13:07:58
- **类型**: terminal_analysis
- **问题**: M27-M31 (ORT-W5/ORT-W1/DCA/ITK/NH4) 终态分析自 tick #182 缺失至今。M27(ort_w5=0.05) 和 M28(ort_w1=0.001) 有 checkpoint 数据可回溯; M29/M30/M31 无 checkpoint 确认从未运行。
- **决策**: 补全 M27-ORT-W5(0.4959@ep19 stopped_unknown) + M28-ORT-W1(0.3916@ep3 stopped_unknown) 终态分析。Orth sweep 结论: 0.01 最优(0.5005), 0.05 降点-0.0046, 0.001 数据不足。关闭 orth 方向。M29/M30/M31 标记为 never-launched。
- **依据**: M27 序列 0.32→0.4959 仍在上升中被中断, 0.4959 vs M17(0.01)=0.5005 差-0.0046; M28 仅3epoch 数据不足; M29/M30/M31 在 tick #181 队列重组时被移除, server-4 无对应 checkpoint 目录
- **证据**: server-4 checkpoint 目录 + 训练日志 grep 验证 + experiments.csv
