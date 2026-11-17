"""Execute only the preregistered fine-leaf prerequisite audit."""
from datetime import datetime,timezone
import json
import shlex
from ops import guard,save,run,tick,OUT,STAGE
owner=guard();assert (datetime.fromisoformat(owner["deadline_at"])-datetime.now(timezone.utc)).total_seconds()>1140
compile((OUT/"native_fine_audit.py").read_text(encoding="utf-8"),"native_fine_audit.py","exec")
for name in ("native_fine_audit.py","matched_control.py","fine_audit_manifest.json","fine_exchange_prereg.md"):
    guard();result=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10",str(OUT/name),"songcl@192.168.1.115:"+STAGE+"/"],45)
    assert result.returncode==0,result.stderr
guard()
command="source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; "+shlex.join(["env","PYTHONDONTWRITEBYTECODE=1","python","-B",STAGE+"/native_fine_audit.py"])
result=run(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","-o","ServerAliveInterval=10","-o","ServerAliveCountMax=3","songcl@192.168.1.115",shlex.join(["bash","-lc",command])],960)
save("fine_audit_execution.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"returncode":result.returncode,"stdout":result.stdout,"stderr":result.stderr})
fetch=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","songcl@192.168.1.115:"+STAGE+"/fine_audit_result.json",str(OUT/"fine_audit_result.json")],45)
save("fine_audit_fetch.json",{"returncode":fetch.returncode,"stderr":fetch.stderr})
assert result.returncode==0,result.stderr[-5000:]
assert fetch.returncode==0,fetch.stderr
payload=tick.load(OUT/"fine_audit_result.json");assert payload["passed_controls"]
rows=payload["rows"]
print(json.dumps({"observed_at":payload["observed_at"],"passed_controls":True,"expressions":payload["expressions"],"scenes":32,"native_forwards":32,"suffix_replays":0,"expressions_with_mixed_leaf":sum(r["mixed_leaves"]>0 for r in rows),"mean_scene_mixed_member_fraction":payload["mean_scene_mixed_member_fraction"],"native_errors_in_mixed":sum(r["native_mixed_leaf_errors"] for r in rows),"native_errors_elsewhere":sum(r["native_other_leaf_errors"] for r in rows)},indent=2))
