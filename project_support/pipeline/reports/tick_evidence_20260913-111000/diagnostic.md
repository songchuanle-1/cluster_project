# Paired Oracle Feasibility Audit
Completed 2026-09-13T11:10:37.198053 Asia/Shanghai.

## Question And Protocol
Does each frozen candidate bank contain any mask with IoU strictly greater
than .5 for the same description? This is a coverage diagnostic, not a selector
intervention. Join all 284 unique description IDs across 71 scenes, four each.
No missing or duplicate IDs. Verify assignment/protocol, five code hashes and
both upstream summary hashes. Verify oracle against actual candidate maxima.
Threshold .5 is inherited from prior success diagnostics, not optimized here.

## Results
```json
{
  "contingency": {
    "baseline_1_m95_1": 256,
    "baseline_1_m95_0": 5,
    "baseline_0_m95_0": 10,
    "baseline_0_m95_1": 13
  },
  "strata": {
    "baseline_1_m95_1": {
      "records": 256,
      "baseline_success": 168,
      "m95_success": 156
    },
    "baseline_1_m95_0": {
      "records": 5,
      "baseline_success": 3,
      "m95_success": 0
    },
    "baseline_0_m95_0": {
      "records": 10,
      "baseline_success": 0,
      "m95_success": 0
    },
    "baseline_0_m95_1": {
      "records": 13,
      "baseline_success": 0,
      "m95_success": 2
    }
  },
  "scene_counts": {
    "scene0030_00": 4,
    "scene0046_00": 4,
    "scene0064_00": 4,
    "scene0081_00": 4,
    "scene0086_00": 4,
    "scene0088_00": 4,
    "scene0131_00": 4,
    "scene0139_00": 4,
    "scene0146_00": 4,
    "scene0149_00": 4,
    "scene0153_00": 4,
    "scene0169_00": 4,
    "scene0196_00": 4,
    "scene0207_00": 4,
    "scene0208_00": 4,
    "scene0221_00": 4,
    "scene0222_00": 4,
    "scene0231_00": 4,
    "scene0246_00": 4,
    "scene0249_00": 4,
    "scene0251_00": 4,
    "scene0256_00": 4,
    "scene0277_00": 4,
    "scene0278_00": 4,
    "scene0300_00": 4,
    "scene0316_00": 4,
    "scene0328_00": 4,
    "scene0334_00": 4,
    "scene0338_00": 4,
    "scene0342_00": 4,
    "scene0351_00": 4,
    "scene0357_00": 4,
    "scene0377_00": 4,
    "scene0389_00": 4,
    "scene0423_00": 4,
    "scene0426_00": 4,
    "scene0430_00": 4,
    "scene0441_00": 4,
    "scene0488_00": 4,
    "scene0496_00": 4,
    "scene0518_00": 4,
    "scene0527_00": 4,
    "scene0553_00": 4,
    "scene0559_00": 4,
    "scene0575_00": 4,
    "scene0578_00": 4,
    "scene0580_00": 4,
    "scene0583_00": 4,
    "scene0591_00": 4,
    "scene0598_00": 4,
    "scene0599_00": 4,
    "scene0607_00": 4,
    "scene0609_00": 4,
    "scene0616_00": 4,
    "scene0618_00": 4,
    "scene0621_00": 4,
    "scene0629_00": 4,
    "scene0644_00": 4,
    "scene0648_00": 4,
    "scene0652_00": 4,
    "scene0663_00": 4,
    "scene0670_00": 4,
    "scene0678_00": 4,
    "scene0684_00": 4,
    "scene0689_00": 4,
    "scene0690_00": 4,
    "scene0693_00": 4,
    "scene0696_00": 4,
    "scene0697_00": 4,
    "scene0702_00": 4,
    "scene0704_00": 4
  }
}
```
The paired per-description stratum manifest and raw IoUs are in audit.json.
Strata report selected-mask success separately from oracle feasibility.

## Interpretation And Limits
Both-feasible failures establish that at least one usable candidate exists in
each respective bank; they do not hold masks fixed between models. Oracle
feasibility does not imply a deployable selector can recover the target.
This selected validation bank is not a population sample, independent test,
or matched causal intervention. No significance, full-validation metric,
supervision defect, new mechanism, or novelty claim is inferred.
No new model is scientifically admitted by this audit.
