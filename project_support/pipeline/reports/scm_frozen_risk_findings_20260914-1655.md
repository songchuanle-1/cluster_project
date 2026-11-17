# SCM Frozen Output Risk
2026-09-14 16:56. CPU-only; no model/inference/training invocation.

## Scope And Checks
Frozen Sep12 M95 outputs284 expressions/71scenes;109recoverable,145success,
30limited. All artifacts verified against capture summary hashes; raw scene
hashes recorded. Saved SP mapping equals raw point inverse mapping; no padding,
missing targets, nonfinite masks/scores or missing data. Selected/oracle indices
recomputed from saved logits with ties recorded. This is NOT M194 outputs.
Raw coordinates recovered by SP means, not historical TRAIN augmentation.
Finite-difference and query permutation checks passed for all284 banks;
maximum error5.483543159374657e-11.

## Results
| Stratum | Banks / scenes | SCM pair correcting | Pair adverse | Same query |
|---|---|---|---|---|
| recoverable |109/58|95|14|0|
| success |145/63|82|35|28|
| limited |30/24|18|11|1|

Pair velocity is the selector-logit gradient-descent direction of selected
minus oracle logit margin. Adverse does NOT mean the hard-selected mask changed.
The oracle is diagnostic, never deployed. Ties use first argmax.

Recoverable adverse fraction14/109=.12844, scene-bootstrap95% interval
[.0700,.19231],10000 draws,seed1999. Individual selected-mask transport is
smaller than oracle transport in5/109; this different denominator-of-events
is expected because mixture gradients depend on all candidates.

Selector-only expected-hard-IoU derivative decreases in2/109 recoverables,
10/145 successes and1/30limited. This expectation can improve even when the
selected-versus-oracle margin worsens: probability can shift to other good
candidates. Neither quantity is a guarantee about hard argmax improvement.
Success-pair adverse directions are not automatically new failed groundings.

## Interpretation
The synthetic risk occurs on real parent outputs but is not the majority pair
direction on recoverable failures. Keep M194 at its existing schedule/patience.
No coefficient change, new corrective variant, premature stop or efficacy claim.
Full-loss/network Jacobians/Adam/mask updates are excluded. Historical mined
validation and selected checkpoint create selection bias; intervals describe
this reused bank, not independent population prevalence.

## Artifacts
- scm_frozen_risk_20260914-1655.json:284 identity rows, all scene/bank hashes,
  group counts, bootstrap intervals, pair velocities, individual costs, ties.
- scm_frozen_risk_20260914.py:worker SHA
  b0468218169a3af38b0916c1cc8e94845c2023d4c845b170d8bb7a8b8b941aae.
- scm_math_check_20260914.py:reference SHA
  3527fc25bad437b5d53ee32a14d3caf48502731151003ddfbdcfb900aa2f5852.
- Decision20260914-165632_other. No production files changed.
