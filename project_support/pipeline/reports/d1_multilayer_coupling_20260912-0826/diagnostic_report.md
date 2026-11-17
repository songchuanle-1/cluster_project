# M95 Multilayer Decoder Coupling Audit

Date: 2026-09-12. Read-only audit on 284 frozen diagnostic banks.

## Question

Do oracle-selection and oracle-mask objectives conflict in the
parameter directions of earlier decoder layers, or only at the final
decoder layer?

## Parameter-Gradient Cosine By Layer

| Layer | Recoverable mean | Recoverable median | Recoverable negative | Success mean |
|---:|---:|---:|---:|---:|
| 0 | 0.01925 | 0.02829 | 0.3670 | -0.01009 |
| 1 | 0.02928 | 0.02438 | 0.3761 | 0.01655 |
| 2 | 0.01126 | 0.01963 | 0.3945 | 0.01097 |
| 3 | 0.01106 | 0.00667 | 0.4404 | 0.01953 |
| 4 | 0.00801 | 0.00742 | 0.4312 | 0.01699 |
| 5 | 0.00796 | 0.00679 | 0.4037 | 0.01294 |

## Interpretation

- A positive cosine means the two local objectives push the layer
  parameters in compatible directions on the frozen bank.
- A near-zero or negative cosine means the simple mask-conditioned
  coupling is not supported by the current local optimization
  geometry.
- This is a diagnostic of the current checkpoint, not a causal
  training result or an admission of a new mechanism.

## Limitation

The per-layer direction is local to decoder-layer parameters and
does not include encoder or backbone parameters. Success banks are
controls, not independent test samples. The bank set is
validation-derived and previously mined.
