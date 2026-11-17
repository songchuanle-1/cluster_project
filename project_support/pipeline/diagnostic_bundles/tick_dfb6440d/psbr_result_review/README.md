# PSBR raw-result review

This stdlib-only reviewer reads the exact four-result PSBR adapter execution directory. It does not run training, SSH, torch, CUDA, synchronization, or scheduling. It creates only a fresh review JSON in this directory. It never writes a standard PASS artifact, admission receipt, or queue item.

`review_directory` verifies immutable prepared/release/source hashes; exact original binding, manifest and lease; four original requests; constructed Popen commands/direct terminal waits and result identities; then the actual native semantics and paired inputs. An empty early `/proc` argv remains explicitly unobserved and is not independent process identity proof for later signals. It never renews or replays the old lease.

The PSBR smoke review requires two original TRAIN batches, finite losses and actual criterion backwards/optimizer steps, actual finite nonzero Wx/Wh/Wo weight gradients and per-step weight changes, at least one truly supported nonsingleton parent group per batch, original support/group/order/reset/inverse observations, raw-bank/ID/map preservation, raw CSORT objects, exact PSBR HCG input, and the original single inst update path. It does not infer an offdiagonal Jacobian or task benefit from Wh updates. Raw centroid vectors are not stored, so external re-sorting is not claimed; actual order validation is the frozen hash-bound worker observation.

The original resource protocol is bs1/lang1/warm20/repeat100, unchanged fvcore handlers, 121 native prediction calls, measured 100 timings with recomputed median/P90, same paired input, disclosed unsupported operators, and candidate counted FLOPs <=10G. The existing observed allocated-memory +15% condition is reported for the owning root's retention decision, not silently cleared or turned into a new gate. Smoke peaks include observer overhead; pure TRAIN memory remains UNKNOWN. No offdiagonal/reset-state probe, full common-state exact-hash gate, zero-unsupported requirement, or new latency gate is added.

Recorded common initialized named parameters exclude only replaced middle FFN/new recurrence and retain middle LN. Their names/counts/hashes and original fine/coarse initial hashes are compared and reported. Differences are not a new exact-full-state acceptance gate; buffers/full common state were not recorded. Actual TRAIN batch fingerprints, seed/pretrain/loader and prediction input pairing are required.

Run only after the owning root has four actual raw executions:

    python -B -X utf8 review_results.py --project D:/project/cluster_project --execution-dir D:/project/cluster_project/pipeline/diagnostic_bundles/tick_dfb6440d/psbr_execution --report D:/project/cluster_project/pipeline/diagnostic_bundles/tick_dfb6440d/psbr_result_review/actual_four_result_review.json

Offline tests read actual immutable local raw results and mutate deep copies in memory. Their modified records are refusal fixtures, never execution evidence. The resource-only fixture reads actual HRC resource observations solely to exercise the common unchanged numeric schema; it is never accepted as PSBR paired evidence. No test writes raw files.

The owning root separately reviews constraints, independence, current policy and any memory retention condition before producing canonical standard artifacts/admission. Actual efficacy remains UNKNOWN until native training evaluation.
