"""Preregister the first independent implementation repair, preserve failures."""
from datetime import datetime,timezone
import json
import shlex
from ops import guard,save,evidence,run,tick,ROOT,OUT,STAGE
guard();work=tick.load(ROOT/"pipeline/research_work.json");candidate=next(c for c in work["candidates"] if c["id"]=="fine-leaf-local-point-exchange")
assert not candidate.get("revision_history")
candidate["revision_history"]=[{"revision":1,"failure_scope":"implementation","reason":"Exact-distanceK32cutoff ties select order-dependent point identities;real32scene audit had no triggering rows but cannot excuse the synthetic counterexample.",
    "change":"For exact cutoff ties only, use permutation-invariant whole-fine-leaf mean;untied rows retain original bounded point attention exactly.",
    "prediction":"Original six controls and untied equality pass;40tied rows become leaf means with invariant outputs and analytic gradients<=1e-12.",
    "preregistered_at":datetime.now(timezone.utc).isoformat(),"failure_evidence":[evidence(OUT/"tie_stress_result.json")],"result":"pending","evidence":[evidence(OUT/"operator_revision1_prereg.md"),evidence(OUT/"fine_exchange_operator_v1.py")]}]
candidate["evidence"].extend(evidence(OUT/name) for name in ("tie_audit_result.json","tie_audit_execution.json","tie_audit_fetch.json","operator_revision1_prereg.md","fine_exchange_operator_v1.py"))
candidate["next_action"]="Execute preregistered independent prototype revision1 controls;retain original failure and all missing native integration/backward/resources/novelty gates. No HDSrevision3."
guard();tick.save(ROOT/"pipeline/research_work.json",work)
for name in ("fine_exchange_operator_v1.py",):
    result=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10",str(OUT/name),"songcl@192.168.1.115:"+STAGE+"/"],45)
    assert result.returncode==0,result.stderr
program="import sys,json,socket;assert socket.gethostname()=='dl04-MS-7E06';sys.path.insert(0,"+repr(STAGE)+");from fine_exchange_operator_v1 import controls;import torch;result=controls();result['cuda_initialized']=torch.cuda.is_initialized();assert not result['cuda_initialized'];print(json.dumps(result))"
command="source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; "+shlex.join(["env","PYTHONDONTWRITEBYTECODE=1","python","-B","-c",program])
result=run(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","songcl@192.168.1.115",shlex.join(["bash","-lc",command])],90)
save("operator_revision1_execution.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"returncode":result.returncode,"stdout":result.stdout,"stderr":result.stderr})
assert result.returncode==0,result.stderr
payload=json.loads(result.stdout);assert payload["passed"] and not payload["cuda_initialized"]
save("operator_revision1_controls.json",payload)
work=tick.load(ROOT/"pipeline/research_work.json");candidate=next(c for c in work["candidates"] if c["id"]=="fine-leaf-local-point-exchange")
candidate["revision_history"][0].update(result="passed",evidence=[evidence(OUT/name) for name in ("operator_revision1_prereg.md","fine_exchange_operator_v1.py","operator_revision1_controls.json","operator_revision1_execution.json")])
candidate["evidence"].extend(evidence(OUT/name) for name in ("operator_revision1_controls.json","operator_revision1_execution.json"))
candidate["next_action"]="Independently integrate this candidate-only fine branch on M95,resolve orphan fine-FFN/geometry graph lifetime,then matched native forward/backward,whole-model<=10G/latency/memory and material prior-art review.Prototype repair is not native admission;do not modify HDS."
guard();tick.save(ROOT/"pipeline/research_work.json",work)
print(json.dumps(payload,indent=2))
