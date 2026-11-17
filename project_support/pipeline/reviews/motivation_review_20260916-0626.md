# Motivation Review - Instance-Preserved Distributional Relations
2026-09-16 06:26 Asia/Shanghai. Proposed computation, NOT ADMITTED.

## 1. Goal
Authority: pipeline/goal.json in full, unchanged;14 constraints and11 bans.
Phase1 NOT YET at06:24:58. ExactM95 .5024607181549072;target.51.
No slot-filling exception to novelty,controls,resource or independence gates.

## 2. Story Status
Target masks cover118/123;non-target exact-name instance masks cover55/335,
although270have sampled seeds. Seed-owner supervision on current referent masks
conflicts on24/123expressions,16with valid other-instance owners.
These fixedTRAIN measurements justify separate physical-instance representation,
not efficacy of a particular architecture or intended anchor labels.

## 3. Experiment Assessment
Baseline .4894491136;M95 .5024607182;M195 .4986896217 belowchampion.
M196 .4799 at06:07;unchanged running. No new training result.
Existing ordered-distribution primitive passed CUDA gradients but lacked an
instance representation and a full downstream computation.

## 4. Gap Analysis
Candidate below preserves a separate index for each physical instance and a
separate referent mask. The relation statistic is never computed over a union
of same-category objects. Physical-instance supervision uses existing instance
labels,not fabricated auxiliary-mention labels.
Duplicate seeds can still represent the same object. Unsupervised anchor
selection,view-dependent relations and missing seeds remain limitations.

## 5. Design Rationale
Test a full instance-preserved distributional relation read at the final decoder
query update. It uses existing ordered-mass primitive for relative support,
not a mask-quality reranker or additional target-vs-competitor objective.
Novelty is UNVERIFIED: NS3D/CSVG/ORD already model object relations;
MDIN/InstAlign already separate masks and relevance; standard attention pooling
is not new. The whole proposal must demonstrate a meaningful distinction in
distributional rather than centroid relation computation AND pass banned checks.
This is a concrete hypothesis for scrutiny,not approval to revive closed pooling,
shared-witness or covariance directions.

## 6. Next Batch
Write full formula and an isolated CUDA mathematical prototype.
Prototype tests separate-mask gradients,strict ties,permutation and pairwise
reference equivalence. No production package or training until literature and
constraints gates genuinely pass. Stable parent same-forward-coverage-diagnosis.
