# Decoder Information-Path Boundary
2026-09-13 22:09 Asia/Shanghai. Static source audit only.

## Evidence
- File: Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/dec.py.
- SHA256: 6f7566bd02121fd218fd1360be7c7b1905c267de8a03f36473779ab4d66b9d3a.
- Python AST parsed Decoder_layer.forward and checked loaded names.
  Its sp_pos, query_pos and k arguments are unused. Assertion passed.
- Lines293-297 execute query-to-instance attention, query-to-language
  attention, query self-attention, normalization and FFN.
- Lines299-300 form mask/quality outputs and separate query-only indis logits.
- Upstream seed construction gathers positions and applies geometry-weighted
  seed attention; cluster_bank.get_cluster receives sp_pos before the loop.
- No source, model, configuration or remote checkpoint was edited.

## Inference And Counterexample
The local decoder does not directly consume the passed position arguments.
It does NOT follow that queries cannot communicate, lack geometry, or cannot
represent relations. Query self-attention is an existing communication path;
seed construction and cluster construction already use geometry upstream.
Adding query attention would duplicate an existing path. Adding a positional
term without an error-specific derivation risks the prohibited numeric/operator
tuning family. Neither is admitted from this static observation.

The completed fixed TRAIN diagnostic corrects both informative errors under
actual full-loss Adam updates (2 pairs in one scene). It provides no reason
to reopen optimizer, sampling, or repeated gradient-audit successors.

## Remaining Admission Work
Same-category wrong-instance evidence identifies an error type, not a missing
dependency. A future hypothesis must identify what two physically distinct
candidates cannot distinguish under the existing computation and show why
the proposed dependency resolves that ambiguity. It needs a concrete
counterexample and mechanism-matched negative control before a trainable design.
The 21-description casebook is outcome-selected (11 scenes), suitable for
regression cases but not population inference or selecting an efficacy subset.
No new cases, relation labels, predictions, literature claims or novelty
clearance were produced. The source boundary is not empirical causal evidence.
No new training mechanism or GPU diagnostic is approved.
