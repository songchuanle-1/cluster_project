"""Save a thin current-owner HVD binding; never call execution interfaces."""
from datetime import datetime, timezone
from pathlib import Path
import ast
import copy
import hashlib
import json
import os

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
EXPECTED_HERE = ROOT / "pipeline/diagnostic_bundles/tick_154767c2/hvd_current_activation"
OLD = ROOT / "pipeline/diagnostic_bundles/tick_c7451cf1"
NATIVE = OLD / "hvd_native_prepare/native"
OPS = OLD / "hvd_operational_prepare"
TOKEN = "154767c278664ba4a7b666c69f12abaa"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
CHILD = "01a1a684-e37c-7023-a69a-924d4014a2d5"
SOURCE = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"
PARENT = "07ef534a6e44f22bd7b2d083550ebd7823d1d3d3"
LEGACY = "e38d92db60f43dde00ae0e537493dc3f3dfc82db"
LEGACY_PARENT = "6bc36adfe42764aac2209e6600fb3a783e2fa374"
REMOTE_ROOT = "/data/songcl/Project/Cluster_project/Cluster_mic_20261105"
SERVERS_SHA = "84730b8f91db3022d2e1819362d803b20293ea6224cfa9d607b8d4e45e8f43c0"
CID = "hierarchy-native-variance-decomposition-composition"
OWNER_KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
SOURCE_PROOF = ROOT / "pipeline/diagnostic_bundles/tick_1138a3fc/hvd_compatible_source_version.json"
SOURCE_REVIEW = SOURCE_PROOF.with_name("hvd_compatible_source_independent_review.json")
PROOF_SHA = "7e3c09ea021de7350e74a7797e535c91990e3a9b226a20af1ed1917c06e8bc41"
REVIEW_SHA = "315562b89da60d17939678f14e52048fa14f75270519ed7288f41fa77eaecf6d"


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
    assert path.parent == HERE.resolve()
    raw = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(raw)
    return path


def replace_once(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new, 1)


def replace_method(source, name, new):
    klass = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "Adapter")
    node = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == name)
    lines = source.splitlines(keepends=True)
    return "".join(lines[:node.lineno - 1]) + new.rstrip() + "\n" + "".join(lines[node.end_lineno:])


owner = guard()
assert sha(SOURCE_PROOF) == PROOF_SHA and sha(SOURCE_REVIEW) == REVIEW_SHA
proof, review = read(SOURCE_PROOF), read(SOURCE_REVIEW)
assert proof["source_commit"] == SOURCE and proof["parent_commit"] == PARENT
assert review["passed"] is True and review["source_commit"] == SOURCE and review["parent_commit"] == PARENT
assert len(proof["source_files_exact9"]) == 9
frozen_refs = []
frozen_count = 0
for directory, digest in (
    (OLD / "hvd_native_prepare", "926814e2fa1d942f96065ff9c3470bdc25761d3019cf46e9bd579e8637933be5"),
    (OPS, "858e5a4b26c4fa05270cb558f8660d999042c3bf44d88817b0758a2433c43289"),
):
    assert sha(directory / "FROZEN.json") == digest
    frozen = read(directory / "FROZEN.json")
    assert all(sha(directory / name) == expected for name, expected in frozen["files"].items())
    frozen_count += len(frozen["files"])
    frozen_refs.append({**ref(directory / "FROZEN.json"), "declared_files_verified": len(frozen["files"])})
assert frozen_count == 34
legacy_preparation = read(NATIVE / "preparation.json")
legacy_template = read(NATIVE / "manifest_template.json")
legacy_binding = read(NATIVE / "source_version_binding.json")
assert legacy_preparation["source_commit"] == legacy_binding["source_commit"] == LEGACY
assert legacy_binding["parent_commit"] == LEGACY_PARENT
assert legacy_binding["source_files"] == proof["source_files_exact9"]
active_fields = ("current_token", "stage", "tick_generated_at", "deadline_at", "physical_gpu",
                 "gpu_uuid", "allowed_gpus", "context_sha256", "pending_sha256", "runtime_code_commit")
