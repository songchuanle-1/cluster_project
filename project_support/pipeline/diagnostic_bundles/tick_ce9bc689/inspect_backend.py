"""Read installed sparse backend provenance; no CUDA initialization."""
import json
import shlex
from ops import guard,save,run,STAGE,HOST,SSH

guard(120)
program='''import importlib,json,pathlib,torch
assert not torch.cuda.is_initialized()
import spconv
from spconv.pytorch import conv
roots=[pathlib.Path(conv.__file__),pathlib.Path(spconv.__file__).parent/'algo.py']
items=[]
for path in roots:
    lines=path.read_text().splitlines()
    chosen=set()
    for i,line in enumerate(lines):
        if any(word in line for word in ('get_tuned_algo','tune_and_cache','algo_cache','class ConvTuner','cache_key','forward_cache','backward_input_cache','backward_weight_cache')):
            chosen.update(range(max(0,i-2),min(len(lines),i+5)))
    items.append({'path':str(path),'lines':len(lines),'excerpt':[str(i+1)+': '+lines[i] for i in sorted(chosen)][:150]})
assert not torch.cuda.is_initialized()
print(json.dumps({'torch':torch.__version__,'spconv':spconv.__version__,'cuda_initialized':torch.cuda.is_initialized(),'sources':items}))
'''
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
    'python -B -c '+shlex.quote('import socket\nassert socket.gethostname()=="dl04-MS-7E06"\n'+program))
r=run(['ssh',*SSH,'songcl@'+HOST,shlex.join(['bash','-lc',command])],60)
save('backend_source_execution.json',{'returncode':r.returncode,'stderr':r.stderr})
assert r.returncode==0,r.stderr
value=json.loads(r.stdout)
save('backend_source_excerpt.json',value)
print(json.dumps(value,indent=2))
