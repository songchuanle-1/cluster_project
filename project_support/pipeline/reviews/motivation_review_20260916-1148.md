# Motivation Review - Impasse Determination And Decision Brief
2026-09-16 11:48 Asia/Shanghai. Determination; no experiment run this tick.

## 1. Goal
Thread objective: keep the loop running until at least one NEW QUALIFIED variant is
enqueued and actually training, without faking admission.
goal.json: 14 constraints, 11 bans, target mIoU >= .51, Phase 1 NOT YET.
M95 ledger .5020 / exact .5024607181549072@16; baseline .4894491136074066@15.

## 2. What The Project Contract Says
Two clauses bear directly on the current state:
- 2026-09-10 execution priority: "没有合格候选时继续数据诊断、推导、原始文献核对或
  离线正确性检查，记录缺口，不为填满 GPU 批量扩展 selector/pooling/回写变体."
  So when no qualified candidate exists, the prescribed action is continued
  diagnosis/derivation/literature - and explicitly NOT filling GPUs.
- 2026-09-14 capacity authorisation: "若合格候选少于容量缺口，允许保留空槽并记录淘汰
  原因." Empty slots with recorded reasons are a permitted, anticipated state.

Consequence: the pipeline itself does not treat "no candidate" as an error. But it does
require that continued work be substantive diagnosis, derivation or literature review -
not restatements and not slot filling.

## 3. The Measured Position
| Finding | Value | Evidence |
|---|---|---|
| expressions with >=1 acceptable query | 118/123 = 95.9% | acceptable_mask_rank |
| mean acceptable queries per expression | 26.3 | same |
| wrong selection despite acceptable existing | 27.3% scene-balanced, CI [18.0, 37.5] | scene uncertainty |
| oracle effect of restricting to native positives | +17.9 pp, CI [+10.9, +25.8], 22 fixed / 0 broken | intervention |
| objectness-only control | exactly null | same |
| nonlinear scene-held-out readout ceiling | 59-65% vs oracle 87.0% | decodability |

## 4. Routes And Why Each Is Closed
| Route | Disposition | Basis |
|---|---|---|
| rescore / calibration / rerank / region scoring | closed | measured to fail, linear and nonlinear |
| objectness-only mechanisms | closed | null control (69.1% -> 69.1%) |
| multi-scale / pooling / selector / readback / scale gate | closed | decision-inert, 0/123 winner changes |
| instance-pure / boundary-aware re-partitioning | closed | banned pooling family + 81.8% not co-clustered |
| shared-support / referent consensus | closed | resolves 0 of 8 persistent disagreements |
| modality re-weight / extra fusion / gate | closed | MDIN prior art; numeric or recombination |
| carry 2D identity to the decision | closed | identity-rich but not language-addressable |
| phrase-graph / relation grounding | prior art | JVGN, NS3D, RelationField |
| region-language scoring | prior art | InstanceRefer, M3DRef |
| mask-aware referent positives | prior art | RefMask3D (cls+BCE+dice), DETR matching |

The causal fix the evidence points to is a **learned** change (readouts excluded), and
the learned change that supplies referent identity is mask-aware matching / one-to-one
assignment - prior art, and therefore unavailable as this project's contribution.

## 5. Why This Is An Impasse Rather Than Thin Progress
The remaining diagnostics are executable but cannot yield the objective's deliverable.
The deliverable is a NOVEL qualified variant; the search for one has now been run
across every evidence-supported axis, and each is closed for one of exactly three
reasons: measured ineffective, decision-inert, or prior art. Continuing to generate
diagnostics would change no admission-relevant state.

The one thing that WOULD change the state is a scope decision that only the user can
make, because goal.json's constraints and banned[] are user-owned and the project
forbids relaxing them autonomously.

## 6. Options For The User
| # | Option | Effect |
|---|---|---|
| A | Authorise the prior-art mechanism (mask-aware referent matching) as a MATCHED CONTROL or baseline, not as the contribution | Immediately gives a runnable, evidence-backed control with a known effect size; does not claim novelty |
| B | Amend goal.json banned[]/constraints[] to open a specific direction | Re-opens exactly one axis; requires naming it |
| C | Redirect the target (different error stratum or a different mechanism family entirely) | Resets the search space |
| D | Commission an annotation-level investigation of the 31/33 cases whose phrases carry a relation, another entity or an attribute contrast, yet where no measured language representation separates a target from a same-name neighbour 1.33 m away | Tests whether those phrases are genuinely under-determined - the one remaining scientific question the current evidence cannot settle |

Option A is the only one that produces a training run from this tick's evidence without
touching goal.json.

## 7. What Has Been Preserved
Nothing was fabricated: admissions/ is empty, no queue entry was written, no commit or
sync happened, and no training was launched. 328 evidence entries in
research_work.json hash-verify against disk with 0 problems. Two of my own earlier
inferences were retracted by measurement rather than left standing.

## 8. Next Batch
-> see pipeline/designs/exp_design_20260916-1148.md
Status: IMPASSE DETERMINED / AWAITING SCOPE DECISION / NOTHING ADMITTED.
