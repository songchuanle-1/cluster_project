================================================================================
  Motivation Review - cluster_project
  2026-09-12 13:11:12
================================================================================

## 1. Goal

Authoritative `pipeline/goal.json`:

- Metric: `mIoU >= 0.5100` on ScanRefer.
- Required research: one concrete ScanRefer error, one lightweight structural
  mechanism, equation-level forward/loss derivation, primary-source novelty,
  matched controls, robustness, and efficiency.
- Scope constraints: diagnose candidate coverage/boundary, same-category
  discrimination/relation binding, and multi-scale evidence duplication before
  selecting one mechanism.
- Execution priority: scientific admission over queue depth. No successor or
  renamed selector/pooling/readback family may be enqueued without admission.

Current state: M95-CTF-HCG-CSORT is champion at
`0.5024607181549072` from epoch 16; target gap is `0.0075392818450928`.
`check_goal.py` at 13:07 keeps Phase 1 in `NOT YET`.

## 2. Story Status

| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Multi-scale cluster context improves the historical baseline | Confirmed historical | M95 .5024607182 vs baseline .4894491136 | Not a new mechanism claim; seed-fragile |
| Candidate coverage is the dominant remaining error | Rejected | 99/111 M95 recoverable failures contain a usable positive; only 12/111 do not | Does not identify one admissible forward/loss change |
| Same-category candidate competition is the dominant residual | Supported diagnostically | Failure rises from 8.8% at 0 distractors to 82.6% at 6-10; 63/111 recoverable errors are same-coarse-semantic wrong instances | Generic matching/ranking/quality scoring is prior art |
| The M95 score contains candidate-specific evidence | Rejected | Selection is query-only: `z_q=indi_embedding(u_q)`, `m_{q,n}=u_q dot f_n` | A new score field must be primary-source-distinct |
| Existing decoder or upstream parameters contain a joint selection-mask direction | Rejected/uncertain | Layer and parameter-group cosine intervals include zero | No robust parameter locus to target |
| Language, semantic-projection, or quality evidence fixes selection | Rejected on frozen banks | Real-language and shuffled controls do not outperform the deployed score reliably | No current language-support mechanism |
| A non-generic relation/shared-anchor mechanism applies | Unproven | The bounded 21-case audit did not establish enough applicable cases | Requires a new measured error before design |

## 3. Experiment Assessment

| Experiment or audit | Result | Motivation View |
|---------------------|--------|-----------------|
| M95-CTF-HCG-CSORT | .5020 champion; +.0130 over baseline | Historical context platform remains strongest |
| M188-CTF-HCG-CSORT-MQB-TR | .4916; -0.0108 vs champion | Terminal-readout successor closed |
| D1 assignment replay | 99/111 recoverable failures retain usable positives | Coverage is not the dominant bottleneck |
| D1/D2 competition | Most recoverable errors are wrong physical instances; failure grows with distractors | Candidate discrimination is real, but generic ranking/scoring is occupied |
| D1 language/quality/projection | Reranking and shuffled controls fail to establish unique evidence | Language-support family closed |
| D1 decoder/upstream coupling | Weak, mixed cosine directions; all paired intervals include zero | No admitted parameter-alignment mechanism |
| N1 full-text boundary | InstanceRefer, LanguageRefer, HAM, 3D-SPS, TransRefer3D, Mask Scoring R-CNN, and Rank & Sort Loss occupy the broad score-field class | No candidate-specific score-field entry |

## 4. Gap Analysis

- Verified: usable target proposals usually exist; the unresolved operation is
  ordering physically distinct same-category candidates.
- Verified negative: simple calibration cannot change `argmax`, and generic
  candidate matching, quality scoring, classification, and ranking are prior art.
- Missing: a newly measured error or an exact non-equivalent distinction from
  those primary sources, with symbols, supervision, gradients, degeneracies,
  complexity, matched controls, and a preregistered rejection condition.
- Missing: independent evaluation of the exact M95 archive. Existing diagnostics
  mine the same 284 validation-derived banks and are exploratory.
- Risk: naming another selector, competition loss, relation embedding, or
  mask-conditioned score would be a prior-art restatement, not a new mechanism.

## 5. Design Rationale

Phase 1.5 asks which unverified causal hypothesis the next batch would test.
No current candidate supplies a primary-source-distinct causal graph that also
addresses a newly measured error. The broad score-field route was closed at
12:13 after full-text review, and no later terminal result creates a new error
signal. Therefore:

- No `exp_design` or training entry is admitted this tick.
- FIFO remains M191-MQSD-TR followed by M193-MQHC-TR.
- Queue depth remains under target, but scientific admission takes precedence.
- The next admissible work must be a bounded diagnostic that discovers a new
  failure relation or an exact theoretical distinction, not a renamed scorer.

## 6. Next Batch

No experiment batch. Continue Phase 1 read-only diagnostic or derivation work.
Do not mutate the queue until a mechanism passes all `goal.json` admission
requirements.

================================================================================
