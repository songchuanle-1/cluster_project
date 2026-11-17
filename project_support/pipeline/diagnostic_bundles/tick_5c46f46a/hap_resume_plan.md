# M207-HAP 完整状态恢复方案

- 当前状态：原运行因 DataLoader 转换异常退出，底因仍未知；恢复尚未授权或启动。
- 只使用 server4 physical GPU0，等待真实空卡并复核 UUID、独占租约、环境、数据及源码。GPU1 继续让给别人，M206 保持暂停。
- 保持已测 f51823bbddf0f8095a9a5813bf1f8169e3d7edb0 与原 YAML、seed1999、50epochs/maxiters70、4workers 不变。
- 使用已冻结且 CPU 校验的 last.pth：meta.epoch18，best_miou0.4975287616252899，no_improve0，模型/优化器642states5groups/调度器均在。下一轮为19。
- 不包含第19轮未完成的minibatch进度，也不含完整RNG/loader状态，不能保证原中断点的精确随机轨迹。
- 新CPU进程1000次及4个持久worker合成2000样本通过；这不证明原生故障已排除。不得据此改训练参数或宣称机制失败。
- 原生恢复入口 cluster_resume.validate 强制本次hash绑定的人工恢复授权；现有实验优先授权保留恢复限制。本方案未创建授权、未入队、未启动。

固定检查点与校验摘要、完整原生参数见同目录 hap_resume_plan.json。
