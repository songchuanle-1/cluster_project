# Exact-Preparation Resource Regression

- Same stable BPS candidate and immutable optimized v3 source manifest.
  Numerical config, seed1999, epochs50/max_iters70, weights and loss unchanged.
- Primary measurement is the existing real-VAL batch1 prediction protocol:
  baseline, champion, candidate, each a clean process, warmup20/repeat100,
  median/P90, allocated/reserved peak memory, historical fvcore FLOPs.
- Supplemental native TRAIN forward/backward uses the existing common
  backbone checkpoint, original frozen dataset and original random state.
  Every target uses identical groups and input fingerprint.
- Fixed cases: stress=[5743,7787] (batch2), nonevent=[0,44] (batch2),
  single=[452] (batch1). They were not selected from performance outcomes.
- Use the same warmup20/repeat100 for all three targets on every case.
  Finite losses/gradients required; zero optimizer updates. Check candidate
  nonevent computes zero pair fields and all expressions are inactive.
- Preserve previous v2 measurements. Compare source/config/checkpoint/sample
  and protocol identities before deriving relative metrics.
- Both project diagnostic locks, GPU7 UUID/host and free>=32768MiB checked
  before each run. Preserve foreign PID262355. Bound each run to240seconds.
- Shared-GPU latency is a resource observation, not an exclusive speedup.
  Instrumented profiler data is not substituted for this uniform protocol.
- Primary FLOPs<=10G and memory+15% rule unchanged. Efficacy, retention and
  subgroup harm require actual training; no pre-training mIoU effect gate.
