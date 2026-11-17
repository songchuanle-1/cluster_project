# 新候选收尾登记，准备完成但作者未执行

默认 NOP。本脚本没有 SSH/GPU/训练入口，仅 root 在当前4ecb5020租约内显式 --execute-root 后写入 research_work、memory 和 tick/report_notes。仅追加 M235-SINC / M236-CSO，原160候选逐对象完全保持；若已登记或 intent 已存在则停止，不重放。

root最短调用：python -B ABS/record_new_candidates.py --execute-root
可选真实证据参数：--sinc-native-actual ABS_JSON --sinc-native-review ABS_REVIEW；--sinc-resources-actual / --sinc-resources-review；CSO对应 --cso-native-actual / --cso-native-review / --cso-resources-actual / --cso-resources-review。--tick-attempt-actual ABS_JSON 可将 tick_attempt 指向上述已接收的新候选 native/resources 真实结果。证据必须本tick下且owner吻合。结果SHA在登记时计算并保存；review必须显式引用该actual SHA。

需 python -B、GIT_OPTIONAL_LOCKS=0、CODEX_THREAD_ID为owner thread；租约/context/pending/foreground/goal/SERVERS/main HEAD/index/dirty28+r0均守卫。源FROZEN+源码hash逐项核对。stage默认implementation；只有真实native和resources均通过且各自review通过才为validation。无actual保留NOT_RUN，有实际PASS未review标为OBSERVED_PASSED_AWAITING_REVIEW，失败为FAILED_OR_INCONCLUSIVE，未完为UNCERTAIN_OR_INCOMPLETE。efficacy/novelty始终UNKNOWN；不入队、不启动完整训练，不宣称M234修复。

保留旧tick_attempt到history；report_notes.actions/decisions中文；memory保留七节并强制少于120行。保留人工“双卡都空了，快设计实验”优先级，同时GPU0-only/cap1/三锁/20GB规则及M206/M227暂停不变。root继续使用既有report/finish收尾流程。若record.intent存在而actual缺失，先核实共享状态，不能自动重跑。
