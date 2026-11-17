"""Create only a disabled local HVD operational preparation from reviewed MIC."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import os

HERE = Path(__file__).resolve().parent
ROOT = Path("D:/project/cluster_project")
OLD = ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_prepare/operational"
NATIVE = HERE.parent / "hvd_native_prepare/native"
EXPECTED = {
    "token": "c7451cf19cec4fc5aa23d2984eb0a249",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-04T17:11:17.373995+00:00",
    "deadline_at": "2026-11-04T18:11:17.373995+00:00",
    "context_sha256": "f0c58a6071231640baaeec3cda1f21eb851f1d79c77be602dc04ba1feb638afb",
    "pending_sha256": "4a4437aee29ce2e814c170b89a07511e56552a8a9d71fec57aed927898f50de5",
}
CHILD = "01a1a684-e37c-7023-a69a-924d4014a2d5"
SOURCE = "e38d92db60f43dde00ae0e537493dc3f3dfc82db"
RUNTIME = "6bc36adfe42764aac2209e6600fb3a783e2fa374"
HISTORICAL_LFT = "4457a46f9075f61e83340aa0f0af87d5bf4e986c"
CANDIDATE = "hierarchy-native-variance-decomposition-composition"
EXPERIMENT = "M230-HVD"
CHECKS = {
    "SERVERS.yaml": "f046762ec6e87321a70d2595cf35e52fa6e57b3f4aa585ab1fedbf624ae7ef6c",
    "pipeline/goal.json": "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85",
    "pipeline/execution_mode.json": "9eee762e94931ad0788895edd5b80641919069583d5d4e96681260300f85fa51",
    "pipeline/closure_policy.json": "299396caa229f5cb680e12d1f0c895c1d35155d619e7dbf0a1fb6cdc3f302efc",
    "pipeline/authorizations/server4_gpu0_overlay_20261104.json": "783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88",
    "pipeline/authorizations/experiment_first_20261021.json": "2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8",
    "pipeline/headless/.tick_context.json": EXPECTED["context_sha256"],
    "pipeline/headless/.tick_context_state.next.json": EXPECTED["pending_sha256"],
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def ref(path):
    return {"path": Path(path).relative_to(ROOT).as_posix(), "sha256": sha(path)}


def guard():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {k: owner.get(k) for k in EXPECTED} == EXPECTED, "Root owner changed"
    assert os.environ.get("CODEX_THREAD_ID") == CHILD and CHILD != EXPECTED["thread_id"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(EXPECTED["deadline_at"])
    assert all(sha(ROOT / path) == digest for path, digest in CHECKS.items())
    assert HERE.resolve() == (ROOT / "pipeline/diagnostic_bundles/tick_c7451cf1/hvd_operational_prepare").resolve()
    return owner


def write_bytes(path, content):
    guard()
    path = Path(path).resolve()
    assert path.is_relative_to(HERE.resolve()) and path != HERE.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)
    guard()


def write_json(path, value):
    write_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode())


def literal_port(text, native_preparation_sha, native_template_sha):
    substitutions = [
        ("hierarchy-ancestry-mobius-interaction-composition", CANDIDATE),
        ("M229-MIC", EXPERIMENT),
        ("07ef534a6e44f22bd7b2d083550ebd7823d1d3d3", SOURCE),
        ("pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_prepare/native",
         "pipeline/diagnostic_bundles/tick_c7451cf1/hvd_native_prepare/native"),
        ("0cf08b6caea46a74fb807ec171ffc061d31f1c7bc772b39fa4fcd69d159ded07",
         native_preparation_sha),
        ("2ce9532e9861b9f7bb23b0106987caa04a8cd956606c8a0e61993f37c315e345",
         native_template_sha),
        ("MIC", "HVD"),
        ("mic_", "hvd_"),
        ("_mic", "_hvd"),
    ]
    for previous, current in substitutions:
        text = text.replace(previous, current)
    return text, substitutions


def main():
    guard()
    frozen_native = read(NATIVE.parent / "FROZEN.json")
    assert frozen_native.get("writer_stopped") is True
    assert all(sha(NATIVE.parent / name) == digest for name, digest in frozen_native["files"].items())
    assert all((NATIVE / name).is_file() for name in (
        "preparation.json", "manifest_template.json", "source_version_binding.json")), "Native producer not frozen/ready yet"
    native_preparation = read(NATIVE / "preparation.json")
    template = read(NATIVE / "manifest_template.json")
    assert native_preparation["candidate_id"] == template["candidate_id"] == CANDIDATE
    assert native_preparation["source_commit"] == SOURCE
    for name, digest in native_preparation["prepared_file_hashes"].items():
        path = (NATIVE / name).resolve()
        assert path.is_relative_to(NATIVE.resolve()) and sha(path) == digest
    version_path = ROOT / "pipeline/diagnostic_bundles/tick_265517f1/hvd_version_prepare/isolated_source_version.json"
    version = read(version_path)
    assert version["source_commit"] == SOURCE and version["parent_commit"] == RUNTIME
    assert len(version["source_files_exact9"]) == 9
    old_files = {p.name: sha(p) for p in OLD.iterdir() if p.is_file()}
    native_preparation_sha, native_template_sha = sha(NATIVE / "preparation.json"), sha(NATIVE / "manifest_template.json")
    all_substitutions = None
    for old_name, new_name in (
        ("adapter.py", "adapter.py"),
        ("remote_ops.py", "remote_ops.py"),
        ("run_mic_operation.py", "run_hvd_operation.py"),
    ):
        text, substitutions = literal_port((OLD / old_name).read_bytes().decode("utf-8"), native_preparation_sha, native_template_sha)
        ast.parse(text)
        write_bytes(HERE / new_name, text.encode("utf-8"))
        all_substitutions = substitutions
    release = read(OLD / "release_template.json")
    release.update(
        purpose="Disabled static GPU0 shared-resource HVD catalogue; not an execution activation or result",
        candidate_id=CANDIDATE,
        experiment_id=EXPERIMENT,
        code_commit=SOURCE,
        native_preparation_sha256=native_preparation_sha,
        manifest_template_sha256=native_template_sha,
        source_version_binding_sha256=sha(NATIVE / "source_version_binding.json"),
        source_hashes={name: sha(HERE / name) for name in ("adapter.py", "remote_ops.py")},
    )
    release["selection_scope"] = release["selection_scope"].replace("MIC", "HVD")
    write_json(HERE / "release_template.json", release)
    write_bytes(HERE / "README.md", (
        "HVD GPU0 shared-resource disabled operational draft. Exact reviewed HVD source e38d92db "
        "is a child of6bc; local primary/runtime remain6bc/current NEC checkout. Historical LFT "
        "technical receipt4457 stays separate. Exact current overlay grant permits physicalGPU0 "
        "only, free memory>=20000MiB, max1project task and three cooperative project locks. "
        "Existing NEC makes _local_idle refuse a concurrent HVD diagnostic. DRAFT remainsTrue, "
        "adapter_release.json and actual request/manifest/binding/lease/stage are absent. "
        "The native template's ten active fields remainNULL. Original1020sec run margin, "
        "common-init/native TRAIN2/resource protocol and no-replay safeguards are unchanged. "
        "This directory supplies only local software preparation, not native/resource evidence.\n"
    ).encode())
    provenance = {
        "schema_version": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "prepared_under_parent_owner": EXPECTED,
        "actual_author_child_thread_id": CHILD,
        "scope": "Exact literal HVD identity/native hash port of reviewed MIC GPU0 shared operational code. No source, Git, SSH, GPU, native, remote staging or shared lifecycle operation.",
        "original_operational_preparation": ref(OLD / "preparation.json"),
        "reviewed_original_independent_review": ref(ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_independent_review.json"),
        "native_preparation": ref(NATIVE / "preparation.json"),
        "native_manifest_template": ref(NATIVE / "manifest_template.json"),
        "native_source_version_binding": ref(NATIVE / "source_version_binding.json"),
        "native_outer_preparation": ref(NATIVE.parent / "preparation.json"),
        "native_frozen_packet": ref(NATIVE.parent / "FROZEN.json"),
        "isolated_source_version": ref(version_path),
        "source_commit": SOURCE,
        "source_parent_commit": RUNTIME,
        "expected_runtime_code_commit": RUNTIME,
        "historical_LFT_technical_receipt_code_commit": HISTORICAL_LFT,
        "literal_substitutions_in_order": all_substitutions,
        "original_operational_file_hashes": old_files,
        "resource_authorization": release["resource_policy"]["authorization"],
        "resource_memory_policy": release["resource_policy"]["resource_memory_policy"],
        "no_execution_binding_created": True,
        "native": "NOT_RUN",
        "resources": "NOT_RUN",
        "independent_review": "PENDING_EXTERNAL_NOT_SELF_SIGNED",
    }
    write_json(HERE / "port_provenance.json", provenance)
    preparation = read(OLD / "preparation.json")
    preparation.update(
        candidate_id=CANDIDATE,
        experiment_id=EXPERIMENT,
        source_preparation=ref(ROOT / "pipeline/diagnostic_bundles/tick_265517f1/new_candidate_prepare/preparation.json"),
        native_protocol=ref(ROOT / "pipeline/diagnostic_bundles/tick_265517f1/new_candidate_prepare/native_protocol.md"),
        recorded_at=datetime.now(timezone.utc).isoformat(),
        status="DISABLED_HVD_GPU0_SHARED_CURRENT6BC_SOURCE_E38_METADATA_DRAFT_NOT_RUN",
        code_commit=SOURCE,
        source_commit=SOURCE,
        source_parent_commit=RUNTIME,
        expected_runtime_code_commit=RUNTIME,
        local_primary_commit=RUNTIME,
        prepared_under_parent_owner=EXPECTED,
        actual_author_child_thread_id=CHILD,
        native_preparation=ref(NATIVE / "preparation.json"),
        native_manifest_template=ref(NATIVE / "manifest_template.json"),
        native_source_version_binding=ref(NATIVE / "source_version_binding.json"),
        native_outer_preparation=ref(NATIVE.parent / "preparation.json"),
        native_frozen_packet=ref(NATIVE.parent / "FROZEN.json"),
        isolated_source_version=ref(version_path),
        independent_source_review=ref(ROOT / "pipeline/diagnostic_bundles/tick_265517f1/new_candidate_independent_review.json"),
        release_template=ref(HERE / "release_template.json"),
        root_launcher=ref(HERE / "run_hvd_operation.py"),
        literal_port_provenance=ref(HERE / "port_provenance.json"),
        frozen_NULL_mother_packet_preserved=ref(ROOT / "pipeline/diagnostic_bundles/tick_265517f1/new_candidate_prepare/FROZEN.json"),
    )
    for key in ("historical_source_commit", "historical_source_parent_commit", "historical_independent_source_review"):
        preparation.pop(key, None)
    preparation["historical_parent_receipt_commit"] = HISTORICAL_LFT
    preparation["prepared_file_hashes"] = {
        name: sha(HERE / name) for name in (
            "adapter.py", "port_provenance.json", "README.md", "release_template.json",
            "remote_ops.py", "run_hvd_operation.py", "prepare_hvd_operations.py", "local_software_check.py",
            "producer_request.json",
        )
    }
    write_json(HERE / "preparation.json", preparation)
    assert {p.name: sha(p) for p in OLD.iterdir() if p.is_file()} == old_files
    guard()
    print(json.dumps({"status": "DISABLED_HVD_OPERATIONAL_DRAFT_PREPARED", "preparation": ref(HERE / "preparation.json"), "native": "NOT_RUN", "resources": "NOT_RUN"}))


if __name__ == "__main__":
    main()
