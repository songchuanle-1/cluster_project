"""Thin current-owner activation copy only. Root creates release after peer review."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json
import os

ROOT=Path("D:/project/cluster_project")
HERE=Path(__file__).resolve().parent
MOTHER=HERE.parent/"nsd_native_prepare"
N=HERE/"native"
OWNER_KEYS=("token","thread_id","generated_at","deadline_at","context_sha256","pending_sha256")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def ref(p):return {"path":Path(p).relative_to(ROOT).as_posix(),"sha256":sha(p)}
def guard():
    assert os.environ.get("CODEX_THREAD_ID")=="01a1b166-dcbf-7d01-b0cb-c85fff644605"
    o=read(ROOT/"pipeline/headless/.foreground.lockdir/owner.json")
    assert o["token"]=="c706ca805df642f3b7d41f51206ed921" and o["thread_id"]=="01a159c5-29ab-7a22-ba7f-e79174757253"
    assert datetime.now(timezone.utc)<datetime.fromisoformat(o["deadline_at"])
    assert sha(ROOT/"pipeline/headless/.tick_context.json")==o["context_sha256"]
    assert sha(ROOT/"pipeline/headless/.tick_context_state.next.json")==o["pending_sha256"]
    return {k:o[k] for k in OWNER_KEYS}
def save(name,value):
    guard();p=HERE/name;assert p.resolve().is_relative_to(HERE.resolve());p.parent.mkdir(parents=True,exist_ok=True)
    raw=value if isinstance(value,bytes) else (value.encode() if isinstance(value,str) else (json.dumps(value,indent=2)+"\n").encode())
    with p.open("xb") as s:s.write(raw)
def once(text,old,new):
    assert text.count(old)==1,old[:100]
    return text.replace(old,new,1)


def main():
    owner=guard();mf=read(MOTHER/"FROZEN.json")
    assert sha(MOTHER/"FROZEN.json")=="4ea59d171f4f4319f5f2b78c525aa70bda822cce02d50cf9acec3753d1815186"
    assert all(sha(MOTHER/name)==digest for name,digest in mf["files"].items())
    original=read(MOTHER/"native/preparation.json")
    for name in original["prepared_file_hashes"]:
        if name not in ("native_runtime.py","source_version_binding.json","manifest_template.json"):
            save("native/"+name,(MOTHER/"native"/name).read_bytes())
    runtime=(MOTHER/"native/native_runtime.py").read_text()
    runtime=once(runtime,"DRAFT_EXECUTION_DISABLED = True","DRAFT_EXECUTION_DISABLED = False")
    save("native/native_runtime.py",runtime)
    version=read(MOTHER/"native/source_version_binding.json")
    version.update(draft_execution_disabled=False,producer_source_version_binding=ref(MOTHER/"native/source_version_binding.json"),
                   author_provenance_only={"owner":owner,"actual_child_thread":os.environ["CODEX_THREAD_ID"],"execution_binding":False})
    save("native/source_version_binding.json",version)
    template=read(MOTHER/"native/manifest_template.json")
    template.update(draft_execution_disabled=False,source_version_binding_sha256=sha(N/"source_version_binding.json"))
    for name in ("native_runtime.py","source_version_binding.json"):template["diagnostic_files"][name]=sha(N/name)
    save("native/manifest_template.json",template)
    p=copy.deepcopy(original)
    p.update(recorded_at=datetime.now(timezone.utc).isoformat(),draft_execution_disabled=False,owner_provenance_only=owner,
             producer_native_preparation=ref(MOTHER/"native/preparation.json"),
             source_version_binding=ref(N/"source_version_binding.json"),manifest_template=ref(N/"manifest_template.json"),
             worker=ref(N/"worker.py"),runtime=ref(N/"native_runtime.py"))
    p["prepared_file_hashes"]={name:sha(N/name) for name in p["prepared_file_hashes"]}
    save("native/preparation.json",p)
    for name in ("remote_ops.py","run_nsd_operation.py"):save(name,(MOTHER/"operational"/name).read_bytes())
    activation_names=["native/"+name for name in p["prepared_file_hashes"]]+["native/preparation.json","remote_ops.py","run_nsd_operation.py"]
    binding=dict(schema_version=1,project="cluster_project",candidate_id=p["candidate_id"],experiment_id="M232-NSD",
        owner=owner,source_commit=p["source_commit"],source_parent_commit=p["source_parent_commit"],
        runtime_code_commit=p["runtime_expected_commit"],runtime_root=template["root"],
        SERVERS_sha256=sha(ROOT/"SERVERS.yaml"),physical_gpu=0,gpu_uuid="GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c",
        allowed_gpus=[0],resource_authorization=template["resource_authorization"],resource_memory_policy=template["resource_memory_policy"],
        mother_FROZEN=ref(MOTHER/"FROZEN.json"),mother_native_preparation=ref(MOTHER/"native/preparation.json"),
        source_proof=p["source_proof"],source_review=p["source_review"],
        diagnostic_only_conda_override=read(MOTHER/"operational/preparation.json")["diagnostic_only_conda_override"],
        activation_files={name:sha(HERE/name) for name in activation_names},
        draft_mother_ten_NULLs_and_DRAFT_True_unchanged=True,execution_material_created=False,
        native="NOT_RUN",resources="NOT_RUN",scientific_admission=False)
    save("current_binding.json",binding)
    adapter=(MOTHER/"operational/adapter.py").read_text()
    adapter=once(adapter,"FROZEN = PROJECT_ROOT/'"+(MOTHER/"native").relative_to(ROOT).as_posix()+"'",
                 "FROZEN = Path(__file__).resolve().parent/'native'")
    adapter=once(adapter,"PREPARATION_SHA = '"+sha(MOTHER/"native/preparation.json")+"'","PREPARATION_SHA = '"+sha(N/"preparation.json")+"'")
    adapter=once(adapter,"TEMPLATE_SHA = '"+sha(MOTHER/"native/manifest_template.json")+"'","TEMPLATE_SHA = '"+sha(N/"manifest_template.json")+"'")
    adapter=once(adapter,"DRAFT_EXECUTION_DISABLED = True","DRAFT_EXECUTION_DISABLED = False")
    adapter=once(adapter,"PAIRS = (","CURRENT_BINDING_SHA256 = '"+sha(HERE/"current_binding.json")+"'\nPAIRS = (")
    method="""
    def _activation_details(self):
        path=self.origin/'current_binding.json'
        require(sha(path)==CURRENT_BINDING_SHA256,'Current NSD activation binding changed')
        b=read(path)
        require(b['project']=='cluster_project' and b['candidate_id']==CANDIDATE
            and b['experiment_id']=='M232-NSD' and b['source_commit']==COMMIT
            and b['source_parent_commit']==EXPECTED_PRIMARY_COMMIT
            and b['runtime_code_commit']==EXPECTED_RUNTIME_COMMIT and b['runtime_root']==REMOTE_ROOT
            and b['SERVERS_sha256']==SERVERS_POLICY_SHA256,'Current NSD source/runtime/root policy mismatch')
        require(b['physical_gpu']==0 and b['allowed_gpus']==[0] and b['gpu_uuid']==GPU_UUIDS[0]
            and b['resource_authorization']==RESOURCE_AUTHORIZATION
            and b['resource_memory_policy']==RESOURCE_MEMORY_POLICY,'Current NSD resource policy mismatch')
        require(b['diagnostic_only_conda_override']['source']==DIAGNOSTIC_CONDA_SOURCE
            and b['diagnostic_only_conda_override']['sha256']==DIAGNOSTIC_CONDA_SOURCE_SHA256,
            'Current NSD immutable diagnostic-only base mismatch')
        require(b['execution_material_created'] is False and b['draft_mother_ten_NULLs_and_DRAFT_True_unchanged'] is True,
            'NSD activation is metadata only')
        for key in ('mother_FROZEN','mother_native_preparation','source_proof','source_review'):
            entry=b[key];item=(self.root/entry['path']).resolve()
            require(item.is_relative_to(self.root) and sha(item)==entry['sha256'],'NSD producer/source proof changed')
        frozen_path=self.root/b['mother_FROZEN']['path']
        for name,expected in read(frozen_path)['files'].items():
            item=(frozen_path.parent/name).resolve()
            require(item.is_relative_to(frozen_path.parent.resolve()) and sha(item)==expected,'NSD frozen mother changed')
        for name,expected in b['activation_files'].items():
            item=(self.origin/name).resolve()
            require(item.is_relative_to(self.origin) and sha(item)==expected,'NSD activation payload changed')
        require(set(b['owner'])=={'token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256'},
            'NSD current owner schema changed')
        return b

