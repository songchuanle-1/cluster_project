"""Localize current semantic controls to fixed native mask-error points."""
import ast
import copy
from datetime import datetime,timezone
import shutil
from ops import *
owner=guard(400)
protocol={'preregistered_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,
 'scope':'First2fixedTRAINscenes only,not all8;diagnostic error localization,not a new loss/model or population efficacy',
 'groups':'For each expression,union of wrong point labels among the ORIGINAL native matched-positive query masks,restricted to valid points. Complement are original correct points. Freeze groups before interventions;groundtruth is diagnostic only.',
 'readouts':'Per-group count,native original message-gradient dot candidate message-change(first-order surrogate only),actual changed mask-logit magnitude. Compare raw-key candidate,uniform mean,cyclic mismatch and identity with unchanged native criterion/matching.',
 'next_if_inconclusive':'Continue SAMEstableID with this frozen protocol on remaining6predefinedTRAINscenes before any diagnosis/admission claim;do not repeat resources,backward or old audits',
 'new_training':False,'new_loss':False,'tolerance':1e-6}
save('error_readout_protocol.json',protocol)
tree=ast.parse((OUT/'raw_key_revision1/native_raw_key.py').read_text())
changes={'support':0,'readout':0,'name':0}
class Errors(ast.NodeTransformer):
    def visit_FunctionDef(self,node):
        self.generic_visit(node)
        if node.name=='observed_loss_masks':
            insertion=ast.parse('''if 'error_support' not in held:
    held['error_support']=[]
    for b,(qi,ti) in enumerate(indices):
        if len(qi)==0 or targets[b].get('masks') is None:
            held['error_support'].append(None)
        else:
            predicted=pred_masks[b][qi].detach()>0
            target=targets[b]['masks'][ti].detach().bool()
            valid=~held['gather'][3][b]
            held['error_support'].append(((predicted!=target).any(0)&valid).detach().clone())
''').body
            index=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Return))
            node.body[index:index]=insertion
            changes['support']+=1
        return node
    def visit_Assign(self,node):
        self.generic_visit(node)
        if len(node.targets)==1 and ast.unparse(node.targets[0])=='condition':
            changes['readout']+=1
            return [node,*ast.parse('''condition['error_group_readouts']=[]
delta=(message-base).detach()
for b,error_group in enumerate(held['error_support']):
    if error_group is None:
        condition['error_group_readouts'].append(None)
        continue
    valid=~mask[b]
    groups={'original_error':error_group,'original_correct':valid&~error_group}
    entry={}
    for group_name,support in groups.items():
        count=int(support.sum().cpu())
        entry[group_name]={'points':count,'native_gradient_dot_message_delta':float((native_gradient[b,support].double()*delta[b,support].double()).sum().cpu()),'message_delta_norm':float(delta[b,support].norm().cpu()),'mask_logit_max_change':float((output[2][b,:,support]-normal[2][b,:,support]).abs().max().cpu()) if count else None}
    condition['error_group_readouts'].append(entry)
''').body]
        return node
    def visit_Constant(self,node):
        if node.value=='native_raw_key_result.json':changes['name']+=1;return ast.Constant('native_error_readout_result.json')
        return node
tree=Errors().visit(tree)
assert changes=={k:1 for k in changes},changes
ast.fix_missing_locations(tree)
local=OUT/'error_readout'
local.mkdir(exist_ok=False)
(local/'native_error_readout.py').write_text(ast.unparse(tree)+'\n',encoding='utf-8')
for n in ('native_runtime.py','coarse_cross_attention_r1.py'):shutil.copyfile(OUT/'raw_key_revision1'/n,local/n)
manifest=copy.deepcopy(tick.load(OUT/'raw_key_revision1/native_manifest.json'))
stage=STAGE+'/error_readout'
manifest.update(stage=stage,cohort=manifest['cohort'][:2],error_protocol=evidence(OUT/'error_readout_protocol.json'))
manifest['diagnostic_files']={p.name:tick.digest(p) for p in local.iterdir()}
save('error_readout/native_manifest.json',manifest)
save('error_readout/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
advance([OUT/'error_readout_protocol.json',local/'native_manifest.json',local/'native_error_readout.py'],next_action='Execute fixed original-error-point readout on first2scenes;remaining6unrun under this new readout,not a scientific failure')
ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
sc=run(['scp',*SSH,*[str(p) for p in local.iterdir()],'songcl@192.168.1.115:'+stage+'/'])
assert sc.returncode==0,sc.stderr
guard(320)
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B '+shlex.quote(stage+'/native_error_readout.py')+' --lease '+shlex.quote(stage+'/execution_lease.json')
result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],min(400,int(remaining)-150))
save('error_readout_execution.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
pull=run(['scp',*SSH,'songcl@192.168.1.115:'+stage+'/native_error_readout_result.json',str(local/'native_error_readout_result.json')])
assert pull.returncode==0,pull.stderr
value=tick.load(local/'native_error_readout_result.json')
advance([local/'native_error_readout_result.json',OUT/'error_readout_execution.json'],next_action='Interpret errorlocalized controls,then complete this same frozen readout on remaining6scenes;do not repeat passed native/resources or claim admission')
print(json.dumps({'execution_completed':value.get('execution_completed'),'controls_passed':value.get('controls_passed'),'error':value.get('error'),'conditions':[{'condition':c['condition'],'loss_delta':c['native_loss_delta'],'error_readouts':c['error_group_readouts']} for c in value.get('coarse_conditions',[])]},ensure_ascii=False))
