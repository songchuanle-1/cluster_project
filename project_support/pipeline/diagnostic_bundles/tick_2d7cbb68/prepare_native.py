"""Freeze same-prefix native controls without editing the production model."""
import ast
import copy
from datetime import datetime,timezone
import shutil
from ops import *

owner=guard(600)
source_root=ROOT/'Cluster/framework/model/Quard_model'
legacy={}
for suffix in ('attnpool','qcond','agg','multi'):
    path=source_root/('model_base1_quard2_c2f_enc_lite_'+suffix)/'hier_postprocess.py'
    parsed=ast.parse(path.read_text(encoding='utf-8-sig'))
    bank=next(c for c in parsed.body if isinstance(c,ast.ClassDef) and c.name=='SharedClusterBank')
    build=next(m for m in bank.body if isinstance(m,ast.FunctionDef) and m.name=='build_cluster_feats')
    legacy[suffix]={'source':evidence(path),'aggregation_definition_sha256':tick.digest(path),'aggregation_function_lines':[build.lineno,build.end_lineno]}
legacy['distinctions']={'attnpool':'Unchanged mean cluster bank;no learned pooling weights or cluster-internal pooled query',
 'qcond':'No decoder/language query,selected-cluster point expansion,QKVprojections or qcond gate',
 'agg':'No learned point weighting/MLP in cluster aggregation',
 'multi':'No extra cluster tokens or changed scale/cluster counts',
 'TrueRoute':'No hard top-k or query-to-cluster route injection;point queries read all8coarse tokens',
 'FLE':'No intra-fine-leaf point graph;fine/middle paths unchanged;coarse-only global semantic source',
 'relation_transport':'No raw2D identity evidence,language relation span or candidate-mask identity transport',
 'residual_gate':'Only replaces coarse readback;existing fusion/output projections remain fixed in structure. Algebraic delta in diagnostic is not a new learned residual/gate.'}
legacy['ban_scope_review']='Specific historical mechanisms are not reused;this does not establish novelty or admission. Dense point-coarse attention is O(N*Kcoarse),notN2;no new projection parameters.'
save('eligibility_review.json',legacy)
protocol={'preregistered_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,
 'conditions':['original','own_coarse_identity','coarse_attention','uniform_coarse_mean','cyclic_key_value_mismatch'],
 'readouts':['actual original native criterion/components','actual mask-target/index/num_boxes fingerprint equality','mask/scores/indicator changes','positive-query mask IoU at native logit0 threshold,diagnostic only','coarse-value and message gradients','attention entropy and own-coarse probability'],
 'sampling':'same frozen2TRAINscenes/8expressions;within-prefix pairing only;no efficacy/populationCI',
 'prediction':'Own-coarse identity reconstructs native1e-6;coarse attention creates an active differentiable remote semantic path distinct from uniform and mismatched value controls. No pretraining accuracy/loss benefit threshold.',
 'investigate_before_admission':'An unexplained adverse native response,no-op,collapsed attention or missing task-relevant diagnosis cannot be passed by weakening gates',
 'tolerance':1e-6,'new_model_full_native_backward':'Pending;the first original forward plus new suffix gradient is NOT the full candidate backward gate',
 'production_changes':False,'training':False}
