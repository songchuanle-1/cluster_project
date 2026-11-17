# Experiment Design - cluster_project
2026-10-18 | Diagnostic-only bounded arithmetic revision2
## 1. Motivation
- Goal mainline:hierarchical interactions actually update mask-generating inst_feats. Establish a valid self/nonself content control rather than conflate its numerical failure with trained task failure. No claim that precision repair is a core mechanism.
## 2. Current Best Results
| Experiment | State | mIoU | Epochs |
|---|---|---|---|
| HistoricalM95 | complete | .5020 |22/50 |
| M203-FLE | normalearlystop,branch stopped | .4885315597 |23/50,best13 |
- Available exact M95epoch16 paired reference .5024607182 is distinct from verified historical champion weights. Independent-repeat noise and full-training allocator peak unknown.
## 3. Analysis And Direction
- Complete4due records from cached hashed results without repeating model tests. Keep a single existing diagnostic stable ID. Revision1 was an implementation failure,not a neighbor-usefulness conclusion.
- Monotonic scalar interval solving is a precision-control algorithm only. It must retain1e-6native/true checks and donor direction;labels and task results cannot guide it.
## 4. Experiment Plan
| ID | Test | Frozen prediction | Failure |
|---|---|---|---|
| fle-self-neighbor-content-separation/diagnosticrevision2 | Saved inputs from both prior norm failures;identity/zero/tie/permutation/gradient controls | Both native/true norms within original tolerance | Any assertion or no feasible radius |
| Same ID/native | Same time-selected epoch2checkpoint,8TRAINscenes32expressions,sameprefix/suffix controls | Valid control plus finite scene-level content readout | No cohort efficacy interpretation if controls fail |
- No seed/config/optimizer/schedule/data change,new training or VALevaluation. Native result at early checkpoint is not terminal efficacy/generalization. Direction of normal-minus-intervention Piou is reported with scene uncertainty,not pretraining admission threshold.
## 5. GPU Allocation Plan
| Server | PhysicalGPU | Use |
|---|---|---|
| server4 |0,pinned UUID | Original native diagnostic only after fresh identity/idleness/3locks |
| server3 |1,pinned UUID | Preserve live occupation;not used without target asset validation |
- server4GPU1 not authorized. CPU controls on server4 with CUDA hidden;local orchestration/edit/static only.
## 6. Implementation Checklist
- Preregister before executing;bind producer/assets/lease hashes;preserve all old results and failed inputs. One bounded diagnosticrevision2,not productionrevision2.
- CPU checks before native;fresh live GPU check and lifetime locks beforeCUDA. Abort on original thresholds;no task-score-driven revision.
- Persist results and report incrementally,finish with original deadline and verified lease release. No scheduler/background/newthread changes.
## 7. Risk Assessment
- Feasible scalar interval may not exist in float32;failure is inconclusive diagnostic,not proof against neighborhood interaction. More precision does not automatically ensure the legacy reduction control.
- Spatial permutation can be out-of-distribution even after exact magnitude matching. Eight earlyTRAINscenes are a mechanism readout only. No automatic model restart/admission follows a numerical PASS.
Status: PREREGISTERED_DIAGNOSTIC_NOT_TRAINING
