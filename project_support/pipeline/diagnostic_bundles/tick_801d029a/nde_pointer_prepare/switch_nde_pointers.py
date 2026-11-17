"""Default NOP, disabled paired runtime/shim switch; never deploy or launch."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,os,re,subprocess,sys,yaml
ROOT=Path("D:/project/cluster_project");HERE=Path(__file__).resolve().parent
DRAFT_EXECUTION_DISABLED = True
EXPECTED_OWNER = {'token': '801d029aa45243ee841454512bcf0b84', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-08T14:23:40.346565+00:00', 'deadline_at': '2026-11-08T15:23:40.346565+00:00', 'context_sha256': 'b9ef46219c253d45bcfeb260172550ea36ccff49567e7bb26b45b498b633ea69', 'pending_sha256': '80d5927f103adce942e5c0ca08f4a8fd8001c25cf087823650c205dca8ada131'}
EXPECTED_SOURCES = {'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/__init__.py': '327bf439ad68108b0493d337a2097dc83626e71af869b2536408232f197eda62', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/backbone.py': '1eb4ac3483961e708c23b0abad396c181dbf38c56fcca559d88b9622af46bafd', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/dec.py': 'ec21d503979fd95c87fa63280948b8a5e9b9f300383a99a53038eb081440ad54', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/hier_postprocess.py': '2f802153fba7483c84cdb8b778108e0edadc44c83d4b2e266094d84a0b315ac5', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/loss.py': 'c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/network.py': '5a77eb852b3c6e5de2804d80a2c7a16504f1fd8a57aa94dc6045d9f35587625d', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/sample_model.py': 'b22319d5c3958a9a893cb6c2134dd7e124778610aba7e8b9c90647560c806999', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/distribution_embedding.py': '4acbbc28748425d37959a5edb6dcbb68f9a61859d693a9222c14ac96e38a877f'}
SOURCE = '0747f6acec1c61018ec99acf2efa5329c9b3523c'
BASE = 'f6257de79148581334ee495e6e2d60ccb525457c'
CID = 'hierarchy-native-distribution-embedding-composition'
CONFIG = 'configs/Quard/ctf_hcg_csort_nde/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde.yaml'
OLD_ROOT = '/data/songcl/Project/Cluster_project/Cluster_nsd_20261107'
NEW_ROOT = '/data/songcl/Project/Cluster_project/Cluster_nsd_20261107'
OLD_SHIM = '/data/songcl/Project/Cluster_project/pipeline/runtime/nsd_path_prod_a6a255d1/conda_source.sh'
NEW_SHIM = '/data/songcl/Project/Cluster_project/pipeline/runtime/nde_path_prod_801d029a/conda_source.sh'
UUID="GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
KEYS=("token","thread_id","generated_at","deadline_at","context_sha256","pending_sha256")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def require(v,message):
    if not v:raise ValueError(message)
def guard():
    require(not DRAFT_EXECUTION_DISABLED,"Disabled pointer draft; separately reviewed root activation required")
    o=read(ROOT/"pipeline/headless/.foreground.lockdir/owner.json")
    require({k:o[k] for k in KEYS}==EXPECTED_OWNER and os.environ.get("CODEX_THREAD_ID")==o["thread_id"],"Owner mismatch")
    require(sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS")=="0","Bytecode/index guard")
    require((datetime.fromisoformat(o["deadline_at"])-datetime.now(timezone.utc)).total_seconds()>60,"Owner deadline")
    require(sha(ROOT/"pipeline/headless/.tick_context.json")==o["context_sha256"] and sha(ROOT/"pipeline/headless/.tick_context_state.next.json")==o["pending_sha256"],"Context changed")
    return o
def paired_bytes(raw,root,shim):
    require(root==NEW_ROOT and shim==NEW_SHIM,"Foreign target pointers")
    before=yaml.safe_load(raw);s=before["servers"]["server-4"]
    require(s["remote_code_root"]==OLD_ROOT and s["conda_source"]==OLD_SHIM,"Unexpected original pointer pair")
    require(s["host"]=="192.168.1.115" and s["user"]=="songcl" and s["expected_hostname"]=="dl04-MS-7E06","Pinned server mismatch")
    require(s["allowed_gpus"]==[0] and s["max_tasks_per_gpu"]==1 and s["allow_external_overlay"] is True and s["task_memory_mb"]==20000,"Resource policy changed")
    require(str(s["expected_gpu_uuids"].get("0",s["expected_gpu_uuids"].get(0)))==UUID and s["conda_env"]=="project_cluster","UUID/environment changed")
    require(raw.count(OLD_ROOT.encode())==1 and raw.count(OLD_SHIM.encode())==1,"Pointers not unique byte spans")
    changed=raw.replace(OLD_ROOT.encode(),root.encode(),1).replace(OLD_SHIM.encode(),shim.encode(),1)
    expected=copy.deepcopy(before);expected["servers"]["server-4"].update(remote_code_root=root,conda_source=shim)
    require(yaml.safe_load(changed)==expected,"Other configuration changed")
    return changed
def validate_production(value,peer):
    require(value["kind"]=="PRODUCTION_PATH_INSTALLED_NO_TRAINER_LAUNCHED" and value["owner"]==EXPECTED_OWNER,"Actual production identity")
    b=value["binding"]
    require(b["kind"]=="production" and b["source_commit"]==SOURCE and b["runtime_root"]==NEW_ROOT and value["shim"]==NEW_SHIM,"Production source/pointers")
    require(b["source_files"]==EXPECTED_SOURCES and b["stage"]==str(Path(NEW_SHIM).parent).replace("\\","/"),"Exact source/stage binding")
    require(re.fullmatch(r"[0-9a-f]{64}",value["shim_sha256"]) is not None and value["files"]["conda_source.sh"]==value["shim_sha256"],"Actual shim hash graph")
    require(b["physical_gpu"]==0 and b["expected_gpu_uuid"]==UUID and b["required_free_memory_mib"]==20000 and b["max_project_tasks"]==1,"Production resource binding")
    require(b["argv"]==["tools/train.py",CONFIG,"--gpu_ids","0","--num_gpus","1"],"Canonical argv changed")
    require([x["path"] for x in b["lock_files"]]==["/tmp/cluster_project_gpu0_"+x+".lock" for x in ("training","diagnostic","exclusive")],"Three original locks")
    require(value["training_launch_or_GPU_use"] is False and value["one_shot_consumed"] is False,"Production already consumed")
    require(peer["passed"] is True and peer.get("material_concerns",[])==[],"Production peer review incomplete")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute-root",action="store_true")
    names=("receipt","receipt-sha256","production-result","production-result-sha256","production-review","production-review-sha256",
        "runtime-proof","runtime-proof-sha256","ff-result","ff-result-sha256","protected-baseline","baseline-sha256",
        "activation-review","activation-review-sha256")
    for name in names:p.add_argument("--"+name)
    a=p.parse_args()
    if not a.execute_root:
        print(json.dumps({"status":"DEFAULT_NOP_NO_SERVERS_OR_SOURCE_MUTATION","draft_execution_disabled":DRAFT_EXECUTION_DISABLED}));return
    guard();require(all(getattr(a,n.replace("-","_")) for n in names),"Actual paths and hashes required")
    paths={}
    for name in ("receipt","production-result","production-review","runtime-proof","ff-result","protected-baseline","activation-review"):
        path=Path(getattr(a,name.replace("-","_"))).resolve()
        hasharg="baseline_sha256" if name=="protected-baseline" else name.replace("-","_")+"_sha256"
        require(path.is_relative_to(ROOT.resolve()) and sha(path)==getattr(a,hasharg),"Actual input hash/path: "+name);paths[name]=path
    activation=read(paths["activation-review"])
    require(activation["passed"] is True and activation["helper_sha256"]==sha(__file__) and activation["owner"]==EXPECTED_OWNER,"Actual helper activation review")
    require(activation["reviewer_thread_id"]!=EXPECTED_OWNER["thread_id"],"Independent helper review required")
    production=read(paths["production-result"]);peer=read(paths["production-review"])
    validate_production(production,peer)
    require(peer["production_result_sha256"]==sha(paths["production-result"]),"Production review hash binding")
    receipt=read(paths["receipt"])
    require(all(receipt.get(k)==v for k,v in {"id":"M233-NDE","candidate_id":CID,"code_commit":SOURCE,"config":CONFIG,"profile":"experiment_first"}.items()),"Canonical NSD receipt")
    runtime=read(paths["runtime-proof"]);ff=read(paths["ff-result"]);baseline=read(paths["protected-baseline"])
    require(runtime["owner"]==ff["owner"]==EXPECTED_OWNER and runtime["local_head"]==ff["local_head"]==SOURCE,"Deployment owner/source")
    require(runtime["runtime_root"]==NEW_ROOT and runtime["runtime_code_commit"]==SOURCE and all(runtime[k] is True for k in ("source_verified","old_roots_preserved","YAML_mapping_verified")),"Actual runtime proof")
    require(ff["prior_tree_and_index_entries_preserved"] is True and ff["exact9_additions"] is True,"FF protection")
    require(baseline["main_head"]==BASE and len(baseline["dirty_files"])==28,"Protected baseline")
    sys.path.insert(0,"C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
    import closure,pipeline_monitor as monitor
    closure.admission(ROOT,{"id":"M233-NDE","candidate_id":CID,"code_commit":SOURCE,"config":CONFIG,
        "profile":"experiment_first","admission_receipt":paths["receipt"].relative_to(ROOT).as_posix(),"requires_exclusive_ownership":False})
    lock=monitor.acquire_lock(str(ROOT));require(lock is not None,"Monitor lock unavailable")
    try:
        git=["C:/Program Files (x86)/Git/cmd/git.exe","--no-optional-locks","-c","core.fsmonitor=false","-C",str(ROOT/"Cluster")]
        def query(*args):return subprocess.check_output(git+list(args),env=dict(os.environ,GIT_OPTIONAL_LOCKS="0",GIT_TERMINAL_PROMPT="0"),timeout=15)
        def protected():
            guard();require(query("rev-parse","HEAD").decode().strip()==SOURCE,"Main changed")
            index=Path(query("rev-parse","--git-path","index").decode().strip())
            if not index.is_absolute():index=ROOT/"Cluster"/index
            require(sha(index)==ff["index_sha256_after"],"Index changed")
            require(hashlib.sha256(query("ls-files","--stage","-z")).hexdigest()==ff["index_entries_sha256_after"],"Index entries changed")
            require(all(sha(ROOT/"Cluster"/n)==d for n,d in baseline["dirty_files"].items()),"User files changed")
            require(all(sha(ROOT/n)==d for n,d in baseline["protected_project_files"].items() if n!="SERVERS.yaml"),"Protected lifecycle changed")
            require(all(sha(path)==getattr(a,"baseline_sha256" if name=="protected-baseline" else name.replace("-","_")+"_sha256") for name,path in paths.items()),"Actual evidence changed")
        protected();server=ROOT/"SERVERS.yaml";raw=server.read_bytes()
        require(hashlib.sha256(raw).hexdigest()==baseline["protected_project_files"]["SERVERS.yaml"],"SERVERS baseline changed")
        changed=paired_bytes(raw,production["binding"]["runtime_root"],production["shim"])
        require(not(HERE/"switch_intent.json").exists() and not(HERE/"switch_result.json").exists(),"Prior attempt: reconcile, never replay")
        def save(path,value):
            with path.open("x",encoding="utf8") as f:json.dump(value,f,indent=2);f.write("\n")
        save(HERE/"switch_intent.json",{"owner":EXPECTED_OWNER,"inputs":{k:{"path":str(v),"sha256":sha(v)} for k,v in paths.items()},"SERVERS_before_sha256":hashlib.sha256(raw).hexdigest(),"paired_change":True,"no_replay":True})
        temp=ROOT/"SERVERS.yaml.nde_pointer_801d029a.tmp"
        with temp.open("xb") as f:f.write(changed);f.flush();os.fsync(f.fileno())
        protected();require(server.read_bytes()==raw,"SERVERS changed during operation");os.replace(temp,server)
        require(server.read_bytes()==changed,"Atomic paired switch bytes differ");protected()
        save(HERE/"switch_result.json",{"owner":EXPECTED_OWNER,"only_runtime_and_conda_source_changed":True,
            "runtime_root":NEW_ROOT,"conda_source":NEW_SHIM,"SERVERS_sha256":sha(server),"training_started":False,"SSH_GPU":False})
        print(json.dumps({"status":"PAIRED_POINTER_SWITCH_COMPLETED_NO_LAUNCH","SERVERS_sha256":sha(server)}))
    finally:lock.close()
if __name__=="__main__":main()
