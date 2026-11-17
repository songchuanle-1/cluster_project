Run once after actual canonical dispatch result exists, using the printed SHA of each actual result:

python -B construct_once.py --execute-root --production-result-sha256 RENDER_RESULT_SHA --dispatch-result-sha256 DISPATCH_RESULT_SHA

Defaults read ../rvec_setup_execution/render_result.json and ../rvec_dispatch_execution/rvec_dispatch_result.json; override paths only with actual artifacts. Requires current root foreground owner, GIT_OPTIONAL_LOCKS=0, PYTHONDONTWRITEBYTECODE=1. Produces ../dispatch_proof_execution/dispatch_proof.json and prints exact proof SHA. All production paths derive from actual render binding/files/artifact hashes; PID/log derive from actual dispatch plus current queue. The sole SSH probe validates hostname/uid/production bytes/cmdline/cwd/marker, then reads the same PID's /proc start tick twice. No guessed log, PID, marker or work directory. No Git, GPU queries/computation, signals, remote writes, source/pointer/queue mutation, or training invocation. Default NOP and exclusive intent/results preserve uncertainty.

Use the existing frozen observer unchanged, with the proof path/SHA just printed:
python -B ../launch_observe_prepare/observe_once.py --execute-root --label before --dispatch-proof ../dispatch_proof_execution/dispatch_proof.json --dispatch-proof-sha256 PROOF_SHA

When native progress has had time to advance, take a distinct sample:
python -B ../launch_observe_prepare/observe_once.py --execute-root --label after --dispatch-proof ../dispatch_proof_execution/dispatch_proof.json --dispatch-proof-sha256 PROOF_SHA --previous ../launch_observe_prepare/before.actual.json --previous-sha256 BEFORE_ACTUAL_SHA

Observer's native_step_growth_observed=true requires same PID/start_ticks/source and lexicographically greater [epoch,batch]. It reads at most128KB and uses the retained canonical parser for Train[E/total]:...| B/total or Epoch:[E][B/total]. before.latest_native_step=null cannot prove growth; preserve that record and use fresh labels for later observations. All-three-original-lock-inodes inheritance and error markers are also reported. Increasing step evidence is not a scientific efficacy, training completion, or exclusive performance claim.
