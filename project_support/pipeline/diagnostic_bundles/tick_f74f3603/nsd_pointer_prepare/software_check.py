"""Pure and disabled-entry checks; never write actual SERVERS or run main."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,importlib.util,json,subprocess,sys
H=Path(__file__).resolve().parent;R=Path("D:/project/cluster_project")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def save(n,v):
    with (H/n).open("x",encoding="utf8") as f:json.dump(v,f,indent=2);f.write("\n")
def ref(p):return {"path":Path(p).relative_to(R).as_posix(),"sha256":sha(p)}
def main():
    negative=H.parent/"nsd_deployment_independent_review.json"
    protected=[R/"SERVERS.yaml",negative,H.parent/"nsd_deployment_prepare/FROZEN.json",
        H.parent/"nsd_result_prepare/FROZEN.json",H.parent/"nsd_path_production_prepare/FROZEN.json",
        H.parent/"nsd_path_production_transport/FROZEN.json"]
    before={str(p):sha(p) for p in protected};checks=[]
    def check(n,v):
        assert v,n
        checks.append({"name":n,"passed":True})
    for p in H.glob("*.py"):compile(p.read_bytes(),str(p),"exec")
    check("all_new_Python_compile",True)
    spec=importlib.util.spec_from_file_location("disabled_paired_pointer",H/"switch_nsd_pointers.py")
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    raw=(R/"SERVERS.yaml").read_bytes()
    changed=m.paired_bytes(raw,m.NEW_ROOT,m.NEW_SHIM)
    check("pure_current_bytes_change_both_pointers",m.NEW_ROOT.encode() in changed and m.NEW_SHIM.encode() in changed and m.OLD_ROOT.encode() not in changed and m.OLD_SHIM.encode() not in changed)
    check("all_other_original_bytes_exact",changed.replace(m.NEW_ROOT.encode(),m.OLD_ROOT.encode()).replace(m.NEW_SHIM.encode(),m.OLD_SHIM.encode())==raw)
    crlf=raw.replace(b"\r\n",b"\n").replace(b"\n",b"\r\n")
    out=m.paired_bytes(crlf,m.NEW_ROOT,m.NEW_SHIM)
    check("CRLF_and_comments_preserved",out.replace(m.NEW_ROOT.encode(),m.OLD_ROOT.encode()).replace(m.NEW_SHIM.encode(),m.OLD_SHIM.encode())==crlf)
    for label,body,root,shim in (
        ("foreign_target",raw,m.NEW_ROOT,m.OLD_SHIM),
        ("partial_prior_root_switch",raw.replace(m.OLD_ROOT.encode(),m.NEW_ROOT.encode()),m.NEW_ROOT,m.NEW_SHIM),
        ("partial_prior_shim_switch",raw.replace(m.OLD_SHIM.encode(),m.NEW_SHIM.encode()),m.NEW_ROOT,m.NEW_SHIM),
        ("duplicate_byte_span",raw+b"\n# "+m.OLD_SHIM.encode(),m.NEW_ROOT,m.NEW_SHIM),
        ("budget_change",raw.replace(b"task_memory_mb: 20000",b"task_memory_mb: 18000"),m.NEW_ROOT,m.NEW_SHIM)):
        try:m.paired_bytes(body,root,shim)
        except ValueError:check(label+"_refused",True)
        else:raise AssertionError(label)
    prod={"kind":"PRODUCTION_PATH_INSTALLED_NO_TRAINER_LAUNCHED","owner":m.EXPECTED_OWNER,
        "shim":m.NEW_SHIM,"shim_sha256":"a"*64,"files":{"conda_source.sh":"a"*64},
        "training_launch_or_GPU_use":False,"one_shot_consumed":False,
        "binding":{"kind":"production","source_commit":m.SOURCE,"runtime_root":m.NEW_ROOT,
            "source_files":m.EXPECTED_SOURCES,"stage":m.NEW_SHIM.rsplit("/",1)[0],
            "physical_gpu":0,"expected_gpu_uuid":m.UUID,"required_free_memory_mib":20000,"max_project_tasks":1,
            "argv":["tools/train.py",m.CONFIG,"--gpu_ids","0","--num_gpus","1"],
            "lock_files":[{"path":"/tmp/cluster_project_gpu0_"+x+".lock"} for x in ("training","diagnostic","exclusive")]}}
    peer={"passed":True,"material_concerns":[]}
    m.validate_production(prod,peer);check("clearly_synthetic_in_memory_production_identity_fixture",True)
    for label,key,value in (("source","source_commit",m.BASE),("UUID","expected_gpu_uuid","foreign"),
        ("memory","required_free_memory_mib",18000),("source8","source_files",{}),("runtime","runtime_root",m.OLD_ROOT)):
        bad=copy.deepcopy(prod);bad["binding"][key]=value
        try:m.validate_production(bad,peer)
        except ValueError:check(label+"_production_refused",True)
        else:raise AssertionError(label)
    bad=copy.deepcopy(prod);bad["one_shot_consumed"]=True
    try:m.validate_production(bad,peer)
    except ValueError:check("consumed_marker_production_refused",True)
    else:raise AssertionError("Consumed production accepted")
    try:m.guard()
    except ValueError as e:check("actual_DRAFT_guard_refuses_before_owner_IO",str(e).startswith("Disabled pointer draft"))
    else:raise AssertionError("Draft enabled")
    nop=subprocess.run([sys.executable,"-B","-X","utf8",str(H/"switch_nsd_pointers.py")],capture_output=True,text=True,timeout=10)
    check("actual_default_NOP",nop.returncode==0 and json.loads(nop.stdout)["status"]=="DEFAULT_NOP_NO_SERVERS_OR_SOURCE_MUTATION")
    text=(H/"switch_nsd_pointers.py").read_text()
    check("actual_evidence_hashes_and_activation_review_required",all(x in text for x in (
        'activation["helper_sha256"]==sha(__file__)','peer["production_result_sha256"]==sha(paths["production-result"])',
        "closure.admission(", '"old_roots_preserved"',
        'ff["index_sha256_after"]','baseline["protected_project_files"]','os.replace(temp,server)')))
    check("all_old_frozen_negative_review_and_SERVERS_bytes_preserved",all(sha(Path(p))==d for p,d in before.items()))
    check("no_actual_intent_temp_or_result",not(H/"switch_intent.json").exists() and not(H/"switch_result.json").exists() and not(R/"SERVERS.yaml.nsd_pointer_f74f3603.tmp").exists())
    save("software_validation.json",{"status":"DISABLED_PAIRED_POINTER_SOFTWARE_CHECKS_PASS_ONLY",
        "recorded_at":datetime.now(timezone.utc).isoformat(),"checks":checks,"check_count":len(checks),
        "synthetic_fixture_scope":"In-memory software identity fixtures only; not actual production evidence. Main was never executed.",
        "actual_SERVERS_changed":False,"SSH_GPU":False,"admission_deploy_dispatch":"NOT_RUN"})
    save("README.md","Separate disabled paired-pointer addendum, superseding the old root-only phase switch after separate actual activation review. Frozen deployment negative review remains unchanged. Default NOP/DRAFT=True. A future reviewed root activation consumes actual canonical NSD receipt, production result and peer review, runtime/FF proofs and after-admission protected baseline, all with CLI SHA anchors, plus independent activation review binding the exact helper SHA and owner. It verifies actual local main/index/user28/lifecycle and atomically replaces both runtime and conda_source pointer bytes, preserving all other bytes/parsed settings. Existing partial pointer switches and prior intents refuse; no replay, deployment, SSH, GPU, queue or training. Helper activation review schema: passed=true, helper_sha256, exact owner, reviewer_thread_id distinct from root. No actual input, authorization or PASS is synthesized here.\n")
    save("preparation.json",{"status":"DISABLED_PAIRED_POINTER_ADDENDUM_PENDING_INDEPENDENT_REVIEW",
        "owner":m.EXPECTED_OWNER,"source_commit":m.SOURCE,"source_parent_commit":m.BASE,
        "supersedes":"Old deployment phase switch only; retains FF/runtime and requires real production review before paired pointers.",
        "preserved_negative_review":ref(negative),"existing_deployment_FROZEN":ref(protected[2]),
        "helper":ref(H/"switch_nsd_pointers.py"),"draft_execution_disabled":True,
        "actual_pointers_written":False,"actual_admission_or_production_evidence_created":False})
    files={p.name:sha(p) for p in sorted(H.iterdir()) if p.is_file()}
    save("FROZEN.json",{"status":"AUTHOR_FROZEN_DISABLED_PAIRED_POINTER_ADDENDUM_PENDING_REVIEW",
        "recorded_at":datetime.now(timezone.utc).isoformat(),"owner":m.EXPECTED_OWNER,"files":files,
        "author_will_not_write_further":True,"actual_operations":False,"draft_execution_disabled":True})
    assert all(sha(H/n)==d for n,d in read(H/"FROZEN.json")["files"].items())
    print(json.dumps({"FROZEN":ref(H/"FROZEN.json"),"helper":ref(H/"switch_nsd_pointers.py"),
        "validation":ref(H/"software_validation.json"),"check_count":len(checks),"author_writes_stopped":True},indent=2))
if __name__=="__main__":main()
