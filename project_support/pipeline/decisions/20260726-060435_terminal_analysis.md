# cluster_project 决策记录

- **时间**: 2026-07-26 06:04:35
- **类型**: terminal_analysis
- **问题**: A4-shuffle done_earlystop (Best=0.4941, ~19/50) 缺失终态分析 — 20260725-160613 tick 声称生成但未实际落盘，需补
- **决策**: 生成 pipeline/analyses/A4-shuffle_done_earlystop_20260726-060301.md: routing 三阶对比 champion(0.5012) > random(0.4941) > content(0.4468)，彻底封死 routing 方向
- **依据**: A4-shuffle 是 routing 故事线的最后一环证据；控制组证明结构注入本身有损(-0.0071)但内容路由才是灾难性退化主因(-0.0544)。补齐后 routing 方向证据链完整
- **证据**: experiments.csv row47: 0.4941 done_earlystop; goal.json findings.A4_shuffle_control; queue.json A4-shuffle entry
