# Frozen Bank Error Budget Audit
Completed 2026-09-13T10:12:37.614849 Asia/Shanghai.

## Question And Protocol
Check whether stored bank limitation and selection gap exactly reconstruct
selected-mask error. All 284 paired descriptions, 71 scenes with four each,
128 candidate IoUs per model-description; no missing or duplicate identities.
Both summary hashes, assignment/protocol and five source-code hashes verified.
All 568 selected/oracle indices checked against their actual candidate arrays.

## Results
```json
{
  "models": {
    "baseline": {
      "records": 284,
      "mean_selected_iou": 0.5359141476531054,
      "mean_oracle_iou": 0.8342458224842246,
      "mean_bank_limitation": 0.1657541775157754,
      "mean_selection_gap": 0.2983316748311192,
      "success": 171,
      "recoverable": 90,
      "bank_limited": 23
    },
    "m95": {
      "records": 284,
      "mean_selected_iou": 0.5022166055171344,
      "mean_oracle_iou": 0.8481078786959111,
      "mean_bank_limitation": 0.1518921213040889,
      "mean_selection_gap": 0.3458912731787767,
      "success": 158,
      "recoverable": 111,
      "bank_limited": 15
    }
  },
  "m95_minus_baseline": {
    "mean_selected_iou": -0.03369754213597098,
    "mean_oracle_iou": 0.013862056211686458,
    "mean_selection_gap": 0.047559598347657495
  }
}
```
Every record satisfies:
1-selected = (1-oracle) + (oracle-selected).
The paired mean identity is delta_selected = delta_oracle - delta_selection_gap.
The full scene aggregates and paired ID manifest are in audit.json.

## Interpretation And Limits
This is an arithmetic decomposition, not a causal allocation of model error.
The two models have different candidate masks, so selection-gap differences
do not isolate the selector. Oracle uses labels and is not deployable.
These are selected validation-bank results, not full-validation metrics,
independent generalization evidence or historical training-target verification.
No population interval is inferred from this selected bank. Do not mix with
original D1 or the 42-record outcome-selected casebook. No training admission.