save('native_controls_protocol.json',protocol)
template=ROOT/'pipeline/diagnostic_bundles/tick_819a58d8/native_task_suffix.py'
tree=ast.parse(template.read_text())
changes={'import':0,'observer':0,'native':0,'suffix':0,'loop':0,'name':0}
def stmts(text):return ast.parse(text).body
class Native(ast.NodeTransformer):
    def visit_Import(self,node):
        self.generic_visit(node)
        if any(n.name=='numpy' for n in node.names):
            changes['import']+=1
            return [node,*stmts('from coarse_cross_attention import coarse_readback\nimport torch.nn.functional as functional')]
        return node
    def visit_Assign(self,node):
        self.generic_visit(node)
        target=ast.unparse(node.targets[0]) if len(node.targets)==1 else ''
        if target=='flags':
            changes['observer']+=1
            return [node,*stmts('''match_trace=[]
positive_trace=[]
original_loss_masks=model.criterion.loss_masks
def observed_loss_masks(pred_masks,pred_scores,targets,indices,num_boxes):
    match_trace.append(fingerprint(torch,([target.get('masks') for target in targets],indices,num_boxes)))
    summary=[]
    for b,(qi,ti) in enumerate(indices):
        if len(qi)==0 or targets[b].get('masks') is None:
            summary.append(None)
            continue
        predicted=pred_masks[b][qi].detach()>0
        target=targets[b]['masks'][ti].detach().bool()
        intersection=(predicted&target).sum(-1).float()
        union=(predicted|target).sum(-1).clamp_min(1).float()
        summary.append({'positive_queries':len(qi),'mean_mask_iou':float((intersection/union).mean().cpu())})
    positive_trace.append(summary)
    return original_loss_masks(pred_masks,pred_scores,targets,indices,num_boxes)
model.criterion.loss_masks=observed_loss_masks
''')]
        if target=='(loss, components)':
            changes['suffix']+=1
            return [node,*stmts("held['last_loss']=loss\nheld['last_matching']=list(match_trace)\nheld['last_positive_iou']=list(positive_trace)\nmatch_trace.clear()\npositive_trace.clear()")]
        return node
    def visit_AugAssign(self,node):
        self.generic_visit(node)
        if ast.unparse(node.target)=="r['native_forwards']":
            changes['native']+=1
            return [node,*stmts("r['native_matching']=list(match_trace)\nr['native_positive_query_iou']=list(positive_trace)\nmatch_trace.clear()\npositive_trace.clear()")]
        return node
    def visit_Try(self,node):
        self.generic_visit(node)
        start=next((i for i,n in enumerate(node.body) if isinstance(n,ast.Assign) and len(n.targets)==1 and ast.unparse(n.targets[0])=='weight'),None)
        if start is not None:
            end=next(i for i in range(start,len(node.body)) if isinstance(node.body[i],ast.Assert) and ast.unparse(node.body[i].test).startswith('[p.requires_grad'))
            node.body[start:end]=stmts('''
r['baseline_matching_identical']=held['last_matching']==r['native_matching']
assert r['baseline_matching_identical']
r['coarse_conditions']=[]
coarse=tokens[-1]
assert coarse.requires_grad
composed=[]
own=torch.zeros_like(x)
for b in range(x.shape[0]):
    index=ids[0][b].long()
    for level in range(1,len(ids)):
        index=ids[level][b].long()[index]
    composed.append(index)
    own[b,:len(index)]=coarse[b,index]
assert isinstance(cluster.point_out_proj,torch.nn.Linear)
level_weights=cluster.level_gate(torch.cat([x,x.mean(1,keepdim=True).expand_as(x)],-1)).softmax(-1)
def make_message(mode):
    if mode=='own_coarse_identity':
        replacement=own
        attention=None
    elif mode=='uniform_coarse_mean':
        replacement=coarse.mean(1,keepdim=True).expand_as(x).masked_fill(mask.unsqueeze(-1),0)
        attention=None
    else:
        values=coarse.roll(1,1) if mode=='cyclic_key_value_mismatch' else None
        replacement,attention=coarse_readback(x,coarse,mask,heads=cluster.nhead,values=values)
    delta=(replacement-own)*level_weights[:,:,-1:]
    raw=original_gather(x,tokens,ids,mask)
    r['source_interface_forwards']+=1
    raw=raw+functional.linear(delta,cluster.point_out_proj.weight,None)
    msg=cluster.message_norm(raw).masked_fill(mask.unsqueeze(-1),0)
    return msg,attention
for mode in ('own_coarse_identity','coarse_attention','uniform_coarse_mean','cyclic_key_value_mismatch'):
    message,attention=make_message(mode)
    output,loss,components=suffix(message)
    condition={'condition':mode,'message_max_change':error(message,base),
               'mask_max_change':error(output[2],normal[2]),'score_max_change':error(output[1],normal[1]),
               'native_loss':loss,'native_loss_delta':loss-base_loss,'components':components,
               'matching_identical':held['last_matching']==r['native_matching'],
               'positive_query_iou':held['last_positive_iou']}
    assert condition['matching_identical'],'Native supervision matching changed'
    if mode=='own_coarse_identity':
        condition['identity_passed']=max(condition['message_max_change'],condition['mask_max_change'],condition['score_max_change'],abs(condition['native_loss_delta']))<=1e-6
        assert condition['identity_passed'],condition
    else:
        message_gradient,coarse_gradient=torch.autograd.grad(held['last_loss'],(message,coarse),retain_graph=True)
        condition['message_gradient_finite']=bool(torch.isfinite(message_gradient).all())
        condition['coarse_gradient_finite']=bool(torch.isfinite(coarse_gradient).all())
        condition['message_gradient_norm']=float(message_gradient.norm().cpu())
        condition['coarse_gradient_norm']=float(coarse_gradient.norm().cpu())
        assert condition['message_gradient_finite'] and condition['coarse_gradient_finite']
        assert condition['message_gradient_norm']>0 and condition['coarse_gradient_norm']>0
        r['suffix_gradient_probes']=r.get('suffix_gradient_probes',0)+1
    if attention is not None:
        entropy=-(attention.clamp_min(1e-30).log()*attention).sum(-1)
        own_probability=[]
        for b,index in enumerate(composed):
            rows=attention[b,:,:len(index)]
            own_probability.append(float(rows.gather(-1,index[None,:,None].expand(rows.shape[0],-1,1)).mean().cpu()))
        condition['attention_entropy_mean']=float(entropy.masked_select((~mask)[:,None,:].expand_as(entropy)).mean().cpu())
        condition['own_coarse_probability_per_expression']=own_probability
        condition['attention_shape']=list(attention.shape)
    r['coarse_conditions'].append(condition)
r['new_candidate_full_native_backward_passed']=False
r['diagnosis_gate_passed']=False
r['task_deficit_status']='Pending task-level interpretation;path activity alone is not proof of a bottleneck'
''')
            changes['loop']+=1
        return node
    def visit_Constant(self,node):
        if node.value=='native_task_suffix_result.json':
            changes['name']+=1
            return ast.Constant('native_coarse_result.json')
        return node
