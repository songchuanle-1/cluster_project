# Score-matched placebo for M95 full TRAIN weak support

Continue stable `m95-sample-context-support`, diagnosis only. The 102-row
native full-TRAIN intervention produced 86 eligible replays in 22 scenes,
but its placebo was chosen by physical instance/seed order. The treatment
may have different pre-intervention sampler scores; a lower focal loss could
reflect score placement rather than meaningful physical context support.

Freeze the same 102 original TRAIN expressions, unchanged checkpoint, source,
geometry, original text and seed 1999. In each same-forward replay, choose
zero-support placebo FPS seeds before any criterion outcomes: among eligible
non-target/non-curtain seeds, greedily match each treatment seed in ascending
native FPS order to the unused placebo seed with the smallest absolute
**baseline** `ref_scores` difference; break ties by seed index. Keep the
original equal number and magnitude of final focal targets, protected seeds
and all non-sample losses invariant. Report baseline score imbalance per row
as mean absolute paired difference and every excluded row, retaining adverse
and target-curtain/unbound cases. Aggregate contrasts by scene and physical
scene-target, not by dependent expression or FPS seed. This is a distinct
control, not a new model or proof of causal target selection. If score-matched
control erases the contrast, do not treat prior loss direction as mechanism
evidence. No post-hoc threshold or sample replacement. No training admission.

Run only under a new exclusive server-6 GPU7 lease and verified live
occupancy, code, original population, source/data and checkpoint hashes.
