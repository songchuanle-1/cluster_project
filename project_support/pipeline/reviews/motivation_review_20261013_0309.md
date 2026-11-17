# Native Main/Other Token Collision And Main-Mention Omission Review

## 1. Goal
Authoritative complete contract: pipeline/goal.json, read beforebegin.
Phase1 ScanRefer target.5100, champion.5020, baseline.4894, gap.0080.
All18constraints/11bans unchanged. Only server-6GPU7/two slots authorized;
this tick native tests CPU-only. No datasets, labels, schedule, seed,
production model/config, allocation or scheduler changes.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Main/other same-token supervision | Tested premise rejected | FullTRAIN overlap0 | Parser semantics and disjoint-role gradients not certified |
| Main mention vanishes from token map | Tested premise rejected | FullTRAIN empty-main0 | Correct referent identity not certified |
| TMR target-role intervention | Training | Prior positive native controls | Trained efficacy unestablished |

These are distinct from prior canonicalization/postfix drift, target-role
rebinding and literal category mapping. Role collision requires a nonempty
token to carry two roles; omission concerns no main token at all. One test
does not imply the other's outcome; intentionally overlapping and empty
controls produce separate signatures on the same original mapping method.

## 3. Experiment Assessment
| Experiment | mIoU | Relation to goal | Status |
|---|---|---|---|
| M95 champion | .5020 | Existing context baseline for deficits | Closed historical result |
| M198-PDC | .497743 | Point-detail realization below champion | Closed, not restarted |
| M199-BEI | .474197 | Boundary realization below baseline | Closed, not restarted |
| M200-TMR | Monitor Best.4953 | Target-role structural screen | Preflight running21/50/noimprove7/10 |

Snapshot2026-10-13T03:09:28.488289+08:00; structured running metrics and
GPU occupation unknown. No terminal result and no new launch this tick.

## 4. Gap Analysis
Original native mapping scanned all36665TRAINexpressions/562scenes:
32747have other-entity maps,34006have multiple graph nodes. Main/other
intersection expressions0/tokens0, empty-main maps0. All roots node_type
Object is source metadata, not proof that the root denotes the actual target.
Native control distinct spans givesmain[2]/other[5]; overlap givesboth[2].
Empty main-span list and out-of-range span both giveempty main withother[5].
These are constructed mapping controls, not real parser replays/errors.
No real positive cases existed for the registered loss-intervention follow-up.

First8unchanged frozen32/128 manifest groups give32native expressions, with
two seed1999 actual augmented getter passes. All seven role fields match the
original mapper; complete16-output digests repeat exactly. This is dataset
transport, not a whole-model forward/backward or effectiveness certificate.
No label was changed, no VAL/test selection and no original manifest rewrite.

## 5. Design Rationale
Reject these two prerequisites only. No structural core, paper novelty,
resource/backward/package PASS or trained improvement is claimed. The actual
native loss includes other-entity maps in a negative term, motivating the
collision test, but absent collisions give no causal gradient-error evidence.
An empty main map would not imply zero whole-model loss; mask/selector/other
roles remain, and no real empty-main case was observed. No substitute
variant is admitted just to fill the free task slot.
ScriptSHA102c7e103911f4a98b0a612a5b9d0a9845e5e0385ce2c67cc0cfef66c5e5361b
and resultSHA183d18fe951a04a7c7b5f256064f077a02aeed01bf7740d3fb74a657d0f48e36
bind executed evidence. Original remote CPU command ended exit0.
Remote observation03:18:32.84624+08 and local retrieval03:16:00.2634318+08
are retained separately (~153seconds clock difference). Original local
deadline04:09:28.488289+08 unchanged; no clock-based extension.

## 6. Next Batch
Scoped no_information_gain for repeating the two independently controlled
prerequisites, not all research exhausted and not a GPU block. No executable
candidate is abandoned. Actual new collision/empty-map evidence, independent
structural error/derivation, goal/queue change or retry eligibility can wake
research. Prior phrase/TMR positives and all native FAILs remain preserved.
Research retry2026-10-13T05:00:00+08:00; actual next scheduler time unknown.
M200 continues naturally. Tick completion only after finishPASS/exit0 plus
owned lease absence; this pre-postflight review does not claim completion.
