# Frozen Bank Leave-One-Scene-Out Sensitivity
## Protocol
All 284 paired descriptions, 71 scenes with four descriptions each; zero missing
or duplicate paired identities. Remove each whole scene once; calculate M95
minus baseline mean selected-IoU and success-rate differences on the remaining
280 descriptions. Success threshold strictly >.5 inherited, not tuned.
Assignment, protocol, five code files and both summaries hash-verified.
No resampling, new sampling, training, or checkpoint evaluation.

## Results
```json
{
  "pairs": 284,
  "scenes": 71,
  "full_success_delta": -0.045774647887323945,
  "full_iou_delta": -0.03369754213597101,
  "loso_success_range": [
    -0.05,
    -0.03571428571428571
  ],
  "loso_iou_range": [
    -0.037935837429748584,
    -0.028073358500842006
  ],
  "nonnegative_success_omissions": 0,
  "nonnegative_iou_omissions": 0
}
```
All 71 omissions and the paired 284-description manifest are in audit.json.

## Limits And Decision
This tests whether one scene alone reverses the sign in this selected bank.
The ranges are sensitivity ranges, NOT confidence intervals. They cannot correct
selection bias, represent full validation, prove statistical significance,
establish causality, or support independent generalization. The two models have
different candidate masks, so neither contrast isolates selector quality.
No scientifically admitted new mechanism follows. Preserve running controls.
