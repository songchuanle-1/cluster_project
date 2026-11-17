# Native Target-Set Cardinality Diagnosis

Tick: 544cb1c4187542cd9ebe69d68351bd98.
Hypothesis ID: multiinstance-union-supervision-mismatch.
Stable candidate: m95-native-target-set-cardinality.

Prediction-blind question: does unchanged ScanRefer TRAIN actually contain
multi-instance target sets whose union is reduced to one supervision unit?
The native get_ref_mask ORs physical object IDs before superpoint averaging.
Plural schema alone is not evidence that plural targets occur.

First test: audit every original TRAIN annotation, compare singular fallback
with explicit object_ids, and separately report the frozen 32-scene/128-expression
cohort. Bind annotation, manifest, dataset source and script SHA256.
Controls: actual singleton projection must equal the original target set;
constructed two-distinct-ID schema controls must be detected by the same parser.
Constructed controls are parser tests, not native population evidence.

If every observed target set is singleton, reject only the multi-instance union
mechanism for this unchanged dataset. Do not reject all mask or supervision
mechanisms. If plural, malformed or missing rows occur, persist exact examples
and execute native physical-ID/union controls before any implementation.
No new data, schedule, labels, prediction-based selection, loss weights, GPU
work or training admission is authorized by this diagnosis.
