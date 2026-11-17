# Assignment Label Provenance Audit
Completed 2026-09-13T06:11:10.309834 Asia/Shanghai.

## Question And Inputs
Does the frozen positive-label / IoU-failure case follow the existing assignment?
Rechecked assignment/protocol link, all five code hashes, casebook and three
upstream hashes, plus both frozen summary hashes. No inference or training.
Assignment SHA256: 9442824e45979fa3891895a90edf7b993d666463773a72dd3e9fbd6b73c8aadd.

## Source Definition
Baseline and M95 match_sampled_ins have identical ASTs. For a single target,
positive queries are the union of queries whose sampled superpoint label equals
the target instance ID and the spatially nearest query to the target centroid.
The assignment function does not take predicted masks or mask IoUs as inputs.
loss_indi uses those matched indices; inference selects maximum class-1
probability. Label membership therefore does not guarantee mask IoU success.
References: Cluster\framework\model\Quard_model\model_base1\loss.py:350;
baseline loss.py:182 and network.py:188. Full source hashes in protocol.json.

## Offline Results
All 568 unique assignment records satisfy union(target-membership, nearest).
All 42 casebook records match stored assignment labels and measured IoUs;
zero missing or duplicate assignment identities. The discordant fixture:
```json
{
  "identity": [
    "baseline",
    "scene0208_00",
    "0",
    "20"
  ],
  "selected_index": 4,
  "selected_seed_label": 0.0,
  "nearest_index": 93,
  "target": 0,
  "positive_from_membership": true,
  "positive_from_nearest": false,
  "selected_iou": 0.4826813042163849,
  "oracle_iou": 0.5549939870834351
}
```
This is source-consistent label construction, not evidence of a parser defect.

## Limits And Next Evidence
This reconstructs existing evaluation-bank labels, not historical training
targets, independent ground truth, or causal efficacy. The 42 selected cases
are not population evidence; the 568 rows belong to the existing diagnostic
protocol, not a new validation sample. No new mechanism or novelty established.
Next mechanism work still needs a derived forward/loss, original-source
distinction and matched falsifiable controls; do not replace labels on this basis.
