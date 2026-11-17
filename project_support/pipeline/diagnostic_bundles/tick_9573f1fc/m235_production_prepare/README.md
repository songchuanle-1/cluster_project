# M235 current-owner complete production packet

Root executes; packet author has not used SSH, GPU, or queue mutation. Current owner 9573f1fc binds new producer sinc_path_prepare_9573f1fc and production sinc_path_prod_9573f1fc. Source b1e639b3 and canonical M235 admission remain byte-identical. Entry factory and lock core are reused byte-for-byte. The only environment base is immutable server4_conda_4ca73fba.sh. No old consumed entry is executed.

This packet requires a NEW root read-only runtime/source verification at ../m235_runtime_verification/runtime_verification.actual.json. Its exact interface is in sync_actual_contract.json. The proof honestly records new_sync_performed:false and the immutable prior canonical sync tick_6b23467a SHA 4a61ee880d3273bf8240bdf5c5011ea39d4d92f0f433b23f26937863a3c0a166. It cannot accept a relabelled old owner result. The old collect is historical evidence only; root performs new CPU collect and render in the new producer.

ROOTARGS: --admission D:/project/cluster_project/pipeline/admissions/M235-SINC.json --admission-sha256 ab1bc5d187022e26dbcbc1063c24a886c7429350739039aff06f51c1bbcb5169 --review ABS_CURRENT_PACKET_REVIEW --review-sha256 REVIEW_SHA --current-verification D:/project/cluster_project/pipeline/diagnostic_bundles/tick_9573f1fc/m235_runtime_verification/runtime_verification.actual.json --current-verification-sha256 ACTUAL_VERIFICATION_SHA

Run with python -B, PROJECT_ROOT set to D:/project, PYTHONDONTWRITEBYTECODE=1, GIT_OPTIONAL_LOCKS=0 and the current CODEX_THREAD_ID:

1. Independent packet review passes (independent_review_contract.json).
2. Root: run_setup_once.py --execute-root --action stage ROOTARGS
3. Root: run_setup_once.py --execute-root --action collect ROOTARGS
4. Independent actual collect review, then a genuine ALLOW_PRODUCTION_PATH_RENDER activation receipt.
5. Root: run_setup_once.py --execute-root --action render ROOTARGS --activation ABS_ACTIVATION --observation-review ABS_COLLECT_REVIEW --observation-review-sha256 COLLECT_REVIEW_SHA
6. Independent actual render review.
7. Root: clear_m235_hold_once.py --execute-root ROOTARGS --production-result ABS_RENDER_RESULT --production-review ABS_RENDER_REVIEW --production-review-sha256 RENDER_REVIEW_SHA
8. Root: dispatch_m235_once.py --execute-root with the same arguments.

Every script defaults to NOP; intent/request/result files are exclusive, and uncertain actions are preserved without replay. Collect_actual.json is the local transport wrapper; its observation.remote_result_sha256 is the exact remote actual_observation.json hash. Collect peer requires owner, passed:true, material_concerns:[], distinct reviewer_thread_id, source_commit, actual_observation_sha256 and collect_actual_sha256. Activation requires the same current owner/source/observation hash, admission_receipt_sha256, independent_observation_review_sha256, training_launch_authorized:false and no draft marker. Production peer binds production_result_sha256 to the local render_result.json hash.

Canonical admission, safe_sync/safe_launch, fresh GPU0 free memory >=20000 MiB, cap1, overlay policy, original three FLOCK inodes (dev66308, inodes92537152/53/54), host UID/UUID and progress gates remain. CPU collect/render does not demand an empty GPU. Dispatch observes current resources and project trainers before canonical dispatch. Source resolution scopes the real detached checkout and temporary server-copy new shim, restoring loader and preserving SERVERS SHA. Goal, SERVERS, scheduler and other jobs are unchanged by preparation. No signals, restarts, foreign-job changes, GPU1 or other servers. Root must still establish real PID/one-shot marker/optimizer progress after a launch.
