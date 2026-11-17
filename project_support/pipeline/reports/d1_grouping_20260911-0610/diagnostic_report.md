# D1 Grouping And Repeatability Audit
2026-09-11 06:15 Asia/Shanghai.

## Protocol
Review/design060900 precede inference. Same audited baseline/M95 checkpoints,
seed1999, source/manifest/code/package hashes and eight frozen pilot IDs.
Two diagnostic scenes: scene0030_00/scene0046_00.
Five original groups per model have32/32/26/32/32 descriptions,154 unique
context descriptions total. Only eight frozen diagnostic IDs contribute metrics;
146 additional descriptions are batch context, not new diagnostic observations.
No reserved physical scene evaluated. Original saved lang_num_max=32.

Four executions per selected description: singleton S, repeat S',
singleton padded to original group length P, original group G.
Compare S:S',S:P,P:G,S:G and priorpilot:S. Padding tokens/masks verified
equal to the corresponding original-group rows. No inference graph changes.
Original predict_by_feat remains unchanged and selected probabilities/IoU are
checked against it. Fullgroup banks saved for only the diagnostic IDs.

## Results
Maximum absolute mask-logit differences:

| Comparison | Baseline | M95 |
|------------|----------|-----|
| Repeat singleton | .0001010895 | .0001277924 |
| Singleton to padded singleton | .0000944138 | .0001525879 |
| Padded singleton to original group | .0001120567 | .0001296997 |
| Singleton to original group | .0001144409 | .0002431870 |
| Prior pilot to current singleton | .0001106262 | .0001602173 |

For all five comparisons and all eight descriptions per model:
- Zero candidate-bank binary bit changes (sigmoid>=.5).
- Zero selected point-mask bit changes and selected-index changes.
- Zero selected/oracle IoU differences.
- FPS seeds, sampled indices, GT and superpoint mappings match.

Therefore the observed three pilot selection failures/model are not explained
by THESE tested grouping/padding changes. This does not prove general batch
invariance, bitwise determinism, historical code identity, causal language errors
or error prevalence. Padding and repeat noise are not independently identified
causal effects; they are measured pairwise execution differences.
No new mechanism admitted and no new novelty claim.

Pilot metrics unchanged: baseline selected/oracle .538820513/.892994612;
M95 .550915219/.889365964; both5/8Acc50. These are not fullvalidation metrics.

## Verification And Resources
-16saved grouped banks downloaded and SHA256 verified.
-CPU readback recomputes all candidate IoUs within1e-7 and checks selected/
 oracle indices, crossmodel GT/superpoints and original group membership.
-CPU verifier CUDA uninitialized; all16banks pass.
-Baseline5groups, peak torch allocation2292.666MiB, inference loop15.220s.
 M95samegroups, peak2055.822MiB,27.172s. Sharedload, not speed comparison.
-Both preflights10601MiB free, allocatorcap4GiB and batchfreeguard5GiB.
 Bothworkers exit0; no OOM or crash repairs.
-Helpers deployed under/tmp/cluster_d1_grouping_20260911_0610 on bothservers.
 Active tracked deployment diffs unchanged; no model/config/checkpoint edits.
-28pipeline tests pass3.567s. Postflight GPU1 back to21509MiB trainer-only.
 Allfourtrainers live;M187newbest.4902902544@17,nowepoch18.

## Remaining Work
Still only8/284diagnostic descriptions and2/71physicalscenes characterized.
276descriptions/69scenes remain. The154context descriptions are NOT additional
coverage. Use original groups for subsequent expansion where resource-safe;
do not assume all scene sizes fit this cap. Record resource skips, no silent
fallback or result-based subset selection.
Then classify coverage/boundary/identity/relation errors with explicit annotation
rules and scene-level uncertainty. Primary-paper novelty and core mechanism
derivation remain incomplete; scientific admission continues to override refill.
