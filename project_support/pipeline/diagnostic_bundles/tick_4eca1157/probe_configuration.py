"""Read only already hash-bound config fields;no dataset/model execution."""
from datetime import datetime,timezone
import json
from pathlib import Path
import socket
import gorilla
from padding_contract import sha

assert socket.gethostname()=='dl04-MS-7E06'
root=Path(__file__).resolve().parent
models=json.loads((root/'models.json').read_text())
rows={}
for tag,m in models.items():
    a=m['assets']
    assert sha(a['config_path'])==a['config_sha256']
    cfg=gorilla.Config.fromfile(a['config_path'])
    rows[tag]={'dataloader':{k:{'batch_size':v.get('batch_size'),'num_workers':v.get('num_workers')}
        for k,v in cfg.dataloader.items() if isinstance(v,dict)},'seed':cfg.train.seed,
        'epochs':cfg.train.epochs,'scheduler_max_iters':cfg.lr_scheduler.max_iters,
        'gradient_clip':cfg.train.grad_clip,'config_sha256':a['config_sha256']}
r={'observed_at':datetime.now(timezone.utc).isoformat(),'models':rows,'model_execution':False}
with (root/'configuration_probe_result.json').open('x') as f:json.dump(r,f,indent=2)
print(json.dumps(r))
