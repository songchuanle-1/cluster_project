================================================================================
  LMEC Novelty Comparison (N1) - cluster_project
  2026-09-11 19:07 +08:00
================================================================================

## 1. Scope

This is the N1 admission gate for the candidate mechanism language-mask
evidence calibration (LMEC). It compares LMEC against the four primary sources
selected in `pipeline/designs/exp_design_20260911-1818.md`, using full extracted
LaTeX, not abstracts. Source hashes are in `source_manifest.json`.

LMEC as proposed in the review and design documents:

    m_qn = sigmoid(mask_logits[q, n])
    v_q^+ = sum_n m_qn f_n / (sum_n m_qn + eps)
    v_q^- = sum_n (1 - m_qn) f_n / (sum_n (1 - m_qn) + eps)
    e_q = g(v_q^+, l) - g(v_q^-, l)
    s_q = u_q + lambda * e_q

`u_q` is the existing candidate unary classifier logit, `f_n` are scene point
features, `l` is the sentence feature, and `g` is a learned scoring function.
The term `e_q` is meant to measure candidate-specific support-versus-complement
evidence, and `s_q` is a proposed re-ranking score.

## 2. Source Structures

### 2.1 arXiv 2411.03405 (AsphaltNet)

Equation for the offset loss:

    L_o = sum_i L2(o_i, c_i - c_gt)

`o_i` is a predicted per-instance offset vector, `c_i` the instance centroid,
`c_gt` the referred centroid. Added as an auxiliary loss after each fusion
block. Equation for the span loss:

    L_sp = H^1(l, l_hat)

with `l` the ground-truth word span and `l_hat` the predicted span logits. Both
are supervision terms, not candidate scores at inference.

### 2.2 arXiv 2506.14238 (UniSpace-3D)

Language-guided query selection:

    O = Top_{N_q}( Max^{-1}( X_v X_t^T ) )

`X_v` are visual queries, `X_t` language queries. Positive contrastive loss:

    L_pos = (L_c^{T->V} + L_c^{V->T}) / 2

Negative contrastive terms `L_p` (scene contrast) and `L_t` (sentence contrast)
use compatibility `phi(b, w) = b * w`. Total objective:

    L = L_pos + L_sem + gamma ( L_pos + alpha L_p + beta L_t )

### 2.3 arXiv 2603.17753 (PC-CrossDiff)

Projections and split:

    Q = F_v^(4) W^Q,  K = T W^K,  V = T W^V
    Q -> [Q_1, Q_2],  K -> [K_1, K_2],  V reshaped

Dual attention kernels and differential output:

    A_1 = softmax(Q_1 K_1^T / sqrt(d_h))
    A_2 = softmax(Q_2 K_2^T / sqrt(d_h))
    DiffAttn(F_v^(4), T) = (A_1 - lambda * A_2) V

with learnable `lambda`. The same operator is reused at cluster level
(`DiffAttn(F'_v, F'_oRel)` and `DiffAttn(F'_t, F'_ctr)`) and as the
localization-aware differential attention block.

### 2.4 arXiv 2310.06214 (CoT3DRef)

Pathway and sequence attention:

    A = sigma( (R^F + O^P) F^T / sqrt(d) )

Total loss:

    L = lambda_V L_cls^V + lambda_T L_cls^T
        + lambda_ref ( L_ref^P + L_ref^COT )
        + lambda_dist L_dist

`L_dist` is an auxiliary binary classification loss separating the target from
same-class distractors. `O^T`/`O^P` are anchors and their logical order.

## 3. Variable And Access Comparison

