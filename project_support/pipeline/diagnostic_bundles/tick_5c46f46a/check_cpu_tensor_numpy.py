"""CPU-only interop diagnostic, explicitly not a native training test or fix proof."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

BASE=Path(__file__).resolve().parent
PAYLOAD=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
import datetime as dt,hashlib,json
from pathlib import Path
import torch,numpy as np
assert not torch.cuda.is_initialized()
torch.set_num_threads(1)
def check(i):
    labels=torch.tensor([0,0,1,1,2,2,2,-100],dtype=torch.int64)
    values=np.unique(labels)
    assert values.tolist()==[-100,0,1,2]
    for v in values:
        mask=labels==v
        assert mask.device.type=='cpu' and mask.dtype==torch.bool
        assert np.where(mask)[0].tolist()==[j for j,x in enumerate(labels.tolist()) if x==v]
        assert np.array_equal(mask.numpy(),np.asarray(mask))
    return int(i)
for i in range(1000):check(i)
class InteropDataset(torch.utils.data.Dataset):
    def __len__(self):return 1000
    def __getitem__(self,index):return check(index)
loader=torch.utils.data.DataLoader(InteropDataset(),batch_size=4,num_workers=4,persistent_workers=True,shuffle=False)
seen=0
for epoch in range(2):
    for batch in loader:seen+=int(batch.numel())
assert seen==2000 and not torch.cuda.is_initialized()
del loader
helper=torch.Tensor.__array__.__globals__['has_torch_function_unary']
root=Path('/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1')
dataset=root/'framework/dataset/scannetv2.py'
print(json.dumps(dict(observed_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    hostname=socket.gethostname(),torch_version=torch.__version__,numpy_version=np.__version__,
    torch_file=torch.__file__,numpy_file=np.__file__,torch_C_file=torch._C.__file__,
    has_torch_function_unary=dict(module=getattr(helper,'__module__',None),name=getattr(helper,'__name__',None),callable=callable(helper)),
    dataset_sha256=hashlib.sha256(dataset.read_bytes()).hexdigest(),
    fresh_cpu_process=dict(iterations=1000,passed=True),
    synthetic_persistent_workers=dict(workers=4,epochs=2,samples=seen,passed=True),
    cuda_initialized=False,GPU_computation=False,native_data_loaded=False,native_training_executed=False,
    failed_sample_index='UNKNOWN_NOT_PRESENT_IN_LOG',original_long_worker_state='NOT_REPRODUCED',
    root_cause='UNKNOWN',runtime_fixed=False,configuration_source_environment_changed=False)))
'''
def main():
    command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
             'songcl@192.168.1.115','/home/songcl/.conda/envs/project_cluster/bin/python -B -']
    r=subprocess.run(command,input=PAYLOAD,capture_output=True,text=True,encoding='utf-8',timeout=90)
    result=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),command=command,
        payload_sha256=hashlib.sha256(PAYLOAD.encode()).hexdigest(),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
    if r.returncode==0:result['data']=json.loads(r.stdout)
    target=BASE/'cpu_tensor_numpy_check.json'
    with target.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(path=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),**result.get('data',{})),ensure_ascii=False))
    if r.returncode:raise SystemExit(r.returncode)

if __name__=='__main__':main()
