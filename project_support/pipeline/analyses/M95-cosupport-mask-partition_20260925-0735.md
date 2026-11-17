# M95 Co-Support Mask Partition

## Question

Do the other-object positives that explain the all-native-positive oracle
advantage carry independent target evidence through predicted-mask co-support?

## Method

For each exact capture row, select the highest-score native-positive query and
load its captured query mask. Classify the query as target-nearest,
target-member, or other-object positive using the native matcher cause. Measure
overlap and IoU against the target union. On rows where this choice differs
from the target-positive top-score choice, report paired scene-balanced
differences.

This is a read-only CPU diagnostic over the completed capture. It does not
train or modify the model.

## Results

| Selected cause | Rows | Success | Scene-balanced IoU | Mask IoU > 0.5 |
|---|---:|---:|---:|---:|
| Target nearest | `20` | `100.0%` | `0.83635` | `20/20` |
| Target member | `150` | `92.0%` | `0.79079` | `138/150` |
| Other-object positive | `86` | `79.1%` | `0.74094` | `68/86` |

The other-object-positive selections have scene-balanced overlap fraction
`0.78812` and scene-balanced target-mask IoU `0.74094`. On `45` rows where the
all-native-positive and target-positive top-score choices differ, all selected
queries belong to the other-object-positive class. The all-native choice
improves IoU on `10` rows and worsens it on `3`, with scene-balanced IoU delta
`+0.03053`, 95% CI `[+0.00647,+0.06147]`.

## Conclusion

The all-native-positive set contains other-object positives whose masks
already co-support the target. This explains why object-identity-only
exclusion is harmful. It does not identify a new missing model capability:
the existing score head already ranks these co-supporting queries highly.

The route is rejected before design as a renamed mask-aware-positive
assignment. RefMask3D and the existing matcher already use mask overlap and
native matching supervision, while this capture cannot show that a new loss
or information path would improve on the deployed score. No training
candidate is admitted from this descriptive result.

## Evidence

- `pipeline/reports/m95_cosupport_mask_partition_20260925-0735.json`
  `sha256=33de0624b6301188cf83e91ad1c4e72803190c647d012b0990967b12107249e9`
- `scripts/m95_cosupport_mask_partition_20260925.py`
  `sha256=6f384ab6b1133b714373842bc4e4abbe62720d36797e8a27852a89b5a8151e96`
- `scripts/test_m95_cosupport_mask_partition_20260925.py`
  `sha256=cc465851b23a967bc2d04711555d8edb46331db6533843860c331b31f0c3dcb7`
