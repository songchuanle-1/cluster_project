# Motivation Review - Existing Semantic Support
2026-09-16 05:41 Asia/Shanghai. Same coverage work,not a new training candidate.

## 1. Goal
Authoritative goal.json unchanged,target .51,exactchampion .5024607181549072.
Existing annotations only,no new dataset/labels,seed1999 and schedule unchanged.

## 2. Story Status
Negative-existence computation needs non-normalized category evidence.
Shared parameter transfer is not guaranteed;generic class supervision is priorart.
This audit tests actual available labels rather than assuming all nouns covered.

## 3. Experiment Assessment
Native annotation-only worker server6 exited0. Fixed32TRAINscenes:
1159instances,578namedinstances,1159single-semantic-label instances.
Observed IDs -100 and0..19. Names are original annotation strings,no synonyms
or new category assignments. Existing dataset loads semantic labels but discards
sem2ins returned by get_sp_label;training batch carries instance labels.
Purity means annotation consistency within instance,not correctness.

## 4. Gap Analysis
Chair/officechair/armchair/sofachair map to observed semantic4.
Pillow28instances,pillows1,monitor8,lamp11 and many other names map to -100.
Negative-case scene0320_00 target34 and selectedwinner18 are both monitor,-100.
Thus category supervision may identify chairs but not distinguish these monitors.
The verticalpillow error is not directly supported by20class semantic supervision.
Do not equate ignore=-100 with background,absence,or a new useful semantic class.

## 5. Design Rationale
For a future class evidence branch,known labels can use standard categorical CE
with ignore_index=-100. No CE on ignored points;do not treat ignored pixels as
negatives for every noun. This training primitive is standard,not novelty.
An actual semantic-spatial mechanism must also resolve reference frame and
predicate scope,calibrate presence without free allzero solutions,and use a
physical support measure robust to arbitrary SP partitioning. These are design
requirements,not proof a model meeting them exists or would improve mIoU.
For the no-chair-before-computer case,available chair labels alone do not
establish which chair is before which computer. No arbitrary axis chosen.
No generic classifier-only candidate or revived sharedwitness/dedup proposal.

## 6. Next Batch
No admission. Native semantic evidence is now complete for fixed32scenes;
do not repeat this audit. Next derive and verify an observable relation frame
or choose a different evidence-backed mechanism. Keep uncertain labels unknown.
