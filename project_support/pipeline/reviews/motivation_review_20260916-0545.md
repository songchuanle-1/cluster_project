# Motivation Review - Raw Annotation Recovery
2026-09-16 05:45 Asia/Shanghai;continuation,not training admission.

## 1. Goal
goal.json unchanged,target.51,exactM95.5024607181549072.
Existing TRAIN annotations only;no new labels,data download or inference oracle.

## 2. Story Status
Correct previous0541 limitation:20class tensor ignores pillows/monitors,
but existing raw aggregation labels preserve their names.
Raw semantic supervision availability is no longer an unverified blocker.

## 3. Experiment Assessment
Server6 annotation-only worker exit0. For32fixedTRAINscenes, reconstruct instance
labels from aggregation segGroups.id and segmentation segIndices.
All5522145points match native .pth instance IDs exactly;groupid/objectid mismatch0.
1159instances;409ignored by20class map,all409 have rawlabels;141rawstrings.
This proves data identity,not correctness of every annotation or anchor binding.

## 4. Gap Analysis
Exactname join11verticaledges changes1:scene0209_00/12 lamp candidates
previous[3],raw[3,30,38]. Fourmissing matches remain;no plural/synonym repair.
Wrongpillow keeps7anchors. Class supervision cannot determine intended referent.
Previously computed lamp geometry bounds over oneanchor are partial,
not complete bounds over all raw candidates. Do not silently reuse as complete.
Original producer prepare_data_refer.py explicitly maps unselected NYU classes
to -100 while reconstructing instances from raw aggregation IDs.

## 5. Design Rationale
Existing raw labels can constrain a learned category field without adding
annotations. This removes the missing-category objection to a trainable
semantic-spatial mechanism;does not establish novelty or efficacy.
Keep rawlabel aliases as observed,unknowns unknown. Any future vocabulary
and mapping must be derived from TRAIN only,not VAL/test.
Need instance-conditioned relation computation distinct from generic classifier
and CoT3DRef/NS3D/EaSe;calibration,viewframe and gradients remain explicit issues.
No pointwise semantic labels or GT object IDs supplied at inference.

## 6. Next Batch
Do not repeat rawidentity/20classaudit. Derive a complete instance-level relation
computation using verified available TRAIN supervision;evaluate against exact
priorart and closed directions before independent implementation.
If further geometry evidence is needed,use raw candidate sets,not incomplete
ScanRefer-mentioned sets. No admission or newmodel this continuation.
