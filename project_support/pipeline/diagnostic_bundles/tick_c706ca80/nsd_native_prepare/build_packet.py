"""Author an execution-disabled original NSD diagnostic packet; local writes only."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import copy
import hashlib
import json
import os
import subprocess

ROOT=Path("D:/project/cluster_project")
HERE=Path(__file__).resolve().parent
NATIVE=HERE/"native"
OPS=HERE/"operational"
OLD=ROOT/"pipeline/diagnostic_bundles/tick_2e51495f"
PRODUCER=OLD/"psc_native_prepare/native"
OLD_OPS=OLD/"psc_operational_prepare"
SOURCE="f6257de79148581334ee495e6e2d60ccb525457c"
PARENT="0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
REMOTE_ROOT="/data/songcl/Project/Cluster_project/Cluster_psc_20261106"
CID="hierarchy-native-spatial-dirichlet-composition"
SERVERS_SHA="1f1ba94e90c6f44e2e9cb0e6f1e746568e38cc1e92f398ee49efc5e8c40232bf"
SOURCE_PROOF=HERE.parent/"nsd_compatible_source/compatible_source_version.json"
SOURCE_REVIEW=HERE.parent/"nsd_compatible_source_independent_review.json"
MOTHER=OLD/"reserve_candidate"
TOKEN="c706ca805df642f3b7d41f51206ed921"
THREAD="01a159c5-29ab-7a22-ba7f-e79174757253"
TEN_NULL=("current_token","stage","tick_generated_at","deadline_at","physical_gpu","gpu_uuid",
          "allowed_gpus","context_sha256","pending_sha256","runtime_code_commit")
BASE="/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh"
BASE_SHA="6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_bytes())
def ref(path):return {"path":Path(path).relative_to(ROOT).as_posix(),"sha256":sha(path)}
def guard():
    assert HERE==ROOT/"pipeline/diagnostic_bundles/tick_c706ca80/nsd_native_prepare"
    assert os.environ.get("CODEX_THREAD_ID")=="01a1b166-dcbf-7d01-b0cb-c85fff644605"!=THREAD
    o=read(ROOT/"pipeline/headless/.foreground.lockdir/owner.json")
    assert o["token"]==TOKEN and o["thread_id"]==THREAD
    assert datetime.now(timezone.utc)<datetime.fromisoformat(o["deadline_at"])
    for name,key in ((".tick_context.json","context_sha256"),(".tick_context_state.next.json","pending_sha256")):
        assert sha(ROOT/"pipeline/headless"/name)==o[key]
    assert sha(ROOT/"SERVERS.yaml")==SERVERS_SHA
    return {k:o[k] for k in ("token","thread_id","generated_at","deadline_at","context_sha256","pending_sha256")}
def save(path,value):
    guard();path=Path(path);assert path.resolve().is_relative_to(HERE.resolve())
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=value if isinstance(value,bytes) else (value.encode() if isinstance(value,str) else (json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode())
    with path.open("xb") as stream:stream.write(raw)
def once(text,old,new):
    assert text.count(old)==1,old[:100]
    return text.replace(old,new,1)
def function(text,name):
    n=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
    return ast.get_source_segment(text,n)
def git(*args):
    return subprocess.check_output(["C:/Program Files (x86)/Git/cmd/git.exe","--no-optional-locks","-c","core.fsmonitor=false","-C",str(ROOT/"Cluster"),*args],
        env=dict(os.environ,GIT_OPTIONAL_LOCKS="0",GIT_TERMINAL_PROMPT="0"))
def port(text):
    return text.replace("position_feature_scatter","spatial_dirichlet").replace("position_scatter","spatial_dirichlet").replace("PSC","NSD").replace("psc","nsd")


def main():
    owner=guard();proof=read(SOURCE_PROOF)
    assert proof["source_commit"]==SOURCE and proof["parent_commit"]==PARENT
    assert sha(SOURCE_REVIEW)=="32609b8720b466713911a3d93650272f5ba4e376218253ef5dd261e5992758d2"
    assert read(SOURCE_REVIEW)["passed"] is True
    assert sha(PRODUCER/"worker.py")=="530a5230021fad8d880c37a34c18973b4c556e7dc1536b6c4faaffdd6d6f93d8"
    original=(PRODUCER/"worker.py").read_text(encoding="utf8")
    worker=port(original)
    start=worker.index("    if candidate:\n        core=att.spatial_dirichlet")
    end=worker.index("    original_csort=",start)
    worker=worker[:start]+(HERE/"nsd_observers.py.txt").read_text(encoding="utf8")+"\n"+worker[end:]
    helper=(HERE/"chain_observation.py.txt").read_text(encoding="utf8")
    worker=once(worker,"def setup(target, mode, result):",helper+"\n\ndef setup(target, mode, result):")
    start=worker.index("    for record in exchange_calls:")
    end=worker.index("    for record in readbacks:",start)
    worker=worker[:start]+"""    for record in exchange_calls:
        count=record['actual_supported_scene_count']
        assert record['actual_true_fine_paths']>0 and count>0
        assert all(record[key]==3*count for key in ('actual_chain_energy_calls','actual_chain_builder_calls','actual_analysis_calls','actual_synthesis_calls','actual_final_index_copy_calls'))
        for level in range(3):
            for key in ('native_normalized_level'+str(level)+'_gradients','native_output_level'+str(level)+'_gradients'):
                assert record.get(key) and all(g['finite'] for g in record[key])
        flags=record.pop('_internal_gradient_flags');record['actual_internal_backward_callbacks']=len(flags)
        record['all_observed_internal_gradients_finite']=bool(torch.stack(flags).all()) if flags else None
        if flags:assert record['all_observed_internal_gradients_finite']
        record['internal_gradient_scope']='Finite observed flags only; no per-branch/parameter nonzero or completeness gate; whole-core aggregate controls trainability.'