"""
    adapter=once(adapter,"    def _frozen_details(self):",method+"    def _frozen_details(self):")
    adapter=once(adapter,"        return p,read(self.frozen/'manifest_template.json')",
        "        self._activation_details()\n        return p,read(self.frozen/'manifest_template.json')")
    adapter=once(adapter,"        owner=read(self.root/'pipeline/headless/.foreground.lockdir/owner.json')",
        "        owner=read(self.root/'pipeline/headless/.foreground.lockdir/owner.json')\n"
        "        activation=self._activation_details()\n"
        "        require({k:owner[k] for k in ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')}==activation['owner'],'NSD activation belongs to a different owner')")
    compile(adapter,"NSD-current-adapter","exec");save("adapter.py",adapter)
    release=read(MOTHER/"operational/release_template.json")
    release.update(purpose="Current-owner NSD activation release template; root independent review/anchors required.",
        draft_execution_disabled=False,native_preparation_sha256=sha(N/"preparation.json"),
        manifest_template_sha256=sha(N/"manifest_template.json"),
        source_version_binding_sha256=sha(N/"source_version_binding.json"),
        source_hashes={name:sha(HERE/name) for name in ("adapter.py","remote_ops.py")},
        current_binding=ref(HERE/"current_binding.json"),independent_review="PENDING_EXTERNAL_ROOT_RELEASE")
    save("release_template.json",release)
    save("README.md","Separate current-owner NSD activation metadata. Mother untouched/DRAFT=True/ten NULLs. Here DRAFT=False with ten NULLs, no root release, binding, manifest, lease, request, stage or actual execution. Exact same worker/source/protocol/resource function. Diagnostic-only immutable original conda base is explicit; old expired production shim and SERVERS untouched. Root must review/anchor native preparation and execution_adapter before prepare/stage/original four runs; original1020second margin remains.\n")
    prepared_names=["build_activation.py","local_software_check.py","current_binding.json","adapter.py",
                    "release_template.json","README.md"]+activation_names
    save("preparation.json",dict(schema_version=1,status="CURRENT_OWNER_NSD_ACTIVATION_PREPARED_PENDING_EXTERNAL_REVIEW_NOT_NATIVE",
        recorded_at=datetime.now(timezone.utc).isoformat(),candidate_id=p["candidate_id"],experiment_id="M232-NSD",
        code_commit=p["source_commit"],source_commit=p["source_commit"],source_parent_commit=p["source_parent_commit"],
        expected_runtime_code_commit=p["runtime_expected_commit"],owner_provenance_only=owner,
        mother_FROZEN=ref(MOTHER/"FROZEN.json"),native_preparation=ref(N/"preparation.json"),
        native_manifest_template=ref(N/"manifest_template.json"),current_binding=ref(HERE/"current_binding.json"),
        release_template=ref(HERE/"release_template.json"),root_launcher=ref(HERE/"run_nsd_operation.py"),
        diagnostic_only_conda_override=binding["diagnostic_only_conda_override"],
        prepared_file_hashes={name:sha(HERE/name) for name in prepared_names},
        operational_ready=False,adapter_release_created=False,execution_material_created=False,
        independent_review="PENDING_EXTERNAL",native="NOT_RUN",resources="NOT_RUN",scientific_admission=False))
    print(json.dumps({"preparation":ref(HERE/"preparation.json"),"native_preparation":ref(N/"preparation.json"),
                      "template":ref(N/"manifest_template.json"),"adapter_release_created":False}))


if __name__=="__main__":main()
