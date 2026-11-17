# D1 Score Coupling Static Audit

Completed 2026-09-12 01:10 Asia/Shanghai. Read-only source and artifact
inspection. No forward pass, training, checkpoint write, CUDA allocation, queue
change, config change, or new mechanism admission.

## Scope

The prior supervision audit showed that most recoverable failures already have
a usable positive candidate. The remaining question is whether the inference
selection score can see candidate-specific mask evidence.

Inputs:

- `Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/dec.py`
  SHA256 `6f7566bd02121fd218fd1360be7c7b1905c267de8a03f36473779ab4d66b9d3a`
- `Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/loss.py`
  SHA256 `c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5`
- `Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/network.py`
- one archived D1 candidate bank, used only to inspect saved fields

The frozen D1 bank schema contains `mask_logits`, `score_logits`,
`selected_probabilities`, `superpoints`, `gt_pmask`, `gt_spmask`,
`seed_indices`, `sample_indices`, `metrics`, and `candidate_ious`. It does not
contain decoder-query embeddings, head inputs, head parameters, optimizer state,
or real training gradients. A real-data head Jacobian audit therefore requires
a new bounded capture protocol; it cannot be reconstructed from the current
archives.

## Formula And Forward Path

For candidate `q` and superpoint `n`, the current implementation computes:

    u_q       = decoder query state for candidate q
    z_q       = indis_embedding(u_q)               # selection logits
    p_q       = softmax(z_q)[1]
    r_q       = out_score(u_q)                     # auxiliary quality score
    m_{q,n}   = u_q dot f_n                        # mask logits
    y_hat_qn  = sigmoid(m_{q,n})
    q_hat     = argmax_q p_q

The code confirms:

- `prediction_head(query, mask_feats, batch_mask)` ignores its `mask_feats`
  and `batch_mask` arguments for `pred_scores`; it returns
  `pred_scores = out_score(query)`.
- `pred_masks` is the only head output that uses `mask_feats`.
- `pred_indis = indi_embedding(query)` is a separate query-only head.
- `predict_by_feat` selects with `argmax softmax(pred_indis[:, 1])`.

Thus the deployed selection field is:

    S_q = phi_z(u_q)

not a mask-coupled field:

    H_q = phi_z(u_q, y_hat_q, {y_hat_r}_{r != q})

The auxiliary quality head is also query-only:

    r_q = phi_r(u_q)

It can predict a scalar during training, but inference does not read it, and it
does not consume the candidate mask.

## Supervision Path

`match_sampled_ins` assigns positive `indis` supervision from geometry:

    q0 = argmin_q ||x_q - mu_c||_2
    y_q = 1[c_q = c or q = q0]

where `x_q` is the query seed position and `c_q` is the seed's superpoint label.
The assignment is therefore based on seed location, not predicted mask
correctness.

`loss_masks` computes:

    IoU_q = IoU(sigmoid(m_q) >= 0.5, GT)

but its score target exists only for matched queries with `IoU_q > 0.5`.
The quality loss is:

    L_score = MSE(r_q, stopgrad(IoU_q))

and the mask losses supervise `m_q` for matched queries:

    L_mask = BCE(m_q, GT) + Dice(m_q, GT)

Selection supervision and mask supervision meet only through shared query
features and the shared network. The selection head itself is not required to
read the candidate mask, and the quality head is not trained on the full
candidate bank.

## Measured Discrepancy

The source contract explains why the previously measured
`Spearman(indis, IoU)` collapse on recoverable banks is possible:

- A high-quality mask can exist while its candidate has low query-only score.
- A low-quality competing mask can have high query-only score.
- Per-bank monotone transforms of `p_q` cannot change the selected candidate.
- The already-saved banks contain enough data to inspect masks and scores, but
  not enough data to measure whether real shared-parameter gradients would
  make a mask-conditioned field separable.

This is an implementation-path discrepancy, not proof that a mask-conditioned
score will remove the error. It also does not establish novelty: standard
detection, mask-scoring, query-selection, and grounding reranking methods may
already cover simple mask-conditioned score heads.

## Decision And Next Evidence

Close the static score-coupling audit. Do not enqueue a simple
mask-conditioned selector from this fact alone. The next admissible work is
one of:

1. a bounded read-only capture of decoder query, mask, and head-feature tensors
   for the frozen recoverable and success controls, followed by a real
   parameter/Jacobian coupling audit; or
2. a primary-source derivation for a structurally distinct score-formation
   mechanism that changes the score field rather than adding a scalar head.

Any proposed mechanism must still pass primary-source comparison, analytic and
finite-difference gradient checks, matched controls, degeneracy tests, and the
full-model `<=10G` resource admission before training.
