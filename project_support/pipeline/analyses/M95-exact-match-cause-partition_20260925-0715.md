# M95 Exact Match-Cause Partition

## Question

Does the oracle advantage of selecting inside the native target-positive set
come specifically from target-instance nearest or membership causes?

## Native Evidence

The exact full-train capture finished with `256` rows, `220` scenes, complete
manifest and checkpoint bindings, and capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`.
The fail-closed postprocess validated capture shape, completion flags,
producer, manifest, and artifacts. Its strict cross-analysis reproducibility
receipt is `failed`: `28/65` paired rows differ, with maximum IoU delta
`0.0294118` and score delta `5.8651e-5`. The cause partition uses the
validated immutable capture and does not inherit a positive reproducibility
claim.

The partition evaluated all `256` expressions:

| Selector | Available | Scene-balanced IoU |
|---|---:|---:|
| Deployed | `256` | `0.67641` |
| All native positive | `256` | `0.77869` |
| Target positive | `215` | `0.78287` |
| Target nearest | `31` | `0.84826` |
| Target member | `207` | `0.77586` |

On the `215` expressions where target-positive queries exist, target-positive
selection is worse than all-native-positive selection by `-0.00545`
scene-balanced IoU, 95% CI `[-0.01069,-0.00123]`. All-native-positive
improves over deployed by `+0.10229`, 95% CI `[+0.06870,+0.13806]`.

## Conclusion

Target-instance binding is not the source of the all-native-positive oracle
advantage. Excluding other-object positive queries materially removes useful
choices. The previous `referent-supervision-axis` formulation is rejected.

The result is oracle diagnostic evidence only. It does not establish a
deployable selector, mechanism, resource result, native-backward result,
novelty, or admission.

## Evidence

- `pipeline/reports/m95_exact_match_cause_partition_20260925-0715.json`
  `sha256=dc37eccc36a6903075ba26952f2be2ef664f728424101f2eb7960718b1de5bef`
- `scripts/m95_exact_match_cause_partition_20260925.py`
  `sha256=07e8717505f1e4daca2cd1b6d9487b67d4469d286aeb55917d8d64fdce6220c4`
- `scripts/test_m95_exact_match_cause_partition_20260925.py`
  `sha256=14669d0198c33a1af182bdd00cbef9bf19963899fcc7a1c38cb2388b80e2e7bf`
- `pipeline/reports/m95_exact_capture_postprocess_receipt_20260925-0605.json`
  `sha256=1f284a157b89ee57db0cb78ffb95f5a1714eb23fcdc7a2f157837390e053e64e`
