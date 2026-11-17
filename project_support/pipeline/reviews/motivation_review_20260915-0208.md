# Motivation Review
2026-09-15 02:08 Asia/Shanghai; design budget 1.
## 1. Goal
Binding source: pipeline/goal.json, read in full: 13 constraints and 11 bans.
ScanRefer mIoU >= .51; Phase1; M95 exact .5024607182, gap .0075392818.
Diagnose concrete grounding errors before proposing a lightweight core mechanism.
No changes to the goal, seed1999, schedule, resource accounting or banned routes.
## 2. Story Status
|Hypothesis|Status|Evidence|Gap|
|Boundary assignment errors exist|Frozen diagnostic only|memory:123/139 failures inverted|TRAIN prevalence|
|Conditional assignment addresses them|M196 running|design20260914-2217|efficacy|
|Count-only likelihood addresses inversions|Not established|count-restoration design20260915-0009|identifiability and gradient direction|
## 3. Experiment Assessment
M95 .5024607182 versus baseline .4894491136; no new terminal evidence.
SCM18/50 best.4888; CPS7/50 best.4662; BCA2/50 best.1079.
Partial metrics neither establish failure nor justify early stopping.
Previous joint count+assignment candidate is algebraically BCE and remains closed.
Count-only was explicitly not resolved by that previous identity.
## 4. Gap Analysis
Count likelihood depends on y only through k=sum(y). It cannot distinguish
different assignments of identical count, precisely the inversion-error question.
The frozen GT-count projection rescued4/139 failures; it does not establish an
independent TRAIN count bottleneck. These numbers are inherited, not recomputed.
## 5. Design Rationale
Review one candidate: count-only boundary likelihood as an independent loss.
Use an exact two-variable counterexample and exhaustive finite-difference checks.
Veto admission for the proposed inversion rationale if its descent reinforces
an incorrect assignment while remaining identical for the correct assignment.
This is a local mathematical falsification, not an efficacy experiment.
## 6. Next Batch
See pipeline/designs/exp_design_20260915-0208.md.
No model construction until the rationale passes; no reserved experiment ID.
