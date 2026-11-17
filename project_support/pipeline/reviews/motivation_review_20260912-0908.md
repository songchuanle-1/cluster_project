================================================================================
  Motivation Review - cluster_project
  2026-09-12 09:08:38
================================================================================

## 1. Goal

Authoritative source: `pipeline/goal.json`.

- Target: mIoU >= 0.5100 on ScanRefer.
- Baseline: `model_base1` 0.4894; champion: M95-CTF-HCG-CSORT 0.5020;
  gap: +0.0080.
- Phase 1 remains active; Phase 2 is not reached.
- Scientific admission takes priority over queue depth. The waiting FIFO
  remains M191 then M193, and no same-family successor is generated.

## 2. Story Status

| Hypothesis | Status | Evidence | Remaining gap |
|---|---|---|---|
| Candidate coverage is the dominant error | rejected | 99/111 M95 recoverable banks retain a usable positive | Selection among competing instances |
| Selection and mask quality already share a useful local parameter direction | rejected | final-head, last-decoder-layer, and all decoder layers show weak/mixed cosine | Encoder and backbone parameters remain unmeasured |
| A simple mask-conditioned score is novel | rejected | Mask Scoring R-CNN and standard detection reranking subsume it | A new score field or objective is still missing |
| Same-category competition drives the residual | supported descriptively | M95 failure rises from 0.088 at zero distractors to 0.826 at 6-10 | No causal mechanism or admitted intervention |

The remaining measured question for this tick is narrow: if decoder-layer
parameters do not align oracle-selection and oracle-mask gradients, do the
shared text encoder, 3D backbone, scene encoder, and decoder-common parameters
provide such a direction instead? A positive result would identify the only
remaining upstream locus for a non-standard alignment mechanism. A negative
result closes that hypothesis without claiming what a future mechanism must
be.

## 3. Experiment Assessment

| Experiment or audit | Result | Motivation relation | Contribution |
|---|---|---|---|
| D1 expansion | 109 M95 recoverable banks | Candidate-selection problem | Frozen diagnostic denominator |
| Assignment replay | 99/111 recoverables retain usable positives | Rejects missing-positive explanation | Focus on score formation |
| Local head coupling | mean cosine .0148 selected-to-oracle | Rejects local joint direction | Head-only result |
| Final decoder layer | mean cosine .00796 on recoverables | Rejects one-layer upstream repair | Shared upstream still unmeasured |
| Multilayer decoder audit | layer means .01925 to .00796 | Rejects decoder-layer conflict | Encoder/backbone still unmeasured |

## 4. Gap Analysis

The earlier audits isolate decoder-layer parameters. They do not measure
whether the text-conditioned backbone and encoder contain a parameter
direction that simultaneously improves oracle selection and the oracle mask.
Without that measurement, the claim that the existing model simply lacks a
joint selection-mask signal remains incomplete.

The audit must not treat a positive cosine as novelty. Parameter alignment is
an optimization diagnostic. Any later mechanism still needs a new forward or
loss derivation, primary-source distinction, matched controls, and resource
admission.

## 5. Design Rationale

For the frozen M95 checkpoint, selection loss is the sum of per-decoder-layer
cross-entropy losses targeting the oracle candidate. Mask loss is the sum of
per-layer BCE+Dice losses on the oracle mask. For a parameter group G, the
audit measures

    cos(grad_G L_sel, grad_G L_mask)

on all 284 fixed banks and reports recoverable and success subsets plus each
group's gradient norms. Groups are defined by top-level model parameter
namespaces, which exposes the text encoder, backbone, scene encoder,
decoder-common parameters, and decoder layers without changing the graph.

Rejection condition: if recoverable-bank means are weak or mixed across all
upstream groups and success controls are similar, no joint upstream direction
is admitted. No mechanism, config, model package, queue entry, or checkpoint
change follows from the audit.

## 6. Next Batch

See `pipeline/designs/exp_design_20260912-0908.md`. This is a bounded
read-only diagnostic only. It does not satisfy primary-source novelty,
matched intervention, robustness, or efficiency requirements for a training
experiment.
================================================================================
