# M95 Native-Negative Query Intrusion

## Question

Do the remaining deployed-query mismatches from the exact M95 capture define
an independent causal unit, or do they restate the closed referent
classification/ranking family?

## Method

- Source: the completed 256-expression full-train capture with SHA256
  `68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`.
- Deployed selection is the recorded `indis[:, 1]` argmax. A mismatch is an
  expression where that query is outside the native-positive set.
- The control chooses the highest-scoring native-positive query on the same
  forward. Scene-cluster bootstrap intervals use 10,000 draws and seed 1999.
- Selected masks were partitioned using physical-instance endpoint IoU:
  target-IoU above 0.5, any non-target instance IoU above 0.5, or neither.
- This is read-only CPU diagnostic evidence. It does not establish a
  deployable selector, new mechanism, native backward, resources, novelty, or
  admission.

## Results

There are `49/256` native-negative deployed-query mismatches across 49 scenes.
The native-positive control improves mean IoU by `+0.50503` and success by
`53.06pp`; scene-balanced IoU delta is `+0.50503`, 95% CI
`[+0.38877,+0.61602]`. The best positive has median score rank `4` and p90 rank
`13`. The deployed query's mean score margin over it is `0.16455` (median
`0.07496`, p90 `0.44019`), so this is not only a near-tie phenomenon.

| Selected-mask endpoint class | Rows | Mean selected IoU | Success |
|---|---:|---:|---:|
| Wrong instance IoU > 0.5 | `32` | `0.00723` | `0.0%` |
| Neither target nor wrong-instance IoU > 0.5 | `13` | `0.22922` | `0.0%` |
| Target IoU > 0.5 but native-negative | `4` | `0.77998` | `100.0%` |

The selected query's seed is outside the target in all `49` rows, while the
best positive has a seed inside the target in `42/49` and some positive has a
target seed in `43/49`. Thus the failure is not primarily missing query
coverage: target-seed candidates exist but the query-only indicator head ranks
them below a native-negative query.

The four target-IoU-positive rows expose a definitional limit of the native
positive set: a query can predict the target well from a seed outside the
target while remaining native-negative. Those rows are already successful and
are not evidence for a deployable repair. The observable failed denominator is
therefore 45, dominated by 32 wrong-instance selections and 13 partial or
disconnected masks.

## Conclusion

The result restates the closed referent classification/ranking problem. The
only non-oracle information visible here is `indis`, whose prior decisions
already measured the same wrong-instance-over-positive-query margin and
rejected reweighting, reranking, competition, listwise, exclusivity, PIRS, and
mask-aware-positive successors. The four mask-positive/native-negative rows
instead duplicate the closed target-binding/co-support route.

No new information path is supplied that can distinguish a target seed from a
wrong-instance seed at inference. Rejecting this as a new candidate is
therefore based on concrete route identity, not on another failed score or
selector experiment. Keep both queue slots empty and do not train or launch a
successor.

## Evidence

- `pipeline/reports/m95_negative_intrusion_partition_20260925-0731.json`
  `sha256=5a277d507c27208e6703152af914f6b0e16d6ea40c4f6be6f03323d1181bff18`
- `scripts/m95_negative_intrusion_partition_20260925.py`
  `sha256=15a9d77134d0ea66e99c6addf98869598b58831f0fefb4b7ab4b88cf25cd0fa3`
- `scripts/test_m95_negative_intrusion_partition_20260925.py`
  `sha256=48ab732a17136c45c44436d9d218e350ccf3fbf688dcfd49027293dd147a7acb`
- `pipeline/decisions/20260916-093202_next_batch.md`
- `pipeline/decisions/20260917-081555_route_change.md`
- `pipeline/decisions/20260917-221554_route_change.md`
- `pipeline/decisions/20260925-071505_route_change.md`