assert all(legacy_template[key] is None for key in active_fields)
mother = ROOT / "pipeline/diagnostic_bundles/tick_265517f1/new_candidate_prepare"
assert sha(mother / "FROZEN.json") == "931a2b02b51dbf43a89efbd6128f42e2672c8fe86314bfa387edc54a0aff4112"
mother_manifest = read(mother / "source_manifest.json")
assert all(mother_manifest[key] is None for key in (
    "source_commit", "code_commit", "source_parent_commit", "actual_parent", "future_version_parent"))
source9 = {}
for name, digest in proof["source_files_exact9"].items():
    path = NATIVE / ("candidate.yaml" if name.endswith(".yaml") else "candidate_model/" + Path(name).name)
    assert sha(path) == digest
    source9[name] = digest
producer_files = [NATIVE / name for name in (
    "preparation.json", "manifest_template.json", "source_version_binding.json", "worker.py", "native_runtime.py")]
producer_files += [OPS / name for name in (
    "adapter.py", "remote_ops.py", "run_hvd_operation.py", "preparation.json", "release_template.json")]
producer_files += [mother / "FROZEN.json", mother / "source_manifest.json"]
producer_refs = [ref(path) for path in producer_files]
audit = {
    "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
    "candidate_id": CID, "experiment_id": "M230-HVD", "actual_author_child_thread_id": CHILD,
    "owner_provenance_only": owner, "source_commit": SOURCE, "parent_commit": PARENT,
    "source_proof": ref(SOURCE_PROOF), "source_review": ref(SOURCE_REVIEW),
    "frozen_packages": frozen_refs, "all34_declared_frozen_files_verified": True,
    "producer_files": producer_refs, "exact9_source_files": source9,
    "source9_matches_compatible_proof_and_frozen_native": True,
    "original_ten_execution_NULLs_preserved": True, "original_mother_NULLs_preserved": True,
    "no_original_packet_written": True, "native": "NOT_RUN", "resources": "NOT_RUN",
    "SSH_GPU_model_execution": False, "execution_material_created": False,
}
save("producer_hash_audit.json", audit)

binding = copy.deepcopy(legacy_binding)
binding.update(code_commit=SOURCE, source_commit=SOURCE, parent_commit=PARENT, runtime_expected_commit=PARENT)
binding["producer_source_version_binding"] = ref(NATIVE / "source_version_binding.json")
binding["producer_isolated_source_version"] = binding["isolated_source_version"]
binding["producer_independent_source_review"] = binding["independent_source_review"]
binding["producer_author_provenance_only"] = binding["author_provenance_only"]
binding["isolated_source_version"] = ref(SOURCE_PROOF)
binding["independent_source_review"] = ref(SOURCE_REVIEW)
binding["compatible_source_proof_owner_provenance_only"] = proof["owner"]
binding["author_provenance_only"] = {
    "prepared_under_current_owner": owner, "actual_child_thread": CHILD, "execution_binding": False}
binding["intended_resource_metadata_only"]["runtime_root"] = REMOTE_ROOT
binding["native_packet_independent_review"] = {
    "path": "pipeline/diagnostic_bundles/tick_c7451cf1/hvd_native_operational_independent_review.json",
    "sha256": "692db1ddc09191f9480ba5fca20a97a72bc6284274693a449d5b8c133f9a394f"}
binding["draft_execution_disabled"] = False
binding["scope"] = (
    "Separately saved d20 child07ef current-owner metadata for the unchanged frozen HVD nine source bytes. "
    "Original e38/6bc binding, proof owners and NULL mother packet remain historical producers. "
    "This is not an execution manifest, lease, request, admission or result.")
save("source_version_binding.json", binding)

runtime = (NATIVE / "native_runtime.py").read_text(encoding="utf-8")
runtime = replace_once(runtime, "DRAFT_EXECUTION_DISABLED = True", "DRAFT_EXECUTION_DISABLED = False")
runtime = replace_once(runtime, "CANDIDATE_COMMIT = '" + LEGACY + "'", "CANDIDATE_COMMIT = '" + SOURCE + "'")
runtime = replace_once(runtime, "SOURCE_PARENT_COMMIT = '" + LEGACY_PARENT + "'", "SOURCE_PARENT_COMMIT = '" + PARENT + "'")
runtime = replace_once(runtime, "RUNTIME_EXPECTED_COMMIT = '" + LEGACY_PARENT + "'", "RUNTIME_EXPECTED_COMMIT = '" + PARENT + "'")
runtime = replace_once(runtime, "assert ROOT == Path('/data/songcl/Project/Cluster_project/Cluster_nec_20261104')",
                       "assert ROOT == Path('" + REMOTE_ROOT + "')")
