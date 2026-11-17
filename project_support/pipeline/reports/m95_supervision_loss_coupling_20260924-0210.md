# M95 Supervision Loss-Coupling Audit

2026-09-24 02:10 Asia/Shanghai. Event-mode continuation of the three
stable diagnosis IDs. Source/static analysis only; no native intervention.

## Fixed Observations

- Frozen 256 TRAIN expressions: six exclusion rows (indices 11, 43, 79,
  88, 103, 253), 70 acceptable queries and zero acceptable native positives;
  seven within-positive score failures have 30 acceptable native positives.
- The six-row denominator is outcome-selected. Five rows lack a target-seed
  selector; target-seed availability is neither native matcher cause nor an
  any-instance objectness control.
- GPU7 has an external 41,996 MiB compute allocation, 42,023 MiB used,
  39,057 MiB free and 100% instantaneous utilization. No process was touched.

## Native Loss Contract

In the M95 criterion, `match_sampled_ins` makes a nearest-query assignment
per GT and adds instance-member queries after excluding *all* nearest
indices. Its `(query, GT)` pairs index GT masks, positive language maps and
the positive indicator target. `loss_indi` uses the union of matched query
indices and downweights unmatched queries by `eos_coef`. `loss_masks`
applies BCE/Dice to matched masks and an IoU-filtered score loss. The
semantic loss consumes the same `(query, GT)` pairs. Thus a positive-set
change also changes target masks, score eligibility, semantic positives and
normalization. It is not an isolated indicator-label intervention.

For a matched native-forward diagnostic, preserve the exact query features,
logits, masks, GT masks, text and seed. Record the ordered `(query, GT)` pairs
and each component's scalar, per-query contribution and gradient support:
indicator, mask BCE/Dice, score, semantic, and sample seed loss. Compare
the unchanged native objective with (a) an indicator-only target change
holding all other pairs and normalization fixed, (b) the same positive set
applied to all affected losses, (c) an any-instance objectness label and
(d) a listwise score objective over the same support. The last three are
controls, not independent candidate mechanisms or approved training runs.
No intervention is interpretable without the missing native matcher-cause
binding, and no efficacy follows from a same-forward gradient.

The source also repeats the matched pairs in auxiliary layer losses, so
the contract must report final and auxiliary contributions separately.
Compare gradient norms/directions at the same logits and parameter groups,
including no-gradient components, before attributing any signal to a
referent-specific supervision unit. Exclusion rows have no acceptable
native-positive support; within-positive rows do, but their binary label
does not rank acceptable positives against failed positives. These distinct
failure types must not be pooled into a causal estimate.

## Disposition

The existing opt-in 256-row cause/query-state producer is still the next
native step when occupancy, host, runtime, data, checkpoint and producer
provenance pass. Run the six-row cause checker and four-scene identity
controls before defining an expression-level mechanism or a matched
training intervention. No new mechanism, backward, resources, admission,
sync, enqueue or training. The two slots remain empty.

Evidence: `pipeline/reports/m95_failure_partition_20260923-0318.json`
SHA256 491492118b2f55d78c02bc023f8e1e9408bd359eb5ef2af8824faee6bff6b5ee;
`Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/loss.py`
SHA256 c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5.
