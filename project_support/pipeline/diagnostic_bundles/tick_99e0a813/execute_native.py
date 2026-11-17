"""Run only the current preregistered diagnostic on verified authorized GPU0."""
from datetime import datetime,timezone
import json
import shlex
from ops import guard,save,run,tick,ROOT,OUT,STAGE

owner=guard()
assert (datetime.fromisoformat(owner["deadline_at"])-datetime.now(timezone.utc)).total_seconds()>1140
for name in ("native_content.py","matched_control.py"):compile((OUT/name).read_text(encoding="utf-8"),name,"exec")
check=tick.load(OUT/"cohort_resource_precheck.json")
assert not check["contexts"] and all(v=="acquired_and_released" for v in check["locks"].values())
result=run(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","songcl@192.168.1.115",shlex.join(["mkdir","-p",STAGE])])
assert result.returncode==0,result.stderr
for name in ("native_content.py","matched_control.py","content_manifest.json","content_prereg.md"):
    guard()
    result=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10",str(OUT/name),"songcl@192.168.1.115:"+STAGE+"/"],45)
    assert result.returncode==0,result.stderr
guard()
command="source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; "+shlex.join(["env","PYTHONDONTWRITEBYTECODE=1","python","-B",STAGE+"/native_content.py"])
result=run(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","-o","ServerAliveInterval=10","-o","ServerAliveCountMax=3","songcl@192.168.1.115",shlex.join(["bash","-lc",command])],960)
save("native_execution.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"returncode":result.returncode,"stdout":result.stdout,"stderr":result.stderr})
fetch=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","songcl@192.168.1.115:"+STAGE+"/content_result.json",str(OUT/"content_result.json")],45)
save("native_fetch.json",{"returncode":fetch.returncode,"stderr":fetch.stderr})
assert result.returncode==0,result.stderr[-5000:]
assert fetch.returncode==0,fetch.stderr
payload=tick.load(OUT/"content_result.json");assert payload["passed_controls"]
keys=("observed_at","passed_controls","expressions","independent_scenes","native_forwards","suffix_replays","scene_native_minus_permuted_fixed_query_iou","mean_scene_native_minus_permuted_fixed_query_iou","local_aligned_content_premise_supported")
print(json.dumps({k:payload[k] for k in keys},indent=2))
