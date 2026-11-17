# M207-HAP 完整状态续训记录

用户已明确授权 HAP 在 GPU0 续训。本操作保持原 f518 版本、原 YAML、seed1999、50epochs/maxiters70、4workers；GPU1 继续留给别人，M206 保持暂停。

固定 epoch18 完整检查点重新核验 SHA、模型、优化器、调度器与 meta 通过；原生训练/数据源、TRAIN 标注与 pretrain 哈希保持，远端源码仅允许原有路径映射，未同步或修改。GPU0 在启动前多次确认空闲、UUID 匹配且三项 flock 可取得。

保留原 crashed 完整归档及 history，以同一 M207 原收据执行一次 canonical full resume。新 PID1063355，原生确认从 epoch19 开始、best_miou0.4975287616252899/noimprove0；额外采样训练步数71→81，物理GPU0 context与固定checkpoint argv匹配。

DataLoader 原故障底因仍未知，此次成功启动不证明已修复。第19轮旧的部分minibatch与完整RNG/worker轨迹未保存，未承诺精确恢复至中断批次。M206队列逐字段保持，无GPU1计算、信号、冷启动、参数/源/环境/调度变更。

完整证据见本目录 operation.json、fresh_runtime_checkpoint_verification.json、checkpoint_evidence.json、dispatch_result.json、native_resume_progress.json；同目录保存原 crashed exp。
