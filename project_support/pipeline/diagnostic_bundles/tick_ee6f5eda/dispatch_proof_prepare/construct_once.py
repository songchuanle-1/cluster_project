"""Default NOP. Root read-only construction of factual observer dispatch proof."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import argparse,hashlib,json,os,shlex,subprocess,sys
ROOT=Path("D:/project/cluster_project");HERE=Path(__file__).resolve().parent;TICK=HERE.parent
KEYS=("token","thread_id","generated_at","deadline_at","context_sha256","pending_sha256")
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with p.open("x",encoding="utf-8",newline="\n") as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write("\n")
def guard():
 assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS")=="0"
 expected=read(HERE/"owner_binding.json")["owner"];raw=read(ROOT/"pipeline/headless/.foreground.lockdir/owner.json");owner={k:raw[k] for k in KEYS}
 assert owner==expected and owner["thread_id"]==os.environ.get("CODEX_THREAD_ID") and datetime.now(timezone.utc)<datetime.fromisoformat(owner["deadline_at"])
 mode=read(ROOT/"pipeline/execution_mode.json");assert mode["mode"]=="foreground" and mode["target_thread_id"]==owner["thread_id"]
 for name,key in ((".tick_context.json","context_sha256"),(".tick_context_state.next.json","pending_sha256")):assert sha(ROOT/"pipeline/headless"/name)==owner[key]
 for name,digest in read(HERE/"FROZEN.json")["files"].items():assert sha(HERE/name)==digest
 return owner
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--execute-root",action="store_true");parser.add_argument("--production-result",type=Path,default=TICK/"rvec_setup_execution/render_result.json");parser.add_argument("--production-result-sha256");parser.add_argument("--dispatch-result",type=Path,default=TICK/"rvec_dispatch_execution/rvec_dispatch_result.json");parser.add_argument("--dispatch-result-sha256");a=parser.parse_args()
 if not a.execute_root:print(json.dumps({"status":"DEFAULT_NOP_NO_SSH_GIT_GPU_SIGNALS_OR_SHARED_MUTATION"}));return
 owner=guard();assert a.production_result_sha256 and a.dispatch_result_sha256
 for path,digest in ((a.production_result,a.production_result_sha256),(a.dispatch_result,a.dispatch_result_sha256)):assert path.resolve().is_relative_to(ROOT) and sha(path)==digest
 production,dispatch=read(a.production_result),read(a.dispatch_result)
 assert production["owner"]==owner and production["kind"]=="PRODUCTION_PATH_INSTALLED_NO_TRAINER_LAUNCHED"
 assert production["training_launch_or_GPU_use"] is False and production["one_shot_consumed"] is False
 assert dispatch["owner_token"]==owner["token"] and dispatch["signals_sent"] is False
 intent=TICK/"rvec_dispatch_execution/rvec_dispatch_intent.json";intent_value=read(intent);assert intent_value["owner"]==owner and intent_value["production_result_sha256"]==a.production_result_sha256
 q=read(ROOT/"pipeline/queue.json");tasks=[task for ts in q["gpu_queues"].values() for task in ts if task.get("id")=="M234-RVE"];assert len(tasks)==1;task=tasks[0];sent=dispatch["task"]
 assert task["status"] in ("running","claiming") and str(task.get("gpu",task.get("claimed_gpu")))=="0"
 assert task["code_commit"]==sent["code_commit"]=="d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e" and int(task["pid"])==int(sent["pid"])>0 and task["log"]==sent["log"]
 binding=production["binding"];artifact=production["artifact"];files=production["files"];stage=PurePosixPath(binding["stage"])
 assert stage.is_absolute() and '..' not in stage.parts and artifact["stage"]==str(stage) and artifact["entry"]==binding["entry"] and artifact["kind"]==binding["kind"]=="production"
 def locate(digest,suffix):
  matches=[name for name,value in files.items() if value==digest and PurePosixPath(name).suffix==suffix];assert len(matches)==1
  rel=PurePosixPath(matches[0]);assert not rel.is_absolute() and '..' not in rel.parts
  return str(stage/rel)
 binding_path=locate(artifact["binding_sha256"],".json");core_path=locate(artifact["core_sha256"],".py")
 entry_relative=str(PurePosixPath(binding["entry"]).relative_to(stage));assert files[entry_relative]==artifact["entry_sha256"]
 assert binding["source_commit"]==task["code_commit"] and binding["runtime_root"]=="/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
 payload={"owner":owner,"task_id":task["id"],"source_commit":task["code_commit"],"pid":int(task["pid"]),"runtime_root":binding["runtime_root"],"log":task["log"],"binding_path":binding_path,"binding_sha256":artifact["binding_sha256"],"entry_sha256":artifact["entry_sha256"],"core_path":core_path,"core_sha256":artifact["core_sha256"],"stage":str(stage),"binding":binding}
 execution=TICK/"dispatch_proof_execution";execution.mkdir(exist_ok=True);attempt=execution/"capture_intent.json";actual=execution/"capture_actual.json";out=execution/"dispatch_proof.json"
 assert all(not x.exists() for x in (attempt,actual,out)),"Existing/uncertain capture: reconcile, never replay"
 references={"production_result":{"path":str(a.production_result),"sha256":a.production_result_sha256},"dispatch_result":{"path":str(a.dispatch_result),"sha256":a.dispatch_result_sha256},"dispatch_intent":{"path":str(intent),"sha256":sha(intent)},"queue_sha256":sha(ROOT/"pipeline/queue.json")}
 save(attempt,{"owner":owner,"recorded_at":datetime.now(timezone.utc).isoformat(),"actual_references":references,"FROZEN_sha256":sha(HERE/"FROZEN.json"),"read_only":True,"no_replay":True})
 program=(HERE/"capture_remote.py.txt").read_text(encoding="utf-8")
 command=["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=8","songcl@192.168.1.115","CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -B -c "+shlex.quote(program)]
 guard();process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8",errors="replace")
 result={"owner":owner,"certainty":"uncertain","local_ssh_pid":process.pid,"actual_references":references,"read_only":True,"training_started":False,"signals_sent":False}
 try:
  stdout,stderr=process.communicate(json.dumps(payload),timeout=35);result.update(certainty="terminal",returncode=process.returncode,stderr=stderr[:2000]);assert process.returncode==0 and len(stdout.encode())<24576
  proof=json.loads(stdout)
  for key in ("owner","task_id","source_commit","pid","runtime_root","log","binding_path","binding_sha256","entry_sha256","core_path","core_sha256"):assert proof[key]==payload[key]
  assert str(proof["start_ticks"]).isdigit() and len(proof["marker_sha256"])==64
  current=read(ROOT/"pipeline/queue.json");now=[t for ts in current["gpu_queues"].values() for t in ts if t.get("id")=="M234-RVE"];assert len(now)==1 and int(now[0]["pid"])==payload["pid"] and now[0]["log"]==payload["log"]
  guard();proof["actual_references"]=references;result["proof"]=proof;save(out,proof);result.update(proof_path=str(out),proof_sha256=sha(out))
 except subprocess.TimeoutExpired:result["reason"]="Read-only capture uncertain; preserve process; no signal or replay"
 except BaseException as e:result.update(error_type=type(e).__name__,error=str(e));save(actual,result);raise
 save(actual,result);assert result.get("returncode")==0 and "proof_sha256" in result
 print(json.dumps({"path":str(out),"sha256":sha(out),"pid":result["proof"]["pid"],"start_ticks":result["proof"]["start_ticks"]}))
if __name__=="__main__":main()