| Axis | LMEC (candidate) | 2411.03405 | 2506.14238 | 2603.17753 | 2310.06214 |
|---|---|---|---|---|---|
| Where used | Re-rank candidate score `s_q` | Auxiliary losses only | Query selection + losses | Attention feature transform | Auxiliary losses |
| Query split source | Instance's own predicted mask `m_qn` | None | None | Learned Q/K subspaces | None |
| Positive region | Masked-in points | None | Target-object visual embedding | `A_1` attention | None |
| Complement region | Masked-out points | None | Negative sentences/scenes | `A_2` attention | Same-class distractors |
| Language use | `g(v, l)` on region features | Word-span supervision | Query/text max similarity | Text as K/V and Q | Sentence-level classes |
| Output type | Scalar evidence added to logit | Loss scalars | Selected indices + losses | Transformed features | Loss scalars |
| Inference use | Candidate re-ranking | None | Query initialization | Feature encoding | Anchor chain decoding |
| Supervision | None proposed yet (reuses GT selection) | Offset + span labels | Contrastive + position | Unified task losses | Anchor + distractor labels |
| Extra annotation | None | Word spans | Generated negatives | None | Pseudo anchor labels |

## 4. Closest-Structure Analysis

### 4.1 Against 2603.17753 (highest prior-art risk)

The literal operator shape is close: both use `A_1 - lambda A_2`, and both call
it differential attention. Two structural differences matter and must be stated
exactly rather than as a naming claim:

1. The two differential channels in 2603.17753 are learned Q/K subspaces over
   the same token set. The subtraction is a noise-canceling operation on
   attention maps, and the result is a transformed feature tensor used inside
   the encoder. LMEC's two channels are disjoint point sets defined by one
   candidate's own predicted mask: support versus complement.
2. 2603.17753's operator never produces a per-candidate scalar that is added
   to a unary classification logit. LMEC's `s_q = u_q + lambda e_q` is a score
   composition over candidates.

These differences are real, but they are refinements of a differential
attention family that 2603.17753 already occupies. Any LMEC write-up must
position itself as mask-conditioned support/complement evidence composition,
not as "differential attention for 3DVG". Presenting the `A_1 - lambda A_2`
shape as the novelty would be a rename and is rejected.

### 4.2 Against 2506.14238 (closest selection prior art)

The LGQS term `O = Top_{N_q}(Max^{-1}(X_v X_t^T))` selects queries by
visual-language similarity. That is a language-conditioned selector, so it
overlaps the goal of better candidate selection. It does not split a candidate
into support and complement regions, and it does not add an evidence scalar to
a unary logit. Overlap is at the level of the error being addressed (selection
under language), not the operator.

### 4.3 Against 2411.03405 and 2310.06214

Both add auxiliary supervision. 2411.03405 supervises geometry (offsets) and
word spans; 2310.06214 supervises an anchor chain and a distractor binary
classifier. The distractor branch in 2310.06214 is the nearest selection-
related structure, but it is a separate binary head over same-class
candidates, not a support-versus-complement feature contrast built from a
candidate's own mask.

## 5. Verdict

N1 verdict: CONDITIONAL PASS, with a narrow and explicitly limited novelty
claim.

- Not found in these four sources: a candidate score defined as
  `u_q + lambda * ( g(support_q, l) - g(complement_q, l) )`, where the split is
  produced by the candidate's own predicted mask.
- Nearest overlap: 2603.17753 differential attention. The distinction must be
  made at the level of the split source and the scalar score composition.
- Weakness: the novelty is a recombination of existing ideas (masked region
  pooling, contrastive evidence, differential subtraction, unary score
  composition). It is not a new primitive on the level of differential
  attention or CLIP-space contrast.
- Additional limitation: this check covered four sources. Masked-attention
  decoders, counterfactual/occlusion evidence scoring, and language-grounded
  region contrast should be checked before a paper-level novelty claim. Those
  were not surveyed here and are recorded as open risk.

## 6. Consequences

Passing N1 is necessary but not sufficient. The synthetic T0 probe in
`t0_lmec_analysis.md` rejects the current closed-form score for training. No
model package, config, queue entry, or trainer may be created from the current
formula.

================================================================================
  Status: N1 CONDITIONAL PASS | T0 BLOCKED | training and enqueue forbidden
================================================================================
