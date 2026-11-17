"""Author disabled local NSD deployment templates; no actual operations."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,importlib.util,json,os,subprocess,sys
ROOT=Path("D:/project/cluster_project");TICK=Path(__file__).resolve().parent
OLD=ROOT/"pipeline/diagnostic_bundles/tick_d20ca92f"
OUT=TICK/"nsd_deployment_prepare"
KEYS=("token","thread_id","generated_at","deadline_at","context_sha256","pending_sha256")
SOURCE="f6257de79148581334ee495e6e2d60ccb525457c";BASE="0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
AUTHOR="01a1b166-dcbf-7d01-b0cb-c85fff644605"
CPU_BASE="/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh"
CPU_SHA="6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
changes=[];checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def ref(p):return {"path":Path(p).relative_to(ROOT).as_posix(),"sha256":sha(p)}
def guard():
    o=read(ROOT/"pipeline/headless/.foreground.lockdir/owner.json")
    assert os.environ["CODEX_THREAD_ID"]==AUTHOR and o["token"]=="f74f3603193a426097a8dc288fd05fde"
    assert datetime.now(timezone.utc)<datetime.fromisoformat(o["deadline_at"])
    assert sha(ROOT/"pipeline/headless/.tick_context.json")==o["context_sha256"]
    assert sha(ROOT/"pipeline/headless/.tick_context_state.next.json")==o["pending_sha256"]
    return {k:o[k] for k in KEYS}
def save(name,v):
    guard();p=OUT/name
    raw=v.encode() if isinstance(v,str) else (json.dumps(v,indent=2,allow_nan=False)+"\n").encode()
    with p.open("xb") as f:f.write(raw)
def check(name,value):
    assert value,name
    checks.append({"name":name,"passed":True})
def change(text,old,new,label):
    assert text.count(old)==1,(label,old[:80])
    changes.append({"change":label,"from":old,"to":new,"count":1})
    return text.replace(old,new,1)
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def function(text,name):
    return ast.get_source_segment(text,next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name))
def main():
    owner=guard();frozen=read(OLD/"psc_deployment_prepare/FROZEN.json")
    assert read(OLD/"psc_deployment_helper_independent_review.json")["passed"] is True
    assert all(sha(OLD/"psc_deployment_prepare"/n)==d for n,d in frozen["files"].items())
    old_owner=read(OLD/"psc_deployment_baseline.json")["owner"]
    replacements=[("0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d",SOURCE),
        ("d20eb221eff6584b67d4e9b5673559d0e1cb735b",BASE),
        ("hierarchy-native-position-feature-cross-scatter-composition","hierarchy-native-spatial-dirichlet-composition"),
        ("PSC","NSD"),("psc","nsd"),("M231-NSD","M232-NSD")]
    replacements += [(old_owner[k],owner[k]) for k in KEYS if old_owner[k]!=owner[k]]
    replacements += [("d20ca92f","f74f3603"),
        ("pipeline/diagnostic_bundles/tick_12e364dc/nsd_compatible_source/compatible_source_version.json",
         "pipeline/diagnostic_bundles/tick_c706ca80/nsd_compatible_source/compatible_source_version.json"),
        ("9c6308fe6d166216123ef23e871eeacec5e8e3b2b3b9c02fb448364a44d13083",
         "e1a03ed4f1631d78f427fedc153d54bf7a3a0a94bcb2272e11c7caf19c1e3302"),
        ('OLD_ROOT = "/data/songcl/Project/Cluster_project/Cluster_hvd_20261106"',
         'OLD_ROOT = "/data/songcl/Project/Cluster_project/Cluster_psc_20261106"'),
        ('Cluster_nsd_20261106','Cluster_nsd_20261107')]
    def port(text,record=True):
        for a,b in replacements:
            count=text.count(a)
            if count and record:changes.append({"change":"literal_port","from":a,"to":b,"count":count})
            text=text.replace(a,b)
        return text
    OUT.mkdir()
    old=(OLD/"psc_deployment_prepare/deploy_psc.py").read_text(encoding="utf8")
    d=port(old)
    d=change(d,'ARGS = None','ARGS = None\nDRAFT_EXECUTION_DISABLED = True\nCPU_CONDA_SOURCE = '+repr(CPU_BASE)+'\nCPU_CONDA_SOURCE_SHA256 = '+repr(CPU_SHA),"disabled_and_CPU_base_constants")
    d=change(d,'def guard(seconds=0):','def guard(seconds=0):\n    assert not DRAFT_EXECUTION_DISABLED, "Disabled NSD deployment template; separate reviewed root activation required"',"disabled_before_IO")
    d=change(d,'choices=["ff", "runtime", "switch", "all"], default="all"','choices=["ff", "runtime", "switch"], default=None',"separate_phases_only")
    d=change(d,'    ARGS = args','    assert args.phase in ("ff", "runtime", "switch"), "Explicit separate phase required"\n    ARGS = args',"explicit_phase")
    d=change(d,'("receipt", "review", "native-manifest", "native-result", "resource-result", "protected-baseline", "baseline-sha256", "review-sha256")',
        '("receipt", "review", "native-manifest", "native-result", "resource-result", "protected-baseline", "baseline-sha256", "review-sha256", "production-result", "production-review", "production-review-sha256")',"switch_actual_production_inputs")
    d=change(d,'    guard(60)\n    assert not (EXEC / "switch_intent.json").exists()',
        '''    guard(60)
    assert ARGS.production_result and ARGS.production_review and ARGS.production_review_sha256
    production_path=Path(ARGS.production_result).resolve();review_path=Path(ARGS.production_review).resolve()
    assert production_path.is_relative_to(ROOT.resolve()) and review_path.is_relative_to(ROOT.resolve())
    assert sha(review_path)==ARGS.production_review_sha256
    actual=read(production_path);peer=read(review_path)
    assert peer["passed"] is True and peer["production_result_sha256"]==sha(production_path)
    assert actual["kind"]=="PRODUCTION_PATH_INSTALLED_NO_TRAINER_LAUNCHED" and actual["owner"]==EXPECTED
    assert actual["binding"]["source_commit"]==SOURCE and actual["binding"]["runtime_root"]==NEW_ROOT
    assert actual["training_launch_or_GPU_use"] is False and actual["one_shot_consumed"] is False
    assert actual["shim"]=="/data/songcl/Project/Cluster_project/pipeline/runtime/nsd_path_prod_f74f3603/conda_source.sh"
    assert not (EXEC / "switch_intent.json").exists()''',"root_switch_requires_actual_reviewed_production")
    d=change(d,'"old_roots": {OLD_ROOT: BASE,','"old_roots": {OLD_ROOT: BASE,\n                  "/data/songcl/Project/Cluster_project/Cluster_hvd_20261106": "d20eb221eff6584b67d4e9b5673559d0e1cb735b",',"preserve_PSC_and_HVD_old_roots")
    d=change(d,'        "pipeline/admissions/M230-HVD.json",','        "pipeline/admissions/M230-HVD.json", "pipeline/admissions/M231-PSC.json",',"preserve_PSC_receipt")
    old_activation='    activation = "source " + shlex.quote(server["conda_source"]) + " && conda activate " + shlex.quote(server["conda_env"]) + " && CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python -B -"'
    new_activation='''    assert server["conda_env"]=="project_cluster"
    verification="/usr/bin/python3 -I -B -c "+shlex.quote("import hashlib,pathlib;assert hashlib.sha256(pathlib.Path("+repr(CPU_CONDA_SOURCE)+").read_bytes()).hexdigest()=="+repr(CPU_CONDA_SOURCE_SHA256))
    activation = verification+" && source " + shlex.quote(CPU_CONDA_SOURCE) + " && conda activate " + shlex.quote(server["conda_env"]) + " && CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python -B -"'''
    d=change(d,old_activation,new_activation,"CPU_only_verified_original_base_bypasses_expired_SERVERS_shim")
    save("deploy_nsd.py",d)
    baseline=port((OLD/"psc_deployment_prepare/prepare_psc_baseline.py").read_text(encoding="utf8"))
    save("prepare_nsd_baseline.py",baseline)
    dispatch=port((OLD/"dispatch_psc_once.py").read_text(encoding="utf8"))
    dispatch=change(dispatch,'HERE = Path(__file__).resolve().parent','HERE = Path(__file__).resolve().parent\nTICK = HERE.parent\nDRAFT_EXECUTION_DISABLED = True\nEXPECTED_OWNER = '+repr(owner),"dispatcher_disabled_exact_owner")
    dispatch=change(dispatch,'def guard():','def guard():\n    assert not DRAFT_EXECUTION_DISABLED, "Disabled NSD dispatch template; separate reviewed root activation required"',"dispatcher_disabled_before_IO")
    dispatch=change(dispatch,'    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD == os.environ["CODEX_THREAD_ID"]',
        '    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD == os.environ["CODEX_THREAD_ID"]\n    assert {k:owner[k] for k in EXPECTED_OWNER}==EXPECTED_OWNER',"dispatcher_six_fields")
    dispatch=change(dispatch,'    assert production["owner"]["token"] == TOKEN','    assert production["owner"] == EXPECTED_OWNER',"production_all_six_owner_fields")
    dispatch=change(dispatch,'    assert raw["remote_code_root"] == RUNTIME and raw["conda_source"] == production["shim"]',
        '    assert raw["remote_code_root"] == RUNTIME and raw["conda_source"] == production["shim"]\n    assert production["shim"]=="/data/songcl/Project/Cluster_project/pipeline/runtime/nsd_path_prod_f74f3603/conda_source.sh"',"dispatch_exact_new_rendered_shim")
    dispatch=change(dispatch,'before = HERE / "protected_assets_before.json"','before = TICK / "protected_assets_before.json"',"dispatcher_current_tick_snapshot")
    save("dispatch_nsd_once.py",dispatch)
    for p in OUT.glob("*.py"):compile(p.read_bytes(),str(p),"exec")
    check("all_three_helper_Python_compile",True)
    m=load("disabled_nsd_deployment",OUT/"deploy_nsd.py")
    q=load("disabled_nsd_dispatch",OUT/"dispatch_nsd_once.py")
    check("source_parent_owner_and_roots",m.SOURCE==SOURCE and m.BASE==BASE and m.EXPECTED==owner
        and m.OLD_ROOT.endswith("Cluster_psc_20261106") and m.NEW_ROOT.endswith("Cluster_nsd_20261107"))
    check("exact_CPU_base_and_source_commit",m.CPU_CONDA_SOURCE==CPU_BASE and m.CPU_CONDA_SOURCE_SHA256==CPU_SHA and q.SOURCE==SOURCE)
    check("dispatcher_new_owner_runtime_and_DRAFT",q.EXPECTED_OWNER==owner and q.RUNTIME==m.NEW_ROOT and m.DRAFT_EXECUTION_DISABLED is True and q.DRAFT_EXECUTION_DISABLED is True)
    for name,module in (("deployment",m),("dispatch",q)):
        try:module.guard()
        except AssertionError as e:check(name+"_actual_DRAFT_refusal_before_IO",str(e).startswith("Disabled NSD"))
        else:raise AssertionError("Disabled guard entered")
    for name in ("deploy_nsd.py","prepare_nsd_baseline.py","dispatch_nsd_once.py"):
        result=subprocess.run([sys.executable,"-B","-X","utf8",str(OUT/name)],capture_output=True,text=True,timeout=15)
        check(name+"_actual_default_NOP",result.returncode==0 and json.loads(result.stdout)["status"].startswith("DEFAULT_NOP"))
    check("FF_function_only_literal_ports_no_algorithm_change",function(d,"ff")==port(function(old,"ff"),False))
    check("protected_function_only_literal_ports_no_algorithm_change",function(d,"protected")==port(function(old,"protected"),False))
    check("actual_receipt_native_resource_and_peer_gate_algorithm_retained",function(d,"gates")==port(function(old,"gates"),False))
    check("baseline_algorithm_only_literal_ports",baseline==port((OLD/"psc_deployment_prepare/prepare_psc_baseline.py").read_text(),False))
    check("dispatcher_proc_probe_and_canonical_queue_contract_retained",
        "read_only_proc_replaced_existence_probe" in dispatch and "monitor._process_queue(" in dispatch
        and 'max_tasks_per_gpu=1, allow_external_overlay=True, task_memory_mb=20000' in dispatch
        and 'current_tasks=0, max_tasks_total=1' in dispatch)
    check("exact_ff_and_existing_index_preservation_guards_retained",
        '"merge", "--ff-only", SOURCE' in d and 'assert all(new_index.get(k) == v for k, v in old_index.items())' in d
        and 'assert set(new_index) == set(old_index) | {p.encode() for p in paths}' in d)
    check("no_actual_baseline_deploy_dispatch_or_release",sorted(p.name for p in OUT.iterdir())==["deploy_nsd.py","dispatch_nsd_once.py","prepare_nsd_baseline.py"])
    validation={"status":"DISABLED_NSD_DEPLOYMENT_TEMPLATE_PROSPECTIVE_CHECKS_PASS","recorded_at":datetime.now(timezone.utc).isoformat(),
        "checks":checks,"check_count":len(checks),"native":"NOT_RUN","resources":"NOT_RUN","actual_deploy_dispatch":False,
        "scope":"Compile/import, actual default-NOP and DRAFT-refusal, exact inherited FF/protected/gates/baseline algorithms and controlled metadata/CPU-base/production-review additions only. No old proof rerun, SSH/GPU, actual admission/request/snapshot or source/index/SERVERS/queue mutation."}
    save("software_validation.json",validation)
    save("change_manifest.json",{"producer_deployment_FROZEN":ref(OLD/"psc_deployment_prepare/FROZEN.json"),
        "producer_deployment_review":ref(OLD/"psc_deployment_helper_independent_review.json"),
        "producer_dispatch":ref(OLD/"dispatch_psc_once.py"),"dispatcher_reference_scope":"Historical successful root dispatcher; current copy separately pending independent review.",
        "builder":ref(Path(__file__)),"changes":changes})
    save("README.md","Disabled NSD deployment/baseline/dispatch templates. Root must create separately reviewed activation copies; frozen drafts must not be edited. Actual peer-reviewed all-four native/resources, canonical M232 receipt and then fresh baseline snapshot precede FF/runtime. Source f625 is a direct exact9-addition child of 0ccc. Existing user28 bytes/index entries/old roots including PSC/HVD remain protected. Runtime CPU uses hash-verified original base6c80 only, hides CUDA and never trains; expired SERVERS PSC shim is bypassed without renewal. Separate ff/runtime/switch only. Switch requires reviewed actual production graph and changes only remote_code_root; root separately changes the explicit reviewed rendered conda_source pointer. Dispatch requires that exact new shim, canonical admission/single eligible NSD task/original GPU0/20GB/max1/three locks/progress; /proc replaces kill0. No actual admission, snapshot, request, release, deploy, queue or training was created.\n")
    save("preparation.json",{"status":"DISABLED_NSD_DEPLOYMENT_HELPERS_PENDING_INDEPENDENT_REVIEW","owner":owner,"author_thread_id":AUTHOR,
        "source_commit":SOURCE,"source_parent_commit":BASE,"candidate_id":"hierarchy-native-spatial-dirichlet-composition","experiment_id":"M232-NSD",
        "source_proof":ref(ROOT/"pipeline/diagnostic_bundles/tick_c706ca80/nsd_compatible_source/compatible_source_version.json"),
        "runtime_root":m.NEW_ROOT,"current_runtime_root":m.OLD_ROOT,"CPU_base":CPU_BASE,"CPU_base_sha256":CPU_SHA,
        "draft_execution_disabled":True,"actual_admission_or_operations_created":False,"independent_review":"PENDING_EXTERNAL"})
    files={p.name:sha(p) for p in sorted(OUT.iterdir()) if p.is_file()}
    save("FROZEN.json",{"status":"AUTHOR_FROZEN_DISABLED_NSD_DEPLOYMENT_HELPERS_PENDING_REVIEW",
        "recorded_at":datetime.now(timezone.utc).isoformat(),"owner":owner,"author_thread_id":AUTHOR,"files":files,
        "draft_execution_disabled":True,"author_will_not_write_further":True,"actual_operations_created":False})
    assert all(sha(OUT/n)==v for n,v in read(OUT/"FROZEN.json")["files"].items())
    print(json.dumps({"FROZEN":ref(OUT/"FROZEN.json"),"preparation":ref(OUT/"preparation.json"),"software_validation":ref(OUT/"software_validation.json"),"check_count":len(checks),"author_writes_stopped":True},indent=2))
if __name__=="__main__":main()
