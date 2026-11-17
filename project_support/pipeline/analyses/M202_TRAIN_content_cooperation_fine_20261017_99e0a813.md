# Experiment Result Analysis - cluster_project
Frozen experiment M202-HDS unchanged;new TRAIN diagnostics and an unadmitted independent prototype

## 1. Basic Info
- Snapshot2026-10-17 20:09:28Shanghai/design,actual deadline21:09:28. Mainline point/superpoint features plus query mask readout;goal,24constraints,11bans and allocation unchanged.
-8pilot scenes32expressions selected by predeclared scene SHA order,excluding the prior4scenes. After freezing an independent next24scene/96expression cohort,all samples were retained. Cooperation/fine/tie audits reuse those same32scene/128expression identities,not96additional scenes.
- All native work on pinned server4physicalGPU0,with3lifetime flocks and unchanged12HDSsource hashes/best epoch19 weights. No training,VAL,optimizer or full-model native backward this tick. CPU-only isolated gradchecks are separate.

## 2. Best Metrics
| Metric | Value | Scope |
|---|---|---|
| Historical champion / target / gap | .5020 / .5100 / .0080 | unchanged |
| M202 best | .4946560263633728@19 | cached trained result,earlystop29/50 |
| Pilot native-minus-norm-matched content | +.0034893621,CI[-.0015276615,.0091529544] |8TRAINscenes32expressions |
| Independent replication contrast | +.0085024113,CI[-.0035666538,.0207177537] |24new TRAINscenes96expressions |
| Independent full-minus-bias-retained empty | +.0093592644,CI[-.0045237190,.0239599130] | same24scenes |
| Independent full-minus-true-zero | +.0664625103,CI[.0360631507,.0984747324] | distinct counterfactual,not content-specific efficacy |
- Intervals:5000whole-scene bootstrap draws,analysis seed1999;not expression-IID,provider billing or independent training repeats. Both matched-content cohorts remain uncertain,not confirmed population gains.

## 3. Convergence Summary
- No new convergence or full training. The existing earlystop,OOM/TypeError histories and previous full-forward repeat failure remain untouched.
- Native same-prefix matching is strict1e-6. Content control recipient-norm maximum relative error2.30e-7 on the pilot;no native precision/deterministic/tolerance change.
- Native model was never run in float64. Detached CPU-only bilinear algebra uses captured float32 tensors converted to double;maximum algebra residual4.09e-14 under separately preregistered1e-10.

## 4. Comparison
- Mean point/query/interaction logit-change energies3.18532466/.09139269/.00277050,total3.35081486. Point energy exceeds query energy on32/32TRAINscenes. Cross inner products are retained;energies are not additive percentages and not IoU contributions.
- Crossed nativeQ/nativeF versus nativeQ/permutedF TRAIN IoUs .68726282/.68398517;permutedQ/nativeF .68340265,permutedQ/permutedF .68204222. Nonlinear IoU interaction+.00191722;BCE interaction-.00020963. This is local readout sensitivity,not proof of the population bottleneck.
- Native augmentation remains the original TRAIN pipeline. Separate diagnostic input tensors were not hashed,so identical scene/annotation identity does not establish exact between-process augmented-input equivalence or numerical noise floor. Within each capture/fork,controls are matched.
- Fine membership:102/128expressions have mixed target/background fine leaves. Mixed membership3513/142720superpoint-expression pairs (pooled.02461463;scene mean.02140759). These are not142720independent geometric points.
- Native majority-superpoint errors:802/3513mixed pairs (.22829490),1156/139207other pairs (.00830418). This is descriptive enrichment with differing label composition,not a causal boundary label or population effect. Bank-only minority-label count1010is NOT a lower bound for the complete model's errors.
- Fine geometry classes PointCloudPartitioner/SharedClusterBank are AST-compared across M95/HDS;see geometry_source_control.json for exact result. That source check does not equate weights/predictions.

## 5. Conclusion
- Mainline continues to target actual point features,not memory-only optimization. Positive full-zero sensitivity does not establish hierarchical-content benefit. Matched-content gains remain uncertain despite independent replication.
- Independent fine-leaf-local-point-exchange is a concrete provisional structure:recipient-specific within-leaf point interaction,fixed original K32/H8,no new projections/gates/loss/language routing,and existing middle/coarse context roles retained. Source/toy tests distinguish it from a shared pooled token;this does not prove material novelty or justify reopening bans.
- Ordinary isolated operator6controls andCPUgradcheck passed. A40node exact-distance stress FAILED permutation equivariance by.0269659085;original failure retained. Real32scene audit had0cutoff ties/adjacency changes,max duplicate-coordinate multiplicity1,which does not excuse the counterexample.
- Independent prototype implementation revision1,preregistered under its own stable ID,uses a symmetric same-leaf mean only on exact cutoff ties. Ordinary output remains exact;tie permutation error8.67e-18,analytic gradient error0. This is NOT HDSrevision3 or full-model native PASS.
- Next actual work:independent M95candidate integration,explicit geometry graph lifetime/orphan fine-only FFN handling,matched native forward/backward,full-model<=10G/latency/memory/independence and material original-paper review. All remain unmeasured;no admission or queue entry. Original-source access is incomplete and no novelty is claimed from standard attention equivalence.

## 6. Crash Info
- No native training ran or crashed. The actual negative is the isolated prototype tie-invariance counterexample,not hierarchical-feature falsification. Its passed repair controls do not erase it.
- Actual128full native captures+192suffix calls,only32distinct TRAINscenes128expression identities. Calls,bootstrap draws,control replays andCPUgradcheck internals are not independent experiments. Full-model backward/optimizer/VAL/admission/training launches/new model packages0;isolated CPUautograd executed,internal reverse-call count unknown.
- Four auxiliary human-scope holds were rechecked once after due and retained;not scientifically rejected or restored. A live mainline implementation remains actionable,so do not claim all routes exhausted or a global external-resource block.
- Postcheck20:58:26Shanghai:server4GPU0 has no contexts/own diagnostic process,3locks released,12source hashes/best weights unchanged. server3GPU1 still has a foreign context and is untouched. Finish/lease-release verification remains required;this analysis does not preclaim completion.
