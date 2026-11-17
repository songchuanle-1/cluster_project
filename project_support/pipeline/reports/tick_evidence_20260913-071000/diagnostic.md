# Frozen Nearest-Query Assignment Audit
Completed 2026-09-13T07:10:26.611766 Asia/Shanghai.

## Question And Protocol
How often does nearest-query union add a positive beyond target membership,
and how often is that added query actually selected? Existing 568 frozen banks
only; no checkpoint execution, new sampling, relabeling or training.
Assignment SHA256: 9442824e45979fa3891895a90edf7b993d666463773a72dd3e9fbd6b73c8aadd. Protocol and all five code hashes verified;
both upstream summary hashes verified. Full identity list is audit.json records.

## Results
```json
{
  "baseline": {
    "total": 284,
    "scenes": 71,
    "no_target_members": 10,
    "nearest_adds_positive": 34,
    "selected_nearest_only": 0,
    "selected_nearest_only_failures": 0,
    "positive_failures": 9
  },
  "m95": {
    "total": 284,
    "scenes": 71,
    "no_target_members": 11,
    "nearest_adds_positive": 35,
    "selected_nearest_only": 2,
    "selected_nearest_only_failures": 1,
    "positive_failures": 9
  }
}
```
All 568 unique rows joined to selected indices; zero missing or duplicate IDs.
Membership union nearest is validated on every row. Outcome threshold is >.5.

## Interpretation And Limits
An added positive is not necessarily selected and selection does not establish
causal harm. These are evaluation-bank labels, not historical training targets.
No population failure rate, independent replication or supervision-defect claim.
Counts are descriptive within the existing diagnostic protocol; no mixing with
the separate 42-record outcome-selected casebook or original D1 denominators.
No target relabeling or generic score/loss successor is admitted from these counts.
Derived mechanism, primary-source distinction and matched falsification remain open.
