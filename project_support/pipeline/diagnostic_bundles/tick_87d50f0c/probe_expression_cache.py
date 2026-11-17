"""First discriminating real-prefix CPU test; no task effect from distances."""
from ops import *
guard(180)
manifest=tick.load(ROOT/'pipeline/diagnostic_bundles/tick_ed0d2b32/rank_m95/native_manifest.json')
cohort=manifest['cohort'][:2]
save('cache_cohort_binding.json',{'source_manifest':evidence(ROOT/'pipeline/diagnostic_bundles/tick_ed0d2b32/rank_m95/native_manifest.json'),'cohort':cohort,'cache':'/data/songcl/Project/Cluster_project/pipeline/native_stride_ed0d2b32/rank_m95/rank_prefix.npz','cache_sha256':'46733f80cebfb2a3afe5a790d3b5ee6921beea2025de6803287940eca0d75132','source_provenance':'Originalrankcapture used first2TRAINscenes/8expressions;physicalpointcorrespondence must still be confirmed in native capture,not inferred from feature similarity.'})
program=r'''import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
prefix=Path('/data/songcl/Project/Cluster_project/pipeline/native_stride_ed0d2b32/rank_m95/rank_prefix.npz')
assert hashlib.sha256(prefix.read_bytes()).hexdigest()=='46733f80cebfb2a3afe5a790d3b5ee6921beea2025de6803287940eca0d75132'
with np.load(prefix,allow_pickle=False) as data:
 points=data['points'];mask=data['mask'];message=data['message']
 assert points.shape==message.shape and len(points)==8
 records=[]
 for scene_i,scene in enumerate(COHORT):
  start=scene_i*4;objects=[row['object_id'] for row in scene['expression_ids']]
  for expression in range(4):
   row=start+expression
   donor=next((start+(expression+shift)%4 for shift in range(1,4) if objects[(expression+shift)%4]!=objects[expression]),None)
   assert donor is not None
   n=int((~mask[row]).sum())
   same_mask=bool(np.array_equal(mask[row],mask[donor]))
   ids_equal=[bool(np.array_equal(data['ids_'+str(s)+'_'+str(row)],data['ids_'+str(s)+'_'+str(donor)])) for s in range(3)]
   delta=message[donor,:n].astype('float64')-message[row,:n].astype('float64')
   input_delta=points[donor,:n].astype('float64')-points[row,:n].astype('float64')
   identity=message.copy();identity[row]=message[row]
   transferred=message.copy();transferred[row,:n]=message[donor,:n]
   transferred[row]=message[row]
   records.append({'scene_id':scene['scene_id'],'recipient':row,'recipient_object_id':objects[expression],'donor':donor,'donor_object_id':objects[donor-start],'valid_receivers':n,'same_padding':same_mask,'same_scale_assignment_ids':ids_equal,'input_point_feature_max_change':float(np.max(np.abs(input_delta))),'hierarchy_message_max_change':float(np.max(np.abs(delta))),'message_rms_change':float(np.sqrt(np.mean(delta**2))),'own_identity_exact':bool(np.array_equal(identity,message)),'transplant_then_restore_exact':bool(np.array_equal(transferred,message))})
 assert all(row['same_padding'] and all(row['same_scale_assignment_ids']) and row['own_identity_exact'] and row['transplant_then_restore_exact'] for row in records)
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'records':records,'fixture_type':'Actual frozen trainedM95pointmessageprefix,not randomsynthetic','cached_expressions':8,'independent_scenes':2,'identity_and_index_contracts_passed':True,'actual_physical_superpoint_coordinates_in_cache':False,'native_targets_or_final_queries_in_cache':False,'actual_task_masks_replayed':False,'diagnosis_passed':False,'cuda_initialized':False,'new_training':0}))
'''
result=remote('server-4','COHORT='+repr(cohort)+'\n'+program,conda=True,timeout=150)
save('expression_cache_result.json',result)
advance([OUT/'cache_cohort_binding.json',OUT/'expression_cache_result.json',OUT/'probe_expression_cache.py'],stage='validation',gate_result='ActualM95within-scene expressionmessagevariation and exactcopy/index controls measured onCPU;noquery,target ornative maskcache,so taskdiagnosis remains UNPASSED. Featurevariation is not causal benefit.',next_action='Freeze exact native fixed-recipientquery message-transplant controls and originaltarget matching;verify live authorized GPUresources before actual task replay. Differentexpressiontaskinformation remains unknown.')
print(json.dumps({'observed_at':result['observed_at'],'records':result['records'],'task_masks_replayed':False,'scientific_passes':0},ensure_ascii=True,indent=2))
