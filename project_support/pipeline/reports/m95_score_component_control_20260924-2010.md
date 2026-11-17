# M95 score component control (offline)

Time: 2026-09-24 20:10 Asia/Shanghai. Source: M95 `loss.py` SHA256
`c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5`.

The separate score component wrapper accepts optional frozen score predictions
alongside the existing fixed-pair masks and logits. For each original/corrected target
binding it applies the criterion's strict hard-IoU > 0.5 eligibility and
computes mean squared score error over only that eligible set; an empty set
contributes zero. The score tensor is never inferred. Indicator loss remains
unmeasured. The result is per expression before native batch normalization,
layer weighting and training gradients.

Focused tests: 20 passed across the score component, existing component and
repeated-GT contract tests.
Synthetic tests include crossed eligibility, empty eligibility, equal-valued
GT masks, and invalid score axes. No frozen score predictions or native ordered
256-row capture were available. This does not measure incidence, efficacy,
backward execution, resources or novelty.

At the single read-only server-6 query, authorized GPU7 had external PID
3694608 occupying 41,996 MiB, 42,023 MiB total used, 39,057 MiB free and
90% utilization. Do not run native diagnostics or displace this job. Once GPU7
clears, verify code/runtime/data/checkpoint/producer provenance and occupancy,
then run one ordered capture and matched mask-only, label-only and coupled
controls. No admission or queue mutation.
