# PSNC actual raw review and owning-root admission draft

`review_psnc.py` is a pure-JSON/local-file semantic review. It derives common,
resource and execution-chain functions from the actual dfb6440d PSBR reviewer;
its native checks are PSNC-specific. Five mutated-data refusals were actually
run without torch or native execution. `actual_four_result_review.json` binds
all four real completed requests and records observed results, not admission.

`admit_psnc_draft.py` is a new root-only adaptation of dfb6440d/admit_psbr.py.
The default requires actual proof/source checks and returns without standard,
receipt or shared-state writes. Its only execute switch is `--execute-root`.
No code in this directory performs SSH, GPU/model execution, source sync or
training dispatch. The draft itself has NOT been executed for admission.

Root usage, only after true main HEAD43 ff promotion and real independent proof:

    python -B -X utf8 <this-dir>/admit_psnc_draft.py --independent-review <absolute-actual-mdc-JSON> --independent-sha <actual-SHA>
    python -B -X utf8 <this-dir>/admit_psnc_draft.py --independent-review <absolute-actual-mdc-JSON> --independent-sha <actual-SHA> --execute-root

Independent proof schema is agreed with mdc: status
FOUR_ACTUAL_PSNC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED;
exact candidate_id/code_commit/goal_sha256, material_concerns=[], and raw_results
with four mode/target/execution_path/execution_sha256/result_sha256/request_id
entries. There is no fabricated/default independent SHA.

Default checks bind actual current owner/environment/target, unchanged original
context/deadline, true main HEAD43, empty index/protected28 status and bytes,
eight candidate source Git blobs plus exact native YAML/Git blob, actual
semantic report and independent four-raw request identities. Admission uses
the unchanged canonical closure.admission and foreground budget before queue.
It preserves original preparation references and takes a history snapshot, then
updates the current worker/adapter/status fields to actual completed state.
M206 remains exactly unchanged. Any dispatch is a separate root operation.

Numeric observations do not create a QtQ/mean threshold. Manifest1e-6 remains
unchanged and actual analysis/synthesis error0 is reported. Offdiagonal and full
zero/singleton/affine/identityQ FP32 controls remain NOT_RUN; empty/pad/singleton
counts0 are not empirical coverage. Smoke peak includes observer/reference
work, pure TRAIN/buffer values/no-cluster baseline/efficacy are UNKNOWN.

Like the previous actual root helper, execute creates exclusive standard files,
then a decision and receipt before final canonical budget/queue publication.
If an exception occurs after a write, preserve those artifacts and reconcile
actual state; do not blindly rerun or overwrite. An exception is not a queued
or launched experiment. Default mode writes none of those artifacts.
