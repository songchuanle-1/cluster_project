# Same-category geometric reach control

Before inspecting the result, retain the same immutable 256-expression
M95 TRAIN capture, 16 mask-limited cases, 16 size-matched covered controls,
and exact original scene-to-superpoint coordinates. Continue the geometric
reach test with the *same* native-positive target support and scene spacing.
Replace its broad uncovered background arm by superpoints that are missed
by every query, physically belong to a non-target instance, and have the
modal target semantic category among target superpoints. This is a
GT-localized retrospective placebo that asks whether merely matching
object class can explain the apparent proximity of missed target pieces.
Do not impute absent same-class peers; report their expression/scene counts.
Compare median nearest-support distance for missed target and same-class
unseen background per expression; report ambiguous/absent rows and the
prior broad-background contrast without choosing a favorable threshold.

If the missed target remains closer in enough independent scenes, pursue
a prediction-blind spatial support hypothesis only after constructing a
same-forward causal mechanism and shuffled/semantic placebo. If the
distance advantage disappears or support is too sparse, reject this
specific local-reach rationale. In neither case infer a deployable GT
positive set, sample a new threshold or admit training.
