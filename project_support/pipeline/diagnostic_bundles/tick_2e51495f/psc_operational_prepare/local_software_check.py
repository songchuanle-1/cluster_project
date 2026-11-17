"""Actual CPU catalogue safety checks; fixtures never stand in for GPU data."""
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import ast
import copy
import importlib.util
import json
import subprocess
import sys
import prepare_psc_operations as author

HERE = Path(__file__).resolve().parent
checks = []
refusals = {}


def record(name, condition):
    assert condition, name
    checks.append({"name": name, "passed": True})


def refused(name, call, exception):
    try:
        call()
    except exception as error:
        refusals[name] = str(error)
        record(name, True)
        return
    raise AssertionError("Expected refusal: " + name)


def main():
    owner = author.guard()
    prep = author.read(HERE / "preparation.json")
    native = author.read(author.NATIVE / "preparation.json")
    template = author.read(author.NATIVE / "manifest_template.json")
    provenance = author.read(HERE / "port_provenance.json")
    record("all_operational_hashes_match", all(author.sha(HERE / k) == v for k, v in prep["prepared_file_hashes"].items()))
    record("all_native_hashes_match", all(author.sha(author.NATIVE / k) == v for k, v in native["prepared_file_hashes"].items()))
    for old_name, new_name in (
        ("adapter.py", "adapter.py"), ("remote_ops.py", "remote_ops.py"),
        ("run_hvd_operation.py", "run_psc_operation.py"),
    ):
        expected, _ = author.literal_port((author.OLD / old_name).read_text(encoding="utf8"),
                                         author.sha(author.NATIVE / "preparation.json"),
                                         author.sha(author.NATIVE / "manifest_template.json"))
        record("exact_controlled_port_" + new_name, (HERE / new_name).read_bytes() == expected.encode())
        ast.parse(expected)
    keys = (
        "current_token", "stage", "tick_generated_at", "deadline_at", "physical_gpu",
        "gpu_uuid", "allowed_gpus", "context_sha256", "pending_sha256", "runtime_code_commit",
    )
    record("ten_execution_fields_NULL", all(key in template and template[key] is None for key in keys))
    record("both_drafts_disabled", native["draft_execution_disabled"] is True
           and prep["draft_execution_disabled"] is True and template["draft_execution_disabled"] is True)
    absent = ("adapter_release.json", "native_manifest.json", "execution_lease.json",
              "execution_binding.json", "prepare_request.json", "stage_request.json")
    record("no_execution_material", all(not (HERE / name).exists() and not (author.NATIVE / name).exists() for name in absent))
    command = [sys.executable, "-B", "-X", "utf8", str(HERE / "run_psc_operation.py")]
    default = subprocess.run(command, capture_output=True, text=True, encoding="utf8", timeout=20)
    response = json.loads(default.stdout)
    record("actual_default_NOP", default.returncode == 0 and response["status"] == "DEFAULT_NOP_NO_ENTRY_OR_TRANSPORT"
           and response["candidate_id"] == author.CANDIDATE and response["code_commit"] == author.SOURCE
           and response["active_binding_created"] is False and response["native_executed"] is False)
    spec = importlib.util.spec_from_file_location("psc_disabled_adapter_software_check", HERE / "adapter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class Tripwire:
        def call(self, *args, **kwargs):
            raise AssertionError("No transport authorized in software checks")

    def no_process(*args, **kwargs):
        raise AssertionError("No Git/SSH/GPU/process allowed in adapter checks")

    adapter = module.Adapter(transport=Tripwire())
    with patch.object(module.subprocess, "run", no_process), \
         patch.object(module.subprocess, "Popen", no_process), \
         patch.object(module.subprocess, "check_output", no_process):
        details, actual_template = adapter._frozen_details()
        record("actual_frozen_verifier", details["source_commit"] == author.SOURCE and actual_template == template)
        refused("actual_DRAFT_refuses_before_parent_receipt_or_Git",
                lambda: adapter._require_parent_promotion(module.STANDING_AUTHORIZATION), module.Refused)
        refused("actual_missing_release_refuses", adapter._release_details, module.Refused)
        record("current_registered_task_is_HVD",
               author.read(author.ROOT / "pipeline/running.json").get("server-4", {}).get("0") == "M230-HVD")
        refused("actual_HVD_project_slot_refuses_PSC", lambda: adapter._local_idle(0), module.Refused)
        probe = {
            "server_id": "server-4", "hostname": "dl04-MS-7E06", "root": module.REMOTE_ROOT,
            "physical_gpu": 0, "gpu_uuid": module.GPU_UUIDS[0], "runtime_code_commit": author.RUNTIME,
            "resource_authorization": module.RESOURCE_AUTHORIZATION,
            "resource_memory_policy": module.RESOURCE_MEMORY_POLICY,
            "usable_under_current_overlay_policy": True, "memory_free_mib": 20000,
            "locks": {kind: "available" for kind in ("training", "diagnostic", "exclusive")},
            "contexts": [{"pid": 999999, "used_memory_mib": "software_fixture"}],
            "idle": False, "utilization_percent": 99,
        }
        adapter._check_probe(probe, 0)
        record("overlay_accepts_foreign_context_without_idle_requirement", True)
        under = copy.deepcopy(probe)
        under["memory_free_mib"] = 19999
        refused("below_original_memory_budget_refused", lambda: adapter._check_probe(under, 0), module.Refused)
        for kind in ("training", "diagnostic", "exclusive"):
            busy = copy.deepcopy(probe)
            busy["locks"][kind] = "busy"
            refused(kind + "_busy_refused", lambda busy=busy: adapter._check_probe(busy, 0), module.Refused)
        wrong = copy.deepcopy(probe)
        wrong["runtime_code_commit"] = author.HISTORICAL_LFT
        refused("historical_LFT_receipt_is_not_current_runtime", lambda: adapter._check_probe(wrong, 0), module.Refused)
        raw = {
            "candidate_id": author.CANDIDATE, "code_commit": author.SOURCE, "goal_sha256": module.GOAL,
            "mode": "smoke", "target": "candidate",
            "model_package": "framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psc",
        }
        record("actual_PSC_result_identity",
               adapter._raw_result_identity(raw, {}, "smoke", "candidate")
               and not adapter._raw_result_identity({**raw, "model_package": raw["model_package"][:-3] + "hvd"}, {}, "smoke", "candidate"))
    record("current_source_runtime_and_historical_receipt_separate",
           module.COMMIT == author.SOURCE and module.EXPECTED_RUNTIME_COMMIT == module.EXPECTED_PRIMARY_COMMIT == author.RUNTIME
           and module.HISTORICAL_PARENT_RECEIPT_COMMIT == author.HISTORICAL_LFT)
    record("both_runtime_roots_are_current_HVD",
           module.REMOTE_ROOT == author.REMOTE_ROOT
           and author.REMOTE_ROOT in (HERE / "remote_ops.py").read_text())
    record("GPU0_and_original_memory_max1_three_locks",
           list(module.GPU_UUIDS) == [0] and list(module.POLICY_GPU_UUIDS) == [0]
           and module.RESOURCE_MEMORY_POLICY["minimum_free_mib_before_launch"] == 20000
           and module.RESOURCE_MEMORY_POLICY["max_project_tasks_per_gpu"] == 1
           and module.RESOURCE_MEMORY_POLICY["cooperative_lock_kinds"] == ["training", "diagnostic", "exclusive"])
    source = (HERE / "adapter.py").read_text(encoding="utf8")
    record("original_1020sec_run_margin", "required_seconds=1020" in source)
    record("old_frozen_HVD_operational_files_unchanged",
           {p.name: author.sha(p) for p in author.OLD.iterdir() if p.is_file()} == provenance["producer_file_hashes"])
    record("no_torch_imported", not any(key == "torch" or key.startswith("torch.") for key in sys.modules))
    author.guard()
    result = {
        "recorded_at": datetime.now(timezone.utc).isoformat(), "passed": True,
        "candidate_id": author.CANDIDATE, "experiment_id": author.EXPERIMENT,
        "owner_provenance_only": owner, "checks": checks, "check_count": len(checks),
        "actual_refusals": refusals, "actual_default_command": command,
        "actual_default_stdout": default.stdout, "actual_default_returncode": default.returncode,
        "fixtures_are_not_real_GPU_observations": True,
        "native": "NOT_RUN", "resources": "NOT_RUN", "Torch_autograd": "NOT_RUN",
        "SSH_GPU_NVML": "NOT_RUN", "efficacy": "UNKNOWN", "novelty": "UNKNOWN",
        "root_identity_impersonated": False, "shared_state_or_source_mutated": False,
    }
    author.write(HERE / "static_validation.json", result)
    author.write(HERE / "FROZEN.json", {
        "recorded_at": datetime.now(timezone.utc).isoformat(), "writer_stopped": True,
        "candidate_id": author.CANDIDATE, "source_commit": author.SOURCE,
        "draft_execution_disabled": True, "native": "NOT_RUN", "resources": "NOT_RUN",
        "files": {p.relative_to(HERE).as_posix(): author.sha(p) for p in HERE.rglob("*") if p.is_file()},
    })
    print(json.dumps({"passed": True, "check_count": len(checks),
                      "static_validation": author.ref(HERE / "static_validation.json"),
                      "frozen": author.ref(HERE / "FROZEN.json")}))


if __name__ == "__main__":
    main()
