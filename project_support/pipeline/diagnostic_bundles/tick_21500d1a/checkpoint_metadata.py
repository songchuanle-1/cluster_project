"""Inspect only trusted ended-run/reference checkpoints on target CPU."""
import json
import shlex
from audit_terminal import guard, save, remote, OUT, tick

guard()
audit = tick.load(OUT / "terminal_observation.json")
paths = {name: row["path"] for name, row in audit["checkpoint_paths"].items()}
paths["frozen_m95"] = audit["frozen_m95"]["path"]
program = "PATHS=" + repr(paths) + "\n" + r'''
import datetime,hashlib,json,pathlib,socket,sys
assert socket.gethostname()=='dl04-MS-7E06'
import torch
assert not torch.cuda.is_initialized()
rows={}
for name,filename in PATHS.items():
    path=pathlib.Path(filename)
    h=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(8*1024*1024),b''):h.update(block)
    checkpoint=torch.load(path,map_location='cpu',weights_only=False)
    meta=checkpoint.get('meta',{})
    selected={}
    for key in ('epoch','best_miou','epochs_no_improve'):
        value=meta.get(key)
        if hasattr(value,'item'):value=value.item()
        selected[key]=value
    rows[name]={'path':str(path),'sha256':h.hexdigest(),'bytes':path.stat().st_size,
                'meta':selected,'model_state_entries':len(checkpoint['model']),
                'optimizer_states':len(checkpoint.get('optimizer',{}).get('state',{})),
                'scheduler_present':'scheduler' in checkpoint,'map_location':'cpu'}
    del checkpoint
assert not torch.cuda.is_initialized()
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'python':sys.version,'torch':torch.__version__,'cuda_initialized':torch.cuda.is_initialized(),
    'checkpoints':rows,'native_forwards':0,'optimizer_steps':0}))
'''
command = "source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; " + shlex.join([
    "env", "CUDA_VISIBLE_DEVICES=", "PYTHONDONTWRITEBYTECODE=1", "python", "-B", "-c", program])
result = json.loads(remote("192.168.1.115", shlex.join(["bash", "-lc", command]), timeout=150))
save("checkpoint_metadata.json", result)
assert result["checkpoints"]["frozen_m95"]["sha256"] == audit["frozen_m95"]["sha256"]
assert result["checkpoints"]["best.pth"]["meta"]["best_miou"] == max(audit["native_scalar_log"]["miou"])
print(json.dumps({name: {"meta": row["meta"], "sha256": row["sha256"]} for name, row in result["checkpoints"].items()}, indent=2))
