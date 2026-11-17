# M95 Query-State Parameter-Coupling Audit

Date: 2026-09-12 03:15. Read-only, CPU-only diagnostic on 284 frozen M95
banks.

## Question

The static score-coupling audit established that the deployed selection score
does not read the candidate mask. Does the frozen checkpoint show a useful
local coupling between the oracle-supervised selection objective and the
oracle-mask objective on the shared decoder query state, or are they effectively
independent?

## Protocol

- Capture:
  `/tmp/cluster_semantic_projection_20260912/full`; 284/284 banks.
- Preserved capture:
  `pipeline/reports/d1_semantic_projection_20260912-0007/`.
- Capture summary SHA-256:
  `17ea5448f1d3021d634a36eeeaf78dd20db362a9c624cc83a1e9e1ec4956155c`.
- Worker:
  `pipeline/headless/d1_parameter_coupling_20260912.py`;
  SHA-256 `381210b1bb80b68ad0c817d42c3717c6c1d4770c81778dee0452bc29c2ebc627`.
- Result:
  `pipeline/reports/d1_parameter_coupling_20260912-0307/result.json`;
  SHA-256 `de1f2559b959a9c806c1e66847d906b520412d090c58644636f81e85e4734bd1`.
- Checkpoint SHA-256:
  `fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`.
- Final decoder layer: index 5.

The reconstructed forward is checked against every captured bank:
`mask RMSE = 0.004354`, maximum mask error `= 0.045502`, and maximum
`indis` error `= 0.002448`. The differences are consistent with capture-time
float16 storage; the worker uses float32 reconstruction.

For each bank, let `q_i` be the final decoder query for candidate `i`. The
deployed binary selection head is `z_i = indis(q_i)`, and the candidate mask
logits are `m_i = LayerNorm(q_i) F^T`. The audit computes:

    L_sel = CE(z, onehot(oracle))
    L_mask_oracle = BCE(m_oracle, GT) + Dice(m_oracle, GT)

at the frozen query state. It then measures the cosine between the selection
gradient and the mask-improvement direction for the selected and oracle
candidates. This is an exact local Jacobian of the final head objectives with
respect to `q`; it does not propagate through the upstream decoder.

## Findings

The score and mask heads have no shared trainable parameter inside the final
prediction head. The score parameters are
`dec.decoder_layers.5.indi_embedding.*`; the mask path uses
`dec.decoder_layers.5.out_norm.*` and the decoder query/instance features.
Coupling can therefore enter only through the shared query representation or
upstream parameters.

On the 109 recoverable banks, the selected wrong candidate has mean
selection margin `3.081` versus mean oracle margin `-1.911`; the selected
candidate is not a near-tie. The local gradient alignment is weak:

| Comparison | Mean cosine | Median | Positive fraction | Fraction < -0.1 |
|---|---:|---:|---:|---:|
| selected-to-oracle selection grad vs oracle-mask improve | 0.0148 | 0.0118 | 53.2% | 9.2% |
| selected-to-selected selection grad vs selected-mask improve | 0.0443 | 0.0456 | 77.1% | 6.4% |
| oracle-to-oracle selection grad vs oracle-mask improve | 0.0074 | 0.0119 | 59.6% | 0.0% |

The corresponding 145 success banks show the same near-orthogonality: the
selected-to-oracle and oracle-to-oracle alignments are `0.0043` and `-0.0054`
mean cosine respectively.

## Interpretation

The frozen checkpoint does not exhibit a strong local synergy in which an
oracle-supervised selection update systematically improves the oracle mask
through the shared query state. The observed recoverable errors are large
score errors on the wrong candidate, and the head-level objectives are close
to orthogonal at the captured state. This does not measure upstream decoder
parameter coupling and is not evidence that a mask-conditioned selector would
fail.

The result closes the bounded local query-state check only. A simple
mask-conditioned score head remains the standard null explanation and still
requires primary-source comparison. A full parameter-level Jacobian would
require a separately specified, bounded capture/audit that propagates through
the decoder, with explicit controls and resource accounting.

## Decision

Close the local query-state coupling audit: record the weak alignment result,
make no model/config/checkpoint/queue change, and do not enqueue a simple
mask-conditioned selector. Continue Phase 1 with a primary-source-distinct N1
derivation or a separately admitted full parameter-Jacobian protocol.
