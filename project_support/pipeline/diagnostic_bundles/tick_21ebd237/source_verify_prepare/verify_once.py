"""Root-only current-owner read-only verification; default NOP; no sync or launch."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,shlex,subprocess,sys
ROOT=Path("D:/project/cluster_project");HERE=Path(__file__).resolve().parent
KEYS=("token","thread_id","generated_at","deadline_at","context_sha256","pending_sha256")
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with p.open("x",encoding="utf-8",newline="\n") as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write("\n")
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def guard(b):
 assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS")=="0"
 raw=read(ROOT/"pipeline/headless/.foreground.lockdir/owner.json");owner={k:raw[k] for k in KEYS};assert owner==b["owner"] and owner["thread_id"]==os.environ.get("CODEX_THREAD_ID")
 assert (datetime.fromisoformat(owner["deadline_at"])-datetime.now(timezone.utc)).total_seconds()>100
 mode=read(ROOT/"pipeline/execution_mode.json");assert mode["mode"]=="foreground" and mode["target_thread_id"]==owner["thread_id"]
 for name,key in ((".tick_context.json","context_sha256"),(".tick_context_state.next.json","pending_sha256")):assert sha(ROOT/"pipeline/headless"/name)==owner[key]
 frozen=read(HERE/"FROZEN.json");assert frozen["owner"]==owner
 for name,digest in frozen["files"].items():assert sha(HERE/name)==digest
 for item in b["anchors"].values():assert sha(item["path"])==item["sha256"]
 assert not Path(b["previous_dispatch_intent_path"]).exists(),"Prior dispatch intent exists; reconcile"
 assert sha(ROOT/"SERVERS.yaml")==b["previous_SERVERS_sha256"]
 return owner
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--execute-root",action="store_true");parser.add_argument("--review",type=Path);parser.add_argument("--review-sha256");a=parser.parse_args()
 if not a.execute_root:print(json.dumps({"status":"DEFAULT_NOP_NO_SSH_GIT_SYNC_LAUNCH_OR_SHARED_MUTATION"}));return
 b=read(HERE/"owner_binding.json");owner=guard(b)
 assert a.review and a.review.resolve().is_relative_to(ROOT) and sha(a.review)==a.review_sha256
 peer=read(a.review);assert peer["passed"] is True and peer["owner"]==owner and peer["material_concerns"]==[]
 assert peer["reviewer_thread_id"] not in (owner["thread_id"],"/root","/root/actual_chain_fast")
 assert peer["FROZEN_sha256"]==sha(HERE/"FROZEN.json")
 execution=HERE.parent/"source_verify_execution";execution.mkdir(exist_ok=True);intent=execution/"verify_intent.json";out=execution/"verify_actual.json"
 assert not intent.exists() and not out.exists(),"Existing/uncertain verification: reconcile, never replay"
 old=read(b["historical_sync_path"]);assert old["owner"]==b["historical_sync_owner"] and old["passed"] is True and old["source_commit"]==b["source_commit"]
 protected=["SERVERS.yaml","pipeline/queue.json","pipeline/running.json","pipeline/research_work.json","pipeline/goal.json","pipeline/closure_policy.json"]
 before={x:sha(ROOT/x) for x in protected}
 resolver=load("rve_retained_real_resolver",b["source_resolver_path"]);detached=resolver.verify()
 si=load("rve_canonical_source_integrity",b["anchors"]["source_integrity"]["path"])
 calls=[]
 def ssh(host,user,command):
  guard(b);assert (host,user)==("192.168.1.115","songcl")
  prefix='test "$(hostname)" = dl04-MS-7E06 && test "$(id -u)" = 1001 && GIT_OPTIONAL_LOCKS=0 GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" '
  process=subprocess.Popen(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=8","songcl@192.168.1.115",prefix+command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8",errors="replace")
  record={"ordinal":len(calls),"local_ssh_pid":process.pid,"command_sha256":hashlib.sha256(command.encode()).hexdigest(),"certainty":"uncertain"};calls.append(record)
  try:stdout,stderr=process.communicate(timeout=45)
  except subprocess.TimeoutExpired:raise RuntimeError("Read-only SSH uncertain; preserve PID "+str(process.pid)+"; no signal or replay")
  assert len(stdout.encode())<131072;record.update(certainty="terminal",returncode=process.returncode,stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr=stderr[:2000]);assert process.returncode==0,stderr[:2000]
  return stdout
 server={"host":"192.168.1.115","user":"songcl","remote_code_root":b["runtime_root"],"python":"/home/songcl/.conda/envs/project_cluster/bin/python"}
 mappings=[["/home/songcl/data/data","/home/songcl/data/data"],["/home/songcl/3dres/project/cluster_project/Checkpoints","/data/songcl/Project/Cluster_project/Cluster_checkpoints"]]
 save(intent,{"owner":owner,"recorded_at":datetime.now(timezone.utc).isoformat(),"FROZEN_sha256":sha(HERE/"FROZEN.json"),"review_sha256":a.review_sha256,"read_only":True,"no_replay":True})
 result={"owner":owner,"recorded_at":datetime.now(timezone.utc).isoformat(),"kind":"CURRENT_READONLY_VERIFICATION_REUSE_OLD_SYNC_NOT_NEW_SYNC","certainty":"uncertain","passed":False,"historical_sync":{"path":b["historical_sync_path"],"sha256":b["historical_sync_sha256"],"owner":old["owner"],"not_relabelled_current_owner":True},"SSH_calls":calls,"training_started":False,"GPU_compute":False,"signals_sent":False,"new_sync_performed":False,"Git_mutations":False}
 try:
  si.verify_git(server,b["source_commit"],mappings,ssh)
  program=(HERE/"verify_remote.py.txt").read_text(encoding="utf-8")
  payload=json.dumps({k:b[k] for k in ('owner', 'source_commit', 'runtime_root', 'source_files_exact9', 'config', 'canonical_preview_sha256', 'canonical_preview_bytes_base64', 'previous_producer_stage', 'previous_production_stage', 'previous_producer_files', 'previous_production_files', 'previous_marker')},separators=(",",":"));full="import io,sys;sys.stdin=io.StringIO("+repr(payload)+")\n"+program
  current=json.loads(ssh(server["host"],server["user"],"CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -B -c "+shlex.quote(full)))
  si.verify_git(server,b["source_commit"],mappings,ssh)
  assert resolver.verify()==detached;assert all(sha(ROOT/x)==v for x,v in before.items());guard(b)
  result.update(passed=True,certainty="terminal",source_commit=b["source_commit"],runtime_root=b["runtime_root"],runtime_code_commit=current["runtime_HEAD"],current_remote=current,actual=current,source_verified=True,source_integrity_before_after=True,canonical_source_integrity_current=True,main_index_user28_r0nine_preserved=True,lifecycle_unchanged=True,detached_checkout=detached,protected_before_after_sha256=before,config_is_original_or_exact_canonical_preview=True,old_ee6_stage_reconciled=True,previous_production_reconciled=True,prior_production_consumed=False,previous_conda_source=b["previous_conda_source"])
 except BaseException as e:result.update(error_type=type(e).__name__,error=str(e));save(out,result);raise
 save(out,result);print(json.dumps({"path":str(out),"sha256":sha(out),"kind":result["kind"],"passed":True}))
if __name__=="__main__":main()
