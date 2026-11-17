# M95 Upstream Parameter-Group Coupling Audit

Date: 2026-09-12. Read-only gradient audit on 284 frozen banks.

## Question

Do top-level upstream parameter groups contain a systematic direction
that jointly improves oracle selection and oracle mask quality?

## Parameter-Gradient Cosine By Group

| Group | Recoverable mean | Recoverable median | Negative fraction | Success mean |
|---|---:|---:|---:|---:|
| dec_shared | 0.09340 | 0.07746 | 0.4037 | -0.02275 |
| decoder_layers | 0.02061 | 0.02174 | 0.3853 | -0.00079 |
| input_conv | 0.00000 | 0.00000 | 0.0000 | 0.00000 |
| output_layer | 0.09135 | 0.14587 | 0.3853 | -0.00043 |
| unet | 0.09198 | 0.12215 | 0.4128 | -0.00531 |

`input_conv` is listed for completeness but has zero gradients in this
inference path, so it carries no signal.

## Scene Bootstrap

The 284 banks come from 71 physical scenes and are not independent. For the
50 scenes containing both recoverable and success banks, a paired
scene-level bootstrap (10,000 resamples, seed 1999) gives the following
descriptive 95% intervals for the recoverable-minus-success mean cosine:

| Group | Delta mean | 95% low | 95% high | Delta positive fraction |
|---|---:|---:|---:|---:|
| dec_shared | 0.11784 | -0.00037 | 0.23328 | 0.12000 |
| decoder_layers | 0.03105 | -0.00281 | 0.06496 | 0.13667 |
| output_layer | 0.08899 | -0.05360 | 0.22744 | 0.07333 |
| unet | 0.09403 | -0.03998 | 0.22374 | 0.08667 |

Every interval includes zero. `dec_shared` is closest to a positive
recoverable-specific shift, but the bank-level distributions still have wide
tails and roughly 40% negative observations in the recoverable subset.

## Interpretation

- Positive cosine means the two objectives push a group in compatible
  directions on the frozen bank.
- Gradient norms are reported in `result.json`; a cosine without
  the corresponding norms is not interpreted as a mechanism.
- `dec_shared`, `unet`, and `output_layer` show a weak recoverable-specific
  positive shift, but scene-level uncertainty and overlapping distributions
  prevent a robust joint-direction claim.
- This is a diagnostic of the current checkpoint, not a causal
  training result or an admission of a new mechanism.

## Limitation

Groups share upstream paths, success banks are controls rather than
independent samples, and the bank set is validation-derived and previously
mined. The result cannot authorize training or label a parameter direction as
a novel contribution.
