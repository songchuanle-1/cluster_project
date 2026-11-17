"""Preregister and execute the real-geometry follow-up to a preserved failure."""
from datetime import datetime,timezone
import json
import shlex
from ops import guard,save,evidence,run,tick,ROOT,OUT,STAGE
owner=guard();assert (datetime.fromisoformat(owner["deadline_at"])-datetime.now(timezone.utc)).total_seconds()>360
stress=tick.load(OUT/"tie_stress_result.json");assert not stress["passed"]
manifest=tick.load(OUT/"fine_audit_manifest.json")
manifest["producer_hashes"]={name:tick.digest(OUT/name) for name in ("native_tie_audit.py","matched_control.py","fine_exchange_operator.py")}
save("tie_audit_manifest.json",manifest)
work=tick.load(ROOT/"pipeline/research_work.json");candidate=next(c for c in work["candidates"] if c["id"]=="fine-leaf-local-point-exchange")
candidate.update(stage="implementation",failure_scope="implementation",next_action="Measure real TRAIN cutoff ties/adjacency reversal on32fixed scenes before designing a bounded invariant neighbor selector. Current operator remains unaccepted;no model/HDSrevision3/admission.")
candidate["evidence"].extend(evidence(OUT/name) for name in ("operator_controls.json","operator_execution.json","tie_stress_prereg.md","tie_stress_result.json","tie_stress_execution.json","real_tie_prereg.md","tie_audit_manifest.json","native_tie_audit.py"))
guard();tick.save(ROOT/"pipeline/research_work.json",work)
for name in ("native_tie_audit.py","fine_exchange_operator.py","matched_control.py","tie_audit_manifest.json"):
    guard();result=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10",str(OUT/name),"songcl@192.168.1.115:"+STAGE+"/"],45)
    assert result.returncode==0,result.stderr
command="source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; "+shlex.join(["env","PYTHONDONTWRITEBYTECODE=1","python","-B",STAGE+"/native_tie_audit.py"])
result=run(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","-o","ServerAliveInterval=10","-o","ServerAliveCountMax=3","songcl@192.168.1.115",shlex.join(["bash","-lc",command])],240)
save("tie_audit_execution.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"returncode":result.returncode,"stdout":result.stdout,"stderr":result.stderr})
fetch=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","songcl@192.168.1.115:"+STAGE+"/tie_audit_result.json",str(OUT/"tie_audit_result.json")],45)
save("tie_audit_fetch.json",{"returncode":fetch.returncode,"stderr":fetch.stderr})
assert result.returncode==0,result.stderr[-5000:]
assert fetch.returncode==0,fetch.stderr
payload=tick.load(OUT/"tie_audit_result.json");assert payload["passed_controls"]
rows=payload["rows"]
print(json.dumps({"observed_at":payload["observed_at"],"expressions":len(rows),"scenes":32,"native_forwards":32,"suffix_replays":0,"exact_cutoff_tie_rows":sum(r["exact_cutoff_tie_rows"] for r in rows),"adjacency_changed_rows":sum(r["adjacency_membership_changed_rows_under_reversal"] for r in rows),"max_duplicate_coordinates":max(r["max_equal_coordinate_multiplicity"] for r in rows)},indent=2))
