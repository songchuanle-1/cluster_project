"""Preregister next fixed-query stage after the measured native geometry result."""
import ast
import json
import shutil
from ops import ROOT,OUT,TOKEN,GOAL,IDS,guard,tick,save,evidence,now
guard(900)
geometry=tick.load(OUT/'relabel_result.json')
assert geometry['execution_completed'] and geometry['controls_passed'] and len(geometry['records'])==4
assert all(all(level['physical_co_membership_changed'] for level in row['levels']) for row in geometry['records'])
base=tick.load(OUT/'native_resolution/native_manifest.json')
folder=OUT/'native_relabel_mask'
folder.mkdir(exist_ok=False)
shutil.copyfile(OUT/'native_resolution/native_runtime.py',folder/'native_runtime.py')
shutil.copyfile(OUT/'native_relabel_mask_task.py',folder/'native_relabel_mask_task.py')
ast.parse((folder/'native_relabel_mask_task.py').read_text())
cohort=base['cohort'][::2]
assert [row['scene_id'] for row in cohort]==[row['scene_id'] for row in geometry['records']]
protocol=save('relabel_mask_protocol.json',{'preregistered_at':now(),'candidate_id':IDS[1],'token':TOKEN,'goal_sha256':GOAL,
    'basis':evidence(OUT/'relabel_result.json'),'cohort':cohort,'pairs':2,'expression_count':16,
    'question':'Do native physical hierarchy changes under lossless row relabeling reach inst_feats and fixed-query masks,with original targets/prefix held?',
    'intervention':'Reverse only native coordinates before original FPS/partitioner;inverse-remap fine membership to original physical feature rows;reuse coherent deeper memberships/childmaps and original native aggregation/refinement/ILA/head. No model/config/feature/query/target changes.',
    'controls':'Original point/features/mask/scores/identity/tokenreaggregation all<=original1e-6;exact inverse coordinate permutation,unchanged prefix/query hashes. No threshold deletion/waiver. Raw readouts may be saved on failed float control but task interpretation MUST remain inconclusive and scientificadmissionFALSE.',
    'readout':'All native primary-target matched queries;mean sigmoid absolute probability error perquery,then expression,then fixedscene. Correlatedrows;no populationCI/validationselection/efficacy or trainable repair.',
    'prior_failure_preserved':evidence(OUT/'resolution_pair_0_result.json'),
    'limits':'Geometryconfirmed4fixedscenes,not maskharm or novelty. This stage is same stable diagnosticID,not mechanism revision/new model. No optimizer/backward/training,canonicalseedrepair or re-opening historical routes.'})
manifest={key:base[key] for key in ('schema_version','root','name','assets','expected_epoch','tolerance')}
manifest.update(candidate_id=IDS[1],stage='/data/songcl/Project/Cluster_project/pipeline/native_a1b2de4f_relabel_mask_gpu0',
    cohort=cohort,protocol=evidence(protocol),physical_gpu=0,gpu_uuid=base['gpu_uuid'],scientific_admission=False,
    diagnostic_files={name:tick.digest(folder/name) for name in ('native_runtime.py','native_relabel_mask_task.py')})
with (folder/'native_manifest.json').open('x',encoding='utf-8') as stream:
    json.dump(manifest,stream,ensure_ascii=False,indent=2)
work=tick.load(ROOT/'pipeline/research_work.json')
row=next(row for row in work['candidates'] if row['id']==IDS[1])
row.update(stage='validation',updated_at=now(),next_action='Run two frozen 4-scene16expression nativefixedquery relabelmask pairs;all originalstrictcontrols apply. Retain every failure and label failed-controltaskreadouts inconclusive;no training.')
row['evidence'].extend([evidence(protocol),evidence(folder/'native_manifest.json'),evidence(folder/'native_relabel_mask_task.py')])
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'protocol':evidence(protocol),'cohort_scenes':[row['scene_id'] for row in cohort],'pairs':2,'tolerance':1e-6,'new_models':0},indent=2))
