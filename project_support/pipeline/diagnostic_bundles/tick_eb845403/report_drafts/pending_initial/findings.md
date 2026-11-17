# M234 worker 段错误诊断：本轮待实际结果初稿

本稿只保存报告准备内容。根因仍为 **UNKNOWN**，不代表诊断已执行、通过或修复。root应在收到本轮actual后另存新标签，补充真实结果与证据哈希。

沿用上轮已完成诊断：确认worker3815203发生SIGSEGV；父进程hier_postprocess赋值帧是已安装PyTorch SIGCHLD失败通知位置，不能代替worker原生fault stack。已修正的journal查询受可见权限限制，Apport路径/日志缺失或拒绝访问；当前共享内存使用不证明故障时压力。历史owner及证据保持原样。

本轮独立静态设计补充：

- 原train.py已选择file_system tensor sharing，并设置TOKENIZERS_PARALLELISM=false；再次设置这些项不能写成已找到修复。
- 有效非空mode4输入也可能产生M×(maxActive+1)的体素规则表/输出表内存放大。这是可检查的分配契约，不是已证明的历史OOM或SIGSEGV原因。
- 实际worker start method、持久worker生命周期、线程状态、失败样本/阶段/原生指令仍缺失。epoch2失败不证明epoch2新建了worker。

本轮路线状态：

1. kern.log/syslog及各自.1的精确PID限定后缀取证：已提出独立只读路线。本稿未读取其actual，状态为PENDING_ROOT_ACTUAL，不声明完成或无匹配。
2. 精确c86f扩展、有效非空CPU输入的fresh/fork矩阵：当前是诊断设计/准备，actual与实际独审待root补入。不能借用旧TRAIN2或数据遍历的通过结论。

解释边界：传输返回0只证明传输/采集层终态，子查询仍可失败、不可用或uncertain。内核正匹配须核对原始时间与PID，才可缩小故障对象；无匹配只覆盖读取的有限后缀。CPU全部通过只说明本组有效合成输入/进程上下文未失败，不能证明ABI全面正确、历史故障已修复或科学效果；fork-only失败也不能单独证明历史因果。

保留原始失败、已通过修订和M206/M227人工暂停。无训练重启、resume、准入、新变体或训练配置修改。本稿作者未执行SSH、Torch/native/GPU、系统查询或共享work/memory/report写入。

引用：上一轮`tick_14977661/diagnosis.md`；本轮`peer_prepare/findings.json`、`peer_prepare/worker_native_next_diagnostic.md`及`ops_prepare/proposal.json`。后两者属于准备/静态证据，不是实际执行结果。
