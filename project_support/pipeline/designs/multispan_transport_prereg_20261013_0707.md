# Root Multi-Span Transport Diagnostic

Stable ID: m95-native-root-multispan-transport.
Hypothesis ID: later-root-mention-spans-are-dropped-before-positive-map-loss-input.

A graph root may have multiple separated target mentions. A row-zero native
loss input might retain only the first mention, losing later valid token
evidence. Test this transport premise independently of sign conflict.

Use every unchanged TRAIN annotation and the original tokenizer/get_positive_map
function. Independently map each stored root target span and sum its rows;
compare token membership and values with the native mapper's actual root row.
Report multi-span population, later-only token positions and native omissions.
No graph editing, prediction-selected population or new labels.

Matched controls use two separated mentions in one constructed root, and an
intentionally first-only broken mapper readout. The original multi-span map
must retain the second span and the broken control must lose it. A zero
observed omission rejects this stored-span transport premise only, not parser
completeness, co-reference correctness or all repeated-mention mechanisms.

Native loss/model backward, resources, independence and novelty remain not run.
The diagnostic is not a proposal to adjust normalization or loss weights.
