# Frozen Bank Paired Outcome Audit
Completed 2026-09-13T08:10:28.372796 Asia/Shanghai.

## Question And Protocol
Can the two 284-record evaluation banks be paired without missing IDs, and
what are their descriptive IoU>.5 outcome transitions? No new sampling,
checkpoint execution, training or relabeling. This is the expansion protocol,
not original D1 or the separate 42-record outcome-selected regression casebook.
Assignment, protocol, five code and two summary hashes verified.
All 568 assignment rows joined to summaries; full 284-pair manifest in audit.json.

## Results
```json
{
  "pairs": 284,
  "scenes": 71,
  "records_per_scene": {
    "4": 71
  },
  "transitions": {
    "False->False": 96,
    "True->True": 141,
    "True->False": 30,
    "False->True": 17
  },
  "missing_ids": 0,
  "duplicate_ids": 0
}
```

## Interpretation And Limits
Paired identity is necessary for paired comparison but does not establish
representative sampling, an independent test, or causal attribution.
These counts describe only this frozen diagnostic bank. A success transition
does not identify which architectural mechanism caused it. No uncertainty or
population estimate claimed; descriptions within a scene are not independent.
The audit closes an identity-comparability check, not scientific admission.
No novel forward/loss, matched mechanism control or generalized gain established.
