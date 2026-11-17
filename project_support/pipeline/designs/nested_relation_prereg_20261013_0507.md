# Native Nested Relation Coverage Preregistration

- Tick: f3d67c69338443d28eee4349fd8576ab.
- Stable ID: m95-native-nested-relation-coverage.
- Hypothesis ID: nonroot-relations-have-active-token-evidence-excluded-by-root-only-loss-map.
- Population: unchanged native ScanRefer TRAIN annotations and stored graphs.
- Question: Does the native relation positive map omit tokenizable relation spans
  on nonroot object nodes that are not already covered by the root relation map?
- This is not the old main-target/other-entity overlap or empty-main-map audit.
  The proposed deficit is nested relation coverage, not target mention identity.
- First test: run the installed original mapper on full TRAIN graphs; inspect the
  actual graph schema before interpreting role fields. Construct the union of
  native root and nonroot relation spans without changing other role fields.
- Readouts: total expressions/scenes, nonroot relation span incidence, tokenizable
  nonroot-only positions, actual original relation map differences, malformed
  spans, and prediction-blind examples in original annotation order.
- Control: constructed nested graph, root-only graph, and already-covered relation
  span. The original mapper must distinguish missing, included, and redundant spans.
- Any alternate map is diagnostic only: no production code, labels, configurations,
  seeds, schedules or prediction inputs are changed.
- Positive incidence is not incorrect parsing, full model activity, novelty,
  causal task benefit, a passed backward/resource gate, or training admission.
- If actual nonroot-only tokenizable relation evidence is absent, reject only
  this omission premise. If present, retain the same ID and execute a matched
  original native loss intervention before proposing a mechanism.
- Protocol: remote server-6 CPU, CUDA_VISIBLE_DEVICES empty, original native
  tokenizer and mapper, frozen seed 1999 where stochastic inputs are used.
- No additional data, annotation, validation-based selection or numerical tuning.
