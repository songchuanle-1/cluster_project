# Motivation Review - Component Conditioning Information Audit
2026-09-15 13:08 Asia/Shanghai.
## 1. Goal
Authority: pipeline/goal.json, read in full (13 constraints, 11 bans).
Target ScanRefer mIoU >= .51; Phase1 NOT YET.
Exact historical M95 .5024607182; baseline .4894491136; gap .0075392818.
No goal, schedule, seed or scheduler changes.
## 2. Story Status
|Hypothesis|Evidence|Gap|
|---|---|---|
|Boundary assignment errors matter|Memory:284 banks/71 scenes, missing0;123/139 failures inverted|Mined diagnostic evidence, not efficacy|
|Component conditioning has a valid boundary domain|1110 proof and exhaustive audit|Native incidence and full-loss benefit unknown|
|Component conditioning adds useful supervision|Independent component shifts are null directions|Exact relationship to global BCA unresolved|
## 3. Experiment Assessment
No new terminal IDs. Preflight M194 .4924 at27/50, M195 .4970 at19/50,
M196 .4441 at7/50; none establishes a new champion or terminal conclusion.
Historical baseline Acc50/spmIoU .541/.451; M95 .557/.465.
Failed/withdrawn branches remain closed as recorded in durable memory.
## 4. Gap Analysis
The 1110 domain correction removes the homogeneous-component objection.
It does not establish that conditioning on component counts adds information.
Determine whether component loss is simply global fixed-count loss with
the probability of the observed component-count event divided out.
## 5. Design Rationale
Q1: Which supervision does component conditioning retain or remove?
Q2: Derive the partition-function identity and test it on disjoint mixed
components, including component shifts and a connected-component control.
Q3: Bound the admissible claim before native tests or production implementation.
Prior-art lead: Tarlow et al., arXiv:1210.4899 (inherited reference).
Web search, PDF open and retrieval probe returned no usable content this tick.
Original-source comparison and novelty remain INCOMPLETE; no novelty claim.
## 6. Next Batch
Candidate budget1; evaluate the existing unresolved proposal, not a renamed
training successor. See designs/exp_design_20260915-1308.md.
Snapshot pending questions: []. Record unresolved gates in artifacts; no user interaction.
