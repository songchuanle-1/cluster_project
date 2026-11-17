# Scene-Level Frozen-Bank Error Decomposition
## Protocol
284 paired descriptions, 71 scenes, four descriptions each; zero missing or
duplicate identities. All 568 rows satisfy 0 <= selected IoU <= oracle IoU <= 1.
For each model, regret = oracle - selected. For M95 minus baseline:
delta(selected) = delta(oracle) - delta(regret). Average within each scene.
Equal scene sizes make the scene-weighted mean equal the description-weighted
mean. Verify this arithmetic identity per description and per scene.
Assignment, protocol, five source files and both summaries hash-verified.

## Results
```json
{
  "pairs": 284,
  "scenes": 71,
  "missing": 0,
  "duplicates": 0,
  "mean": {
    "selected_delta": -0.03369754213597101,
    "oracle_delta": 0.01386205621168647,
    "regret_delta": 0.04755959834765748
  },
  "signs": {
    "selected_delta": {
      "positive": 29,
      "zero": 6,
      "negative": 36
    },
    "oracle_delta": {
      "positive": 36,
      "zero": 3,
      "negative": 32
    },
    "regret_delta": {
      "positive": 42,
      "zero": 2,
      "negative": 27
    }
  },
  "better_oracle_worse_selected": 16,
  "max_identity_residual": 0.0
}
```
The 284-pair manifest and all 71 scene decompositions are in audit.json.

## Limits
This is an arithmetic decomposition of an exploratory validation-derived bank.
Oracle is not deployable. Regret is not an isolated causal selector effect:
the models have different candidate masks. Sign counts are descriptive, not
significance tests or confidence intervals; neither scene grouping nor this
identity fixes sample selection bias. No training-target repair, new efficacy,
independent generalization or novel mechanism is established.
