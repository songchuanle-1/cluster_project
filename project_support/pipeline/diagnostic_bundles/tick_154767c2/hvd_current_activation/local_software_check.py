"""Actual software checks with process/transport tripwires; no execution operation."""
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
OLD = ROOT / "pipeline/diagnostic_bundles/tick_c7451cf1"
NATIVE = OLD / "hvd_native_prepare/native"
OPS = OLD / "hvd_operational_prepare"
TOKEN = "154767c278664ba4a7b666c69f12abaa"
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


def author_guard():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    record("actual_author_identity_separate_from_root",
           bool(os.environ.get("CODEX_THREAD_ID")) and os.environ["CODEX_THREAD_ID"] != THREAD)
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
    return owner


def main():
    owner = author_guard()
    prep = read(HERE / "preparation.json")
    record("prepared_file_hash_graph", all(sha(HERE / name) == digest for name, digest in prep["prepared_file_hashes"].items()))
    current = read(HERE / "current_binding.json")
    original = read(NATIVE / "manifest_template.json")
    template = read(HERE / "manifest_template.json")
    version = read(HERE / "source_version_binding.json")
    for name in ("adapter.py", "remote_ops.py", "native_runtime.py", "run_hvd_operation.py"):
        compile((HERE / name).read_bytes(), str(HERE / name), "exec")
    record("all_four_adapted_python_files_compile_without_execution", True)
    record("no_duplicate_worker_model_or_YAML",
           not any((HERE / name).exists() for name in ("worker.py", "candidate_model", "candidate.yaml")))
    record("worker_exact_frozen_original",
           sha(NATIVE / "worker.py") == "f91bddf7be81cc2e823f5c2e38a16d3a666e45022d885c6cb7a4ff654806646c")
    old_adapter = (OPS / "adapter.py").read_text(encoding="utf-8")
    new_adapter = (HERE / "adapter.py").read_text(encoding="utf-8")
    old_functions, new_functions = functions(old_adapter, "Adapter"), functions(new_adapter, "Adapter")
    allowed = {"_frozen_details", "guard", "_check_probe", "_require_parent_promotion", "stage"}
    record("all_other_adapter_methods_byte_exact",
           all(new_functions[name] == source for name, source in old_functions.items() if name not in allowed))
    # _check_probe/_require_parent_promotion change only stale descriptive words.
    for name in ("_check_probe", "_require_parent_promotion"):
        normalized = old_functions[name].replace("exact expected current NEC6bc checkout", "exact expected current MIC07ef checkout").replace(
            "actual primary HEAD must be current NEC6bc", "actual primary HEAD must be current MIC07ef")
        record(name + "_logic_exact_only_error_description_updated", new_functions[name] == normalized)
    for name in ("remote_ops.py", "native_runtime.py"):
        record(name + "_all_function_bodies_byte_exact",
               functions((HERE / name).read_text(encoding="utf-8")) ==
               functions(((OPS if name == "remote_ops.py" else NATIVE) / name).read_text(encoding="utf-8")))
    record("original_1020_second_run_margin",
           "required_seconds=1020" in new_functions["run"] and new_functions["run"] == old_functions["run"])
    record("replay_and_flock_paths_preserved",
           new_functions["_no_replay"] == old_functions["_no_replay"]
           and functions((HERE / "native_runtime.py").read_text())["acquire"] ==
           functions((NATIVE / "native_runtime.py").read_text())["acquire"])
    record("new_static_release_exact_template",
           read(HERE / "adapter_release.json") == read(HERE / "release_template.json"))
    spec = importlib.util.spec_from_file_location("hvd_current_software_checked_adapter", HERE / "adapter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    class Tripwire:
        def call(self, *args, **kwargs):
            raise AssertionError("Transport is forbidden in a software check")
    adapter = module.Adapter(transport=Tripwire())
    def forbidden(*args, **kwargs):
        raise AssertionError("Process/Git/SSH/GPU execution is forbidden in a software check")
    with patch.object(module.subprocess, "run", forbidden), patch.object(module.subprocess, "Popen", forbidden), \
         patch.object(module.subprocess, "check_output", forbidden):
        producer, effective = adapter._frozen_details()
        record("actual_frozen_producer_and_current_projection_verifier",
               producer["source_commit"] == current["legacy_source_commit"] and effective == template
               and template["code_commit"] == current["source_commit"])
        for name in template["diagnostic_files"]:
            path = adapter._diagnostic_path(name, template)
            expected_root = HERE if name in ("native_runtime.py", "source_version_binding.json") else NATIVE
            record("payload_resolves_exact_bytes:" + name, path == (expected_root / name).resolve())
        refused("payload_path_escape_refused", lambda: adapter._diagnostic_path("../foreign", template), module.Refused)
        refused("unreviewed_external_candidate_anchor_refused", adapter._release_details, module.Refused)
        refused("actual_child_cannot_use_root_execution_guard",
                lambda: adapter.guard(0, 0, mutation=True), module.Refused)
        adapter._local_idle(0)
        record("actual_canonical_GPU0_slot_currently_clear_read_only", True)
        probe = {"server_id": "server-4", "hostname": "dl04-MS-7E06",
                 "root": module.REMOTE_ROOT, "physical_gpu": 0, "gpu_uuid": module.GPU_UUIDS[0],
                 "runtime_code_commit": module.EXPECTED_RUNTIME_COMMIT,
                 "resource_authorization": module.RESOURCE_AUTHORIZATION,
                 "resource_memory_policy": module.RESOURCE_MEMORY_POLICY,
                 "usable_under_current_overlay_policy": True, "memory_free_mib": 20000,
                 "locks": {kind: "available" for kind in ("training", "diagnostic", "exclusive")},
                 "contexts": [{"pid": 999999, "used_memory_mib": "software_fixture"}], "idle": False}
        adapter._check_probe(probe, 0)
        record("current_overlay_probe_accepts_external_context_fixture_at_budget", True)
        for label, fields in (
            ("under_budget", {"memory_free_mib": 19999}),
            ("old_runtime6bc", {"runtime_code_commit": current["legacy_source_parent_commit"]}),
            ("old_NEC_root", {"root": original["root"]}),
            ("foreign_UUID", {"gpu_uuid": "GPU-foreign"}),
            ("physical_GPU1", {"physical_gpu": 1}),
        ):
            refused(label + "_probe_refused", lambda fields=fields: adapter._check_probe({**probe, **fields}, 0), module.Refused)
        for kind in ("training", "diagnostic", "exclusive"):
            changed = copy.deepcopy(probe); changed["locks"][kind] = "busy"
            refused(kind + "_lock_busy_refused", lambda changed=changed: adapter._check_probe(changed, 0), module.Refused)
        original_read = module.read
        for label, task in (
            ("claiming", {"status": "claiming", "gpu": 0}),
            ("pending_progress", {"status": "waiting", "gpu": 0, "launch_verification": "pending_progress"}),
            ("launch_uncertain", {"status": "waiting", "gpu": 0, "dispatch_hold": "Launch uncertain; fixture"}),
            ("unknown_GPU", {"status": "running"}),
        ):
            def fixture_read(path, task=task):
                if Path(path) == ROOT / "pipeline/running.json": return {"server-4": {}}
                if Path(path) == ROOT / "pipeline/queue.json": return {"gpu_queues": {"server-4": [task]}}
                return original_read(path)
            with patch.object(module, "read", fixture_read):
                refused(label + "_reservation_refused", lambda: adapter._local_idle(0), module.Refused)
        with patch.object(sys, "argv", [str(HERE / "run_hvd_operation.py")]):
            output = io.StringIO()
            with redirect_stdout(output):
                runpy.run_path(str(HERE / "run_hvd_operation.py"), run_name="__main__")
            nop = json.loads(output.getvalue())
            record("actual_default_launcher_NOP_no_process_or_transport",
                   nop["status"] == "DEFAULT_NOP_NO_ENTRY_OR_TRANSPORT"
                   and nop["code_commit"] == current["source_commit"]
                   and not nop["active_binding_created"] and not nop["native_executed"])
    runtime_source = (HERE / "native_runtime.py").read_text(encoding="utf-8")
    runtime_tree = ast.parse(runtime_source)
    runtime_functions = functions(runtime_source)
    globals_ = {"re": re, "DRAFT_EXECUTION_DISABLED": False, "CANDIDATE_COMMIT": current["source_commit"],
                "SOURCE_PARENT_COMMIT": current["source_parent_commit"],
                "RUNTIME_EXPECTED_COMMIT": current["runtime_code_commit"],
                "SOURCE_PREPARATION_SHA256": template["source_preparation_sha256"]}
    exec(compile(runtime_functions["require_promoted_version"], "isolated_runtime_version_guard", "exec"), globals_)
    globals_["require_promoted_version"]()
    record("actual_runtime_version_guard_accepts_current_metadata_without_IO", True)
    globals_["DRAFT_EXECUTION_DISABLED"] = True
    refused("runtime_disabled_guard_refuses_before_manifest_IO", globals_["require_promoted_version"], RuntimeError)
    globals_["DRAFT_EXECUTION_DISABLED"] = False
    populated = copy.deepcopy(template)
    stage = Path("/data/songcl/Project/Cluster_project/pipeline/hvd_" + TOKEN[:8] + "_gpu0")
    populated.update(current_token=TOKEN, stage=str(stage), tick_generated_at=owner["generated_at"],
                     deadline_at=owner["deadline_at"], physical_gpu=0, gpu_uuid=module.GPU_UUIDS[0],
                     allowed_gpus=[0], context_sha256=owner["context_sha256"],
                     pending_sha256=owner["pending_sha256"], runtime_code_commit=current["runtime_code_commit"])
    pure_asserts = [node for node in runtime_tree.body if isinstance(node, ast.Assert) and 47 <= node.lineno <= 70]
    assert_code = compile(ast.Module(body=pure_asserts, type_ignores=[]), "isolated_runtime_identity_assertions", "exec")
    def identity_assertions(manifest):
        values = {**globals_, "MANIFEST": manifest, "Path": Path, "ROOT": Path(manifest["root"]),
                  "STAGE": stage, "NAME": manifest["name"], "GOAL": module.GOAL, "GPU_UUIDS": module.GPU_UUIDS,
                  "BASE_NAME": manifest["name"], "PHYSICAL_GPU": manifest["physical_gpu"],
                  "RESOURCE_AUTHORIZATION": module.RESOURCE_AUTHORIZATION, "RESOURCE_MEMORY_POLICY": module.RESOURCE_MEMORY_POLICY}
        exec(assert_code, values)
    identity_assertions(populated)
    record("actual_runtime_identity_assertions_accept_current_fixture_without_IO", True)
    for label, changes in (
        ("source_e38", {"code_commit": current["legacy_source_commit"]}),
        ("runtime6bc", {"runtime_code_commit": current["legacy_source_parent_commit"]}),
        ("NEC_root", {"root": original["root"]}),
        ("GPU1", {"physical_gpu": 1}),
    ):
        refused("runtime_" + label + "_identity_refused",
                lambda changes=changes: identity_assertions({**populated, **changes}), AssertionError)
    class VersionFile:
        def __init__(self, value): self.value = value
        def read_text(self): return json.dumps(self.value)
    class VersionStage:
        def __init__(self, value): self.value = value
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
    for label, changes in (
        ("e38", {"code_commit": current["legacy_source_commit"]}),
        ("parent6bc", {"parent_commit": current["legacy_source_parent_commit"]}),
        ("eight_files", {"source_files": dict(list(version["source_files"].items())[:8])}),
    ):
        refused("source_binding_" + label + "_refused",
                lambda changes=changes: verify_version({**version, **changes}), AssertionError)
    record("Torch_not_imported", not any(name == "torch" or name.startswith("torch.") for name in sys.modules))
    fields = ("current_token", "stage", "tick_generated_at", "deadline_at", "physical_gpu",
              "gpu_uuid", "allowed_gpus", "context_sha256", "pending_sha256", "runtime_code_commit")
    record("original_and_current_template_ten_fields_still_NULL",
           all(original[k] is None and template[k] is None for k in fields))
    record("no_execution_material_created",
           all(not (HERE / name).exists() for name in ("native_manifest.json", "execution_lease.json",
               "execution_binding.json", "prepare_request.json", "stage_request.json"))
           and not (HERE.parent / "hvd_execution").exists())
    author_guard()
    result = {
        "schema_version": 1, "status": "ACTUAL_LOCAL_THIN_ACTIVATION_SOFTWARE_CHECKS_PASSED_NOT_NATIVE",
        "recorded_at": datetime.now(timezone.utc).isoformat(), "candidate_id": current["candidate_id"],
        "source_commit": current["source_commit"], "runtime_code_commit": current["runtime_code_commit"],
        "actual_author_child_thread_id": os.environ.get("CODEX_THREAD_ID"),
        "owner_provenance_only": current["owner"], "check_count": len(checks),
        "checks": checks, "actual_refusals": refusals,
        "fixtures_not_actual_GPU_observations": True, "root_execution_guard_pass_claimed": False,
        "SSH_GPU_subprocess_Popen_model_execution": False, "native": "NOT_RUN", "resources": "NOT_RUN",
        "scientific_admission": False, "execution_material_created": False,
        "original_packets_or_shared_state_written": False,
    }
    with (HERE / "software_validation.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2); stream.write("\n")
    print(json.dumps({"status": result["status"], "check_count": len(checks),
                      "path": str(HERE / "software_validation.json"), "sha256": sha(HERE / "software_validation.json")}))


if __name__ == "__main__":
    main()
