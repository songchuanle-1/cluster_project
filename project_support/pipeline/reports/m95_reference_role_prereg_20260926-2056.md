# Explicit Other-Referent Role Screen

Stable ID `m95-reference-role-ownership`. Source:
`pipeline/reports/mention_role_objective_20260916.json`, SHA256
`65e110e0a11c7486c5f552b94c917525412d6cfc8e52a10974f709a69cafc01e`;
join `pipeline/reports/relation_response_identifiability_20260916.json`,
SHA256 `ea63f5e141a6a1687fd9d8a1f33768540daa22f9a537c8ef3191ac67c234802d`.
TRAIN only; fixed 123-expression cohort, no validation selection.

Group exact `(scene, ann_id)` expressions, counting all role mentions but
only one outcome per expression. Compare `explicit_other_cue` with
`sentence_initial_definite_repeat` and unknown controls. Report
confident-wrong fractions, unique scenes, overlap between cue groups,
and whether the previously captured noun intervention changed the
*same* role mention. Do not treat repeated definite noun as proven
coreference or string equality as ground-truth ownership.

Falsifier: no differentiated error incidence, no untested role mentions,
or ambiguous target/reference ownership. A positive descriptive
screen remains diagnosis only. Next executable native test must alter
the exact explicit-other mention with matched token length and a
same-forward unchanged/repeat/control on the frozen scenes, verifying
native physical support and attention axes. A generic relation fusion,
selector, lexical threshold or noun-string merge is not a candidate.
