"""Local copy/hash/metadata/refusal checks, never native/remote execution."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import importlib.util
import json
import re
import subprocess
import sys
from unittest.mock import patch
import build_fresh_activation as author

HERE = Path(__file__).resolve().parent
NATIVE = HERE / "native"
OP = HERE / "operational"


def main():
    author.guard()
    checks = []
    refusals = {}
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append({"name": name, "passed": True})
    def refused(name, operation, exception):
        try:
            operation()
        except exception as error:
            refusals[name] = str(error)
            return
        raise AssertionError("Expected refusal: " + name)
    native = author.read(NATIVE / "preparation.json")
    oprep = author.read(OP / "preparation.json")
    provenance = author.read(OP / "port_provenance.json")
    template = author.read(NATIVE / "manifest_template.json")
    for base, prep in ((NATIVE, native), (OP, oprep)):
        check(base.name + "_declared_hash_graph_matches",
              all(author.sha(base / n) == h for n, h in prep["prepared_file_hashes"].items()))
    identical = ["candidate.yaml", "worker.py"] + [
        q.relative_to(author.OLD / "native").as_posix()
        for q in (author.OLD / "native/candidate_model").glob("*.py")
    ]
    check("final_worker_and_original_model8_YAML_byte_exact",
          all((NATIVE / n).read_bytes() == (author.OLD / "native" / n).read_bytes() for n in identical)
          and len(list((NATIVE / "candidate_model").glob("*.py"))) == 8)
    check("native_runtime_only_DRAFT_flag_changed",
          (NATIVE / "native_runtime.py").read_bytes()
          == (author.OLD / "native/native_runtime.py").read_bytes().replace(
              b"DRAFT_EXECUTION_DISABLED = True", b"DRAFT_EXECUTION_DISABLED = False", 1))
    check("remote_and_root_launcher_byte_exact",
          all((OP / n).read_bytes() == (author.OLD / "operational" / n).read_bytes()
              for n in ("remote_ops.py", "run_mic_operation.py")))
    expected_adapter = (author.OLD / "operational/adapter.py").read_bytes()
    for previous, current in provenance["adapter_literal_changes"]:
        expected_adapter = expected_adapter.replace(previous.encode(), current.encode(), 1)
    check("adapter_only_declared_location_hash_and_DRAFT_literals_changed",
          (OP / "adapter.py").read_bytes() == expected_adapter)
    active = ("current_token", "stage", "tick_generated_at", "deadline_at", "physical_gpu",
              "gpu_uuid", "allowed_gpus", "context_sha256", "pending_sha256", "runtime_code_commit")
    check("all10_template_execution_fields_remain_NULL", all(template[k] is None for k in active))
    check("current_owner_provenance_exact_not_execution_lease",
          provenance["owner_provenance_only"] == author.EXPECTED
          and template["activation_provenance_only"]["owner"] == author.EXPECTED)
    check("same_source07ef_runtime6bc_GPU0_overlay",
          provenance["source_commit"] == "07ef534a6e44f22bd7b2d083550ebd7823d1d3d3"
          and provenance["runtime_code_commit"] == "6bc36adfe42764aac2209e6600fb3a783e2fa374"
          and provenance["physical_gpu"] == 0
          and provenance["gpu_uuid"] == "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
          and provenance["resource_authorization"]["sha256"] == "783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88")
    check("all_original_scientific_protocol_fields_and_assets_unchanged",
          all(template[k] == author.read(author.OLD / "native/manifest_template.json")[k]
              for k in ("assets", "protocol", "candidate_source_hashes", "candidate_config_sha256",
                        "tolerance", "config", "source_preparation_sha256")))
    for q in HERE.rglob("*.py"):
        ast.parse(q.read_text(encoding="utf-8"))
    check("all_authored_and_copied_Python_AST_parse", True)
    command = [sys.executable, "-B", "-X", "utf8", str(OP / "run_mic_operation.py")]
    default = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
    nop = json.loads(default.stdout)
    check("actual_default_root_launcher_is_NOP_without_transport_or_entry",
          default.returncode == 0 and nop["status"] == "DEFAULT_NOP_NO_ENTRY_OR_TRANSPORT"
          and nop["native_executed"] is False and nop["active_binding_created"] is False)
    spec = importlib.util.spec_from_file_location("mic_fresh_metadata_check", OP / "adapter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    class Tripwire:
        def call(self, *args, **kwargs):
            raise AssertionError("Transport must not run in local software checks")
    adapter = module.Adapter(transport=Tripwire())
    def forbidden(*args, **kwargs):
        raise AssertionError("No process/Git/SSH/GPU call is authorized in adapter checks")
    with patch.object(module.subprocess, "run", forbidden), \
         patch.object(module.subprocess, "Popen", forbidden), \
         patch.object(module.subprocess, "check_output", forbidden):
        p, t = adapter._frozen_details()
        check("actual_adapter_accepts_exact_new_native_metadata_hash_graph",
              p == native and t == template)
        refused("missing_reviewed_static_release_before_transport_or_binding",
                adapter._release_details, module.Refused)
        refused("actual_child_identity_cannot_use_root_guard",
                lambda: adapter.guard(0, 0, mutation=True), module.Refused)
        adapter._local_idle(0)
        check("canonical_project_slot_is_unreserved_local_only", True)
    check("adapter_DRAFT_enabled_only_in_new_copy", module.DRAFT_EXECUTION_DISABLED is False)
    text = (NATIVE / "native_runtime.py").read_text(encoding="utf-8")
    fn = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)
              and n.name == "require_promoted_version")
    namespace = {
        "re": re, "DRAFT_EXECUTION_DISABLED": False,
        "SOURCE_PARENT_COMMIT": native["source_parent_commit"],
        "CANDIDATE_COMMIT": native["source_commit"],
        "SOURCE_PREPARATION_SHA256": template["source_preparation_sha256"],
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), "<metadata-only>", "exec"), namespace)
    namespace["require_promoted_version"]()
    check("actual_extracted_native_version_guard_accepts_enabled_metadata_without_importing_runtime", True)
    namespace["DRAFT_EXECUTION_DISABLED"] = True
    refused("native_guard_still_refuses_disabled_metadata",
            namespace["require_promoted_version"], RuntimeError)
    check("missing_release_and_active_execution_materials_absent",
          not (OP / "adapter_release.json").exists()
          and not (HERE.parent / "mic_execution").exists()
          and not any(q.name in ("native_manifest.json", "execution_lease.json", "execution_binding.json")
                      or q.name.endswith("_request.json") for q in HERE.rglob("*") if q.is_file()))
    check("all_producer_files_preserved",
          {q.relative_to(author.OLD).as_posix(): author.sha(q)
           for q in author.OLD.rglob("*") if q.is_file()} == provenance["producer_files_preserved"])
    check("no_Torch_import", not any(n == "torch" or n.startswith("torch.") for n in sys.modules))
    check("original_1020sec_run_margin_preserved",
          "required_seconds=1020" in (OP / "adapter.py").read_text(encoding="utf-8"))
    author.guard()
    result = {
        "schema_version": 1, "candidate_id": native["candidate_id"], "experiment_id": "M229-MIC",
        "status": "LOCAL_SOFTWARE_COPY_HASH_METADATA_NOP_AND_FAIL_CLOSED_CHECKS_PASSED_NOT_NATIVE",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "owner_provenance_only": author.EXPECTED, "actual_author_child_thread": author.CHILD,
        "checks": checks, "check_count": len(checks), "actual_refusals": refusals,
        "default_command": command, "default_returncode": default.returncode,
        "default_stdout": default.stdout, "default_stderr": default.stderr,
        "native": "NOT_RUN", "resources": "NOT_RUN", "Torch_autograd": "NOT_RUN",
        "GPU_NVML_SSH_Git": "NOT_RUN", "scientific_admission": False,
        "root_environment_impersonated": False, "shared_state_or_source_mutation": False,
        "independent_review": "PENDING_EXTERNAL_NOT_SELF_SIGNED",
    }
    author.dump(HERE / "static_validation.json", result)
    author.dump(HERE / "FROZEN.json", {
        "schema_version": 1, "candidate_id": native["candidate_id"], "experiment_id": "M229-MIC",
        "frozen_at": datetime.now(timezone.utc).isoformat(), "writer_stopped": True,
        "owner_provenance_only": author.EXPECTED,
        "native": "NOT_RUN", "resources": "NOT_RUN",
        "files": {q.relative_to(HERE).as_posix(): author.sha(q)
                  for q in HERE.rglob("*") if q.is_file() and q.name != "FROZEN.json"},
    })
    print(json.dumps({"check_count": len(checks), "preparation": author.ref(HERE / "preparation.json"),
                      "static_validation": author.ref(HERE / "static_validation.json"),
                      "FROZEN": author.ref(HERE / "FROZEN.json")}))


if __name__ == "__main__":
    main()
