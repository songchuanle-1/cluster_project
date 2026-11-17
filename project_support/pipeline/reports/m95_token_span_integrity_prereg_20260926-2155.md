# M95 token-span integrity diagnostic

Stable ID: `m95-token-span-integrity`. This is a TRAIN-only, prediction-blind
data-path diagnostic, not an admitted mechanism.

Freeze the 256-row cohort and its native selected-query outcome from
`m95_shape_evidence_screen_20260926-2128.json` before running the test.
The TRAIN source and scene-graph SHA256 values are
`018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d`
and `e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08`.
Use the actual server-6 `roberta-base` tokenizer and exactly the dataset's
normalized graph utterance; also tokenize its actual model-input suffix
` . not mentioned`.

For each graph-node-zero target/modifier/pronoun/relation span and other-object
target span, check integer character bounds, exact tokenizer `char_to_token`
mapping with the dataset's +1/+2 and -2/-3 fallbacks, token index <256,
unchanged original token IDs in the suffixed model input, and whether the
mapped token text equals the claimed source substring after normalization.
No imputed target binding when the graph has no target span. Report target
and other-role gaps separately by ambiguous/class-unique stratum and by
selected IoU <=0.5. Report all identities and denominators, not only failures.

A true unreachable or shifted target token in failed expressions relative
to matched successful expressions would motivate a *new* causal proposal,
subject to distinction from closed supervision/role fixes. If no target
alignment deficit exists, reject this realization. A descriptive association
alone cannot pass admission: matched same-forward native intervention,
new-path backward, resources, independent package/config, goal constraints
and primary-source review remain necessary. Do not enqueue from this audit.
