"""Prepare a new current-owner PSC activation copy; never execute its interfaces."""
from datetime import datetime, timezone
from pathlib import Path
import ast
import copy
import hashlib
import json
import os

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
EXPECTED_HERE = ROOT / "pipeline/diagnostic_bundles/tick_0bb87433/psc_current_activation"
OLD = ROOT / "pipeline/diagnostic_bundles/tick_2e51495f"
NATIVE = OLD / "psc_native_prepare/native"
OPS = OLD / "psc_operational_prepare"
NEW_NATIVE = HERE / "native"
TOKEN = "0bb874337dde412e98bbbaac369f3370"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
CHILD = "01a1b166-dcbf-7d01-b0cb-c85fff644605"
SOURCE = "0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
PARENT = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"
REMOTE_ROOT = "/data/songcl/Project/Cluster_project/Cluster_hvd_20261106"
SERVERS_SHA = "6a87d428190d77955500b34d58bff0310eecb13c8b233c7b3e4fd7ef253787a7"
CID = "hierarchy-native-position-feature-cross-scatter-composition"
OWNER_KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
ACTIVE_FIELDS = ("current_token", "stage", "tick_generated_at", "deadline_at", "physical_gpu",
                 "gpu_uuid", "allowed_gpus", "context_sha256", "pending_sha256", "runtime_code_commit")
WORKER_SHA = "530a5230021fad8d880c37a34c18973b4c556e7dc1536b6c4faaffdd6d6f93d8"
PREP_SHA = "757546b94efb9ac3d2490f68351cea78ca6b64e65495c039cb8e91d5015a4b4f"
TEMPLATE_SHA = "897b26ec1127cbaf4a9799474023e7c41234df045aba5ce67bc9074448a0f49e"
PACKET_REVIEW = OLD / "psc_native_operational_independent_review.json"
PACKET_REVIEW_SHA = "a7ef01e93fa03ebf7818f1351a18329ec71ad6aa2cf3f4c78e8986f43e69d75a"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    path = Path(path)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def guard():
    assert HERE.resolve() == EXPECTED_HERE.resolve()
    assert os.environ.get("CODEX_THREAD_ID") == CHILD != THREAD
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
    assert sha(ROOT / "SERVERS.yaml") == SERVERS_SHA
    return {key: owner[key] for key in OWNER_KEYS}


