# Live Common-Epoch Audit
Tick #20260912-2107; sampled 2026-09-12T21:10:04.883086 Asia/Shanghai.

## Protocol
Read-only log analysis of the original preserved M189/M190 controls.
Compare epochs 1 through min(completed child validations, completed parent
validations), without extrapolation, smoothing choices or early-stop changes.
Pairs were fixed by the existing designs, not selected from these scores.
Each complete live validation reports 9508 expressions. Counts do not prove
identical expression identities/order or input preprocessing.

## Observations
| Child | Parent | Common epochs | Child best | Parent best | Best delta | Last5 mean epoch delta |
|-------|--------|---------------|------------|-------------|------------|------------------------|
| M189 | M177 | 24 | 0.4908618331 | 0.4962787926 | -0.0054169595 | -0.0026091576 |
| M190 | M178 | 19 | 0.4890006185 | 0.4905349910 | -0.0015343726 | -0.0041712761 |

The best delta compares two maxima within a common epoch budget; best epochs
need not coincide. Last5 is a descriptive paired-epoch mean, not independent
replication or a scene-paired confidence interval. All epoch metrics are in
audit.json. Raw live snapshots are retained with SHA256.

## Interpretation
Both children remain live and censored. Do not label either as failed or
complete and do not stop before the existing patience criterion. This
comparison reduces unequal epoch-budget distortion but does not establish
a causal or statistically reliable effect. M190 also fixes padding, so its
recurrence effect cannot be isolated. Single-seed and unverified environment
matching remain limitations. No new mechanism or successor is admitted.

## Integrity
All 229 analyses read/hash-inventoried; 226 ledger rows loaded.
Parent local hashes match the prior remote-verified provenance record;
no fresh remote parent hash check is claimed. Goal, queue, running map and
ledger hashes are unchanged. No model/config, checkpoint, schedule, GPU job,
deployment or training modification. No terminal or crash marker in snapshots.
