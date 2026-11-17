"""Nondeployable factorial control of own-context removal and remote addition."""
import ast
import copy
from datetime import datetime,timezone
import shutil
from ops import *
owner=guard(600)
reference=tick.load(OUT/'raw_key_revision1/native_manifest.json')
protocol={'preregistered_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,
 'scope':'Explanatory counterfactual diagnostic ONLY;not a new residual/gate design,implementation revision,admission or training variant',
 'cohort':'First8frozenTRAINscenes,unchanged from eight_scene_protocol.json;stop safely with unrun conditions marked if lease budget becomes insufficient',
 'causal_decomposition':'OriginalownV + removal[-(1-Aown)*Vown] + addition[sumremote Aremote*Vremote]. Both equals the current coarse replacement. Separate removal and addition while holding attention keys/weights,fine/middle/query/native matching fixed.',
 'conditions':['own_coarse_identity','own_removal_only','remote_addition_only','coarse_attention','remote_addition_mismatch'],
 'readouts':'Actual criterion/components,masks,positive-query IoU,matching;do not interpret fixed pretrained loss changes as trained harm/benefit or authorize a residual successor',
 'tolerance':1e-6,'new_model':False,'optimizer_steps':0}
save('replacement_attribution_protocol.json',protocol)
tree=ast.parse((OUT/'raw_key_revision1/native_raw_key.py').read_text())
source='''def make_message(mode):
    if mode=='own_coarse_identity':
        replacement=own
        attention=None
    else:
        attended,attention=coarse_readback(x,coarse,mask,heads=cluster.nhead,key_features=raw_coarse)
        own_weight=torch.zeros_like(x)
        width=x.shape[-1]//cluster.nhead
        for b,index in enumerate(composed):
            n=len(index)
            probability=attention[b,:,:n].gather(-1,index[None,:,None].expand(cluster.nhead,-1,1))
            own_weight[b,:n]=probability.permute(1,0,2).expand(-1,-1,width).reshape(n,-1)
        removal=-(1-own_weight)*own
        addition=attended-own_weight*own
        if mode=='own_removal_only':
            replacement=own+removal
        elif mode=='remote_addition_only':
            replacement=own+addition
        elif mode=='remote_addition_mismatch':
            wrong_values=coarse.roll(1,1)
            wrong,_=coarse_readback(x,coarse,mask,heads=cluster.nhead,key_features=raw_coarse,values=wrong_values)
            wrong_own=torch.zeros_like(own)
            for b,index in enumerate(composed):wrong_own[b,:len(index)]=wrong_values[b,index]
            replacement=own+wrong-own_weight*wrong_own
        else:
            replacement=own+removal+addition
    delta=(replacement-own)*level_weights[:,:,-1:]
    raw=original_gather(x,tokens,ids,mask)
    r['source_interface_forwards']+=1
    raw=raw+functional.linear(delta,cluster.point_out_proj.weight,None)
    msg=cluster.message_norm(raw).masked_fill(mask.unsqueeze(-1),0)
    return msg,attention
'''
newfunction=ast.parse(source).body[0]
changes={'function':0,'modes':0,'name':0}
class Factorial(ast.NodeTransformer):
    def visit_FunctionDef(self,node):
        if node.name=='make_message':changes['function']+=1;return newfunction
        return self.generic_visit(node)
    def visit_For(self,node):
        self.generic_visit(node)
        if ast.unparse(node.target)=='mode':
            node.iter=ast.parse("('own_coarse_identity','own_removal_only','remote_addition_only','coarse_attention','remote_addition_mismatch')",mode='eval').body
            changes['modes']+=1
        return node
    def visit_Constant(self,node):
        if node.value=='native_raw_key_result.json':changes['name']+=1;return ast.Constant('native_attribution_result.json')
        return node
tree=Factorial().visit(tree)
assert changes=={k:1 for k in changes},changes
ast.fix_missing_locations(tree)
text=ast.unparse(tree)+'\n'
summary=[]
for pair in range(4):
    remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
    if remaining<600:
        summary.append({'pair':pair,'executed':False,'reason':'Insufficient guarded lease budget;not resource block or scientific failure'})
        break
    guard(600)
    label='attribution_'+str(pair)
    local=OUT/label
    local.mkdir(exist_ok=False)
    (local/'native_attribution.py').write_text(text,encoding='utf-8')
    for name in ('native_runtime.py','coarse_cross_attention_r1.py'):shutil.copyfile(OUT/'raw_key_revision1'/name,local/name)
    manifest=copy.deepcopy(reference)
    stage=STAGE+'/'+label
    manifest.update(stage=stage,cohort=reference['cohort'][2*pair:2*pair+2],attribution_protocol=evidence(OUT/'replacement_attribution_protocol.json'))
    manifest['diagnostic_files']={p.name:tick.digest(p) for p in local.iterdir()}
    save(label+'/native_manifest.json',manifest)
    save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
    advance([OUT/'replacement_attribution_protocol.json',local/'native_manifest.json',local/'native_attribution.py'],next_action='Execute nondeployable own-removal/remote-addition controls;do not turn explanatory residual counterfactual into a new model')
    ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
    sc=run(['scp',*SSH,*[str(p) for p in local.iterdir()],'songcl@192.168.1.115:'+stage+'/'])
    assert sc.returncode==0,sc.stderr
    command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B '+shlex.quote(stage+'/native_attribution.py')+' --lease '+shlex.quote(stage+'/execution_lease.json')
    result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],min(600,int(remaining)-180))
    save(label+'_execution.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
    output='native_attribution_result.json'
    pull=run(['scp',*SSH,'songcl@192.168.1.115:'+stage+'/'+output,str(local/output)])
    assert pull.returncode==0,pull.stderr
    value=tick.load(local/output)
    advance([local/output,OUT/(label+'_execution.json')],gate_result='Explanation-only source decomposition pair'+str(pair)+' complete='+str(value.get('execution_completed'))+';no residual model or efficacy claim')
    summary.append({'pair':pair,'executed':True,'execution_completed':value.get('execution_completed'),'controls_passed':value.get('controls_passed'),'error':value.get('error'),'loss_deltas':{c['condition']:c['native_loss_delta'] for c in value.get('coarse_conditions',[])}})
    if not value.get('execution_completed'):break
save('replacement_attribution_summary.json',summary)
print(json.dumps(summary,ensure_ascii=False))
