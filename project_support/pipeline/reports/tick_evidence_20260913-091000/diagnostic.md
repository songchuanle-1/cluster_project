# Frozen Bank Scene Outcome Audit
Completed 2026-09-13T09:10:26.515290 Asia/Shanghai.

## Question And Protocol
Are the previously counted 17 success gains and 30 losses concentrated in the
same scenes? Use all 284 paired descriptions in the frozen expansion bank,
four per scene, with unchanged IoU>.5 threshold. Recheck both source summaries,
assignment/protocol and five source-code hashes. No training or new sampling.
Full 71-scene manifest and upstream audit hash are in audit.json.

## Results
```json
{
  "pairs": 284,
  "scenes": 71,
  "scenes_with_gain": 17,
  "scenes_with_loss": 23,
  "scenes_with_both": 2,
  "net_success_histogram": {
    "0": 35,
    "-2": 5,
    "-1": 15,
    "1": 15,
    "-3": 1
  },
  "total_gains": 17,
  "total_losses": 30
}
```

## Interpretation And Limits
Gain/loss scene counts overlap: a scene can contain both kinds of transition.
Net success zero can mean no transitions or cancelling transitions.
These are descriptive counts for a selected validation diagnostic bank only.
No population confidence interval, independent generalization estimate or
causal mechanism is established. Do not substitute this bank for full-validation
champion metrics or combine it with original D1 or the 42-record casebook.
Scene grouping prevents treating descriptions as independent evidence but
does not repair selection bias. Core mechanism admission remains incomplete.
