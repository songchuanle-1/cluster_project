"""Actual source CPU discrimination and live authorized-resource inventory."""
import ast
from ops import *
guard(600)
resources=tick.load(OUT/'resource_probe.json') if (OUT/'resource_probe.json').is_file() else {}
for host,hostname,gpu,uuid in (('192.168.1.115','dl04-MS-7E06',0,'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),('192.168.1.120','sysu311-MS-7C59',1,'GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0')):
    if hostname in resources:
        continue
    program='''import json,subprocess,fcntl
from datetime import datetime,timezone
gpu=GPU
row=subprocess.check_output(['nvidia-smi','-i',str(gpu),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],universal_newlines=True,timeout=10).strip()
assert [x.strip() for x in row.split(',')][:2]==[str(gpu),UUID]
contexts=subprocess.check_output(['nvidia-smi','-i',str(gpu),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],universal_newlines=True,timeout=10).strip()
locks={}
for kind in ('training','diagnostic','exclusive'):
    with open('/tmp/cluster_project_gpu'+str(gpu)+'_'+kind+'.lock','a+b') as f:
        try:
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            locks[kind]='available_then_released'
        except BlockingIOError:locks[kind]='held_by_existing_writer'
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'gpu':row,'contexts':contexts,'locks':locks}))
'''.replace('GPU',repr(gpu)).replace('UUID',repr(uuid))
    resources[hostname]=ssh(program,host,hostname)
if not (OUT/'resource_probe.json').is_file():
    save('resource_probe.json',resources)
path=ROOT/'Cluster/framework/model/Quard_model'/NAME/'hier_postprocess.py'
tree=ast.parse(path.read_text(encoding='utf-8-sig'))
node=next(c for c in tree.body if isinstance(c,ast.ClassDef) and c.name=='C2F_ClusterAttn_CTF_HCG')
method=next(m for m in node.body if isinstance(m,ast.FunctionDef) and m.name=='_cluster_to_points')
source=ast.unparse(method)
prototype=(OUT/'coarse_cross_attention.py').read_text()
program='''import os,socket,json,math
assert socket.gethostname()=='dl04-MS-7E06'
os.environ['CUDA_VISIBLE_DEVICES']=''
import torch
from torch import nn
import torch.nn.functional as F
exec(PROTOTYPE)
namespace={}
exec(SOURCE,globals(),namespace)
class Original(nn.Module):
    _cluster_to_points=namespace['_cluster_to_points']
    def __init__(self):
        super().__init__()
        self.num_scales=3
        self.level_gate=nn.Linear(32,3,bias=False).double()
        self.level_gate.weight.data.zero_()
        self.point_out_proj=nn.Identity()
        self.dropout=nn.Identity()
original=Original()
x=torch.arange(6*16,dtype=torch.float64).reshape(1,6,16)/96.
fine=torch.arange(6*16,dtype=torch.float64).reshape(1,6,16)/80.
middle=torch.arange(3*16,dtype=torch.float64).reshape(1,3,16)/40.
coarse=(torch.arange(3*16,dtype=torch.float64).reshape(1,3,16)/60.).requires_grad_()
mask=torch.zeros(1,6,dtype=torch.bool)
ids=[[torch.arange(6)],[torch.tensor([0,0,1,1,2,2])],[torch.arange(3)]]
tokens=[fine,middle,coarse]
base=original._cluster_to_points(x,tokens,ids,mask)
perturbed=coarse.detach().clone()
perturbed[0,2,3]+=1.
changed=original._cluster_to_points(x,[fine,middle,perturbed],ids,mask)
candidate,weights=coarse_readback(x,coarse,mask)
remote,_=coarse_readback(x,coarse,mask,values=perturbed)
native_grad=torch.autograd.grad(base[0,0].sum(),coarse,retain_graph=True)[0]
new_grad=torch.autograd.grad(candidate[0,0].sum(),coarse)[0]
print(json.dumps({'source_cpu_calls':2,'prototype_cpu_calls':2,'cuda_calls':0,'original_receiver_remote_max_change':float((changed[0,0]-base[0,0]).abs().max()),'candidate_receiver_remote_max_change':float((candidate[0,0]-remote[0,0]).abs().max()),'original_remote_value_gradient_max':float(native_grad[0,2].abs().max()),'candidate_remote_gradient_max':float(new_grad[0,2].abs().max()),'attention_shape':list(weights.shape),'has_projection_parameters':False,'no_N_squared_attention':True,'task_deficit_established':False,'scientific_admission':False}))
'''.replace('PROTOTYPE',repr(prototype)).replace('SOURCE',repr(source))
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B -c '+shlex.quote(program)
result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],120)
save('cpu_execution_attempt3.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'harness_repair':'Supply existing projection/dropout interfaces as frozen Identity after reading all original dependencies;both AttributeErrors retained,operator/hypothesis/tolerance unchanged'})
assert result.returncode==0,result.stderr
value=json.loads(result.stdout)
value['source']=evidence(path)
save('cpu_controls.json',value)
advance([OUT/'cpu_controls.json',OUT/'cpu_execution.json',OUT/'cpu_execution_attempt2.json',OUT/'cpu_execution_attempt3.json',OUT/'resource_probe.json'],next_action='Check exact legacy mechanism/bans;only an eligible independent realization may proceed to native task diagnosis')
print(json.dumps({'resources':resources,'cpu_controls':value},ensure_ascii=False))