compile(runtime, "native_runtime.py", "exec")
save("native_runtime.py", runtime)

remote = (OPS / "remote_ops.py").read_text(encoding="utf-8")
remote = replace_once(remote, "COMMIT='" + LEGACY + "'", "COMMIT='" + SOURCE + "'")
remote = replace_once(remote, "ROOT=Path('/data/songcl/Project/Cluster_project/Cluster_nec_20261104')",
                      "ROOT=Path('" + REMOTE_ROOT + "')")
compile(remote, "remote_ops.py", "exec")
save("remote_ops.py", remote)
launcher = (OPS / "run_hvd_operation.py").read_text(encoding="utf-8")
launcher = replace_once(launcher, "EXPECTED_RUNTIME='" + LEGACY_PARENT + "'", "EXPECTED_RUNTIME='" + PARENT + "'")
launcher = replace_once(launcher, "code_commit='" + LEGACY + "'", "code_commit='" + SOURCE + "'")
compile(launcher, "run_hvd_operation.py", "exec")
save("run_hvd_operation.py", launcher)

template = copy.deepcopy(legacy_template)
template.update(root=REMOTE_ROOT, code_commit=SOURCE, source_version_commit=SOURCE,
                source_parent_commit=PARENT, base_reference_commit=PARENT, future_version_parent=PARENT,
                runtime_expected_commit=PARENT, draft_execution_disabled=False,
                source_version_binding_sha256=sha(HERE / "source_version_binding.json"))
template["assets"]["config_path"] = REMOTE_ROOT + "/configs/Quard/ctf_hcg_csort/" + template["name"] + ".yaml"
for name in ("native_runtime.py", "source_version_binding.json"):
    template["diagnostic_files"][name] = sha(HERE / name)
assert all(template[key] is None for key in active_fields)
save("manifest_template.json", template)
current = {
    "schema_version": 1, "project": "cluster_project", "candidate_id": CID, "experiment_id": "M230-HVD",
    "owner": owner, "actual_author_child_thread_id": CHILD, "source_commit": SOURCE,
    "source_parent_commit": PARENT, "runtime_code_commit": PARENT, "runtime_root": REMOTE_ROOT,
    "legacy_source_commit": LEGACY, "legacy_source_parent_commit": LEGACY_PARENT,
    "SERVERS_sha256": SERVERS_SHA, "physical_gpu": 0,
    "gpu_uuid": "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c", "allowed_gpus": [0],
    "resource_authorization": legacy_template["resource_authorization"],
    "resource_memory_policy": legacy_template["resource_memory_policy"],
    "source_proof": ref(SOURCE_PROOF), "source_review": ref(SOURCE_REVIEW),
    "frozen_packages": frozen_refs, "producer_files": producer_refs,
    "producer_hash_audit": ref(HERE / "producer_hash_audit.json"),
    "activation_files": {name: sha(HERE / name) for name in (
        "native_runtime.py", "source_version_binding.json", "manifest_template.json",
        "remote_ops.py", "run_hvd_operation.py")},
    "no_duplicate_worker_or_model_or_YAML": True, "original_NULLs_not_filled": True,
    "execution_material_created": False, "native": "NOT_RUN", "resources": "NOT_RUN",
    "scientific_admission": False, "requires_independently_reviewed_external_candidate_anchors": True,
    "producer_protocol_text_is_preserved_historical_description": True,
    "scope": "Current-owner source/runtime/root/resource thin binding only; no model or protocol revision.",
}
save("current_binding.json", current)

