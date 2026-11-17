# Motivation Review: Native Exposure And Identity

## 1. Goal
Current authoritative goal is pipeline/goal.json, ScanRefer mIoU>=.5100.
Champion M95=.5020, baseline=.4894, gap=.0080. All18 constraints/11 bans
remain unchanged; only server-6 GPU7/two slots, seed1999/original schedule.
No proposal is admitted merely to fill capacity.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Physical target anchors are necessary to represent a target mask | disconfirmed for observed missing-anchor cases | 2/128 missing anchors but selected masks .600/.909 | Other proposal failure causes remain unknown |
| Observed FPS index drift changes referent-positive identity | disconfirmed in controlled group | 8 index changes,0 physical/positive changes; wrong-identity controls separate | Numeric full-forward repeat FAIL persists |
| Previous exact-caption ambiguity and selector deficit | unresolved | Preserved earlier evidence | No independent validated new core |

## 3. Experiment Assessment
| Experiment/Diagnosis | mIoU | Motivation Relation | Contribution |
|---|---|---|---|
| M95 | .5020 historical | Existing reference model | No new efficacy this tick |
| M198-PDC / M199-BEI | .4977434 / .4741974 historical | Prior detail/boundary realizations | Natural early stops retained; no restart |
| Native anchor coverage32/128 | unknown | Separates exposure from selector failure | All target supports survive; both unanchored targets have successful native fallback |
| Native FPS identity4+4 forwards | unknown | Tests numerical identity conflict | Coordinate intervention fixes FPS drift,not full-output repeats |

## 4. Gap Analysis
Raw integer index drift is not itself a contradictory physical supervision
label. Native nearest-query fallback already represents the two observed
physically unanchored targets; forcing physical membership is not justified
by these cases. The prior real selector deficit and caption ambiguity remain.
Native float repeat failures are real; all thresholds and original failures
are preserved. No new-model native backward/resources/independence gate was run.

## 5. Design Rationale
Bootstrap exposure candidate was created before broad route review. Its
original configured counts256->128 were preserved; initial diagnostic512
assertion was an adapter bug, archived and corrected rather than a model edit.
The independently observed FPS drift motivated a second preregistered causal
identity test. Both concrete proposed explanations received disconfirming
native controls. Reject only these explanations,not every possible query axis.
Repeated mandatory-membership or FPS-only identity probes have no further
defensible information gain without new physical/supervision counterexamples.
This is scoped early stop,not global route exhaustion or a fake GPU block.

## 6. Next Batch
No exp_design/admission/launch. The short retry can resume independent causal
mechanism design on changed goal/queue/evidence or its due time. Do not
rebrand mandatory anchor membership, drift-only identity repairs, older
vertical signs/generic NLL, or PDC/BEI/PIRS; no tuning or tolerance changes.
