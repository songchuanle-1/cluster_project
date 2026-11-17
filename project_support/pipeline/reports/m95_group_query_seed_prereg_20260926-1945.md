# M95 group-topology query-seed diagnostic

Stable ID: `m95-explicit-group-topology`. Freeze the native 256-row
changed-producer TRAIN capture at server-6
`pipeline/diagnostic_runs/m95_boundary_repeat_20260926-1813/capture.json`
and the prior seven-row screen at
`pipeline/reports/m95_group_topology_screen_20260926-1851.json`.
Bind rows by manifest index, scene, and annotation ID. Do not use
validation data or inspect outcomes to form neighbors.

For every screened group expression, count native sampled query seeds
on the target physical instance. For each target seed with another
physical-instance seed, choose the nearest other-instance seed in XY,
breaking ties by query index. Compare the vertical sign with the
explicit target-bound lower/bottom or upper/top expression, and its
reverse sign. Report target seed and nearest-neighbor coverage per
expression, not just aggregate seed counts. For bottom/lower only,
exclude expressions whose group word modifies another object or is a
mixed relation; report exclusions. Compute a separate exploratory
seed-to-instance mapping for the independent physical cohorts only
if their native capture exists. Sampled instance labels are GT used
here solely as a diagnostic oracle to attribute proposal seeds;
they cannot define deployable neighborhood membership.

Falsifier: missing target proposal coverage, ambiguous referent binding,
or nearest-seed cue unstable to selection of multiple seeds. Even
favorable signs are insufficient for admission: `sampled_pos` is
seed position rather than predicted mask centroid, and the native
same-forward true/shuffled mask-level model intervention, native
backward, resources, independence and constraints must all pass.
The changed-producer subset is not a strict reproduction of the
historical full scan (26/65 strict comparison failed).
