# Motivation Review - What The Encoder Features Do And Do Not Encode
2026-09-16 10:48 Asia/Shanghai. Diagnostic only; nothing admitted.

## 1. Goal
pipeline/goal.json authoritative: 14 constraints, 11 bans, target mIoU >= .51.
Ledger champion M95 .5020; exact .5024607181549072@16; Phase 1 NOT YET.

## 2. Question
The bottleneck is referent identification among same-name neighbours, and every
readout over existing features failed. Before deriving another mechanism, establish
what the encoder features actually encode: do they separate two same-name instances
at all, or do they cluster by category?

## 3. Method Note
Deep features share a dominant mean direction, and raw cosine is inflated by it: on
this checkpoint the scene-mean pairwise cosine is .928 while the target-to-wrong
cosine is .854, which superficially suggests the pair is *less* similar than average.
That statistic is dominated by the common component and is not discriminative.
The measurement below centres every instance centroid on the scene mean before
computing similarity, which is what removes the shared direction. The first run of
this script also included self-similarity in the "nearest neighbour" statistic; that
bug is fixed and self-similarity is excluded.

## 4. Result
Fixed 16 TRAIN batches, M95 eval forward, instance feature centroids = mean of the
final encoder `inst_feats` over each instance's superpoints (native sp_ins_labels),
centred on the scene mean. For each of the recoverable failures, rank every instance
by centred cosine similarity to the instance the deployed query actually segmented.

| Quantity | Value |
|---|---|
| scenes have (mean / median) instances | 38.7 / 40 |
| target is the nearest neighbour of the wrong instance | 21.4% (chance 3.3%) |
| target in the top-3 | 42.9% |
| target in the top-5 | 53.6% (chance 16.4%) |
| median rank of the target | 4th |
| centred similarity target-to-wrong | .270 (median .269) |
| centred similarity over all instance pairs (null) | .029 (median .031) |
| centred similarity to the nearest other instance | .675 |
| spatial distance target-to-wrong | 1.33 m median |

## 5. Interpretation
Same-name instances are about 9x more similar to each other than a random instance
pair (.270 vs .029), and the target is the wrong instance's nearest neighbour in one
case in five. So the encoder features do carry instance-specific content, and they
systematically encode *category* similarity. What they do not do is resolve
*identity* within a category: in nearly half the recoverable failures the target is
not even in the top-5 nearest neighbours of the instance that was chosen.

This is a better explanation of the earlier readout failures than "region pooling
breaks the signal". Any scorer that pools or averages instance features, and any
language-vs-region similarity, inherits a representation whose leading axis is
category. That is why 23 readout variants and both probes failed while the mask head
itself works: the mask head only has to decide *where*, which category-dominated
features do well, not *which one*, which they do not.

It also fits the expression side: 31 of 33 recoverable failures carry a content
relation, another mentioned entity or an attribute contrast, and the target-to-wrong
distance is only 1.33 m. The discrimination that separates the pair is spatial and
relational, and it is exactly what the feature space does not encode.

## 6. What This Rules Out
- Any further scorer, probe, re-projection, re-weighting or pooling over the current
  instance features: they cannot manufacture identity discrimination that the
  representation does not carry, which matches the measured failures.
- Treating the earlier region-scoring negative result as a property of pooling
  specifically; it is a property of the features.

## 7. What Remains
The mechanism has to introduce discriminative information that the current encoder
does not provide, i.e. relational or spatial identity evidence, rather than
re-reading what is already there. The standard fixes on the supervision side are
prior art (RefMask3D) and banned, and the cluster/scale side is decision-inert, so
the remaining space is narrow and must be argued explicitly against NS3D, JVGN,
RefMask3D, InstAlign and HCF-RES before anything is admitted.

## 8. Next Batch
-> see pipeline/designs/exp_design_20260916-1048.md
Status: DIAGNOSTIC COMPLETE / REPRESENTATION CHARACTERISED / NOT ADMITTED.
