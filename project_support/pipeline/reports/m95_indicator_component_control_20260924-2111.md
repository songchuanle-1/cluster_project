# M95 indicator component control (offline)

Time: 2026-09-24 21:11 Asia/Shanghai. Source: M95 `loss.py` SHA256
`c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5`.

The frozen score-control wrapper now computes the native indicator
cross-entropy from the same optional frozen query probabilities used by the
score MSE. It reproduces the matched-positive set, the `eos_coef=0.1`
no-object weight, and the per-query
`log(1 + 1e-6)` entropy constant from `loss_indi`. No probability or label is
inferred when the frozen tensor is absent.

The direct mask paths remain BCE, Dice and the hard-IoU score target. Indicator
labels use the matched query indices and do not read the expanded GT-mask
index. A crossed-mask synthetic fixture changes the mask component while
leaving the computed indicator loss identical. The native coupled control
therefore needs to report the three components separately rather than treating
the native indicator loss as evidence for or against mask-binding repair.

Verification: 22 focused tests passed across the score, mask-component and
repeated-GT contracts. The tests cover exact indicator terms, EOS weighting,
crossed masks, empty score eligibility, duplicate positives, invalid
probabilities and fail-closed axes. This remains a CPU source contract, not a
native incidence, backward, resource, efficacy, novelty or admission result.

At 21:07 Asia/Shanghai, read-only server-6 status showed external PID 3694608
using 41,996 MiB on authorized GPU7, 42,023 MiB total and 100% utilization.
No native capture, model execution, sync, admission or queue mutation was
performed. The next executable action remains the ordered 256-row native TRAIN
capture and matched mask-only, label-only and coupled replay after GPU7 clears
and provenance checks pass.
