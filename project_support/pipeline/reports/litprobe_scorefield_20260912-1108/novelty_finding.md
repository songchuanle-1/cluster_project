================================================================================
  N1 Novelty Finding - cluster_project
  Candidate class: candidate-specific score field / discrimination path
  Tick #20260912-1108, 2026-09-12 11:08
================================================================================

## 1. What Was Checked

The measured residual is wrong-instance selection among physically distinct
same-category candidates. The deployed M95 selection score is query-only:

    z_q = indis_embedding(u_q)
    m_{q,n} = u_q dot f_n
    q_hat = argmax softmax(indis)[:,1]

The score path does not read the candidate mask, while the candidate mask is
computed from a separate head. Simple mask-conditioned reranking, quality-head
reranking, language/support reranking, plain competition losses, and
hierarchy-derived competitor sets have already been screened or measured.

This pass asked whether the broader class of "candidate-specific score field"
mechanisms is already occupied by established 3D visual grounding designs.

Method: read-only OpenAlex search API queries in
`pipeline/headless/n1_scorefield_litprobe_20260912-1108.py`; raw records are in
`openalex_probe.json`. This is an abstract-level boundary screen, not full-text
verification and not a novelty approval.

## 2. Closest Prior Art

| Source | Established mechanism | Consequence for this project |
|--------|-----------------------|------------------------------|
| InstanceRefer, ICCV 2021, DOI 10.1109/ICCV48922.2021.00181 | Recasts 3D grounding as grounding-by-matching over instance candidates, with multi-level contextual inference for each candidate. | A new "candidate-specific matching score with multi-scale context" is not distinct at the problem-framing level. |
| LanguageRefer, 2021, DOI 10.48550/arXiv.2107.03438 | Predicts the target from a bounded set of object candidates using spatial and language embeddings. | Candidate classification over same-scene objects is standard, so a renamed target classifier is insufficient. |
| HAM, 2022, DOI 10.48550/arXiv.2210.12513 | Learns multi-granular point-language alignment with context modulation across local and global fields. | Additional multi-granular visual-language alignment is already an established mechanism family. |
| 3D-SPS, 2022, DOI 10.48550/arXiv.2204.06272 | Uses progressive referred-point selection rather than an isolated detector-plus-matcher score. | Progressive candidate refinement is established and cannot be claimed as this project's core novelty. |
| LIBA, AAAI 2025, DOI 10.1609/aaai.v39i8.32875 | Builds a language-instructed multi-granularity bridge for 3D vision-language alignment. | The unresolved multi-granularity coupling must have a stronger distinction than a bilateral alignment adapter. |
| TransRefer3D, 2021, DOI 10.1145/3474085.3475397 | Explicitly models entity and relation information to distinguish same-category distractors. | Same-category distractor discrimination is already published as task framing in 3D VG. |
| GuideGround, 2026, OpenAlex W7172557765 | Uses VLM semantic enhancement and viewpoint-specific hypothesis verification to complement a grounding model. | Generic external semantic verification is also occupied; it is not an admitted route here. |

## 3. Finding

No candidate-specific score-field derivation is admitted this tick. The broad
directions of candidate matching, progressive candidate selection,
multi-granular vision-language alignment, same-category distractor reasoning,
and hypothesis verification are already represented in primary 3D grounding
literature. A proposal that merely adds candidate-conditioned context, mask
evidence, or another hierarchical alignment path would duplicate that space.

The result is a negative boundary screen, not a claim that all possible
score-field mechanisms are known. It prevents rebranding an established
grounding/matching operator as the new core contribution.

## 4. What Remains Unresolved

The measured problem remains narrow:

- 99/111 M95 recoverable failures contain a usable positive candidate.
- 97/111 have an available usable positive with an opposing score-level
  corrective signal under the current `indis` objective.
- The wrong selected and oracle candidates are usually disjoint physical
  instances; the wrong candidate wins by a large margin.
- Existing readout changes do not recover the oracle, and the established
  candidate-matching/multi-granularity families cannot be renamed as novelty.

An admissible continuation must derive a new score-formation mechanism from
observed supervision and information access, then state an exact distinction
from InstanceRefer, LanguageRefer, HAM, 3D-SPS, LIBA, TransRefer3D, and standard
mask-scoring or ranking losses. No such derivation currently exists.

## 5. Limits

- Abstract/metadata-level OpenAlex screen only; full texts and supplementary
  material were not verified in this tick.
- Absence of a direct exact-equation match is not evidence of novelty.
- No model, config, checkpoint, queue, scheduler, deployment, or training
  artifact changed.
- No test data was used; all conclusions remain bounded by the frozen
  validation-derived diagnostics.

================================================================================
  Status: NEGATIVE SCREEN - no candidate-specific score-field admission
  Created: 2026-09-12 11:08 +08:00
================================================================================
