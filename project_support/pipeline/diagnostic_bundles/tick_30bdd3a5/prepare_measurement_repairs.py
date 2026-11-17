"""Preregister bounded diagnostic-only repairs before observing their results."""
from gpu1_ops import *
import ast,copy,shutil
guard(360)
scope='Diagnosticmeasurementonly;no model/config/precision/tolerance/weights/targets/query/cohortchange;not a newtrainable realization.'
plans=[
 ('expression','expression_fix','m95-expression-specific-point-message','native_expression_task.py',
  'Native target is bool. Probability-minus-bool raises RuntimeError after all5native identity controls exactly0,so no error rows were measured.',
  'Cast only originalbinarytarget0/1 to the originalpredictiondtype inside the2probability-error arithmetic expressions. Do not relabel or change selection.',
  'All5exactnativecontrolsremain<=1e-6;native boolvaluesandtyped0/1areidentical,errorcalculationfinite,originaltargetmatchingunchanged.'),
 ('scale','scale_fix','m95-scale-specific-boundary-responsibility','native_scale_task.py',
  'Original source/ILA/head/identity errors0,but full-source receiverpermutation2.86102294921875e-6 fails1e-6. This control re-evaluates global-mean/fusion logits despite the preregistered conditionalintervention holding fusion fixed.',
  'Retain/recompute original full-source permutation failure separately. Test the SAME conditional intervention operator under receiverpermutation with ORIGINALfusionlogits permuted,not reestimated. Add frozen-gate identity. Native baseline and actualscale-deletion taskcode unchanged.',
  'Frozen-original-fusion identity and receiverpermutation meet unchanged1e-6 while originalfullsource errorremainsreported,possiblyfailed. Neverclaimfullnative sourcepermutationpassed;query/weights/cohort/deletionreadoutunchanged.')]
work=tick.load(ROOT/'pipeline/research_work.json')
for oldlabel,label,cid,entry,reason,change,prediction in plans:
 c=next(c for c in work['candidates'] if c['id']==cid);history=c.setdefault('revision_history',[])
 assert not history,'Useboundedstablehistory;do notreset revisions'
 result=tick.load(OUT/(oldlabel+'_pair_0_result.json'))
 assert result['execution_completed'] is False
 revision={'revision':1,'failure_scope':'implementation','scope':scope,'reason':reason,'change':change,'prediction':prediction,'preregistered_at':datetime.now(timezone.utc).isoformat(),'failure_evidence':[evidence(OUT/(oldlabel+'_pair_0_result.json')),evidence(OUT/(oldlabel+'_pair_0_execution.json'))],'result':'pending','evidence':[]}
 history.append(revision);c['failure_scope']='implementation'
 save(label+'_prereg.json',revision)
 folder=OUT/label;folder.mkdir()
 original=OUT/oldlabel;manifest=copy.deepcopy(tick.load(original/'native_manifest.json'))
 for name in manifest['diagnostic_files']:shutil.copy2(original/name,folder/name)
 tree=ast.parse((folder/entry).read_text(encoding='utf-8'))
 if oldlabel=='expression':
  class CastTarget(ast.NodeTransformer):
   count=0
   def visit_BinOp(self,node):
    self.generic_visit(node)
    if isinstance(node.op,ast.Sub) and isinstance(node.right,ast.Name) and node.right.id=='target':
     node.right=ast.parse('target.to(dtype=logits.dtype)',mode='eval').body;self.count+=1
    return node
  adapter=CastTarget();tree=adapter.visit(tree);assert adapter.count==2
 else:
  class FreezeControl(ast.NodeTransformer):
   count=0
   def visit_Assign(self,node):
    self.generic_visit(node)
    if len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='perm':
     self.count+=1
     original_statement=copy.deepcopy(node);original_statement.targets[0].id='full_source_perm'
     statements=ast.parse("""
result['full_source_permutation_max_error']=error(full_source_perm,torch.stack([base[b,index] for b,index in enumerate(p)]))
result['full_source_permutation_original_1e_minus6_passed']=result['full_source_permutation_max_error']<=1e-6
original_gate_logits=cluster.level_gate(torch.cat([x,x.mean(1,keepdim=True).expand_as(x)],-1))
gate_identity_hook=cluster.level_gate.register_forward_hook(lambda module,values,output:original_gate_logits)
try:
 frozen_identity=cluster.message_norm(original_gather(x,tokens,ids,mask)).masked_fill(mask.unsqueeze(-1),0)
finally:
 gate_identity_hook.remove()
controls['frozen_original_fusion_identity']=error(frozen_identity,base)
permuted_gate_logits=torch.stack([original_gate_logits[b,index] for b,index in enumerate(p)])
gate_permutation_hook=cluster.level_gate.register_forward_hook(lambda module,values,output:permuted_gate_logits)
try:
 perm=cluster.message_norm(original_gather(px,tokens,pi,pm)).masked_fill(pm.unsqueeze(-1),0)
finally:
 gate_permutation_hook.remove()
result['permutation_control_scope']='Conditionaloriginal-fusion-fixedinterventionoperator;NOTfullnative-sourcepermutationPASS. Originalfullsourceerrorretainedseparately.'
""").body
     return [original_statement,*statements]
    return node
  adapter=FreezeControl();tree=adapter.visit(tree);assert adapter.count==1
 ast.fix_missing_locations(tree);(folder/entry).write_text(ast.unparse(tree)+'\n',encoding='utf-8')
 ast.parse((folder/entry).read_text(encoding='utf-8'))
 manifest.update(stage='/data/songcl/Project/Cluster_project/pipeline/gpu1_30bdd3a5/'+label,
  diagnostic_files={name:tick.digest(folder/name) for name in manifest['diagnostic_files']},
  measurement_revision={'revision':1,'scope':scope,'preregistration':evidence(OUT/(label+'_prereg.json')),'failure':evidence(OUT/(oldlabel+'_pair_0_result.json'))})
 assert manifest['tolerance']==1e-6
 assert manifest['assets']==tick.load(original/'native_manifest.json')['assets']
 tick.save(folder/'native_manifest.json',manifest)
 for path in (OUT/(label+'_prereg.json'),folder/entry,folder/'native_manifest.json'):
  item=evidence(path)
  if item not in c['evidence']:c['evidence'].append(item)
guard();tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'registered_before_results':True,'measurement_revisions':2,'model_config_changes':0,'tolerance':1e-6,'original_failures_preserved':True},ensure_ascii=True))
