# Motivation Review - cluster_project
2026-09-13 21:10 Asia/Shanghai

## 1. Goal
- Authoritative full goal: ../goal.json, read in full this tick (12 constraints,
  11 bans). Companion goal_snapshot_20260913-2110.json preserves its full content.
- Description: cluster: 面向 ScanRefer 三维语言定位的具体错误，研究有核心新颖性、可推导且可证伪的轻量结构机制，目标 mIoU ≥ 0.51。多尺度 cluster context 是已有研究基础，不再把变更 pooling、selector、回写位置或变体数量当作研究主线。先诊断候选覆盖与边界、同类目标辨别与关系绑定、多尺度证据重复等问题，再依据证据选择一个核心机制；覆盖机制对照、泛化稳健性和效率验证。共享参照物一致性仅为待验证候选，不预设为最终方向。既有 context/routing 结果是历史证据，不等于新机制已获验证。
- Target .51; M95 exact .5024607181549072; gap .0075392818450928.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Existing context benefits seed1999 | historical support | M95 versus baseline | robustness and new mechanism |
| Rest-bank head gradients reverse correcting failure pairs | rejected on captured failures | 0/91, source-head audit | no full-training extrapolation |
| Actual full-loss optimizer step worsens a corrective margin | untested | optimizer state exists | fixed TRAIN manifest and faithful replay |

## 3. Experiment Assessment
| Experiment | mIoU | Motivation relationship | Contribution |
|------------|------|-------------------------|--------------|
| baseline | .4894491136 | reference | no cluster |
| M95 | .5024607182 | historical context foundation | champion, not new mechanism |
| M191 | .4917144179 | old terminal recurrence control | no champion improvement |
| M193 | .4906114340 | old consensus recurrence control | normal stop27; no successor |
Earlier terminal-route outcomes and exclusions are retained in analyses/ and
codex_memory.md; this is a new-result/prerequisite review, not a new full-ledger audit.

## 4. Gap Analysis
Historical checkpoint lacks sampler/RNG/augmentation state. Optimizer availability
does not reconstruct the historical trajectory. Head-only corrections do not
explain retained errors. A train-mode local counterfactual can test a narrower
claim but cannot establish training efficacy, generalization or novelty.

## 5. Design Rationale
Pre-register a fixed-batch diagnostic before inspecting its margins. Restore
parameters, buffers, per-parameter optimizer states and RNG for each arm.
Separate gradient direction, accumulated Adam state and finite-step effects.
No new mechanism, loss coefficient, projection training or validation-driven
batch search. Scientific admission takes priority over queue depth.

## 6. Next Batch
See ../designs/exp_design_20260913-2110.md: DRAFT diagnostic protocol only.
No training variant implemented or enqueued. Next work is manifest and mapping
verification, not execution of a modified training run.
