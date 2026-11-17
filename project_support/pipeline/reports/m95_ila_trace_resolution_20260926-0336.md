# M95 Layer-5 Trace Resolution

## Native control

On authorized server-6 GPU7, the exact M95 model-source hash
`cf4ce01548cecf186ba4677f5c13977f9fa527b2e33af6c82f564a7150a4c1d0`
was verified before invoking its unmodified `CrossAttentionLayer` with fixed,
synthetic source/query/mask tensors and fixed initialized weights. Across 32
forwards, the primary 1332x256 output and first 1332x48 auxiliary output
each had one byte hash and zero maximum finite delta. The second auxiliary
output was nonfinite in all 32 repeats, with one stable byte hash; this
diagnostic records that separately and does not use it as a finite delta.
Receipt: `pipeline/reports/m95_ila_fixed_operator_20260926-0332.json`
SHA256 `18477f06ea14c8e9233e87dffc1bfe66c8be2d315d4609f8ee40adfe5f6a8006`;
script SHA256 `758dbf0ed3be3cb6c42ed49f3f6c08f25cf8373e081429d75d8f1e73a607a1f0`.

This disconfirms the isolated fixed-input `ila` operator as sufficient for
the earlier four-hash final-layer drift. It does not reproduce the trained
M95 weights, the original layer inputs, or the frozen TRAIN item.

## Blocked matched replay

The diagnostic harness now hashes the final layer's structured cluster
message and both exact `ila` inputs and can replay the first CPU-all-scatter
cluster message through later forwards. It compiles locally; script SHA256
`2c3b6f93d18f23a8eac6be8864f338d872675bf01c4b9a29ba0626ba5420edf1`.
It was **not** executed: the required checkpoint SHA256
`fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`
was not found in the authorized host's project checkpoint tree or bounded
diagnostic staging, nor in the local project checkpoint tree. No substitute
checkpoint is valid. A historical replay exists, but its command did not
persist the checkpoint path. Locate or restore a read-only copy and verify
its full hash before resuming; then check GPU7 occupancy and run the bounded
four-repeat matched control. The frozen full-scan item SHA must be bound
separately before any row-83 causal claim.

## Admission

The original strict comparator still fails 26/65 paired rows. The 256-row
component intervention changed zero masks and measured zero harm; coverage,
selector, referent relabeling, duplicate, relation and scale routes remain
rejected or closed. There is no novel mechanism with diagnosis, matched
controls, native backward, resources, independence and constraints all passed.
No queue entry, sync or training launch was made.
