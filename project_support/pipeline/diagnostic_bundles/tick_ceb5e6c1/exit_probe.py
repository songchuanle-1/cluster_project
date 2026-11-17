"""Collect exact original run disposition and stable checkpoint metadata."""
import json,shlex
from ops import guard,save,ssh,run,NAME,REMOTE_ROOT,OUT
guard()
program=r'''import json,re,socket,hashlib
from pathlib import Path
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06'
name=%r;root=Path(%r)
folder=Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints')/name/'20261017_230113'
logs=list(folder.glob('*.log'));assert len(logs)==1
native=logs[0].read_text(errors='replace')
launcher=root/'logs'/('train_'+name+'_20261017_230107.log');launchtext=launcher.read_text(errors='replace')
markers=re.findall(r'.*Early stopping at epoch (\d+): no improvement for (\d+) epochs \(best=([0-9.]+)\).*',native)
values=[float(v) for v in re.findall(r'mIoU\s*:\s*([0-9.]+)',native)]
traces=[line for text in (native,launchtext) for line in text.splitlines() if 'Traceback (most recent call last)' in line or 'CUDA out of memory' in line or 'RuntimeError:' in line or 'TypeError:' in line]
value={'observed_at':datetime.now(timezone.utc).isoformat(),'native_log':str(logs[0]),'launcher_log':str(launcher),
    'native_log_sha256':hashlib.sha256(logs[0].read_bytes()).hexdigest(),'launcher_log_sha256':hashlib.sha256(launcher.read_bytes()).hexdigest(),
    'earlystop_markers':markers,'native_validation_miou':values,'native_validation_count':len(values),'best_native_miou':max(values),
    'last_native_steps':re.findall(r'Epoch \[(\d+)/(\d+)\]\[(\d+)/(\d+)\]',native)[-2:],
    'error_markers':traces,'last_native_summary':native.splitlines()[-6:],
    'checkpoint_metadata':{},'pid_alive':Path('/proc/1995443').exists()}
import torch
assert not torch.cuda.is_initialized()
for filename in ('best.pth','last.pth'):
    p=folder/filename;before=p.stat()
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
    checkpoint=torch.load(p,map_location='cpu',weights_only=False,mmap=True)
    meta={k:v for k,v in checkpoint.get('meta',{}).items() if isinstance(v,(int,float,str,bool))}
    value['checkpoint_metadata'][filename]={'path':str(p),'sha256':h.hexdigest(),'bytes':before.st_size,'mtime_ns':before.st_mtime_ns,
        'meta':meta,'optimizer_present':'optimizer' in checkpoint,'scheduler_present':'lr_scheduler' in checkpoint}
    after=p.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
    del checkpoint
assert not torch.cuda.is_initialized()
value['cuda_initialized']=False
value['disposition']='done_earlystop' if len(markers)==1 and not traces and not value['pid_alive'] else 'unknown_requires_review'
print(json.dumps(value))
'''%(NAME,REMOTE_ROOT)
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && CUDA_VISIBLE_DEVICES= python -B -c '+shlex.quote(program)
response=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],180)
save('exit_probe_execution.json',dict(returncode=response.returncode,stdout=response.stdout,stderr=response.stderr));assert response.returncode==0,response.stderr
value=json.loads(response.stdout);save('exit_result.json',value)
print(json.dumps({'disposition':value['disposition'],'native_validation_count':value['native_validation_count'],'best_native_miou':value['best_native_miou'],
    'earlystop_markers':value['earlystop_markers'],'checkpoint_meta':{k:v['meta'] for k,v in value['checkpoint_metadata'].items()},'error_markers':value['error_markers']}))
