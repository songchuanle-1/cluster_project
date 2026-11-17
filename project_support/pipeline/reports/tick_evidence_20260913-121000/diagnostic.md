# Acceptable-Candidate Multiplicity Audit
Completed 2026-09-13T12:10:41.515579 Asia/Shanghai.

## Question And Protocol
For each of 284 paired descriptions across 71 scenes (four per scene), count
candidate masks with IoU strictly greater than .5 in each frozen 128-mask bank.
Threshold inherited from prior success diagnostics, not tuned here.
Report zero, exactly one, and multiple acceptable masks; retain the full count
histogram and all 568 model-description rows in audit.json.
No missing/duplicate description IDs. Assignment/protocol, five source-code
hashes and two upstream summary hashes match. All candidate ranges/maxima pass.

## Results
| Model | Acceptable candidates | Records | Selected success | Selected failure |
|-------|-----------------------|---------|------------------|------------------|
| baseline | multiple | 255 | 171 | 84 |
| baseline | zero | 23 | 0 | 23 |
| baseline | one | 6 | 0 | 6 |
| m95 | multiple | 259 | 158 | 101 |
| m95 | zero | 15 | 0 | 15 |
| m95 | one | 10 | 0 | 10 |

## Interpretation And Limits
Multiplicity counts masks, not distinct physical objects: overlapping predictions
may cover the same target. A failure despite multiple acceptable candidates is
not explained by only one acceptable mask being available, but does not identify
why the selector failed. This is a descriptive audit of a selected validation
bank, not population performance, causal intervention or an independent test.
Masks differ across models; counts cannot isolate selector quality. Oracle labels
are diagnostic only, not deployable inputs. No training-label repair, novelty,
significance or new scientifically admitted mechanism follows from these counts.
