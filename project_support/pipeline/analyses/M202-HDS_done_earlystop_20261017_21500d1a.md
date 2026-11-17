# Experiment Result Analysis - cluster_project
Experiment: M202-HDS | State: done_earlystop | Evidence collected2026-10-17

## 1. Basic Info
- SAME frozen hierarchical disjoint-support point-feature update,revision2,server4 physicalGPU0. Native stopped2026-10-17 13:12:28+08 at29/50 after10nonimproving validations. No signal,restart,new training or third model revision.
- Native best checkpoint epoch19,SHA c863202420152aeeef3efd2b21932f24a33a636f3db2904e6772cfa7ece078e8; last epoch28/no_improve9,SHA9786ffb1e6a1a03f633372b61d4db0e509f230d9e8a501d94efc6927af561484. Native loop breaks at earlystop before saving epoch29; this is not a missing/corrupt resume state.

## 2. Best Metrics
| Metric | Value | Evidence |
|---|---|---|
| Training native best mIoU | 0.4946560263633728 | epoch19 |
| Frozen candidate full VAL mIoU | 0.4946560263633728 | same best checkpoint,9508expressions/141scenes |
| Candidate full VAL Acc@50 | 0.5474337400084139 | native piou>0.5 |
| Best-epoch spmIOU | unknown | not reconstructed from another epoch's maximum |
| Whole-training peak memory | unknown | diagnostic inference peaks are not training maxima |

## 3. Convergence Summary
- Best first reached epoch19;10later validation epochs failed to refresh best. Native explicit earlystop29,not OOM/TypeError. Original previous TypeError cause remains unknown; successful continuation does not prove its repair.
- Current resumed scalar log has22records of SAME9508VALexpressions,not22independent experiments. Source12hashes and best checkpoint remained unchanged after diagnostics.

## 4. Comparison
- Historical baseline .4894: numeric delta0.005256026363372801; historical champion .5020: numeric delta-0.007343973636627199; target .5100 unmet. No matched baseline checkpoint prediction claim.
- Exact frozen M95epoch16 reference full VAL=0.5024607181549072. Its identity is NOT verified as historical champion weights; historical ledger .5020 is not rewritten.
-9508full-ID pairs/141scene clusters; expression-weighted paired HDS-reference delta=-0.0078046682678767606,95%scene-cluster bootstrap CI=[-0.015523352509624454, -0.00025731673156842596]; macro-scene delta=-0.011230266870248197.5000whole-scene draws,analysis seed1999 fixed before outcomes. No expression-IID or repeat-noise claim.
- Predefined optional unique/multiple/relation/boundary subgroup labeling is unmeasured,not fabricated; independent-repeat noise floor/cross-dataset generalization remain unmeasured. CI excludes0 in this fixed comparison but does not meet the predeclared material-harm margin of upper<-0.003,and subgroup rules are not silently applied to overall data.

## 5. Conclusion
- This HDS realization did not improve the existing M95 reference/champion and is not promoted/restarted. This is not a falsification of hierarchical point-feature updates generally.
- Same-captured-prefix TRAIN diagnosis:4scenes/16expressions,original message omission at fixed normal query yields mean point-feature contribution+0.023922300897538662;3scene means positive,1negative. Query/point interaction is real but heterogeneous; four off-distribution counterfactual TRAIN scenes cannot explain the population VAL deficit or establish generalization.
- Original unchanged FULL-forward repeat failed1e-6(Q6.20e-6/F2.38e-6/logits6.74e-5). Same-prefix native injection/head reconstruction/replay controls are exactly0 at unchanged tolerance; old failure retained,not retroactively passed or independent noise estimate.
- No VAL-selected tuning,new loss,gate sweep,banned routing,new model,scientific gate relaxation or model revision3. Future independent design needs fresh TRAIN-only evidence; remaining auxiliary holds are unchanged.

## 6. Crash Info
- Current training did not crash. Preserve historical OOM/TypeError evidence and this tick's registry-import,full-repeat-control and static-generation failures separately. Model sources/shared libraries were not changed to repair them.
