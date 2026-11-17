import socket
assert socket.gethostname() == 'dl04-MS-7E06'
import os
os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1')
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import shutil

source = Path(PARAMS['source_checkpoint'])
base = Path('/data/songcl/Project/Cluster_project/pipeline/resume_snapshots').resolve()
destination = base / PARAMS['operation_id'] / source.parent.name / 'last.pth'
assert destination.resolve().is_relative_to(base) and not destination.exists()
assert source.name == 'last.pth' and source.is_file()
assert shutil.disk_usage(base).free > source.stat().st_size * 2
destination.parent.mkdir(parents=True, exist_ok=False)


def info(path):
    s = path.stat()
    return (s.st_ino, s.st_size, s.st_mtime_ns)


attempts = []
for attempt in range(3):
    temporary = destination.parent / ('copy_' + str(attempt) + '.pth')
    before = info(source)
    with source.open('rb') as inp, temporary.open('xb') as out:
        shutil.copyfileobj(inp, out, 8 * 1024 * 1024)
        out.flush()
        os.fsync(out.fileno())
    after = info(source)
    attempts.append(dict(before=before, after=after, stable=before == after))
    if before == after:
        temporary.rename(destination)
        break
else:
    raise RuntimeError('No stable checkpoint copy; no stop signal sent')
h = hashlib.sha256()
with destination.open('rb') as stream:
    for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
        h.update(block)
import torch
assert not torch.cuda.is_initialized()
value = torch.load(str(destination), map_location='cpu', weights_only=False, mmap=True)
assert isinstance(value, dict) and all(key in value for key in ('model', 'optimizer', 'scheduler', 'meta'))
assert isinstance(value['model'], dict) and value['model']
optimizer, scheduler, meta = value['optimizer'], value['scheduler'], value['meta']
assert isinstance(optimizer, dict) and optimizer.get('state') and optimizer.get('param_groups')
assert isinstance(scheduler, dict) and scheduler and isinstance(meta, dict)
assert isinstance(meta['epoch'], int) and meta['epoch'] >= 8
assert isinstance(meta['epochs_no_improve'], int) and meta['epochs_no_improve'] >= 0
assert math.isfinite(float(meta['best_miou']))


def all_cpu(v):
    if torch.is_tensor(v):
        return v.device.type == 'cpu'
    if isinstance(v, dict):
        return all(all_cpu(x) for x in v.values())
    if isinstance(v, (list, tuple)):
        return all(all_cpu(x) for x in v)
    return True


assert all_cpu(value) and not torch.cuda.is_initialized()
print(json.dumps(dict(observed_at=dt.datetime.now(dt.timezone.utc).isoformat(), source=str(source),
    resume_from=str(destination), checkpoint_sha256=h.hexdigest(), bytes=destination.stat().st_size,
    copy_attempts=attempts, top_level_keys=list(value),
    cpu_inspection=dict(load_succeeded=True, map_location='cpu', all_tensors_cpu=True, cuda_initialized=False,
        model_state_present=True, model_state_nonempty=True, optimizer_state_present=True,
        optimizer_state_nonempty=True, scheduler_state_present=True, scheduler_state_nonempty=True,
        optimizer_state_count=len(optimizer['state']), optimizer_parameter_groups=len(optimizer['param_groups']),
        scheduler_keys=list(scheduler), meta=dict(epoch=int(meta['epoch']), best_miou=float(meta['best_miou']),
            epochs_no_improve=int(meta['epochs_no_improve']))),
    partial_current_epoch_saved=False, resume_authorized_by_this_operation=False)))
