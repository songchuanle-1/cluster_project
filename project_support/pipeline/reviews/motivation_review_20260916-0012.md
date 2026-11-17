# Motivation Review - Anchor Token Access Diagnostic
## 1. Goal
Authority:pipeline/goal.json,14constraints/11bans,target.51;M95exact.5024607182.
No training admission,coefficient tuning,selector successor or new annotations.
## 2. Story Status
Same-forward native TRAIN123expressions32scenes:85success,33recoverable,5limited.
Six no-FPS-target cases;zero cases lose all target seeds during sampling.
This bounded diagnostic does not support a sampling expansion mechanism.
## 3. Experiment Assessment
BCCA complete16batch effect weak/mixed and prior-art overlap;rejected.
CPS conditional paired selection failed to beatM95;not reopened.
Language-evidence reranking and tied heads already rejected/unadmitted.
## 4. Gap Analysis
Candidate availability does not identify why target discrimination fails.
Specific question:does decoder query-language attention use other-entity tokens?
Existing role maps provide spans without new labels;maps can be missing/overlap.
## 5. Design Rationale
Intervene on native query-language token access,not output score rescaling.
Compare original,repeat,other-entity masking,equal-count non-target token masking.
All effects diagnostic;removing words can harm semantics or induce distribution shift.
No new method/novelty claim follows automatically.
## 6. Next Batch
See exp_design_20260916-0012.md;execute fixed16TRAIN batches before further design.
