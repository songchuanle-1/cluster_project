# Motivation Review - Boundary Component Domain Audit
2026-09-15 11:10 Asia/Shanghai.
## 1. Goal
Authority: pipeline/goal.json, all 13 constraints and 11 bans read.
ScanRefer mIoU>=.51, Phase1 NOT YET; exact M95 .5024607182,
baseline .4894491136; gap .0075392818. No policy changes.
## 2. Story Status
|Hypothesis|Evidence|Status|
|---|---|---|
|Boundary assignment errors matter|Frozen 284 banks/71 scenes, missing0|Diagnostic, not efficacy|
|BCA improves grounding|M196 running6/50,best.4275|Unresolved|
|Homogeneous components invalidate component conditioning|0808 synthetic counterexample|Domain needs checking|
## 3. Experiment Assessment
M194 .4924@25 observed epochs; M195 .4924@16; neither terminal.
M95 peak16 Acc50 .557/spmIoU .465; baseline peak15 .541/.451.
No new terminal IDs; no failed-route successor authorized.
## 4. Gap Analysis
The 0808 design distinguishes GT-crossing and full induced contact graphs,
but does not prove that its homogeneous components survive actual boundary
selection. M196 boundary_assignment.py defines B as endpoints of GT-crossing
edges. Every vertex in B therefore has an opposite-label neighbor also in B.
This may invalidate the synthetic counterexample even on the induced graph G[B].
## 5. Design Rationale
Q1: Is the rejection counterexample in the proposed mechanism's domain?
Q2: Prove the boundary graph invariant, enumerate small graphs, and contrast
an unrestricted full-scene component with the actual induced boundary graph.
Q3: Correct the evidence boundary without treating removal of one objection
as positive efficacy or novelty evidence. No renamed training successor.
Prior-art lead inherited from durable evidence: Tarlow et al. (2012),
Fast Exact Inference for Recursive Cardinality Models, arXiv:1210.4899.
Search and direct abstract retrieval returned no usable content this tick.
Independent source verification, full-text comparison and application novelty
remain incomplete; no new mathematical primitive is claimed.
## 6. Next Batch
Budget1; no fresh scientifically admissible candidate established.
Perform an offline correctness audit tied to the 0808 component proposal.
See designs/exp_design_20260915-1110.md. Pending snapshot questions: [].
