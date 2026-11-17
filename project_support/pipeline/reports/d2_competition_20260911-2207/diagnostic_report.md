================================================================================
  D2 Diagnostic - cluster_project
  Does selection failure scale with same-category competition?
  2026-09-11 22:07 tick (tick #20260911-2207)
================================================================================

## 1. Question And Inputs

Goal constraint (2026-09-10) selects ONE main mechanism from measured error.
The frozen D1 audit already reported that most recoverable failures select a
different physical instance. This D2 pass asks the narrower design question
that decides whether a competition/instance-discrimination mechanism is
justified: **does the selection-failure rate depend on how many same-category
distractor instances share the scene?**

Read-only inputs, no model load, no inference, no CUDA, no queue or trainer
change:

    pipeline/reports/d1_instance_20260911-0810/instance_audit.json
    pipeline/reports/d1_calibration_20260911-1815/calibration.json

Reproduce with: `python pipeline/headless/d2_competition_stratify_20260911.py`
Result: `pipeline/reports/d2_competition_20260911-2207/distractor_stratification.json`

Stratum variable: `same_semantic_other_instances` of the selected candidate's
best-matching GT instance. `NA` = the selected mask matched no GT instance, so
its scene-level distractor context is undefined; it is reported separately and
is **not** a distractor bucket.

## 2. Result - Selection Failure vs Same-Category Distractor Count

M95-CTF-HCG-CSORT (champion, 284 banks):

| Same-category others | Banks | Selection failures | Fail rate | Recoverable | Wrong physical instance |
|----------------------|-------|--------------------|-----------|-------------|--------------------------|
| 0                    | 57    | 5                  | 0.088     | 4           | 4 / 4 = 1.000            |
| 1-2                  | 74    | 24                 | 0.324     | 23          | 21 / 23 = 0.913          |
| 3-5                  | 32    | 20                 | 0.625     | 19          | 19 / 19 = 1.000          |
| 6-10                 | 23    | 19                 | 0.826     | 15          | 15 / 15 = 1.000          |
| >10                  | 27    | 21                 | 0.778     | 20          | 20 / 20 = 1.000          |
| NA (unmatched)       | 71    | 37                 | 0.521     | 30          | 26 / 30 = 0.867          |

model_base1 (baseline, 284 banks):

| Same-category others | Banks | Selection failures | Fail rate | Recoverable | Wrong physical instance |
|----------------------|-------|--------------------|-----------|-------------|--------------------------|
| 0                    | 57    | 4                  | 0.070     | 2           | 2 / 2 = 1.000            |
| 1-2                  | 74    | 22                 | 0.297     | 20          | 17 / 20 = 0.850          |
| 3-5                  | 32    | 19                 | 0.594     | 17          | 16 / 17 = 0.941          |
| 6-10                 | 23    | 18                 | 0.783     | 14          | 14 / 14 = 1.000          |
| >10                  | 27    | 21                 | 0.778     | 18          | 18 / 18 = 1.000          |
| NA (unmatched)       | 71    | 29                 | 0.409     | 19          | 18 / 19 = 0.947          |

Reading: selection failure is monotone in same-category competition from 0 to
6-10 distractors (0.088 -> 0.324 -> 0.625 -> 0.826 for M95), and the recoverable
failures in the competitive buckets are almost entirely wrong-physical-instance
(1.000 in the 3-5, 6-10 and >10 buckets). The ceiling at >10 is a saturation
effect, not a reversal: banks there are already ~78% failing.

M95's advantage over baseline comes mostly from the sparse end: at 0 and 1-2
distractors M95 fails 8.8%/32.4% vs baseline 7.0%/29.7% (champion is *slightly
worse*), while at 2-10 distractors the two are within a few points of each
other. So the champion's cluster-context gain is not concentrated in crowded
scenes, and the dominant residual now sits exactly in the crowded regime.

## 3. Result - The Score Margin Is Large, Not A Near-Tie

From the frozen calibration rows (`score_of_selected - score_of_oracle`, M95):

| Stratum     | Banks | Median oracle score rank (of 128) | Median selected-minus-oracle margin |
|-------------|-------|-----------------------------------|-------------------------------------|
| recoverable | 111   | 17                                | 0.546                               |
| success     | 158   | 10                                | 0.095                               |

On recoverable banks the wrong candidate does not beat the oracle by a tie-break
amount; the median margin is 0.546 logits versus 0.095 on success banks. The
oracle is usually inside the top ~15 of 128 but rarely near rank 1.

## 4. Derived Constraint On Any Candidate Mechanism

Within a fixed bank, `argmax` is invariant under any strictly increasing
transform of a per-candidate score:

    argmax_q s_q = argmax_q f(s_q)      for any strictly increasing f

Therefore per-bank standardization, temperature rescaling, min-max or z-score
normalization of the existing `indis` score **provably cannot change which
candidate is selected**. A calibration-only mechanism is dead on arrival. The
measured failure requires a mechanism that changes the score *field*: new
per-candidate evidence, new supervision, or both.

Combined with section 2, the admissible target is now narrow: a mechanism that
produces per-candidate evidence separating a target instance from competing
same-category instances, in scenes with 3+ distractors, where 54 of M95's 111
recoverable failures live and essentially all of them are wrong-instance.

## 5. Limitations

- Descriptive frozen-artifact analysis; it cannot establish causality.
- `NA` is a mixed bucket (29 empty/miss, 34 target_pass50 among M95's 71) and
  is excluded from the distractor trend.
- The distractor count is taken from the selected candidate's matched GT
  instance; when that match is absent the count is undefined.
- Repeated mining of this validation-derived bank set is exploratory, not an
  independent confirmation. No test data was used.

================================================================================
