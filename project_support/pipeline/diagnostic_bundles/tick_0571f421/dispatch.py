"""One admitted dispatch through the existing monitor, without another preflight."""
from datetime import datetime,timezone
import json
import os
from ops import ROOT,OUT,CID,guard,save,run,tick
import pipeline_monitor as monitor
import closure

owner=guard()
assert (datetime.fromisoformat(owner["deadline_at"])-datetime.now(timezone.utc)).total_seconds()>300
EID="M203-FLE"
os.environ["GIT_SSH_COMMAND"]="ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10"

def strict_ssh(host,user,command):
    result=run(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10",user+"@"+host,command],180)
    assert result.returncode==0,result.stderr
    return result.stdout

monitor.ssh=strict_ssh
lock=monitor.acquire_lock(str(ROOT));assert lock is not None,"Project queue lock busy"
try:
    guard();servers=monitor.load_servers(str(ROOT));server=servers["server-4"]
    assert server["host"]=="192.168.1.115" and server["allowed_gpus"]==[0] and server.get("dispatch_enabled") is True
    assert strict_ssh(server["host"],server["user"],"hostname").strip()=="dl04-MS-7E06"
    queue=monitor.load_queue(str(ROOT));tasks=queue["gpu_queues"]["server-4"]
    task=next(t for t in tasks if t["id"]==EID)
    assert task["status"]=="waiting" and not task.get("pid")
    assert sum(t.get("status") in ("waiting","claiming","running") for t in tasks)==1
    closure.admission(ROOT,task)
    events=[]
    monitor._process_queue(queue,"server-4",server["host"],server["user"],str(ROOT),set(),{"0"},events,
        max_tasks_per_gpu=1,allow_external_overlay=False,remote_code_root=server["remote_code_root"],current_tasks=0,max_tasks_total=1)
    current=monitor.load_queue(str(ROOT));task=next(t for t in current["gpu_queues"]["server-4"] if t["id"]==EID)
    save("dispatch_result.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"task":task,"events":events,"another_preflight":False})
    work=tick.load(ROOT/"pipeline/research_work.json");candidate=next(c for c in work["candidates"] if c["id"]==CID)
    if task.get("launch_verified") and task["status"]=="running":
        candidate.update(stage="training",next_action="Monitor this SAME M203-FLE native run;preserve all source/seed/schedule/earlystop settings. First VAL efficacy and full-training peak remain unknown;no duplicate launch.",
            gate_result="Admitted and native increasing Train steps verified;trained efficacy/material novelty/full-run peak remain UNKNOWN.")
    else:
        candidate.update(stage="deployment",next_action="Reconcile exact M203-FLE config/PID/log and startup guard;do not relaunch blindly. "+str(task.get("dispatch_hold",task.get("launch_verification",task["status"]))))
    candidate["evidence"].append({"path":"pipeline/diagnostic_bundles/tick_0571f421/dispatch_result.json","sha256":tick.digest(OUT/"dispatch_result.json")})
    guard();tick.save(ROOT/"pipeline/research_work.json",work)
finally:lock.close()
print(json.dumps({k:task.get(k) for k in ("id","status","pid","log","launch_verified","launch_verification","dispatch_hold")},ensure_ascii=False))
