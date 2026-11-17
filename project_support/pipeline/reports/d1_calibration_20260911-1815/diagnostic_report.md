# D1 Score Calibration And Mask-Support Audit

## Scope And Provenance

CPU-only readback of the 568 immutable candidate-bank artifacts from
`reports/d1_expansion_20260911-0715` (baseline 284, M95 284, 128 candidates
per bank). No model, checkpoint, ScanRefer sample, optimizer, or CUDA context
was loaded. The worker and independent verifier hashes are recorded in
`execution.json`; the artifact hash is in `verification.json`.

This is an exploratory diagnostic, not a causal experiment or a mechanism
claim. The worker was fixed before execution, but the protocol was recorded
after the run; it is not a preregistered intervention.

## Formula

For candidate q:

    p_q = softmax(indis_q)[1]
    IoU_q = IoU(sigmoid(mask_logits_q) >= .5, GT)
    q_sel = argmax_q p_q
    q_oracle = argmax_q IoU_q

The measured rank agreement is `Spearman(p, IoU)`. The top-k diagnostic asks
whether `q_oracle` appears in the highest-score five candidates. Soft and
binary mask-support summaries are

    A_soft(q) = mean_n sigmoid(mask_logits[q,n])
    A_bin(q) = mean_n 1[sigmoid(mask_logits[q,n]) >= .5]

An equal rank-sum fusion of `p_q` and `A_bin(q)` was evaluated only as a
descriptive complementarity probe.

## Results

| Stratum | Banks | Oracle in top5 by p | Spearman(p,IoU) | Binary NDCG | Soft-area Spearman | Binary-area Spearman |
|---|---:|---:|---:|---:|---:|---:|
| baseline recoverable | 90 | 16 | .113652 | .485801 | .109732 | .118377 |
| M95 recoverable | 111 | 14 | .172253 | .492124 | .161065 | .186103 |
| baseline success | 171 | 64 | .408655 | .929669 | .314450 | .402273 |
| M95 success | 158 | 59 | .514325 | .931687 | .542701 | .616956 |
| all banks | 568 | 155 | .326115 | .763260 | .305739 | .360476 |

The oracle is outside the score top five for 74/90 baseline recoverable and
97/111 M95 recoverable banks. The score remains more informative on successful
banks than on recoverable banks.

The mask-support proxies do not repair this: on M95 recoverable banks, the
binary-area top five contains the oracle for 8/111 banks, and the equal rank
fusion contains it for 0/111. These are exploratory probes, not deployable
rerankers or evidence that mask information is useless.

## Interpretation Limits

The result supports a candidate-selection/calibration problem, not a new
mechanism. It does not prove that a mask-conditioned score will generalize,
that the saved classifier score is the only cause, or that any particular
learned evidence term is novel. It also does not measure real training
gradients, shared-parameter effects, or full-model resource cost.

The next admissible step is a primary-source and derivation review for one
selection mechanism. It must define the forward/loss graph, gradients,
degeneracies, matched controls, and preregistered rejection criteria before any
training enqueue. The existing FIFO queue remains unchanged.
