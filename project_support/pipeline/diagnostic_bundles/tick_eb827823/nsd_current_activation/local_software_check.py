"""Activation software checks only; no real process/transport/native execution."""
from pathlib import Path
from datetime import datetime,timezone
from types import ModuleType
from unittest.mock import patch
from contextlib import redirect_stdout
import ast
import hashlib
import importlib.util
import io
import json
import runpy
import subprocess
import sys

HERE=Path(__file__).resolve().parent
MOTHER=Path('D:\\project\\cluster_project\\pipeline\\diagnostic_bundles\\tick_c706ca80\\nsd_native_prepare')
OP_V2=Path('D:\\project\\cluster_project\\pipeline\\diagnostic_bundles\\tick_c706ca80\\nsd_operational_prepare_v2')
N=HERE/"native"
checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def check(n,v):
    assert v,n
    checks.append({"name":n,"passed":True})
def forbidden(*args,**kwargs):raise AssertionError("Process/SSH/GPU forbidden")
def functions(text,klass=None):
    body=ast.parse(text).body
    if klass:body=next(n for n in body if isinstance(n,ast.ClassDef) and n.name==klass).body
    return {n.name:ast.get_source_segment(text,n) for n in body if isinstance(n,ast.FunctionDef)}
def main():
    prep=read(HERE/"preparation.json");template=read(N/"manifest_template.json")
    check("entire_activation_prepared_hash_graph",all(sha(HERE/n)==d for n,d in prep["prepared_file_hashes"].items()))
    check("frozen_mother_complete_hash_graph_unchanged",all(sha(MOTHER/n)==d for n,d in read(MOTHER/"FROZEN.json")["files"].items()))
    check("worker_exact_frozen_mother_bytes",sha(N/"worker.py")==sha(MOTHER/"native/worker.py")=="cd1cb8b000b7109db99b7bb44b69867d1c3bb5e63466a749b51bb4d35fd09112")
    for name,digest in read(N/"preparation.json")["source_files"].items():
        path="candidate.yaml" if name.endswith(".yaml") else "candidate_model/"+Path(name).name
        check("exact9_copied_source:"+path,sha(N/path)==digest==sha(MOTHER/"native"/path))
    for p in HERE.rglob("*.py"):compile(p.read_bytes(),str(p),"exec")
    check("all_new_Python_compile",True)
    old=(MOTHER/"operational/adapter.py").read_text();new=(HERE/"adapter.py").read_text()
    before,after=functions(old,"Adapter"),functions(new,"Adapter")
    check("all_other_adapter_methods_byte_exact",all(after[n]==s for n,s in before.items() if n not in ("_frozen_details","guard")))
    check("diagnostic_only_SSH_transport_byte_exact",functions(old,"SSHTransport")==functions(new,"SSHTransport"))
    check("all_runtime_functions_byte_exact",functions((N/"native_runtime.py").read_text())==functions((MOTHER/"native/native_runtime.py").read_text()))
    check("remote_ops_and_launcher_byte_exact",all((HERE/n).read_bytes()==(OP_V2/"operational"/n).read_bytes() for n in ("remote_ops.py","run_nsd_operation.py")))
    fields=("current_token","stage","tick_generated_at","deadline_at","physical_gpu","gpu_uuid","allowed_gpus","context_sha256","pending_sha256","runtime_code_commit")
    check("mother_and_activation_ten_execution_fields_NULL",all(template[k] is None and read(MOTHER/"native/manifest_template.json")[k] is None for k in fields))
    spec=importlib.util.spec_from_file_location("nsd_current_checked_adapter",HERE/"adapter.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    class Tripwire:
        def call(self,*a,**k):raise AssertionError("Transport forbidden")
    a=m.Adapter(transport=Tripwire())
    with patch.object(subprocess,"run",forbidden),patch.object(subprocess,"Popen",forbidden),patch.object(subprocess,"check_output",forbidden):
        p,t=a._frozen_details();check("actual_current_frozen_details_full_graph_success",p==read(N/"preparation.json") and t==template)
        try:a._release_details()
        except m.Refused:check("missing_root_release_refused",True)
        else:raise AssertionError("Missing root release allowed")
        try:a.guard(0,0,mutation=True)
        except m.Refused:check("actual_child_cannot_use_root_guard",True)
        else:raise AssertionError("Child impersonated root")
        with patch.object(sys,"argv",[str(HERE/"run_nsd_operation.py")]),redirect_stdout(io.StringIO()) as output:runpy.run_path(str(HERE/"run_nsd_operation.py"),run_name="__main__")
        check("actual_default_launcher_NOP",json.loads(output.getvalue())["status"]=="DEFAULT_NOP_NO_ENTRY_OR_TRANSPORT")
    check("original1020second_run_margin", "required_seconds=1020" in after["run"])
    check("explicit_hash_pinned_diagnostic_only_original_conda_base",m.DIAGNOSTIC_CONDA_SOURCE_SHA256=="6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0")
    check("no_release_or_execution_material",all(not(HERE/n).exists() for n in ("adapter_release.json","native_manifest.json","execution_lease.json","execution_binding.json","prepare_request.json","stage_request.json")))
    import importlib.util as _ilu
    _spec=_ilu.spec_from_file_location("identity_regression",HERE/"identity_regression.py");_m=_ilu.module_from_spec(_spec);_spec.loader.exec_module(_m)
    checks.extend(_m.run())
    result={"status":"ACTUAL_LOCAL_CURRENT_NSD_ACTIVATION_SOFTWARE_PASSED_NOT_NATIVE","recorded_at":datetime.now(timezone.utc).isoformat(),
        "check_count":len(checks),"checks":checks,"native":"NOT_RUN","resources":"NOT_RUN","SSH_GPU_process_or_shared_mutation":False}
    with (HERE/"software_validation.json").open("x",encoding="utf8") as s:json.dump(result,s,indent=2);s.write("\n")
    print(json.dumps({"check_count":len(checks),"software_validation_sha256":sha(HERE/"software_validation.json")}))
if __name__=="__main__":main()
