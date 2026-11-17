"""Actual local software checks only; no real Torch, forward, native or resources."""
from pathlib import Path
from datetime import datetime, timezone
from types import ModuleType
from unittest.mock import patch
from contextlib import redirect_stdout
import ast
import copy
import hashlib
import importlib.util
import io
import json
import math
import runpy
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=Path("D:/project/cluster_project")
N=HERE/"native"
O=HERE/"operational"
OLD=ROOT/"pipeline/diagnostic_bundles/tick_2e51495f/psc_native_prepare/native"
checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def check(name,value):
    assert value,name
    checks.append({"name":name,"passed":True})
def func(text,name):
    return ast.get_source_segment(text,next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name))
def forbidden(*args,**kwargs):raise AssertionError("No process/SSH/GPU/model operation allowed")


def main():
    p=read(N/"preparation.json");template=read(N/"manifest_template.json");worker=(N/"worker.py").read_text(encoding="utf8")
    for path in HERE.rglob("*.py"):compile(path.read_bytes(),str(path),"exec")
    check("all_native_operational_and_author_Python_compile",True)
    check("native_prepared_file_hash_graph",all(sha(N/n)==d for n,d in p["prepared_file_hashes"].items()))
    op=read(O/"preparation.json")
    check("operational_prepared_file_hash_graph",all(sha(O/n)==d for n,d in op["prepared_file_hashes"].items()))
    check("manifest_full_payload_hash_graph",all(sha(N/n)==d for n,d in template["diagnostic_files"].items()))
    check("original_complete_resource_function_byte_exact",func(worker,"resources")==func((OLD/"worker.py").read_text(),"resources"))
    check("original_TRAIN2_native_function_and_init_preserved",all(s in worker for s in (
        "train.train(1,model,TwoNativeBatches(loader),optimizer,scheduler,cfg,logger,writer)",
        "len(losses)==len(steps)==len(batches)==len(backward_records)", "common_initialized_parameters",
        "dec.cluster_att.spatial_dirichlet.", "whole_spatial_dirichlet_weight_gradient",
        "whole_spatial_dirichlet_weight_updated","whole_spatial_dirichlet_module_updated")))
    check("no_stale_PSC_core_observer_functions",all(s not in worker for s in (
        "graph.cross_scatter_components","graph.pack_cross_rows","core.factor","10*core.channels")))
    check("actual_NSDirichlet_original_calls_and_stage_observers",all(s in worker for s in (
        "output=original_mean(values,labels,count)","plan=original_chain(coordinates,labels,count)",
        "output=original_energy(values,coordinates,labels,count)","('analysis','synthesis')",
        "actual_analysis_calls","actual_synthesis_calls","actual_chain_energy_calls",
        "actual_original_valid_coordinate_and_feature_mask_reference")))
    check("two_original_mask_expressions_use_lineage_and_equal_values_not_identity",
        "selected['points_mask_ref'].tolist()==selected['positions_mask_ref'].tolist()" in worker
        and "selected['points_mask_ref'] is selected['positions_mask_ref']" not in worker)
    check("original_squared_contrast_dtype_preserved_without_FP32_cast",
        "output.dtype==tensor.dtype" in worker and "extra_FP32_cast_added':False" in worker)
    core_source=(N/"candidate_model/spatial_dirichlet.py").read_text()
    values={"math":math}
    for name in ("build_chain_plan","build_support_plan"):
        exec(compile(func(core_source,name),"original_pure_builder_only","exec"),values)
    exec(compile(func(worker,"nsd_chain_plan_observation"),"new_observer_helper_only","exec"),values)
    tie=values["build_chain_plan"]([[0,0,0],[0,0,0],[1,0,0]],[0,0,0],1)
    observed=values["nsd_chain_plan_observation"](tie,1)
    check("actual_observer_tie_group_fixture",observed["actual_coordinate_tie_group_count"]==1 and observed["actual_edge_count"]==1)
    singleton=values["build_chain_plan"]([[0,0,0],[2,0,0]],[0,1],3)
    observed=values["nsd_chain_plan_observation"](singleton,3)
    check("actual_observer_singleton_empty_zero_edge_fixture_legal",observed["actual_edge_count"]==0 and observed["actual_singleton_or_empty_chain_parent_count"]==3)
    check("optional_native_boundary_absence_not_a_resampling_or_positivity_gate",
        observed["coordinate_ties_on_original_batch"]=="NOT_EXERCISED"
        and observed["optional_boundary_coverage_is_not_a_new_nonzero_or_resampling_gate"] is True)
    malformed=copy.deepcopy(singleton);malformed["left"]=[0]
    try:values["nsd_chain_plan_observation"](malformed,3)
    except AssertionError:check("malformed_observer_plan_refused",True)
    else:raise AssertionError("Malformed plan accepted")
    fields=("current_token","stage","tick_generated_at","deadline_at","physical_gpu","gpu_uuid","allowed_gpus","context_sha256","pending_sha256","runtime_code_commit")
    check("all_ten_execution_fields_NULL",all(template[k] is None for k in fields))
    check("runtime_and_adapter_DRAFT_True","DRAFT_EXECUTION_DISABLED = True" in (N/"native_runtime.py").read_text() and "DRAFT_EXECUTION_DISABLED = True" in (O/"adapter.py").read_text())
    spec=importlib.util.spec_from_file_location("nsd_disabled_checked_adapter",O/"adapter.py");module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    class Tripwire:
        def call(self,*args,**kwargs):raise AssertionError("Transport forbidden")
    adapter=module.Adapter(transport=Tripwire())
    with patch.object(subprocess,"run",forbidden),patch.object(subprocess,"Popen",forbidden),patch.object(subprocess,"check_output",forbidden):
        actual,effective=adapter._frozen_details()
        check("actual_adapter_frozen_details_success",actual==p and effective==template)
        try:adapter._release_details()
        except module.Refused:check("missing_release_refuses_before_transport",True)
        else:raise AssertionError("Missing release accepted")
        with patch.object(sys,"argv",[str(O/"run_nsd_operation.py")]),redirect_stdout(io.StringIO()) as output:
            runpy.run_path(str(O/"run_nsd_operation.py"),run_name="__main__")
        check("actual_default_root_launcher_NOP",json.loads(output.getvalue())["status"]=="DEFAULT_NOP_NO_ENTRY_OR_TRANSPORT")
        with patch.object(sys,"path",[str(N)]+sys.path):
            try:runpy.run_path(str(N/"worker.py"),run_name="__main__")
            except RuntimeError as error:check("actual_DRAFT_worker_refuses_before_manifest_GPU_Torch", "execution-disabled" in str(error))
            else:raise AssertionError("Draft worker executed")
    check("diagnostic_only_original_base_override_explicit_and_hash_bound",module.DIAGNOSTIC_CONDA_SOURCE=="/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh"
        and module.DIAGNOSTIC_CONDA_SOURCE_SHA256=="6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
        and "shlex.quote(DIAGNOSTIC_CONDA_SOURCE)" in (O/"adapter.py").read_text())
    check("genuine_PSC_parent_receipt_anchor_only",module.PARENT_EXPERIMENT=="M231-PSC" and module.HISTORICAL_PARENT_RECEIPT_COMMIT=="0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d")
    check("original_1020second_run_margin_and_three_locks", "required_seconds=1020" in (O/"adapter.py").read_text() and "('training', 'diagnostic', 'exclusive')" in (N/"native_runtime.py").read_text())
    check("real_Torch_not_imported",not any(k=="torch" or k.startswith("torch.") for k in sys.modules))
    check("no_active_execution_material_or_release",not any(p.name in ("adapter_release.json","native_manifest.json","execution_lease.json","execution_binding.json","prepare_request.json") for p in HERE.rglob("*")))
    result={"status":"ACTUAL_LOCAL_NSD_DIAGNOSTIC_SOFTWARE_CHECKS_PASSED_NOT_NATIVE","recorded_at":datetime.now(timezone.utc).isoformat(),
        "checks":checks,"check_count":len(checks),"worker_sha256":sha(N/"worker.py"),
        "scope":"Compile/AST/hash/actual disabled-adapter/default-NOP/default-worker refusal plus pure original chain-builder/new observer boundary fixtures only. No tensor arithmetic, real Torch/autograd/native data/model/GPU/resources.",
        "observer_only_correction":"Two original mask inversions create distinct objects; verify same original mask/batch lineage and equal Boolean selections. No source/model change.",
        "native":"NOT_RUN","resources":"NOT_RUN","Torch_autograd":"NOT_RUN","SSH_GPU_shared_or_source_mutation":False}
    with (HERE/"software_validation.json").open("x",encoding="utf8") as stream:json.dump(result,stream,indent=2);stream.write("\n")
    print(json.dumps({"check_count":len(checks),"software_validation_sha256":sha(HERE/"software_validation.json"),"native":"NOT_RUN","resources":"NOT_RUN"}))


if __name__=="__main__":main()
