# Preserved Control Archive Provenance

Tick #20260912-2007; verification 2026-09-12 20:10 Asia/Shanghai.
Read-only SSH SHA256 verification of four original parent logs. No training,
new experiment, registry update, checkpoint transfer or deployment change.

| Parent | Child | Exact best mIoU | Acc50 | spmIOU | Best/final epoch | Stale | Remote hash |
|--------|-------|-----------------|-------|--------|------------------|-------|-------------|
| M177-MQBC | M189-MQBC-TR | .4962787926197052 | .548 | .459 | 17/27 | 10 | matches |
| M178-MQTD | M190-MQTD-TR | .49304044246673584 | .546 | .455 | 24/34 | 10 | matches |
| M176-MQSD | M191-MQSD-TR | .4935617446899414 | .541 | .456 | 14/24 | 10 | matches |
| M174-MQHC | M193-MQHC-TR | .49349164962768555 | .548 | .457 | 17/22 | 5 | matches |

All 107 validation records are contiguous within each run and contain paired
mIoU/Acc50/spmIOU metrics. Every evaluation reports 9508 expressions.
This confirms denominator counts, not identity/order equality of every expression.
Hashes, exact metric sequences, archive paths and verification times: audit.json.

## Live Observations

At20:10 M189 has23 completed validations, best .49086183309555054 at19,
current24/50, stale4/10. M190 has18 completed validations, best
.4890006184577942 at14, current19/50, stale4/10. No terminal marker.
Trainer PIDs3398172 and3595977 remain present; additional matching processes
are workers, not additional experiments. Two timestamped raw snapshots retained.

## Interpretation

Only archive provenance is newly closed. Prior source audit remains valid:
M190 changes both recurrence and padding; M193 parent has only five stale
validations; M191 changes server platform without verified environment matching.
All four parents are historical >10G comparisons. Single-seed aggregate
differences do not establish paired-scene uncertainty or robust causal effects.
No successor, rerun or new mechanism is admitted.

## Integrity

All229 analysis documents read/hash-inventoried;226 ledger rows loaded.
goal.json, queue.json, running.json and experiments.csv hashes unchanged.
Prior audit SHA256 recorded. No fresh primary-source review was undertaken;
existing novelty closures remain in force. No validation outcomes are independent
confirmation of the diagnostic banks or evidence of test-set performance.
