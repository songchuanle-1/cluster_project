"""Bounded new-owner sanity only; no repeat native or mechanism suite."""
from pathlib import Path
from datetime import datetime, timezone
from contextlib import redirect_stdout
from unittest.mock import patch
import hashlib
import importlib.util
import io
import json
import os
import runpy
import subprocess
import sys

HERE = Path(__file__).resolve().parent
OLD = HERE.parent.parent / "tick_f74f3603/nsd_current_activation"
checks = []
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_bytes())
def check(name, value):
    assert value, name
    checks.append({"name": name, "passed": True})
def forbidden(*a, **k): raise AssertionError("Process/SSH/GPU forbidden")
def main():
    b, old = read(HERE / "current_binding.json"), read(OLD / "current_binding.json")
    keys = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
    actual = read(HERE.parents[2] / "headless/.foreground.lockdir/owner.json")
    check("actual_author_child_not_root", os.environ.get("CODEX_THREAD_ID") == "01a1b6ff-4235-7741-943b-732c0abb417d")
    check("current_binding_owner_exact_six_fields", b["owner"] == {k: actual[k] for k in keys})
    check("only_binding_owner_changed", {**b, "owner": old["owner"]} == old)
    check("entire_native_remote_launcher_payload_byte_exact", all(
        (HERE / n).read_bytes() == (OLD / n).read_bytes() for n in b["activation_files"]))
    old_text = (OLD / "adapter.py").read_bytes().decode()
    expected = old_text.replace("CURRENT_BINDING_SHA256 = '" + sha(OLD / "current_binding.json") + "'",
                               "CURRENT_BINDING_SHA256 = '" + sha(HERE / "current_binding.json") + "'", 1)
    check("adapter_only_binding_hash_changed", (HERE / "adapter.py").read_bytes().decode() == expected)
    release, prior = read(HERE / "release_template.json"), read(OLD / "release_template.json")
    restore = {**release, "current_binding": prior["current_binding"],
               "source_hashes": prior["source_hashes"]}
    check("release_only_current_binding_and_adapter_hash_changed", restore == prior
          and release["source_hashes"]["remote_ops.py"] == prior["source_hashes"]["remote_ops.py"])
    check("native_worker_cd1cb_unchanged", sha(HERE / "native/worker.py") ==
          "cd1cb8b000b7109db99b7bb44b69867d1c3bb5e63466a749b51bb4d35fd09112")
    check("manifest_ten_execution_fields_still_NULL", all(read(HERE / "native/manifest_template.json")[k] is None for k in
          ("current_token", "stage", "tick_generated_at", "deadline_at", "physical_gpu", "gpu_uuid",
           "allowed_gpus", "context_sha256", "pending_sha256", "runtime_code_commit")))
    spec = importlib.util.spec_from_file_location("nsd_newowner_sanity", HERE / "adapter.py")
    m = importlib.util.module_from_spec(spec)
    with patch.object(subprocess, "run", forbidden), patch.object(subprocess, "Popen", forbidden), patch.object(subprocess, "check_output", forbidden):
        spec.loader.exec_module(m)
        class Tripwire:
            def call(self, *a, **k): forbidden()
        adapter = m.Adapter(transport=Tripwire())
        check("actual_activation_owner_and_payload_graph", adapter._activation_details() == b)
        p, template = adapter._frozen_details()
        check("actual_reused_native_hash_graph", p == read(HERE / "native/preparation.json"))
        try:
            adapter.guard(0, 0, mutation=True)
        except m.Refused:
            check("actual_child_root_guard_refuses_without_spoofing", True)
        else:
            raise AssertionError("Child impersonated root")
        with patch.object(sys, "argv", [str(HERE / "run_nsd_operation.py")]), redirect_stdout(io.StringIO()) as output:
            runpy.run_path(str(HERE / "run_nsd_operation.py"), run_name="__main__")
        check("actual_default_launcher_NOP", json.loads(output.getvalue())["status"] == "DEFAULT_NOP_NO_ENTRY_OR_TRANSPORT")
    check("original1020second_margin", "required_seconds=1020" in expected and "1020 if a.operation=='run'" in (HERE / "run_nsd_operation.py").read_text())
    check("immutable_original_diagnostic_base", m.DIAGNOSTIC_CONDA_SOURCE_SHA256 == "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0")
    check("no_root_release_or_execution_material", all(not (HERE / n).exists() for n in
          ("adapter_release.json", "execution_binding.json", "execution_lease.json", "native_manifest.json", "prepare_request.json", "stage_request.json")))
    check("new_preparation_hashes", all(sha(HERE / n) == h for n, h in read(HERE / "preparation.json")["prepared_file_hashes"].items()))
    check("no_model_imported", "torch" not in sys.modules)
    record = {"recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": "BOUNDED_NEW_OWNER_SOFTWARE_SANITY_PASSED_NOT_NATIVE",
        "actual_author_child": os.environ["CODEX_THREAD_ID"], "owner": b["owner"],
        "check_count": len(checks), "checks": checks, "independent_review": False,
        "native": "NOT_RUN", "resources": "NOT_RUN", "root_release_execution_metadata_or_prepare_intent": False,
        "SSH_GPU_model_or_shared_mutation": False, "root_guard_spoofed": False}
    with (HERE / "software_validation.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(record, f, indent=2); f.write("\n")
    print(json.dumps({"check_count": len(checks), "software_validation_sha256": sha(HERE / "software_validation.json")}))
if __name__ == "__main__": main()
