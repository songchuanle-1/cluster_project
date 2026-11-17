# Same-object category contract screen

Stable ID `m95-object-category-conflict`. Freeze the exact ScanRefer TRAIN
source SHA256 and 256-row changed-producer cohort SHA256 from the earlier
data-contract screens. This is distinct from the identical-description
different-target collision screen: group annotations by `(scene_id,
object_id)` and compare their `object_name` labels.

Before reading model outcomes, normalize only case, underscores, spaces and
terminal plural `s`. Primary exposure is an object with at least two
different normalized annotation names. Retain all raw names, descriptions
and annotation IDs so synonyms and fine-grained aliases can be separated
from genuine mutually exclusive categories. Negative control is objects
with multiple annotations but one normalized name. Report all frozen
identities, 128/128 strata, failures at selected native IoU <=0.5 and
same-scene exposure-discordant pairs. Single-annotation targets are a
separate denominator, not the control.

Category-name conflict does not imply conflicting target-mask labels:
model supervision uses instance ID and graph text. Reject if labels are
aliases, no failure link exists, or no independent causal supervision unit
is affected. No variant or queue mutation follows from this audit alone.
