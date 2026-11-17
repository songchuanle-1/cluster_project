"""Freeze review and evaluation protocol before grouped inference."""
import json
from pathlib import Path

ROOT = Path("D:/project/cluster_project")
goal = json.loads((ROOT / "pipeline/goal.json").read_text(encoding="utf-8"))
stamp = "20260911-060900"
review = """# Motivation Review - cluster_project
2026-09-11 06:09 Asia/Shanghai.

## 1. Goal
Complete authoritative goal:
```json
""" + json.dumps(goal, ensure_ascii=False, indent=2) + """
```
Checker06:08:29:Phase1 NOT YET, championledger.5020/target.5100/gap+.0080.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context platform improves baseline | Historical support | Exact.5024607182 vs .4894491136 | Seed fragility and historical replay |
| Candidate selection can fail despite good masks | Confirmed in pilot examples only | Bothmodels3/8fail withoracle>.5 | Not population prevalence or relation cause |
| Singleton collector represents saved evaluation grouping | Untested | Same-forward equality only | Grouping/padding/repeatability audit |
| Shared-anchor mechanism is novel and useful | Provisional | Rethink memo | Error classification, derivation and primary sources |

## 3. Experiment Assessment
| Experiment | mIoU | Relation to motivation | Contribution |
|------------|------|-------------------------|--------------|
| Baseline historical best15 | .4894491136 | Reference | Strict-compatible audited checkpoint |
| M95 historical best16 | .5024607182 | Context platform | Strongest ledger model, not replay verified |
| M183 | .4915492237 | Fixed ancestor initialization | Closed tested variant |
| M186 | .4944996834 | Terminal transport | Closed tested variant, already analyzed |
| Baseline/M95 pilot8 | .538820513/.550915219 | Diagnostic correctness | 16 banks verified; not comparable to fullvalidation |
| M184/M185/M187/M188 | unfinished | Legacy controls | Preserve existing training and FIFO |

## 4. Gap Analysis
Same-forward capture equality does not prove singleton/group equivalence.
Dataset groups up to saved lang_num_max32, tokenizer pads to longest text.
Forward may depend on padding or batch kernels; repeatability is also untested.
Eight selected IDs are fixed from two diagnostic scenes; no reserved IDs allowed.
Additional descriptions from their original groups are nuisance batch context,
not additions to the diagnostic sample; record them without evaluating their errors.
Remaining276descriptions/69scenes, error labels, uncertainty, primary papers and
mechanism derivation are still missing. No population or causal claim from pilot.

## 5. Design Rationale
Q1: Is the new collector's input batching a protocol confound?
Q2: Hold checkpoint/inputs/seed fixed; compare singleton repeat, padded
singleton and original saved group for the same eight descriptions.
Q3: Determine whether diagnostic expansion must retain original groups.
Six coverage areas: this audit addresses diagnostic validity and a robustness
control; no novel mechanism/derivation claim, primary sources pending, matched
efficacy controls pending, resource guards retained (not efficiency benchmark).
All12constraints/11bans remain. No graph or numeric tuning, newtraining,
dataset, externalannotations, multiseed campaign or resource waiver.

## 6. Next Batch
See exp_design_20260911-060900.md, D1-GROUP evaluation-only.
No new training queue entries. Preserve legacy FIFO M189/M190/M191/M193.
"""
design = """# Experiment Design - cluster_project
2026-09-11 06:09 Asia/Shanghai.

## 1. Motivation
Goal description: """ + goal["description"] + """
Upstream review060900. Waiting4<reserve5 triggers review; scientific admission
overrides refill. D1-GROUP is protocol validation, not a new trained mechanism.

## 2. Current Best Results
| ID | Config | State | mIoU | Acc50 | spmIOU | Epoch |
|----|--------|-------|------|-------|--------|-------|
| Baseline | audited model_base2.yaml, explicitmodel_base1 | done | .4894491136 | .541 | .451 | 15 |
| M95 | audited ctf_hcg_csort | done | .5024607182 | .557 | .465 | 16 |
| M186 | mqht_tr | done_earlystop | .4944996834 | .548 | .459 | 17 |
Historical metrics, not fresh replay; pilot8 is not fullvalidation.

## 3. Analysis & Direction
### 3.1 Effective
Audited collector saves same original128candidate bank and exact selected output.
### 3.2 Failed
M183/M186 belowchampion; no automatic descendants or numeric rescue.
### 3.3 Unverified
For fixed x and weights theta, let F(x;B,L) be full bank/score output with
batch context B and padded length L. Compare:
S=F(x;{x},Lx), S'=repeat(S), P=F(x;{x},Lgroup),
G=F(x;original_group,Lgroup). S-S' estimates repeat drift;
S-P tests padding sensitivity; P-G tests joint-batch effects, not causal
decomposition if interactions exist. This is an evaluation identity, no gradients
or model graph changes. Report maxabsolute logit/score/probability difference,
changed bank bits, selected mask bits, selected index, a/o and seed/sample identity.
Original same-bank identity 1-a=(1-o)+(o-a) remains; oracleGT diagnostic only.
### 3.4 Conclusion
Do not assume singleton equivalence. Discrete prediction/IoU change rejects
interchangeability for that example; exact equality versus numerical closeness
reported separately. No post-hoc threshold for selecting a mechanism.

## 4. Experiment Plan
| # | ID | Config | Purpose | Expected Result | Priority | Depends On |
|---|----|--------|---------|-----------------|----------|------------|
| 1 | D1-GROUP-baseline | audited saved YAML | Repeat/padding/group comparison | Measure drift, no assumed equivalence | P0 | pilot |
| 2 | D1-GROUP-M95 | audited saved YAML | Same comparison | Measure drift on same8IDs | P0 | pilot |
Reuse scene0030_00/scene0046_00 and all8frozenpilotIDs. Original groups from
unchanged dataset.scene_inputs (lang_num_max32). Only selected8 errors measured.
Save group membership/token lengths/hash identities; no reservedscene inference.
Run singleton twice, padded singleton once and each relevant fullgroup once.
Keep group banks for selected8 and quantitative comparisons to immutablepilot.

## 5. GPU Allocation Plan
| Server | GPU | Assignment | Config | Justification |
|--------|-----|------------|--------|---------------|
| server-4 | 0 | Preserve M188 | mqb_tr | Active trainer |
| server-4 | 1 | Preserve M187; sequential bounded evaluation | baseline/M95 | free>=8GiB, torchallocatorcap4GiB |
| server-6 | 7 | Preserve M184/M185 | mqst_tr/mqpp_tr | max2trainers |
Before eachbatch free>=5GiB; eachworker max600seconds, shelltimeout720.
If group exceeds4GiB do not expandcap or killtrainer; record incomplete protocol
test and defer larger evaluation to resource-safe conditions.

## 6. Implementation Checklist
- [x] Upstream fullgoalreview and frozen protocol.
- [ ] Standalone helper, unchanged activepackages/checkpoints/configs.
- [ ] Hashverified deployment bothservers, onlyserver-4inference.
- [ ] Originaloutput equality; repeat/padding/group comparison and group IDs.
- [ ] CPU bankreadback/metrics and postflight trainer verification.
- [ ] Report exact gaps and refresh seven-sectionmemory.
No variant codecommit/enqueue: evaluation-only; no trainingpermission implied.

## 7. Risk Assessment
Same learnedstate does not establish baseline historicalforwardidentity.
Batch memory may exceedguard; do not treat resource abort as efficacy failure.
Record nonfinite/ID/hash mismatch, all missing comparisons;<=3repairattempts.
No assertion of general invariance from2scenes. No originalpaper noveltyclaim.
No tuning smells: no new modelgraph, hyperparametersearch or bannedfamily.
Data/seed/schedule/resources/Phase2boundary unchanged.
Status: APPROVED for bounded evaluation only.
"""
for directory, prefix, text in (("reviews", "motivation_review", review),
                                ("designs", "exp_design", design)):
    path = ROOT / "pipeline" / directory / f"{prefix}_{stamp}.md"
    assert not path.exists()
    path.write_text(text, encoding="utf-8")
print("Review then design frozen", stamp)
