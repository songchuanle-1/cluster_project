================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M61-SCT | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M61-SCT
  - Config: configs/Quard/sct/model_base1_quard2_c2f_enc_lite_posA_l1_sct.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-05 17:03:30 | Finished: 2026-08-06 10:32:18 | Duration: ~17.5h
  - State: done_earlystop (远端日志 "Early stopping at epoch 28: no improvement for 10
    epochs (best=0.4854)", 训练脚本自身早停退出)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4854 | 28/50   |
  | Acc@50   | 0.533  | 28/50   |
  | spmIOU   | 0.442  | 28/50   |

## 3. Convergence Summary
  - Best first reached at: 早于/≤ep18 (死亡观察期 best 已 0.4854, 后 10 ep 无刷新)
  - Subsequent no_improve epochs: 10/10 (ep28 触发 patience=10 早停)
  - 收敛形态: 前期缓升到 0.4854 后进入平台, 后期验证序列持续下滑
    (近期 0.4832/0.4824/0.4812/0.4793/0.4762), 从未逼近 champion 0.5012

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = -0.0040 (失败, 低于 baseline)
  - vs current champion (DRP/posA_l1 0.5012): γ = -0.0158
  - vs CTF (M41 0.4995, 指向 readback/融合机制): γ = -0.0141
  - 顺序依赖 readback (粗→细两阶段) 在本项目中显著差于并行逐尺度 gate 融合

## 5. Conclusion
  - 结论: [失败]
  - 解释: 顺序 readback (阶段1注入粗尺度 context → 阶段2细/中尺度融合权重条件于
    粗注入后特征) 的粗→细顺序信息流依赖, 在残缺交付 + 本项目结构下无益 — 0.4854
    远低于 champion 的并行 per-point gate (0.5012)。细尺度的融合权重不应条件于粗尺度
    已注入 context; 并行独立 gate 更优。
  - 对后续实验设计的建议: readback 的"顺序依赖"子维度就此闭合。剩余 readback 补格
    (M64-SSP 投影放置 / M65-HCG 正确多尺度交付 / M66-DET-HCG / M67-PSR-HCG) 继续排队。
    SCT 的失败也反向印证: champion 的并行多尺度 gate 融合是一个稳健设计, 破 0.5012
    的关键不在融合权重顺序, 而在"正确多尺度交付"(HCG) 或 "message 内容"(detail/PSR)。

## 6. Crash Info (if crashed)
  - 无 crash — 训练脚本正常 early-stop (ep28 best=0.4854)。进程消失由 monitor deathwatch
    捕捉, 日志确认早停, 语义等价 done_earlystop。server-4 gpu1 槽已由 M63-PSR 复用
    (11:03 推送)。
================================================================================
