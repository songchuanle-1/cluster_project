# Motivation Review - Instance Boundary Relations
2026-09-16 07:22 Asia/Shanghai. Scientific review only; NOT ADMITTED.

## 1. Goal
Authority: the full pipeline/goal.json, read this turn without truncating its
14 constraints or 11 bans. SHA256:
8f022b3988ea186058165f43c497db2a284cb96fe8bb88452f63716c0298c087.
Target .51; ledger champion .5020; exact checkpoint .5024607181549072.
07:20 goal check remains Phase1 NOT YET. Four authorized slots, zero active.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Same-class discrimination is relevant | descriptive evidence | 29/31 confidently wrong cases same name | not mechanism causality |
| Independent context-instance masks are feasible | component tested | native backward and 9.90225518G | full mechanism absent |
| Boundary rather than centroid information explains some errors | investigated | 8/123 captions, 7 scenes | ownership and anchor ambiguity |
| Generic phrase/instance alignment is new | unsupported | originals below | distinct complete computation required |

## 3. Experiment Assessment
Baseline .4894491136; M95 .5024607182; M195 .4986896217;
M196 .4799236655. The last experiment was stopped after only five native
validations without improvement; do not treat it as a patience-complete failure.
No additional training or efficacy result this turn.

## 4. Gap Analysis
Read and verified three downloaded original papers:
- arXiv2603.06250v1, Hierarchical Collaborative Fusion for 3D Instance-aware
  Referring Expression Segmentation, Zhou/Chen/Gong/Liu. Section III-C uses
  SAM-guided instance features; III-D already enhances language-selected
  sparse queries through scene-wide instance cross-attention and modal weighting.
  Our existing feature cache does not supply that additional instance image input.
- arXiv2603.02896v1, 3D-DRES: Detailed 3D Referring Expression Segmentation.
  DetailBase section4, equations4-8 uses token queries, visual cross-attention,
  token self-attention and token-mask supervision. Its fine-grained additional
  annotations are not authorized here. Section6 explicitly discusses instance cues.
- arXiv2103.01128v1, InstanceRefer. Sections3.4-3.5, equations5-9 already
  combine object categories, relative centers and instance neighborhood features.
Also reread NS3D section3.3: learned object relations plus latent reference
selection trained from target supervision are prior art, not a new candidate
merely because auxiliary anchors lack labels.

## 5. Design Rationale
Test the narrower physical premise before proposing a production architecture:
some language mentions anchor faces/corners, not just center displacement.
Use all eight matching captions in the already fixed 123-TRAIN capture,
regardless of outcome. Six are confidently wrong; two are successes.
Keep every exact-name instance candidate and flags for self identity.
Native-data diagnostic on server6 completed; six synthetic rigid-transform,
permutation and scale checks passed. No model forward or optimizer was run.

For an anchor XY covariance eigensystem (V,lambda), project points into V,
retain its rectangular extents and calculate distances to finite short/long
faces, corners and end midpoints. These are ordinary geometric proxies,
NOT a novel mechanism. They cannot determine front/back or linguistic ownership.
The whole proposal must still justify how a phrase-owned boundary relation is
identified and used without inference labels or legacy ranking/gating.

## 6. Next Batch
See exp_design_20260916-0722.md for the executed feasibility plan and
its disposition. No new experiment ID, model package, receipt or queue entry.
Maintain stable same-forward-coverage-diagnosis rather than duplicate candidates.
