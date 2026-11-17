# M95 Contact-Geometry Control Preregistration

Stable ID `m95-contact-support-relation`; read-only native TRAIN diagnostic.
Freeze the strict anchor audit SHA256
`3b6fec07b3f578ac4a828796af613f945c6751b23c37510c285b10805a57c81b`
and 256-row manifest SHA256
`4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`.
Evaluate only the four ambiguous expressions with a unique graph-subject
`object_id` (three failures, one success); do not add posthoc matches.

Bind object IDs to native `scene*_refer.pth` instance labels and verify
the target and anchor have points. For each same-class target/peer candidate,
compute the minimum point-to-point Euclidean distance to the *same* anchor
from a deterministic maximum 2048 evenly indexed points per instance.
For `under`/`below` also report center-z difference (anchor minus
candidate); for `on top of` report candidate minus anchor. `against`
is treated as distance only. No learned weights or geometric threshold.
The primary descriptive check asks whether target distance is strictly
smaller than every same-class peer and the relevant z sign is positive.
The negative control rolls the anchor ID among the other non-target
instances in that scene in sorted order (first available), leaving the
candidate instances and phrases unchanged. Report candidate count, ranks
and control results per row, without choosing a winner posthoc.

This four-row, anchor-resolvable subset cannot establish population
benefit or an independent relation mechanism even if all target ranks
are correct. No training admission follows without broader deployable
anchor resolution, matched native intervention, backward, resources,
independence and goal checks. Failure to separate target from peers
disconfirms this strict named-anchor/contact-distance realization.
