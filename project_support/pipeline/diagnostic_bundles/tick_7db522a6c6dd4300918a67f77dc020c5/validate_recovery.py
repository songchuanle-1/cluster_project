"""Validate the same experiment's complete native CPU resume before any recovery."""

import json
from pathlib import Path
from audit_terminal import BUNDLE, PROJECT, SSH, PYTHON, command, save, monitor

exp = monitor.load_experiment(str(PROJECT), "M201-BPS")
server = monitor.load_servers(str(PROJECT))["server-4"]
root = server["remote_code_root"]
checkpoint = server["work_dir"] + "/" + Path(exp["config"]).stem + "/20261014_154431/last.pth"
assets = "/data/songcl/Project/Cluster_project/pipeline/transport_port_75d7e1ea35634b1fa29749fcf54163c8/assets"
env = {
    "CUDA_VISIBLE_DEVICES": "", "OMP_NUM_THREADS": "2", "MKL_NUM_THREADS": "2",
    "PYTHONPATH": root + ":" + root + "/framework/lib",
    "LD_LIBRARY_PATH": "/home/songcl/.conda/envs/project_cluster/lib:/home/songcl/.conda/envs/project_cluster/lib/python3.10/site-packages/torch/lib",
    "TMPDIR": "/data/songcl/Project/Cluster_project/pipeline/tmp",
    "HF_HUB_OFFLINE": "1", "TOKENIZERS_PARALLELISM": "false", "PYTHONDONTWRITEBYTECODE": "1",
}
program = f"""
import os
os.environ.update({env!r})
import datetime,fcntl,hashlib,json,pathlib,subprocess,sys
sys.path[:0]=[{root!r},{root + "/framework/lib"!r}]
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
import torch,tools.train,gorilla
from framework import resolve_network
torch.set_num_threads(2)
assert not torch.cuda.is_initialized()
cfg=gorilla.Config.fromfile({root + "/" + exp["config"]!r})
assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
manifest=json.loads((pathlib.Path({assets!r})/'source_manifest.json').read_text())
package=pathlib.Path({root!r})/'framework/model/Quard_model'/{Path(exp["config"]).stem!r}
for name,expected in manifest['package'].items():
    assert hashlib.sha256((package/name).read_bytes()).hexdigest()==expected,name
path=pathlib.Path({checkpoint!r});before=path.stat()
saved=torch.load(path,map_location='cpu',weights_only=False,mmap=True)
assert saved['meta']=={{'epoch':26,'best_miou':0.489848792552948,'epochs_no_improve':8,'time':'Thu Oct 15 02:44:31 2026'}}
gorilla.set_random_seed(1999)
model=resolve_network({exp["config"]!r})(**cfg.model)
extra=set(saved['model'])-set(model.state_dict())
assert extra=={{'text_encoder.embeddings.position_ids','text_encoder.embeddings.token_type_ids'}}
assert not (set(model.state_dict())-set(saved['model']))
buffers=dict(model.named_buffers())
assert all(torch.equal(saved['model'][key].cpu(),buffers[key].cpu()) and
           saved['model'][key].dtype==buffers[key].dtype for key in extra)
filtered={{key:value for key,value in saved['model'].items() if key not in extra}}
model.load_state_dict(filtered,strict=True)
optimizer=gorilla.build_optimizer(model,cfg.optimizer)
scheduler=gorilla.build_lr_scheduler(optimizer,cfg.lr_scheduler)
restored=gorilla.resume(model=model,filename=str(path),optimizer=optimizer,scheduler=scheduler,
                       strict=False,map_location='cpu')
def identical(left,right):
    if isinstance(left,torch.Tensor):
        return isinstance(right,torch.Tensor) and left.shape==right.shape and left.dtype==right.dtype and torch.equal(left.cpu(),right.cpu())
    if isinstance(left,dict):
        return isinstance(right,dict) and left.keys()==right.keys() and all(identical(left[key],right[key]) for key in left)
    if isinstance(left,(list,tuple)):
        return isinstance(right,(list,tuple)) and len(left)==len(right) and all(identical(a,b) for a,b in zip(left,right))
    return left==right
assert identical(optimizer.state_dict(),saved['optimizer'])
assert identical(scheduler.state_dict(),saved['scheduler'])
assert restored==saved['meta']
assert all(parameter.grad is None and parameter.device.type=='cpu' for parameter in model.parameters())
h=hashlib.sha256()
with path.open('rb') as stream:
    for block in iter(lambda:stream.read(8*1024**2),b''):h.update(block)
after=path.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
locks={{}};handles=[]
try:
    for name in ('/tmp/cluster_project_gpu0_m201_migration.lock',
                 '/tmp/cluster_project_gpu0_exclusive.lock',
                 '/tmp/cluster_project_gpu0_parameter_transport.lock'):
        f=open(name,'a+b');handles.append(f)
        try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[name]='available'
        except BlockingIOError:locks[name]='held'
finally:
    for f in reversed(handles):f.close()
assert not torch.cuda.is_initialized()
print(json.dumps({{'status':'PASS','observed_at':datetime.datetime.now().astimezone().isoformat(),
    'checkpoint':str(path),'checkpoint_sha256':h.hexdigest(),'checkpoint_bytes':before.st_size,
    'meta':restored,'strict_model_state_after_identical_constant_audit':True,
    'identical_nonpersistent_constants':sorted(extra),'native_resume_strict_argument':False,
    'optimizer_state_exact':True,
    'optimizer_state_count':len(saved['optimizer']['state']),'scheduler_state_exact':True,
    'package_source_exact':True,'next_epoch':27,'seed':1999,'epochs':50,'scheduler_max_iters':70,
    'cuda_initialized':False,'native_forwards':0,'parameter_gradients':0,'optimizer_steps':0,
    'locks':locks,'gpu':subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip(),
    'compute':subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip(),
    'scope':'Same M201 complete-state CPU resume only; interrupted epoch27 would replay, no mid-epoch/RNG/bitwise claim; no GPU recovery launched'}},
    default=lambda value:value.item()))
"""
try:
    output = command(SSH + [PYTHON, "-B", "-"], program, timeout=120)
except BaseException as exc:
    save("recovery_attempt3_failure", {"status": "FAIL", "error_type": type(exc).__name__, "error": str(exc)})
    raise
result = json.loads(output.splitlines()[-1])
save("recovery_validation", {"raw_output": output, **result})
print(json.dumps(result))