adapter = (OPS / "adapter.py").read_text(encoding="utf-8")
for old, new in (
    ("COMMIT = '" + LEGACY + "'", "COMMIT = '" + SOURCE + "'"),
    ("EXPECTED_RUNTIME_COMMIT = '" + LEGACY_PARENT + "'", "EXPECTED_RUNTIME_COMMIT = '" + PARENT + "'"),
    ("EXPECTED_PRIMARY_COMMIT = '" + LEGACY_PARENT + "'", "EXPECTED_PRIMARY_COMMIT = '" + PARENT + "'"),
    ("DRAFT_EXECUTION_DISABLED = True", "DRAFT_EXECUTION_DISABLED = False"),
    ("SERVERS_POLICY_SHA256 = 'f046762ec6e87321a70d2595cf35e52fa6e57b3f4aa585ab1fedbf624ae7ef6c'",
     "SERVERS_POLICY_SHA256 = '" + SERVERS_SHA + "'"),
    ("REMOTE_ROOT = '/data/songcl/Project/Cluster_project/Cluster_nec_20261104'",
     "REMOTE_ROOT = '" + REMOTE_ROOT + "'"),
):
    adapter = replace_once(adapter, old, new)
adapter = replace_once(adapter, "PAIRS = (", "LEGACY_SOURCE_COMMIT = '" + LEGACY + "'\nCURRENT_BINDING_SHA256 = '" + sha(HERE / "current_binding.json") + "'\nPAIRS = (")
new_methods = '''
    def _activation_details(self):
        path=self.origin/'current_binding.json'
        require(sha(path)==CURRENT_BINDING_SHA256,'Current thin binding changed')
        b=read(path)
        require(b['project']=='cluster_project' and b['candidate_id']==CANDIDATE
            and b['experiment_id']=='M230-HVD' and b['source_commit']==COMMIT
            and b['source_parent_commit']==EXPECTED_PRIMARY_COMMIT
            and b['runtime_code_commit']==EXPECTED_RUNTIME_COMMIT
            and b['runtime_root']==REMOTE_ROOT and b['SERVERS_sha256']==SERVERS_POLICY_SHA256,
            'Current source/runtime/root binding mismatch')
        require(b['physical_gpu']==0 and b['allowed_gpus']==[0] and b['gpu_uuid']==GPU_UUIDS[0]
            and b['resource_authorization']==RESOURCE_AUTHORIZATION
            and b['resource_memory_policy']==RESOURCE_MEMORY_POLICY,'Current resource binding mismatch')
        require(b['execution_material_created'] is False and b['original_NULLs_not_filled'] is True,
            'Thin metadata is not an execution artifact or a NULL backfill')
        require(set(b['owner'])=={'token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256'},
            'Thin owner schema changed')
        for entry in b['producer_files']+[b['source_proof'],b['source_review'],b['producer_hash_audit']]:
            path=(self.root/entry['path']).resolve()
            require(path.is_relative_to(self.root) and sha(path)==entry['sha256'],'Thin producer proof changed')
        for entry in b['frozen_packages']:
            path=(self.root/entry['path']).resolve()
            require(path.is_relative_to(self.root) and sha(path)==entry['sha256'],'Original FROZEN changed')
            for name,expected in read(path)['files'].items():
                item=(path.parent/name).resolve()
                require(item.is_relative_to(path.parent.resolve()) and sha(item)==expected,'Original frozen file changed')
        require(set(b['activation_files'])=={'native_runtime.py','source_version_binding.json',
            'manifest_template.json','remote_ops.py','run_hvd_operation.py'},'Thin file set changed')
        for name,expected in b['activation_files'].items():
            path=(self.origin/name).resolve()
            require(path.is_relative_to(self.origin) and sha(path)==expected,'Thin activation file changed: '+name)
        proof=read(self.root/b['source_proof']['path']); audit=read(self.root/b['source_review']['path'])
        require(proof['source_commit']==COMMIT and proof['parent_commit']==EXPECTED_PRIMARY_COMMIT
            and audit['passed'] is True and audit['source_commit']==COMMIT
            and audit['parent_commit']==EXPECTED_PRIMARY_COMMIT,'Compatible source proof mismatch')
        version=read(self.origin/'source_version_binding.json')
        require(version['candidate_id']==CANDIDATE and version['code_commit']==version['source_commit']==COMMIT
            and version['parent_commit']==EXPECTED_PRIMARY_COMMIT
            and version['runtime_expected_commit']==EXPECTED_RUNTIME_COMMIT
            and version['source_files']==proof['source_files_exact9'] and len(version['source_files'])==9,
            'Current source-version binding mismatch')
        return b

    def _diagnostic_path(self,name,manifest):
        require(name in manifest['diagnostic_files'],'Unknown diagnostic payload file')
        base=self.origin if name in ('native_runtime.py','source_version_binding.json') else self.frozen
        path=(base/name).resolve()
        require(path.is_relative_to(base.resolve()) and sha(path)==manifest['diagnostic_files'][name],
            'Current/frozen diagnostic payload changed')
        return path
'''
adapter = replace_once(adapter, "    def _frozen_details(self):", new_methods + "\n    def _frozen_details(self):")
adapter = replace_method(adapter, "_frozen_details", '''
    def _frozen_details(self):
        require(isinstance(COMMIT,str) and re.fullmatch(r'[0-9a-f]{40}',COMMIT) is not None,'Exact compatible source commit is required')
        require(sha(self.frozen/'preparation.json')==PREPARATION_SHA,'Frozen preparation changed')
        p=read(self.frozen/'preparation.json')
        require(sha(self.frozen/'manifest_template.json')==TEMPLATE_SHA,'Frozen template changed')
        require(p['source_commit']==LEGACY_SOURCE_COMMIT and p['candidate_id']==CANDIDATE,'Original frozen producer mismatch')
        for name,expected in p['prepared_file_hashes'].items():
            path=(self.frozen/name).resolve()
            require(path.is_relative_to(self.frozen) and sha(path)==expected,'Frozen file changed: '+name)
        b=self._activation_details()
        original=read(self.frozen/'manifest_template.json')
        expected=copy.deepcopy(original)
        expected.update(root=REMOTE_ROOT,code_commit=COMMIT,source_version_commit=COMMIT,
            source_parent_commit=EXPECTED_PRIMARY_COMMIT,base_reference_commit=EXPECTED_PRIMARY_COMMIT,
            future_version_parent=EXPECTED_PRIMARY_COMMIT,runtime_expected_commit=EXPECTED_RUNTIME_COMMIT,
            draft_execution_disabled=False,
            source_version_binding_sha256=b['activation_files']['source_version_binding.json'])
        expected['assets']['config_path']=REMOTE_ROOT+'/configs/Quard/ctf_hcg_csort/'+expected['name']+'.yaml'
        for name in ('native_runtime.py','source_version_binding.json'):
            expected['diagnostic_files'][name]=b['activation_files'][name]
        template=read(self.origin/'manifest_template.json')
        require(template==expected,'Current template exceeds the reviewed identity/path/hash projection')
        require(all(template[k] is None for k in ('current_token','stage','tick_generated_at','deadline_at',
            'physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')),
            'Effective template must not contain execution bindings')
        version=read(self.origin/'source_version_binding.json')
        require(version['candidate_source_hashes']==original['candidate_source_hashes']
            and version['candidate_config_sha256']==original['candidate_config_sha256']
            and version['original_source_preparation_sha256']==original['source_preparation_sha256'],
            'Unchanged source/preparation identity mismatch')
        return p,template
''')
adapter = replace_once(adapter, "        self._frozen_details(); self._release_details()",
    "        self._frozen_details(); self._release_details()\n"
    "        capability=self._activation_details()\n"
    "        require({k:owner[k] for k in capability['owner']}==capability['owner'],"
    "'Thin capability belongs to a different owner/context/deadline')")
