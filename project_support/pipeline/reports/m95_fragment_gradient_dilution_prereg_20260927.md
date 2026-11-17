# Positive-set dilution in fragmented mask support

Stable ID `m95-sample-context-support`. In the SHA256-bound TRAIN M95 final
mask replay, compare the four fragmented limited expressions with the other
12 limited expressions. Hypothesis: fragmentation associates with more matched
positive queries, and the selected query's gradient is attenuated because
native mask loss averages over the positive set. Use the previously frozen
membership (extra recall > 0); report median matched-query count and median
selected-query gradient multiplied by the positive count, alongside the raw
gradient. A smaller raw gradient but similar count-corrected gradient is
compatible with normalization dilution, not proof of it. Both are observational;
different errors and query interactions can confound this comparison.

No training candidate may be admitted from this join alone. A mechanism would
need prediction-blind supervision, a matched same-forward control, full native
backward and all other six gates. Do not convert this into a loss coefficient
sweep or generic repeated-positive mask loss.
