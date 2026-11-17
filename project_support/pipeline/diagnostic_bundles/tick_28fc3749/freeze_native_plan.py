"""Complete bounded non-GPU preparation; no GPU dispatch or scientific PASS."""
from ops import *
import ast,copy,shutil
from scale_metrics import paired_interaction,summarize

guard(180)
old=ROOT/'pipeline/diagnostic_bundles/tick_2d7cbb68'
manifest=tick.load(old/'raw_key_revision1/native_manifest.json')
summary=tick.load(old/'eight_scene_execution_summary.json')
cohort=manifest['cohort'][:8]
assert [s['scene_id'] for s in cohort]==[scene for pair in summary for scene in pair['scene_ids']]
runtime=old/'raw_key_revision1/native_runtime.py'
shutil.copy2(runtime,OUT/'native_runtime.py')
for path in (OUT/'native_scale_task.py',OUT/'native_runtime.py',OUT/'scale_metrics.py'):
 ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
base={'identity':{'mixed':.2,'interior':.3},'delete_fine':{'mixed':.6,'interior':.4},'delete_coarse':{'mixed':.3,'interior':.5}}
assert abs(paired_interaction(base)-.4)<1e-12
empty=copy.deepcopy(base);empty['identity']['interior']=None
assert paired_interaction(empty) is None
rows=[{'scene_id':'fixture_a','expression_index':0,'conditions':base},{'scene_id':'fixture_a','expression_index':1,'conditions':empty},{'scene_id':'fixture_b','expression_index':2,'conditions':base}]
reference=summarize(rows)
assert abs(reference['scene_balanced_mean']-.4)<1e-12
assert summarize(rows+[rows[0]])['scene_balanced_mean']==reference['scene_balanced_mean']
save('metric_contracts.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'syntax_passed':True,'known_interaction_passed':True,'empty_group_returns_unknown':True,'same_expression_replication_does_not_reweight_scene':True,'fixture_only':True,'native_task_results':0,'scientific_diagnosis_passed':False})
plan={'preregistered_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,
 'cohort':'First8 scenes of existing frozen32-scene TRAIN manifest,in existing order;4original expressions per scene,no outcome-based selection',
 'checkpoint':'Available trainedM95epoch16;not verified historical champion weights',
 'capture':'Exact final cluster gathered refined tokens,points,assignments,padding,ILA inputs,final decoder query/output and final native criterion matching. No optimizer/backward/new training.',
 'controls':'Same-device source message identity,ILA feature identity,native prediction_head mask+score identity,zero identity and receiver permutation must meet unchanged1e-6. Preserve any failure and stop task interpretation.',
 'interventions':'Zero only one refined scale bank before exact native _cluster_to_points;original fixed fusion weights,projection bias,message_norm and encoder gate. No weight renormalization or new residual/gate.',
 'query':'Original final decoder returned query remains bitwise fixed;replay exact native ILA and prediction_head. Do not call whole decoder to update query.',
 'targets':'Exact final native Criterion.loss_masks targets and original positive query/target indices,selected by equality with captured final logits. Valid native superpoints only;binary labels0/1 must be exact.',
 'groups':'For each original matched target,original fine cell is mixed iff it contains both target0and1. Define before interventions;empty groups => unknown.',
 'primary':'Per receiver abs(sigmoid(native_mask_logit)-original_binary_target). Fine-deletion excess mixed-versus-interior minus coarse-deletion excess mixed-versus-interior. Positive is preregistered direction,not a tuned cutoff.',
 'aggregation':'Mean matched-query contrasts within expression,then expressions within scene,then scenes equally. Report counts/empty groups;queries and expressions are not independent scenes. Four fixed scene-pairs;no population CI/efficacy claim.',
 'numerics':'CPU float32 failures and float64 precision discrimination retained;CPU/GPU cached-message mismatch remains a failed1e-6 control. Only fresh same-device native controls can establish task replay validity;do not waive/relax gates.',
 'resources':'New execution needs fresh current foreground lease,server4 pinned hostname+GPU0UUID,live idleGPU and all3exclusiveflocks. Alternate authorized server3GPU1 currently occupied and exact frozen assets not mirrored. No sharing/eviction/automatic launch.',
 'current_execution':'Prepared and CPU-checked only;0nativeGPU task runs;no new training admission.'}
save('native_scale_protocol.json',plan)
new={'schema_version':1,'candidate_id':CID,'root':manifest['root'],'stage':'/data/songcl/Project/Cluster_project/pipeline/native_scale_28fc3749','name':NAME,'assets':manifest['assets'],'cohort':cohort,'expected_epoch':16,'tolerance':1e-6,
 'diagnostic_files':{name:tick.digest(OUT/name) for name in ('native_scale_task.py','native_runtime.py','scale_metrics.py')},
 'protocol':evidence(OUT/'native_scale_protocol.json'),'scope':'Prepared frozen native mask diagnostic only;not launched,not a scientific admission'}
save('native_manifest.json',new)
save('native_preparation_result.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'manifest':evidence(OUT/'native_manifest.json'),'protocol':evidence(OUT/'native_scale_protocol.json'),'cohort_scenes':len(cohort),'expressions':32,'source_syntax_and_metric_contracts':evidence(OUT/'metric_contracts.json'),'native_gpu_executions':0,'native_task_controls_passed':False,'scientific_diagnosis_passed':False,'next_test':'After fresh authorized exclusive slot verification,stage frozen3runnerfiles+manifest;bind a fresh foreground lease and run native_scale_task.py --pair0,then remaining pairs only after exact controls pass.'})
advance([OUT/name for name in ('native_scale_task.py','native_runtime.py','scale_metrics.py','metric_contracts.json','native_scale_protocol.json','native_manifest.json','native_preparation_result.json','freeze_native_plan.py')],stage='validation',native_plan=plan['primary'],next_action='Execute frozen native same-device controls and fixed-query scale-deletion paired task masks on first8frozenTRAINscenes only when an authorized idle exclusiveGPU is verified. Retain allCPUstrict numeric failures;native control failure is INCONCLUSIVE,not permission to relax thresholds.')
print(json.dumps({'prepared':True,'native_gpu_executions':0,'scientific_diagnosis_passed':False,'cohort_scenes':8,'expressions':32,'metric_contracts':reference},ensure_ascii=True,indent=2))
