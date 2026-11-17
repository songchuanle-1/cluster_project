"""Default NOP. Root-only exact peer-confirmed M234 crash canonical archival."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import argparse,copy,hashlib,json,math,os,re,subprocess,sys
ROOT=Path("D:/project/cluster_project");HERE=Path(__file__).resolve().parent;TICK=HERE.parent
KEYS=("token","thread_id","generated_at","deadline_at","context_sha256","pending_sha256")
def read(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def save(p,v):
 with p.open("x",encoding="utf-8",newline="\n") as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write("\n")
def guard(meta):
 assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS")=="0"
 raw=read(ROOT/"pipeline/headless/.foreground.lockdir/owner.json");owner={k:raw[k] for k in KEYS};assert owner==meta["owner"] and owner["thread_id"]==os.environ.get("CODEX_THREAD_ID")
 assert (datetime.fromisoformat(owner["deadline_at"])-datetime.now(timezone.utc)).total_seconds()>60
 mode=read(ROOT/"pipeline/execution_mode.json");assert mode["mode"]=="foreground" and mode["target_thread_id"]==owner["thread_id"]
 for n,k in ((".tick_context.json","context_sha256"),(".tick_context_state.next.json","pending_sha256")):assert sha(ROOT/"pipeline/headless"/n)==owner[k]
 frozen=read(HERE/"FROZEN.json");assert frozen["owner"]==owner
 for n,h in frozen["files"].items():assert sha(HERE/n)==h,n
 for a in meta["anchors"].values():assert sha(a["path"])==a["sha256"],a["path"]
 return owner
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--execute-root",action="store_true");parser.add_argument("--terminal-review-sha256");parser.add_argument("--archive-review",type=Path);parser.add_argument("--archive-review-sha256");a=parser.parse_args()
 if not a.execute_root:print(json.dumps({"status":"DEFAULT_NOP_NO_SSH_SCP_ARCHIVE_OR_SHARED_MUTATION"}));return
 m=read(HERE/"binding.json");owner=guard(m);assert a.terminal_review_sha256==m["anchors"]["terminal_review"]["sha256"]
 assert a.archive_review and a.archive_review.resolve().is_relative_to(ROOT) and sha(a.archive_review)==a.archive_review_sha256
 source_peer=read(a.archive_review);assert source_peer["owner"]==owner and source_peer["passed"] is True and source_peer["material_concerns"]==[] and source_peer["FROZEN_sha256"]==sha(HERE/"FROZEN.json")
 assert source_peer["reviewer_thread_id"] not in (owner["thread_id"],"/root","/root/actual_chain_fast")
 assert source_peer["reconcile_actual_sha256"]==m["anchors"]["actual"]["sha256"] and source_peer["terminal_review_sha256"]==a.terminal_review_sha256
 actual=read(m["anchors"]["actual"]["path"]);peer=read(m["anchors"]["terminal_review"]["path"]);obs=actual["observation"]
 assert actual["owner"]==owner and actual["passed"] is True and actual["returncode"]==0 and actual["certainty"]=="terminal"
 assert peer["owner"]==owner and peer["passed"] is True and peer["material_concerns"]==[] and peer["reconcile_actual_sha256"]==m["anchors"]["actual"]["sha256"]
 assert peer["reviewer_thread_id"] not in (owner["thread_id"],"/root","/root/actual_chain_fast") and peer["classification_supported"]=="crashed" and peer["process_absent"] is True
 proof=read(m["anchors"]["historical_dispatch_proof"]["path"]);process=obs["process"]
 assert process["pid"]==proof["pid"]==3813109 and process["expected_start_ticks"]==proof["start_ticks"] and process["exists"] is False and process["alive"] is False and obs["project_trainers"]==[]
 assert obs["hostname"]=="dl04-MS-7E06" and obs["uid"]==1001 and obs["source_commit"]==proof["source_commit"]==m["source_commit"] and obs["runtime_root"]==proof["runtime_root"] and obs["source_and_producer_verified"] is True
 assert obs["marker_consumed"] is True and obs["marker_sha256"]==proof["marker_sha256"]
 stdout_info=obs["logs"]["registered_stdout"];native_info=obs["logs"]["actual_native_logger"]
 assert stdout_info["path"]==proof["log"] and stdout_info["error_markers"]["Traceback"] is True and stdout_info["error_markers"]["RuntimeError"] is True and stdout_info["error_markers"]["CUDA out of memory"] is False
 assert "DataLoader worker (pid 3815203) is killed by signal: Segmentation fault" in stdout_info["error_excerpt"]
 assert not any(stdout_info["terminal_markers"].values())
 sys.path.insert(0,str(Path(m["anchors"]["canonical_monitor"]["path"]).parent));import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard(m);queue=monitor.load_queue(str(ROOT));matches=[(server,t) for server,ts in queue["gpu_queues"].items() for t in ts if t.get("id")==m["experiment_id"]];assert len(matches)==1;server,task=matches[0]
  assert server=="server-4" and task["status"]=="running" and int(task["pid"])==proof["pid"] and task["log"]==proof["log"] and task["code_commit"]==m["source_commit"] and str(task["gpu"])=="0" and task["launch_verified"] is True
  assert task["config"]==proof["actual_identity_capture"]["argv"][2]
  journal=ROOT/"pipeline/archive_pending"/(hashlib.sha256(m["experiment_id"].encode()).hexdigest()+".json");assert not journal.exists(),"Existing pending archive: use canonical recover, never re-finalize"
  prior_exp=monitor.load_experiment(str(ROOT),m["experiment_id"]);assert prior_exp and prior_exp["status"]=="running" and int(prior_exp["pid"])==proof["pid"] and prior_exp["log"]==proof["log"]
  execution=TICK/"archive_execution_v2";execution.mkdir(exist_ok=True);intent=execution/"archive_intent.json";result_path=execution/"archive_actual.json";assert not intent.exists() and not result_path.exists(),"Existing or uncertain archive; reconcile without replay"
  baseline=read(m["anchors"]["preservation_baseline"]["path"])
  protected=[ROOT/n for n in ("SERVERS.yaml","pipeline/research_work.json","pipeline/codex_memory.md","pipeline/goal.json","pipeline/closure_policy.json","pipeline/deathwatch.json","pipeline/experiments/M206-CGCA.json","pipeline/experiments/M227-LFT.json")]
  protected += [ROOT/"Cluster"/n for n in {**baseline["dirty_files_exact28"],**baseline["working_tree_r0_files_exact9"]}]
  protected += [ROOT/"Cluster/.git"/n for n in ("index","HEAD")]
  protected_hashes={str(q):sha(q) for q in protected if q.is_file()};before_running=monitor.load_running(str(ROOT));expected_queue=copy.deepcopy(queue);expected_queue["gpu_queues"][server]=[t for t in expected_queue["gpu_queues"][server] if t.get("id")!=m["experiment_id"]]
  work=read(ROOT/"pipeline/research_work.json");candidate=next(c for c in work["candidates"] if c.get("id")==m["candidate_id"]);revision=next(x for x in candidate["revision_history"] if x["revision"]==1);assert canonical(revision)==m["immutable_revision_sha256"]
  save(intent,{"owner":owner,"recorded_at":datetime.now(timezone.utc).isoformat(),"FROZEN_sha256":sha(HERE/"FROZEN.json"),"actual_sha256":m["anchors"]["actual"]["sha256"],"terminal_review_sha256":a.terminal_review_sha256,"archive_source_review_sha256":a.archive_review_sha256,"task":task,"experiment_before_sha256":sha(ROOT/"pipeline/experiments/M234-RVE.json"),"exact_log_sources":{"registered_stdout":stdout_info,"actual_native_logger":native_info},"no_replay":True,"no_restart_signals_sync_dispatch":True})
  result={"owner":owner,"certainty":"uncertain","kind":"EXACT_PEER_CONFIRMED_CRASH_CANONICAL_FINALIZE","state":"crashed","actual_sha256":m["anchors"]["actual"]["sha256"],"terminal_review_sha256":a.terminal_review_sha256,"archive_source_review_sha256":a.archive_review_sha256,"scp_calls":[],"signals_sent":False,"new_training_or_resume":False,"source_sync_or_Git_mutation":False,"checkpoint_content_loaded_or_transferred":False}
  try:
   def fetch(label,info):
    guard(m);remote=PurePosixPath(info["path"]);assert remote.is_absolute() and '..' not in remote.parts and str(remote).startswith("/data/songcl/Project/Cluster_project/")
    directory=ROOT/"Checkpoints/server_4"/"M234-RVE_terminal_342a6a92_v2"/label;assert directory.resolve().is_relative_to((ROOT/"Checkpoints/server_4").resolve());directory.mkdir(parents=True,exist_ok=False);target=directory/remote.name;assert not target.exists()
    process=subprocess.Popen(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=8","songcl@192.168.1.115:"+str(remote),remote.name],cwd=str(directory),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8",errors="replace")
    rec={"label":label,"remote":str(remote),"local":str(target),"local_pid":process.pid,"certainty":"uncertain"};result["scp_calls"].append(rec)
    try:stdout,stderr=process.communicate(timeout=45)
    except subprocess.TimeoutExpired:raise RuntimeError("Exact log transfer uncertain; preserve PID "+str(process.pid)+" and local partial; do not replay")
    rec.update(returncode=process.returncode,stderr=stderr[:2000],certainty="terminal");assert process.returncode==0,stderr[:2000]
    raw=target.read_bytes();assert len(raw)==info["size"] and hashlib.sha256(raw[info["offset"]:info["offset"]+info["bytes_read"]]).hexdigest()==info["tail_sha256"],"Exact log size/tail mismatch; preserve without archive"
    rec["sha256"]=sha(target);rec["bytes_archived"]=len(raw);rec["bytes_decoded_for_observation"]=min(len(raw),131072);guard(m);return target,raw[-131072:].decode("utf-8",errors="replace")
   stdout_local,stdout_text=fetch("registered_stdout",stdout_info);native_local,native_text=fetch("actual_native_logger",native_info)
   values,best,no_improve=None,None,None # No complete validation/checkpoint metric is established by these bounded tails.
   matches=re.findall(r"Train\[(\d+)/(\d+)\]:[^\r\n]*?\|\s*(\d+)/(\d+)",stdout_text);assert matches,"No exact partial native epoch/batch found"
   epoch,total,batch,denominator=map(int,matches[-1]);assert [epoch,batch]==stdout_info["latest_native_step"]==peer["last_observed_native_step"]
   ep=f"partial Train[{epoch}/{total}] batch{batch}/{denominator}; precise completed-epoch count UNKNOWN"
   result["metrics"]={"source_native_log":str(native_local),"native_log_sha256":sha(native_local),"exact_validation_values":values,"best_observed":best,"no_improve_observed":no_improve,"metric_scope":"UNKNOWN; full raw logs archived/hash-verified, only final128KiB decoded; no full stdout or complete-validation metric parsed","partial_epoch_label":ep,"precise_completed_epoch_count":"UNKNOWN","full_training_complete":False}
   original_pull,original_ssh=monitor.pull_log,monitor.ssh
   def exact_pull(project,host,user,remote_log,cfg_name,state,srv_name=""):
    assert Path(project).resolve()==ROOT and (host,user,remote_log,state,srv_name)==("192.168.1.115","songcl",proof["log"],"crashed","server-4")
    assert Path(stdout_local).name==PurePosixPath(proof["log"]).name and sha(stdout_local)==result["scp_calls"][0]["sha256"]
    return str(stdout_local)
   def no_ssh(*args,**kwargs):raise AssertionError("Canonical archival must not issue remote commands")
   events=[];guard(m);monitor.pull_log=exact_pull;monitor.ssh=no_ssh
   try:monitor.finalize_task(str(ROOT),queue,"server-4","192.168.1.115","songcl",task,Path(task["config"]).stem,"crashed",best,ep,"0",proof["log"],events)
   finally:monitor.pull_log=original_pull;monitor.ssh=original_ssh
   assert not journal.exists();exp=monitor.load_experiment(str(ROOT),m["experiment_id"]);assert exp["status"]=="crashed" and exp["code_commit"]==m["source_commit"] and exp["log_local"]==str(stdout_local) and exp["launch_verified"] is True
   assert monitor.load_queue(str(ROOT))==expected_queue;assert all(sha(Path(q))==h for q,h in protected_hashes.items())
   expected_running=copy.deepcopy(before_running)
   if server in expected_running and "0" in expected_running[server]:
    value=expected_running[server]["0"]
    if value==m["experiment_id"]:del expected_running[server]["0"]
    elif isinstance(value,list):
     expected_running[server]["0"]=[x for x in value if x!=m["experiment_id"]]
     if not expected_running[server]["0"]:del expected_running[server]["0"]
    if not expected_running[server]:del expected_running[server]
   assert monitor.load_running(str(ROOT))==expected_running;guard(m)
   result.update(certainty="terminal",passed=True,recorded_at=datetime.now(timezone.utc).isoformat(),archive_id=exp["archive_id"],experiment=exp,canonical_events=events,exact_local_stdout=str(stdout_local),exact_local_native_logger=str(native_local),M206_M227_and_unrelated_queue_preserved=True,source_memory_work_SERVERS_deathwatch_preserved=True,immutable_revision_preserved=True,queue_only_M234_removed=True)
  except BaseException as error:result.update(passed=False,error_type=type(error).__name__,error=str(error));save(result_path,result);raise
  save(result_path,result);print(json.dumps({"path":str(result_path),"sha256":sha(result_path),"archive_id":result["archive_id"],"state":"crashed","metrics":result["metrics"]}))
 finally:lock.close()
if __name__=="__main__":main()
