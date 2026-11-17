"""Non-GPU executable preparation,not a fabricated admission or task result."""
from ops import *
import ast,shutil
from expression_metrics import select_donors,summarize
guard(180)
old=ROOT/'pipeline/diagnostic_bundles/tick_28fc3749'
previous=tick.load(old/'native_manifest.json')
assert len(previous['cohort'])==8
shutil.copy2(old/'native_runtime.py',OUT/'native_runtime.py')
for name in ('native_expression_task.py','native_runtime.py','expression_metrics.py'):ast.parse((OUT/name).read_text(encoding='utf-8'),filename=name)
fixture=[{'scene_id':'a','expression_ids':[{'object_id':'1'},{'object_id':'1'},{'object_id':'2'}]},{'scene_id':'b','expression_ids':[{'object_id':'7'},{'object_id':'7'}]}]
_,donors=select_donors(fixture);assert donors=={0:2,1:2,2:0,3:None,4:None}
rows=[{'scene_id':'a','expression_index':0,'native_query':1,'donor_minus_own_probability_error':.2},{'scene_id':'a','expression_index':1,'native_query':2,'donor_minus_own_probability_error':.4},{'scene_id':'b','expression_index':2,'native_query':None,'donor_minus_own_probability_error':None}]
summary=summarize(rows);assert abs(summary['scene_balanced_effect']-.3)<1e-12
assert summarize(rows+[rows[0]])['scene_balanced_effect']==summary['scene_balanced_effect']
save('expression_metric_contracts.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'syntax_passed':True,'donor_skips_same_target':True,'no_other_target_returns_unknown':True,'scene_balanced_known_effect_passed':True,'duplicatequery_does_not_reweightscene':True,'synthetic_statistics_only':True,'native_task_tests':0,'scientific_passes':0})
protocol={'preregistered_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,'cohort':previous['cohort'],'assets_source':evidence(old/'native_manifest.json'),
 'intervention':'Onlyposthierarchymessagefromfixedsame-scenedifferentoriginalobjectexpression;recipientquery/coreinst/language/weights/gate/ILA/positions/head/nativegroundtruth/matchedqueriesunchanged.',
 'target_binding':'Mainannotationobject_idmustbelongtooriginalCriterionobject_idss;mainbinarymaskequalsoriginalsp_ins_labels==object_id. Readonlyoriginalpositivequery/targetpairswhoseexistingtargetexactlymatchesthatmask;missingqueriesareUNKNOWN,notreselected.',
 'point_correspondence':'Exactsameoriginalscene,validitymask,nativespatialcoordinatesintheoriginaldecoderargs,andall3existingassignmentlistsmustmatchbetweendonor/recipientbeforetransplant. CachedIDequalityaloneisnotnativephysicalpointproof.',
 'controls':'Capturedownmessageidentity/nativeILAfeature/nativeprediction_headmask+score/copyidentity/transplantthenrestoreidentityandbitwiseoriginalquery;unchanged1e-6. NoCPU/GPUmessage-reconstructionthresholdwaiverforoldscalediagnosis.',
 'primary':'Donorminusownmeanabs(sigmoid(actualnative_mask_logit)-originalbinarytarget);positivepredicted. Meanquerieswithinexpression,expressionswithinscene,scenesequally;reportdenominators/missing,notpopulationefficacy.',
 'resource':'Freshforegroundleaseandpinnedserver4GPU0idleness/all3exclusiveflocksrequired;server3GPU1alternativecurrentlyNVMLfailurecannotbeused. Noproductionchanges/newtraining/restarts.',
 'history_boundary':'NotM202QFenergy/spatialpermutation,notM95scaledeletion/boundarygroups,notlanguage/queryselectionorCPAkeytuning. Oldclosedrejectionsandallstrictfailurespreserved.',
 'current_status':'Preparedonly,CPUactualprefixidentity/indexobservedandstatisticsfixturepassed;actualnativeGPUtaskruns0,allscientificgatesfalse.'}
save('native_expression_protocol.json',protocol)
manifest={'schema_version':1,'candidate_id':CID,'root':previous['root'],'stage':'/data/songcl/Project/Cluster_project/pipeline/native_expression_87d50f0c','name':NAME,'assets':previous['assets'],'cohort':previous['cohort'],'expected_epoch':16,'tolerance':1e-6,'diagnostic_files':{name:tick.digest(OUT/name) for name in ('native_expression_task.py','native_runtime.py','expression_metrics.py')},'protocol':evidence(OUT/'native_expression_protocol.json'),'scope':'Preparedsame-sceneexpressionmessagefixedquerydiagnostic;notlaunched/admitted'}
save('native_manifest.json',manifest)
save('expression_preparation_result.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'native_manifest':evidence(OUT/'native_manifest.json'),'protocol':evidence(OUT/'native_expression_protocol.json'),'metric_contracts':evidence(OUT/'expression_metric_contracts.json'),'native_task_runs':0,'new_training':0,'scientific_passes':0,'next_test':'AfterfreshauthorizedexclusiveGPUandassetsverification,runpair0native_expression_task.py,onlythenremaining3pairsifallstrictcontrols pass.'})
advance([OUT/name for name in ('native_expression_task.py','native_runtime.py','expression_metrics.py','expression_metric_contracts.json','native_expression_protocol.json','native_manifest.json','expression_preparation_result.json','prepare_expression_native.py')],stage='validation',gate_result='ActualM95CPUmessagevariation/copy/indexcontractsobserved;nativeexpressiontransplanttaskentranceandmetriccontractsprepared. Noactualmasktaskresult/benefit/nativephysicalcoordinatecontrolPASSyet. OldQFandscale-boundarydiagnosticsnotreopened.')
print(json.dumps({'prepared':True,'frozen_scenes':8,'expressions':32,'statistics_contracts_passed':True,'native_gpu_runs':0,'scientific_passes':0},ensure_ascii=True))