adapter = replace_once(adapter,
    "            path=(self.frozen/name).resolve(); require(path.is_relative_to(self.frozen),'Payload path outside frozen directory')",
    "            path=self._diagnostic_path(name,manifest)")
adapter = adapter.replace("exact expected current NEC6bc checkout", "exact expected current MIC07ef checkout")
adapter = adapter.replace("actual primary HEAD must be current NEC6bc", "actual primary HEAD must be current MIC07ef")
compile(adapter, "adapter.py", "exec")
save("adapter.py", adapter)

release = copy.deepcopy(read(OPS / "release_template.json"))
release.update(purpose="Static current-owner thin HVD adapter release candidate; external independently reviewed anchors remain required; no execution grant",
               code_commit=SOURCE, manifest_template_sha256=sha(HERE / "manifest_template.json"),
               source_version_binding_sha256=sha(HERE / "source_version_binding.json"),
               source_hashes={name: sha(HERE / name) for name in ("adapter.py", "remote_ops.py")},
               current_binding=ref(HERE / "current_binding.json"), draft_execution_disabled=False,
               operational_ready=False, independent_review="PENDING_EXTERNAL_ROOT_ANCHOR")
release["conditional_parent_promotion"]["expected_primary_HEAD"] = PARENT
release["resource_policy"]["SERVERS_sha256"] = SERVERS_SHA
release["runtime_binding"] = {"expected_runtime_code_commit": PARENT, "remote_code_root": REMOTE_ROOT}
release["selection_scope"] = "Current GPU0-only sharing grant; minimum free20000MiB, max1, three project locks, canonical local-busy and no-replay guards preserved."
save("release_template.json", release)
save("adapter_release.json", release)
save("README.md", (
    "Thin current-owner HVD operational adaptation, source d20 child07ef, runtime MIC07ef.\n"
    "Original c745 frozen worker, source8 and YAML are referenced in place, never duplicated or rewritten.\n"
    "Only current runtime/source-version metadata and adapter transport identity/path projection are new.\n"
    "The manifest template retains the frozen scientific protocol text as historical producer description;\n"
    "the new explicit status fields describe this capability. Its ten execution fields are still NULL.\n"
    "Static release presence is not approval: actual root candidate preparation/release anchors require independent review.\n"
    "No manifest, lease, request, stage, GPU/model execution or scientific admission is created here.\n"
    "Old packets/NULLs remain unchanged; root must reconcile canonical slot, verify memory/three locks,\n"
    "and retain original1020sec run margin before prepare/stage/each original request.\n"))
