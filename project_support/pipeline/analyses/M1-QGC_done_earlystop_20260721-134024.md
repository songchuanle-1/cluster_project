================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M1-QGC | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M1-QGC
  - Config: configs/Quard/qgc/model_base1_quard2_c2f_enc_lite_posA_l1_qgc.yaml
  - Server: server-4 | GPU: 0
  - State: done_earlystop

## 2. Best Metrics
  | Metric | Value | @ Epoch |
  |--------|-------|---------|
  | mIoU   | 0.4939 | ~20     |
  | Acc@50 | 0.503  | —       |
  | spmIOU | 0.447  | —       |

## 3. Convergence Summary
  - Best first reached at: epoch ~20 (0.4939)
  - Subsequent no_improve epochs: 10 (0.4889→0.4891→...→0.4827→0.4857)
  - 收敛形态: warmup 后升至 0.4939, 之后缓慢下降

## 4. Comparison
  - vs champion (Lite=0.5012): γ = −0.0073 (未超越)
  - vs D1-detail (0.5003): γ = −0.0064

## 5. Conclusion
  - 结论: [无效] — 用 query→cluster attention 给 cluster token 加权未带来增益
  - 解释: query 信息注入 context 后性能 ≈ 不加 (0.4939≈A4/0.4941<champion/0.5012)
  - 建议: query→cluster attn 丢弃是正确设计; QGC 方向不继续
================================================================================
