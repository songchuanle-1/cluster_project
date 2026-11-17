"""Fresh MIC activation copy from final reviewed bytes; no old assembler or execution."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import os

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
OLD = ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_prepare"
EXPECTED = {
    "token": "abb177b593654188aa78ca4196688dc5",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-05T11:05:11.386845+00:00",
    "deadline_at": "2026-11-05T12:05:11.386845+00:00",
    "context_sha256": "2f8cbe9b50330d57dbaaddb2698777f393d51171fd9c496c9834402cec876768",
    "pending_sha256": "b56a0651b5b633a042808e3a029e71a5e54d094ebb4cd6c28aedb65fb56cc47a",
}
CHILD = "01a1a684-e37c-7023-a69a-924d4014a2d5"
CHECKS = {
    "SERVERS.yaml": "f046762ec6e87321a70d2595cf35e52fa6e57b3f4aa585ab1fedbf624ae7ef6c",
    "pipeline/goal.json": "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85",
    "pipeline/execution_mode.json": "9eee762e94931ad0788895edd5b80641919069583d5d4e96681260300f85fa51",
    "pipeline/closure_policy.json": "299396caa229f5cb680e12d1f0c895c1d35155d619e7dbf0a1fb6cdc3f302efc",
    "pipeline/authorizations/server4_gpu0_overlay_20261104.json": "783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88",
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
    assert {k: owner.get(k) for k in EXPECTED} == EXPECTED
    assert os.environ.get("CODEX_THREAD_ID") == CHILD and CHILD != EXPECTED["thread_id"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(EXPECTED["deadline_at"])
    assert all(sha(ROOT / name) == digest for name, digest in CHECKS.items())
    assert HERE.resolve() == (ROOT / "pipeline/diagnostic_bundles/tick_abb177b5/mic_gpu0_activation").resolve()


def put(path, value):
    guard()
    path = Path(path).resolve()
    assert path.is_relative_to(HERE.resolve()) and path != HERE.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(value)
    guard()


def dump(path, value):
    put(path, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode())


def main():
    guard()
    assert not (HERE / "FROZEN.json").exists(), "Never rebuild a frozen activation"
    old_hashes = {q.relative_to(OLD).as_posix(): sha(q) for q in OLD.rglob("*") if q.is_file()}
    prior_review = read(ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_independent_review.json")
    assert prior_review["passed"] is True
    assert all(sha(OLD / n) == h for n, h in prior_review["checked_files"].items())
    native = HERE / "native"
    operational = HERE / "operational"
    for rel in ["candidate.yaml", "worker.py"] + [
        q.relative_to(OLD / "native").as_posix() for q in (OLD / "native/candidate_model").glob("*.py")
    ]:
        put(native / rel, (OLD / "native" / rel).read_bytes())
    runtime = (OLD / "native/native_runtime.py").read_bytes()
    assert runtime.count(b"DRAFT_EXECUTION_DISABLED = True") == 1
    put(native / "native_runtime.py", runtime.replace(b"DRAFT_EXECUTION_DISABLED = True", b"DRAFT_EXECUTION_DISABLED = False", 1))
    version = read(OLD / "native/source_version_binding.json")
    version["independent_source_review"] = ref(ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_compatible_source_independent_review.json")
    version["activation_provenance_only_not_execution_lease"] = {
        "owner": EXPECTED, "actual_author_child_thread": CHILD,
        "producer_source_binding": ref(OLD / "native/source_version_binding.json"),
        "producer_native_preparation": ref(OLD / "native/preparation.json"),
        "producer_software_review": ref(ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_independent_review.json"),
    }
    dump(native / "source_version_binding.json", version)
    template = read(OLD / "native/manifest_template.json")
    template["draft_execution_disabled"] = False
    template["activation_provenance_only"] = {
        "owner": EXPECTED, "actual_author_child_thread": CHILD,
        "producer_native_preparation": ref(OLD / "native/preparation.json"),
        "producer_worker": ref(OLD / "native/worker.py"),
        "producer_runtime": ref(OLD / "native/native_runtime.py"),
        "original_protocol_text_preserved": True,
    }
    template["source_version_binding_sha256"] = sha(native / "source_version_binding.json")
    for name in template["diagnostic_files"]:
        template["diagnostic_files"][name] = sha(native / name)
    dump(native / "manifest_template.json", template)
    put(native / "README.md", (
        "Fresh enabled MIC native copy; awaiting external review/static release registration and live resource checks. "
        "Final worker5bdaa and eight model files/original YAML are exact producer bytes. Runtime differs only by "
        "DRAFT_EXECUTION_DISABLED=True->False. Original scientific protocol text is retained as historical producer "
        "description, including its old draft prose; operative activation flag here is false. Ten execution fields "
        "remain NULL; only a reviewed root prepare may create a new manifest/lease/binding. No native result exists.\n"
    ).encode())
    nprep = read(OLD / "native/preparation.json")
    nprep.update(
        status="FRESH_MIC_ENABLED_COPY_PENDING_EXTERNAL_REVIEW_AND_RELEASE_NOT_EXECUTED",
        recorded_at=datetime.now(timezone.utc).isoformat(),
        draft_execution_disabled=False, operational_ready=False,
        prepared_under_parent_owner=EXPECTED, actual_child_thread=CHILD,
        compatible_source_review=ref(ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_compatible_source_independent_review.json"),
        independent_source_review=ref(ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_compatible_source_independent_review.json"),
        producer_native_preparation=ref(OLD / "native/preparation.json"),
        source_version_binding=ref(native / "source_version_binding.json"),
        manifest_template=ref(native / "manifest_template.json"),
        worker=ref(native / "worker.py"), runtime=ref(native / "native_runtime.py"),
        independent_review="PENDING_EXTERNAL_NOT_SELF_SIGNED",
    )
    nprep["prepared_file_hashes"] = {name: sha(native / name) for name in nprep["prepared_file_hashes"]}
    dump(native / "preparation.json", nprep)
    adapter_bytes = (OLD / "operational/adapter.py").read_bytes()
    mappings = [
        (b"pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_prepare/native",
         b"pipeline/diagnostic_bundles/tick_abb177b5/mic_gpu0_activation/native"),
        (b"0cf08b6caea46a74fb807ec171ffc061d31f1c7bc772b39fa4fcd69d159ded07", sha(native / "preparation.json").encode()),
        (b"2ce9532e9861b9f7bb23b0106987caa04a8cd956606c8a0e61993f37c315e345", sha(native / "manifest_template.json").encode()),
        (b"DRAFT_EXECUTION_DISABLED = True", b"DRAFT_EXECUTION_DISABLED = False"),
    ]
    for previous, current in mappings:
        assert adapter_bytes.count(previous) == 1
        adapter_bytes = adapter_bytes.replace(previous, current, 1)
    put(operational / "adapter.py", adapter_bytes)
    for name in ("remote_ops.py", "run_mic_operation.py"):
        put(operational / name, (OLD / "operational" / name).read_bytes())
    release = read(OLD / "operational/release_template.json")
    release.update(
        purpose="Fresh MIC activation static catalogue; requires independent review/external registration, not execution evidence",
        native_preparation_sha256=sha(native / "preparation.json"),
        manifest_template_sha256=sha(native / "manifest_template.json"),
        source_version_binding_sha256=sha(native / "source_version_binding.json"),
        source_hashes={name: sha(operational / name) for name in ("adapter.py", "remote_ops.py")},
        draft_execution_disabled=False, operational_ready=False,
        activation_provenance_only={"owner": EXPECTED, "actual_author_child_thread": CHILD},
    )
    dump(operational / "release_template.json", release)
    put(operational / "README.md", (
        "Fresh MIC enabled operational copy. Only native location/hash constants and DRAFT flag differ from "
        "reviewed GPU0 shared adapter. remote_ops and root launcher remain byte-exact. No adapter_release.json "
        "is supplied: root must register an independently reviewed exact release_template copy and external "
        "candidate anchors before any probe/prepare/stage/run. Original local-idle,20000MiB,three locks,max1,"
        "1020sec and no-replay safeguards remain. Actual manifest/lease/binding/request/stage not created.\n"
    ).encode())
    provenance = {
        "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "owner_provenance_only": EXPECTED, "actual_author_child_thread": CHILD,
        "producer_preparation": ref(OLD / "preparation.json"),
        "producer_operational_preparation": ref(OLD / "operational/preparation.json"),
        "producer_native_preparation": ref(OLD / "native/preparation.json"),
        "producer_independent_review": ref(ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_independent_review.json"),
        "compatible_source_review": ref(ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_compatible_source_independent_review.json"),
        "source_commit": "07ef534a6e44f22bd7b2d083550ebd7823d1d3d3",
        "source_parent_commit": "6bc36adfe42764aac2209e6600fb3a783e2fa374",
        "runtime_code_commit": "6bc36adfe42764aac2209e6600fb3a783e2fa374",
        "runtime_root": "/data/songcl/Project/Cluster_project/Cluster_nec_20261104",
        "physical_gpu": 0, "gpu_uuid": "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c",
        "historical_LFT_technical_receipt_code_commit": "4457a46f9075f61e83340aa0f0af87d5bf4e986c",
        "resource_authorization": nprep["resource_authorization"],
        "resource_memory_policy": nprep["resource_memory_policy"],
        "runtime_change_only": "DRAFT_EXECUTION_DISABLED = True -> False",
        "adapter_literal_changes": [(a.decode(), b.decode()) for a, b in mappings],
        "worker_model8_yaml_remote_launcher_exact_producer_bytes": True,
        "old_assembler_executed": False, "root_environment_impersonated": False,
        "producer_files_preserved": old_hashes,
        "native": "NOT_RUN", "resources": "NOT_RUN",
        "independent_review": "PENDING_EXTERNAL_NOT_SELF_SIGNED",
    }
    dump(operational / "port_provenance.json", provenance)
    oprep = read(OLD / "operational/preparation.json")
    oprep.update(
        status="FRESH_MIC_ENABLED_COPY_PENDING_EXTERNAL_REVIEW_AND_RELEASE_NOT_EXECUTED",
        recorded_at=datetime.now(timezone.utc).isoformat(),
        draft_execution_disabled=False, operational_ready=False,
        prepared_under_parent_owner=EXPECTED, actual_author_child_thread_id=CHILD,
        producer_operational_preparation=ref(OLD / "operational/preparation.json"),
        native_preparation=ref(native / "preparation.json"),
        native_manifest_template=ref(native / "manifest_template.json"),
        native_source_version_binding=ref(native / "source_version_binding.json"),
        compatible_source_review=ref(ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_compatible_source_independent_review.json"),
        release_template=ref(operational / "release_template.json"),
        root_launcher=ref(operational / "run_mic_operation.py"),
        literal_port_provenance=ref(operational / "port_provenance.json"),
        production_static_release="NOT_CREATED; root external independent review and candidate anchors required",
    )
    oprep["prepared_file_hashes"] = {name: sha(operational / name) for name in oprep["prepared_file_hashes"]}
    dump(operational / "preparation.json", oprep)
    for q in HERE.rglob("*.py"):
        ast.parse(q.read_text(encoding="utf-8"))
    dump(HERE / "preparation.json", {
        "schema_version": 1, "candidate_id": nprep["candidate_id"], "experiment_id": "M229-MIC",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": "FRESH_ACTIVATION_COPY_PREPARED_PENDING_EXTERNAL_REVIEW_RELEASE_AND_LIVE_RESOURCE_CHECKS",
        "owner_provenance_only": EXPECTED, "actual_author_child_thread": CHILD,
        "native_preparation": ref(native / "preparation.json"),
        "operational_preparation": ref(operational / "preparation.json"),
        "release_template": ref(operational / "release_template.json"),
        "root_launcher": ref(operational / "run_mic_operation.py"),
        "provenance": ref(operational / "port_provenance.json"),
        "actual_execution_materials": "NOT_CREATED", "native": "NOT_RUN", "resources": "NOT_RUN",
        "scientific_admission": False, "independent_review": "PENDING_EXTERNAL_NOT_SELF_SIGNED",
        "source_commit": provenance["source_commit"], "runtime_code_commit": provenance["runtime_code_commit"],
        "all10_template_execution_fields_NULL": True,
    })
    assert {q.relative_to(OLD).as_posix(): sha(q) for q in OLD.rglob("*") if q.is_file()} == old_hashes
    guard()
    print(json.dumps({"prepared": ref(HERE / "preparation.json"), "native": "NOT_RUN", "resources": "NOT_RUN"}))


if __name__ == "__main__":
    main()
