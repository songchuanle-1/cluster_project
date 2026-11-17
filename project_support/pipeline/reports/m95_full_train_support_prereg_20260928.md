# M95 full TRAIN support-backward generality test

Stable candidate: `m95-sample-context-support` (diagnosis only). This test
extends the frozen two-scene 11-expression native result without selecting
additional rows on checkpoint outcomes. Freeze **all** 102 original TRAIN
expressions in the 28 scenes with adjacent `shower curtain` tokens and a
physical non-target curtain instance, using the existing full-TRAIN census.
Keep target-curtain and linguistically unbound/mixed-role cases in the cohort.
Each expression keeps its original graph utterance, physical target ID and
other-curtain instance IDs. No validation/test-set selection or new labels.

Run the unchanged M95 checkpoint with seed 1999 and native TRAIN loader on
the selected 28 scene batches. Reconstruct original weak support and require
parity with native `sp_ref_masks`. Within each original forward, add physical
non-target curtain support versus a same-count, same-magnitude final FPS-seed
placebo outside target/curtain support; preserve matched/top-k protected seeds
and non-sample losses. Do not replace ineligible rows after outcomes: report
the exclusion count and reason. Read out per-expression sample-loss contrast
and native **existing** sampler-parameter gradient deltas, grouped by physical
scene and scene-target; retain adverse results and linguistic role strata.
No optimizer update. Fail closed on input hash/identity/parity/gradient drift.

This test asks whether the previously observed two-scene loss-path activity
generalizes to the full eligible TRAIN population, not whether a deployable
new mechanism improves inference. Physical geometry is reused across
descriptions; neither 102 expressions nor FPS seeds are independent trials.
No training admission follows until a distinct structural candidate, matched
mechanism control, candidate-native backward, resources, independence and
goal constraints all pass. Run only under a fresh exclusive server-6 GPU7
diagnostic lease with live occupancy and frozen code/data/checkpoint hashes.
