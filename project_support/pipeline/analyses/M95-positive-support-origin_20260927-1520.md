# M95 native-positive target-support origin

This tick continued `m95-sample-context-support` on the SHA256-frozen
256-expression / 220-scene M95 TRAIN capture. The primary frozen cohorts
were four fragmented mask-limited expressions (four scenes), 12 other
mask-limited expressions (12 scenes), and 16 preselected target-size-matched
covered controls (16 scenes). All relevant artifact and source hashes,
manifest indices, native positive sets, and physical seed axes were checked.
Server-6 CPU executed three native-capture reads; a local fourth audit
checked the existing IoU threshold. None changed the model or trained.

| Readout | Fragmented 4 | Other limited 12 | Covered 16 |
|---|---:|---:|---:|
| Positive union adds target recall | 2 | 0 | 2 |
| Positive union repairs best-positive IoU <=0.5 | 1 | 0 | not applicable |
| Positive union harms best-positive IoU | 2 | 3 | 5 |
| Positive union breaks best-positive IoU >0.5 | not applicable | not applicable | 1 |
| Missed-by-positive support reached by target-seeded negative queries | 0 | 0 | 0 |
| Missed-by-positive support reached only by non-target-seeded negatives | 5 | 23 | 5 |
| Target superpoints uncovered by every query | 11 | 47 | 5 |
| Uncovered target superpoints directly sampled as FPS seeds | 1 | 4 | 1 |

The four fragmented rows each have a target-seeded native-positive query,
yet the additional support is not generically available inside the native
positive set. Among their five target superpoints reachable only by
matcher-negative off-seed queries, one is covered by a same-class seed,
three by other-class seeds and one has unknown target/seed semantics. The
one native-positive union threshold repair (manifest 64, 0.47 to 0.65)
is a retrospective upper bound with GT-dependent matcher membership;
the covered-control threshold break (manifest 8, 0.54 to 0.43) is a
specificity warning. All-query union repairs none of the limited rows.

Neither "new positives are missing" nor "same-class peer transport" is
supported as a general independent mechanism. The remaining uncovered
superpoints are mostly not directly sampled, but every fragmented
expression has some target-seeded query: the census cannot distinguish
sampling resolution, decoder context, feature representation or ordinary
mask loss. No new prediction-blind information unit, matched same-forward
causal intervention, placebo, independent native-model backward, resources
or constraints receipt exists. Do not promote any retrospective union to
inference or relabel generic mask-aware matching/ranking/PIRS/BCCA.

Evidence: `pipeline/reports/m95_native_positive_union_20260927.json`,
`pipeline/reports/m95_missed_positive_origin_20260927.json`,
`pipeline/reports/m95_offseed_semantic_origin_20260927.json`,
`pipeline/reports/m95_positive_union_specificity_20260927.json`,
`pipeline/reports/m95_uncovered_seed_reach_20260927.json`.
Resume only from a distinct, falsifiable prediction-blind deficit with
preregistered mechanism/placebo controls, keeping Phase 1 gates intact.
