# Motivation Review - The 2D Identity Lead Does Not Cash Out Under The Language
2026-09-16 11:35 Asia/Shanghai. Decisive negative result; nothing admitted.

## 1. Goal
pipeline/goal.json authoritative: 14 constraints, 11 bans, target mIoU >= .51.
Ledger champion M95 .5020; exact .5024607181549072@16; Phase 1 NOT YET.

## 2. Why This Test
The previous tick found that the raw paired 2D modality preserves instance identity
better than the fused 3D representation (top-5 81.8% vs 57.6% on the same 33
failures). That was recorded as a lead with one explicit caveat: it measured instance
*similarity structure*, not *phrase alignment*, and a modality can be identity-rich
yet poorly aligned to the expression. This tick tests that caveat directly, because
the lead is only actionable if the identity signal is language-addressable.

## 3. Method
Both branches and the language are put into the one shared `d_model` space using the
model's own projections: `input_proj` for the 3D branch, `input_proj_2d` for the
clip_feat rows (captured before fusion), and `lang_norm(lang_proj(...))` for the text.
Each instance is represented by the mean of its superpoint features, then scored by
cosine against the dataset's own referent-phrase token map. Two pooling strategies
are used so that "mean pooling destroyed the signal" is not left open: mean over
referent tokens, and max over referent tokens. Ranks are over all instances of the
scene; `prefers_target` is the fraction of failures where the referred instance
outscores the wrongly selected one.

## 4. Result
| Variant | top-5 of referred instance | prefers target | mean margin |
|---|---|---|---|
| 3D + mean tokens | 15.2% | 54.5% | -0.0027 |
| 3D + max tokens | 12.1% | 54.5% | -0.0012 |
| 2D + mean tokens | 6.1% | 51.5% | +0.0047 |
| 2D + max tokens | 6.1% | 57.6% | +0.0037 |
| chance (top-5 of ~39 instances) | 12.8% | ~50% | 0 |

All four variants sit at chance on `prefers_target`, and their top-5 rates are at or
below the 12.8% chance level. Mean margins are ~1e-3 to 5e-3, i.e. noise. The 2D
modality is in fact *worse* than 3D under language scoring (top-5 6.1% vs 12.1-15.2%),
the reverse of its identity-structure advantage.

## 5. Interpretation
The lead is closed. The paired 2D modality does carry instance-identity structure, but
that structure is not addressable by the referring phrase at this checkpoint: given
the language, neither modality prefers the referred instance over the same-name
neighbour it was confused with. There is therefore no language-aligned identity signal
to "carry through a different path" — the missing half is the alignment, not the
identity, and the alignment is absent for these pairs in both modalities and under
both pooling strategies.

This is also a consistency check on earlier findings rather than a contradiction: the
phrase-group experiment (15 variants over fused features) and this experiment agree
that language-instance alignment for same-name discrimination is the failure, not
feature identity per se.

## 6. Consequences
The routes measured and closed across this and prior ticks now cover: every readout
over existing features (23 scoring variants, 2 probes, 4 alignment variants);
multi-scale/pooling/selector/readback (decision-inert on 123/123); instance-pure
re-partitioning (weak causal link, banned family); referent-positive retargeting and
mask-aware matching (RefMask3D prior art, banned family); region-level language
scoring (measured to fail, prior art); modality re-weighting / extra fusion / gating
(MDIN prior art, numeric change); and the 2D identity lead (closed here).

The remaining explanation consistent with all measurements is that the referring
phrases in these cases do not, at this representation, carry enough discriminative
information to separate the target from a same-name neighbour 1.33 m away — which is
the annotation-ambiguity question already flagged in prior reviews, and which cannot
be resolved without a scope or annotation decision outside this agent's authority.

## 7. Next Batch
-> see pipeline/designs/exp_design_20260916-1135.md
Status: DECISIVE NEGATIVE / NO ADMISSIBLE CANDIDATE / IMPASSE RECORDED.
