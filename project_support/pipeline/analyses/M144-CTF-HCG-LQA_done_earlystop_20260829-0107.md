================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M144-CTF-HCG-LQA | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M144-CTF-HCG-LQA
  - Config: configs/Quard/ctf_hcg_lqa/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_lqa.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-28 11:09 | Finished: 2026-08-29 01:07 (早停 kill) | Duration: ~14h
  - State: done_earlystop (monitor kill PID=2399815, no_improve=13/10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4930 | ~14     |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (log 验证序列 max=0.4926 @val#14; monitor 台账 Best=0.4930)

## 3. Convergence Summary
  - 验证序列 (20 次): 0.333→0.449(ep5)→0.481(ep10)→0.489(ep11)→0.4926(ep14)→0.485-0.490 平台
  - Best 首刷于验证 #14 (0.4926); 之后 6 次验证无刷新 (0.485-0.490) → 早停
  - 收敛形态: 快速上升至 ep11 ~0.489, ep14 刷顶, 之后平台回落, 与 loss 轴同族形态一致

## 4. Comparison
  - vs baseline (model_base1 = 0.4894): γ = +0.0036 (有效, 但低于 base 机制收益)
  - vs 父模型 ctf_hcg base (M81 = 0.5012): γ = -0.0082 (失败)
  - vs current champion (M95-CTF-HCG-CSORT = 0.5020): γ = -0.0090
  - vs loss 轴同族: M140-CLICA=0.4970 / M141-CSIC=0.4960 / M142-dual=0.4890 /
    M143-OBJG=0.5000 → LQA=0.4930 为 loss 轴第 5 败

## 5. Conclusion
  - 结论: [失败] (相对父模型 ctf_hcg 0.5012 掉 0.0082)
  - 解释: LQA (cluster-token 语言查询语义对齐 aux loss, cluster_lqa_loss 加载
    ctf_hcg base 上) 0.4930 < base 0.5012。直接监督 cluster token 与语言查询
    对齐不能带来增益 — 与 CLICA/CSIC/dual/OBJG 一致。
  - 对后续实验设计的建议: loss 监督轴 5 连败 (CLICA/CSIC/dual/OBJG/LQA 均
    ≤0.5000 < base 0.5012) → **该轴整体关闭**。平台突破只能靠结构机制
    (CSORT 系 M145-150 在队)。OBJG=0.5000 为 loss 轴最佳但仍 < base。

## 6. Crash Info (if crashed)
  - Error type: N/A (早停 kill, 非 crash)
  - Auto-fix attempt: N
================================================================================
