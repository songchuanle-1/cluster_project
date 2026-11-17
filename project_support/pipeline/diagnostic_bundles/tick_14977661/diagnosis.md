# M234 DataLoader 段错误排查

结论：确认 worker3815203 的 SIGSEGV，根因仍未知；未重启、修改训练配置或执行GPU诊断。

- 已安装Torch 2.8.0+cu128的signal_handling源码与原始trace一致：主进程通过SIGCHLD收到worker失败通知。hier_postprocess.py:87不是worker的原生fault stack。
- 实际训练batch2、4个persistent workers。worker路径包括NumPy/SciPy、TokenizerFast、torch-scatter和CPU体素化；现存日志不能确定失败worker的输入样本、阶段或原生指令。
- pointgroup扩展当前SHA与启动时c86f5168…一致。C++空输入存在边界风险，但正常数据路径在进入该边界前有非空约束，未证明本次触发。
- 原始stdout最后mtime为2026-11-09T11:32:46.407313Z，这是查询时间锚，不能当作已证明的精确崩溃时刻。
- 系统当前使用Apport；coredumpctl未安装。第一次kernel查询参数错误的记录保留；修正为journalctl -k后无可见匹配项，同时明确提示系统日志权限受限。两个限定的项目Python/UID1001 Apport报告路径不存在，/var/log/apport.log读取被拒绝。不能据此断言系统未记录错误。
- 原uncertain uname helper883090已不存在；未重放、发信号或清理。当前/dev/shm容量/使用率不是故障时压力证据。

下一项有效证据是该worker的core/原生回溯，或受控数据加载诊断中的worker PID、输入scene/annotation和阶段记录。现有数据不足以支持原因特定的代码修复，不能以短检通过证明故障已修复。