def save(name, value):
    guard()
    path = (HERE / name).resolve()
    assert path.is_relative_to(HERE.resolve())
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else (
        value.encode("utf8") if isinstance(value, str) else
        (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf8"))
    with path.open("xb") as stream:
        stream.write(raw)
    return path


def replace_once(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new, 1)


def main():
    owner = guard()
    assert sha(NATIVE / "preparation.json") == PREP_SHA
    assert sha(NATIVE / "manifest_template.json") == TEMPLATE_SHA
    assert sha(NATIVE / "worker.py") == WORKER_SHA
    assert sha(PACKET_REVIEW) == PACKET_REVIEW_SHA
    review = read(PACKET_REVIEW)
    assert review["passed"] is True
    frozen_refs = []
    for directory in (OLD / "psc_native_prepare", OPS):
        frozen = read(directory / "FROZEN.json")
        assert all(sha(directory / name) == digest for name, digest in frozen["files"].items())
        frozen_refs.append({**ref(directory / "FROZEN.json"), "declared_files_verified": len(frozen["files"])})
    original_prep = read(NATIVE / "preparation.json")
    original_template = read(NATIVE / "manifest_template.json")
    original_version = read(NATIVE / "source_version_binding.json")
    assert original_template["draft_execution_disabled"] is True
    assert all(original_template[key] is None for key in ACTIVE_FIELDS)
    assert original_version["source_commit"] == SOURCE and original_version["parent_commit"] == PARENT
    proof_ref = original_version["isolated_source_version"]
    source_review_ref = original_version["independent_source_review"]
    for entry in (proof_ref, source_review_ref):
        assert sha(ROOT / entry["path"]) == entry["sha256"]
    proof, source_review = (read(ROOT / entry["path"]) for entry in (proof_ref, source_review_ref))
    assert proof["passed"] is True and source_review["passed"] is True
    assert proof["source_commit"] == source_review["source_commit"] == SOURCE
    assert proof["parent_commit"] == source_review["parent_commit"] == PARENT
    assert proof["source_files_exact9"] == original_version["source_files"]
    assert len(proof["source_files_exact9"]) == 9
    producers = [NATIVE / name for name in (
        "preparation.json", "manifest_template.json", "source_version_binding.json", "worker.py", "native_runtime.py")]
    producers += [OPS / name for name in (
        "adapter.py", "remote_ops.py", "run_psc_operation.py", "preparation.json", "release_template.json")]
    audit = {
        "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CID, "experiment_id": "M231-PSC", "source_commit": SOURCE, "parent_commit": PARENT,
        "owner_provenance_only": owner, "actual_author_child_thread_id": CHILD,
        "frozen_packages": frozen_refs, "producer_files": [ref(path) for path in producers],
        "source_proof": proof_ref, "source_review": source_review_ref,
        "packet_review": ref(PACKET_REVIEW), "exact9_source_files": proof["source_files_exact9"],
        "original_ten_execution_NULLs_preserved": True, "original_DRAFT_True_preserved": True,
        "no_original_packet_written": True, "native": "NOT_RUN", "resources": "NOT_RUN",
        "SSH_GPU_model_execution": False, "execution_material_created": False,
    }
    save("producer_hash_audit.json", audit)
    for name, digest in original_template["diagnostic_files"].items():
        if name in ("native_runtime.py", "source_version_binding.json"):
            continue
        assert sha(NATIVE / name) == digest
        save("native/" + name, (NATIVE / name).read_bytes())
    runtime = (NATIVE / "native_runtime.py").read_text(encoding="utf8")
    runtime = replace_once(runtime, "DRAFT_EXECUTION_DISABLED = True", "DRAFT_EXECUTION_DISABLED = False")
    compile(runtime, "native_runtime.py", "exec")
    save("native/native_runtime.py", runtime)
    version = copy.deepcopy(original_version)
    version.update(draft_execution_disabled=False, producer_source_version_binding=ref(NATIVE / "source_version_binding.json"),
                   producer_author_provenance_only=original_version["author_provenance_only"],
                   author_provenance_only={"prepared_under_current_owner": owner, "actual_child_thread": CHILD,
                                           "execution_binding": False},
                   native_packet_independent_review=ref(PACKET_REVIEW),
                   scope="New current-owner activation metadata for unchanged exact9 PSC bytes; source0ccc parent/current-runtime d20. No execution binding.")
    save("native/source_version_binding.json", version)
    template = copy.deepcopy(original_template)
    template["draft_execution_disabled"] = False
    template["source_version_binding_sha256"] = sha(NEW_NATIVE / "source_version_binding.json")
    for name in ("native_runtime.py", "source_version_binding.json"):
        template["diagnostic_files"][name] = sha(NEW_NATIVE / name)
    assert all(template[key] is None for key in ACTIVE_FIELDS)
    save("native/manifest_template.json", template)
    save("native/README.md", (
        "PSC current-owner activation copy. Worker, exact9 source, TRAIN2/common-init/full-core update and resource function unchanged.\n"
        "DRAFT=False is activation metadata; ten execution fields remain NULL. No release, manifest, binding, lease, request or stage.\n"
        "Root external review and current resource checks remain required. Native/resources NOT_RUN.\n"))
    native_prep = copy.deepcopy(original_prep)
    native_prep.update(recorded_at=datetime.now(timezone.utc).isoformat(),
                       status="CURRENT_OWNER_PSC_NATIVE_ACTIVATION_COPY_PREPARED_NOT_EXECUTED",
                       draft_execution_disabled=False, producer_native_preparation=ref(NATIVE / "preparation.json"),
                       producer_parent_owner_provenance_only=original_prep["prepared_under_current_parent_owner_provenance_only"],
                       prepared_under_current_parent_owner_provenance_only={**owner, "execution_binding": False},
                       actual_child_thread=CHILD, source_version_binding=ref(NEW_NATIVE / "source_version_binding.json"),
                       manifest_template=ref(NEW_NATIVE / "manifest_template.json"),
                       worker=ref(NEW_NATIVE / "worker.py"), runtime=ref(NEW_NATIVE / "native_runtime.py"),
                       native_packet_independent_review=ref(PACKET_REVIEW),
                       independent_review="PENDING_CURRENT_ACTIVATION_EXTERNAL_REVIEW",
                       local_static_validation_scope="Historical producer45 software checks; new activation software evidence is separate.",
                       no_active_manifest_binding_lease_request_result_release_remote_stage=True)
    native_prep["prepared_file_hashes"] = {
        name: sha(NEW_NATIVE / name) for name in original_prep["prepared_file_hashes"]}
    save("native/preparation.json", native_prep)
    save("remote_ops.py", (OPS / "remote_ops.py").read_bytes())
    save("run_psc_operation.py", (OPS / "run_psc_operation.py").read_bytes())
    activation_names = ["native/" + name for name in native_prep["prepared_file_hashes"]]
    activation_names += ["native/preparation.json", "remote_ops.py", "run_psc_operation.py"]
    current = {
        "schema_version": 1, "project": "cluster_project", "candidate_id": CID, "experiment_id": "M231-PSC",
        "owner": owner, "actual_author_child_thread_id": CHILD, "source_commit": SOURCE,
        "source_parent_commit": PARENT, "runtime_code_commit": PARENT, "runtime_root": REMOTE_ROOT,
        "SERVERS_sha256": SERVERS_SHA, "physical_gpu": 0,
        "gpu_uuid": "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c", "allowed_gpus": [0],
        "resource_authorization": template["resource_authorization"], "resource_memory_policy": template["resource_memory_policy"],
        "source_proof": proof_ref, "source_review": source_review_ref, "packet_review": ref(PACKET_REVIEW),
        "frozen_packages": frozen_refs, "producer_files": audit["producer_files"],
        "producer_hash_audit": ref(HERE / "producer_hash_audit.json"),
        "activation_files": {name: sha(HERE / name) for name in activation_names},
        "exact9_source_files": proof["source_files_exact9"], "worker_byte_exact": True,
        "original_NULLs_not_filled": True, "execution_material_created": False,
        "native": "NOT_RUN", "resources": "NOT_RUN", "scientific_admission": False,
        "requires_independently_reviewed_external_candidate_anchors": True,
        "producer_protocol_text_is_preserved_historical_description": True,
        "scope": "New activation copy only; source0ccc/runtime d20, current root/GPU0 policy. Historical LFT4457 receipt remains separate.",
    }
    save("current_binding.json", current)
    adapter = (OPS / "adapter.py").read_text(encoding="utf8")
    adapter = replace_once(adapter, "FROZEN = PROJECT_ROOT/'pipeline/diagnostic_bundles/tick_2e51495f/psc_native_prepare/native'",
                           "FROZEN = Path(__file__).resolve().parent/'native'")
    adapter = replace_once(adapter, "PREPARATION_SHA = '" + PREP_SHA + "'", "PREPARATION_SHA = '" + sha(NEW_NATIVE / "preparation.json") + "'")
    adapter = replace_once(adapter, "TEMPLATE_SHA = '" + TEMPLATE_SHA + "'", "TEMPLATE_SHA = '" + sha(NEW_NATIVE / "manifest_template.json") + "'")
    adapter = replace_once(adapter, "DRAFT_EXECUTION_DISABLED = True", "DRAFT_EXECUTION_DISABLED = False")
    adapter = replace_once(adapter, "PAIRS = (", "CURRENT_BINDING_SHA256 = '" + sha(HERE / "current_binding.json") + "'\nPAIRS = (")
    new_method = '''
    def _activation_details(self):
        path=self.origin/'current_binding.json'
        require(sha(path)==CURRENT_BINDING_SHA256,'Current activation binding changed')
        b=read(path)
        require(b['project']=='cluster_project' and b['candidate_id']==CANDIDATE
            and b['experiment_id']=='M231-PSC' and b['source_commit']==COMMIT
            and b['source_parent_commit']==EXPECTED_PRIMARY_COMMIT
            and b['runtime_code_commit']==EXPECTED_RUNTIME_COMMIT
            and b['runtime_root']==REMOTE_ROOT and b['SERVERS_sha256']==SERVERS_POLICY_SHA256,
            'Current source/runtime/root binding mismatch')
        require(b['physical_gpu']==0 and b['allowed_gpus']==[0] and b['gpu_uuid']==GPU_UUIDS[0]
            and b['resource_authorization']==RESOURCE_AUTHORIZATION
            and b['resource_memory_policy']==RESOURCE_MEMORY_POLICY,'Current resource binding mismatch')
        require(b['execution_material_created'] is False and b['original_NULLs_not_filled'] is True,
            'Current metadata must not be execution material or NULL backfill')
        require(set(b['owner'])=={'token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256'},
            'Current owner schema changed')
        for entry in b['producer_files']+[b['source_proof'],b['source_review'],b['packet_review'],b['producer_hash_audit']]:
            path=(self.root/entry['path']).resolve()
            require(path.is_relative_to(self.root) and sha(path)==entry['sha256'],'Current producer proof changed')
        for entry in b['frozen_packages']:
            path=(self.root/entry['path']).resolve()
            require(path.is_relative_to(self.root) and sha(path)==entry['sha256'],'Original FROZEN changed')
            for name,expected in read(path)['files'].items():
                item=(path.parent/name).resolve()
                require(item.is_relative_to(path.parent.resolve()) and sha(item)==expected,'Original frozen file changed')
        for name,expected in b['activation_files'].items():
            path=(self.origin/name).resolve()
            require(path.is_relative_to(self.origin) and sha(path)==expected,'Activation file changed: '+name)
        proof=read(self.root/b['source_proof']['path']); review=read(self.root/b['source_review']['path'])
        require(proof['passed'] is True and review['passed'] is True
            and proof['source_commit']==review['source_commit']==COMMIT
            and proof['parent_commit']==review['parent_commit']==EXPECTED_PRIMARY_COMMIT,
            'Source proof mismatch')
        version=read(self.frozen/'source_version_binding.json')
        require(version['source_commit']==version['code_commit']==COMMIT
            and version['parent_commit']==EXPECTED_PRIMARY_COMMIT
            and version['runtime_expected_commit']==EXPECTED_RUNTIME_COMMIT
            and version['source_files']==proof['source_files_exact9']==b['exact9_source_files']
            and len(version['source_files'])==9,'Current source version mismatch')
        return b

'''
    adapter = replace_once(adapter, "    def _frozen_details(self):", new_method + "    def _frozen_details(self):")
    adapter = replace_once(adapter, "        return p,read(self.frozen/'manifest_template.json')", '''
        self._activation_details()
        template=read(self.frozen/'manifest_template.json')
        require(template['draft_execution_disabled'] is False and all(template[k] is None for k in
            ('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid',
             'allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')),
            'Activation template must retain all ten execution NULL fields')
        return p,template'''.strip("\n"))
    adapter = replace_once(adapter, "        owner=read(self.root/'pipeline/headless/.foreground.lockdir/owner.json')", '''
        owner=read(self.root/'pipeline/headless/.foreground.lockdir/owner.json')
        binding=self._activation_details()
        require({k:owner[k] for k in ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')}
            ==binding['owner'],'Activation belongs to a different foreground owner')'''.strip("\n"))
    compile(adapter, "adapter.py", "exec")
    save("adapter.py", adapter)
    release = copy.deepcopy(read(OPS / "release_template.json"))
    release.update(purpose="Current-owner PSC activation release template; root external review/anchors required; no execution grant",
                   native_preparation_sha256=sha(NEW_NATIVE / "preparation.json"),
                   manifest_template_sha256=sha(NEW_NATIVE / "manifest_template.json"),
                   source_version_binding_sha256=sha(NEW_NATIVE / "source_version_binding.json"),
                   source_hashes={name: sha(HERE / name) for name in ("adapter.py", "remote_ops.py")},
                   current_binding=ref(HERE / "current_binding.json"), draft_execution_disabled=False,
                   operational_ready=False, independent_review="PENDING_EXTERNAL_ROOT_RELEASE")
    release["selection_scope"] = "Only physical server4 GPU0; external sharing permitted, >=20000MiB free, projectmax1, three original locks; fresh actual checks required."
    assert release["conditional_parent_promotion"]["historical_LFT_receipt_code_commit"] == "4457a46f9075f61e83340aa0f0af87d5bf4e986c"
    save("release_template.json", release)
    save("README.md", (
        "New current-owner PSC activation copy. Source0ccc(parentd20), current runtimeHVDd20; historical LFT4457 receipt stays a separate technical anchor.\n"
        "Frozen original PSC native/ops packets remain DRAFT=True and ten execution fields NULL; new native activation is DRAFT=False with the same ten NULLs.\n"
        "Worker and exact9 source bytes, original four arms, TRAIN2/common-init/full-core update, original resource function, safety guards and1020sec run margin are unchanged.\n"
        "No adapter_release is authored here. Root must independently review, create the exact release, and anchor new preparation/release and worker preparation before guarded operations.\n"
        "No execution manifest/binding/lease/request/remote stage, SSH, GPU or lifecycle action. Native/resources NOT_RUN.\n"))
    core_names = ("build_current_activation.py", "local_software_check.py", "producer_hash_audit.json",
                  "current_binding.json", "adapter.py", "remote_ops.py", "run_psc_operation.py",
                  "release_template.json", "README.md")
    preparation = {
        "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CID, "experiment_id": "M231-PSC", "code_commit": SOURCE, "source_commit": SOURCE,
        "source_parent_commit": PARENT, "expected_runtime_code_commit": PARENT, "runtime_root": REMOTE_ROOT,
        "status": "CURRENT_OWNER_PSC_ACTIVATION_PREPARED_PENDING_EXTERNAL_REVIEW_NOT_EXECUTED",
        "owner_provenance_only": owner, "actual_author_child_thread_id": CHILD,
        "draft_execution_disabled": False, "native_preparation": ref(NEW_NATIVE / "preparation.json"),
        "native_manifest_template": ref(NEW_NATIVE / "manifest_template.json"),
        "native_source_version_binding": ref(NEW_NATIVE / "source_version_binding.json"),
        "native_worker": ref(NEW_NATIVE / "worker.py"), "current_binding": ref(HERE / "current_binding.json"),
        "release_template": ref(HERE / "release_template.json"), "root_launcher": ref(HERE / "run_psc_operation.py"),
        "original_frozen_packages": frozen_refs, "source_proof": proof_ref, "source_review": source_review_ref,
        "producer_packet_review": ref(PACKET_REVIEW),
        "prepared_file_hashes": {name: sha(HERE / name) for name in list(core_names) + activation_names},
        "software_validation_output": (HERE / "software_validation.json").relative_to(ROOT).as_posix(),
        "conditional_parent_promotion": release["conditional_parent_promotion"],
        "resource_authorization": template["resource_authorization"], "resource_memory_policy": template["resource_memory_policy"],
        "original_NULLs_not_filled": True, "worker_exact9_source_byte_exact_copies": True,
        "operational_ready": False, "independent_review": "PENDING_EXTERNAL_NOT_SELF_SIGNED",
        "active_manifest_binding_lease_request_stage_created": False, "adapter_release_created": False,
        "native": "NOT_RUN", "resources": "NOT_RUN", "scientific_admission": False,
    }
    save("preparation.json", preparation)
    guard()
    print(json.dumps({"status": preparation["status"], "preparation": ref(HERE / "preparation.json"),
                      "native_preparation": ref(NEW_NATIVE / "preparation.json"),
                      "manifest_template": ref(NEW_NATIVE / "manifest_template.json"),
                      "current_binding": ref(HERE / "current_binding.json"),
                      "adapter_release_created": False, "native": "NOT_RUN", "resources": "NOT_RUN"}))


if __name__ == "__main__":
    main()
