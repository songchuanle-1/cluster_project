# Motivation Review - cluster_project
2026-09-14 12:57 local. Design continuation, not training admission.

## 1. Goal
Authoritative contract: pipeline/goal.json, read in full this tick (13 constraints,
11 bans). Target ScanRefer mIoU >= .51, Phase1 NOT YET. Exact retained M95
.5024607181549072; baseline .4894491136074066; gap .0075392818450928.
Snapshot generated 12:55:43; active0, capacity4, candidate_budget4.

## 2. Story Status
| Hypothesis | Status | Evidence | Remaining gap |
|---|---|---|---|
| Historical context improves grounding | retained support | goal findings | not SCM evidence |
| Joint score-mask spatial supervision helps selection | unverified | 1245 design and cited 0945 derivation | novelty, admission, efficacy |
| Prior sparse count alone rejects SCM | superseded | C1; 124745 route decision | consistent historical profile |
| Historical timing satisfies C8 | false for current entry point | tools/train.py:229-230 | separate 20/100 timing run |

## 3. Experiment Assessment
No new terminal IDs; no terminal analysis or repair required. The snapshot's
M191 .4917 and M193 .4906 remain below M95. No failed-route successors.
Retained original bank: 284 expressions/71 scenes; M95 recoverables111,
same-category63/111 and disjoint89/111. No new diagnostic denominator.

## 4. Gap Analysis
Four web search queries and two direct opens returned no usable content this
tick. They establish neither novelty nor a prior-art match. Do not promote
unretrieved search targets into verified citations.
Current tools/train.py:187-251 specifies first VAL batch, lang_num_max1,
batch_size1, eval/no_grad and fvcore(model,(batch,'predict')). Its latency loop
uses warmup3/repeat10, unlike C8 warmup20/repeat100. Prior 1245 resources
correctly distinguished TRAIN/VAL but did not explicitly separate these loops.

## 5. Design Rationale
Create a read-only source-contract audit, not another execution of passed SCM
unit tests. Separate historical FLOPs compatibility from current latency
acceptance. This removes ambiguity before matched baseline/M95/SCM measurement;
it does not substitute source inspection for measured resources.
Keep SCM as the sole continuing core hypothesis. Boundary/adjacency lack
specific deficit prevalence; span remains a prior-art/small-head rejection.

## 6. Next Batch
See designs/exp_design_20260914-1257.md. Four slots screened, none admitted.
No new model IDs, model changes, training, queue mutation or deployment.
