"""Build a separate disabled correction; perform local in-memory identity checks."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import redirect_stdout
import ast
import copy
import hashlib
import importlib.util
import io
import json
import runpy
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=Path("D:/project/cluster_project")
TICK=HERE.parent
MOTHER=TICK/"nsd_native_prepare"
O=HERE/"operational"
EXPECTED="hierarchy-native-spatial-dirichlet-composition"
PSC="hierarchy-native-position-feature-cross-scatter-composition"
COMMIT="f6257de79148581334ee495e6e2d60ccb525457c"
GOAL="0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85"
UUID="GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write(p,v):
    p=Path(p)
    assert p.resolve().is_relative_to(HERE.resolve()) and not (HERE/"FROZEN.json").exists()
    with p.open("w",encoding="utf8",newline="\n") as f:json.dump(v,f,indent=2,allow_nan=False);f.write("\n")
def ref(p):return {"path":Path(p).relative_to(ROOT).as_posix(),"sha256":sha(p)}
def check(name,value):
    assert value,name
    checks.append({"name":name,"passed":True})
def forbidden(*a,**kw):raise AssertionError("Actual process, SSH, GPU or resource access forbidden")

def load_remote(path):
    # Windows lacks fcntl. Execute the full module AST except that unused import.
    tree=ast.parse(path.read_text(encoding="utf8"))
    tree.body=[n for n in tree.body if not (isinstance(n,ast.Import) and any(a.name=="fcntl" for a in n.names))]
    ns={"__name__":"isolated_remote_identity_fixture","__file__":str(path),"fcntl":SimpleNamespace()}
    exec(compile(tree,str(path),"exec"),ns)
    return ns

def expect_refusal(name,fn,text):
    try:fn()
    except RuntimeError as e:check(name,text in str(e))
    else:raise AssertionError(name+": unexpectedly accepted")

def main():
    assert not (HERE/"FROZEN.json").exists(),"A frozen package must never be rewritten"
    preserved=[MOTHER/"FROZEN.json",TICK/"nsd_current_activation/FROZEN.json",
        TICK/"nsd_native_prepare_independent_review.json",TICK/"nsd_activation_independent_review.json"]
    before={str(p):sha(p) for p in preserved}
    O.mkdir(exist_ok=True)
    for name in ("adapter.py","run_nsd_operation.py"):shutil.copyfile(MOTHER/"operational"/name,O/name)
    original=(MOTHER/"operational/remote_ops.py").read_bytes()
    old=("CANDIDATE='"+PSC+"'").encode();new=("CANDIDATE='"+EXPECTED+"'").encode()
    assert original.count(old)==1
    (O/"remote_ops.py").write_bytes(original.replace(old,new))
    check("remote_only_one_candidate_literal_changed", (O/"remote_ops.py").read_bytes().replace(new,old)==original)
    for name in ("adapter.py","run_nsd_operation.py"):
        check(name+"_byte_exact_to_frozen_mother",sha(O/name)==sha(MOTHER/"operational"/name))
    for path in (HERE/"build_and_validate.py",O/"adapter.py",O/"remote_ops.py",O/"run_nsd_operation.py"):
        compile(path.read_bytes(),str(path),"exec")
    check("all_four_Python_files_compile",True)
    release=read(MOTHER/"operational/release_template.json")
    release["purpose"]="Disabled operational v2 identity correction only; no execution release."
    release["source_hashes"]={n:sha(O/n) for n in ("adapter.py","remote_ops.py")}
    write(O/"release_template.json",release)
    prep=read(MOTHER/"operational/preparation.json")
    prep["recorded_at"]=datetime.now(timezone.utc).isoformat()
    prep["version"]=2
    prep["purpose"]="Fresh disabled correction of remote NSD candidate identity; frozen failures retained."
    prep["release_template"]=ref(O/"release_template.json")
    prep["root_launcher"]=ref(O/"run_nsd_operation.py")
    prep["prepared_file_hashes"]={n:sha(O/n) for n in ("adapter.py","remote_ops.py","run_nsd_operation.py","release_template.json")}
    prep["frozen_mother"]=ref(MOTHER/"FROZEN.json")
    prep["negative_evidence"]=[ref(p) for p in preserved[2:]]
    prep["prior_activation"]=ref(preserved[1])
    prep["fresh_owner_activation_required"]=True
    write(O/"preparation.json",prep)
    ns=load_remote(O/"remote_ops.py")
    original_ns=load_remote(MOTHER/"operational/remote_ops.py")
    filesystem={};directories=set()
    class MemoryPath(PurePosixPath):
        def exists(self):return str(self) in filesystem or str(self) in directories
        def resolve(self):return self
        def mkdir(self,parents=False,exist_ok=False):
            if self.exists() and not exist_ok:raise FileExistsError(str(self))
            directories.add(str(self))
        def open(self,mode="r",*args,**kwargs):
            assert mode=="xb",mode
            assert not self.exists()
            filesystem[str(self)]=b""
            return io.BytesIO()
    now=datetime.now(timezone.utc)
    binding={"project":"cluster_project","candidate_id":EXPECTED,"code_commit":COMMIT,
        "stage":"/data/songcl/Project/Cluster_project/pipeline/nsd_12345678_gpu0",
        "owner":{"token":"1234567890abcdef1234567890abcdef",
            "generated_at":(now-timedelta(minutes=1)).isoformat(),"deadline_at":(now+timedelta(minutes=30)).isoformat()},
        "physical_gpu":0,"gpu_uuid":UUID,"native_manifest_sha256":"a"*64,
        "execution_lease_sha256":"b"*64,"runtime_code_commit":"0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d",
        "resource_authorization":{"path":"pipeline/authorizations/server4_gpu0_overlay_20261104.json",
            "sha256":"783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88"},
        "resource_memory_policy":{"allow_external_overlay":True,"minimum_free_mib_before_launch":20000,
            "max_project_tasks_per_gpu":1,"cooperative_lock_kinds":["training","diagnostic","exclusive"],
            "external_contexts":"record_preserve_no_signals","measurement_scope":"authorized_overlay_potentially_contended_not_exclusive"}}
    def expected(request_id,operation):
        # Independent literal oracle; never reads ns['CANDIDATE'] or adapter constants.
        return {"project":"cluster_project","candidate_id":"hierarchy-native-spatial-dirichlet-composition",
            "code_commit":"f6257de79148581334ee495e6e2d60ccb525457c","stage":binding["stage"],
            "token":binding["owner"]["token"],"request_id":request_id,"operation":operation,
            "physical_gpu":0,"gpu_uuid":"GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c","native_manifest_sha256":"a"*64}
    def raw(mode,target):
        return {"candidate_id":"hierarchy-native-spatial-dirichlet-composition",
            "code_commit":"f6257de79148581334ee495e6e2d60ccb525457c","goal_sha256":GOAL,
            "mode":mode,"target":target,"execution_completed":True,
            "model_package":"framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"+("_nsd" if target=="candidate" else "")}
    for module in (ns,original_ns):
        module["Path"]=MemoryPath
        module["PARENT"]=MemoryPath("/data/songcl/Project/Cluster_project/pipeline")
        module["subprocess"]=SimpleNamespace(Popen=forbidden,check_output=forbidden,TimeoutExpired=subprocess.TimeoutExpired)
    expect_refusal("negative_control_frozen_remote_rejects_external_NSD_binding",lambda:original_ns["binding_stage"](binding),"Foreign binding")
    check("negative_control_frozen_remote_emits_wrong_identity",original_ns["identity"](binding,expected("stage-fixture","stage"))!=expected("stage-fixture","stage"))
    check("corrected_binding_stage_accepts_external_NSD",str(ns["binding_stage"](binding))==binding["stage"])
    foreign=copy.deepcopy(binding);foreign["candidate_id"]=PSC
    expect_refusal("corrected_binding_stage_rejects_PSC_binding",lambda:ns["binding_stage"](foreign),"Foreign binding")
    spec=importlib.util.spec_from_file_location("disabled_v2_adapter",O/"adapter.py")
    adapter_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter_module)
    class Tripwire:
        def call(self,*a,**kw):return forbidden()
    adapter=adapter_module.Adapter(transport=Tripwire())
    with patch.object(subprocess,"run",forbidden),patch.object(subprocess,"Popen",forbidden),patch.object(subprocess,"check_output",forbidden):
        frozen,template=adapter._frozen_details()
        check("actual_unchanged_adapter_native_frozen_details",frozen==read(MOTHER/"native/preparation.json"))
        check("DRAFT_execution_still_disabled",adapter_module.DRAFT_EXECUTION_DISABLED is True)
        try:adapter._release_details()
        except adapter_module.Refused:check("missing_actual_release_refuses_before_transport",True)
        else:raise AssertionError("Actual release unexpectedly present")
        with patch.object(sys,"argv",[str(O/"run_nsd_operation.py")]),redirect_stdout(io.StringIO()) as output:
            runpy.run_path(str(O/"run_nsd_operation.py"),run_name="__main__")
        check("actual_default_launcher_NOP",json.loads(output.getvalue())["status"]=="DEFAULT_NOP_NO_ENTRY_OR_TRANSPORT")
    for operation in ("stage","run","reconcile"):
        oracle=expected(operation+"-fixture",operation)
        check(operation+"_remote_identity_matches_external_literal",ns["identity"](binding,oracle)==oracle)
        check(operation+"_actual_adapter_identity_matches_external_literal",adapter._identity(binding,oracle["request_id"],operation)==oracle)
    ns["read"]=lambda p:copy.deepcopy(filesystem[str(p)])
    ns["write"]=lambda p,v:filesystem.__setitem__(str(p),copy.deepcopy(v))
    ns["sha"]=lambda p:"a"*64 if str(p).endswith("native_manifest.json") else hashlib.sha256(str(filesystem.get(str(p),"fixture")).encode()).hexdigest()
    ns["native_verify"]=lambda *a:None
    ns["require_usable"]=lambda *a:None
    ns["exact_workers"]=lambda *a,**kw:[]
    ns["process_info"]=lambda pid:{"pid":pid,"start_ticks":"fixture","argv":["fixture"],"state":"Z"}
    ns["sys"]=SimpleNamespace(executable="/opt/conda/envs/project_cluster/bin/python",path=[])
    request=expected("stage-fixture","stage")
    bad=dict(request,candidate_id=PSC)
    expect_refusal("stage_rejects_PSC_request_before_mocked_IO",lambda:ns["stage_operation"]({"binding":binding,"request":bad,"files":{}}),"Stage request identity mismatch")
    staged=ns["stage_operation"]({"binding":binding,"request":request,"files":{}})
    check("actual_stage_lifecycle_emits_external_NSD_identity",staged["verified"] is True and staged["identity"]==request)
    stage=MemoryPath(binding["stage"])
    filesystem[str(stage/"native_manifest.json")]={"fixture":True}
    for mode in ("smoke","resources"):
        for target in ("champion","candidate"):
            prefix=mode+"_"+target
            request={**expected(prefix+"-fixture","run"),"mode":mode,"target":target}
            bad=dict(request,candidate_id=PSC)
            expect_refusal(prefix+"_run_rejects_PSC_request",lambda:ns["run_operation"]({"binding":binding,"request":bad}),"Worker request identity mismatch")
            class Process:
                pid=12345
                def wait(self,timeout):
                    assert timeout==660
                    filesystem[str(stage/(prefix+"_result.json"))]=raw(mode,target)
                    return 0
            def popen(command,**kwargs):
                check(prefix+"_command_matches_actual_validator",ns["command_matches"](command,stage,mode,target))
                return Process()
            ns["subprocess"]=SimpleNamespace(Popen=popen,check_output=forbidden,TimeoutExpired=subprocess.TimeoutExpired)
            completed=ns["run_operation"]({"binding":binding,"request":request})
            check(prefix+"_actual_run_lifecycle_external_identity",completed["identity"]==expected(prefix+"-fixture","run") and completed["returncode"]==0)
            check(prefix+"_remote_and_adapter_accept_external_NSD_result",ns["result_matches"](raw(mode,target),mode,target) and adapter._raw_result_identity(raw(mode,target),binding,mode,target))
            badraw=dict(raw(mode,target),candidate_id=PSC)
            check(prefix+"_remote_and_adapter_reject_PSC_result",not ns["result_matches"](badraw,mode,target) and not adapter._raw_result_identity(badraw,binding,mode,target))
            check(prefix+"_original_result_negative_control",not original_ns["result_matches"](raw(mode,target),mode,target))
    def inventory(command,**kw):
        assert command[0]=="nvidia-smi"
        return "0, "+UUID if "--query-gpu=index,uuid" in command else ""
    ns["subprocess"]=SimpleNamespace(Popen=forbidden,check_output=inventory,TimeoutExpired=subprocess.TimeoutExpired)
    reconciled=ns["reconcile_operation"]({"binding":binding})
    check("actual_reconcile_all_five_request_identities",len(reconciled["requests"])==5 and all(x["identity_matches"] and x["completed_identity_matches"] for x in reconciled["requests"]))
    check("actual_reconcile_all_four_result_identities",all(x["result_identity_matches"] and x["completed_result_identity_matches"] for x in reconciled["requests"] if x["file"]!="stage_request.json"))
    selected=ns["reconcile_operation"]({"binding":binding,"request_id":"smoke_candidate-fixture"})
    check("actual_reconcile_original_request_id_filter",len(selected["requests"])==1 and selected["requests"][0]["request"]["request_id"]=="smoke_candidate-fixture")
    key=str(stage/"smoke_candidate_request.json");filesystem[key]["candidate_id"]=PSC
    key2=str(stage/"smoke_candidate_result.json");filesystem[key2]["candidate_id"]=PSC
    tainted=ns["reconcile_operation"]({"binding":binding,"request_id":"smoke_candidate-fixture"})["requests"][0]
    check("actual_reconcile_flags_foreign_PSC_request_and_result",not tainted["identity_matches"] and not tainted["result_identity_matches"])
    fields=("current_token","stage","tick_generated_at","deadline_at","physical_gpu","gpu_uuid","allowed_gpus","context_sha256","pending_sha256","runtime_code_commit")
    check("referenced_native_all_ten_execution_fields_NULL",all(template[k] is None for k in fields))
    check("all_preserved_frozen_and_negative_review_bytes_unchanged",all(sha(Path(p))==digest for p,digest in before.items()))
    check("operational_preparation_hash_graph",all(sha(O/n)==digest for n,digest in prep["prepared_file_hashes"].items()))
    check("release_template_source_hash_graph",all(sha(O/n)==digest for n,digest in release["source_hashes"].items()))
    check("no_actual_execution_material",not any(p.name in ("adapter_release.json","native_manifest.json","execution_binding.json","execution_lease.json") for p in HERE.rglob("*")))
    check("no_Torch_import",not any(k=="torch" or k.startswith("torch.") for k in sys.modules))
    validation={"status":"LOCAL_OPERATIONAL_V2_IDENTITY_REGRESSION_PASS_DISABLED",
        "recorded_at":datetime.now(timezone.utc).isoformat(),"check_count":len(checks),"checks":checks,
        "expected_candidate_literal":EXPECTED,"fixture_scope":"Full actual remote identity/binding/stage/run/reconcile functions with in-memory POSIX filesystem and mocked resource/native/process/inventory boundaries; actual local adapter identity/frozen/default-NOP/refusal checks. External literal oracle and original failed producer negative controls.",
        "native":"NOT_RUN","resources":"NOT_RUN","SSH_GPU":False,"scientific_admission":False,
        "independent_review":"PENDING_EXTERNAL","execution_material_created":False}
    write(HERE/"software_validation.json",validation)
    (HERE/"README.md").write_text("Disabled operational v2 fixes only the remote candidate literal. Adapter and launcher remain byte-exact to the frozen mother; native model, worker, protocol and all ten NULL fields are unchanged and referenced there. Both failed frozen packages and negative reviews are preserved. Regression oracles use the external literal NSD ID and reproduce the original bug. Full lifecycle functions use only in-memory synthetic fixtures, with resource/native/process boundaries mocked. No release, execution binding, lease, stage, SSH, GPU, native or resource run exists. Requires independent review and separately authorized fresh-owner activation; this tick is not an execution grant.\n",encoding="utf8")
    top={"status":"AUTHOR_FROZEN_DISABLED_OPERATIONAL_V2_PENDING_INDEPENDENT_REVIEW",
        "recorded_at":datetime.now(timezone.utc).isoformat(),"candidate_id":EXPECTED,"source_commit":COMMIT,
        "draft_execution_disabled":True,"operational_ready":False,"frozen_mother":ref(MOTHER/"FROZEN.json"),
        "prior_activation":ref(preserved[1]),"negative_evidence":[ref(p) for p in preserved[2:]],
        "source_proof":ref(TICK/"nsd_compatible_source/proof.json") if (TICK/"nsd_compatible_source/proof.json").exists() else None,
        "operational_preparation":ref(O/"preparation.json"),"software_validation":ref(HERE/"software_validation.json"),
        "native":"NOT_RUN","resources":"NOT_RUN","scientific_admission":False,
        "fresh_owner_activation_required":True,"independent_review":"PENDING_EXTERNAL"}
    write(HERE/"preparation.json",top)
    files={p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob("*")) if p.is_file()}
    write(HERE/"FROZEN.json",{"status":"AUTHOR_FROZEN_DISABLED_OPERATIONAL_V2_PENDING_INDEPENDENT_REVIEW",
        "recorded_at":datetime.now(timezone.utc).isoformat(),"files":files,"author_will_not_write_further":True,
        "source_commit":COMMIT,"native":"NOT_RUN","resources":"NOT_RUN","execution_material_created":False})
    print(json.dumps({"directory":str(HERE),"check_count":len(checks),"FROZEN":sha(HERE/"FROZEN.json"),
        "preparation":sha(HERE/"preparation.json"),"operational_preparation":sha(O/"preparation.json"),
        "remote_ops":sha(O/"remote_ops.py"),"software_validation":sha(HERE/"software_validation.json")},indent=2))

if __name__=="__main__":main()
