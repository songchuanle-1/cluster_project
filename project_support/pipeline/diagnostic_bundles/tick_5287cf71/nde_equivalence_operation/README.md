# Fresh standalone revision1 equivalence preparation

This packet is preparation only. No operation_release.json, actual EQ request,
intent, transport, GPU operation or model import was created or performed.

The f653 standalone remote_ops.py is copied byte-for-byte. The root wrapper has
exactly one deterministic sibling locator replacement: nde_operational_active
becomes nde_resource_operational_active. Every function AST is unchanged; the
whole module AST is identical after normalizing that one literal. Existing
original 1020/free20000/max1/three-lock/overlay/prior-failed and no-replay guards
remain in place. The existing staged EQ entry/model/reference/runtime bytes are
reused from nde_resource_native_active; no model source/revision is created.

A distinct equivalence_capability.json limits this operation to ONE standalone
revision1_equivalence AFTER BOTH current-owner ordinary champion and candidate
resource arms are independently verified terminal rc0. Any failed, missing,
uncertain or blocked arm blocks EQ. The original _previous_complete guard remains
unchanged and continues rejecting failed/uncertain prior requests. Root must
verify both successful arms and exact chain before issuing the separate release.

inputs.json intentionally has null future actual binding/manifest/lease/release
hashes. No actual chain is claimed. Root must finalize these hashes only from the
actual current-owner chain, regenerate the metadata hash graph and obtain an
independent operation/scope/actual-chain review before creating the exact static
operation release or a unique EQ intent/request. This draft is not runnable as-is.

The wrapper remains default NOP. Following actual prerequisite verification and
release only, its exact local invocation is python -B run_equivalence_operation.py
--execute-root --operation run. Existing intent/journals force reconciliation.
Exact remote command remains the pinned project_cluster interpreter with -B,
<stage>/equivalence_diagnostic.py --lease <stage>/execution_lease.json. No native
TRAIN2/common835 repetition, ordinary worker-mode extension or crash bootstrap.

Require terminal rc0, exact owner/source/runtime/root/UUID/producer/result hashes,
equivalence_passed, distinguishing_control_passed, all caller_RNG_restored flags,
native_data_loaded=false and native_TRAIN_steps=new_training=0. Preserve failed or
inconclusive fixed fixtures without resampling or tolerance changes. This fixture
cannot establish native full-model/task-loss equivalence, resources or admission.
