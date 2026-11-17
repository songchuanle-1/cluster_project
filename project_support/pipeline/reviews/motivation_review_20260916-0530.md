# Motivation Review - Negation Evidence
2026-09-16 05:30 Asia/Shanghai. Diagnostic continuation, not a new variant.

## 1. Goal
goal.json remains authoritative: target .51, exact M95 .5024607181549072.
No constraints, bans, seed or schedule changed.

## 2. Story Status
Fixed123TRAIN has one lexical negation case among31confident wrong,
zero among85success and7other failures. Insufficient for population attribution.
Case scene0320_00/19: no chair before it; target34, wrongwinner18.

## 3. Experiment Assessment
Stored graph has affirmative has/before edges; no at76:78 absent from saved
target/modifier/relation spans. Full contextual input still contains no.
Full existing36665TRAIN/562scenes:419cueexpressions/203scenes,438cues;
101covered by any node span including pronouns,92covered by targetnode.
Lexical no/not/without/neither/nor/except includes idioms and unknown scope.
These counts are not failure rates or new semantic labels.

## 4. Gap Analysis
Native one-case no-chair to a-chair probe on server6GPU7, worker exit0:
fixed geometry/FPS/query support;one token changed. Selected query69 and
original-label selectedIoU0 both branches;candidate scores and masks change.
Scoremaxdelta about.48, maskmaxdelta13.53,228hard-mask entries change.
Repeat selectedquery69,0hardmask changes. Contextual negation token is not ignored.
Affirmative sentence does not retain original reference truth;IoU is not an
affirmative correctness measure. No native backward,training or novelty claim.

## 5. Design Rationale
Missing parser cue supervision alone does not justify a new loss:encoder response
is present and predicate truth/frame/negation scope remain unverified.
Need an observable signed predicate with a matched falsifying control before
any negative-existence mechanism. No automatic complement mask or pseudoanchor.
Do not generalize one case into the31same-class failures or repeat the same probe.
Web literature search yielded no usable content;novelty remains unverified.

## 6. Next Batch
Keep same-forward-coverage-diagnosis;no independent candidate or queue entry.
Use this explicit scope gap when deriving a concrete mechanism;do not call
parser repair or adding an auxiliary cue loss a demonstrated innovation.
