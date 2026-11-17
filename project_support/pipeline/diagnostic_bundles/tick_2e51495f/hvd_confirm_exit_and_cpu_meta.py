"""Three fresh process-absence observations and CPU-only saved-state metadata."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import shlex
import subprocess

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
assert owner["token"] == "2e51495f07244023946fc53eec6e6d98"
assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
program = r'''
from pathlib import Path
from datetime import datetime,timezone
import os,json,socket,time,hashlib
assert socket.gethostname()=='dl04-MS-7E06'
assert os.environ['CUDA_VISIBLE_DEVICES']==''
observations=[]
for index in range(3):
 observations.append({'observed_at':datetime.now(timezone.utc).isoformat(),
  'pid':2829477,'exists':Path('/proc/2829477').exists()})
 if index<2:time.sleep(1)
assert all(not row['exists'] for row in observations)
import torch
assert not torch.cuda.is_initialized()
base=Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hvd/20261106_195236')
result=[]
for filename in ('last.pth','best.pth'):
 path=base/filename;before=path.stat()
 payload=torch.load(path,map_location='cpu',weights_only=False)
 metadata=payload.get('meta',{})
 selected={key:metadata.get(key) for key in ('epoch','best_miou','epochs_no_improve')}
 selected={key:(value.item() if hasattr(value,'item') else value) for key,value in selected.items()}
 assert payload.get('optimizer') is not None
 assert payload.get('lr_scheduler') is not None or payload.get('scheduler') is not None or any('sched' in key for key in payload)
 after=path.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
 result.append({'path':str(path),'bytes':after.st_size,'mtime_ns':after.st_mtime_ns,
  'meta':selected,'top_level_keys':list(payload),'map_location':'cpu'})
 del payload
assert not torch.cuda.is_initialized()
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),
 'process_absence_observations':observations,'saved_checkpoints':result,
 'CUDA_VISIBLE_DEVICES':os.environ['CUDA_VISIBLE_DEVICES'],'cuda_initialized':False,
 'native_partial_epoch':5,'native_partial_step':1449,'partial_epoch_saved':False,
 'classification':'crashed_implementation_not_hypothesis_falsification',
 'restart_or_resume':False,'signals_sent':False}))
'''
command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8",
           "songcl@192.168.1.115",
           "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /home/songcl/.conda/envs/project_cluster/bin/python -B -c " + shlex.quote(program)]
out = subprocess.run(command, capture_output=True, text=True, encoding="utf8", timeout=60)
result = {
    "recorded_at": datetime.now(timezone.utc).isoformat(),
    "owner": {key: owner[key] for key in ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")},
    "actual_command": command, "returncode": out.returncode,
    "stdout": out.stdout, "stderr": out.stderr,
}
path = HERE / "hvd_death_confirmation_cpu_checkpoint.json"
with path.open("x", encoding="utf8") as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
assert out.returncode == 0, out.stderr[-1800:]
observation = json.loads(out.stdout)
print(json.dumps({
    "death_checks": len(observation["process_absence_observations"]),
    "checkpoints": [item["meta"] for item in observation["saved_checkpoints"]],
    "cuda_initialized": observation["cuda_initialized"],
    "evidence_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
}))
