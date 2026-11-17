# Frozen physical target / semantic class contract

Stable ID `m95-physical-target-semantic-conflict`. The question is whether
exact in-vocabulary ScanRefer target names disagree with the native semantic
class of the physical target instance, producing a conflicting class context
for target versus distractor seeds. This differs from lexical span/annotation
agreement: it checks physical instance labels in the frozen M95 capture.

Before outcomes, freeze the 256-expression changed-producer TRAIN native
capture SHA256 `9271ea8e5202590e99e3d1e2da1a729ee87262bba8fecf96bd394c7f0abda1cd`
(the derived cohort JSON has distinct SHA256 `5a1ddd9a906983416adbfb0e9d03b386de92a21803fdf20afe40740b5a69687e`),
annotation SHA256 `018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d`,
dataset-source SHA256 `2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d`,
and label-TSV SHA256 `9c17c0da2061beea889edc9f49ff14e8218f4cd040ab241fc70186e03b32a744`.
Use native `type2class`, `sem2nyu`, and label-TSV mapping. Include only target names exactly present in
`type2class` other than `others`; mark aliases, compounds, unknown semantic
labels, missing/ambiguous physical target identities, and inconsistent
semantic labels unresolved. Primary exposure: resolved physical target
semantic class differs from the exact annotation class. Report every row,
all and ambiguous/class-unique denominators, frozen deployed failures,
same-scene discordant pairs and class-matched controls. Do not use outcome
to choose synonyms or change eligibility.

Zero or sparse failure-unlinked contradictions reject this realization.
If exposed failures are present, verify raw native point/support and
annotation identity plus matched loss-path control before any mechanism
design. An observed class mismatch alone is not causal evidence, backward,
resource validation, novelty, or admission. No training or queue mutation.
