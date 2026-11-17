# Motivation Review
2026-09-15 00:09 Asia/Shanghai. Design budget: 1.
## 1. Goal
Source: pipeline/goal.json, read in full this tick (13 constraints, 11 bans).
Phase1 ScanRefer mIoU >= .51; exact M95 .5024607182; gap .0075392818.
Goal: diagnose concrete grounding errors and derive a falsifiable lightweight
mechanism; do not treat pooling/selector variants or queue depth as research.
All constraints/bans remain binding; no goal or scheduler changes.
## 2. Story Status
|Hypothesis|Status|Evidence|Gap|
|Boundary assignments matter|diagnostic only|boundary_cardinality_probe_20260914.json|training efficacy|
|Conditional boundary assignment helps|M196 running|design2217|no validation yet|
|Missing count supervision merits another mechanism|under review|BCA ignores common logit shift|BCE already retained|
## 3. Experiment Assessment
Baseline .4894491136 and M95 .5024607182 remain the comparison anchors.
M194 .4888 at progress16/50; M195 .4413 at5/50; M196 at1/50 without validation.
These are partial runs, not terminal comparisons or grounds to stop a route.
Frozen count projection rescues4/139 failures and retains144/145 successes;
123/139 failures have boundary inversions. GT boundary/count is not deployable.
Source hash:17ea5448f1d3021d634a36eeeaf78dd20db362a9c624cc83a1e9e1ec4956155c.
## 4. Gap Analysis
Conditioning discards count likelihood, but retained BCE supervises occupancy.
A count-restoration proposal must first show it is not algebraic BCE duplication.
Frozen inversion statistics do not establish a separate count-calibration bottleneck.
## 5. Design Rationale
Review exactly one candidate: joint boundary count and assignment likelihood.
Derive its reduction and test values/gradients offline before model construction.
If equal to BCE, reject as an independent core rather than train a renamed loss.
This tests a redundancy hypothesis, not efficacy or original-source novelty.
## 6. Next Batch
See pipeline/designs/exp_design_20260915-0009.md.
No training admission unless the structural and scientific gates pass.
