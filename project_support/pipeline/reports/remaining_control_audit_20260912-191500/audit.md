# Remaining Legacy Control Audit

2026-09-12, tick #20260912-1907. CPU-only audit of the four preserved pairs,
selected from the original queue, not from current scores. No new experiment.

| Child | Parent | Parent exact best | Best/final epoch | Post-best validations | Source change |
|-------|--------|-------------------|------------------|-----------------------|---------------|
| M189-CTF-HCG-CSORT-MQBC-TR | M177-CTF-HCG-CSORT-MQBC | 0.4962787926 | 17/27 | 10 | recurrence only |
| M190-CTF-HCG-CSORT-MQTD-TR | M178-CTF-HCG-CSORT-MQTD | 0.4930404425 | 24/34 | 10 | recurrence + padding fix |
| M191-CTF-HCG-CSORT-MQSD-TR | M176-CTF-HCG-CSORT-MQSD | 0.4935617447 | 14/24 | 10 | recurrence only |
| M193-CTF-HCG-CSORT-MQHC-TR | M174-CTF-HCG-CSORT-MQHC | 0.4934916496 | 17/22 | 5 | recurrence only |

All four numerical YAMLs are byte-identical to their parents; all four
packages differ only in dec.py. For M189/M191/M193, the complete source
difference is the final-layer condition replacing the recurrent condition.
M190 additionally slices padded cluster features to each scene's real
cluster count. This confirms the already documented repair; it is not a new
bug or permission to change the active trainer.

## Interpretation Boundaries

- M189 vs M177: a source-level recurrence intervention with full-patience
  parent evidence; one seed and no paired scene predictions still preclude
  a statistically established recurrence effect.
- M190 vs M178: padding correction and recurrence removal are two changed
  behaviors. A future score difference cannot isolate recurrence alone.
- M191 vs M176: source-level recurrence intervention, but parent ran on
  server-6 and child is assigned server-4. Hardware and training environment
  matching remain unverified; do not claim they are controlled.
- M193 vs M174: parent has only five post-best validations due to historical
  monitor-parser stopping error. A future full-patience child comparison is
  censored on the parent side.
- All four parents exceeded the current 10G gate in archived analyses.
  Their scores remain historical comparisons, not resource-qualified baselines.
- Live M189/M190 are censored observations, not terminal results. Waiting
  M191/M193 have no outcome. No successors or reruns follow this audit.

## Evidence And Limits

All 229 analysis documents and 226 ledger rows were read.
JSON inventories every analysis hash, four parent log hashes, exact paired
best metrics, package hashes and two timestamped live-log snapshots. Hashes
are local integrity records; this tick does not claim fresh remote hash
verification of the four parent archives.

This audit addresses correctness of existing comparisons. It supplies no new
measured error, forward/loss derivation, novelty, robustness or efficiency result.
The admission gap remains open. goal/queue/running/ledger bytes are unchanged.
