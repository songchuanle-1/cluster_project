import socket
assert socket.gethostname() == 'dl04-MS-7E06'
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import torch

assert not torch.cuda.is_initialized()
rows=[]
for target in PARAMS['targets']:
    checkpoint_rows=[]; inspected=None
    for item in target['checkpoint_files_before']:
        path=Path(item['path']); stat=path.stat()
        h=hashlib.sha256()
        with path.open('rb') as f:
            for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
        if path.name=='last.pth':
            data=torch.load(str(path),map_location='cpu',weights_only=False,mmap=True)
            assert all(k in data for k in ('model','optimizer','scheduler','meta'))
            assert data['model'] and data['optimizer']['state'] and data['optimizer']['param_groups'] and data['scheduler']
            meta=data['meta']; assert isinstance(meta['epoch'],int) and math.isfinite(float(meta['best_miou']))
            inspected=dict(path=str(path),meta=dict(epoch=int(meta['epoch']),best_miou=float(meta['best_miou']),
                epochs_no_improve=int(meta['epochs_no_improve'])),full_model_optimizer_scheduler_present=True,cpu_load_succeeded=True)
            del data
        after=path.stat(); assert (stat.st_ino,stat.st_size,stat.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns)
        checkpoint_rows.append(dict(path=str(path),bytes=stat.st_size,sha256=h.hexdigest(),stable_during_inspection=True))
    assert inspected is not None
    rows.append(dict(id=target['id'],checkpoints=checkpoint_rows,last_complete_checkpoint=inspected,
        original_log=target['log'],original_log_preserved=Path(target['log']).is_file(),current_partial_epoch_saved=False))
assert not torch.cuda.is_initialized()
for target in PARAMS['targets']:
    p=Path('/proc')/str(target['original']['pid'])
    if p.exists():
        tail=(p/'stat').read_text().rsplit(')',1)[1].split()
        assert tail[19]!=target['original']['starttime'] or tail[0] in ('Z','X')
contexts=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
assert not any(int(line.split(',')[1]) in PARAMS['original_member_pids'] for line in contexts.splitlines())
print(json.dumps(dict(observed_at=datetime.now(timezone.utc).isoformat(),hostname=socket.gethostname(),
    checkpoints=rows,cuda_initialized=False,no_training_or_resume=True,contexts=contexts,
    gpus=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip())))
