"""Execute the second, already preregistered frozen-model diagnosis."""
from datetime import datetime,timezone
import json
import shlex
from ops import guard,save,run,tick,OUT,STAGE
owner=guard();assert (datetime.fromisoformat(owner["deadline_at"])-datetime.now(timezone.utc)).total_seconds()>1140
for name in ("native_cooperation.py","matched_control.py"):compile((OUT/name).read_text(encoding="utf-8"),name,"exec")
for name in ("native_cooperation.py","matched_control.py","cooperation_manifest.json","cooperation_prereg.md"):
    guard();result=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10",str(OUT/name),"songcl@192.168.1.115:"+STAGE+"/"],45)
    assert result.returncode==0,result.stderr
guard()
command="source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; "+shlex.join(["env","PYTHONDONTWRITEBYTECODE=1","python","-B",STAGE+"/native_cooperation.py"])
result=run(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","-o","ServerAliveInterval=10","-o","ServerAliveCountMax=3","songcl@192.168.1.115",shlex.join(["bash","-lc",command])],960)
save("cooperation_execution.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"returncode":result.returncode,"stdout":result.stdout,"stderr":result.stderr})
fetch=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","songcl@192.168.1.115:"+STAGE+"/cooperation_result.json",str(OUT/"cooperation_result.json")],45)
save("cooperation_fetch.json",{"returncode":fetch.returncode,"stderr":fetch.stderr})
assert result.returncode==0,result.stderr[-5000:]
assert fetch.returncode==0,fetch.stderr
payload=tick.load(OUT/"cooperation_result.json");assert payload["passed_controls"]
energies={key:sum(r["bilinear"][key] for r in payload["rows"])/len(payload["rows"]) for key in ("point_energy","query_energy","interaction_energy","total_energy")}
print(json.dumps({"passed_controls":True,"observed_at":payload["observed_at"],"expressions":payload["expressions"],"independent_scenes":32,"native_forwards":payload["native_forwards"],"suffix_replays":payload["suffix_replays"],"mean_selected_query_energies":energies,"local_point_energy_dominates":energies["point_energy"]>energies["query_energy"]},indent=2))
