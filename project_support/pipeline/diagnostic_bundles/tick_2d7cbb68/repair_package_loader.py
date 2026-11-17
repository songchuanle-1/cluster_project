"""Avoid dual registration by importing only the tested candidate package."""
import ast
import copy
from datetime import datetime,timezone
import shutil
from ops import *
owner=guard(900)
failed=OUT/'independent_package/native_package_candidate_result.json'
failure=tick.load(failed)
assert failure['execution_completed'] is False and failure['error_type']=='KeyError'
assert failure['native_train_forwards']==failure['native_train_backwards']==0
protocol={'preregistered_at':datetime.now(timezone.utc).isoformat(),
 'failure_evidence':evidence(failed),'scope':'Diagnostic loader isolation only;candidate code/realization/keys/hyperparameters unchanged',
 'cause':'Loader unnecessarily constructed M95 then imported independent candidate into the same process;both loss.py definitions register Criterion. This is not a native candidate forward/backward failure.',
 'repair':'In a fresh process import ONLY candidate package and load the same frozen checkpoint directly,using canonical source/buffer/state/seed checks. Do not clear or override registries,force registration,edit installed packages,or rerun successful champion resources.',
 'full_candidate_backward':'pending','scientific_admission':False}
save('package_loader_repair_protocol.json',protocol)
tree=ast.parse((OUT/'native_package_resources.py').read_text())
setup_source='''def setup_candidate_direct():
    import torch,gorilla
    import importlib.util
    sys.path[:0]=[MANIFEST['root'],str(Path(MANIFEST['root'])/'framework/lib')]
    from tools import train
    assert not torch.cuda.is_initialized()
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(.75,0)
    importlib.import_module('framework.model.Quard_model')
    name=MANIFEST['candidate_name']
    qualified='framework.model.Quard_model.'+name
    path=STAGE/name
    spec=importlib.util.spec_from_file_location(qualified,path/'__init__.py',submodule_search_locations=[str(path)])
    module=importlib.util.module_from_spec(spec)
    sys.modules[qualified]=module
    spec.loader.exec_module(module)
    cfg=gorilla.Config.fromfile(str(STAGE/(name+'.yaml')))
    assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
    assert cfg.dataloader.train.batch_size==2 and cfg.dataloader.train.num_workers==4
    gorilla.set_random_seed(1999)
    model=module.Network(**cfg.model)
    checkpoint=torch.load(MANIFEST['assets']['checkpoint'],map_location='cpu',weights_only=False,mmap=True)
    state=checkpoint['model']
    extra=set(state)-set(model.state_dict())
    buffers={'text_encoder.embeddings.position_ids','text_encoder.embeddings.token_type_ids'}
    assert extra<=buffers
    assert all(torch.equal(state[k],dict(model.named_buffers())[k]) for k in extra)
    model.load_state_dict({k:v for k,v in state.items() if k not in extra},strict=True)
    meta=checkpoint['meta']
    del checkpoint,state
    model.cuda().eval()
    return torch,gorilla,cfg,model,meta
'''
tree.body.insert(0,ast.parse(setup_source).body[0])
changes={'setup':0,'output':0}
class Repair(ast.NodeTransformer):
    def visit_Try(self,node):
        self.generic_visit(node)
        start=next((i for i,n in enumerate(node.body) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='setup'),None)
        if start is not None:
            end=next(i for i in range(start,len(node.body)) if isinstance(node.body[i],ast.Assert) and 'original_flags' in ast.unparse(node.body[i]))
            node.body[start:end+1]=ast.parse('''assert args.target=='candidate'
torch,gorilla,cfg,model,meta=setup_candidate_direct()
assert meta['epoch']==16
state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
original_flags={k:p.requires_grad for k,p in model.named_parameters()}
hierarchy=importlib.import_module('framework.model.Quard_model.'+MANIFEST['candidate_name']+'.hier_postprocess')
''').body
            changes['setup']+=1
        return node
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Name) and node.func.id=='save':
            node.args[0]=ast.parse("'native_package_'+args.target+'_isolated_result.json'",mode='eval').body
            changes['output']+=1
        return node
tree=Repair().visit(tree)
assert changes=={'setup':1,'output':1},changes
ast.fix_missing_locations(tree)
label='package_isolated'
local=OUT/label
local.mkdir(exist_ok=False)
(local/'native_package_isolated.py').write_text(ast.unparse(tree)+'\n',encoding='utf-8')
info=tick.load(OUT/'independent_package.json')
name=info['name']
shutil.copytree(Path(info['source_path']),local/name)
shutil.copyfile(ROOT/info['candidate_config']['path'],local/(name+'.yaml'))
shutil.copyfile(ROOT/'pipeline/diagnostic_bundles/tick_ce9bc689/trace_m95_1/native_runtime.py',local/'native_runtime.py')
manifest=copy.deepcopy(tick.load(OUT/'independent_package/native_manifest.json'))
stage=STAGE+'/'+label
manifest.update(stage=stage,loader_repair=evidence(OUT/'package_loader_repair_protocol.json'))
manifest['diagnostic_files']={p.relative_to(local).as_posix():tick.digest(p) for p in local.rglob('*') if p.is_file()}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
advance([OUT/'package_loader_repair_protocol.json',failed,local/'native_manifest.json',local/'native_package_isolated.py'],
 next_action='Run unchanged independent candidate in a fresh process without prior M95 registration;retain completed champion baseline and import failure')
ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
sc=run(['scp',*SSH,'-r',*[str(p) for p in local.iterdir()],'songcl@192.168.1.115:'+stage+'/'])
assert sc.returncode==0,sc.stderr
guard(600)
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B '+shlex.quote(stage+'/native_package_isolated.py')+' --lease '+shlex.quote(stage+'/execution_lease.json')+' --target candidate'
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],min(1000,int(remaining)-180))
save('package_isolated_execution.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
output='native_package_candidate_isolated_result.json'
pull=run(['scp',*SSH,'songcl@192.168.1.115:'+stage+'/'+output,str(local/output)])
assert pull.returncode==0,pull.stderr
value=tick.load(local/output)
advance([local/output,OUT/'package_isolated_execution.json'],gate_result='Isolated full candidate native/resources completed='+str(value.get('execution_completed'))+';do not infer diagnosis,efficacy or admission')
print(json.dumps({k:value.get(k) for k in ('execution_completed','error_type','error','native_train_forwards','native_train_backwards','native_predict_calls','parameters','profile','median_ms','p90_ms','peak_allocated_bytes')},ensure_ascii=False))
