================================================================================
  Motivation Review - cluster_project
  2026-09-11T18:18:00+08:00
================================================================================

## 1. Goal

Authoritative source: `pipeline/goal.json`.

- Target: mIoU >= 0.5100 on ScanRefer.
- Baseline: `model_base1` 0.4894; champion: M95 0.5020; gap: +0.0080.
- Phase 1 remains active. Phase 2 is not reached.
- The next mechanism must address a measured ScanRefer error, have a
  stepwise forward/loss derivation, distinguish itself from verified primary
  work, and include matched controls, robustness, and efficiency.
- Scientific admission takes priority over queue refill. Existing waiting
  `M189/M190/M191/M193` remain untouched in their original FIFO.

## 2. Story Status

| Hypothesis | Status | Evidence | Remaining gap |
|---|---|---|---|
| Candidate generation is the main M95 bottleneck | rejected as dominant | 15/126 failures have no >.5-IoU candidate; 111 are recoverable | Recoverable banks still need a selection explanation |
| Missing positive supervision explains recoverable selection errors | rejected as dominant | 99/111 recoverable banks have a usable positive; 97 selected negative | Objective-level signals do not imply effective parameter updates |
| The saved `indis` score is poorly calibrated with candidate IoU in failures | measured | On recoverable banks, top-5 oracle recall is 16/90 baseline and 14/111 M95; Spearman is .1137/.1723 versus .4087/.5143 on successes | Descriptive only; no causal claim |
| Simple mask-area evidence repairs selection | rejected for the tested proxy | Binary-area top5 has 5/90 and 8/111 oracle hits; equal rank fusion has 3/90 and 0/111 | A learned language-mask evidence term remains untested |
| Validation indexing selects the wrong decoder layer | rejected | `out['masks']` and `out['indis']` are final-layer batch tensors; earlier layers are in `aux_outputs` | No source change or rerun needed |
| Head sharing is the core missing mechanism | rejected | Baseline tied-head and M95 independent-head contracts are verified implementation facts; parameter tying is standard | No novelty or causal claim |

## 3. Experiment Assessment

| Experiment or audit | Result | Motivation relation | Contribution |
|---|---|---|---|
| D1 expansion | 568 paired banks, 71 physical scenes | Candidate/oracle decomposition | Diagnostic foundation |
| Instance/identity audits | 105/111 M95 recoverable failures select a different physical instance | Localizes the dominant failure inside selection | Supports candidate competition as the next question |
| Ordering/margin audits | Positive candidates are often present and receive opposing independent signals | Rules out a simple missing-target explanation | Still does not measure the real parameter trajectory |
| Head ownership audit | Baseline ties six head modules; M95 uses six independent modules | Closes the implementation-contract question | Standard chain-rule coupling; no mechanism admitted |
| D1 score calibration | Score/IoU rank agreement collapses on recoverable banks | Directly measures whether the selection score tracks mask quality | New testable gap, but not a mechanism |
| Evaluator indexing check | Final-layer tensors are indexed by batch correctly | Removes a suspected evaluator defect | No invalidated diagnostic result |

## 4. Gap Analysis

The measured problem is candidate competition, not candidate presence. The
current selection score is a classifier logit `p_q = softmax(indis_q)[1]`. It
can rank the correct candidate outside the top five even when a >.5-IoU
candidate exists. This separates "which candidate is correct?" from "does the
candidate's predicted support contain the evidence named by the language?".

The missing scientific object is a single structural mechanism that makes that
distinction without using the GT mask, anchors, test labels, or extra
annotation. Mask area alone is not enough. A simple score fusion is not enough.
Any next mechanism must explain why its evidence term carries information not
already present in the classifier score.

## 5. Design Rationale

The candidate under review is language-mask evidence calibration (LMEC). Let
`m_qn = sigmoid(mask_logits[q,n])`, let `f_n` be the scene feature at point n,
and let `l` be the sentence representation. Define normalized positive and
complement support features:

    v_q^+ = sum_n m_qn f_n / (sum_n m_qn + eps)
    v_q^- = sum_n (1 - m_qn) f_n / (sum_n (1 - m_qn) + eps)

and the support evidence contrast

    e_q = g(v_q^+, l) - g(v_q^-, l).

The candidate score is the log-odds composition

    s_q = u_q + lambda e_q,

where `u_q` is the existing unary classifier logit. This is only a candidate:
the independence assumption behind log-odds addition and the novelty of the
specific support contrast are unverified. It must not be implemented or
enqueued before the primary-source and gradient review.

The diagnostic rejection condition is explicit: if a matched random or
language-shuffled evidence control produces the same ranking gain, the
mechanism is rejected. If mask area or score fusion already recovers the
oracle, the evidence term is unnecessary.

## 6. Next Batch

See `pipeline/designs/exp_design_20260911-1818.md`. The immediate work is
CPU/web-only N1 and T0: verify closest primary sources, derive the forward and
loss graph, check degeneracies, and specify matched controls. No training
config, checkpoint write, model package, queue mutation, or GPU allocation is
authorized by this review.

================================================================================
