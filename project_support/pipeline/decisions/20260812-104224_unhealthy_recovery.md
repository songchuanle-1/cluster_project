# cluster_project 决策记录

- **时间**: 2026-08-12 10:42:24
- **类型**: unhealthy_recovery
- **问题**: 上次 tick (~Aug 11 18:22) 不健康, .tick_unhealthy 存在, 报告/分析缺失~16h
- **决策**: 补齐 5 个终态分析(M75/M76/M77/M80/M81) + 修复 queue.json(M85/M86 移至 server-6 running, 新增 M88-QMOD-MLAY) + 生成 tick 报告 #486
- **依据**: pipeline_monitor 显示 5 running 存活, experiments.csv 有 5 个新 stopped_unknown 无分析; queue.json server-4 waiting 含 M85/M86 但实际在 server-6 运行
- **证据**: experiments.csv + queue.json + analyses/ 对比
