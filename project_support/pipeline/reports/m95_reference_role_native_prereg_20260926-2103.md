# Reference-Role Native Intervention

Stable ID `m95-reference-role-ownership`. Frozen TRAIN identities are
`scene0110_00/ann7`, `scene0416_00/ann74`, and
`scene0452_00/ann59`. Four exact role-marker positions are in
`m95_reference_role_token_feasibility_20260926-2101.json`; each permits
same-length replacement with `the`. Use the M95 checkpoint SHA256
`fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`,
native seed 1999, unchanged TRAIN dataset/model and criterion, and only
server-6 GPU7 after checking occupancy and memory.

For one marker at a time, freeze the native batch, physical
superpoint coordinates, query sampling and target mask. Run original,
marker-to-`the`, original repeat. Select a matched noun-only control
from the existing TRAIN vocabulary *before reading outputs*, requiring
same token length and changes confined to the role noun tokens. If no
control is feasible, report the absence and do not claim control PASS.
No per-row tuning of replacements or reference-object selection.

Record per expression/marker: token IDs and changed positions, input
and physical support hashes, logits and masks on the fixed 128-query
axis, selected query/IoU as a descriptive readout, relation-token LIA
attention on the bound superpoint axis, and original-versus-repeat
noise. The primary mechanism readout is marker-versus-noun-control
change in the attention distribution assigned to the role mention,
with a corresponding query-mask or score effect in the expected
referent direction. The marker is *not* proof of physical anchor ID:
all GT labels are posthoc diagnostic only. Report every row including
null and reversed effects; do not select a favorable scene.

Disconfirm on missing exact support/repeat binding, no
marker-specific change beyond noun-only/repeat, a reversed effect,
or no independently identifiable reference assignment. A positive
three-scene response cannot establish population efficacy. A
candidate still needs a genuinely distinct structural mechanism,
native backward, matched model control, resources, independent
package/config and all goal constraints before admission.
