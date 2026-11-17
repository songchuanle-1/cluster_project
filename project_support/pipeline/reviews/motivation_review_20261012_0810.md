# Motivation Review: Target Mention Role

## 1. Goal
ScanRefer mIoU>=0.5100; M95=0.5020; baseline=0.4894; gap0.0080.
The unchanged goal.json is the complete constraints/bans authority. Native work
only server-6 GPU7, two slots; local orchestration/static only; Phase1 seed1999,
original schedule and <=10G uniform FLOPs. No routing/residual/selector successor.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Lexical shared-reference join supplies physical identity | realization rejected | 28/216 multiple-target joins | independently grounded identity unknown |
| Parser root necessarily names annotated target | counterexample | scene0631_00/ann1 root window, target trash can | broader true identity error rate unknown |
| Target-role maps influence native optimization | supported diagnostic | two native passes, paired gradients and null identity control | full model backward/resources unverified |
| New structural mechanism improves ScanRefer | unknown | no new training | complete six-gate admission required |

## 3. Experiment Assessment
| Experiment | mIoU | Relation | Contribution |
|---|---|---|---|
| M95 | 0.5020 | current comparator | actual champion |
| M198-PDC | 0.4977434277534485 | point-detail failure | no automatic successor |
| M199-BEI | 0.4741974174976349 | boundary supervision failure | retain negative trained evidence |
Old whole-model strict1e-6 failures remain failures. Current native logit2.861e-6
and mask2.766e-5 repeat FAIL; role-loss3.576e-7 and detached role gradients3.448e-7/
1.080e-7 are narrower PASS, not a full model certificate.

## 4. Gap Analysis
Frozen32/128 has one literal target-name mention outside root,109 overlapping,
18 absent literal matches. Whole TRAIN2115 outside-root candidates are NOT2115
proved identity errors. V1 taxonomy adapter error and initial CUDA/CPU fault
are archived; corrected V2 is authoritative for current native categories.
No predicted scores or VAL labels selected the cases.

## 5. Design Rationale
Test training-only annotation-anchored target mention roles on existing native
semantic alignment. For a single literal label span disjoint from parser-root
target spans, rebind target positive tokens and transfer the old root noun to
other-entity support. Preserve uncertain/multiple/absent cases unchanged.
This is a new positive-set definition, not another forward gate or config sweep.
It is a data/supervision correction; independent novelty is NOT established.
Original semantic alignment and generic phrase anchoring are not contributions.
Substantive source comparison is pending because current web calls returned
no usable content, not because the literature is absent.

## 6. Next Batch
See exp_design_20261012_0810.md. Build an isolated physical package/config, run
native full backward and matched controls, then paired predict resources.
No admission or training until all six gates substantively pass.
