# Native target-support contract, frozen M95 TRAIN capture

Stable diagnostic ID: `m95-sample-context-support`. Source is the 256-row
same-forward capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`;
the four mask-limited rows are frozen in
`m95_seed_coverage_residual_20260927.json` SHA256
`915e1d7e9385392a4f30da35a50b2698b54e005394caeb1d6d6a5ed2d3ca6bd5`.

Test whether the native mask target `target_union` on its own superpoint
axis differs from the physical target-instance membership of those same
superpoints. Recompute each selected query IoU from the artifact mask and
both support definitions. Require exact manifest, scene, annotation, selected
query, positive/matcher membership and capture/artifact hashes. Include
positive-control successful rows whose selected query is both target-seeded
and matcher-positive; report each denominator and support disagreement.

If the four failures have zero support disagreement, reject a native
target-support mismatch explanation for this subset. If disagreement exists,
do not infer that either target is preferable or admit a label-repair variant:
check its provenance, incidence against controls and a matched native causal
intervention first. No inference-time GT, retargeted loss, training claim or
validation-set selection is authorized by this diagnostic.
