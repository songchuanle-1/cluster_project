"""Build only separately versioned, disabled NDE operational software.

No adapter import, SSH, stage, runtime checkout, GPU, or execution binding.
The original NSD files and every native producer file remain read-only.
"""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import os
import re
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
OLD = ROOT / "pipeline/diagnostic_bundles/tick_355279e0/nsd_current_activation"
AUTHOR = "01a1b845-a78e-7cb2-8d77-a64fb63b444f"
TOKEN = "71e15360fb3349f08e5af82b14daea55"
KEYS = ("token", "thread_id", "generated_at", "deadline_at",
        "context_sha256", "pending_sha256")
PRIMARY = "f6257de79148581334ee495e6e2d60ccb525457c"
COMMIT = "46adb90573118902d0a7c7723ce8817a085f38b9"
CID = "hierarchy-native-distribution-embedding-composition"
CONFIG = "configs/Quard/ctf_hcg_csort_nde/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde.yaml"
RUNTIME = "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
SERVERS_SHA = "fd465e93a88a0b92199e7b911575a5a50ac9be453356b5f8db4cf4e24420335e"


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def guard():
    assert sys.dont_write_bytecode and os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
    assert os.environ.get("CODEX_THREAD_ID") == AUTHOR
    o = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    owner = {k: o[k] for k in KEYS}
    assert owner["token"] == TOKEN
    assert owner["thread_id"] == "01a159c5-29ab-7a22-ba7f-e79174757253"
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
    assert sha(ROOT / "SERVERS.yaml") == SERVERS_SHA
    return owner


