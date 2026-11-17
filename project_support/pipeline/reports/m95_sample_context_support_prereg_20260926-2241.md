# Auxiliary seed-context supervision screen

Stable ID `m95-sample-context-support`. The M95 native dataset builds
`sp_ref_masks` by scanning whitespace-separated graph utterance words for
exact keys in `type2class`, assigning context-class points 0.5 and
overwriting target-instance points to 1. The loss samples this support at
FPS seeds before additional native matched-seed assignments. This audit
tests the *pre-overwrite lexical class support* only; it cannot claim
the actual final per-seed target or a causal loss conflict.

Freeze the 256-row changed-producer TRAIN cohort and exact native annotation
and graph SHA256. Parse `type2class` with Python AST from the champion dataset
source; fail closed if the expression is not a literal dict. For each row,
reproduce the exact `lang_utterance.split()` membership in class keys,
excluding `others`. Define exposures before reading outcomes:
no class key, target annotation name exactly one class key but absent from
the matched word set, and at least one non-target class key. An annotation
name outside class keys is unresolved for target coverage, not absent.
Report the exact words/keys, full 256 identities, 128/128 strata, frozen
selected-mask IoU <=0.5, and same-scene discordant pairs. No synonym repair
or outcome-conditioned category selection. Source-code hash is recorded.

Falsify this realization if missing target-class cues are absent/sparse or
not failure-linked. Even if enriched, the target-instance overwrite means
lexical absence alone does not establish degraded target seed supervision;
native final-label/backward and matched controls would be next. Do not
admit, sync model code, or train based on this screen.
