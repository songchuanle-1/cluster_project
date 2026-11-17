# Motivation Review - Scene-Level Uncertainty For The Corrected Selection Metric
2026-09-16 11:45 Asia/Shanghai. Statistical control; nothing admitted.

## 1. Goal
pipeline/goal.json authoritative: 14 constraints, 11 bans, target mIoU >= .51.
Ledger champion M95 .5020; exact .5024607181549072@16; Phase 1 NOT YET.

## 2. Why This
The 111052 audit requires same-class controls with scene-level uncertainty because
expressions repeat scenes and per-expression counts are not independent samples. The
corrected selection metrics from 1121 were pooled over expressions only. This adds the
scene-balanced and scene-bootstrap figures, using the same single same-forward
capture and no cross-capture joins.

## 3. Dependency Structure
123 expressions over 32 scenes: 30 scenes contribute 4 expressions, one contributes
2, one contributes 1. Pooled per-expression rates therefore over-weight the 30
four-expression scenes. Scene-level bootstrap resamples SCENES with replacement
(10000 draws, seed1999).

## 4. Result
| Metric | pooled | scene-balanced | scene bootstrap 95% CI |
|---|---|---|---|
| selection success | 69.1% | 68.75% | [57.8%, 78.9%] |
| expression has >=1 acceptable mask | 95.9% | 96.1% | [93.0%, 99.2%] |
| best acceptable rank in top-5 | 83.9% | 83.9% | [76.0%, 91.1%] |
| selected a wrong query although an acceptable one exists | 26.8% | 27.3% | [18.0%, 37.5%] |
| scenes with no acceptable mask anywhere | 0 of 32 | - | - |

## 5. Interpretation
The corrected findings survive scene clustering. The existence of an acceptable mask
is 96.1% scene-balanced with a CI that stays above 93%: this is not an artifact of
repeated scenes. The discrimination defect - the deployed score selecting an
unacceptable query when an acceptable one exists - is 27.3% scene-balanced with CI
[18.0%, 37.5%], i.e. a robust, non-trivial effect rather than a handful of scenes.

A sharper structural fact: **zero of 32 scenes lack an acceptable mask anywhere.**
All five expressions with no acceptable query sit in scenes that do have acceptable
masks for other expressions. So the mask-limited stratum is expression-specific, not
scene-specific, and cannot be explained by a scene the model simply cannot segment.

## 6. What This Does Not Change
It does not open a new mechanism. The candidate classes remain as listed in
design_20260916-1135: measured-to-fail readouts, decision-inert multi-scale changes,
prior-art mask-aware matching, prior-art modality fusion, and the closed 2D identity
lead. This work hardens the evidence base and satisfies an explicit audit requirement;
it is not an efficacy result.

## 7. Next Batch
-> see pipeline/designs/exp_design_20260916-1145.md
Status: STATISTICAL CONTROL COMPLETE / NO CANDIDATE ADMITTED.
