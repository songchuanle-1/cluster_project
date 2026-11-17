# Motivation Review - Cluster Instance Purity
2026-09-16 07:58 Asia/Shanghai. Diagnostic only; no training admitted.

## 1. Goal
pipeline/goal.json remains authoritative: 14 constraints, 11 bans, target .51.
Ledger champion M95 .5020; exact checkpoint .5024607181549072@16; Phase 1 NOT YET.
The goal description names three diagnostic targets: candidate coverage and
boundary, same-class discrimination and relation binding, and multi-scale
evidence duplication. The first is complete; this review addresses an
unmeasured cause behind the second.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Cluster context beats no-cluster baseline | confirmed | A1-A0=+.0118 | which sub-design is necessary |
| Explicit routing carries benefit | refuted | A3-A1=-.0544 | closed |
| Same-name misselection is caused by geometric cluster mixing | refuted this tick | wrong winner shares an l0 cluster with the target in 18.2% of wrong cases vs 6.7% for an average other instance | residual causes unidentified |
| Target features are contaminated by other instances | confirmed, weak causal link | 48.2% of target superpoints sit in a mixed l0 cluster; 58.1% on failures vs 43.8% on successes | not sufficient to explain 33 wrong instances |

## 3. Experiment Assessment
Fixed 16 TRAIN batches, M95 eval forward, geometry taken from the model's own FPS
partitioner, purity computed against native sp_ins_labels. 123 expressions over 32
scenes; 85 success / 38 failure (33 wrong instance). 91 of 123 expressions repeat
a scene's geometry, so scene counts are not independent samples.

Measured:
- Mixed-cluster fraction by scale: l0 26.7%, l1 64.8%, l2 97.5%.
- Target superpoint contamination (cluster holds >=2 instances): l0 48.2%,
  l1 89.0%, l2 100%.
- Contamination split: success l0 43.8% vs failure l0 58.1% (+14.2pp).
- Wrong instance shares an l0 cluster with the target in 18.2% of wrong cases.
- That same case averages 6.7% against the scene's other instances, so
  co-clustering is enriched about 2.7x, but is absent in 81.8% of wrong cases.
- Wrong winner centroid distance 2.03 m vs 2.84 m for an average other instance:
  the confused instance is systematically nearer, not merged.

## 4. Gap Analysis
Refuted: geometric cluster mixing is not the primary cause of same-name
misselection. Co-clustering is enriched but covers only 18.2% of wrong cases, so
an instance-pure partitioner cannot explain the remaining 81.8%.

Confirmed but not sufficient: target evidence is genuinely diluted. Half of the
target superpoints receive a cluster token averaged over at least one other
instance, and coarse scales are almost entirely mixed. This is a representation
quality fact, not a demonstrated cause of the specific wrong selection.

Consequences: an instance-aware or boundary-aware re-partitioner would target a
mechanism that is (a) only weakly linked to the observed failures and (b) already
inside the goal's banned pooling family. It also duplicates heavy prior art in
soft-grouping 3D instance segmentation. It must not be admitted on this evidence.

## 5. Design Rationale
The measured separation between the observed 18.2% and the 6.7% null is real and
should be preserved as a stable observation for any future mechanism that claims
to fix instance contamination. It is not enough to justify a training variant:
the causal route from contamination to the wrong winner is absent in four of five
wrong cases.

Not pursued this tick, with reasons:
- Instance-pure re-partitioning: banned pooling family plus weak causal link.
- Stronger cross-scale decorrelation: CSORT already occupies that axis; raising
  its weight is a numeric change, not a structural mechanism.
- Query-conditioned scale mixing: duplicates the banned qcond family by rename.
- Inference-time query re-selection: banned reranking family.

## 6. Next Batch
-> see pipeline/designs/exp_design_20260916-0758.md
Status: DIAGNOSTIC COMPLETE / TRAINING NOT ADMITTED.