def save(name, value):
    guard()
    path = HERE / name
    assert path.resolve().is_relative_to(HERE.resolve())
    raw = value if isinstance(value, bytes) else (value.encode() if isinstance(value, str)
          else (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())
    with path.open("xb") as stream:
        stream.write(raw)


def replace_one(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def common(text):
    # Nonrecursive sequence: candidate f625 ->46ad, historical parent0ccc ->f625.
    for old, new in [
        (PRIMARY, COMMIT),
        ("0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d", PRIMARY),
        ("hierarchy-native-spatial-dirichlet-composition", CID),
        ("M232-NSD", "M233-NDE"),
        ("/data/songcl/Project/Cluster_project/Cluster_psc_20261106", RUNTIME),
        ("1f1ba94e90c6f44e2e9cb0e6f1e746568e38cc1e92f398ee49efc5e8c40232bf", SERVERS_SHA),
        ("_nsd", "_nde"), ("nsd_", "nde_"), ("NSD", "NDE"),
    ]:
        text = text.replace(old, new)
    return text


def main():
    owner = guard()
    native_root = TICK / "nde_native_prepare"
    native = native_root / "native" if (native_root / "native/preparation.json").is_file() else native_root
    # Missing native hashes are a stop, never a fabricated producer binding.
    required = [native / "preparation.json", native / "manifest_template.json",
                native / "source_version_binding.json", native / "worker.py",
                native / "native_runtime.py", native_root / "FROZEN.json"]
    assert all(p.is_file() for p in required), "NDE native producer is not frozen; no operational files generated"
    native_prepared = read(native / "preparation.json")
    template = read(native / "manifest_template.json")
    assert native_prepared["source_commit"] == COMMIT and native_prepared["candidate_id"] == CID
    assert template["config"] == CONFIG
    assert native_prepared.get("native", "NOT_RUN") == "NOT_RUN"
    assert all(sha(native / n) == s for n, s in native_prepared["prepared_file_hashes"].items())
    assert all(sha(native_root / n) == s for n, s in read(native_root / "FROZEN.json")["files"].items())
    assert sha(OLD / "adapter.py") == "cce23f1a820c4fc095b769ccfaa433d4d13fdf0e73fb62fe2a8f4e321a714fae"
    assert sha(OLD / "remote_ops.py") == "7b1946bb1ff29640dbd280c8aeea52087cfc515b14f1cb9565c3e251ffe14408"
    assert sha(OLD / "run_nsd_operation.py") == "3c825c8618056c0783255db83e23e5aa7826073730aafff298b96a4a31d6e6c6"

    launcher = common((OLD / "run_nsd_operation.py").read_bytes().decode())
    remote = common((OLD / "remote_ops.py").read_bytes().decode())
    save("run_nde_operation.py", launcher)
    save("remote_ops.py", remote)
    old_binding = read(OLD / "current_binding.json")
    binding = {**old_binding, "candidate_id": CID, "experiment_id": "M233-NDE",
               "owner": owner, "source_commit": COMMIT, "source_parent_commit": PRIMARY,
               "runtime_code_commit": PRIMARY, "runtime_root": RUNTIME,
               "SERVERS_sha256": SERVERS_SHA,
               "mother_FROZEN": ref(native_root / "FROZEN.json"),
               "mother_native_preparation": ref(native / "preparation.json"),
               "source_proof": ref(ROOT / "pipeline/diagnostic_bundles/tick_13eb9f90/nde_source_commit.json"),
               "source_review": ref(ROOT / "pipeline/diagnostic_bundles/tick_13eb9f90/nde_source_commit_independent_review.json"),
               "activation_files": {n: sha(HERE / n) for n in ("remote_ops.py", "run_nde_operation.py")}}
    save("current_binding.json", binding)
    adapter = common((OLD / "adapter.py").read_bytes().decode())
    adapter = replace_one(adapter, "FROZEN = Path(__file__).resolve().parent/'native'",
                          "FROZEN = PROJECT_ROOT/" + repr(native.relative_to(ROOT).as_posix()))
    adapter = replace_one(adapter, "PREPARATION_SHA = '1561c98a81d8a0ba07bc769bd51c939c7c54a5c7eed5bf2d8cc921d5ed22be31'",
                          "PREPARATION_SHA = " + repr(sha(native / "preparation.json")))
    adapter = replace_one(adapter, "TEMPLATE_SHA = '62972dc875b48a463fdf17584b2156151a25e62ed77d8994df278aee414f5cd8'",
                          "TEMPLATE_SHA = " + repr(sha(native / "manifest_template.json")))
    adapter = replace_one(adapter, "CURRENT_BINDING_SHA256 = 'ed27fb961428335906c8c96b655962c7fdb7e4b39061b5479e251cfb2ddd954e'",
                          "CURRENT_BINDING_SHA256 = " + repr(sha(HERE / "current_binding.json")))
    adapter = replace_one(adapter, "DRAFT_EXECUTION_DISABLED = False", "DRAFT_EXECUTION_DISABLED = True")
    # Exact current parent technical receipt; no training-completion/efficacy gate.
    for old, new in [
        ("PARENT_EXPERIMENT = 'M231-PSC'", "PARENT_EXPERIMENT = 'M232-NSD'"),
        ("PARENT_CANDIDATE = 'hierarchy-native-position-feature-cross-scatter-composition'",
         "PARENT_CANDIDATE = 'hierarchy-native-spatial-dirichlet-composition'"),
        ("PARENT_CONFIG = 'configs/Quard/ctf_hcg_csort_psc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psc.yaml'",
         "PARENT_CONFIG = 'configs/Quard/ctf_hcg_csort_nsd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nsd.yaml'"),
        ("receipt_path=self.root/'pipeline/admissions/M231-PSC.json'",
         "receipt_path=self.root/'pipeline/admissions/M232-NSD.json'"),
    ]:
        adapter = replace_one(adapter, old, new)
    save("adapter.py", adapter)
    release = read(OLD / "release_template.json")
    release.update(candidate_id=CID, experiment_id="M233-NDE", code_commit=COMMIT,
                   native_preparation_sha256=sha(native / "preparation.json"),
                   manifest_template_sha256=sha(native / "manifest_template.json"),
                   source_version_binding_sha256=sha(native / "source_version_binding.json"),
                   source_hashes={n: sha(HERE / n) for n in ("adapter.py", "remote_ops.py")},
                   draft_execution_disabled=True, operational_ready=False,
                   current_binding=ref(HERE / "current_binding.json"))
    release["purpose"] = "Disabled current-owner NDE operational software template; no execution release."
    release["conditional_parent_promotion"] = {
        "expected_primary_HEAD": PRIMARY, "required_technical_receipt": "pipeline/admissions/M232-NSD.json",
        "profile": "experiment_first", "training_completion_or_effect_requirement": False,
        "applies_to_mutations_only": True, "required_NSD_receipt_code_commit": PRIMARY}
    release["resource_policy"]["SERVERS_sha256"] = SERVERS_SHA
    release["runtime_binding"] = {"expected_runtime_code_commit": PRIMARY, "remote_code_root": RUNTIME}
    save("release_template.json", release)
    save("README.md", (
        "Disabled NDE operational preparation only. The original proven NSD adapter/transport/one-shot "
        "protocol is reused with separately saved NDE owner/source/runtime/root/UUID/native-producer hashes. "
        "Runtime remains actual deployed parent Cluster_nsd_20261107/f625; candidate46ad is a frozen stage overlay. "
        "SERVERS and expired production shim are unchanged; diagnostics use immutable baseconda6c80 only. "
        "Root must independently review this exact disabled package, create a separately reviewed activated copy/release, "
        "anchor its preparation/release and actual goal hash in the candidate, then perform fresh resource checks. "
        "No adapter_release.json, prepare request, execution binding/manifest/lease, remote stage, SSH or GPU use is created. "
        "Original360/420/1020-second margins and uncertain-launch reconcile semantics remain unchanged.\n"))
    names = ["build_disabled_operational.py", "ROOT_ACTIVATION.md", "coordination.json", "adapter.py", "remote_ops.py",
             "run_nde_operation.py", "current_binding.json", "release_template.json", "README.md"]
    checks = {"AST_compilation_only": True, "no_Torch_or_adapter_import": True,
              "native_producers_hash_bound": True, "candidate_overlay_parent_runtime_not_deployed_NDE": True,
              "DRAFT_EXECUTION_DISABLED_True": True, "no_adapter_release": not (HERE / "adapter_release.json").exists(),
              "no_execution_metadata": True, "no_SSH_GPU_or_native_execution": True}
    for name in ("adapter.py", "remote_ops.py", "run_nde_operation.py"):
        compile(ast.parse((HERE / name).read_text(encoding="utf8")), name, "exec")
    save("change_manifest.json", {
        "recorded_at": datetime.now(timezone.utc).isoformat(), "owner_provenance_only": owner,
        "producer_agent": "/root/nde_ops", "producer_thread_id": AUTHOR,
        "reused_original_operational": {n: ref(OLD / n) for n in ("adapter.py", "remote_ops.py", "run_nsd_operation.py")},
        "changes": ["candidate identity/source46ad, current parent/runtimef625+actual root, SERVERS hash",
                    "original M232 technical receipt as current parent; no efficacy/completion gate",
                    "current six-field owner, NDE stage/manifest/model package labels and native producer hashes",
                    "native packet external project-local path; no duplicate packet copy",
                    "DRAFT=True; no root release/execution metadata"], "checks": checks})
    names.append("change_manifest.json")
    save("preparation.json", {
        "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CID, "experiment_id": "M233-NDE", "code_commit": COMMIT,
        "owner_provenance_only": owner, "producer_agent": "/root/nde_ops", "producer_thread_id": AUTHOR,
        "native_preparation": ref(native / "preparation.json"),
        "native_manifest_template": ref(native / "manifest_template.json"),
        "current_binding": ref(HERE / "current_binding.json"), "release_template": ref(HERE / "release_template.json"),
        "root_launcher": ref(HERE / "run_nde_operation.py"),
        "prepared_file_hashes": {n: sha(HERE / n) for n in names},
        "draft_execution_disabled": True, "operational_ready": False,
        "native": "NOT_RUN", "resources": "NOT_RUN", "no_active_execution_metadata": True})
    names.append("preparation.json")
    save("FROZEN.json", {"schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CID, "experiment_id": "M233-NDE", "producer_agent": "/root/nde_ops",
        "producer_thread_id": AUTHOR, "files": {n: sha(HERE / n) for n in names},
        "draft_execution_disabled": True, "root_release_created": False,
        "execution_binding": None, "lease": None, "manifest": None, "remote_stage": None,
        "native": "NOT_RUN", "resources": "NOT_RUN"})
    print(json.dumps({"preparation": ref(HERE / "preparation.json"), "FROZEN": ref(HERE / "FROZEN.json"),
                      "disabled": True, "SSH_GPU_or_native_execution": False}))


if __name__ == "__main__":
    main()
