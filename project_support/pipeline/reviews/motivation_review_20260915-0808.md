# Motivation Review - Component Conditioning Admission Audit
2026-09-15 08:08 Asia/Shanghai.
## 1. Goal
Authority: pipeline/goal.json, read fully: 13 constraints and 11 bans.
ScanRefer mIoU>=.51; Phase1 NOT YET; exact M95 .5024607182,
baseline .4894491136; exact gap .0075392818. No policy changes.
## 2. Story Status
|Hypothesis|Status|Evidence|Gap|
|Boundary assignment errors matter|Diagnostic only|284 M95 banks/71 scenes;123/139 failures inverted|Deployment efficacy|
|Group conditional assignment helps|M196 running|4/50,.4041|Terminal evidence|
|Independent contact components need independent counts|Unverified|No component-stratified evidence in bounded snapshot|Causal admission|
## 3. Experiment Assessment
M95 peak16: Acc50 .557/spmIoU .465; baseline peak15: .541/.451.
M184-M191/M193:0/9 exceed M95; no successors.
M194/M195/M196 remain independent running hypotheses, not efficacy evidence.
Previous oriented-contact audit (exp_design_20260915-0608.md) distinguishes
pairwise and full-group BCA; it does not establish that more conditioning helps.
## 4. Gap Analysis
Q1: Does conditioning on each contact component's GT count remove spurious
cross-component competition, or erase needed occupancy-transfer supervision?
Current diagnostic counts do not resolve this. No new sample prevalence claim.
## 5. Design Rationale
Q2: Derive the conditional objective and construct a disconnected-component
counterexample before allocating a new training variant.
Q3: A failed universal correction rationale can prevent an unsupported BCA
regrouping successor. A toy pass would still not establish native efficacy.
Prior-art lead: Tarlow et al., Fast Exact Inference for Recursive Cardinality
Models, inherited from M196's durable evidence. Search and attempted abstract
retrieval returned no usable content this tick. Independent source verification
and application novelty review are INCOMPLETE; no novel primitive is claimed.
## 6. Next Batch
Budget1; evaluate one component-conditioned proposal offline, admit only if
all gates pass. See exp_design_20260915-0808.md.
Snapshot pending approval questions: []. No user interaction required.
