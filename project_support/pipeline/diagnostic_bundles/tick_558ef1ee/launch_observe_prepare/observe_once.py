"""Default NOP. Owner-bound single-use read-only SSH observer; no launch or signals."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,re,shlex,subprocess,sys
ROOT=Path("D:/project/cluster_project");HERE=Path(__file__).resolve().parent
KEYS=("token","thread_id","generated_at","deadline_at","context_sha256","pending_sha256")
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with p.open("x",encoding="utf-8",newline="\n") as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write("\n")
def main():
 a=argparse.ArgumentParser();a.add_argument("--execute-root",action="store_true");a.add_argument("--label");a.add_argument("--dispatch-proof",type=Path);a.add_argument("--dispatch-proof-sha256");a.add_argument("--previous",type=Path);a.add_argument("--previous-sha256");args=a.parse_args()
 if not args.execute_root:print("NOOP: explicit root execution, a fresh label and authenticated actual dispatch proof are required.");return
 assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS")=="0"
 b=read(HERE/"owner_binding.json");o={k:read(ROOT/"pipeline/headless/.foreground.lockdir/owner.json")[k] for k in KEYS};assert o==b["owner"] and o["thread_id"]==os.environ.get("CODEX_THREAD_ID") and datetime.now(timezone.utc)<datetime.fromisoformat(o["deadline_at"])
 for name,key in [(".tick_context.json","context_sha256"),(".tick_context_state.next.json","pending_sha256")]:assert sha(ROOT/"pipeline/headless"/name)==o[key]
 frozen=read(HERE/"FROZEN.json")
 for name,digest in frozen["files"].items():assert sha(HERE/name)==digest
 assert args.label and re.fullmatch(r"[a-z][a-z0-9_-]{0,31}",args.label)
 assert args.dispatch_proof and args.dispatch_proof.resolve().is_relative_to(ROOT) and sha(args.dispatch_proof)==args.dispatch_proof_sha256
 p=read(args.dispatch_proof);assert p["task_id"]=="M234-RVE" and p["source_commit"]=="d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
 for k in ["pid","start_ticks","runtime_root","log","binding_path","binding_sha256","entry_sha256","core_path","core_sha256","marker_sha256"]:assert p.get(k),"Missing actual launch fact: "+k
 q=read(ROOT/"pipeline/queue.json");tasks=[t for ts in q["gpu_queues"].values() for t in ts if t.get("id")=="M234-RVE"];assert len(tasks)==1;t=tasks[0]
 assert t["code_commit"]==p["source_commit"] and int(t["pid"])==p["pid"] and t["log"]==p["log"] and t["status"] in ["running","claiming"] and str(t.get("gpu",t.get("claimed_gpu")))=="0"
 intent=HERE/(args.label+".intent.json");out=HERE/(args.label+".actual.json");assert not intent.exists() and not out.exists(),"Existing/uncertain observation cannot replay"
 program=(HERE/"observe_remote.py.txt").read_text(encoding="utf-8")
 save(intent,{"recorded_at":datetime.now(timezone.utc).isoformat(),"owner":o,"label":args.label,"dispatch_proof":{"path":str(args.dispatch_proof),"sha256":args.dispatch_proof_sha256},"queue_sha256":sha(ROOT/"pipeline/queue.json"),"observer_sha256":sha(Path(__file__)),"program_sha256":sha(HERE/"observe_remote.py.txt"),"read_only":True,"no_replay":True})
 proc=subprocess.Popen(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=8","songcl@192.168.1.115","PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c "+shlex.quote(program)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8",errors="replace")
 result={"recorded_at":datetime.now(timezone.utc).isoformat(),"owner":o,"label":args.label,"certainty":"uncertain","local_ssh_pid":proc.pid,"dispatch_proof_sha256":args.dispatch_proof_sha256,"read_only":True}
 try:
  stdout,stderr=proc.communicate(json.dumps(p),timeout=35);result.update(certainty="terminal",returncode=proc.returncode,stderr=stderr[:2000]);assert len(stdout.encode())<24576
  result["observation"]=json.loads(stdout)
  if args.previous:
   assert sha(args.previous)==args.previous_sha256;old=read(args.previous)["observation"];new=result["observation"];assert old["pid"]==new["pid"] and old["start_ticks"]==new["start_ticks"] and old["source_commit"]==new["source_commit"]
   x,y=old.get("latest_native_step"),new.get("latest_native_step");result["native_step_growth_observed"]=bool(x and y and tuple(y)>tuple(x));result["previous_sha256"]=args.previous_sha256
 except subprocess.TimeoutExpired:result["reason"]="Read-only observation uncertain; no signals, cleanup, replay or inferred completion"
 except BaseException as e:result["parse_or_identity_error"]=str(e)
 save(out,result);assert result.get("returncode")==0 and "observation" in result and "parse_or_identity_error" not in result
 print(json.dumps({"path":str(out),"sha256":sha(out),"observation":result["observation"],"native_step_growth_observed":result.get("native_step_growth_observed")}))
if __name__=="__main__":main()
