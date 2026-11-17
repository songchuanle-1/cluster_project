# Motivation Review - cluster_project
2026-10-18 | Continuing tick ceb5e6c142dc446d87145d00bdce392e

## 1. Goal
- Full unchanged goal is quoted by frozen artifact `pipeline/diagnostic_bundles/tick_ceb5e6c1/scope_goal.json`, SHA256 42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec. All24constraints/11bans remain in force.
- Mainline: scale-specific interactions update point/superpoint inst_feats actually used with query features for masks. Memory efficiency alone is not the contribution. Target .5100, historical M95 .5020, gap .0080; baseline .4894.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| This trained FLE realization improves the main task | Not supported | Normal earlystop23; best epoch13 .4885315597; frozen fullVAL confirms | Does not falsify every point-exchange design |
| Useful neighbor content beyond self/magnitude | Inconclusive | Original and diagnostic revision1 fail unchanged native norm control | Valid matched intervention still needed |
| Fixed native fine membership survives seven geometry transforms | Finite sampled control passes | 8TRAIN geometries/56comparisons,zero output differences | Synthetic features,not whole-hierarchy or trained-mask robustness |

## 3. Experiment Assessment
| Experiment | mIoU | Relation to motivation | Contribution |
|---|---|---|---|
| M203-FLE | .48853155970573425 | Recipient-specific fine point exchange; larger scales retained | First trained negative result for this realization,not an innovation claim |
| Frozen available M95epoch16 | .5024607181549072 | Paired same-VAL comparator | Available checkpoint identity,not verified historical champion weights |
| Historical baseline / M95 | .4894 / .5020 | Scalar references | No invented paired baseline uncertainty |
- Full IDs align9508expressions/141scenes. Expression-weighted paired delta -.0139291520,95%scene-bootstrap CI[-.0223369116,-.0054631474];macro-scene delta-.0087360696,CI[-.0178804073,.0010744083]. Different estimands remain separate.
- Predeclared mixed-fine-leaf group8558expressions/135scenes:delta-.0115597977,CI[-.0204810688,-.0020668053]. No-mixed group950/80:delta-.0352732931,CI[-.0679328646,-.0024762026]. Both fail to establish the strict upper-CI<-.003 subgroup harm rule;neither is a benefit PASS. Missing subgroup mappings0;scene memberships can overlap between groups.

## 4. Gap Analysis
- Terminal training is verified,not merely absent PID. Native earlystop at12:08:47Shanghai follows10nonimproving validations;best epoch13. Last checkpoint epoch22 is expected because stopping precedes epoch23save.
- Original self/nonself runner:2forwards,1completed scene,3suffix replays then AssertionError. Capture-only attempt:1forward,0completed scenes. One preregistered diagnostic arithmetic repair:2forwards,1completed scene,3replays then the same1e-6control fails. Partial scenes cannot establish cohort-level neighbor usefulness.
- Captured true float64 norm drift reaches1.4637015386e-6;not just reduction measurement. Higher-precision diagnostic scaling reduces true errors to about2.3e-7 but fails legacy CPU checks in3/4captured conditions and native scene2. The CPU aggregate `passed:true` does not override these failed subcontrols.
- Training efficacy is measured negative for this realization. Material novelty,independent-repeat noise,full-training allocator peak and original no-cluster resource delta remain UNKNOWN. Inference peak is not training peak.

## 5. Design Rationale
- Stop this converged trained realization;do not restart,select a different checkpoint,scan numerical parameters or claim global mechanism falsification.
- Preserve the failed diagnostic under the same stable ID in implementation. Before another native attempt,derive and preregister a bounded strict norm-preserving diagnostic repair on captured inputs;do not loosen1e-6,change model precision or consume a production revision by relabeling it.
- Preserve the previous artificial lattice counterexample even though sampled native fixed-membership controls pass. No epsilon repair is justified by the current data.

## 6. Next Batch
- See `pipeline/designs/exp_design_20261018_ceb5e6c1.md`. No new training candidate is admitted. Four auxiliary human/scope holds remain unchanged and not reopened by a timer or GPU availability.
