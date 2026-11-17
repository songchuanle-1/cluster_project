# D1 Exact Identity And Geometry Audit

## Protocol And Coverage
Frozen21descriptionIDs from the existing12errors/9controls, threecontrols missing
without replacement. 11physicalscenes, two models,42records. No new inference.
All445 aggregation object masks exactly equal raw instance-ID masks.
Raw point SHA matches the prior audit; segmentation and aggregation SHA saved
per scene. All42 target names agree with source labels after case/underscore
token normalization. Zero missing ID joins, duplicateIDs or nonfinite geometry.
No label guessed from predicted appearance. No external annotation or new dataset.

## Fixed Error Evidence
| Case | Scene/object/ann | Target label | Winner ID | Winner label | M95 IoU | Centroid distance | AABB lower bound |
|---|---|---|---|---|---|---|---|
| 1 | scene0578_00/5/36 | chair | 7 | chair | 0.000000 | 0.775659 | 0.200751 |
| 2 | scene0208_00/0/20 | bookshelf | 106 | bookshelf | 0.000000 | 6.259455 | 4.048936 |
| 3 | scene0328_00/24/52 | kitchen cabinet | 21 | kitchen cabinet | 0.000000 | 1.185387 | 0.417069 |
| 4 | scene0621_00/2/85 | table | 3 | table | 0.000000 | 2.097896 | 0.679224 |
| 5 | scene0334_00/5/23 | coffee table | 2 | couch | 0.000000 | 4.239098 | 2.222955 |
| 6 | scene0621_00/22/68 | chair | 20 | chair | 0.000000 | 1.389078 | 0.589928 |
| 7 | scene0146_00/16/8 | toilet paper dispenser | 16 | toilet paper dispenser | 0.488442 | 0.000000 | 0.000000 |
| 8 | scene0249_00/23/41 | trash can | 28 | trash can | 0.000000 | 3.622357 | 3.098981 |
| 9 | scene0046_00/26/27 | door | 21 | door | 0.000000 | 1.899084 | 1.560199 |
| 10 | scene0426_00/22/24 | pillow | 0 | pillow | 0.000000 | 1.482519 | 0.591076 |
| 11 | scene0591_00/14/22 | pillow | 16 | pillow | 0.000000 | 0.649575 | 0.000000 |
| 12 | scene0652_00/6/33 | cabinet | 27 | dresser | 0.069973 | 0.855560 | 0.000000 |

M95 fixed12errors: {'different_instance_equal_annotation_label': 9, 'no_instance_pass50': 1, 'target_best_partial': 1, 'different_instance_different_annotation_label': 1}.
These are outcome-selected examples, not prevalence estimates or causal effects.
The two pillow cases (scene0426 object22 and scene0591 object14) now have verified
same annotation labels despite unknown coarse semantics. Scene0249 object23
versus28 is trash can versus trash can, not merely equality of coarseID19.
Scene0652 cabinet6 versus dresser27 is different annotation labels; the wording
"taller of the two" does not license calling these the same semantic category.
Scene0334 coffee table5 best overlaps couch2 but no instance reachesIoU>.5:
do not upgrade this to a confident couch prediction. Scene0146 dispenser16
remains target-best partial mask, not demonstrated wrong-object selection.

## Geometry And Language Limits
For object point set X_i, c_i=mean(X_i), l_i=min(X_i), u_i=max(X_i).
d_ij=||c_i-c_j||2; g=max(0,l_i-u_j,l_j-u_i) coordinatewise;
||g||2 is the distance between enclosing axis-aligned boxes, hence a lower
bound on point-set distance, not contact or predicate truth.
Local independent scalar recomputation verifies all42 target/winner distances,
all object extents and centroid containment. Original point-coordinate frame
and numeric units retained; viewpoint/alignment/unit provenance not adjudicated.
No thresholds applied to infer near, on, behind, right, color or target height.
Exact token-subsequence noun matches produce object candidate lists and target
distances in JSON. Singular/plural variants and misspellings are not corrected.
These lists are incomplete lexical matches, not grounded anchors or parser recall.
All42 relation and boundary causal labels remain unknown.

## Controls And Interpretation
Nine original same-scene successful controls retained, three missing. These are
descriptive controls chosen by M95 outcomes, not matched randomized experiments.
Scene0046 object26 ann27 fails in bothmodels while ann34 succeeds: same target,
different descriptions, not a controlled paraphrase or proof of relation failure.
Do not impute these12 labels to remaining99 M95 recoverable errors. Earlier
284-ID coarse-semantic audit and its denominator remain unchanged.
The candidate-selection headroom evidence is stronger than any proposed cause.
No shared-anchor mechanism, novelty, generalization or efficacy claim admitted.

## Next Evidence Gate
Choose a concrete explanatory question only after addressing language ambiguity:
does the available description distinguish target from the verified same-name
alternative through an observable property, or is viewpoint/anchor ambiguous?
Freeze per-case text spans, alternative object IDs, anchor candidates and missing
frame evidence before evaluating a predicate; use existing scene assets only.
Then compare one candidate to primary papers and historical variants and derive
its objective, forward/loss, gradients, degeneracies and matched controls.
No automatic selector/pooling descendants or new training entry.

## Verification And Resources
8synthetic local/remote checks passed;42independent scalar distance checks and
445 object geometry/identity records validated. AuditCPU
2.372s,peakRSS580.816MiB,CUDAuninitialized.
These costs exclude training/model inference and are not efficiency admission.
Initial Python3.10 hashlib API crash occurred before pointdata load; portable
SHA256 repair attempt1 succeeded. Initial logs preserved; no training interrupted.
Worker hash verified on server-4 and server-6; deployment diffs unchanged.
AuditSHA:ed61c14728a966720cff87904a3ac5a839f7423188c600dbed87b76fed86f6bd.
