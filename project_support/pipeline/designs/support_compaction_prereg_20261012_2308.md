# Native Superpoint Compaction Preregistration

Tick42f0e79c9e444f47808a5e16c9ea80d4, unchanged deadline.
Hypothesis: cropping preserves gapped support IDs, producing zero-point
scatter rows that become spurious model supports.

Test unchanged original32-scene/128-expression TRAIN manifest, seed1999,
original native __getitem__ twice. For each returned support assignment,
enumerate occupancy of every ID from0throughmax. Cross-check support-shaped
GT/context masks and instance labels; collate consecutive pairs using the
original method and verify offset support IDs are occupied. Native CPU only.

Controls: [0,2] creates one empty row under the actual torch_scatter mean;
original unique-return-inverse compaction gives[0,1] and removes the empty
row. Identity/permutation preserve occupied support membership.
Reject only the gapped-ID/empty-row premise on the fixed cohort if every
getter and collated batch has zero empty IDs. Report points/supports,
sample IDs, hashes and exact repeat. This is not an argument against all
support geometry, padding, boundary or refinement mechanisms.
