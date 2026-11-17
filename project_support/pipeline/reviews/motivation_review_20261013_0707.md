# Motivation Review - cluster_project

## 1. Goal
Goal source: pipeline/goal.json, SHA256
d7296cbb4cfc0742e92ccccc65a17b36513dcd8940c98c90e38801e79f14b21b.
ScanRefer mIoU target0.5100; champion0.5020, gap0.0080. All18 constraints
and11 bans remain unchanged, including Phase1 no tuning, seed1999, original
schedule, prediction-blind TRAIN diagnosis and the six admission gates.
This cycle addresses referent/relational supervision, not pooling/routing.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Actual relation/other token intersection | Observed220/36665,274positions | Original native mapper full562TRAINscenes | Shared tokens' semantics and native model consequences |
| Later root mentions dropped by row-zero transport | Rejected premise only | 9748multi-span expressions,10878later-only positions,0omission/value mismatch | Parser completeness remains unknown |
| Relation/other intersection changes loss gradient pathway | Controlled synthetic indication | Original Criterion,220cases/155scenes,exact repeats;7sign flips | Native decoder/total-loss backward not run |

## 3. Experiment Assessment
| Experiment | mIoU | Relation To Goal | Contribution |
|---|---|---|---|
| M95-CTF-HCG-CSORT | 0.5020 | Current champion | Unchanged comparator |
| M200-TMR | 0.4952795207500458 | Prior root-role screen | Native earlystop23/50; no champion gain or automatic restart |
| Current two registered diagnostics | Unknown | Test distinct map-to-loss/transport premises | Not trained variants or efficacy estimates |

## 4. Gap Analysis
Native loss source gives root relation positions a positive term and doubles
other-entity logits in a negative denominator. Actual intersections exist,
unlike the previously tested target/other intersection. On zero synthetic
queries and identity-token inputs, all220cases change gradient when only
overlap's other term is removed; scalar loss remains equal at zero logits.
Of274coordinates, original gradients are7positive/267negative; the7positives
reverse after removal. This supports pathway activity at this operating point,
NOT274wrong labels,7trained failures or harmful native gradients.
Actual first8positive-scene native getter groups contain29expressions; all7map
fields match the original mapper, twice seed1999. Synthetic loss repeats
exactly;19cases lack enough disjoint other positions for equal-size placebo.

## 5. Design Rationale
First stable diagnosis was registered before broad review. The second tests
omitted span transport independently of intersecting-role signs. Its broken
first-only control loses a valid second token while the original retains it.
Only the transport omission premise is rejected. Original source/data/config
hashes were verified and all diagnostics ran remotely on server-6 CPU.
Bare removal/masking or loss-weight changes are diagnostic controls, not this
project's new core. No novelty claim, new architecture or admission is made.
Native GPU7 same-forward original/identity/intersection/opposite/disjoint
controls are preregistered and implemented but NOT run.

## 6. Next Batch
GPU7's original exclusive guard detected PID262355 and started no diagnostic.
Post-CPU observation still shows34557MiB/81559MiB with that process;0%instantaneous
utilization is NOT idle. Both diagnostic locks were available after the failed
guard. Project queue0 and2training slots do not imply an available EXCLUSIVE
card, and process ownership/project is not inferred from the username.
Only authorized physical GPU7 is occupied; no other legal card can supply the
frozen exclusive test. Do not call both training slots occupied or evict jobs.
Mark the same relation candidate blocked on that exclusive resource after
completing non-GPU work; retry2026-10-13T08:00:00+08:00 or earlier when GPU7 has
no compute processes, memory<1000MiB and both diagnostic leases are acquired.
Reuse frozen first8positive groups and first original frozen control group,
the original M95 checkpoint/config and unchanged1e-6 repeat threshold.
Remote clocks are about206seconds ahead of local; retain both timestamps,
not an extended deadline. No new train/admission; original deadline08:07:49+08.
