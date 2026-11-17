# Motivation Review - Oriented Contact Conditional Audit
2026-09-15 06:08 Asia/Shanghai.
## 1. Goal
Authority: pipeline/goal.json, read in full (13 constraints, 11 bans).
ScanRefer mIoU>=.51; Phase1; exact champion .5024607182, gap .0075392818.
No policy changes; preflight already performed monitor/goal exactly once.
## 2. Story Status
|Hypothesis|Status|Evidence|Gap|
|Boundary assignment is relevant|Diagnostic only|284 M95 banks/71 scenes;123/139 failing banks inverted|Deployable corrective mechanism|
|Unsigned contact identifies orientation|Rejected rationale|exp_design_20260915-0408.md|Directed supervision may duplicate existing losses|
|SCM/CPS/BCA improve efficacy|Running|Snapshot:3 running, no new terminals|Final validation|
## 3. Experiment Assessment
Exact historical baseline .4894491136, Acc50 .541, spmIoU .451 at epoch15.
M95 .5024607182, Acc50 .557, spmIoU .465 at epoch16.
M184-M191/M193:0/9 exceed M95; do not reopen their descendants.
M196 is already testing group conditional boundary assignment.
## 4. Gap Analysis
Q1: Giving crossing edges an orientation fixes the unsigned objective's label
ambiguity, but may only re-express an existing pairwise ranking primitive.
Need to distinguish mathematical identity from identical whole-model behavior.
No new sample collection is necessary for this admission-level algebra audit.
## 5. Design Rationale
Q2: Derive P(Y_i=1,Y_j=0 | Y_i+Y_j=1), compare with pair BCA and RankNet.
Q3: An identity closes a renamed-duplicate proposal without another GPU run.
Primary paper checked: Burges et al., Learning to Rank using Gradient Descent,
ICML2005, section3, equations(1)-(3), official ICML-hosted PDF:
`https://icml.cc/Conferences/2015/wp-content/uploads/2015/06/icml_ranking.pdf`
The pair cost uses a logistic score difference and cross-entropy. This is
prior art for the primitive; no exhaustive claim about contact applications.
## 6. Next Batch
Budget1. Audit one potential proposal; do not allocate a model/config/ID.
See exp_design_20260915-0608.md. Native/full-loss/resource gates not passed.
Pending approval questions from snapshot: [].
