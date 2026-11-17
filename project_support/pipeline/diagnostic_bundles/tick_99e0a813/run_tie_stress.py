"""Seek a preregistered structural invariance counterexample, no GPU work."""
import json
import shlex
from datetime import datetime,timezone
from ops import guard,save,evidence,run,tick,ROOT,OUT,STAGE
guard();work=tick.load(ROOT/"pipeline/research_work.json")
candidate=next(c for c in work["candidates"] if c["id"]=="fine-leaf-local-point-exchange")
candidate["evidence"].append(evidence(OUT/"tie_stress_prereg.md"))
candidate["next_action"]="Execute frozen40member equal-distanceK32permutation stress;preserve any implementation counterexample and test real TRAIN tie frequency before integration."
guard();tick.save(ROOT/"pipeline/research_work.json",work)
program="STAGE="+repr(STAGE)+"\n"+r'''
import json,socket,sys
assert socket.gethostname()=="dl04-MS-7E06"
sys.path.insert(0,STAGE)
import numpy as np,torch
from fine_exchange_operator import build_neighbors,point_exchange
torch.set_num_threads(1)
coordinates=np.zeros((40,3));leaves=np.zeros(40,dtype=np.int64)
x=torch.sin(torch.arange(640,dtype=torch.float64).reshape(40,16)/7)
indices,allowed=build_neighbors(coordinates,leaves,k=32)
original=point_exchange(x,indices,allowed)
permutation=torch.arange(39,-1,-1)
pi,pa=build_neighbors(coordinates[permutation],leaves[permutation],k=32)
changed=point_exchange(x[permutation],pi,pa)
error=float((changed-original[permutation]).abs().max())
print(json.dumps({"property":"permutation_equivariance_under_truncated_distance_ties","passed":error<=1e-12,"maximum_error":error,"tolerance":1e-12,"members":40,"k":32,"cuda_initialized":torch.cuda.is_initialized(),"native_model_execution":False,"real_TRAIN_tie_frequency":"unknown"}))
'''
command="source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; "+shlex.join(["env","PYTHONDONTWRITEBYTECODE=1","python","-B","-c",program])
result=run(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","songcl@192.168.1.115",shlex.join(["bash","-lc",command])],90)
save("tie_stress_execution.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"returncode":result.returncode,"stdout":result.stdout,"stderr":result.stderr})
assert result.returncode==0,result.stderr
payload=json.loads(result.stdout);assert not payload["cuda_initialized"]
save("tie_stress_result.json",payload)
print(json.dumps(payload,indent=2))
