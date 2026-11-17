# CPU 诊断对照局部修订预注册

- 同一稳定候选：m95-hierarchical-mask-feature-path-audit。
- 初次控制失败：masked_mean_padding_control_delta=1.1920928955078125e-6，大于原1e-6；其余读数和原始cpu_attempt.json全部保留。
- 范围：诊断对照实现，不是原模型修复或核心机制被证伪。向量化 masked sum 在补零后改变归约长度，不能作为严格同序归约对照。
- 唯一修订：在内存克隆的同一global_mean表达式中先按mask取有效行，再原顺序求mean；不改变原生产代码/模型权重/fixture/seed/阈值。
- 预测：有效行相同，隔离对照的有效行均值与输出应在原1e-6内保持；原实现的padding差异必须原样报告。
- 不进行阈值、精度、seed或样本搜索。再次失败则保留FAIL，继续诊断而非标记PASS。
