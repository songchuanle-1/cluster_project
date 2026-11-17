# M95 Frozen Score Margin and Checkpoint Recovery Audit

## Frozen control

The original reference analysis SHA256 `c7b6e78c` and the strict full-scan
analysis SHA256 `f8456b4e` were compared on all 256 manifest expressions
from 220 scenes. The read-only query-score margin control found zero
selected-query changes. Only one row has a reference top-two margin no
larger than twice its observed maximum per-query score drift: row 202,
scene0615_00, margin 1.0728836e-6 versus drift 7.8231096e-7.
Its selected query 4 and IoU 0.9565217 are unchanged. This is an observed
pairwise drift bound, not a bound on future runs. It does not support
reopening a ranking/selector model route. The original strict identity
gate remains failed at 26/65 paired rows.

Receipt: `pipeline/reports/m95_score_margin_stability_20260926-0350.json`.
Focused tests: 4/4 passed, including hash/selector guards and synthetic
exposed and stable margins.

## Matched native replay

At 2026-09-26 03:44-03:51 Asia/Shanghai, key-based SSH to the authorized
server-6 succeeded and GPU7 sampled at 0% utilization / 0 MiB. A bounded
read-only check found the exact M95 checkpoint directory absent under the
configured server-6 work_dir. The prior bounded local and diagnostic-stage
checks also found no `.pth` with the required full SHA256
`fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`.
Other variant checkpoints were present, but are not substitutes. No trained
`--trace-ila` control or full-scan item binding was claimed.

## Disposition

`m95-repro-drift-boundary` remains blocked by unavailable exact trained
weights, not rejected on efficacy. Retry after 2026-09-26 04:07:05+08:00
if a read-only copy is restored or located and full hash verified. Recheck
GPU7 guard, then run the four-repeat matched layer-5 cluster-message and
`ila`-operand trace and intervention. Bind the transformed item to the
frozen full-scan native-input hash separately. No queue mutation, sync,
training launch, or six-gate admission.
