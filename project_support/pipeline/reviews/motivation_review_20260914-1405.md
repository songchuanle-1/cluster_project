================================================================================
  Motivation Review — cluster_project
  2026-09-14 14:05:00
================================================================================

## 1. Goal
  - Goal: develop a lightweight, falsifiable mechanism for concrete ScanRefer
    grounding errors while keeping historical-profile FLOPs <= 10.0G.
  - Target: mIoU >= 0.5100.
  - Exact retained champion: M95-CTF-HCG-CSORT = 0.5024607181549072.
  - Baseline: model_base1 = 0.4894491136074066.
  - Gap to target: 0.0075392818450928.
  - Phase: 1, target not reached.
  - Queue state before this review: active 0 / capacity 4; candidate budget 4.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Multiscale context improves grounding | supported historically | M95 +0.0130 over baseline | not new SCM evidence |
| Current candidate masks contain usable targets but selection is often wrong | supported diagnostically | original 284-expression bank: 111 M95-recoverable cases; 89/111 selected and oracle masks disjoint | mined bank is not independent validation |
| Joint selector-mask spatial supervision can reduce hard-selection errors | unverified, admissible | SCM derives one spatial measure from native selector probabilities and all candidate masks | requires training and hard-selector validation |
| More selector/readback variants will solve the gap | closed | M184-M191 and M193: 0/9 beat M95 | no descendants or renamed variants |

## 3. Experiment Assessment
| Experiment | mIoU | Relation to motivation | Contribution |
|---|---:|---|---|
| model_base1 | 0.489449 | no cluster context | baseline |
| M95-CTF-HCG-CSORT | 0.502461 | retained context and diversity parent | current parent/champion |
| M191-MQSD-TR | 0.491714 | terminal selector/readout branch | negative evidence |
| M193-MQHC-TR | 0.490611 | terminal hierarchy consensus branch | negative evidence |

The completed selector/readout family does not justify more inference modules.
SCM instead changes the training objective while leaving the M95 inference graph
unchanged. It is therefore a distinct causal intervention rather than another
pooling, routing, or readback variant.

## 4. Gap Analysis
  - Observed: M95 has substantial selection regret on a fixed diagnostic bank.
  - Observed: the final hard prediction is chosen by native selector logits, while
    final Dice supervises matched masks separately.
  - Missing: evidence that coupling selector probability and candidate-mask
    spatial mass improves the deployed hard-selected mask.
  - Missing: independent efficacy evidence; diagnostic oracle gains are only an
    upper bound.
  - Novelty boundary: Wasserstein supervision, sliced/projected Wasserstein
    distances, offset-head losses, and mask-quality reranking are prior art.
    The experiment tests their non-equivalent application boundary: native
    selector probabilities and all candidate masks form one predicted spatial
    measure, supervised against target-mask coordinate marginals during training,
    with no new inference head or reranking stage.
  - This boundary supports a controlled experiment, not an exhaustive novelty
    certification or a publication claim.

## 5. Design Rationale
  - SCM directly targets the measured selection bottleneck without oracle
    candidate identity, validation-tuned score weights, or a new inference path.
  - It replaces only final-layer Dice at its inherited weight. Auxiliary Dice,
    BCE, selector CE, semantic, sampling, and CSORT losses remain unchanged.
  - Its causal prediction is falsifiable: hard-selected full-validation grounding
    must improve, not merely the soft mixture or oracle upper bound.
  - A gain below 0.002 after the existing plateau criterion closes the branch.
  - Conditional coordinate-permutation and detached-selector controls are not
    queued now and cannot be used as capacity fillers.

## 6. Next Batch
  - Admit one experiment only: M194-CTF-HCG-CSORT-SCM.
  - Keep the other three capacity slots empty because no other candidate passed
    the current evidence, novelty-boundary, and structural-mechanism gates.
  - See pipeline/designs/exp_design_20260914-1405.md.
================================================================================
