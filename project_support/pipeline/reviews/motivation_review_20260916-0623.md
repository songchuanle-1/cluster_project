# Motivation Review - Instance Versus Referent Masks
2026-09-16 06:23 Asia/Shanghai.

## 1. Goal
goal.json remains authoritative:target.51,exactM95.5024607181549072.
Scientific admission before capacity. No modified schedule/seed/newannotations.

## 2. Story Status
Context mask coverage55/335 despite270sampled exact-other-noun instances motivates
explicit physical-instance learning,not a claim that any auxiliary loss is novel.
Need distinguish a query's geometric owner from the referent it is assigned.

## 3. Experiment Assessment
Native123TRAIN16batches,original matcher wrapped without changing returns.
| Support | Matched queries | Owner-target mismatches | Valid other-instance owner |
|---|---:|---:|---:|
| FPS |867|25|17|
| Selected |824|24|16|
Each mismatch is in a distinct expression. Native helperexit0,no repair.
The matcher first assigns nearest center regardless of seedowner,then adds
target-owned seeds. This is intentional coverage fallback,not automatically a bug.
All-instance seed supervision on the SAME mask conflicts with existing target
supervision for these queries. Invalid/unassigned owners are excluded separately.
No full-training impact,VAL improvement,or coreinnovation demonstrated.

## 4. Gap Analysis
For a conflicting query let owner mask be u and assigned target mask v.
Both are valid disjoint physical instances. Summed unweighted BCE on identical
logits z has derivative2sigmoid(z)-u-v;where u != v its optimum is1/2.
Thus generic extra owner BCE compromises the shared mask rather than defining
two representations. This algebra is not a novel objective.
Removing fallback may sacrifice uncovered targets;not authorized as a shortcut.

## 5. Design Rationale
Primarytexts archived/read:
- MDIN arXiv2407.20664:multiquery target instance decomposition and discrimination.
- InstAlign arXiv2411.15087 HTML sections3.1-3.4:instance supervision,phrase-object
  alignment and relevance-weighted aggregation;2D referred instances,not proof
  of full-scene3D context supervision.
- 3DRefTR arXiv2308.11887v2 section3.5:jointREC/RES losses and maskbranch.
Do not claim dual heads,instance supervision or generic alignment themselves new.
Full candidate needs distinct physical-instance versus referent representations,
defined communication and relation computation beyond generic dualbranch/gating.
The observation changes implementation requirements;does not disprove trainability.

## 6. Next Batch
Derive complete instance-preserving relational computation with non-conflicting
supervision and bounded cost. Preserve target fallback;no generic all-instance
shared-mask loss or rebranded lossweight scan. No more matcher/coverage audits.
Independentpackage/config,novelty,backward,resources,receipt,sync/launch pending.
Evidence:instance_match_contract_20260916.json;decision062225.
