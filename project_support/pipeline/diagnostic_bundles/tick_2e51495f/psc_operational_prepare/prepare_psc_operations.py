"""Create a new disabled PSC catalogue from the reviewed HVD operational code."""
from datetime import datetime, timezone
from pathlib import Path
import ast
import copy
import hashlib
import json
import os

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
OLD = ROOT / "pipeline/diagnostic_bundles/tick_c7451cf1/hvd_operational_prepare"
NATIVE = HERE.parent / "psc_native_prepare/native"
TOKEN = "2e51495f07244023946fc53eec6e6d98"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
SOURCE = "0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
RUNTIME = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"
HISTORICAL_LFT = "4457a46f9075f61e83340aa0f0af87d5bf4e986c"
CANDIDATE = "hierarchy-native-position-feature-cross-scatter-composition"
EXPERIMENT = "M231-PSC"
REMOTE_ROOT = "/data/songcl/Project/Cluster_project/Cluster_hvd_20261106"
SERVERS_SHA = "6a87d428190d77955500b34d58bff0310eecb13c8b233c7b3e4fd7ef253787a7"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return {"path": Path(path).relative_to(ROOT).as_posix(), "sha256": sha(path)}


def guard():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"] == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
    assert sha(ROOT / "SERVERS.yaml") == SERVERS_SHA
    return {k: owner[k] for k in (
        "token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256",
    )}


def write(path, value):
    guard()
    assert Path(path).resolve().is_relative_to(HERE.resolve())
    data = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    with Path(path).open("xb") as stream:
        stream.write(data)


def literal_port(text, preparation_sha, template_sha):
    substitutions = [
        ("pipeline/diagnostic_bundles/tick_c7451cf1/hvd_native_prepare/native",
         "pipeline/diagnostic_bundles/tick_2e51495f/psc_native_prepare/native"),
        ("hierarchy-native-variance-decomposition-composition", CANDIDATE),
        ("M230-HVD", EXPERIMENT),
        ("e38d92db60f43dde00ae0e537493dc3f3dfc82db", SOURCE),
        ("e781aa7a3709392242945e2393a262187b7b8800ee3bc66c7ce765c4c54038dc", preparation_sha),
        ("43dd4ac595646917004e3e29f9ac48dc5b262388a1cd9df1537b51b27b7201c6", template_sha),
        ("HVD", "PSC"), ("hvd_", "psc_"), ("_hvd", "_psc"),
        ("EXPECTED_RUNTIME_COMMIT = '6bc36adfe42764aac2209e6600fb3a783e2fa374'",
         "EXPECTED_RUNTIME_COMMIT = '" + RUNTIME + "'"),
        ("EXPECTED_PRIMARY_COMMIT = '6bc36adfe42764aac2209e6600fb3a783e2fa374'",
         "EXPECTED_PRIMARY_COMMIT = '" + RUNTIME + "'"),
        ("EXPECTED_RUNTIME='6bc36adfe42764aac2209e6600fb3a783e2fa374'",
         "EXPECTED_RUNTIME='" + RUNTIME + "'"),
        ("f046762ec6e87321a70d2595cf35e52fa6e57b3f4aa585ab1fedbf624ae7ef6c", SERVERS_SHA),
        ("/data/songcl/Project/Cluster_project/Cluster_nec_20261104", REMOTE_ROOT),
        ("current NEC6bc", "current HVDd20"),
    ]
    for previous, current in substitutions:
        text = text.replace(previous, current)
    return text, substitutions


