"""MIC deployment plan only. Default NOP; no Git, SSH, GPU or lifecycle writer."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
EXPECTED = {
    "token": "3b2b394d2fa242b19bbf4fef5ea11c67",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-05T13:07:08.623175+00:00",
    "deadline_at": "2026-11-05T14:07:08.623175+00:00",
    "context_sha256": "fe48ed24dba1c4e039abbf0c098ace6ec43bad7c5c91b3def914f40e492dc065",
    "pending_sha256": "8a63b7b374f3cd520c81f28baae4a09b5f9266b53b45eafd4f65e40893922d77",
}
CHILD = "01a1a684-e37c-7023-a69a-924d4014a2d5"
SOURCE = "07ef534a6e44f22bd7b2d083550ebd7823d1d3d3"
BASE = "6bc36adfe42764aac2209e6600fb3a783e2fa374"
CONFIG = "configs/Quard/ctf_hcg_csort_mic/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mic.yaml"
CID = "hierarchy-ancestry-mobius-interaction-composition"
UUID = "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
NEC = ROOT / "pipeline/diagnostic_bundles/tick_692e522c"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def ref(path):
    return {"path": Path(path).relative_to(ROOT).as_posix(), "sha256": sha(path)}


def guard():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {k: owner.get(k) for k in EXPECTED} == EXPECTED
    assert os.environ.get("CODEX_THREAD_ID") == CHILD != EXPECTED["thread_id"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(EXPECTED["deadline_at"])
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == EXPECTED["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == EXPECTED["pending_sha256"]


def make_plan():
    references = [
        NEC / "nec_overlay_promotion_active/dispatch_nec_once_v2.py",
        NEC / "nec_overlay_promotion_active/fast_forward_tested_nec.py",
        NEC / "nec_overlay_promotion_active/admit_nec_queue.py",
        NEC / "nec_overlay_promotion_active/nec_evidence.py",
        NEC / "nec_overlay_promotion_active/dispatch_nec_immutable_bindings.json",
        NEC / "prepare_nec_runtime.py",
        NEC / "nec_runtime_preparation.json",
        NEC / "nec_runtime_binding_update.json",
        NEC / "nec_overlay_promotion_active/deployment_notes.json",
        ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_version_prepare/isolated_source_version.json",
        ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_compatible_source_independent_review.json",
        ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_independent_review.json",
        ROOT / "pipeline/diagnostic_bundles/tick_abb177b5/mic_actual_partial_independent_review.json",
    ]
    identity = {
        "id": "M229-MIC", "candidate_id": CID, "config": CONFIG, "code_commit": SOURCE,
        "goal_sha256": "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85",
    }
    return {
        "schema_version": 1,
        "status": "PLAN_ONLY_DEFAULT_NOP_NO_DEPLOYMENT_OR_DISPATCH_AUTHORITY",
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "owner_provenance_only": EXPECTED, "actual_author_child_thread": CHILD,
        "scope": "Read-only source review plus this private plan. No actual Git/SSH/GPU, source promotion, runtime creation, SERVERS/queue/research/admission mutation.",
        "identity": identity,
        "version_roles": {
            "tested_candidate_source": SOURCE, "single_source_parent": BASE,
            "expected_local_primary_before_ff": BASE,
            "actual_diagnostic_runtime_commit": BASE,
            "actual_diagnostic_runtime_root": "/data/songcl/Project/Cluster_project/Cluster_nec_20261104",
            "proposed_training_runtime_commit": SOURCE,
            "proposed_new_training_runtime_root_not_created": "/data/songcl/Project/Cluster_project/Cluster_mic_20261105",
            "protected_remote_roots": {
                "/data/songcl/Project/Cluster_project/Cluster_nec_20261104": BASE,
                "/data/songcl/Project/Cluster_project/Cluster_resume_wfc_20261104": "94c4fe61b38f46f321a7ee84236fea70ade04d9b",
                "/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1": "4457a46f9075f61e83340aa0f0af87d5bf4e986c",
            },
            "historical_LFT_receipt_commit": "4457a46f9075f61e83340aa0f0af87d5bf4e986c",
        },
        "reuse_decision": {
            "reuse_algorithms_only": True,
            "old_scripts_directly_executable_for_MIC": False,
            "reasons": [
                "Old NEC promotion guard imports expired692 owner; evidence module expects NEC identities/base4457/diagnostic runtime94 and NEC four-arm filenames.",
                "Old ff helper explicitly verifies child6bc of4457; MIC is exact-nine07ef child6bc. A global version replacement would corrupt distinct parent/runtime/historical roles.",
                "dispatch_v2 immutable-admission catalogue can be adapted by explicit MIC identities and fresh hashes. Do not rerun diagnostic evidence.require_execution/reviewed after the deployed runtime pointer changes.",
                "The v2 Markdown protocol reader correction must remain: immutable protocol refs are hashed with parse=False, not parsed as JSON.",
            ],
        },
        "required_actual_evidence_before_any_promotion": [
            "Keep the two actual old-owner TRAIN2/common-init results under their true abb177b5 headers. Keep the known prelaunch resource refusal and original intent.",
            "Obtain the missing actual candidate resource arm under a new current lease/stage. Validate paired fixture/input SHA, original fvcore handler hashes and complete unsupported list; resource results are not assumed by this plan.",
            "Produce actual MIC smoke/resource/constraints summaries and independent actual-result review. Same-code valid old evidence may be referenced by immutable hashes without relabeling its owner/runtime.",
            "Require original whole-model<=10G and original conditional+15percent memory/+0.003 retention policy. No extra numerical or latency gate; efficacy/novelty remain UNKNOWN.",
        ],
        "standard_native_smoke_fields": {
            "identity": identity, "steps": 2, "losses": "two actual finite MIC losses",
            "native_data_loaded": True, "backward_finite": True, "intended_path_observed": True,
            "split": "train", "command": "actual tools.train.train two-natural-batch command",
            "data_source": "actual original TRAIN loader and fingerprints",
            "evidence": "immutable actual raw results/current reviewed summaries, with path+sha256",
            "paired_validation": "actual two batch records and shared named-parameter names/shapes/hash equal; original3LN retained; whole MIC core finite/nonzero original-loss weight gradient and actual update",
        },
        "canonical_receipt_fields": {
            **identity, "profile": "experiment_first",
            "authorization": {"path": "pipeline/authorizations/experiment_first_20261021.json",
                              "sha256": "2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8"},
            "native_smoke": "actual MIC native smoke path+sha256",
            "decision": "actual project decision path+sha256",
            "gates": {n: {"passed": "true only after actual review", "evidence": "nonempty path+sha256"}
                      for n in ("native_backward", "resources", "independence", "constraints")},
            "destination": "pipeline/admissions/M229-MIC.json",
        },
        "minimal_order_after_actual_gates": [
            "Freeze current root-owned protected_assets_before: actual HEAD6bc, original28 dirty file bytes/status, no staged changes, all existing index/tree entries, WFC9/LFT9 plus NEC source, prior ledgers and LFT/M206 holds.",
            "Adapt fast_forward_tested_nec algorithm with explicit BASE6bc/TESTED07ef and MIC exact9 manifest. Verify one parent, diff exactly9A, prior tree entries unchanged, no path collision and all9 blobs match actual tested hashes.",
            "Under project lock, write a unique ff intent and run merge --ff-only07ef with original no-autostash/no-hooks/no-CRLF safeguards. No reset/stash/clean/force. Preserve prior index entries and empty staged diff; adding9 legitimately updates index rather than preserving its raw file SHA.",
            "Write actual MIC decision/receipt and validate closure.admission(ROOT,task) plus closure.validate_foreground_dispatch_budget(ROOT,prospective_queue,task) before adding one FIFO waiting task.",
            "Adapt prepare_nec_runtime into a separately reviewed MIC root helper: bundle07ef excluding6bc; create a NEW detached07ef remote worktree. Never ff, reset, replace or mutate source in protected6bc/94/4457 roots; inspect any existing target instead of replaying.",
            "Verify new root, environment/assets, eight actual source hashes, original YAML and same-SHA ignored extension; apply only existing deterministic YAML path mappings. Freeze actual runtime proof and old-root before/after equality.",
            "Record a project-scoped SERVERS.server4.remote_code_root-only change to the independently verified new root. Preserve GPU list, UUIDs, overlay,max1,20000MiB, pauses, other servers and scheduler. Canonical strict closure reloads SERVERS; merely passing remote_code_root or inventing task.isolated_runtime will not route cluster correctly.",
            "Freeze a fresh MIC immutable admission/source/protocol/standard/peer/runtime/ff catalogue. Adapt dispatch_v2 guards/protection/strictSSH without globally changing old version roles. Default NOP must precede explicit root execution.",
            "Under project lock and fresh physical checks, invoke canonical _process_queue EXACTLY ONCE, with only MIC eligible waiting and no registered/claiming/uncertain GPU0 project slot. Verify native training steps increase. Preserve any request/claim/PID on uncertainty and reconcile; never retry blindly.",
        ],
        "runtime_extension": {
            "source_current6bc": "/data/songcl/Project/Cluster_project/Cluster_nec_20261104/framework/lib/pointgroup_ops/pointgroup_ops_ext.cpython-310-x86_64-linux-gnu.so",
            "relative_path": "framework/lib/pointgroup_ops/pointgroup_ops_ext.cpython-310-x86_64-linux-gnu.so",
            "sha256": "c86f516858d480e2583a437deb598279bc626e74975a060b17d75bf03f630033",
            "rule": "Verify source hash, copy2 to missing destination, verify identical hash and check-ignore; no rebuild or replacement of tracked code.",
        },
        "deterministic_yaml_mapping": [
            {"source": "/home/songcl/data/data", "server_key": "data_root", "current_destination": "/home/songcl/data/data"},
            {"source": "/home/songcl/3dres/project/cluster_project/Checkpoints", "server_key": "work_dir",
             "current_destination": "/data/songcl/Project/Cluster_project/Cluster_checkpoints"},
        ],
        "waiting_task_fields": {
            **identity, "label": "MIC ancestry Mobius interaction composition",
            "admission_receipt": "pipeline/admissions/M229-MIC.json", "status": "waiting",
            "gpu": "0", "server": "server-4", "profile": "experiment_first",
            "requires_exclusive_ownership": False,
            "resource_authorization": {"path": "pipeline/authorizations/server4_gpu0_overlay_20261104.json",
                                       "sha256": "783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88"},
            "must_be_absent": ["pid", "resume_from", "dispatch_hold", "pending_progress", "uncertain prior launch"],
        },
        "single_canonical_dispatch_call": (
            "mon._process_queue(queue, 'server-4', server['host'], server['user'], str(ROOT), "
            "set(), {'0'}, events, max_tasks_per_gpu=1, allow_external_overlay=True, "
            "task_memory_mb=20000, remote_code_root=server['remote_code_root'], "
            "current_tasks=0, max_tasks_total=1)"
        ),
        "dispatch_wrapper_required_guards": [
            "Actual root thread/current owner/context/pending/deadline, current immutable receipt and exact source/runtime proof, no previous dispatch intent/result/transport call.",
            "Only physicalGPU0 UUID958; strict known-host SSH/songcl/.115 and hostname dl04-MS-7E06. Keep v2 query rewrite to nvidia-smi -i0; refuse any unexpected other-card query.",
            "All3cooperative training/diagnostic/exclusive locks and real free memory>=20000MiB at actual Popen; external contexts preserved, no external-idle gate and no signals.",
            "One native Popen maximum, deadline check immediately before Popen, selected-card projectmax1, original canonical admission/budget/FIFO/progress verifier.",
            "Preserve nontarget queue/running/CSV/candidate digests/ledgers and user28/prior index and source files before and after; restore mon.ssh/environment in finally.",
        ],
        "unsupported_runtime_shortcuts": [
            "Do not invoke old NEC scripts unchanged, globally replace6bc or4457, or mutate old diagnostics to claim runtime07ef.",
            "Do not rely on task.isolated_runtime: existing generic override support is scoped to another project, and strict cluster closure reloads live SERVERS.",
            "Do not use only PID or registry running as launch proof; increasing native training steps are required.",
        ],
        "references": [ref(p) for p in references],
        "actual_source_promotion": "NOT_RUN", "actual_runtime_deployment": "NOT_RUN",
        "actual_admission_or_dispatch": "NOT_RUN", "efficacy": "UNKNOWN",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show-plan", action="store_true")
    parser.add_argument("--write-plan", action="store_true")
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if args.execute_root:
        raise SystemExit("PLAN_ONLY: this script has no deployment/dispatch implementation; root must review MIC-specific execution helpers.")
    if not args.show_plan and not args.write_plan:
        print(json.dumps({"status": "DEFAULT_NOP_PLAN_ONLY", "candidate_id": CID,
                          "source_commit": SOURCE, "source_promotion": False,
                          "remote_deployment": False, "dispatch_invoked": False}))
        return
    plan = make_plan()
    if args.write_plan:
        guard()
        with (HERE / "deployment_plan.json").open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
        guard()
        print(json.dumps({"written": ref(HERE / "deployment_plan.json")}))
    else:
        print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
