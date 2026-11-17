# Query-universe seed-context score control

Continue `m95-sample-context-support`. Freeze the same hash-bound native
256-row capture and graph/dataset/TSV as the physical seed screen. The
earlier selected-query exposure was conditional on the deployed top score.
Before examining query scores, compare all resolved unmatched non-target
queries within each expression: exact class-context seed versus non-context
seed. Exclude matcher-positive and unresolved seeds in both arms. Require
both arms within an expression; report eligible expressions/scenes,
context/non-context counts, mean score difference and proportion of
positive differences across expressions, separately by ambiguous/class-
unique stratum. Score is the native `indis[:,1]` probability, not an
intervention; no outcome threshold or top-k selection in the exposure.

If there is no consistent score elevation, reject a class-context
score-bias explanation. If elevated, this is still observational and
could reflect semantic class information or geometry; the next step
must capture the actual post-overwrite seed-loss targets and test a
same-forward matched removal/placebo with native backward. Do not
admit a model from score association.