tree=Native().visit(tree)
assert changes=={k:1 for k in changes},changes
ast.fix_missing_locations(tree)
label='native_coarse'
local=OUT/label
local.mkdir(exist_ok=False)
(local/'native_coarse.py').write_text(ast.unparse(tree)+'\n',encoding='utf-8')
shutil.copyfile(OUT/'coarse_cross_attention.py',local/'coarse_cross_attention.py')
shutil.copyfile(ROOT/'pipeline/diagnostic_bundles/tick_ce9bc689/trace_m95_1/native_runtime.py',local/'native_runtime.py')
manifest=copy.deepcopy(tick.load(ROOT/'pipeline/diagnostic_bundles/tick_819a58d8/task_suffix/native_manifest.json'))
stage=STAGE+'/'+label
manifest.update(candidate_id=CID,stage=stage,protocol=evidence(OUT/'native_controls_protocol.json'),eligibility=evidence(OUT/'eligibility_review.json'))
manifest['diagnostic_files']={name:tick.digest(local/name) for name in ('native_runtime.py','native_coarse.py','coarse_cross_attention.py')}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
advance([OUT/'eligibility_review.json',OUT/'native_controls_protocol.json',local/'native_manifest.json',local/'native_coarse.py',OUT/'prepare_native.py'],
        next_action='Execute frozen same-prefix native TRAIN criterion and actual matching controls;then investigate adverse/no-op responses before any admission')
ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
result=run(['scp',*SSH,*[str(local/n) for n in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')],'songcl@192.168.1.115:'+stage+'/'])
assert result.returncode==0,result.stderr
guard(500)
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B '+shlex.quote(stage+'/native_coarse.py')+' --lease '+shlex.quote(stage+'/execution_lease.json')
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],min(900,int(remaining)-120))
save('native_execution.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
pull=run(['scp',*SSH,'songcl@192.168.1.115:'+stage+'/native_coarse_result.json',str(local/'native_coarse_result.json')])
assert pull.returncode==0,pull.stderr
value=tick.load(local/'native_coarse_result.json')
advance([local/'native_coarse_result.json',OUT/'native_execution.json'],failure_scope='inconclusive',gate_result='Original native+new same-prefix controls executed='+str(value.get('execution_completed'))+';full candidate backward/resources/independence/diagnosis are not yet PASS')
print(json.dumps({k:v for k,v in value.items() if k not in ('before','after','records')},ensure_ascii=False))
