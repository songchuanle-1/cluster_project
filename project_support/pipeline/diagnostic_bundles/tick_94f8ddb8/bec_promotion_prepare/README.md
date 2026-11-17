Private BEC R1 promotion preparation

This directory is disabled by `promotion_common.DRAFT_EXECUTION_ENABLED = False`.
It performs no work on import or on a default CLI invocation. Only root may make
a reviewed sibling copy with that one flag changed to True. The independent
four-result review must have an actual path, SHA and expected status before any
phase is allowed. Static preparation is not an admission receipt or a launch.

The tested candidate is M215-BEC / 026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563,
whose sole parent must be current primary CTS 4e80006047d5cb3dcdfb9c1102e02c33f354a07d.
Only the eight BEC model files and original YAML in this exact tested child may
be added by `merge --ff-only`. No new commit/reset/stash/clean/forced checkout is
used. Source2ef, unchanged worker7e5 and implementation R1 preregistration3fa are
distinct from historical source9b and its earlier resource-trace failure.

Current and native-test owner are the actual six fields of tick94f8ddb8, with
the original 15:57:12.614254 UTC deadline. Current resource policy and grant allow
physical GPU0 only. Raw results are the four original envelopes in the sibling
`bec_r1_execution` directory. The original source, request identities, model
packages, manifest/lease and exact reviewer are rechecked; no old9b result is
relabelled as026c. Native technical success does not establish efficacy.

Execution order for a reviewed root sibling copy:

1. `python -B -X utf8 fast_forward_tested_bec.py --execute-root --bec-native-round-settled`
2. `python -B -X utf8 admit_bec_queue.py --execute-root`
3. `python -B -X utf8 dispatch_bec.py --execute-root`

Each phase holds the canonical project lock and writes a durable
`bec_phase_<phase>_intent.json` before its mutations. Existing intent/result or
an uncertain launch requires read-only reconciliation, never blind replay.
Phase result filenames differ from `bec_dispatch_result.json`, avoiding the
prior same-path double-write collision. A partial ff/admission/queue update is
not repaired automatically.

The original28 user files, status and empty index are protected. M211/BTC,
M212/BCR, M213/BFC and M214/CTS original terminal status/identity, archive and
receipts remain intact; CTS stays stopped_unknown with cause UNKNOWN. The only
permitted later CTS log_local value is this tick's independently SHA/size checked
single-file archive. M206 remains explicitly paused and cannot be resumed.

The dispatcher uses one canonical FIFO `_process_queue` call, strict pinned SSH
keys and hostname verification. Only physicalGPU0 is queried. A remote holder
keeps the training/diagnostic/exclusive flocks while checking UUID/idle/no compute
context and until the canonical native Popen command returns. The original
canonical source sync/admission/budget/native progress checks stay in force.
No native checks, Git mutations, SSH or shared writes are executed by the authors
of this preparation package.
