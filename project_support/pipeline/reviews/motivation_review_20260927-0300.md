# Motivation Review - Same-Scene Role Transitions

## 1. Goal
`goal.json` describes a lightweight, falsifiable structural mechanism for
ScanRefer 3D referring localization, based on concrete errors rather than
pooling, selector or routing permutations. Phase 1 target mIoU 0.5100;
champion M95 0.5020, baseline model_base1 0.4894. All `goal.json`
constraints and bans, particularly no Phase 1 tuning, remain binding.

## 2. Story Status
| Hypothesis | State | Evidence | Gap |
|---|---|---|---|
| Multi-scale context helps | historical confirmed | M95 0.5020 versus baseline 0.4894 | New core mechanism unproved |
| Correct referent among available candidates is the bottleneck | causal readout, not new method | fixed-checkpoint positive-set restriction +17.9 scene-balanced pp on 123 TRAIN expressions | Standard mask-aware matching is prior art |
| Non-target class-context seed scores expose wrong selections | observational | two 32-key transform passes, four exposed failures each | No matched causal training intervention |
| Seed lies within selected query mask | non-discriminating | corrected positive 201/207, negative 47/49 | Cannot identify referent role |

## 3. Experiment Assessment
| Experiment | mIoU / result | Relation to goal | Contribution |
|---|---|---|---|
| model_base1 | 0.4894 | baseline | no cluster |
| M95-CTF-HCG-CSORT | 0.5020 | champion | multiscale context benefit |
| M197-PIRS | 0.4920 stopped_unknown | score-target supervision | no automatic restart; prior-art successor closed |
| Physical-instance noisy-OR diagnostic | 316/316 bags above target, 289 suppressive and 27 zero gradients | context seed supervision | rejected formulation |
| Same-scene role census | 44 target-to-context pairs in 14/32 scenes; two selected wrong-context failures | possible paired supervision unit | feasibility only, not efficacy |

## 4. Gap Analysis
The dataset groups several expressions for the same scene. The model copies
one scene's superpoint features and FPS seed indices for each expression
(`network.py:225-249`), so physical seed identity can be aligned. Yet the
captured role census omits the full per-expression FPS indices and gradient
vectors; its 44 pairs do not prove an actual shared-parameter conflict.
Two selected wrong-context failures are not a population benefit estimate.

## 5. Design Rationale
The direct role-positive/negative contrast is already object-text contrastive
supervision (ConcreteNet original audited in
`referent_exclusivity_source_audit_20260917-2213.json`); generic conflicting
gradient projection is PCGrad (Yu et al., NeurIPS 2020). A task-specific
coupling cannot claim novelty merely from restricting those algorithms to
same-scene instances. We therefore permit a *diagnostic-only* native
shared-feature gradient conflict census, with an instance-matched placebo,
before any training design is considered.

## 6. Next Batch
See `pipeline/designs/exp_design_20260927-0300.md`. Do not implement a
training package, commit, sync or enqueue until the mechanism is independent
of these closed/prior-art families and all six executable gates pass.
