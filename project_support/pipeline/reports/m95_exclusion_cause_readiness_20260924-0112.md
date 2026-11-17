# M95 Exclusion Cause Readiness

2026-09-24 01:12 Asia/Shanghai. Event-mode continuation of three stable
diagnosis IDs. No native model execution or efficacy result.

The fixed six exclusion expressions (manifest indices 11, 43, 79, 88, 103,
253) contain 70 acceptable queries, none native-positive. Five lack a
target-seed selector, so a target-seed-matched contrast is unavailable there.
The saved labels do not identify which GT generated each native positive.

`scripts/m95_exclusion_cause_audit_20260924.py` now requires a complete
256-row opt-in native matcher-cause capture with the frozen manifest and M95
checkpoint. It binds the six rows by manifest index, scene and annotation;
checks native geometry, membership, positive vectors, counts and hard-IoU
outcomes; and records each positive query's nearest-GT or member cause and
target/other-GT binding. Target cause and acceptable mask remain different
observables. A missing target GT or mismatched capture fails closed.

Fifteen focused synthetic/contract tests pass, and both new scripts compile.
They do not validate host data or model behavior. Native producer, runtime,
data, checkpoint and GPU occupancy still require verification before capture.
One read-only GPU7 check: foreign PID 3694608, 41,996 MiB process memory;
42,023 MiB used, 39,057 MiB free, 0% instantaneous utilization. The foreign
allocation was left untouched. No native execution, backward, matched
intervention, resource measurement, mechanism admission or training occurred.

The supervision axis still lacks an expression-level causal unit distinct
from positive-set relabeling/listwise ranking and matched native-positive,
any-instance objectness and listwise controls. Keep all three IDs at diagnosis;
run the existing opt-in capture when authorized GPU7 capacity is clear, then
apply this checker and the preregistered four-scene query-state controls.
