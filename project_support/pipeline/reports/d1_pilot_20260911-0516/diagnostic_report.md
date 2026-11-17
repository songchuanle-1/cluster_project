# D1 Candidate-Bank Pilot
2026-09-11 05:19 Asia/Shanghai. Correctness pilot, not a trained variant.

## Protocol
Upstream review/design051200. Frozen v2 manifest
84a7d60f85ecd5bec44b77b304140ff00c8c1fa00177dc12ecf7ef5ebfabb468.
First two lexicographic diagnostic scenes scene0030_00/scene0046_00,
four frozen descriptions each. Baseline/M95: same eight inputs, seed1999,
singleton language batches. No reserved-scene inference or package changes.
Explicit audited modules; strict learned-state loading permits only two
verified equal historical nonpersistent buffers to be omitted in memory.

For candidate q: mask[n]=1[sigmoid(logit[q,superpoint[n]])>=.5],
GT[n]=1[y[n]>.5], IoU=intersection/(union+1e-6).
Selected index=argmax softmax(indis)[:,1]. All128candidates retained.
Original predict_by_feat called unchanged; selected probabilities/IoUs exactly
equal in all16 calls. This is same-forward equality, NOT repeated-forward
stability or historical full-validation replay.
Point-level oracle evaluated one candidate at a time, no Q-by-N allocation.
Saved logits/scores/indices/point mapping/GT support independent recomputation.

## Results
All metrics describe ONLY these eight examples/two scenes.

| Model | N | Selected a | Oracle o | Bank limitation 1-o | Selection gap o-a | Acc50 |
|-------|---|------------|----------|---------------------|-------------------|-------|
| Baseline | 8 | .538820513 | .892994612 | .107005388 | .354174100 | 5/8 |
| M95 | 8 | .550915219 | .889365964 | .110634036 | .338450745 | 5/8 |

| Scene | N | Baseline a / o | M95 a / o |
|-------|---|----------------|-----------|
| scene0030_00 | 4 | .485673234 / .933980510 | .485673234 / .927750722 |
| scene0046_00 | 4 | .591967791 / .852008715 | .616157204 / .850981206 |

Both models have3/8 selected failures(IoU<=.5) with oracle>.5; sameexamples:

| Scene | Object | Ann | Baseline a / o | M95 a / o |
|-------|--------|-----|----------------|-----------|
| scene0030_00 | 50 | 85 | 0 / .848289967 | 0 / .902010024 |
| scene0030_00 | 4 | 87 | 0 / .926151574 | 0 / .866299927 |
| scene0046_00 | 26 | 27 | 0 / .864908099 | 0 / .888059676 |

These demonstrate selection errors in these pilot examples, NOT population
prevalence or relation/anchor failure. No mechanism choice from two scenes.
Oracle headroom is not deployable gain. Verified 1-a=(1-o)+(o-a) is diagnostic
algebra, not novelty, and does not distinguish coverage from boundary roughness.

## Verification
- 7CPUunit tests pass0.004s: inclusive threshold/ties/point weighting/oracle,
  empty or single bank, NaN, bad mapping, empty GT/prediction.
- CPUreadback all16artifacts: SHA256, everycandidateIoU(tolerance1e-7),
  selected/oracleindex and binary masks verified.
- Crossmodel GT/GTsuperpoint/mapping equal; rawpoint/CLIP/scenegraph/source
  and worker hashes match. No CUDA initialized during CPUreadback.
- Localpython lacks torch; used existing server-4environment, no installation.
- Missing276/284diagnostic descriptions on69/71physicalscenes; noreserved4646
  descriptions evaluated. No pilotmissing data; all8/model completed.
- Peak torch allocation952.223MiB baseline/967.477MiB M95; inference loops
  4.355s/4.811s sharedGPU. NOT speed benchmark/trainingpeak/resourceadmission.
- GPU1free10601MiB at each preflight, allocatorcap4GiB; bothworkers exit0.
  Postflight21509MiB trainer-only. Fourtrainers preserved;M187epoch17.
- Helpers hashverified to bothservers/tmp/cluster_d1_pilot_20260911_0516;
  active tracked deployment diffs unchanged. No model/config/queue changes.
- 28pipeline tests pass3.509s. No worker/model crashes or repair attempts.

## Next Gate
Validate singleton versus saved historical language grouping/padding and
repeated-forward stability, then complete frozen diagnostics under resource
guards with explicit missing-data accounting. Baseline historical forward
identity/fullvalidation metrics still unverified.
Classify errors with stated annotation rules and scene-level uncertainty
before selecting ONE mechanism. Primary-paper novelty, derivation and matched
controls remain prerequisites; no new mechanism admitted.
