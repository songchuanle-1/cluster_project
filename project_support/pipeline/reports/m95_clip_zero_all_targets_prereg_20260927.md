# Zero CLIP feature exposure across all frozen-scene annotations

Stable `m95-sample-context-support`, diagnosis. The previous first-annotation
screen found four zero-CLIP target superpoints in two scenes, but one annotation
per scene undercounts target identities. Freeze the same first 64 TRAIN scenes
and all their `ScanRefer_train_new.json` annotations, without using predictions.
For each annotation, aggregate physical superpoints majority-owned by its
target object and having at least five points; count zero and nonzero CLIP
rows, reporting expression-, unique-object-, and scene-level denominators.
Compare with non-target superpoints in those same scenes, and report how
many scenes contain both exposed and unexposed target annotations.

The actionable screen is a target-specific zero-feature enrichment across
independent scenes. If target exposure remains lower than non-target exposure,
this cache-zero realization cannot justify a target-defect mechanism. An
association alone is not causal training evidence or admission.
