================================================================================
  Motivation Review - cluster_project
  2026-09-12 15:08:30
================================================================================

## 1. Goal

Authoritative `pipeline/goal.json`:

- Metric: `mIoU >= 0.5100` on ScanRefer.
- Required research: diagnose one concrete error, select one lightweight
  structural mechanism, derive its forward/loss and gradients, verify the
  closest primary sources, and preregister matched controls, robustness, and
  efficiency checks.
- Scope: candidate coverage/boundary, same-category discrimination and relation
  binding, and multi-scale evidence duplication. Pooling, selector, readback
  location, and variant-count changes are not the research main line.
- Admission: scientific admission takes priority over queue depth. A candidate
  without a concrete error, exact equations, novelty comparison, degeneration
  analysis, controls, and a rejection rule must not be trained.
- Existing constraints remain active: Phase 1 structural changes only, seed
  1999 for first screening, epochs 50/max_iters 70, FLOPs <= 10G, no N^2
  attention, and all current bans.

Current state: M95-CTF-HCG-CSORT remains champion at
`0.5024607181549072`, 0.0075392818 below target. `check_goal.py` at 15:07
still reports Phase 1 `NOT YET`.

## 2. Story Status

| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Multi-scale context improves the historical baseline | Confirmed historical | M95 .5024607182 vs baseline .4894491136 | Existing platform, not a new mechanism |
| Candidate coverage is the dominant residual | Rejected | 99/111 M95 recoverable failures contain a usable positive | Selection remains unresolved |
| Wrong same-category instance selection is the dominant residual | Supported diagnostically | 105/111 recoverable failures select another physical instance | Generic matching and ranking mechanisms are prior art |
| Candidate score contains mask-specific selection evidence | Rejected | Selection is query-only: `z_q = indis_embedding(u_q)` | A mask-conditioned repair is standard prior art |
| Existing decoder/upstream parameters contain a robust joint direction | Rejected/uncertain | Layer and parameter-group intervals include zero | No measured parameter locus supports admission |
| Multi-scale duplication can be repaired by a new lightweight mechanism | Unsupported | CSORT already targets adjacent-scale token redundancy; the broad family is closed | No fresh measured error or non-equivalent derivation |
| Relation/shared-anchor evidence supplies the missing distinction | Unproven | Parser relation edges are not grounded object truth; the prior fixed-case audit did not confirm applicability | Requires a measured applicable subset and exact derivation |

## 3. Experiment Assessment

| Experiment or audit | Result | Motivation view |
|---------------------|--------|-----------------|
| M95-CTF-HCG-CSORT | .5020 champion; +.0130 over baseline | Historical context platform remains strongest |
| M188-MQB-TR | .4916; -0.0108 vs champion | Terminal-readout successor is closed |
| D1 assignment replay | Usable positive exists in 99/111 recoverable failures | Coverage is not the current blocker |
| D2 competition stratification | Failure rises with same-category distractors | Competition is real, but generic repairs are occupied |
| D1 score, head, layer, and parameter audits | Weak or mixed coupling | No existing parameter direction is a credible mechanism |
| N1 full-text score-field screen | Seven primary sources occupy matching, scoring, ranking, and quality calibration | Broad candidate-specific scoring is closed |
| CSORT historical ablation family | Multi-scale redundancy is already the target of the champion component | Reopening it needs a distinct measured failure, not a renamed loss |

## 4. Gap Analysis

- Verified: a usable target candidate usually exists, and the unresolved
  operation is ordering physically distinct same-category candidates.
- Verified negative: simple masking, calibration, language support, quality,
  projection, early-layer readout, and parameter-alignment mechanisms either
  do not recover the oracle or duplicate established work.
- Missing: an independently measured error signal or an exact non-equivalent
  distinction from established candidate matching, mask scoring, ranking,
  progressive selection, and multi-scale alignment.
- Missing: independent confirmation beyond the repeatedly mined 284
  validation-derived banks.
- Risk: another selector, ranking loss, relation embedding, scale-fusion
  weight, or score calibration would not satisfy the user's scientific scope.

## 5. Design Rationale

Phase 1.5 requires a candidate mechanism to answer a concrete unverified causal
question. Queue depth is 2 waiting versus 5 declared capacity, but no candidate
supplies the required primary-source-distinct causal graph. Creating an
experiment solely to satisfy depth violates the authoritative admission
constraint. Therefore no `exp_design` and no queue entry are created this tick.
FIFO remains M191-MQSD-TR followed by M193-MQHC-TR.

The next admissible work must remain read-only and produce either a new failure
signal with explicit denominators and controls or a derivation exactly
non-equivalent to the closed literature boundary. It may not be a renamed
selector, ranker, relation embedding, scale coefficient, or score calibration.

## 6. Next Batch

No experiment batch. Preserve the existing FIFO and continue bounded Phase 1
diagnostic/derivation work until the scientific admission gate is satisfied.

================================================================================
