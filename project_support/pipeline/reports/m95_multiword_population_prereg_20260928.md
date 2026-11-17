# Full TRAIN population of unreachable multiword class context

Extend the frozen first-64-scene physical audit to every original TRAIN
scene/annotation without changing the native code or class mapping. Bind
the same annotation, graph, TSV and dataset-source hashes. Before loading
physical data, identify all expressions whose normalized original graph
utterance contains adjacent exact `shower curtain` tokens. Load only these
scenes, recover physical instances' first retained semantic class, and
count non-target physical shower-curtain instances. Report the number of
all TRAIN scenes/annotations, phrase-exposed scenes/expressions, unique
physical instance exposures and any native source-level context rows
that would change under audit-only phrase membership. Include the frozen
64-scene counts as a parity check, and expression/scene denominators
instead of treating repeated superpoints as independent.

No outcome-selected sample, threshold search, dataset patch, native
backward or training admission. This establishes reachability and bounds
the potential scope of a linguistic-class source error, not whether the
model fails on it or whether a lexical patch is a distinct Phase 1 mechanism.
