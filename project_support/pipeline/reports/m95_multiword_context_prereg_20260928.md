# Native multiword class-key reachability

Continue `m95-sample-context-support`. The frozen native dataset's class
dictionary contains the key `shower curtain`, but the context producer
iterates whitespace-separated tokens. Before inspecting outcomes, test
whether this class has actual expression and physical-instance exposure
in the 64-scene, all-annotation TRAIN cohort used by the previous
physical context audit. Bind identical annotation, graph, native dataset,
and physical hashes. Count expressions containing adjacent exact tokens
`shower curtain`, how many have at least one *other* physical instance
of that class, and how many have that instance as target. Calculate
the existing producer's exact class-key match and an **audit-only**
phrase-aware membership for that class, holding all other keys fixed.

Report unique scenes/annotations/physical non-target instances and
the superpoint rows that gain weak 0.5 support under the audit-only
membership. Negative control: expressions lacking the phrase must have
zero change. The target overwrite should keep target-point supervision
unchanged. If no qualifying physical non-target appears, reject this
multiword-tokenization realization for current native cohort. Even
if it does, this does not prove failure-specificity, a viable novel
mechanism, matched native gradient or training benefit; do not patch
or enqueue from this source audit.
