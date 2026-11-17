# Paired Scene Bootstrap - Frozen Exploratory Bank
## Protocol
284 paired identities, 71 scenes, four descriptions per scene; zero missing or
duplicate identities. Verify assignment/protocol, five source files and two
summary hashes. Resample 71 whole scenes with replacement 10,000 times using
NumPy default_rng seed1999; retain model pairing and all four descriptions.
Outcomes: selected IoU, oracle IoU, regret=oracle-selected and success IoU>.5.
Report M95 minus baseline. Equal scene sizes imply equal description weighting.
Percentile bounds use NumPy default linear quantiles at .025/.975.
Full manifest, scene means, seed/version and binary draw hash are in audit.json.
## Results
```json
{
  "selected_delta": {
    "mean": -0.03369754213597101,
    "percentile_95": [
      -0.07175225293727815,
      0.004763570895400446
    ]
  },
  "oracle_delta": {
    "mean": 0.01386205621168647,
    "percentile_95": [
      -0.0011332962438988848,
      0.030119812056999387
    ]
  },
  "regret_delta": {
    "mean": 0.04755959834765748,
    "percentile_95": [
      0.008933127216189692,
      0.08578639236216525
    ]
  },
  "success_rate_delta": {
    "mean": -0.045774647887323945,
    "percentile_95": [
      -0.09859154929577464,
      0.0035211267605633804
    ]
  }
}
```
## Correctness
All568 rows satisfy selected<=oracle; scene and bootstrap draws satisfy
selected_delta=oracle_delta-regret_delta. Pair counts and frozen hashes pass.
## Limits
These are exploratory, unadjusted marginal 95% bootstrap intervals conditional
on the empirical scene bank and a scene-exchangeability assumption. They do
not remove selection bias or establish full-validation/test generalization.
No p-values, multiplicity-adjusted inference, causal selector isolation or
mechanism efficacy claim. Candidate banks differ. Oracle is not deployable.
