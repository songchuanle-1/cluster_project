================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M63-PSR | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M63-PSR
  - Config: configs/Quard/psr/model_base1_quard2_c2f_enc_lite_posA_l1_psr.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-06 11:03:23 | Resumed: 2026-08-06 20:09 | Finished: 2026-08-07 06:40
  - Duration: ~19h (首段 11:03→17:59 + resume 段 20:09→06:40; 中间 2h 为外部 fineweb-edu 资源冲突停滞)
  - State: done_earlystop (Early stopping at epoch 24: no improvement for 10 epochs, best=0.4964)
  - Note: M63 = cluster_mode psr (per-scale point-cluster residual readback, message 构造轴补格).
    Resume 自 last.pth (no_impr carried over). 上 tick 处置外部资源冲突后恢复推进, 本 tick 判定终态.

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4964 | 14      |
  | Acc@50   | 0.551  | 14      |
  | spmIOU   | 0.460  | 14      |

## 3. Convergence Summary
  - 本日志窗口可见序列 (resume 后, ep10-24): 0.483→0.493→0.485→0.494→0.496(best@ep14)→
    0.490→0.492→0.494→0.494→0.493→0.492→0.490→0.491→0.487→0.488(ep24)
  - Best first reached at: epoch 14 (mIoU=0.4964, 日志窗口内)
  - 之后 10 个 epoch (15-24) 全部未刷新 best → no_impr 10/10 → epoch 24 触发 early stop
  - 收敛形态: 爬升至 0.496@ep14 后进入 0.490-0.494 平台, 最后 2 个 epoch (0.487/0.488) 回落

## 4. Comparison
  - vs baseline (model_base1, 0.4894): γ = +0.0070 (有效, 高于 baseline)
  - vs champion (posA_l1/DRP, 0.5012): γ = -0.0048 (失败, 未超 champion)
  - vs M60-DET-CSF (0.4973): γ = -0.0009 (持平)
  - vs M62-ORTG (0.4979): γ = -0.0015 (持平)
  - vs M61-SCT (0.4854): γ = +0.0110 (高于同轴 sequential readback)
  - 结论链条: PSR (0.4964) > baseline 但 < champion; 与 detail 组合 M67-PSR-HCG 未跑待验.
    per-scale 残差 message 轴单独有效但未突破, 与同轴 M61-SCT (0.4854) 相比 PSR 明显更优
    (逐尺度残差 > 顺序粗→细), 但与已测 M60/M62 持平在 0.497 平台.

## 5. Conclusion
  - 结论: [失败] — 未超 champion (0.5012), γ=-0.0048; 但高于 baseline (γ=+0.0070)
  - 解释: per-scale point-cluster residual readback 是有效的 message 构造改进 (优于 SCT 0.4854,
    与 DET-CSF/ORTG 持平 0.497 平台), 但单轮 readback 已饱和在 0.496-0.498 区间, 与 champion
    DRP 0.5012 仍有 ~0.004 差距. 说明 message 构造轴 (detail/CSF/PSR) 无法单独突破 champion,
    需要与交付正确性轴 (HCG) 组合.
  - 对后续实验设计的建议: (1) M67-PSR-HCG (3×2 因子矩阵最后一格) 继续按队列跑, 验证 PSR ×
    正确多尺度交付是否有协同; (2) 突破 champion 需依赖 M65-HCG/M66-DET-HCG 的正确多尺度交付
    首测结果; (3) message 构造单轴已耗尽 (detail/CSF/PSR/SCT 四格), 不再单独设计.
================================================================================
