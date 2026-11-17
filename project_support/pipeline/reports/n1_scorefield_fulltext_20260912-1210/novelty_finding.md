================================================================================
  N1 Novelty Finding - cluster_project
  Candidate class: candidate-specific score field / candidate discrimination
  Tick #20260912-1207, 2026-09-12 12:10
================================================================================

## 1. Scope

The measured residual is wrong-instance selection among physically distinct
same-category candidates. The deployed M95 score is query-only:

    z_q = indis_embedding(u_q)
    m_{q,n} = u_q dot f_n
    q_hat = argmax softmax(indis)[:,1]

The selection score does not read the candidate mask, although mask logits are
computed by the same query-point network. The previous 11:08 OpenAlex screen
was metadata-level and left open the possibility that a concrete, equation-level
candidate-specific score field might be distinct. This pass downloaded and
extracted the closest primary sources to resolve that boundary.

## 2. Primary-Source Findings

| Source | Verified full-text mechanism | Boundary consequence |
|--------|------------------------------|----------------------|
| InstanceRefer (arXiv:2103.01128) | Uses IoU-thresholded contrastive matching, a matching loss, language/object classification, and a sigmoid instance confidence. | Candidate-specific matching plus confidence scoring is established. |
| LanguageRefer (arXiv:2107.03438) | Runs a transformer over M candidates, applies `argmax` to candidate logits, and trains the target with binary classification. | Classification/argmax over candidates is the standard formulation, not a new score field. |
| HAM (arXiv:2210.12513) | Performs hierarchical proposal-language matching, chooses the one-hot highest-IoU target, and trains matching by softmax cross-entropy. | A learned candidate-query score with IoU-derived supervision is directly occupied. |
| 3D-SPS (arXiv:2204.06272) | Progressively selects language-relevant candidates and predicts referring confidence with IoU-derived positive labels. | Progressive candidate selection and confidence scoring are established. |
| TransRefer3D (arXiv:2108.02388) | Explicitly models entity and relation information to separate same-category distractors and trains query classification with cross-entropy. | The stated same-category-distractor problem framing is already a published mechanism. |
| Mask Scoring R-CNN (arXiv:1903.00241) | Predicts MaskIoU from mask and RoI features and multiplies it by the classification score. | Mask-conditioned quality scoring and score composition are established. |
| Rank & Sort Loss (arXiv:2107.11669) | Ranks positives above negatives and sorts positives by continuous IoU, explicitly replacing auxiliary quality heads. | Plain ranking, continuous-IoU sorting, and quality-score supervision are established. |

The full texts were extracted to `.txt` files in this directory. The pass
therefore changes the prior metadata-level screen from inconclusive to a
negative boundary for the broad candidate-specific score-field derivation.

## 3. Decision

Close the broad candidate-specific score-field derivation as a negative
novelty screen. Add no candidate-conditioned reranker, mask-quality score,
candidate classifier, progressive score, competitor ranking loss, or renamed
combination of those operators.

This does not claim that every possible scoring equation is known. It establishes
that generic candidate matching, mask-conditioned quality, IoU sorting, and
same-category competition cannot be the core contribution. Preserve the existing
FIFO unchanged: M191-MQSD-TR followed by M193-MQHC-TR.

## 4. Admission Gate For Any Continuation

A later proposal must start from a newly measured error or an exact,
non-equivalent distinction from all seven sources above. It must specify the
new variables, supervision, equation, gradients, degeneracies, matched controls,
and a pre-registered rejection condition before it can receive a design review
or queue entry. An abstract claim of "candidate-specific" or "mask-aware"
scoring is insufficient.

No model, config, checkpoint, queue, scheduler, deployment, or training artifact
changed during this screen.

## 5. Artifact Hashes

| Artifact | SHA-256 |
|----------|---------|
| instancerefer_2103.01128.pdf | 4726413D4E51E2EAFBFE3E458E40E5808F402CBBBE243FB01F6307C8E9EF1568 |
| instancerefer_2103.01128.txt | 9134D9751B4F0658D65240E1772C6F7D5459C7EAFB4A2FAFE45C57BEA706032C |
| languageRefer_2107.03438.pdf | 0ED46A905DE4D7D5BF4BB3B2B1FB6D3CFA14A787EF9DAFFD14019860144F20C5 |
| languageRefer_2107.03438.txt | CAFAA0135CE29A9F4B0734FA9A890E8497FB29BE076C931544B09EDEF6D9AC8F |
| ham_2210.12513.pdf | 1EF71A6F25968471659296826E4A407D3C687B9D718BF53BEA0D8BA8ADC9A39A |
| ham_2210.12513.txt | C79B5AC4595D5CDAA5DEF784E8AE51EC3073562A5356DB6F2594D36D72998840 |
| sps3d_2204.06272.pdf | 805B8DDB3AA69F800868E88BDA9565EC9CBF275C1D96FA26C9B088B2DF870B52 |
| sps3d_2204.06272.txt | 7CB1C105E1864CAE15EC01ACC52C9CF8AC822A74BD5E7C87558AD29E29AEBB22 |
| transrefer3d_2108.02388.pdf | F0F055F56EF92D5A651977E9E7B418350C08FD563AAA9513D30AF5AF7C62038D |
| transrefer3d_2108.02388.txt | C50C9CA7F44A38AE060C7B4D3763321652F26B5E38D72432AA94867AB5BDEE96 |
| mask_scoring_1903.00241.pdf | 87FB301A260AF6C76F4821A0298085A122289F4D16644DCBA30E9A18CD5CFD97 |
| mask_scoring_1903.00241.txt | D7734AD727C36285EC6B8AEE2B24D0842AB15D2407112567BCD119CA472A5CBA |
| rank_sort_2107.11669.pdf | B1B639736AA662810956DA25742B6A2C1BFFEF2CE633D5A452F679B70719A7D1 |
| rank_sort_2107.11669.txt | 52B88BB81EEC3B48E694B55F0EE9093DF1CE0FE51037576E756490745F167472 |

================================================================================
  Status: NEGATIVE SCREEN - no candidate-specific score-field admission
  Created: 2026-09-12 12:10 +08:00
================================================================================
