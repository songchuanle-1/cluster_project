# Semantic-Projection Candidate-Evidence Diagnostic

Date: 2026-09-12 00:31. Read-only, evaluation-only, 284 frozen M95 banks.

## Question

The M95 decoder trains `proj_query` and `proj_token` with `loss_sem_align`
but discards both at inference. Can that trained semantic-alignment projection
form a language-specific candidate-selection score on the already observed
recoverable selection errors?

## Protocol

- Capture: `/tmp/cluster_semantic_projection_20260912/full`; 284/284 banks.
- Local preserved copy:
  `pipeline/reports/d1_semantic_projection_20260912-0007/`.
- Capture summary SHA-256:
  `17ea5448f1d3021d634a36eeeaf78dd20db362a9c624cc83a1e9e1ec4956155c`.
- Worker SHA-256:
  `17efd374147b9468576fb1eb3e96ab065b72685572633bfd9a1e1d02b9d884d3`.
- Source JSON SHA-256:
  `4455b8857ade37aaafa32581537a961a77bcc756b22d8143ed4021bc88b7931f`.
- Artifacts: 284 `.pth`, 659,116,219 bytes; sorted per-file SHA-256 list
  digest `7f7130d9dd3e10af9a428199369e20dcfeb3acfc331e82d25db1b87d8931c4e1`.
- Candidate support is `mask_logits > 0.0`, matching the corrected language
  diagnostic protocol.
- The deployed selector is `argmax_c softmax(indis_logits_c, dim=1)[1]`.
  The prior language report used `indis_logits[:, 1]`; that row was not the
  deployed selector when the other class logit varied. This report records
  both and uses the deployed softmax row for comparisons.

## Methods

For candidate query `q_c` and valid text token `t_l`, the capture already
contains L2-normalized `proj_query[q_c]` and `proj_token[t_l]`. Let

    a_cl = <proj_query[q_c], proj_token[t_l]>.

Scores compared:

    sem_max_cos                 = max_l a_cl
    sem_mean_cos                = mean_l a_cl
    sem_lse_cos                 = logsumexp_l a_cl - log L
    sem_lse_train_tau           = logsumexp_l (a_cl / 0.07) - log L
    sem_margin_top2             = top1_l a_cl - top2_l a_cl
    sem_token_contrast_train_tau
        = mean_l [ a_cl / 0.07 - logsumexp_c'(a_c'l / 0.07) ]

Controls use the same candidate queries but replace the text projection and
text mask with (a) the next bank in the frozen manifest and (b) a different
bank with the same `object_name`. Same-category controls cover 261 banks with
at least one peer.

## Results

| Method | Banks | Acc@50 | Recoverable rescued | Success harmed | Oracle top-5 |
|---|---:|---:|---:|---:|---:|
| deployed `indis` softmax | 284 | 0.5106 | 0 | 0 | 0.2887 |
| `sem_max_cos` | 284 | 0.5070 | 3 | 4 | 0.2535 |
| `sem_mean_cos` | 284 | 0.5000 | 2 | 5 | 0.2852 |
| `sem_lse_cos` | 284 | 0.5000 | 2 | 5 | 0.2817 |
| `sem_lse_train_tau` | 284 | 0.5035 | 2 | 4 | 0.2782 |
| `sem_margin_top2` | 284 | 0.4754 | 24 | 34 | 0.2183 |
| `sem_token_contrast_train_tau` | 284 | 0.5000 | 2 | 5 | 0.2852 |
| shuffled-language `sem_max_cos` | 284 | 0.5141 | 4 | 3 | 0.2394 |
| same-category shuffled `sem_max_cos` | 261 | 0.5249 | 5 | 4 | 0.2452 |

On the 261-bank same-category-control subset, the deployed selector reaches
0.5211 Acc@50, real-language `sem_max_cos` reaches 0.5172, and both
shuffled-language and same-category shuffled `sem_max_cos` reach 0.5249.

## Decision

Close the current semantic-projection reranking/readout family. It is not a
language-specific selector: shuffled-language and same-category controls do
not underperform the real-language score, and real-language semantic scores do
not exceed the deployed selector. The projection is already optimized by an
existing loss, so adding it back as a reranker would also be a selector/readout
variant outside the active research scope.

This is a diagnostic closure, not a claim that semantic alignment is useless,
that `loss_sem_align` never influenced training, or that a jointly trained
structural mechanism involving language is impossible. No model, config,
checkpoint, queue state, or training budget changed.
