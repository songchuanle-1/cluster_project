# Experiment Result Analysis - cluster_project
Experiment: M201-BPS | State: stopped_unknown / monitor-induced interruption

## 1. Basic Info
- 同一M201-BPS，server4 GPU0，代码与配置不变。训练从server6的epoch8完整状态迁移，未作冷启动。
- 03:09的监控以三位小数输出计算11次未改善并终止PID2634704；该原始记录保留。
- 最新完成检查点为2026-10-15 02:44:31的epoch26；epoch27仅完成到3656/4686，不能记作完成27轮。
- 本轮精确原PID已不可见，但NVML仍报告该PID占20016 MiB，训练flock仍持有。内核锁记录PID2634697也不可见，残留原因未知。

## 2. Best Metrics
| Metric | Value | @ Epoch |
|---|---|---|
| mIoU | 0.489848792552948 | 18 |
| Acc@50 | 0.541，日志三位小数 | 18 |
| spmIOU | 0.454，日志三位小数 | 18 |

## 3. Convergence Summary
- 原生完整精度日志和best/last检查点一致：epoch18刷新最佳值，epoch26的epochs_no_improve为8。
- 三位小数输出将epoch15、17、18的0.48952746、0.48971656、0.48984879均记为0.490；旧监控据此错误累计11次。
- 日志无原生Early stopping消息；本次不是原生patience10的正常收敛终止。不能把误停后的成绩当完整筛选结果或据此拒绝整个机制。

## 4. Comparison
- 相对报告Baseline 0.4894：约+0.000449；相对Champion 0.5020：约-0.012151；目标0.5100仍未达到。
- 差值仅为目前最佳点对历史参照的比较，不含不确定性、子群伤害、完整收敛或泛化证明。

## 5. Conclusion
- 结论：训练协议被监控误停打断，科学筛选未完成。保留原误停记录，当前状态修正为stopped_unknown。
- 修复只用于cluster/server4显式精确PID模式：从同一实际日志恢复原生full-precision最佳值及初始patience状态；无法核验精度或续训谱系时不执行早停。
- 真实日志回放7项、精确PID6项、公共闭环69项测试通过；未放宽patience、目标或科学门槛。
- 同一实验的epoch26完整CPU恢复校验通过：模型参数严格加载前逐一验证两项完全相同的非持久常量，642项优化器状态和scheduler状态精确一致，Best及未改善8次保留。
- 只有GPU残留及训练锁实际释放且当前租约/代码/检查点校验通过后，才能恢复同一实验；epoch27会重放，不声称中途/RNG或逐位轨迹恢复。

## 6. Crash Info
- 错误类型：监控精度/续训谱系错误，加上尚未解释的GPU上下文与flock残留；不是已证CUDA OOM或新模型失败。
- CPU恢复首轮因未先审计历史常量键失败；第二轮完成状态检查后因numpy float32收据序列化失败；原始失败保留，第三轮通过。
- 冻结epoch4四组参数诊断启动器实际返回BLOCKED、GPU launches0；三条旧ID的六科学门槛仍false。
- 未执行GPU reset、sudo、外部进程扫描或信号；未重复启动训练、生成变体或把同一仪器冒充独立机制。
