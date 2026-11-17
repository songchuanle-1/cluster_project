# M95 Layerwise Candidate-Selection Audit

Date: 2026-09-12. Read-only evaluation on 284 frozen diagnostic banks.

## Question

Does recoverable candidate evidence already exist in decoder layers 0-4
and then disappear when the deployed selector uses only layer 5?

## Metrics

| Layer | Acc@50 | Selected IoU | Chance IoU | Oracle rank | Oracle top-5 | Final-oracle rank | Selects final oracle |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.4648 | 0.4471 | 0.1439 | 16.2 | 0.3592 | 26.4 | 0.0986 |
| 1 | 0.5141 | 0.4576 | 0.1782 | 16.8 | 0.3521 | 24.8 | 0.0986 |
| 2 | 0.5106 | 0.4692 | 0.2079 | 21.5 | 0.2782 | 25.0 | 0.1056 |
| 3 | 0.5246 | 0.4663 | 0.1957 | 21.6 | 0.3099 | 24.8 | 0.1021 |
| 4 | 0.5141 | 0.4635 | 0.2077 | 23.9 | 0.3028 | 24.7 | 0.0986 |
| 5 | 0.5106 | 0.4619 | 0.1854 | 24.5 | 0.2887 | 24.5 | 0.1021 |

## Final-Recoverable Subset

Count: 109. These are banks where the final selector
picked a candidate with IoU <= 0.5 while its own final-layer mask
candidate set contained a candidate with IoU > 0.5.

| Layer | Acc@50 | Selected IoU | Early valid rescue | Early final-success harm |
|---:|---:|---:|---:|---:|
| 0 | 0.0642 | 0.1201 | 0.0642 | 0.0000 |
| 1 | 0.0917 | 0.1177 | 0.0917 | 0.0000 |
| 2 | 0.0367 | 0.0935 | 0.0367 | 0.0000 |
| 3 | 0.0550 | 0.0913 | 0.0550 | 0.0000 |
| 4 | 0.0367 | 0.0865 | 0.0367 | 0.0000 |
| 5 | 0.0000 | 0.0684 | 0.0000 | 0.0000 |

## Interpretation

- At least one of decoder layers 0-4 selects a valid candidate on
  0.1651 of final-recoverable banks.
- All of decoder layers 0-4 select a valid candidate on
  0.0000 of final-recoverable banks.
- The deployed selector is the final layer. A high early-layer rescue
  rate would indicate that useful evidence is present before layer 5
  but is not preserved by the final selector.

## Limitation

Auxiliary decoder outputs are trained by the existing auxiliary loss but
are not an independently validated deployment path. This diagnostic does
not establish a new mechanism or a training-time causal effect.