def main():
    owner = guard()
    assert not (HERE / "preparation.json").exists(), "Do not rebuild a frozen catalogue"
    native = read(NATIVE / "preparation.json")
    template = read(NATIVE / "manifest_template.json")
    assert native["source_commit"] == template["code_commit"] == SOURCE
    assert native["candidate_id"] == template["candidate_id"] == CANDIDATE
    assert native["draft_execution_disabled"] is True and template["draft_execution_disabled"] is True
    for name, digest in native["prepared_file_hashes"].items():
        assert sha(NATIVE / name) == digest
    native_preparation_sha, template_sha = sha(NATIVE / "preparation.json"), sha(NATIVE / "manifest_template.json")
    prior_hashes = {p.name: sha(p) for p in OLD.iterdir() if p.is_file()}
    all_substitutions = None
    for old_name, new_name in (
        ("adapter.py", "adapter.py"), ("remote_ops.py", "remote_ops.py"),
        ("run_hvd_operation.py", "run_psc_operation.py"),
    ):
        text, substitutions = literal_port((OLD / old_name).read_text(encoding="utf8"), native_preparation_sha, template_sha)
        ast.parse(text)
        write(HERE / new_name, text.encode("utf8"))
        all_substitutions = substitutions
    release = copy.deepcopy(read(OLD / "release_template.json"))
    release.update({
        "purpose": "Disabled PSC software catalogue; no execution release, binding or resource grant.",
        "candidate_id": CANDIDATE, "experiment_id": EXPERIMENT, "code_commit": SOURCE,
        "native_preparation_sha256": native_preparation_sha,
        "manifest_template_sha256": template_sha,
        "source_version_binding_sha256": sha(NATIVE / "source_version_binding.json"),
        "source_hashes": {name: sha(HERE / name) for name in ("adapter.py", "remote_ops.py")},
        "selection_scope": "Only GPU0, external sharing permitted, real free memory >=20000MiB, projectmax1 and three locks. Existing HVD excludes concurrent PSC diagnostics.",
        "runtime_binding": {"expected_runtime_code_commit": RUNTIME, "remote_code_root": REMOTE_ROOT},
    })
    release["resource_policy"]["SERVERS_sha256"] = SERVERS_SHA
    release["conditional_parent_promotion"]["expected_primary_HEAD"] = RUNTIME
    assert release["conditional_parent_promotion"]["historical_LFT_receipt_code_commit"] == HISTORICAL_LFT
    assert release["conditional_parent_promotion"]["required_technical_receipt"] == "pipeline/admissions/M227-LFT.json"
    write(HERE / "release_template.json", release)
    write(HERE / "README.md", (
        "PSC disabled local operational catalogue, source0ccc(parentd20), runtimeHVDd20. "
        "The unchanged historical LFT4457 technical receipt remains a separate legacy anchor; "
        "it is not the current source/runtime and never permits resume of paused LFT. "
        "DRAFT=True and ten native execution fields NULL; no adapter_release/binding/manifest/"
        "lease/request or remote stage. Real HVD owns the sole project GPU0 slot. "
        "Future current-owner activation and actual native TRAIN2/resources remain necessary. "
        "No shared lifecycle, source, model, runtime, scheduler or GPU operation occurs here.\n"
    ).encode())
    provenance = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "prepared_under_owner_provenance_only": owner,
        "producer": ref(OLD / "preparation.json"),
        "producer_file_hashes": prior_hashes,
        "native_preparation": ref(NATIVE / "preparation.json"),
        "literal_substitutions_in_order": all_substitutions,
        "historical_LFT_receipt_commit_preserved": HISTORICAL_LFT,
        "current_source_commit": SOURCE, "current_runtime_commit": RUNTIME,
        "scope": "New disabled software copy; original frozen files and historical versions unchanged.",
    }
    write(HERE / "port_provenance.json", provenance)
    preparation = {
        "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE, "experiment_id": EXPERIMENT, "code_commit": SOURCE,
        "source_commit": SOURCE, "source_parent_commit": RUNTIME,
        "expected_runtime_code_commit": RUNTIME, "local_primary_commit": RUNTIME,
        "historical_parent_receipt_commit": HISTORICAL_LFT,
        "status": "DISABLED_PSC_GPU0_OVERLAY_SOFTWARE_PREPARED_NOT_NATIVE",
        "draft_execution_disabled": True, "operational_ready": False,
        "prepared_under_owner_provenance_only": owner,
        "native_preparation": ref(NATIVE / "preparation.json"),
        "native_manifest_template": ref(NATIVE / "manifest_template.json"),
        "native_source_version_binding": ref(NATIVE / "source_version_binding.json"),
        "release_template": ref(HERE / "release_template.json"),
        "root_launcher": ref(HERE / "run_psc_operation.py"),
        "literal_port_provenance": ref(HERE / "port_provenance.json"),
        "resource_authorization": release["resource_policy"]["authorization"],
        "resource_memory_policy": release["resource_policy"]["resource_memory_policy"],
        "prepared_file_hashes": {name: sha(HERE / name) for name in (
            "adapter.py", "remote_ops.py", "run_psc_operation.py", "release_template.json",
            "README.md", "port_provenance.json", "prepare_psc_operations.py", "local_software_check.py",
        )},
        "native": "NOT_RUN", "resources": "NOT_RUN", "full_forward": "NOT_RUN",
        "Torch_autograd": "NOT_RUN", "efficacy": "UNKNOWN", "novelty": "UNKNOWN",
        "independent_review": "PENDING_EXTERNAL_NOT_SELF_SIGNED",
    }
    write(HERE / "preparation.json", preparation)
    assert {p.name: sha(p) for p in OLD.iterdir() if p.is_file()} == prior_hashes
    guard()
    print(json.dumps({"prepared": True, "preparation": ref(HERE / "preparation.json"),
                      "DRAFT": True, "native": "NOT_RUN", "resources": "NOT_RUN"}))


if __name__ == "__main__":
    main()
