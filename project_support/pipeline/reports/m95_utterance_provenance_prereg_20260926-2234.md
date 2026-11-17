# Frozen utterance-provenance audit

Stable ID: `m95-utterance-provenance`. On the exact 256 frozen TRAIN
expressions, compare the native `ScanRefer_train_new.json` description
against the parsed `scene_graphs_new_train.json` utterance supplied to the
model. The source, graph and capture hashes are fixed in the prior
target-label audit. This differs from token-span integrity, which checked
graph spans against model-input tokens but did not compare the graph
utterance to its original annotation.

Before reading outcomes, use lowercase whitespace normalization and
punctuation-insensitive word tokens (ASCII alphanumeric groups), with no
synonym repair. Report exact normalized string equality, token-sequence
equality, and a `difflib.SequenceMatcher` token edit summary for each
row. Explicitly retain both original strings for discrepancies and
separately report any token deletion, insertion or substitution. The
negative control is punctuation/whitespace-only difference, expected
to leave the word sequence identical. Stratify by the frozen ambiguous
and class-unique groups and selected native IoU <=0.5. Count same-scene
discordant-exposure pairs. No outcome-conditioned text filters.

A systematic loss/change of task-bearing words in failed rows would
motivate a native matched intervention. Punctuation-only changes or
absence of failure enrichment disconfirm this realization. No model
admission without all six gates and a distinct mechanism.
