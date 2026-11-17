"""Remote CPU-only prototype controls and final exact-source postcheck."""
from datetime import datetime,timezone
import json
import shlex
from ops import guard,save,evidence,run,tick,ROOT,OUT,STAGE,ssh
guard()
work=tick.load(ROOT/"pipeline/research_work.json");candidate=next(c for c in work["candidates"] if c["id"]=="fine-leaf-local-point-exchange")
assert candidate["stage"]=="diagnosis"
candidate["evidence"].extend(evidence(OUT/name) for name in ("fine_audit_result.json","fine_audit_execution.json","fine_audit_fetch.json","fine_exchange_operator.py","prototype_prereg.md"))
candidate["next_action"]="Run6isolated CPU operator controls including gradcheck/standard-attention equivalence;then bind native geometry evidence and review the full implementation/novelty/resource gaps. No training admission."
guard();tick.save(ROOT/"pipeline/research_work.json",work)
result=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10",str(OUT/"fine_exchange_operator.py"),"songcl@192.168.1.115:"+STAGE+"/"],45)
assert result.returncode==0,result.stderr
program="STAGE="+repr(STAGE)+"\n"+r'''
import fcntl,json,socket,subprocess,sys
assert socket.gethostname()=="dl04-MS-7E06"
uuid=subprocess.check_output(["nvidia-smi","-i","0","--query-gpu=uuid","--format=csv,noheader"],universal_newlines=True).strip()
assert uuid=="GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
contexts=subprocess.check_output(["nvidia-smi","-i","0","--query-compute-apps=pid,used_memory","--format=csv,noheader,nounits"],universal_newlines=True).strip()
assert not contexts
locks=[]
try:
    for kind in ("training","diagnostic","exclusive"):
        handle=open("/tmp/cluster_project_gpu0_"+kind+".lock","rb")
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(handle)
    import torch
    sys.path.insert(0,STAGE)
    from fine_exchange_operator import standalone_controls
    result=standalone_controls();result.update(cuda_initialized=torch.cuda.is_initialized(),pinned_gpu_uuid=uuid,lifetime_locks_held=3)
    assert not result["cuda_initialized"]
    print(json.dumps(result))
finally:
    for handle in reversed(locks):handle.close()
'''
command="source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; "+shlex.join(["env","PYTHONDONTWRITEBYTECODE=1","python","-B","-c",program])
result=run(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","songcl@192.168.1.115",shlex.join(["bash","-lc",command])],90)
save("operator_execution.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"returncode":result.returncode,"stdout":result.stdout,"stderr":result.stderr})
assert result.returncode==0,result.stderr
payload=json.loads(result.stdout);assert payload["passed"] and not payload["cuda_initialized"]
save("operator_controls.json",payload)
print(json.dumps(payload,indent=2))
