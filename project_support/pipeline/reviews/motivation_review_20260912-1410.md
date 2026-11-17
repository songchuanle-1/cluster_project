================================================================================
  Motivation Review - cluster_project
  2026-09-12 14:10:55
================================================================================

## 1. Goal

Authoritative `pipeline/goal.json`:

- Metric: `mIoU >= 0.5100` on ScanRefer.
- Required research: diagnose one concrete error, select one lightweight
  structural mechanism, derive its forward/loss and gradients, verify the
  closest primary sources, and preregister matched controls, robustness, and
  efficiency checks.
- Scope: candidate coverage/boundary, same-category discrimination and relation
  binding, and multi-scale evidence duplication. Do not use pooling, selector,
  readback-location, or variant-count changes as the research main line.
- Admission: scientific admission takes priority over queue depth. No
  successor family is admitted without a concrete error, exact equations,
  novelty comparison, degeneration analysis, controls, and a rejection rule.
- Existing constraints: Phase 1 structural changes only, seed 1999 for first
  screening, epochs 50/max_iters 70, FLOPs <= 10G, no N^2 attention, and all
  existing bans remain active.

Current state: M95-CTF-HCG-CSORT is champion at
`0.5024607181549072` from epoch 16, `0.0075392818450928` below target.
`check_goal.py` at 14:07 remains Phase 1 `NOT YET`.

## 2. Story Status

| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Multi-scale context improves the historical baseline | Confirmed historical | M95 .5024607182 vs baseline .4894491136 | Not a new mechanism; seed-fragile |
| Candidate coverage is the dominant remaining error | Rejected | 99/111 M95 recoverable failures contain a usable positive | Does not identify an admissible structural change |
| Same-category wrong-instance selection is the dominant residual | Supported diagnostically | 105/111 recoverable failures select another physical instance; failure rises to 82.6% at 6-10 distractors | Generic matching, scoring, ranking, and quality calibration are prior art |
| The M95 selection score contains candidate-mask evidence | Rejected | `z_q=indis_embedding(u_q)`; selection ignores mask features | A mask-conditioned score is not primary-source-distinct |
| Existing decoder/upstream parameters contain a robust selection-mask direction | Rejected/uncertain | Layer and parameter-group alignment intervals include zero | No measured parameter locus supports a new mechanism |
| Language/support/quality reranking fixes selection | Rejected on frozen banks | Real-language and shuffled controls do not reliably outperform `indis` | No surviving frozen-score mechanism |
| A narrow relation/shared-anchor mechanism applies | Unproven | Parser relation edges occur, but they are not grounded object truth; the prior fixed-case audit did not confirm the narrow condition | Requires an exact measured error and a non-equivalent derivation before design |

## 3. Experiment Assessment

| Experiment or audit | Result | Motivation view |
|---------------------|--------|-----------------|
| M95-CTF-HCG-CSORT | .5020 champion; +.0130 over baseline | Historical context platform remains strongest |
| M188-MQB-TR | .4916; -0.0108 vs champion | Terminal-readout successor is closed |
| D1 assignment replay | 99/111 recoverable failures retain a usable positive | Candidate coverage is not the dominant bottleneck |
| D2 competition stratification | Failures increase with same-category distractors | Competition is real, but the generic mechanism class is occupied |
| D1 score/head/parameter coupling | Weak or mixed alignment on all audited loci | No existing parameter direction is a credible mechanism |
| N1 full-text score-field screen | Seven primary sources occupy generic candidate matching, mask-quality scoring, ranking, and selection | Broad candidate-specific scoring is closed |

## 4. Gap Analysis

- Verified: a usable target mask usually exists, and the unresolved operation is
  ordering physically distinct same-category candidates.
- Verified negative: per-bank monotone calibration cannot change `argmax`;
  simple language, support, quality, projection, and mask-conditioned readouts
  fail the available controls.
- Missing: a newly measured error or an exact non-equivalent distinction from
  InstanceRefer, LanguageRefer, HAM, 3D-SPS, TransRefer3D, Mask Scoring R-CNN,
  and Rank & Sort Loss.
- Missing: independent confirmation beyond the repeatedly mined 284
  validation-derived banks.
- Risk: another selector, competition loss, relation embedding, or score head
  would restate established work rather than provide the requested core
  contribution.

## 5. Design Rationale

Phase 1.5 requires a candidate mechanism to answer a concrete unverified causal
question. The current queue deficit is 2 waiting versus 5 declared slots, but
no candidate supplies the required primary-source-distinct causal graph.
Creating an experiment solely to satisfy depth would violate the authoritative
admission constraint. Therefore no `exp_design` and no queue entry are created
this tick. FIFO remains M191-MQSD-TR followed by M193-MQHC-TR.

The next admissible work must be read-only and must produce either a new failure
signal with explicit denominators and controls or a derivation that is exactly
non-equivalent to the closed literature boundary. It may not be a renamed
selector, ranker, relation embedding, or score calibration.

## 6. Next Batch

No experiment batch. Preserve the existing FIFO and continue bounded Phase 1
diagnostic/derivation work until the scientific admission gate is satisfied.

================================================================================
