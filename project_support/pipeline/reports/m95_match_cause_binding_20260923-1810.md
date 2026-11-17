# M95 Native Matcher-Cause Binding Correction

2026-09-23 18:10 Asia/Shanghai. Event-mode continuation of three due
diagnosis IDs; no native model execution or efficacy result.

The prior opt-in producer passed the native matcher input tuple directly to
`matcher_cause_record`. The native `match_sampled_ins` signature in the exact
M95 loss is `(sampled_ins_lbl, obj_ids, sampled_pos, obj_pos)`, whereas that
helper expects `(sampled_pos, obj_pos, labels, object_ids)`. This would have
failed the coordinate/axis checker on a native run. A dedicated adapter now
binds the source argument order explicitly before verification. The existing
positive-vector and `(query, GT)` pair checks remain unchanged. The prior
"ready" report was static readiness only, not a successful native capture.

One new native-order regression plus the existing manifest and matcher
contract tests pass: 15/15. The corrected producer SHA256 is
`c8cb99b02b412761c4c56890132a93afeb0a63d1fa66275105f45f82d55e0d76`.
These are CPU synthetic tests, not native validation. No model forward,
backward, resource or admission gate passed.

Server-6 GPU7 targeted read-only query: one external PID using 41,996 MiB;
42,025 MiB used, 39,055 MiB free and 100% instantaneous utilization.
No process was touched. Defer the full 256-row capture until actual capacity,
host/runtime/data/checkpoint and code provenance are verified. The six
outside-seed positives and four same-physical-ID classes remain unattributed;
supervision still lacks a distinct causal unit and matched controls. Both
queue slots remain empty.
