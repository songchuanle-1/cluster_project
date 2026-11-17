"""Actual local activation checks with subprocess and transport tripwires; no native run."""
from pathlib import Path
from datetime import datetime, timezone
from contextlib import redirect_stdout
from unittest.mock import patch
import ast
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import runpy
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path("D:/project/cluster_project")
OLD = ROOT / "pipeline/diagnostic_bundles/tick_2e51495f"
NATIVE = OLD / "psc_native_prepare/native"
NEW_NATIVE = HERE / "native"
OPS = OLD / "psc_operational_prepare"
TOKEN = "0bb874337dde412e98bbbaac369f3370"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
checks = []
refusals = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def record(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append({"name": name, "passed": True})


def refused(name, function, error):
    try:
        function()
    except error as found:
        refusals[name] = str(found)
        record(name, True)
        return
    raise AssertionError("Expected refusal: " + name)


def functions(source, klass=None):
    body = ast.parse(source).body
    if klass:
        body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == klass).body
    return {n.name: ast.get_source_segment(source, n)
            for n in body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def guard():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD
    assert os.environ.get("CODEX_THREAD_ID") == "01a1b166-dcbf-7d01-b0cb-c85fff644605" != THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
    return {key: owner[key] for key in ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")}


def main():
    owner = guard()
    prep, current = read(HERE / "preparation.json"), read(HERE / "current_binding.json")
    original, template = read(NATIVE / "manifest_template.json"), read(NEW_NATIVE / "manifest_template.json")
    version = read(NEW_NATIVE / "source_version_binding.json")
    record("actual_author_separate_from_root_and_six_owner_fields_current", current["owner"] == owner)
    record("prepared_file_hash_graph", all(sha(HERE / n) == h for n, h in prep["prepared_file_hashes"].items()))
    for path in HERE.rglob("*.py"):
        compile(path.read_bytes(), str(path), "exec")
    record("all_new_python_sources_compile_without_execution", True)
    record("worker_unchanged", sha(NEW_NATIVE / "worker.py") == sha(NATIVE / "worker.py") ==
           "530a5230021fad8d880c37a34c18973b4c556e7dc1536b6c4faaffdd6d6f93d8")
    for source, digest in current["exact9_source_files"].items():
        name = "candidate.yaml" if source.endswith(".yaml") else "candidate_model/" + Path(source).name
        record("exact9_source_copy:" + name, sha(NEW_NATIVE / name) == sha(NATIVE / name) == digest)
    old_adapter, new_adapter = ((p / "adapter.py").read_text(encoding="utf8") for p in (OPS, HERE))
    old_functions, new_functions = functions(old_adapter, "Adapter"), functions(new_adapter, "Adapter")
    record("all_adapter_methods_except_identity_binding_byte_exact", all(
        new_functions[n] == text for n, text in old_functions.items() if n not in ("_frozen_details", "guard")))
    record("SSH_transport_byte_exact", functions(new_adapter, "SSHTransport") == functions(old_adapter, "SSHTransport"))
    record("historical_LFT_technical_receipt_validator_byte_exact",
           functions(new_adapter)["validate_parent_technical_receipt"] == functions(old_adapter)["validate_parent_technical_receipt"])
    record("original_four_arms_and_1020_second_margin_preserved",
           "required_seconds=1020" in new_functions["run"] and new_functions["run"] == old_functions["run"])
    record("all_runtime_function_bodies_byte_exact",
           functions((NEW_NATIVE / "native_runtime.py").read_text()) == functions((NATIVE / "native_runtime.py").read_text()))
    for name in ("remote_ops.py", "run_psc_operation.py"):
        record(name + "_byte_exact_current_PSC_producer", (HERE / name).read_bytes() == (OPS / name).read_bytes())
    expected = copy.deepcopy(original)
    expected["draft_execution_disabled"] = False
    expected["source_version_binding_sha256"] = sha(NEW_NATIVE / "source_version_binding.json")
    for name in ("native_runtime.py", "source_version_binding.json"):
        expected["diagnostic_files"][name] = sha(NEW_NATIVE / name)
    record("template_exact_reviewed_activation_projection", template == expected)
    record("native_hash_graph", all(sha(NEW_NATIVE / n) == h for n, h in template["diagnostic_files"].items()))
    spec = importlib.util.spec_from_file_location("psc_current_software_checked_adapter", HERE / "adapter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class Tripwire:
        def call(self, *args, **kwargs):
            raise AssertionError("Transport forbidden during local software checks")

    def forbidden(*args, **kwargs):
        raise AssertionError("Process/Git/SSH/GPU execution forbidden during local software checks")

    adapter = module.Adapter(transport=Tripwire())
    with patch.object(module.subprocess, "run", forbidden), patch.object(module.subprocess, "Popen", forbidden), \
         patch.object(module.subprocess, "check_output", forbidden):
        producer, effective = adapter._frozen_details()
        record("actual_frozen_details_succeeds_with_entire_new_hash_graph",
               producer == read(NEW_NATIVE / "preparation.json") and effective == template)
        record("adapter_uses_new_native_preparation_and_template_hashes",
               module.PREPARATION_SHA == sha(NEW_NATIVE / "preparation.json")
               and module.TEMPLATE_SHA == sha(NEW_NATIVE / "manifest_template.json"))
        refused("missing_external_root_release_refused_before_transport", adapter._release_details, module.Refused)
        refused("actual_child_cannot_execute_root_guard", lambda: adapter.guard(0, 0, mutation=True), module.Refused)
        probe = {"server_id": "server-4", "hostname": "dl04-MS-7E06", "root": module.REMOTE_ROOT,
                 "physical_gpu": 0, "gpu_uuid": module.GPU_UUIDS[0], "runtime_code_commit": module.EXPECTED_RUNTIME_COMMIT,
                 "resource_authorization": module.RESOURCE_AUTHORIZATION, "resource_memory_policy": module.RESOURCE_MEMORY_POLICY,
                 "usable_under_current_overlay_policy": True, "memory_free_mib": 20000,
                 "locks": {kind: "available" for kind in ("training", "diagnostic", "exclusive")},
                 "contexts": [{"pid": 999999, "used_memory_mib": "software_fixture"}], "idle": False}
        adapter._check_probe(probe, 0)
        record("external_overlay_at_original_budget_fixture_accepted", True)
        for label, fields in (
            ("under_budget", {"memory_free_mib": 19999}), ("foreign_runtime", {"runtime_code_commit": "0" * 40}),
            ("foreign_root", {"root": "/foreign/root"}), ("foreign_UUID", {"gpu_uuid": "GPU-foreign"}),
            ("physical_GPU1", {"physical_gpu": 1}),
        ):
            refused(label + "_fixture_refused", lambda fields=fields: adapter._check_probe({**probe, **fields}, 0), module.Refused)
        for kind in ("training", "diagnostic", "exclusive"):
            changed = copy.deepcopy(probe)
            changed["locks"][kind] = "busy"
            refused(kind + "_busy_fixture_refused", lambda changed=changed: adapter._check_probe(changed, 0), module.Refused)
        original_read = module.read
        for label, task in (
            ("claiming", {"status": "claiming", "gpu": 0}),
            ("pending_progress", {"status": "waiting", "gpu": 0, "launch_verification": "pending_progress"}),
            ("launch_uncertain", {"status": "waiting", "gpu": 0, "dispatch_hold": "Launch uncertain; fixture"}),
            ("unknown_GPU", {"status": "running"}),
        ):
            def fixture_read(path, task=task):
                if Path(path) == ROOT / "pipeline/running.json":
                    return {"server-4": {}}
                if Path(path) == ROOT / "pipeline/queue.json":
                    return {"gpu_queues": {"server-4": [task]}}
                return original_read(path)
            with patch.object(module, "read", fixture_read):
                refused(label + "_reservation_fixture_refused", lambda: adapter._local_idle(0), module.Refused)
        with patch.object(sys, "argv", [str(HERE / "run_psc_operation.py")]):
            output = io.StringIO()
            with redirect_stdout(output):
                runpy.run_path(str(HERE / "run_psc_operation.py"), run_name="__main__")
            nop = json.loads(output.getvalue())
            record("actual_default_launcher_NOP_no_process_or_transport",
                   nop["status"] == "DEFAULT_NOP_NO_ENTRY_OR_TRANSPORT"
                   and nop["code_commit"] == current["source_commit"]
                   and not nop["active_binding_created"] and not nop["native_executed"])
    runtime_source = (NEW_NATIVE / "native_runtime.py").read_text(encoding="utf8")
    runtime_tree, runtime_functions = ast.parse(runtime_source), functions(runtime_source)
    globals_ = {"re": re, "DRAFT_EXECUTION_DISABLED": False, "CANDIDATE_COMMIT": current["source_commit"],
                "SOURCE_PARENT_COMMIT": current["source_parent_commit"], "RUNTIME_EXPECTED_COMMIT": current["runtime_code_commit"],
                "SOURCE_PREPARATION_SHA256": template["source_preparation_sha256"]}
    exec(compile(runtime_functions["require_promoted_version"], "isolated_runtime_version_guard", "exec"), globals_)
    globals_["require_promoted_version"]()
    record("actual_runtime_version_guard_accepts_current_metadata_without_IO", True)
    globals_["DRAFT_EXECUTION_DISABLED"] = True
    refused("runtime_disabled_guard_refuses_before_manifest_IO", globals_["require_promoted_version"], RuntimeError)
    globals_["DRAFT_EXECUTION_DISABLED"] = False
    stage = Path("/data/songcl/Project/Cluster_project/pipeline/psc_" + TOKEN[:8] + "_gpu0")
    populated = copy.deepcopy(template)
    populated.update(current_token=TOKEN, stage=str(stage), tick_generated_at=owner["generated_at"],
                     deadline_at=owner["deadline_at"], physical_gpu=0, gpu_uuid=module.GPU_UUIDS[0],
                     allowed_gpus=[0], context_sha256=owner["context_sha256"], pending_sha256=owner["pending_sha256"],
                     runtime_code_commit=current["runtime_code_commit"])
    pure_asserts = [node for node in runtime_tree.body if isinstance(node, ast.Assert)]
    assert_code = compile(ast.Module(body=pure_asserts, type_ignores=[]), "isolated_runtime_identity_assertions", "exec")
    def identity_assertions(manifest):
        values = {**globals_, "MANIFEST": manifest, "Path": Path, "ROOT": Path(manifest["root"]), "STAGE": stage,
                  "NAME": manifest["name"], "GOAL": module.GOAL, "GPU_UUIDS": module.GPU_UUIDS,
                  "BASE_NAME": manifest["name"], "PHYSICAL_GPU": manifest["physical_gpu"],
                  "RESOURCE_AUTHORIZATION": module.RESOURCE_AUTHORIZATION, "RESOURCE_MEMORY_POLICY": module.RESOURCE_MEMORY_POLICY}
        exec(assert_code, values)
    identity_assertions(populated)
    record("actual_runtime_identity_assertions_accept_current_fixture_without_IO", True)
    for label, changes in (("source", {"code_commit": "0" * 40}), ("runtime", {"runtime_code_commit": "0" * 40}),
                           ("root", {"root": "/foreign/root"}), ("GPU1", {"physical_gpu": 1})):
        refused("runtime_" + label + "_fixture_refused", lambda changes=changes: identity_assertions({**populated, **changes}), AssertionError)
    class VersionFile:
        def __init__(self, value):
            self.value = value
        def read_text(self):
            return json.dumps(self.value)
    class VersionStage:
        def __init__(self, value):
            self.value = value
        def __truediv__(self, name):
            assert name == "source_version_binding.json"
            return VersionFile(self.value)
    def verify_version(value):
        values = {**globals_, "json": json, "STAGE": VersionStage(value), "MANIFEST": populated,
                  "sha": lambda path: populated["source_version_binding_sha256"]}
        exec(compile(runtime_functions["verify_source_version"], "isolated_source_binding_verifier", "exec"), values)
        values["verify_source_version"]()
    verify_version(version)
    record("actual_source_version_verifier_accepts_current_binding_without_IO", True)
    for label, changes in (("source", {"code_commit": "0" * 40}), ("parent", {"parent_commit": "0" * 40}),
                           ("eight_files", {"source_files": dict(list(version["source_files"].items())[:8])})):
        refused("source_binding_" + label + "_fixture_refused", lambda changes=changes: verify_version({**version, **changes}), AssertionError)
    active = ("current_token", "stage", "tick_generated_at", "deadline_at", "physical_gpu", "gpu_uuid",
              "allowed_gpus", "context_sha256", "pending_sha256", "runtime_code_commit")
    record("original_and_current_templates_ten_execution_fields_NULL", all(original[k] is None and template[k] is None for k in active))
    record("original_DRAFT_still_True", original["draft_execution_disabled"] is True
           and "DRAFT_EXECUTION_DISABLED = True" in (NATIVE / "native_runtime.py").read_text())
    record("historical_LFT_receipt_anchor_separate_from_current_source_runtime",
           module.HISTORICAL_PARENT_RECEIPT_COMMIT == "4457a46f9075f61e83340aa0f0af87d5bf4e986c"
           and module.COMMIT != module.EXPECTED_RUNTIME_COMMIT != module.HISTORICAL_PARENT_RECEIPT_COMMIT)
    record("no_root_release_or_execution_material", not (HERE / "adapter_release.json").exists()
           and all(not (HERE / name).exists() and not (NEW_NATIVE / name).exists() for name in
                   ("native_manifest.json", "execution_lease.json", "execution_binding.json", "prepare_request.json", "stage_request.json"))
           and not (HERE.parent / "psc_execution").exists())
    record("Torch_not_imported", not any(n == "torch" or n.startswith("torch.") for n in sys.modules))
    guard()
    result = {
        "schema_version": 1, "status": "ACTUAL_LOCAL_PSC_ACTIVATION_SOFTWARE_CHECKS_PASSED_NOT_NATIVE",
        "recorded_at": datetime.now(timezone.utc).isoformat(), "candidate_id": current["candidate_id"],
        "source_commit": current["source_commit"], "runtime_code_commit": current["runtime_code_commit"],
        "actual_author_child_thread_id": os.environ.get("CODEX_THREAD_ID"), "owner_provenance_only": owner,
        "check_count": len(checks), "checks": checks, "actual_refusals": refusals,
        "fixtures_not_actual_GPU_observations": True, "root_execution_guard_pass_claimed": False,
        "SSH_GPU_subprocess_Popen_model_execution": False, "native": "NOT_RUN", "resources": "NOT_RUN",
        "scientific_admission": False, "execution_material_created": False,
        "original_packets_or_shared_state_written": False,
    }
    with (HERE / "software_validation.json").open("x", encoding="utf8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "check_count": len(checks),
                      "path": str(HERE / "software_validation.json"), "sha256": sha(HERE / "software_validation.json")}))


if __name__ == "__main__":
    main()
