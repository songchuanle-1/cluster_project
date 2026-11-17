================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M118-CTF-HCG-LCC | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M118-CTF-HCG-LCC
  - Config: configs/Quard/ctf_hcg_lcc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_lcc.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-22 03:13:09 | Finished: 2026-08-22 16:08:46 (monitor early-stop kill) | Duration: ~13h
  - State: done_earlystop (no_improve=11/10, killed at ep23/50)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4950 | ~12-13  |
  | Acc@50   | 0.549  | ~12-13  |
  | spmIOU   | 0.459  | ~12-13  |
  (source: remote log train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_lcc_20260822_031309.log)

## 3. Convergence Summary
  - Best first reached at: epoch ~12-13 (0.4950)
  - Subsequent no_improve epochs: 11/10 → early-stopped at ep23
  - Final epochs best: mIoU=0.4950, recent 5 validations: 0.4550, 0.4910, 0.4550, 0.4850, 0.4490 (震荡下行，未再刷新 best)
  - 收敛形态: 快速上升至 ep~13 后平台震荡，之后持续下滑

## 4. Comparison
  - vs baseline (model_base1): γ = +0.0056 (有效，超过 +0.002 阈值，但幅度小)
  - vs champion (M95-CTF-HCG-CSORT 0.5020): γ = -0.0070 (未破顶)
  - vs 同系 M119-CTF-HCG-MFP (running, 当前 0.5020): LCC 低 0.0070 — MFP 明显更优
  - vs M65-HCG (0.5002): LCC 低 0.0052 — 语言条件化未带来增益

## 5. Conclusion
  - 结论: [有效] 但弱 — Language-Conditioned Cluster Context 相对 baseline 有 +0.0056 增益，但距 champion 0.5020 差 -0.0070，未突破。
  - 解释: 在 cluster context 构造中加入语言条件（LCC）提升有限；对比同批的 MFP (masked feature prediction, 0.5020 running)，语言条件化不是破顶方向。
  - 对后续实验设计的建议: 放弃 LCC 方向的进一步扩展。优先关注 MFP（当前 0.5020 与 champion 持平，仍在运行）与 DCA/DCM 系列（M123-M128 waiting，decoder 直接访问 cluster token）。该结果与 goal.json 动机一致：context 机制有效但需更强的信息交互路径，而非语言调制。
================================================================================
