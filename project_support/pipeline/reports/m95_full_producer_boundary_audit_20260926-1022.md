# M95 Original-Order Boundary Recovery

2026-09-26 10:22 Asia/Shanghai. Candidate: `m95-repro-drift-boundary`.
The previous 09:07 scheduled tick timed out, but its server-6 GPU7
diagnostic completed at 10:06. The remote `result.json` was recovered
without restarting the process. Remote and local SHA256 match:
`0de128c44bb103ad2e3b7690e27e83b5d2f310c1e59b0087f9ddf2457dbbd742`.
The diagnostic script on both hosts matches SHA256
`514274822f78244bf9ad43523cab530f078817a2d23662ad3664b685a13c9d26`.

The full TRAIN-order loader reached row 83 at step 3137, dataset index 3799,
expression slot 6, and verified the frozen native item
`a39cfebecda7333f23c3abcf9bdd0029bee13be070305a604d195397fdbc068c`.
Checkpoint/config/model package and reference/strict artifact identities
matched the fixed-batch receipt. It selected query 2 with IoU 0, and its
query-103 point-169 logit was positive (`7.26437e-6`). The original reference
logit was negative (`-2.37107e-7`) and the strict artifact positive
(`7.61159e-6`). Raw 3D differs from reference by up to `4.53e-6` and
from strict by up to `5.96e-6`.

The original-order sparse output hash `ef0b1b70` differs from the
fixed-batch trace's stable sparse output `e466a41e` (0/16 matching records).
Feature scatter input also differs (`569fd7de` versus fixed-batch
`3c002cc7`, 0/16 matches), while p2v and superpoint index hashes match.
Thus the within-fixed-batch GPU reduction variability is not the first
established cause of the cross-context difference: its input is already
different. The historical reference has no sparse-output or scatter-input
hashes, so the first reference-versus-original-order operation cannot yet
be identified. Hash inequality does not measure effect size or prove a
particular upstream operator caused task behavior.

The unchanged strict 256-row comparator still fails 26/65 paired rows,
with no selected-query or selected-IoU change in the completed full scans.
This recovered diagnostic provides provenance and a narrower next test,
not task benefit, a trainable structural mechanism, native backward,
resource/independence evidence, or admission. No queue mutation, model
sync, training launch, or intervention on foreign processes.

Next bounded test: on the exact saved row-83 batch, capture and compare
the sparse input-conv input, coordinate/p2v ordering and first sparse
stage output under the original-order producer context and the fixed-batch
context. Include numerical distances as well as hashes and the unchanged
point-169/selected-output readout. Only inspect the next stage after the
first measured divergence; if original historical reference still lacks
upstream captures, state that attribution remains unidentifiable.
