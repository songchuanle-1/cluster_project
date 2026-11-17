# Cross-scale redundancy failure screen

Stable ID: `m95-cross-scale-evidence-redundancy`. Frozen M95
`pipeline/reports/cluster_scale_necessity_20260916.json`, SHA256
`fb330f24710a12b3aecb244c0a58246ec455b39495f95acaadb2cd6138c1b342`.
The fixed 16 TRAIN batches cover 123 expressions in 32 scenes.
No validation data, new forward, or threshold selection.

Join base, scale-drop and target-superpoint duplication records by
(step, scene, expression_slot), fail on missing or duplicate keys.
Undefined cosine from an empty target-superpoint support is missing,
not zero; report missing counts and calculate each metric on observed
rows/scenes only.
Outcome is base selected mask IoU <= 0.5; compare cosine L1/L2
between failed and successful expressions with scene as the unit.
Within scenes that contain both outcomes, report the paired
failure-minus-success difference. Also report L0/L1 and L0/L2
as predeclared controls, and the absolute base-to-drop IoU delta
for each scale by outcome. Use the fixed baseline/three-drop same-forward
control; do not tune a threshold or select a scale by observed gain.

Hypothesis: redundant L1/L2 evidence is enriched on failure scenes
and a matched scale removal changes failure masks more than successful
masks. Falsifier: no coherent enrichment or negligible matched
response. A descriptive association alone cannot pass the native
mechanism control, backward, resources or independence gates.
Any new candidate requires a distinct information path rather than
reweighting or deleting a scale.
