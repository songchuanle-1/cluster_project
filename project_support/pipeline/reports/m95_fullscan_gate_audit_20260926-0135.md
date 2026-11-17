# M95 Full-Scan Gate Audit

## Contract and result

The unchanged composite producer `206c594d` completed its full TRAIN scan
on server-6 GPU7. Its 256-row capture SHA256 is `9271ea8e`; the manifest
is `4ad801fe` and checkpoint `fe5e4a5f`. The original frozen postprocessor
validated the capture and ran all three analyzers, then failed the strict
reference comparison at its original tolerances: 26 mismatches across 65
paired rows, maximum query-score delta 3.0100e-6 and IoU delta 0.02299.
The first reported mismatch is row 24 score (1.0133e-6); the first
substantive mask-support mismatch is row 83/query 103/point 169.
No selected query or selected IoU changed among 256 rows.

## Boundary and controls

- The two full scans have equal recorded native-input hashes for all 256 rows.
  Entry FPS indices differ at rows 4, 41, 173, 177, 211 and 214; hierarchy
  positions differ on all 256 and level-0 assignments on six. These are
  full-scan observations, not proof of a unique upstream cause.
- At rows 83 and 174, entry FPS indices and all three assignment levels
  match, but hierarchy positions and child maps differ. Raw 3D feature
  maximum deltas are 5.01e-6 and 5.72e-6, respectively; raw 2D is identical.
  Row 83/query 103/point 169 crosses the zero mask-logit threshold from
  -2.37e-7 to +7.61e-6 and adds one non-target point. Row 174 has no
  changed masks in this full-scan pair.
- A separately transformed fixed TRAIN item for each of rows 83 and 174
  produced 128/128 distinct GPU scatter coordinate hashes, versus 1/128
  on CPU. Maximum within-GPU coordinate deltas were 6.91e-6 and 5.25e-6.
  Native FPS output was identical in all 128 repeats per row. Four new
  transforms per row had four distinct native-input hashes and none matched
  either frozen full-scan item. This control cannot be causally assigned to
  the row 83 mask flip.
- Six full-scan FPS-changing rows have zero query-IoU changes and only one
  row with a query-score delta above 1e-6. The sole query-IoU drift row
  (83) has unchanged FPS and unchanged assignments. The fresh component
  counterfactual has zero changed mask pairs and zero measured harm on
  256 expressions/220 scenes.
- A new fixed-item native M95 replay used the exact checkpoint/config/model
  source, holding one transformed batch in memory for four forwards per arm.
  CPU-only coordinate aggregation stabilized the coordinate hash but not
  raw 3D features. Moving all network `scatter_mean` calls to CPU made
  raw 3D, projected 3D and fused features byte-stable. Final encoder
  features and query logits still differed in all four repeats. Query masks
  and selected queries were unchanged for rows 83 and 174. This isolates
  at least two numeric paths; it does not bind either replayed item to the
  historical full-scan item or causally repair the strict gate.
- In the row-83 all-scatter CPU arm, encoder inputs and outputs for layers
  0-4 are byte-stable across four repeats. Layer 5 input is byte-stable,
  but its output has four hashes. The first remaining observed variation
  is inside the final encoder layer; the internal operation is unisolated.
- A final-layer hook found stable `lla` and `lia` outputs and four distinct
  `ila` outputs under the CPU-scatter arm. The cluster module returned a
  structured object that the hook did not hash; its message and the exact
  `ila` inputs remain unmeasured. This is an observed boundary, not a
  causal attribution to `ila`.

## Disposition

The strict reproducibility gate is **failed**, not relaxed. This audit
narrows the observed result to small numeric and boundary differences;
it does not demonstrate a causal remedy or a novel structural mechanism.
The closed selector/ranking, mask matching, PIRS, relation, duplicate,
and multiscale variants cannot be readmitted on these results. There is
no candidate backward/resource/independence receipt, queue mutation, sync,
or model training. The two slots remain empty.

The next executable diagnostic is a fixed-batch native trace of layer-5
cluster message and both `ila` input tensors under the all-scatter CPU arm,
then a matched-input intervention if an operand varies. Separately bind
a transformed item to the frozen full-scan item
before attributing the historical row-83 flip; new dataset reads produced
distinct item hashes. Recheck GPU7 occupancy and memory before native work.
Neither diagnostic admits a model.

## Evidence

- `pipeline/reports/m95_postprocess_20260926-0113.json` SHA256 `4f5af1ce`.
- `pipeline/reports/m95_reproducibility_20260926-0113.json` SHA256 `6c5f0d38`.
- `pipeline/reports/m95_fullscan_boundary_20260926-0123.json` SHA256 `177619ba`.
- `pipeline/reports/m95_fullscan_census_20260926-0126.json` SHA256 `7ba1234f`.
- `pipeline/reports/m95_fullscan_score_drift_20260926-0129.json` SHA256 `a075a97e`.
- `pipeline/reports/m95_scatter_fps_rows83_174_20260926-0132.json` SHA256 `8d2aad9f`.
- `pipeline/reports/m95_boundary_item_fingerprint_20260926-0137.json` SHA256 `83c70c76`.
- `pipeline/reports/m95_fixed_batch_fused_row83_20260926-0200.json` SHA256 `1bc64352`.
- `pipeline/reports/m95_fixed_batch_all_scatter_row174_20260926-0159.json` SHA256 `8902f663`.
- `pipeline/reports/m95_fixed_batch_encoder_row83_20260926-0203.json` SHA256 `874b8076`.
- `pipeline/reports/m95_fixed_batch_internal_row83_20260926-0205.json` SHA256 `323b0850`.
- Local focused score/census tests: 4/4 passed.
