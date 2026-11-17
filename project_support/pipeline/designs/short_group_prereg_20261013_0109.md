# Native Short Language Group Transport

Tick df2a9c7a64ac4f32aaeeb64746369555; unchanged deadline
2026-10-13T02:09:04.233414+08:00. TRAIN only, seed1999, no new labels/config.

Independent hypothesis: original train groups with fewer than lang_num_max=4
lose or misassociate annotation IDs, referent masks or language rows in the
original dataset partition and collate, before they reach model.loss.
This is not missing semantic category, support-ID compaction or padded mask
loss weighting. Scope is loss-input transport, not full GPU forward.

Freeze all original36665 annotations; every scene/ann pair must appear once
in scene_inputs, in the original scene-local order, no cross-scene group.
Select first two native groups of each actually observed length1/2/3/4 in
original dataset order, prediction blind, at most8groups. Fetch these groups
twice with seed1999. Pair adjacent selected groups in original collate, then
reverse each pair as a matched control. Compare IDs, counts, object IDs, all
GT masks, context masks, tokenized language rows and dense maps with the exact
concatenated getter outputs. Repeat hashes must agree.

Negative control deliberately assigns four expressions per group instead of
observed lengths and must disagree for an actually short pair. No production
code is changed. Reject only the pre-loss short-group omission/misassociation
premise if all partition counts and sampled collations pass. Do not certify
GPU expansion/FPS/decoder/loss or all arbitrary batch combinations.
Native whole-model backward/resources/independence remain pending, not PASS.
