# Native-positive mask coverage for unselected failure queries

For the same frozen 256-expression M95 TRAIN capture and native `loss.py`
hashes in `m95_native_mask_population_prereg_20260927.md`, examine all 16
expressions with no query mask IoU >0.5, including the 11 whose *selected*
query is matcher-negative. Select the native matcher-positive query with
highest mask IoU per expression, breaking ties by lowest query index.
This is a GT-guided diagnostic readout only, never an inference selector.

Replay the native matched-query BCE+Dice, confirm selected positive query
is really matched, verify its IoU and sign of final-logit gradients on
missed target and contaminant support. Report denominator of rows lacking
any positive query, eligible negative-selected rows, and finite/corrective
gradients. A present corrective gradient disproves only the narrow
"no final mask supervision" explanation. It does not demonstrate a new
causal representation mechanism or admit a score/selector/mask-quality
variant.
