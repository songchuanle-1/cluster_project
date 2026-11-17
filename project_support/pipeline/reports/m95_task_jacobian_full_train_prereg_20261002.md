# Full TRAIN Task-Jacobian Replication

2026-10-02 15:15 Asia/Shanghai; diagnosis, no admission.

The first original 31-expression/2-scene probe shows near-orthogonal
mask/referent gradients and positive referent/semantic alignment. One mask
direction is adverse. The strict 1e-6 repeat tolerance failed on derived
cosines despite matching input fingerprints and native losses. Preserve
this failed check; do not calibrate a new tolerance from the observed drift.

Test the same actual native loss-component Jacobian on the existing frozen
TRAIN population of 102 expressions/28 scenes, population hash
`325626925578df183ef3f8ffdce2b7cb7f010ccefa87de70db0b4b1353f0d664`.
Retain all original loader companions and two seeded repeats. Expose the
whole denominator and per-scene summaries, not only positive results.
Use exact original checkpoint, dataset/annotation/graph hashes and native
matching. Same-query versus rotated-query ownership controls; no new
thresholds, optimizer, training or hyperparameter changes.

Expected general-antagonism diagnosis would require an actually adverse
native objective update, ownership-specific control separation and repeated
sign/direction; negative near-zero cosine alone is not proof. The full
102 cohort remains narrow physical-curtain exposure, not all ScanRefer.
Report strict repeat PASS/FAIL separately from raw descriptive readouts.
Candidate-native backward and efficacy remain untested.
