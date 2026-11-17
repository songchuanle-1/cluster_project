"""External literal NSD identity oracle against the actual new remote code."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone, timedelta
import ast
import copy
import importlib.util
import json

HERE=Path(__file__).resolve().parent
OLD=Path("D:/project/cluster_project/pipeline/diagnostic_bundles/tick_c706ca80/nsd_native_prepare/operational/remote_ops.py")
def load(path):
    tree=ast.parse(path.read_text(encoding="utf8"))
    tree.body=[n for n in tree.body if not(isinstance(n,ast.Import) and any(a.name=="fcntl" for a in n.names))]
    ns={"__name__":"identity_fixture","__file__":str(path)}
    exec(compile(tree,str(path),"exec"),ns)
    class FixturePath(PurePosixPath):
        def exists(self):return False
    ns["Path"]=FixturePath;ns["PARENT"]=FixturePath("/data/songcl/Project/Cluster_project/pipeline")
    return ns
def run():
    checks=[]
    def check(name,value):
        assert value,name
        checks.append({"name":name,"passed":True})
    new=load(HERE/"remote_ops.py");old=load(OLD)
    expected_id="hierarchy-native-spatial-dirichlet-composition"
    foreign_id="hierarchy-native-position-feature-cross-scatter-composition"
    metadata=json.loads((HERE/"current_binding.json").read_bytes())
    binding={"project":"cluster_project","candidate_id":expected_id,
        "code_commit":"f6257de79148581334ee495e6e2d60ccb525457c",
        "stage":"/data/songcl/Project/Cluster_project/pipeline/nsd_12345678_gpu0",
        "owner":{"token":"1234567890abcdef1234567890abcdef"},
        "physical_gpu":0,"gpu_uuid":"GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c",
        "native_manifest_sha256":"a"*64,"resource_authorization":metadata["resource_authorization"],
        "resource_memory_policy":metadata["resource_memory_policy"]}
    spec=importlib.util.spec_from_file_location("current_identity_checked_adapter",HERE/"adapter.py")
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    class Tripwire:
        def call(self,*a,**kw):raise AssertionError("Transport forbidden")
    adapter=m.Adapter(transport=Tripwire())
    for operation in ("stage","run","reconcile"):
        oracle={"project":"cluster_project","candidate_id":"hierarchy-native-spatial-dirichlet-composition",
            "code_commit":"f6257de79148581334ee495e6e2d60ccb525457c","stage":binding["stage"],
            "token":binding["owner"]["token"],"request_id":"external-"+operation,"operation":operation,
            "physical_gpu":0,"gpu_uuid":"GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c","native_manifest_sha256":"a"*64}
        check(operation+"_new_remote_matches_external_literal",new["identity"](binding,oracle)==oracle)
        check(operation+"_new_adapter_matches_external_literal",adapter._identity(binding,oracle["request_id"],operation)==oracle)
        check(operation+"_frozen_bug_reproduced",old["identity"](binding,oracle)!=oracle)
    check("actual_new_binding_stage_accepts_external_NSD",str(new["binding_stage"](binding))==binding["stage"])
    for label,module,value in (("frozen_rejects_correct_NSD",old,binding),("new_rejects_PSC",new,dict(binding,candidate_id=foreign_id))):
        try:module["binding_stage"](value)
        except RuntimeError as e:check(label,str(e)=="Foreign binding")
        else:raise AssertionError(label)
    for mode in ("smoke","resources"):
        for target in ("champion","candidate"):
            raw={"candidate_id":"hierarchy-native-spatial-dirichlet-composition",
                "code_commit":"f6257de79148581334ee495e6e2d60ccb525457c",
                "goal_sha256":"0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85",
                "mode":mode,"target":target,
                "model_package":"framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"+("_nsd" if target=="candidate" else "")}
            check(mode+"_"+target+"_new_remote_and_adapter_accept_external_NSD",
                new["result_matches"](raw,mode,target) and adapter._raw_result_identity(raw,binding,mode,target))
            check(mode+"_"+target+"_new_remote_and_adapter_reject_PSC",
                not new["result_matches"](dict(raw,candidate_id=foreign_id),mode,target)
                and not adapter._raw_result_identity(dict(raw,candidate_id=foreign_id),binding,mode,target))
            check(mode+"_"+target+"_frozen_result_negative_control",not old["result_matches"](raw,mode,target))
    return checks