core_names = (
    "build_current_activation.py", "local_software_check.py", "producer_hash_audit.json",
    "source_version_binding.json", "native_runtime.py", "remote_ops.py", "run_hvd_operation.py",
    "manifest_template.json", "current_binding.json", "adapter.py", "release_template.json",
    "adapter_release.json", "README.md")
preparation = {
    "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
    "candidate_id": CID, "experiment_id": "M230-HVD", "code_commit": SOURCE, "source_commit": SOURCE,
    "source_parent_commit": PARENT, "expected_runtime_code_commit": PARENT, "runtime_root": REMOTE_ROOT,
    "status": "THIN_CURRENT_OWNER_ADAPTATION_PREPARED_PENDING_INDEPENDENT_REVIEW_NOT_EXECUTED",
    "owner_provenance_only": owner, "actual_author_child_thread_id": CHILD,
    "native_preparation": ref(NATIVE / "preparation.json"), "native_worker": ref(NATIVE / "worker.py"),
    "original_frozen_packages": frozen_refs, "current_binding": ref(HERE / "current_binding.json"),
    "source_proof": ref(SOURCE_PROOF), "source_review": ref(SOURCE_REVIEW),
    "prepared_file_hashes": {name: sha(HERE / name) for name in core_names},
    "software_validation_output": (HERE / "software_validation.json").relative_to(ROOT).as_posix(),
    "conditional_parent_promotion": release["conditional_parent_promotion"],
    "resource_authorization": legacy_template["resource_authorization"],
    "resource_memory_policy": legacy_template["resource_memory_policy"],
    "original_NULLs_not_filled": True, "no_duplicate_worker_model_YAML": True,
    "operational_ready": False, "independent_review": "PENDING_EXTERNAL_NOT_SELF_SIGNED",
    "active_manifest_binding_lease_request_stage_created": False,
    "native": "NOT_RUN", "resources": "NOT_RUN", "scientific_admission": False,
}
save("preparation.json", preparation)
guard()
print(json.dumps({"status": preparation["status"], "preparation": ref(HERE / "preparation.json"),
                  "release": ref(HERE / "adapter_release.json"), "current_binding": ref(HERE / "current_binding.json"),
                  "original_frozen_files_verified": frozen_count, "native": "NOT_RUN", "resources": "NOT_RUN"}))
