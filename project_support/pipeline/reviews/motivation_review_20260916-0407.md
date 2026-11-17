# Motivation Review - Mention Ownership
2026-09-16 04:07 Asia/Shanghai.

## 1. Goal
Authoritative pipeline/goal.json: Phase1 target .51, exact M95 .5024607181549072.
All14 constraints and11 bans unchanged; server4GPU0/1 and server6GPU7 only.
Research admission precedes capacity. No extra labels, dataset or seed sweep.

## 2. Story Status
| Hypothesis | State | Evidence | Gap |
|---|---|---|---|
| Missing attribute loss | excluded | prior native map audit | none |
| Non-target graph attributes omitted from dense maps | source-confirmed | scannetv2.py | contextual text still contains them |
| Repeated target noun receives negative supervision | measured lexical case | native semantic-logit gradients | coreference truth |
| Role-aware supervision improves grounding | untested | no optimizer step | identification and novelty |

## 3. Experiment Assessment
Fixed123TRAIN expressions, joined by scene and annotation identity.
Non-target attributes occur in44/85success,20/31confidentwrong,3/7otherfailure.
Multiple non-target entities:46/85,18/31,3/7 respectively. Zero invalid spans.
These are parser categories, not verified physical entity ownership.
Native final semantic-loss probe:18expressions have exact repeated target nouns;
8success,8confidentwrong,2otherfailure. All189 measured other-token partial
derivatives are positive. Original native loss and detached-logit probe agree
within declared1e-5 tolerance at every invocation. No optimizer step.

## 4. Gap Analysis
Examples scene0289_00/64 and scene0642_00/44 repeat the described chair/curtain
in a following sentence. But scene0110_00/7 explicitly says another trash can,
scene0420_00/98 distinguishes white and gray tables, and scene0452_00/59 says
another/different picture. Exact noun equality is not a coreference label.
Positive logit partials do not prove net shared-parameter updates or causality.
EDA original archived HTML section3.1 already handles pronoun attributes and
five component decoupling, including global contextual information.
Generic decoupling or adding attribute supervision is not a novelty claim.

## 5. Design Rationale
Narrow next question: can a role-ambiguous mention be supervised without
incorrectly repelling actual repeated target references or attracting distinct
same-class objects? Must derive a role-identifying objective, not lexical merging,
arbitrary confidence thresholds, loss weight tuning or relabeling annotations.
Shared-witness required two predicates with one anchor; this asks about target
mention ownership. The distinction defines a question, not proven novelty.
No native training admission, independent package or resource clearance exists.

## 6. Next Batch
Continue same-target-description-grounding stable work ID with ownership evidence.
Build a fixed explicit-repeat versus explicit-other control manifest from these
existing captions, retaining ambiguous cases as unknown; never use it as new
training annotation. Derive candidate objective and check primary literature.
Then native backward/resources and independent package only if scientifically
admissible. No repeat coverage or modality capture.
Decision20260916-040726_next_batch.md; native workerexit0.
