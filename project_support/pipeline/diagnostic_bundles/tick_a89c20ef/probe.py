"""Read-only authorized-device inventory and a source-executed CPU control."""
import ast
from ops import *

guard(600)
results = {}
for host, hostname, gpu, uuid in (
    ('192.168.1.115', 'dl04-MS-7E06', 0, 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),
    ('192.168.1.120', 'sysu311-MS-7C59', 1, 'GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0')):
    program = '''import json,subprocess,fcntl
from datetime import datetime,timezone
gpu=GPU
row=subprocess.check_output(['nvidia-smi','-i',str(gpu),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],universal_newlines=True,timeout=10).strip()
fields=[x.strip() for x in row.split(',')]
assert fields[:2]==[str(gpu),UUID]
contexts=subprocess.check_output(['nvidia-smi','-i',str(gpu),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],universal_newlines=True,timeout=10).strip()
locks={}
for kind in ('training','diagnostic','exclusive'):
    with open('/tmp/cluster_project_gpu'+str(gpu)+'_'+kind+'.lock','a+b') as stream:
        try:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            locks[kind]='available_then_released'
        except BlockingIOError:locks[kind]='held_by_existing_writer'
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'gpu':row,'contexts':contexts,'locks':locks}))
'''.replace('GPU', repr(gpu)).replace('UUID', repr(uuid))
    results[hostname] = ssh(program, host, hostname)
save('resource_probe.json', results)
source = ROOT / 'Cluster/framework/model/Quard_model' / NAME / 'hier_postprocess.py'
tree = ast.parse(source.read_text(encoding='utf-8-sig'))
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'aggregate_cluster')
program = '''import ast,json,os,socket
assert socket.gethostname()=='dl04-MS-7E06'
os.environ['CUDA_VISIBLE_DEVICES']=''
import torch
from torch_scatter import scatter_mean,scatter_max
source=SOURCE
exec(compile(ast.Module(body=[ast.parse(source).body[0]],type_ignores=[]),'actual_aggregate_cluster','exec'))
x=torch.tensor([[-2.,1.],[2.,3.],[-4.,5.],[4.,7.]],dtype=torch.float64)
p=torch.tensor([[-1.,0.,0.],[1.,0.,0.],[-1.,0.,0.],[1.,0.,0.]],dtype=torch.float64)
ids=torch.tensor([0,0,1,1])
permuted=x[torch.tensor([1,0,3,2])]
a=aggregate_cluster(x,ids);b=aggregate_cluster(permuted,ids)
moment=lambda f:scatter_mean(p[:,:,None]*f[:,None,:],ids,dim=0)
print(json.dumps({'source_cpu_calls':2,'cuda_calls':0,'native_mean_max_change':float((a-b).abs().max()),'feature_position_moment_max_change':float((moment(x)-moment(permuted)).abs().max()),'blind_spot_in_this_aggregate_only':bool(torch.equal(a,b)),'task_deficit_established':False}))
'''.replace('SOURCE', repr(ast.unparse(fn)))
command = ('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B -c ' + shlex.quote(program))
result = run(['ssh', *SSH, 'songcl@192.168.1.115', shlex.join(['bash','-lc',command])],120)
save('source_control_execution.json', {'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
assert result.returncode == 0, result.stderr
value = json.loads(result.stdout)
value['source'] = evidence(source)
save('source_control.json', value)
advance([OUT/'resource_probe.json',OUT/'source_control.json'], next_action='Execute frozen native TRAIN feature-position permutation controls on the same captured prefix; no claim of an accuracy deficit from CPU nullspace.')
print(json.dumps({'resources':results,'source_control':value},ensure_ascii=False))
