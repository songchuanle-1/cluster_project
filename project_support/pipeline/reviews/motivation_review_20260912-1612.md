================================================================================
  Motivation Review - cluster_project
  2026-09-12 16:12:06
================================================================================

## 1. Goal

Authoritative source: `pipeline/goal.json`.

- Metric: ScanRefer `mIoU >= 0.5100`.
- Research goal: diagnose a concrete error, select one lightweight structural
  mechanism with a causal derivation, verify primary-source novelty, and include
  matched controls, robustness, and efficiency evidence.
- Scope: candidate coverage/boundary, same-category discrimination and relation
  binding, and multi-scale evidence duplication. Pooling, selector, readback
  location, and variant-count changes are not the research main line.
- Admission: scientific admission takes priority over queue depth. No mechanism
  without exact variables, forward/loss derivation, gradients, degeneracies,
  novelty comparison, matched controls, and a preregistered rejection rule may
  be trained.
- Active limits: Phase 1 structural changes only; seed 1999 first screen;
  epochs 50/max_iters 70; <=10G; no N^2 attention; all existing bans remain.

Current state: M95-CTF-HCG-CSORT remains champion at
`0.5024607181549072`, target gap `0.0075392818`. `check_goal.py` at 16:07
reports Phase 1 `NOT YET`. Queue depth is 2 waiting versus 5 declared capacity.

## 2. Story Status

| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Multi-scale context improves the historical baseline | Confirmed historical | M95 .5024607182 vs baseline .4894491136 | Existing platform, not a new mechanism |
| Candidate coverage is the dominant residual | Rejected | 99/111 M95 recoverable failures contain a usable positive | Selection remains unresolved |
| Wrong same-category instance selection is the dominant residual | Supported diagnostically | Failure increases with same-category distractors | Generic matching/ranking repairs are prior art |
| True selection field consumes candidate mask evidence | Rejected | `z_q = indi_embedding(u_q)` is query-only | A simple mask-conditioned head is standard prior art |
| Decoder/upstream parameters contain a robust joint direction | Rejected/uncertain | Layer and parameter-group intervals include zero | No measured parameter locus supports admission |
| Narrow shared-anchor binding explains fixed errors | Rejected on fixed cases | 0/21 readings confirm the required same-anchor predicate pair | Shared-anchor mechanism is not applicable |
| CSORT can be extended by a new redundancy mechanism | Unsupported | CSORT already targets adjacent-scale token redundancy | Requires a distinct measured failure |

## 3. Experiment Assessment

| Experiment or audit | Result | Motivation view |
|---|---|---|
| M95-CTF-HCG-CSORT | .5020 champion; +.0130 over baseline | Historical context platform remains strongest |
| M188-MQB-TR | .4916; -0.0108 vs champion | Terminal-readout successor is closed |
| D1 assignment replay | 99/111 recoverable failures retain usable positives | Coverage is not the dominant blocker |
| D2 competition stratification | Failures rise with same-category distractors | Competition is real; generic repairs are occupied |
| D1 margin/calibration/head/layer/parameter audits | Corrective local directions exist, but coupling is weak/mixed | No admissible parameter-locus mechanism |
| N1 full-text score-field screen | Matching, scoring, ranking, and quality calibration are established | Broad candidate-specific scoring is closed |
| D1 fixed case-scope coupling | 12/12 M95 errors recoverable and corrective; 0/21 shared-anchor | Shared-anchor path closed as inapplicable |

## 4. Gap Analysis

- Verified: usable target candidates usually exist, but their query-only
  selection scores are below wrong same-category candidates.
- Verified negative: missing positives, missing local corrective direction,
  simple shared-anchor binding, mask-conditioned scoring, quality calibration,
  language support, and decoder/upstream parameter coupling do not supply an
  admissible new mechanism.
- Missing: an independently measured error that is exactly non-equivalent to
  established candidate matching, mask scoring, ranking, progressive selection,
  and relation modeling.
- Missing: independent confirmation beyond the repeatedly mined 284
  validation-derived banks.
- Risk: another selector, ranking loss, relation embedding, score calibration,
  or feature-alignment variant would be a renamed closed direction.

## 5. Design Rationale

The fixed relation/attribute cases were tested because prior work proposed a
narrow shared-anchor consistency mechanism. The new bounded audit found that
none of the 21 readings satisfies that mechanism's applicability rule. All 12
fixed M95 errors already have a usable positive and a corrective local score
margin, and seven have only one relation or unary/comparison evidence. The
observed discrepancy is therefore broader than shared-anchor binding.

Queue depth does not override the admission gate. No candidate has an exact
forward/loss graph, primary-source-distinct claim, matched control, and
preregistered rejection condition. Creating an experiment solely to satisfy
depth would violate `goal.json`.

## 6. Next Batch

No experiment batch and no `exp_design` this tick. Admit no mechanism, preserve
FIFO M191-MQSD-TR then M193-MQHC-TR, and continue read-only diagnostic or
derivation work until the scientific admission gate is satisfied.

================================================================================
