from pathlib import Path
from datetime import datetime,timezone
import json,base64,socket,pwd,os,hashlib,subprocess
assert socket.gethostname()=="dl04-MS-7E06" and pwd.getpwuid(os.getuid()).pw_name=="songcl" and os.getuid()==os.geteuid()!=0
b=P["binding"];o=b["root_owner_provenance"]
def guard():
 assert o["token"]=="12e364dc14cd4e1195532c7fd295b834" and o["thread_id"]=="01a159c5-29ab-7a22-ba7f-e79174757253"
 assert datetime.now(timezone.utc)<datetime.fromisoformat(o["deadline_at"])
guard()
assert hashlib.sha256(Path(b["original_conda_source"]["path"]).read_bytes()).hexdigest()==b["original_conda_source"]["sha256"]
stage=Path(P["stage"]);assert str(stage)=="/data/songcl/Project/Cluster_project/pipeline/runtime/hvd_three_lock_12e364dc"
assert not stage.exists(),"Existing current-stage evidence: do not replay or overwrite"
stage.mkdir(exist_ok=False)
for name,value in P["files"].items():
 guard();assert Path(name).name==name;raw=base64.b64decode(value,validate=True)
 if name in b["files"]:assert hashlib.sha256(raw).hexdigest()==b["files"][name]
 with (stage/name).open("xb") as f:f.write(raw)
guard()
p=subprocess.Popen(["/usr/bin/python3","-B",str(stage/"cpu_proof.py"),"--binding",str(stage/"binding.json")],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
try:out,err=p.communicate(timeout=60)
except subprocess.TimeoutExpired:raise RuntimeError("Own CPU probe uncertain; no signals/replay. PID "+str(p.pid))
guard();capture={"returncode":p.returncode,"stdout":out,"stderr":err,"cpu_proof_process_pid":p.pid,"hostname":socket.gethostname(),"uid":os.getuid(),"author_child_thread_id":b["actual_author_child_thread_id"],"root_owner_provenance":o}
with (stage/"cpu_execution_capture.json").open("x") as f:json.dump(capture,f,indent=2);f.write("\n")
result={"capture":capture,"stage":str(stage),"proof":json.loads((stage/"actual_cpu_proof.json").read_text()) if (stage/"actual_cpu_proof.json").exists() else None,"remote_sha256":{q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in stage.iterdir() if q.is_file()}}
print(json.dumps(result))
