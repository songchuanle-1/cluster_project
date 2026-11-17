# Independent Native Followups And Matched Resources

Continue revision2, no further implementation changes. First-pair full native
backward passed for both matched branches and the physical independent package.
Run the same independent package on frozen TRAIN second pair101,124, using the
same full4group loader/random order as prior controls; retain expected scans,
annotation IDs and offsets0,406,1847. Keep original25%cap and no optimizer.

Resource protocol is existing tools/validate_hqi.py/profile and train.py's
full-model FVCore predict call, not the synthetic bench_cluster_att sweep.
Fresh baseline and independent processes on same server3GPU1; same frozen M95
weights, original VAL first sample0 ONLY for computational profiling, one
language expression, batch1, workers0, eval/no_grad, warmup20, repeat100.
No VAL metric selection, tuning, new sample search, test-set evaluation or training.
Record FVCore counted full-model FLOPs/by-module and all unsupported operations;
same<=10G historical counted metric, not a new one-sided supplemental rejection.
Missing/incomplete profiler is unknown, never0orPASS. Use synchronized wall
clock median/P90 and full-model peak allocated/reserved bytes. Check original
25%allocator/NVML guards before/after; no instrumentation hooks in timed passes.
Report relative parameter/FLOPs/latency/memory and historical+15%memory rule.
Do not invent a latency cutoff or population benefit from resource success.
The shared pure-prefix checkpoint is disabled in eval in BOTH branches.

Native training-memory comparison uses the already completed matched first-pair
actual full backwards, not a partial failed forward. Full independent second-pair
validation broadens the frozen native cohort; neither run performs optimizer steps.
