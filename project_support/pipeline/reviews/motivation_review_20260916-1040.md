# Motivation Review - Referent Supervision Prior Art And Scene Blindness
2026-09-16 10:40 Asia/Shanghai. Diagnostics only; OHRS rejected as contribution.

## 1. Goal
pipeline/goal.json authoritative: 14 constraints, 11 bans, target mIoU >= .51.
Ledger champion M95 .5020; exact .5024607181549072@16; Phase 1 NOT YET.

## 2. What Was Tested This Tick
Three things, all on the fixed forward / fixed TRAIN data:
1. whether the correct query is even distinguishable in the space the referent head
   reads (query separability);
2. whether the object-level question is learnable by a readout on the head's own
   input, including the model's discarded language attention (learnability probe);
3. whether the previously derived OHRS is actually novel (literature gate).

## 3. Code-Level Finding: The Referent Decision Never Reads Its Own Hypothesis
Correction recorded: the query is NOT scene-blind. `qia` cross-attends `inst_feats`
and `qla` cross-attends the language, so scene and language information do reach the
query, and the same query produces the mask. An earlier stronger claim ("no extent
information") was wrong and is retracted; a concurrent audit had already disproved
it as a general premise.

The accurate, narrower statement is that the referent decision never reads the
hypothesis (the mask) that the same query produces. `Decoder_layer.forward`
(dec.py) also receives `sp_pos` and `query_pos` and never uses them:

    query_qia ... = self.qia(inst_feats, query, batch_mask)
    query_qla ... = self.qla(lang_feats, query_qia, lang_masks)
    query = self.qqa_ffn(self.norm_qqa(query_qla + self.qqa(query_qla)))
    pred_scores, pred_masks = self.prediction_head(query, inst_feats, batch_mask)
    pred_indis = self.indi_embedding(query)

`pred_masks` is an explicit inner product with `inst_feats`; `pred_scores` and
`pred_indis` are read off the query alone. The query influences the mask, but the
mask never influences the referent decision.

## 3b. Decisive Confirmation: The Head Tracks Seed Containment, Not Its Own Mask
Native contingency over all 128 queries of every expression in the fixed forward.
`seed_pos` = the query's sampled FPS seed lies inside the referred instance (the
training positive criterion of `match_sampled_ins`). `mask_pos` = the query's own
predicted mask overlaps the referred instance above IoU 0.5 (what deployment
measures). Mean deployed `indis` per cell:

| cell | expressions present | mean indis |
|---|---|---|
| seed=0, mask=0 | 123 | .047 |
| seed=0, mask=1 | 113 | .130 |
| seed=1, mask=0 | 13 | **.848** |
| seed=1, mask=1 | 110 | .876 |

Mean seed/mask agreement .841. Only 35 query-slots are seed-only across the whole
set, but 2473 are mask-only, i.e. the model produces a great many queries whose
mask covers the target and whose seed does not.

Interpretation. Moving from mask=0 to mask=1 while the seed is negative raises the
referent score by only .083, whereas a positive seed raises it by .80. The deployed
head is overwhelmingly a seed-containment detector: it assigns .848 to queries
whose mask does NOT cover the target, and only .130 to queries whose mask does.
This confirms the operational form of the root cause.

## 4. Query Separability
Over the 33 recoverable failures, comparing the query that covers the target with
the deployed argmax query:

| Quantity | mean | median |
|---|---|---|
| cosine of the two final query embeddings | .565 | .677 |
| cosine of their mask-pooled region features | .877 | .895 |
| mask IoU between the two | .086 | .000 |
| positional distance | 2.007 m | 1.803 m |

Two consequences. First, the query space *does* separate the pair (cos .677) while
the region space almost collapses it (cos .895) — which explains why every region
scoring variant failed and why "score regions instead of queries" is not a repair
here. Second, because the two are separable but which one is right depends on the
expression and scene, the missing computation cannot be a fixed re-weighting.

## 5. Learnability Probe
Label = the query's mask overlaps the referred instance above IoU 0.5. Features =
the final query embedding (256) + the query's own mask geometry (size and
mask-centroid offset) + the model's language attention over the referent /
modifier / other-entity / relation token groups (8). L2 logistic regression,
5-fold cross-validation grouped by scene so no scene is in both folds.

| Method | top-1 | mean rank | selected-mask-hit |
|---|---|---|---|
| deployed indis | .178 | 15.68 | .720 |
| probe (query + geometry) | .110 | 25.75 | .627 |
| probe (+ language attention) | .110 | 25.66 | .619 |

The readout does not beat the existing head, and the model's own language attention
adds nothing. Interpretation: on a *frozen* checkpoint trained with the current
point-level supervision, no linear readout of already-computed quantities solves
the object-level question. This rules out readout-only repairs; it does not by
itself prove that a training change would fail, because retraining would move the
features.

## 6. Literature Gate: OHRS Is Prior Art
RefMask3D (arXiv 2407.18244v1, ACM MM 2024) is the closest prior work and was
verified from the original PDF this tick. It uses Hungarian matching whose cost
includes classification, BCE and dice terms, then applies
`Lmatch = l_cls L_cls + l_bce L_bce + l_dice L_dice` to the matched object, plus a
contrastive term. Its Object Cluster Module and Linguistic Primitives exist
specifically to sharpen target identification.

Therefore "assign the referent head's positives by agreement between the query's
predicted mask and the referred instance" — the core of OHRS — is an established
mask-aware matching/classification design, not a new mechanism. It also falls
inside this project's banned assignment-successor family. OHRS must not be
enqueued, under that name or any other.

## 7. Conclusion
The diagnosed root cause (referent positives defined by seed containment while
deployment uses mask agreement) is real and now fully evidenced, and its standard
fix is prior art. The project's remaining contribution cannot be:
- any readout, rescoring, calibration, re-ranking, contrastive or competition
  change (all measured to fail on this checkpoint);
- region-level language scoring (measured to fail and prior art);
- mask-aware matching or referent-positive retargeting (RefMask3D prior art and a
  banned family);
- multi-scale / pooling / selector / readback changes (decision-inert, measured).

## 8. Next Batch
-> see pipeline/designs/exp_design_20260916-1040.md
Status: DIAGNOSTIC COMPLETE / OHRS REJECTED / SCOPE QUESTION OPEN.
