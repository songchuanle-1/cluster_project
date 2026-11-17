# Original Supervision Token Prefix Under Model Postfix

Stable candidate m95-native-supervision-postfix-token-drift.
Tick8e65b0e186784f1ca037a3d81231f738, original deadline06:19:21.766453Z.

Hypothesis: the original map tokenizer encodes the graph caption alone while
the native model input appends " . not mentioned", displacing the supervised
prefix token indices. Distinct from character normalization or truncation.

Discriminating server6 CPU test: full unchanged TRAIN graph captions, original
native tokenizer, compare caption-only versus exactly appended native text;
exclude EOS from the prefix comparison because it is replaced by real suffix.
Native role maps frozen128 compare assigned positive token positions under the
two token views, including actual offsets and token IDs. Missing/zero-map rows
remain explicitly missing, not successes. Identity and leading-character
insertion/wrong-caption controls must show sensitivity.

Precondition disconfirmed if all full TRAIN prefixes retain IDs and offsets
and all observed supervised indices remain attached to the same native token.
This does not prove all parse maps correct, backward, novelty or efficacy.
No production/training/protocol changes; CPU only.
