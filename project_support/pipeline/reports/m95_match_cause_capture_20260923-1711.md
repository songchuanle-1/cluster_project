# M95 Matcher-Cause Capture Readiness

2026-09-23 17:11 Asia/Shanghai. Event-mode follow-up for the three due
diagnosis IDs. No model execution or new efficacy observation.

The existing frozen TRAIN manifest producer now accepts
`--capture-match-causes`. At the criterion's unmodified query-level matcher
call it records sampled query coordinates and instance labels, ordered native
GT IDs and centroids, per-GT nearest queries and post-exclusion members.
The independent checker verifies coordinate/label consistency and equality
to native positives; a second assertion matches the native `(query, GT)`
pairs, retaining multi-GT assignments. The producer hashes the checker,
requires every manifest expression to carry the cause axis, and retains the
fixed 256-expression denominator. Without the flag, prior capture output
semantics remain unchanged.

Three new binding tests and six existing manifest tests pass locally; Python
compilation passes. These are synthetic/static tests, not native validation.
The existing five checker tests also passed in the previous tick. No native
matcher cause or query-state vector has been observed for the six outside-seed
positives or four same-physical-ID discordant classes.

Targeted server-6 GPU7 check: 42,025 MiB used, 39,055 MiB free, 100%
instantaneous utilization, one external 41,996 MiB compute process. No
process was touched. Native capture is deferred until occupancy, host/runtime,
data, checkpoint and code provenance can be verified under the whitelist.
Supervision still lacks a distinct expression-level causal unit and matched
native-positive/objectness/listwise controls. Identity still requires an
independent query-state capture. No admission, sync, enqueue or launch.
