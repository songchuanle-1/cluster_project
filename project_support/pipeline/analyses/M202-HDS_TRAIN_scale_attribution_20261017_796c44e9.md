# Experiment Result Analysis - cluster_project
Experiment: M202-HDS | State: done_earlystop, unchanged | New evidence: TRAIN diagnostic only

## 1. Basic Info
- Frozen HDS revision2, best epoch19; server4 physicalGPU0. Native diagnostic collected2026-10-17 16:31:08 Shanghai, resource/source postcheck16:33:09. Four already-fixed TRAIN scenes/groups [0,60,101,124],16expressions. No VAL data or new training.
- Stable diagnostic m202-trained-scale-contribution, not a new model, third model revision, gate sweep, omitted-scale training variant or reopening of the completed previous diagnostic.
- Each captured native prefix is reused for all8scale subsets, with original weights and no renormalization. Native projection/normalization/ILA/decoder remain unchanged. Normal query/selection is fixed for primary point-feature endpoint. These interventions can be off distribution.

## 2. Best Metrics
| Metric | Value | Scope |
|---|---|---|
| Training best mIoU | 0.4946560263633728 | cached exact best epoch19, unchanged |
| Historical champion / target | 0.5020 / 0.5100 | unchanged, gap0.0080 |
| TRAIN fixed-query point IoU, full scales | 0.7017901409417391 |16expressions/4scenes, not VAL |
| TRAIN fixed-query point IoU, no scale content but native biases retained | 0.7051412204746157 | same prefix/query/selection |
| TRAIN fixed-query point IoU, true zero message | 0.6778678400442004 | distinct counterfactual |
| Whole-training peak / generalization | unknown | not measured by inference diagnostic |

## 3. Convergence Summary
- No new optimizer or convergence measurements. Original native earlystop29/50 with best19 remains; do not restart HDS or treat the diagnostic as a trained ablation.
- Original full-network repeated-forward matching failure remains. Here the ordered scale sum, message reconstruction/injection, all-scales suffix Q/F/logits and native head/IoU match with maximum error0 under unchanged1e-6. Four native expression-batch canonical counts are [4,4,4,4]. Exact Shapley efficiency residual<=5.56e-17.

## 4. Comparison
- Primary descriptive3player attribution is relative to the preregistered empty-scale subset retaining learned projection/normalization biases. Negative Shapley values are NOT claims that a scale is globally harmful or removable without retraining.
| Fixed TRAIN scene | Fine | Middle | Coarse | Full minus empty | Full minus true zero |
|---|---:|---:|---:|---:|---:|
| scene0000_00 | -0.01396003 | -0.00262337 | +0.03052957 | +0.01394618 | +0.00400846 |
| scene0002_00 | +0.01063977 | -0.01504761 | -0.05472042 | -0.05912825 | +0.12694995 |
| scene0003_00 | +0.00570645 | +0.00085212 | -0.00655857 | 0.00000000 | +0.03629795 |
| scene0004_00 | +0.02788547 | -0.00129160 | +0.00518389 | +0.03177776 | -0.07156715 |
| Mean | +0.00756792 | -0.00452761 | -0.00639138 | -0.00335108 | +0.02392230 |
- Empty bias-retained minus true-zero mean=+0.027273380430415273. Thus previously measured full-vs-zero positive contribution cannot isolate scale-content benefit. This new counterfactual comparison does not establish that biases cause the VAL deficit.
- Joint Q/F fixed-selection full-minus-empty mean=-0.005146848212461919; reported separately from fixed-query point path. No population CI from4scenes or validation-based mechanism choice.
- Previous fullVAL pair9508expressions/141scenes, HDS-reference=-0.0078046683, remains cached prior evidence, not recomputed or recounted this tick. Frozen M95epoch16 is not verified as historical champion weights.

## 5. Conclusion
- The local all-three-scales-nonnegative-in-every-scene premise is refuted. Scale effects differ in sign and depend on the exact counterfactual reference. The full message still has the same local positive mean contribution relative to true zero, not proof of population improvement.
- Do not drop middle/coarse scales, change their weights, tune gates or add HDS revision3 from these16expressions. Mainline remains scale-specific point-feature updates and query cooperation, not memory-only optimization.
- Next research: pre-register disjoint TRAIN scenes without consulting outcomes, then test content/geometry negative controls preserving the original projection/normalization and matched message magnitude. A distinct deployable mechanism needs independent TRAIN evidence, derivation, original-source novelty checks and every unchanged admission gate. No new mechanism is claimed here.

## 6. Crash Info
- Training did not run or crash this tick. First diagnostic attempt stopped after1full forward/0suffixes because the capture expected1canonical call per scene rather than one per expanded expression. Raw source/manifest/result/attempt preserved as attempt1_*.
- Measurement-only protocol revision1 was registered before retry, captured each expression axis and passed4full forwards/36suffix replays. Native matching tolerance, frozen model/config/checkpoint and model revision count remain unchanged. Original source OOM/TypeError and prior full-forward repeat failure remain separate, not repaired or erased.
- Actual work total5full native forwards (including failed attempt),36suffix replays,4CPU control families,0backward/optimizer/VAL/training/admissions/model revisions. server4 own process/context absent and3flocks released;12source hashes/best weights unchanged. server3GPU1 is externally occupied, not touched.
- Evidence: pipeline/diagnostic_bundles/tick_796c44e9/{scale_prereg.md,scale_protocol_revision1.md,scale_result.json,scale_analysis.json,postcheck_resources.json,server3_resource_observation.json,attempt1_scale_result.json}.
