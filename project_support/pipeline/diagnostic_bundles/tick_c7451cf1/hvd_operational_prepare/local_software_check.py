"""Actual local software checks only; no Torch/model/Git/SSH/GPU operation."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import copy
import importlib.util
import json
import subprocess
import sys
from unittest.mock import patch
import prepare_hvd_operations as author

HERE = Path(__file__).resolve().parent
ROOT = author.ROOT
NATIVE = author.NATIVE
checks = []
refusals = {}


def record(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append({"name": name, "passed": True})


def import_local(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_refused(name, function, exception):
    try:
        function()
    except exception as error:
        refusals[name] = str(error)
        return
    raise AssertionError("Expected a real refusal: " + name)


def main():
    author.guard()
    record("actual_child_identity_no_root_environment_impersonation",
           author.os.environ.get("CODEX_THREAD_ID") == author.CHILD != author.EXPECTED["thread_id"])
    prep = author.read(HERE / "preparation.json")
    native = author.read(NATIVE / "preparation.json")
    manifest = author.read(NATIVE / "manifest_template.json")
    provenance = author.read(HERE / "port_provenance.json")
    record("all_operational_prepared_file_hashes_match",
           all(author.sha(HERE / n) == h for n, h in prep["prepared_file_hashes"].items()))
    record("all_native_prepared_file_hashes_match",
           all(author.sha(NATIVE / n) == h for n, h in native["prepared_file_hashes"].items()))
    for key, path in (
        ("native_preparation", NATIVE / "preparation.json"),
        ("native_manifest_template", NATIVE / "manifest_template.json"),
        ("native_source_version_binding", NATIVE / "source_version_binding.json"),
        ("release_template", HERE / "release_template.json"),
        ("root_launcher", HERE / "run_hvd_operation.py"),
        ("literal_port_provenance", HERE / "port_provenance.json"),
    ):
        record("exact_hash_ref_" + key, prep[key] == author.ref(path))
    for name in ("adapter.py", "remote_ops.py", "run_hvd_operation.py"):
        ast.parse((HERE / name).read_text(encoding="utf-8"))
    record("all_three_ported_python_files_parse", True)
    for old_name, new_name in (
        ("adapter.py", "adapter.py"),
        ("remote_ops.py", "remote_ops.py"),
        ("run_mic_operation.py", "run_hvd_operation.py"),
    ):
        expected, _ = author.literal_port(
            (author.OLD / old_name).read_bytes().decode("utf-8"),
            author.sha(NATIVE / "preparation.json"),
            author.sha(NATIVE / "manifest_template.json"))
        record("precise_reviewed_MIC_literal_port_" + new_name,
               (HERE / new_name).read_bytes() == expected.encode("utf-8"))
    active_keys = (
        "current_token", "stage", "tick_generated_at", "deadline_at", "physical_gpu",
        "gpu_uuid", "allowed_gpus", "context_sha256", "pending_sha256", "runtime_code_commit",
    )
    record("all_ten_native_execution_fields_remain_null",
           all(k in manifest and manifest[k] is None for k in active_keys))
    record("native_and_operational_metadata_are_disabled",
           native["draft_execution_disabled"] is True and prep["draft_execution_disabled"] is True
           and manifest["draft_execution_disabled"] is True and prep["operational_ready"] is False)
    absent_names = (
        "adapter_release.json", "native_manifest.json", "execution_lease.json",
        "execution_binding.json", "prepare_request.json", "stage_request.json",
    )
    record("no_active_release_binding_manifest_lease_request_present",
           all(not (HERE / name).exists() and not (NATIVE / name).exists() for name in absent_names)
           and not (HERE.parent / "hvd_execution").exists())
    command = [sys.executable, "-B", "-X", "utf8", str(HERE / "run_hvd_operation.py")]
    default = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
    default_data = json.loads(default.stdout)
    record("actual_root_launcher_default_is_NOP",
           default.returncode == 0
           and default_data["status"] == "DEFAULT_NOP_NO_ENTRY_OR_TRANSPORT"
           and default_data["candidate_id"] == author.CANDIDATE
           and default_data["code_commit"] == author.SOURCE
           and default_data["active_binding_created"] is False
           and default_data["native_executed"] is False)
    module = import_local("hvd_local_disabled_adapter_check", HERE / "adapter.py")
    class Tripwire:
        def call(self, *args, **kwargs):
            raise AssertionError("No transport is authorized in a software check")
    adapter = module.Adapter(transport=Tripwire())
    def forbidden_process(*args, **kwargs):
        raise AssertionError("No process/Git/SSH/GPU is authorized in adapter software checks")
    with patch.object(module.subprocess, "run", forbidden_process), \
         patch.object(module.subprocess, "Popen", forbidden_process), \
         patch.object(module.subprocess, "check_output", forbidden_process):
        details, checked_template = adapter._frozen_details()
        record("actual_adapter_frozen_hash_graph_verifier_accepts",
               details["source_commit"] == author.SOURCE and checked_template == manifest)
        expect_refused("disabled_before_parent_receipt_or_Git",
                       lambda: adapter._require_parent_promotion(module.STANDING_AUTHORIZATION), module.Refused)
        expect_refused("missing_release_before_external_anchor_or_transport",
                       adapter._release_details, module.Refused)
        expect_refused("actual_child_cannot_use_root_execution_guard",
                       lambda: adapter.guard(0, 0, mutation=True), module.Refused)
        record("current_NEC_is_registered_on_GPU0",
               bool(author.read(ROOT / "pipeline/running.json").get("server-4", {}).get("0")))
        expect_refused("actual_current_NEC_project_slot_blocks_HVD",
                       lambda: adapter._local_idle(0), module.Refused)
        probe = {
            "server_id": "server-4", "hostname": "dl04-MS-7E06",
            "root": module.REMOTE_ROOT, "physical_gpu": 0, "gpu_uuid": module.GPU_UUIDS[0],
            "runtime_code_commit": author.RUNTIME,
            "resource_authorization": module.RESOURCE_AUTHORIZATION,
            "resource_memory_policy": module.RESOURCE_MEMORY_POLICY,
            "usable_under_current_overlay_policy": True, "memory_free_mib": 20000,
            "locks": {k: "available" for k in ("training", "diagnostic", "exclusive")},
            "contexts": [{"pid": 999999, "used_memory_mib": "unknown_software_fixture"}],
            "idle": False, "utilization_percent": 99,
        }
        adapter._check_probe(probe, 0)
        record("overlay_probe_accepts_external_context_without_external_idle_condition", True)
        under = copy.deepcopy(probe)
        under["memory_free_mib"] = 19999
        expect_refused("available_memory_below_20000_rejected",
                       lambda: adapter._check_probe(under, 0), module.Refused)
        for kind in ("training", "diagnostic", "exclusive"):
            busy = copy.deepcopy(probe)
            busy["locks"][kind] = "busy"
            expect_refused(kind + "_cooperative_lock_busy_rejected",
                           lambda busy=busy: adapter._check_probe(busy, 0), module.Refused)
        old_runtime = copy.deepcopy(probe)
        old_runtime["runtime_code_commit"] = author.HISTORICAL_LFT
        expect_refused("historical_LFT4457_not_accepted_as_current_runtime",
                       lambda: adapter._check_probe(old_runtime, 0), module.Refused)
        raw = {
            "candidate_id": author.CANDIDATE, "code_commit": author.SOURCE, "goal_sha256": module.GOAL,
            "mode": "smoke", "target": "candidate",
            "model_package": "framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hvd",
        }
        record("actual_result_identity_requires_HVD_source_package",
               adapter._raw_result_identity(raw, {}, "smoke", "candidate")
               and not adapter._raw_result_identity({**raw, "model_package": raw["model_package"][:-3] + "mic"}, {}, "smoke", "candidate"))
    source = (HERE / "adapter.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Adapter")
    run = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == "run")
    record("original_1020sec_run_margin_retained", "required_seconds=1020" in ast.get_source_segment(source, run))
    record("current_source_runtime_historical_receipt_are_separated",
           module.COMMIT == author.SOURCE
           and module.EXPECTED_RUNTIME_COMMIT == module.EXPECTED_PRIMARY_COMMIT == author.RUNTIME
           and module.HISTORICAL_PARENT_RECEIPT_COMMIT == author.HISTORICAL_LFT)
    record("GPU0_only_and_original_20000MiB_max1_three_locks",
           list(module.GPU_UUIDS) == [0] and list(module.POLICY_GPU_UUIDS) == [0]
           and module.RESOURCE_MEMORY_POLICY["minimum_free_mib_before_launch"] == 20000
           and module.RESOURCE_MEMORY_POLICY["max_project_tasks_per_gpu"] == 1
           and module.RESOURCE_MEMORY_POLICY["cooperative_lock_kinds"] == ["training", "diagnostic", "exclusive"])
    record("all_reviewed_MIC_original_files_preserved",
           {p.name: author.sha(p) for p in author.OLD.iterdir() if p.is_file()}
           == provenance["original_operational_file_hashes"])
    record("Torch_not_imported", not any(k == "torch" or k.startswith("torch.") for k in sys.modules))
    author.guard()
    result = {
        "schema_version": 1,
        "status": "LOCAL_SOFTWARE_NOP_FAIL_CLOSED_HASH_GRAPH_CHECKS_PASSED_NOT_NATIVE",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": author.CANDIDATE, "experiment_id": author.EXPERIMENT,
        "prepared_under_parent_owner": author.EXPECTED,
        "actual_author_child_thread_id": author.CHILD,
        "checks": checks, "check_count": len(checks), "actual_refusals": refusals,
        "actual_default_command": command,
        "default_command_returncode": default.returncode,
        "default_command_stdout": default.stdout,
        "default_command_stderr": default.stderr,
        "software_fixtures_are_not_actual_GPU_observations": True,
        "native": "NOT_RUN", "resources": "NOT_RUN", "full_model_forward": "NOT_RUN",
        "GPU_NVML_SSH_Git": "NOT_RUN", "efficacy": "UNKNOWN", "novelty": "UNKNOWN",
        "root_identity_impersonated": False, "shared_lifecycle_or_source_mutation": False,
        "scientific_admission": False,
    }
    author.write_json(HERE / "static_validation.json", result)
    frozen_files = {p.relative_to(HERE).as_posix(): author.sha(p)
                    for p in HERE.rglob("*") if p.is_file() and p.name != "FROZEN.json"}
    author.write_json(HERE / "FROZEN.json", {
        "schema_version": 1, "candidate_id": author.CANDIDATE, "experiment_id": author.EXPERIMENT,
        "frozen_at": datetime.now(timezone.utc).isoformat(), "writer_stopped": True,
        "source_commit": author.SOURCE, "expected_runtime_code_commit": author.RUNTIME,
        "draft_execution_disabled": True, "operational_ready": False,
        "files": frozen_files, "native": "NOT_RUN", "resources": "NOT_RUN",
        "independent_review": "PENDING_EXTERNAL_NOT_SELF_SIGNED",
    })
    print(json.dumps({
        "status": result["status"], "check_count": len(checks),
        "preparation": author.ref(HERE / "preparation.json"),
        "static_validation": author.ref(HERE / "static_validation.json"),
        "frozen": author.ref(HERE / "FROZEN.json"),
    }))


if __name__ == "__main__":
    main()
