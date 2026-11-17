# Motivation Review - The 2D Modality Carries Identity The 3D Path Loses
2026-09-16 11:08 Asia/Shanghai. Diagnostic only; nothing admitted.

## 1. Goal
pipeline/goal.json authoritative: 14 constraints, 11 bans, target mIoU >= .51.
Ledger champion M95 .5020; exact .5024607181549072@16; Phase 1 NOT YET.

## 2. Question
Every readout over the 3D instance features failed to resolve same-name instances,
and the 3D features were measured to encode category rather than identity. The
paired 2D modality (clip_feat) is already fused into the encoder. Does that modality
carry instance-level identity that the 3D path does not preserve?

## 3. Method
Same fixed 16 TRAIN batches, M95 eval forward, same 33 recoverable failures, same
protocol as the 3D measurement: per-instance centroids (mean over the instance's
superpoints), centred on the scene mean, self-similarity excluded, then every
instance ranked by similarity to the instance the deployed query actually segmented.
The two modalities are compared on identical instances:
- feat3d = final encoder `inst_feats`;
- feat2d = the `clip_feat` rows the loader feeds to `input_proj_2d`, captured from
  `DEC.forward_iter_pred` before that projection, i.e. the raw paired modality.

## 4. Result
| Quantity | 3D | 2D |
|---|---|---|
| median rank of the referred instance | 4 | **2** |
| mean rank | 7.94 | **4.27** |
| top-1 | 27.3% | **30.3%** |
| top-3 | 48.5% | **72.7%** |
| top-5 | 57.6% | **81.8%** |
| p90 rank | 19 | **10** |
| centred similarity null | .029 | -.024 |
| similarity to the nearest other instance | .698 | .780 |

Paired per-failure comparison: 2D ranks the referred instance better in **20** of 33
failures and worse in 7 (6 ties). In 9 failures the target is inside the 2D top-5 but
outside the 3D top-5, against 1 failure the other way.

## 5. Interpretation
Two things follow.

First, the paired 2D modality is a materially better carrier of same-name instance
identity than the 3D feature path, on the very failures that matter. This is the
first measured, constructive asymmetry found in this project: the discrimination the
referent decision needs is present in an input the model already receives.

Second, and more pointedly, the model already fuses that modality:
`inst_feats = sum_norm(inst_feats + input_proj_2d(feats_2d))` at the top of
`DEC.forward_iter_pred`. Yet the *fused and encoder-processed* 3D representation
scores worse on this measurement than the raw 2D rows. So the fusion-plus-encoder
path is diluting or distorting instance identity that the 2D input supplies.

## 6. Caveats, Stated Before Any Design
- Centred cosine is computed in different ambient dimensions for the two modalities;
  the statistic is comparable in ranking terms, not in absolute value.
- Instance centroids are a coarse summary, and 33 failures over 32 scenes are not
  independent samples.
- This measures instance *similarity structure*, not the language alignment the
  referent decision needs. A modality can be identity-rich and still poorly aligned
  to the phrase; the earlier phrase-group measurements are evidence that alignment
  is the harder half.
- Nothing here says the 2D modality is currently unused; it is used, and the point is
  that its identity content does not survive to the decision.

## 7. Novelty Gate To Clear
Multimodal 3D referring designs are dense prior art (MDIN was already verified in
this project as prior art for dual-branch modality fusion; InstanceRefer, HCF-RES,
RefMask3D and NS3D were verified earlier). Simply raising the weight of the 2D
branch, or adding another fusion of the same two features, is a numeric or
recombination change and is not admissible under this goal. A mechanism derived from
this finding must add an information flow that a generic modality-fusion design does
not already provide, and must be argued against those works before admission.

## 8. Next Batch
-> see pipeline/designs/exp_design_20260916-1108.md
Status: DIAGNOSTIC COMPLETE / NEW LEAD IDENTIFIED / NOT ADMITTED.