"""+worker[end:]
    start=worker.index("        intended_path_observed=")
    end=worker.index("\n        new_operator_parameters=",start)
    worker=worker[:start]+"        intended_path_observed=(len(exchange_calls)==2 and all(v['actual_production_NSDirichlet_path_observed'] and v['actual_true_fine_paths']>0 for v in exchange_calls)) if candidate else len(calls)==6,"+worker[end:]
    assert function(worker,"resources")==function(original,"resources")
    compile(worker,"NSD-worker","exec");save(NATIVE/"worker.py",worker)
    runtime=port((PRODUCER/"native_runtime.py").read_text(encoding="utf8"))
    runtime=runtime.replace("M231-NSD","M232-NSD").replace("hierarchy-native-position-feature-cross-scatter-composition",CID)
    runtime=runtime.replace(PARENT,SOURCE).replace("d20eb221eff6584b67d4e9b5673559d0e1cb735b",PARENT)
    runtime=runtime.replace("/data/songcl/Project/Cluster_project/Cluster_hvd_20261106",REMOTE_ROOT)
    runtime=runtime.replace("183bd9e44f1cfea19421337f71934fa86e5244efe59f76c96e0d8ac6f8896086",sha(MOTHER/"source_preparation.json"))
    assert "DRAFT_EXECUTION_DISABLED = True" in runtime
    compile(runtime,"NSD-runtime","exec");save(NATIVE/"native_runtime.py",runtime)
    for path,digest in proof["source_files_exact9"].items():
        raw=git("show",SOURCE+":"+path);assert hashlib.sha256(raw).hexdigest()==digest
        save(NATIVE/("candidate.yaml" if path.endswith(".yaml") else "candidate_model/"+Path(path).name),raw)
    hashes={Path(n).name:d for n,d in proof["source_files_exact9"].items() if n.endswith(".py")}
    version=dict(schema_version=1,candidate_id=CID,experiment_id="M232-NSD",code_commit=SOURCE,source_commit=SOURCE,
        parent_commit=PARENT,runtime_expected_commit=PARENT,candidate_source_hashes=hashes,
        candidate_config_sha256=sha(NATIVE/"candidate.yaml"),source_files=proof["source_files_exact9"],
        original_source_preparation_sha256=sha(MOTHER/"source_preparation.json"),
        source_preparation=ref(MOTHER/"source_preparation.json"),native_protocol=ref(MOTHER/"native_protocol.md"),
        isolated_source_version=ref(SOURCE_PROOF),independent_source_review=ref(SOURCE_REVIEW),
        author_provenance_only={"owner":owner,"actual_child_thread":os.environ["CODEX_THREAD_ID"],"execution_binding":False},
        draft_execution_disabled=True,native_packet_independent_review=None)
    save(NATIVE/"source_version_binding.json",version)
    template=read(PRODUCER/"manifest_template.json")
    template.update(root=REMOTE_ROOT,candidate_id=CID,candidate_name=template["name"]+"_nsd",code_commit=SOURCE,
        experiment_id="M232-NSD",config="configs/Quard/ctf_hcg_csort_nsd/"+template["name"]+"_nsd.yaml",
        candidate_source_hashes=hashes,candidate_config_sha256=sha(NATIVE/"candidate.yaml"),
        source_preparation_sha256=sha(MOTHER/"source_preparation.json"),base_reference_commit=PARENT,
        source_version_commit=SOURCE,source_version_binding_sha256=sha(NATIVE/"source_version_binding.json"),
        source_parent_commit=PARENT,future_version_parent=PARENT,runtime_expected_commit=PARENT,
        protocol="Original NSD protocol: paired natural TRAIN2/common835/native loss; exact native coordinates/support/coordinate-only chains/tie-group means/original-precision squared pair contrasts; three original analysis and synthesis stages, original HCG/raw skips/single-inst path; whole-core aggregate finite weight gradient and weight/module updates; complete original resource function. Optional ties/singleton coverage recorded, no resampling/nonzero/FP32/minimum-effect gate.")
    template["assets"]["config_path"]=REMOTE_ROOT+"/configs/Quard/ctf_hcg_csort/"+template["name"]+".yaml"
    for key in TEN_NULL:template[key]=None
    template["diagnostic_files"]={p.relative_to(NATIVE).as_posix():sha(p) for p in sorted(NATIVE.rglob("*")) if p.is_file()}
    save(NATIVE/"manifest_template.json",template)
    save(NATIVE/"README.md","NSD original source disabled native packet. DRAFT=True and ten execution NULLs. No manifest, lease, binding, request, release or stage. Native/resources/Torch/autograd NOT_RUN.\n")
    native_prep=dict(schema_version=1,recorded_at=datetime.now(timezone.utc).isoformat(),candidate_id=CID,
        experiment_id="M232-NSD",code_commit=SOURCE,source_commit=SOURCE,source_parent_commit=PARENT,
        runtime_expected_commit=PARENT,config=template["config"],source_files=proof["source_files_exact9"],
        source_file_count=9,model_file_count=8,owner_provenance_only=owner,draft_execution_disabled=True,
        manifest_template=ref(NATIVE/"manifest_template.json"),source_version_binding=ref(NATIVE/"source_version_binding.json"),
        source_proof=ref(SOURCE_PROOF),source_review=ref(SOURCE_REVIEW),
        original_source_preparation=ref(MOTHER/"source_preparation.json"),native_protocol=ref(MOTHER/"native_protocol.md"),
        producer_worker=ref(PRODUCER/"worker.py"),worker=ref(NATIVE/"worker.py"),runtime=ref(NATIVE/"native_runtime.py"),
        resource_authorization=template["resource_authorization"],resource_memory_policy=template["resource_memory_policy"],
        original_resource_function_byte_exact=True,ten_active_fields_all_NULL=True,
        native="NOT_RUN",resources="NOT_RUN",Torch_autograd="NOT_RUN",full_forward="NOT_RUN",scientific_admission=False,
        operational_ready=False,independent_review="PENDING_EXTERNAL",prepared_file_hashes={
            p.relative_to(NATIVE).as_posix():sha(p) for p in sorted(NATIVE.rglob("*")) if p.is_file()})
    save(NATIVE/"preparation.json",native_prep)
    adapter=port((OLD_OPS/"adapter.py").read_text(encoding="utf8"))
    adapter=adapter.replace("M231-NSD","M232-NSD").replace("hierarchy-native-position-feature-cross-scatter-composition",CID)
    adapter=adapter.replace("COMMIT = '"+PARENT+"'","COMMIT = '"+SOURCE+"'")
    adapter=adapter.replace("d20eb221eff6584b67d4e9b5673559d0e1cb735b",PARENT)
    adapter=adapter.replace("pipeline/diagnostic_bundles/tick_2e51495f/nsd_native_prepare/native",NATIVE.relative_to(ROOT).as_posix())
    adapter=adapter.replace("757546b94efb9ac3d2490f68351cea78ca6b64e65495c039cb8e91d5015a4b4f",sha(NATIVE/"preparation.json"))
    adapter=adapter.replace("897b26ec1127cbaf4a9799474023e7c41234df045aba5ce67bc9074448a0f49e",sha(NATIVE/"manifest_template.json"))
    adapter=adapter.replace("/data/songcl/Project/Cluster_project/Cluster_hvd_20261106",REMOTE_ROOT)
    adapter=adapter.replace("6a87d428190d77955500b34d58bff0310eecb13c8b233c7b3e4fd7ef253787a7",SERVERS_SHA)
    adapter=adapter.replace("4457a46f9075f61e83340aa0f0af87d5bf4e986c",PARENT)
    adapter=adapter.replace("M227-LFT","M231-PSC").replace("hierarchy-nonlinear-lifting-analysis-synthesis","hierarchy-native-position-feature-cross-scatter-composition")
    adapter=adapter.replace("ctf_hcg_csort_lft","ctf_hcg_csort_psc").replace("LFT","PSC").replace("HVDd20","PSC0ccc")
    adapter=once(adapter,"class SSHTransport:",f"DIAGNOSTIC_CONDA_SOURCE = {BASE!r}\nDIAGNOSTIC_CONDA_SOURCE_SHA256 = {BASE_SHA!r}\n\nclass SSHTransport:")
    adapter=once(adapter,
        "            python = shlex.join(['bash','-lc','source '+shlex.quote(server['conda_source'])",
        "            verification = \"/usr/bin/python3 -I -B -c \" + shlex.quote(\"import hashlib,pathlib;assert hashlib.sha256(pathlib.Path(\"+repr(DIAGNOSTIC_CONDA_SOURCE)+\").read_bytes()).hexdigest()==\"+repr(DIAGNOSTIC_CONDA_SOURCE_SHA256))\n"
        "            python = shlex.join(['bash','-lc',verification+' && source '+shlex.quote(DIAGNOSTIC_CONDA_SOURCE)")
    compile(adapter,"NSD-adapter","exec");save(OPS/"adapter.py",adapter)
    remote=port((OLD_OPS/"remote_ops.py").read_text(encoding="utf8"))
    remote=remote.replace("COMMIT='"+PARENT+"'","COMMIT='"+SOURCE+"'").replace("/data/songcl/Project/Cluster_project/Cluster_hvd_20261106",REMOTE_ROOT)
    compile(remote,"NSD-remote","exec");save(OPS/"remote_ops.py",remote)
    launcher=port((OLD_OPS/"run_psc_operation.py").read_text(encoding="utf8"))
    launcher=launcher.replace("d20eb221eff6584b67d4e9b5673559d0e1cb735b",PARENT)
    launcher=launcher.replace("code_commit='"+PARENT+"'","code_commit='"+SOURCE+"'").replace("hierarchy-native-position-feature-cross-scatter-composition",CID)
    compile(launcher,"NSD-launcher","exec");save(OPS/"run_nsd_operation.py",launcher)
    release=read(OLD_OPS/"release_template.json")
    release.update(purpose="Disabled original NSD diagnostic software catalogue; no execution release.",
        candidate_id=CID,experiment_id="M232-NSD",code_commit=SOURCE,
        native_preparation_sha256=sha(NATIVE/"preparation.json"),manifest_template_sha256=sha(NATIVE/"manifest_template.json"),
        source_version_binding_sha256=sha(NATIVE/"source_version_binding.json"),
        source_hashes={n:sha(OPS/n) for n in ("adapter.py","remote_ops.py")},
        runtime_binding={"expected_runtime_code_commit":PARENT,"remote_code_root":REMOTE_ROOT},
        diagnostic_only_conda_override={"source":BASE,"sha256":BASE_SHA,"env":"project_cluster",
            "reason":"Current SERVERS PSC production shim is historical and expired; preserve it. Only diagnostics use this separately reviewed original immutable base; never full trainer launch."})
    release["resource_policy"]["SERVERS_sha256"]=SERVERS_SHA
    release["conditional_parent_promotion"].update(expected_primary_HEAD=PARENT,required_PSC_receipt_code_commit=PARENT,required_technical_receipt="pipeline/admissions/M231-PSC.json")
    release["conditional_parent_promotion"].pop("historical_LFT_receipt_code_commit",None)
    release["selection_scope"]="Original GPU0-only overlay/free20000MiB/max1/three locks; NSD diagnostics only, no actual execution or training grant."
    save(OPS/"release_template.json",release)
    ops_prep=dict(schema_version=1,recorded_at=datetime.now(timezone.utc).isoformat(),candidate_id=CID,
        experiment_id="M232-NSD",code_commit=SOURCE,source_commit=SOURCE,source_parent_commit=PARENT,
        expected_runtime_code_commit=PARENT,draft_execution_disabled=True,operational_ready=False,
        owner_provenance_only=owner,native_preparation=ref(NATIVE/"preparation.json"),
        release_template=ref(OPS/"release_template.json"),root_launcher=ref(OPS/"run_nsd_operation.py"),
        diagnostic_only_conda_override=release["diagnostic_only_conda_override"],
        observed_current_SERVERS={"sha256":SERVERS_SHA,"historical_conda_source":"/data/songcl/Project/Cluster_project/pipeline/runtime/psc_path_prod_d20ca92f/conda_source.sh","historical_deadline":"2026-11-06T18:08:14.169854+00:00","written":False},
        prepared_file_hashes={p.name:sha(p) for p in OPS.iterdir() if p.is_file()},
        native="NOT_RUN",resources="NOT_RUN",scientific_admission=False,independent_review="PENDING_EXTERNAL")
    save(OPS/"preparation.json",ops_prep)
    save(HERE/"preparation.json",dict(status="DISABLED_ORIGINAL_NSD_NATIVE_OPERATIONAL_SOFTWARE_PREPARED_NOT_NATIVE",
        candidate_id=CID,experiment_id="M232-NSD",source_commit=SOURCE,parent_commit=PARENT,
        owner_provenance_only=owner,native_preparation=ref(NATIVE/"preparation.json"),
        operational_preparation=ref(OPS/"preparation.json"),worker=ref(NATIVE/"worker.py"),
        source_proof=ref(SOURCE_PROOF),source_review=ref(SOURCE_REVIEW),
        original_resource_function_byte_exact=True,no_source_model_YAML_protocol_change=True,
        draft_execution_disabled=True,ten_execution_NULLs=True,execution_material_created=False,
        native="NOT_RUN",resources="NOT_RUN",Torch_autograd="NOT_RUN",independent_review="PENDING_EXTERNAL"))
    print(json.dumps({"prepared":True,"worker":ref(NATIVE/"worker.py"),"native_preparation":ref(NATIVE/"preparation.json"),"operational_preparation":ref(OPS/"preparation.json"),"native":"NOT_RUN","resources":"NOT_RUN"}))


if __name__=="__main__":main()
