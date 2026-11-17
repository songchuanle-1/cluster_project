# Frozen M95 Batch Cluster Control

The unchanged TRAIN loader yielded exact native-item SHA256 matches at row
134/step 9, row 174/step 2751, and row 83/step 3137. The saved two-scene
batches for rows 83 and 174 were replayed on authorized server-6 GPU7
(0 MiB before each diagnostic), using the exact M95 checkpoint SHA256
`fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`,
config and model package. The frozen manifest bound scene and annotation
to expression slot 6 (row 83, scene0281_00/ann18) and slot 6
(row 174, scene0650_00/ann2). Four native-loss repeats were executed per
arm per item, 16 forwards each, with seed 1999 reset before each forward.

Arms were native, cluster-bank scatter on CPU only, all network scatter on
CPU, and all network plus cluster-bank scatter on CPU. The CPU moves are
reversible diagnostics, not a proposed model or training configuration.

| Frozen item | Probe query | Native mask hashes | Cluster-only CPU mask hashes | All-network CPU mask hashes | Both CPU mask hashes | Selected outcome |
|---|---:|---:|---:|---:|---:|---|
| 83 | 103 | 1/4 | 1/4 | 1/4 | 1/4 | query 2, IoU 0.0000 in all 16 |
| 174 | 87 | 2/4 | 2/4 | 1/4 | 1/4 | query 9, IoU 0.85294 in all 16 |

Row 83/query 103 has IoU 0.66667 and identical binary mask in all
16 repeats. Its pre-registered point-169 logit stays positive in every arm
and repeat (native 2.65e-6 to 7.68e-6; both CPU 5.21e-6), while the
historical strict full-scan pair crossed from -2.37e-7 to +7.61e-6 on
that non-target point. Thus this exact-item fixed-batch control does not
reproduce the historical negative logit. Exact item identity is necessary
but does not establish identical model-internal draws or the original
full-loader forward context.

Row 174/query 87 has two native binary masks: three repeats have 20
positive superpoints and IoU 0.58824; one has 21 and IoU 0.61765.
Cluster-only CPU leaves the same two-mask variability. Both all-network
CPU arms have the 21-point mask in all four repeats. No selected-mask
hash, selected query or selected IoU changes in either item across arms.
This is a numeric provenance finding on two pre-registered examples, not
population efficacy. The unchanged strict full-scan comparator remains
failed at 26/65 paired rows; no tolerance was changed.

## Direct full-scan artifact comparison

The saved batches were replayed against unchanged strict full-scan
artifact tensors, after checking manifest index, scene, annotation,
native-item hash, checkpoint hash, query shape and target support.
For row 83, all 16 query-103 binary masks equal the strict-run artifact;
the selected query is 2 in both. The largest per-query logit difference
ranges from 1.14e-5 to 1.81e-5 across repeats, but no point crosses zero.
The strict-run point-169 logit is +7.61e-6. The historical reference
run had -2.37e-7 on that point; exact item binding alone does not
reproduce the reference sign.

For row 174, all eight all-network-CPU repeats match the strict-run
query-87 binary mask. Across the eight native and cluster-only repeats,
some match and some differ at one point (20 versus 21 positive
superpoints), with a maximum logit difference about 0.56. The selected
query remains 9. This does not attribute row 83's historical sign flip
to the cluster bank.

Direct receipts: `pipeline/reports/m95_frozen_cluster_row83_artifact_20260926-0831.json`
SHA256 `1ef01cefaa2eac9fcc25e53da8e1edf374149975d7c6d596246d472c6d760521`;
`pipeline/reports/m95_frozen_cluster_row174_artifact_20260926-0836.json`
SHA256 `87e72baeb63664d0c6823b24c358f3e3bd4c8e3dbed2e1de77158faf21fd1e13`.
An earlier artifact attempt stopped on a CPU/GPU equality-check error
and produced no receipt; the recorded runs include the correction.

Against the original reference row-83 artifact (the reference capture
SHA256 is `f9028684`), the first observed feature boundary is already
raw 3D: maximum absolute difference across four repeats is 1.31e-5
in the native/cluster-only arms and 6.56e-6 in both all-network CPU
arms. Fused features differ up to 1.37e-5; final features up to
3.81e-6; selected score vectors up to 5.22e-7. All 16 probe masks
disagree with reference at exactly one point, while all selected
queries remain 2. The bound native item is identical; this is
upstream numeric state, not evidence that cluster-bank CPU alone
restores the reference. Receipt:
`pipeline/reports/m95_frozen_cluster_row83_stage_20260926-0842.json`
SHA256 `0767f322776128d3399298ec3feb625a445f84b16abedd8b91fae221b7b4ce0a`.
The first feature-stage attempt stopped on a batched-tensor shape
assumption and produced no receipt; this run corrected it.

An additional four-repeat hook on the bound row-83 batch found one
byte-identical hash within each arm for the sparse `input_conv` input,
`input_conv` output, `unet` output and `output_layer` output. This
rules out within-arm repeat variation at these captured boundaries;
it does not establish reference-run equality because the reference
artifact has no corresponding backbone hashes. The observed raw-3D
comparison is downstream of the sparse backbone and superpoint
feature reduction. Receipt:
`pipeline/reports/m95_frozen_cluster_row83_backbone_20260926-0848.json`
SHA256 `455778c88eafab9ae181a66b11d6090a373e3521e8d4d468d49e148228537097`.

The trained fixed-item cluster-token stabilization previously observed on
independently transformed items is not, on these bound items, a
task-relevant selected-output improvement. The cluster-bank-only arm does
not isolate or repair the observed row-174 mask variation. No novel
structural mechanism has diagnosis, controls, native backward, resources,
independence and goal constraints together. Zero of two queue slots are
admitted. The next executable diagnosis is a matched bound-item
superpoint feature-reduction input/output trace with reference-run
hashes, comparing sparse-backbone output, gather index/order and
`scatter_mean` operands before claiming a first causal operation.
Inspect producer/package and model-internal sequence state only
where reference and replay first differ. Keep row-83 point-169 logit
as an unchanged downstream criterion. Do not reopen selector, normalization
or scatter variants
on the present evidence.

Evidence:

- `pipeline/reports/m95_frozen_item_replay_20260926-0609.json`
  SHA256 `676b40fdc4ac353ef5c8fc10f5594bc437449d309fd69a26083ef0c42af62382`.
- `pipeline/reports/m95_frozen_cluster_row83_4arm_20260926-0822.json`
  SHA256 `ab2e562e4e2c1b9effde597042795f743d1c5468eb06e3d30032c073a16e7e3e`.
- `pipeline/reports/m95_frozen_cluster_row174_4arm_20260926-0825.json`
  SHA256 `f6581fec2ff096fae4ec0b0ea3bc72121e23a4916f676849a188f6451f8f0b78`.
- `scripts/m95_frozen_batch_cluster_control_20260926.py`
  SHA256 `acf770ecec3e018ef31062ed045a28431de6d93bbf511ed132792d1383d4c5c9`.
