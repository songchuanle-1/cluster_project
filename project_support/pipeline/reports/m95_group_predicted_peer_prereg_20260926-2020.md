# Predicted-mask local-peer test

Stable ID: `m95-explicit-group-topology`. Inputs are frozen independent
lower/upper TRAIN cohorts (SHA256 `ecf6d9fe21f254e512b4fc490bc8a843a256a0a8c9e8ae5cab79c86bbf894edc`,
`e86746aac35cae5e3a47e6cf277bdc67fbd4dc14efb4ddc9811f68d499bbbe85`)
and graph binding (SHA256 `4cd1e5e9e3739fbaa892c91c9fd786a292a72d68b381d4898e14470fbd9c1031`).
Only expressions whose node-0 modifier contains the matching lower/bottom
or top/upper cue and with a same-name physical peer enter the frozen set;
deduplicate by (cohort, scene, target), lowest annotation ID first. The
original seven-row group screen and all 256 manifest expressions are excluded.

Native producer: server-6 GPU7, M95 checkpoint, TRAIN mode, seed 1999,
unchanged forward and criterion. Save all 128 proposal mask logits, sampled
superpoint XYZ, native scores, target mask, physical-instance labels and
the native input hash for each frozen expression in one forward. Fail closed
on incomplete identities/support, nonfinite positions, or changed source
and checkpoint hashes. An exact replay of the same frozen rows must match
the saved input and model hashes. This changed-producer diagnostic cannot
repair the historical strict full-scan mismatch (26/65).

Outcome-blind construction: binarize each proposal at native logit > 0;
discard empty masks. The center is the mean XYZ of its positive
superpoints. For each proposal, select the nearest distinct proposal in XY
among masks with Jaccard < 0.5, breaking ties by query ID; the overlap
condition prevents duplicate masks of one object masquerading as peers.
No class label, GT target, IoU, score, language cue or success enters this
construction. For the shuffled control, rotate the sorted eligible peer
query IDs by one within the expression; this preserves the same eligible
pool and mask centers. A single eligible peer yields an unchanged control,
reported separately and excluded from claims of control separation. Freeze
true/shuffled assignments before attribution.

After assignment, attribute each target-covering proposal using native
mask IoU > 0.5 against the saved target mask. Compare the expected vertical
sign of target versus true local peer and shuffled peer, by unique
scene-target unit, reporting both directions, missing coverage, mixed votes,
and scene-level counts. Attribute a peer to one physical instance only when
its positive mask has a strict majority of that instance's superpoints;
report the stronger target-distinct same-name peer-and-sign conjunction
separately from raw signs. Expected true-minus-shuffled improvement is
positive on target-bound cases, not selected by outcome. Zero/reversed
difference, missing target proposal coverage, or unstable repeat rules
disconfirm this realization. Even a positive result is only a diagnostic:
an actual matched model-path intervention, native backward, resource
budget, independent package/config and constraints remain required.
