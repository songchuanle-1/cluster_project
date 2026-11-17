"""Bounded independent24scene measurement on the original authorized GPU."""
from datetime import datetime,timezone
import json
import shlex
from ops import guard,save,run,tick,OUT,STAGE
owner=guard();assert (datetime.fromisoformat(owner["deadline_at"])-datetime.now(timezone.utc)).total_seconds()>1140
for name in ("native_content_replication.py","matched_control.py"):compile((OUT/name).read_text(encoding="utf-8"),name,"exec")
for name in ("native_content_replication.py","matched_control.py","replication_manifest.json","replication_prereg.md"):
    guard();result=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10",str(OUT/name),"songcl@192.168.1.115:"+STAGE+"/"],45)
    assert result.returncode==0,result.stderr
guard()
command="source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; "+shlex.join(["env","PYTHONDONTWRITEBYTECODE=1","python","-B",STAGE+"/native_content_replication.py"])
result=run(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","-o","ServerAliveInterval=10","-o","ServerAliveCountMax=3","songcl@192.168.1.115",shlex.join(["bash","-lc",command])],960)
save("replication_execution.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"returncode":result.returncode,"stdout":result.stdout,"stderr":result.stderr})
fetch=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","songcl@192.168.1.115:"+STAGE+"/replication_result.json",str(OUT/"replication_result.json")],45)
save("replication_fetch.json",{"returncode":fetch.returncode,"stderr":fetch.stderr})
assert result.returncode==0,result.stderr[-5000:]
assert fetch.returncode==0,fetch.stderr
payload=tick.load(OUT/"replication_result.json");assert payload["passed_controls"]
print(json.dumps({k:payload[k] for k in ("observed_at","passed_controls","expressions","independent_scenes","native_forwards","suffix_replays","mean_scene_native_minus_permuted_fixed_query_iou","local_aligned_content_premise_supported")},indent=2))
