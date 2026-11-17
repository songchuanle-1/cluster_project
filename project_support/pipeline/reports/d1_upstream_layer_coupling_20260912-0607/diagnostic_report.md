# M95 One-Layer Upstream Coupling Audit

Date: 2026-09-12 06:14. Read-only, CPU-only diagnostic on 284 frozen M95
banks. No GPU, model, config, checkpoint, queue, or training artifact changed.

## Question

The final-head audit showed near-orthogonal selection and oracle-mask
gradients at the shared decoder query. Does the preceding decoder layer
contain a systematic shared-parameter direction that jointly improves
oracle-selection and mask quality, or is the conflict already present one
layer upstream?

## Protocol

- Capture: `/tmp/cluster_semantic_projection_20260912/full`; 284/284 banks.
- Preserved capture:
  `pipeline/reports/d1_semantic_projection_20260912-0007/`.
- Capture summary SHA-256:
  `17ea5448f1d3021d634a36eeeaf78dd20db362a9c624cc83a1e9e1ec4956155c`.
- Worker:
  `pipeline/headless/d1_upstream_layer_coupling_20260912.py`;
  SHA-256 `a941d436c75b8841c4cd5bbef8588f361b044ef3267331af76eaeeb64a1c6a84`.
- Result:
  `pipeline/reports/d1_upstream_layer_coupling_20260912-0607/result.json`;
  SHA-256 `c2477041231956fd5ba8a7ccc81d82bea0fb102599aa84cfee8ca2d5912fac13`.
- Checkpoint SHA-256:
  `fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`.
- Reconstructed final decoder layer: index 5.

Let `theta` be the trainable parameters of the final decoder layer
(`qia`, `qla`, `qqa`, `qqa_ffn`, `norm_qqa`). The audit reconstructs the
layer from the frozen checkpoint, verifies its output against each captured
bank, and computes:

    L_sel  = CE(indis_logits, one-hot/oracle-target per candidate)
    L_mask = BCE(mask_logits_oracle, GT) + Dice(mask_logits_oracle, GT)

For each bank, it reports `cos(grad_theta L_sel, grad_theta L_mask)`. A
positive cosine means the two descent directions reinforce each other; a
negative cosine means they conflict. It also reports the same comparison for
the reconstructed layer input query and for each parameter group.

The reconstructed forward matched the capture within float16 storage error:
query maximum absolute error `0.006181`, mask maximum absolute error
`0.046005`, and `indis` maximum absolute error `0.002427`.

## Findings

Across all 284 banks, the shared parameter-gradient cosine is weak:
mean `0.01165`, median `0.00869`; 58.5% positive and 41.5% negative. The
query-input cosine has mean `0.00638`, with 44.0% negative.

On the 109 recoverable failures, the parameter-gradient cosine has mean
`0.00796`, median `0.00668`; 59.6% positive and 40.4% negative. The
query-input cosine has mean `0.00711` and is effectively split: 51.4%
positive, 48.6% negative.

On the 145 success controls, the parameter-gradient cosine has mean
`0.01294`, median `0.00783`; 55.2% positive and 44.8% negative. The two
subsets do not show a useful recoverability-specific coupling pattern.

The parameter-group means on recoverable banks are also weak:

| Group | Mean cosine | Median | Positive fraction | Negative fraction |
|---|---:|---:|---:|---:|
| qia | 0.00471 | 0.00840 | 55.0% | 45.0% |
| qla | 0.00046 | 0.01018 | 54.1% | 45.9% |
| qqa | 0.01774 | 0.00930 | 52.3% | 47.7% |
| qqa_ffn | 0.00927 | -0.00249 | 44.0% | 56.0% |
| norm_qqa | 0.00328 | 0.01523 | 56.9% | 43.1% |

## Interpretation

The frozen checkpoint does not contain a systematic final-layer direction
that simultaneously improves oracle selection and oracle mask quality. The
selection/mask conflict is not resolved one decoder layer upstream: the
parameter-gradient alignment remains near zero, with a substantial negative
fraction.

This closes the bounded one-layer upstream check. It does not measure the
remaining encoder layers and is not evidence that a mask-conditioned
mechanism would fail. It also does not admit one: a simple mask-conditioned
score head remains standard prior art, and the current evidence only shows
that the existing frozen objective does not align the two heads.

## Decision

Close the one-layer upstream coupling audit: record the weak alignment result,
make no model/config/checkpoint/queue change, and do not enqueue a
mask-conditioned reranker. Continue Phase 1 with either a
primary-source-distinct N1 score-field derivation or a separately specified
bounded encoder-level audit with explicit controls and resource accounting.
