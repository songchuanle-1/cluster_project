# Motivation Review - Reconstruction Admission
2026-09-16 03:48.

## 1. Goal
Full authoritative contract:pipeline/goal.json,read this continuation.
Phase1 target .51,exact champion .5024607181549072,gap .0075392818450928.
All14constraints/11bans retained;capacity gap does not waive novelty.

## 2. Story Status
| Hypothesis | State | Evidence | Gap |
|---|---|---|---|
| Same-target grounding failures persist | observed | shared-support128TRAIN | distinct mechanism |
| Generic masked reconstruction is new | contradicted | Mask Grounding Eq4 | substantive difference |
| Relation classifier is new | contradicted | 3DWG instance relation matching | substantive difference |
| Late masking blocks full text | contradicted for proposed graph | source dependency audit | mask before encoding |

## 3. Experiment Assessment
M95 exact .5024607182,M195 .4986896217;no new terminal result.
Existing M196 unchanged. Prior mean-exchange diagnostics completed,not repeated.
Six static dependency/countermodel checks completed;no native efficacy claim.

## 4. Gap Analysis
Mask Grounding2312.12198v2 section3.2 Eq4 uses LanguageEncoder(Mask(T)),
ImageEncoder(I),MaskEncoder(M) and categorical masked token loss. Its mask signal
is GT mask center coordinates. Original PDF downloaded and read,not secondary claim.
3DWG2505.01809 instance relation matching extracts relation phrases between noun
phrases,selects proposal features and supervises relation classification.
Generic adaptation of either is not a new core contribution.
Earlier visual-only squared difference rejection does not invalidate conditional
categorical reconstruction;diverse same-object descriptions remain possible.

## 5. Design Rationale
Native network.py124 encodes full text,126 sends it to decoder;dec.py206
updates visual features using language via ila. Proposed late-mask reconstruction
on those features retains a full-text bypass. AST checks confirm the actual
source edges;finite two-token countermodel reconstructs without visual input.
This proves a possible shortcut,not learned native leakage. Existing grounding
has no such reconstruction head and is not declared buggy.
Pre-encoder masking plus image-only features removes this direct bypass but is
already part of Mask Grounding;correct implementation is not novel contribution.

## 6. Next Batch
No new model/config or experiment admission for these generic formulations.
Continue distinct conditional supervision derivation with semantic identifiability;
no renamed reconstruction,relation-classifier,ranking or feature-swap successor.
Do not repeat dependency audit or already-completed native modality interventions.
Decision20260916-034807_next_batch.md;sources and output hashed in research_work.
