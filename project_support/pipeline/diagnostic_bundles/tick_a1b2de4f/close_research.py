"""Honest bounded scientific cooldown after two native diagnostic routes."""
from collections import defaultdict
from datetime import datetime,timedelta,timezone
import json
import os
import shutil
import statistics
import subprocess
from ops import ROOT,OUT,SKILL,TOKEN,GOAL,IDS,guard,tick,save,evidence,now,remote

owner,_=guard(180)
resolution=tick.load(OUT/'resolution_pair_0_result.json')
geometry=tick.load(OUT/'relabel_result.json')
masks=[tick.load(OUT/('relabel_mask_pair_'+str(pair)+'_result.json')) for pair in range(2)]
native=tick.load(OUT/'native_aggregation_source_binding.json')['data']
training=tick.load(OUT/'M204_actual_output_checkpoint_metadata.json')['data']
assert not resolution['execution_completed'] and not resolution['baseline_controls_passed']
assert resolution['controls']['native_token_reaggregation']==1.9073486328125e-6
assert geometry['execution_completed'] and geometry['controls_passed'] and len(geometry['records'])==4
assert all(all(level['identity_equal'] and level['physical_co_membership_changed'] for level in scene['levels']) for scene in geometry['records'])
assert all(row['execution_completed'] and not row['controls_passed'] and row['task_interpretation']=='INCONCLUSIVE_STRICT_CONTROL_FAILURE' for row in masks)
assert all(row['controls']['native_token_reaggregation']==1.9073486328125e-6 for row in masks)
assert native['atomic_nondeterminism_documented'] and not native['cuda_initialized']
assert training['checkpoints']['best.pth']['meta']['epoch']==18
assert training['checkpoints']['best.pth']['meta']['best_miou']=='0.49925217'
assert training['checkpoints']['last.pth']['meta']['epoch']==27
assert training['checkpoints']['last.pth']['meta']['epochs_no_improve']==9

program="""import json,subprocess,fcntl
from datetime import datetime,timezone
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
assert [p.strip() for p in row.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
locks={}
for kind in ('training','diagnostic','exclusive'):
 with open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b') as handle:
  try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True
  except BlockingIOError:locks[kind]=False
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':row,'contexts':contexts,'locks_available':locks,'new_training':0}))
"""
released=remote('server-4',program)
release_path=save('final_gpu0_release.json',released)
assert released['returncode']==0 and not released['data']['contexts'] and all(released['data']['locks_available'].values())

expressions=defaultdict(list)
for pair,row in enumerate(masks):
    for record in row['records']:
        expressions[(record['scene_id'],pair,record['expression_index'])].append(record['relabeled_minus_original_probability_error'])
scenes=defaultdict(list)
for (scene,pair,index),values in expressions.items():
    scenes[scene].append(statistics.mean(values))
scene_means={scene:statistics.mean(values) for scene,values in scenes.items()}
raw_summary={'matched_native_query_rows':sum(len(row['records']) for row in masks),
    'observed_expression_count':len(expressions),'planned_expression_count':16,
    'observed_scene_count':len(scenes),'planned_scene_count':4,
    'scene_probability_error_delta':scene_means,
    'scene_balanced_raw_delta':statistics.mean(scene_means.values()) if scene_means else None,
    'scope':'Raw fixed-query readouts ONLY;strict native reaggregation controls failed on both pairs. No causal harm/benefit,efficacy,novelty or populationCI is established.'}

work=tick.load(ROOT/'pipeline/research_work.json')
aux_ids=['m95-native-relation-other-sign-conflict','m95-native-main-role-weight-precedence',
    'm95-native-secondary-positive-mass','m95-native-between-pair-support']
clock=datetime.now(timezone.utc)
aux_due=[row for row in work['candidates'] if row['id'] in aux_ids and datetime.fromisoformat(row['retry_after'])<=clock]
scope_path=None
if aux_due:
    scope_path=save('auxiliary_scope_recheck.json',{'observed_at':now(),'checked_ids':[row['id'] for row in aux_due],
        'goal_sha256':GOAL,'decision':'Latest mainline remains pointfeatureupdate;GPU authorization does not restore auxiliary priority or M201. Preserve all science and failures;no additional human consent or tests inferred.',
        'scope_changed':False,'scientific_result':None})
    for row in aux_due:
        row['last_scope_check_at']=now()
        row['retry_after']=(clock+timedelta(hours=4)).isoformat()
        row['evidence'].append(evidence(scope_path))
retry=(clock+timedelta(hours=2)).isoformat()
earliest=min([datetime.fromisoformat(row['retry_after']) for row in work['candidates'] if row['id'] in aux_ids]+[datetime.fromisoformat(retry)])

analysis=save('analysis.json',{'observed_at':now(),'token':TOKEN,'snapshot_at':'2026-10-19T20:09:18.413082+00:00',
    'scientific_status':'Native geometry order sensitivity measured in4fixedscenes;taskreadout causal interpretation INCONCLUSIVE due unchanged strict aggregation control failures. No new mechanism/admission/training.',
    'M204':{'native_early_stop_epoch':28,'total_epochs':50,'patience':10,'native_log_ended_at':'2026-10-19T20:06:30.610420+00:00',
        'best_checkpoint_epoch':18,'best_native_scalar_repr':'0.49925217','best_below_historical_M95':True,
        'actual_output_folder':training['actual_output_folder'],'last_checkpoint_epoch':27,'last_checkpoint_patience':9,
        'explanation':'Native earlystop break precedes checkpointsave. Original20261019_093003epoch5 input remains preserved;actual resumed outputs are20261019_162904. Registry stillrunning/deathwatch1of3 until canonical subsequent monitor reconciliation;not live training and no forcedcounter/queue edit.',
        'new_training_or_restart':False},
    'resolution':{'same_id':IDS[0],'actual_native_attempts_this_tick':1,'valid_supports':resolution['valid_supports'],
        'observed_fine_tokens':255,'baseline_control_values':resolution['controls'],'intervention_executed':False,
        'pairs_1_to_3':'UNRUN after original baseline guard failed;not claimed as failed or completedmask experiments.',
        'failure_scope':'inconclusive measurement/implementation,not hypothesisfalsification'},
    'relabel_geometry':{'same_id':IDS[1],'fixed_train_scenes':4,'identity_controls_passed_levels':12,
        'physical_co_membership_changed_levels':12,'original_first_physical_rows':[row['original_first_physical_row'] for row in geometry['records']],
        'reversed_first_physical_rows':[row['relabeled_first_physical_row'] for row in geometry['records']],
        'compiled_firstseed_behavior_measured':True,'supplied_source_binary_correspondence_proved':False,
        'scope':'Observed native property,not a proven harmful defect/innovation or fullGPUcentroidbitwiseCPUproof.'},
    'relabel_mask':{'native_pairs_executed':2,'native_loss_forwards':2,'strict_control_pass_pairs':0,
        'controls':[row['controls'] for row in masks],'raw_point_message_max_deltas':[row['point_message_max_delta'] for row in masks],
        'raw_mask_max_deltas':[row['mask_max_delta'] for row in masks],**raw_summary},
    'numerical_source_binding':{'atomic_nondeterminism_documented':True,'actual_failure_cause_isolated':False,
        'decision':'Original1e-6gate remains FAILED. No threshold reduction/removal,new seed/precision or model repair. Stop unchanged repetitions until a concrete controlpreserving diagnostic revision is preregistered.'},
    'this_tick_outputs':{'new_stable_candidates':0,'native_gpu_executions':4,'resolution_prefix_attempts':1,
        'native_geometry_scenes':4,'mask_pairs_executed':2,'mask_task_planned_expressions':16,
        'mask_task_observed_expressions':len(expressions),'native_backwards':0,'new_models':0,'admissions':0,'new_training':0,
        'checkpoint_metadata_probes':2,'aggregation_source_binding_probes':1,'aux_scope_rechecks':len(aux_due)},
    'resource_status':'GPU0 actuallyavailable/released,not a resourceblock. GPU1foreignoccupation andserver3SSHtimeout cached at04:12Shanghai;notre-polled to fabricate closure.',
    'stop_reason':'no_information_gain','stop_scope':'Further unchanged replays of these two finite native diagnostic implementations cannot remove their common failed numerical prerequisite;NOT no new observations this tick,NOT independent falsification of the mainline,NOT global routeexhaustion/resourceblock or deadlineexpiry.',
    'next_required_evidence':'A concrete preregistered measurementimplementation change with a causal prediction that preserves original native1e-6controls and every originalfailedresult. No specific justified repair currently established after sourcebinding audit;do not rerun unchanged probes or fabricate candidate fillers.',
    'candidate_retry_after':retry,'cooldown_not_after':earliest.isoformat(),
    'evidence':[evidence(OUT/name) for name in ('current_resources_and_training.json','gpu0_resource_binding.json',
        'resolution_pair_0_result.json','relabel_result.json','relabel_mask_protocol.json',
        'relabel_mask_pair_0_result.json','relabel_mask_pair_1_result.json','native_aggregation_source_binding.json',
        'M204_exit_and_checkpoint_metadata.json','M204_actual_output_checkpoint_metadata.json','final_gpu0_release.json')],
    'execution_status':'Report and finish still required;no postflight success claimed.'})

for row in work['candidates']:
    if row['id'] not in IDS:
        continue
    row.update(stage='blocked',updated_at=now(),failure_scope='inconclusive',
        blocker_kind='numerical_control_failure',
        blocker='Actual native tokenreaggregation control is1.9073486328125e-6 > unchanged1e-6 in resolutionpair0 and both relabelmaskpairs. GPU0isavailable;not a resource/authorizationblock. Native-source atomics documentation is compatible but exactcauseunisolated;no justified controlpreserving measurementrepair defined.',
        retry_after=retry,unblock_condition='New causal source/native measurement evidence supports a concrete preregistered bounded diagnosticimplementation revision preserving original1e-6control and allfailedresults. Timer alone never grantsPASS/rerun/revision/training or relaxes scientificgates.',
        next_action='Under SAME stableID inspect new controlpreserving measurementrepair evidence first. Do not repeat unchanged failedprefix/kernel probes,waive tolerance,select favorable pairs or infer task harm/benefit. No justified repair yet;keep originalfinite test evidence and numericalblock visible.',
        scientific_admission=False)
    row.pop('required_server',None)
    row.pop('physical_gpu',None)
    row['gate_result']=('Nativepair0 baselineguardfailedbeforeintervention;3remainingpairsUNRUN,maskeffectUNKNOWN,not corehypothesisfalsified.' if row['id']==IDS[0] else
        'Nativegeometry4scenes/12levels identitypassed and physicalmembershipchanged. Nativefixedquerymask2pairs/16plannedexpressions completedbutboth strictreaggregationcontrolsFAILED;rawmaskchange not causal harm/efficacy/admission.')
    row['evidence'].extend([evidence(OUT/'native_aggregation_source_binding.json'),evidence(analysis)])
work['design_cycle']={'updated_at':now(),'stop_reason':'no_information_gain','attempted_ids':list(IDS),
    'no_gain_reason':'Two independent interventions (batch-peer cardinality versus lossless row relabeling) were actually tested this tick. Their native task-readout implementations share an unresolved failed1e-6reaggregation prerequisite;geometry observations are new,not erased. Further unchanged replays cannotresolve it. No concrete admissible measurementrepair or separately evidenced independent executable route is currently established;not a global no-progress/no-novelty or independent mechanism-falsification claim.',
    'resume_condition':'Concrete new controlpreserving measurementimplementation evidence,preregisteredunderstableIDbeforetesting;originalstrictcontrols/failures preserved. Actual authorizedresource checks still required. No fallback to training,tuning,canonicalseedrepair or removed thresholds.',
    'retry_after':earliest.isoformat(),
    'evidence':[evidence(analysis),evidence(OUT/'native_aggregation_source_binding.json')],
    'attempt_results':[
        {'candidate_id':IDS[0],'hypothesis_id':'native-batch-peer-cardinality-coupling','test':'Original frozen native resolutionpair0 onactualsupports667/255;strictbaseline replay and tokenreaggregation.',
         'result':'Point/features/mask/scores/identitycontrols0;tokenreaggregation1.907e-6FAILS1e-6beforeintervention. No taskmaskpair completed;corecouplingnotfalsified. Originalremainingpairsheldbythatguard.',
         'evidence':[evidence(OUT/'resolution_pair_0_result.json')]},
        {'candidate_id':IDS[1],'hypothesis_id':'native-row-label-geometric-hierarchy-invariance','test':'Original nativeFPS/composedhierarchy4scene identity/inversegeometry,then preregistered2fixedquerymaskpairs/16expressions.',
         'result':'12/12physicalmembershipschangewith12/12identitycontrolsPASS. Bothmaskpairscompletedbuttokenreaggregation1.907e-6FAILS1e-6;rawmaskdeltasnotcausalharm/benefit. Numericalblocknotresourceunavailability or falsifiedrepair.',
         'evidence':[evidence(OUT/'relabel_result.json'),evidence(OUT/'relabel_mask_pair_0_result.json'),evidence(OUT/'relabel_mask_pair_1_result.json')]}]}
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
shutil.copyfile(ROOT/'pipeline/codex_memory.md',OUT/'memory_before.md')
memory='''# Codex Research Memory
## Goal And Phase
- Current a1b2de4f938b490c9f4cf17decc7a8f6,begin2026-10-19T20:09:18.413082Z/deadline21:09:18.413082Z(Oct20 04:09/05:09Shanghai),DESIGN. Actualowner01a04987-fdbe-7301-b2f0-f9b6ab60f74c/PipelineDisabled verified;onebegin,no duplicatepreflight.
- PRIORdc944b44 FINALIZED/PASS/contextcommitted;ownedlock+pendingabsent verified02:23:10Oct20. Neverfinish/abort/reuseoldtoken;oldmemoryprefinishwordingstale.
- GoalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85,25constraints/11bans,target.5100. Primaryhierarchicalpoint/inst_featsupdate;4supervisionIDsauxiliaryscopeholds,notrejection. Seed1999/epochs50/max_iters70/scienceunchanged.
- Server4[0,1],server3[1],1task/card,capacity3. DirectGPU1consent pipeline/authorizations/server4_gpu1_20261019.json remainsvalid;no repeatpermissionquestion. No server3GPU0/server6newdispatch,reset,eviction,restart,migration,schedulerchange.
- Pinnedserver4.115/dl04-MS-7E06 GPU0UUID958e741a-e5cf-127e-ffe8-9b984e1f404c,GPU1UUID7f82edb9-f620-8045-caea-a75232265cd1;server3.120/sysu311-MS-7C59 GPU1UUID340de111-e7e4-ed2d-15c9-8ab6a253e4a0. Strictknownhost/keySSH,passwordreferenceunread.
## Champion And Baseline
- HistoricalM95.5020,baseline.4894,target.5100,gap.0080. AvailablefrozenM95epoch16=.5024607181549072 NOTverifiedhistoricalchampionweights.
- CURRENTM204nativeearlystop28/50,patience10,logend2026-10-20 04:06:30Shanghai;bestnativecheckpointscalarrepr0.49925217@epoch18,belowhistoricalM95. CurrentfullVALpaireduncertaintyUNKNOWN,notcoreCPAglobalfalsification ornewchampion.
- CURRENTactualresumedoutput20261019_162904/best.pth epoch18;last.pth epoch27/noimprove9 because nativebreakprecedescheckpointsave. Bothinclude model/optimizer/scheduler andunchangedstat. Original20261019_093003best/lastarepreservedepoch5/.43399662INPUTS,notcurrentoutput. Bothmetadatareadsretained.
- CACHEDM203FLE.4885315597@epoch13,earlystop23/50,priorfullVALdelta-.0139291520/sceneCI[-.0223369116,-.0054631474];notrestarted.
## Active Hypotheses
- coarse-semantic-point-cross-attention/M204CPA-R1 registryTRAININGbutnativeprocessGONEandnormalearlystopconfirmed. Q=currentpoint,K=rawpreCTFcoarse,V=refinedcoarse;otherfine/middle/fusion/query/lossunchanged. Oneconnectionrevision,zeronewparams,no revision2/automaticrestart. Queuecanonicaldeathwatch1/3pending;doNOTforcecounters orcallanotherpreflight.
- CPA diagnosis/controls/constraintsUNPASSED;manualresumeexceptionNOTscientificadmission. Prior9.769168428GvsM959.762532428G,inferpeak+1.2878%,matchedtrainpeak+.3289%to+.7063%;fulloptimizerpeakUNKNOWN. Terminalsingle-runbelowchampionnotwholemechanismfalsification.
- hierarchy-native-batch-minimum-resolution nowBLOCKEDnumerical_control_failure,NOTresourceblocked. PriorCPU562/562census28support<256,min131,0missing/unknown;groups240/9372 REUSED,nocensusrerun.
- CURRENToriginalnativepair0executedonGPU0:8expressionssupports667x4/255x4,finetokens8x255x256. Point/features/mask/score/identityreplayerrors0,tokenreaggregation1.9073486328125e-6FAILSoriginal1e-6;assertstopsBEFOREintervention. Actualmaskpairscompleted0;originalpairs1-3UNRUN,notfailed/completed. Failureinconclusivemeasurement,notclamp-hypothesisfalsification;unchangedrerunsnotjustified.
- hierarchy-native-superpoint-relabeling-audit nowBLOCKEDsamenumericalprerequisite. CURRENToriginalnativeFPS/partition4frozenTRAINgeometriesscene0000/0001/0002/0003_00:12/12identitycontrolspass,12/12physicalco-membershipschangedafterinverse-labeling. Binaryfirstphysicalseed0->666/709/2328/405measured. Actualprovidedsource-binarycorrespondencestillUNPROVED.
- CURRENTpreregisteredfixedqueryrelabeledhierarchyMASKextension,2pairs/4scenes/16expressionsplanned,exactnativeprefix/query/targetsheld:bothcompletedbutboth1.907e-6tokenreaggregationFAIL1e-6;allotherfivefloatcontrols0. Rawpointmax1.5078/1.58795,rawmaskmax9.5246/11.1023;taskcausalinterpretationINCONCLUSIVE,notharm/benefit/admission. Queryrowscorrelated,no populationCI;actualcoverage/readoutsinanalysis.json.
- OldCPUfixedanchor0assignmentcontrolsarenotFPScontrols;oldCPUpreparedmeansnotbitwiseGPUscatterproof. ExactFPSCPUunsupportedattemptnotrepeated. CurrentnativegeometrypropertyobservedseparatelyfromCPUsourcewitness;doNOTre-runsamefiniteaudits.
- CURRENTinstalledtorch_scatter2.1.2/torch2.8.0+cu128sourcebindingshaff6a3fc29e3461675986fb73a3a82f6a76c264adc4dd3e6d1dbd01e8d0f11be2 documentsGPUatomicnondeterminism;actualmeanoperatorconfirmed. Consistentwithfailure,NOTisolatedcauseorpermissiontowaivetolerance. 0newkernelreplaysintheCPUsourceaudit.
## Closed Or Failed Directions
- Allrank/meanmoment/ancestry/padding/prefix/QF/HDS/FLEdiagnoses/rejections/bansanddirtyPDC/untrackedBCCA preserved. No renamedrouting/gate/residual/largeQKV/N2attention/tuning/canonicalseed singleoprepair/HDSrevision3/FLErestart/M201recovery.
- Prior8scene/32exprstudiesCOMPLETE,nottrainable:expressiondonorerror+.004466350020434506,7positive/1negative,295correlatedqueryrows;scaleboundaryinteraction-.006994256213229087,2positive/6negative,30/32expr. Not efficacy/populationCI/newmechanism;no unchangedreruns.
- Originalexpressionboolsubtractionfailure+revision1preserved. OriginalscaleFULLSOURCEpermutation2.86102294921875e-6FAILED1e-6all4;fixedfusioncontrols0NOTfullsourcePASS. CPUassignment0/currentgeometryPASSdoNOToverrideit.
- PriorCPUfloat32identity3.814697265625e-6/algebra2.4318695068359375e-5FAILED1e-6;float64internal0/4.44e-14butcachedGPUreconstruction7.48e-6FAILED. No thresholdwaiver/precisionoroptionalrepeatedkernelrepair/reopenedhistoricalfamilies.
## Running And Queue
- CURRENT04:09snapshotregistryactive1/target3,waiting0,candidatebudget2,reserve0/2,prep2,pending6/8=2primary+4auxholds. LaterM204nativeearlystopobserved;registryremainsrunningpendingcanonicalarchive,notlivetraining. 0newcandidates/models/admissions/queueentries/training.
- CURRENT04:12:24server4GPU0IDLE41MiB/0%,contextsnone/3locksavailable,M204PID1085297absent. GPU0usedonlyfor4diagnosticprocesses,eachreleaseverified. FinalGPU0releaseevidenceinthecurrentbundle;notresourceblocked.
- CURRENT04:12:24server4GPU1ONEforeigncontext3209554,9673MiB/77%;3projectlocksavailablebutsharingprohibited. server3strictSSH255TIMEOUT04:12:33,GPU1occupationUNKNOWN/notidleoroccupied. Thesearecachedtimestampsafterthispoint;no reset/restart/driverchanges.
- GPU0resource-onlyadaptationfrozen:onlynvidiaindex/UUID/lockpathsandmanifeststagechanged;originalruntimeinverse-diffrestoresexactsource,model/config/checkpoint/data/protocoltoleranceunchanged. No scientificimplementationrevision ornewmodel. Currentbundle pipeline/diagnostic_bundles/tick_a1b2de4f/.
- Recordedproductioncommitc31f45994f8d68b78dfe8bb4fef3f9aaefabe86e(prior,notreaudited);no model/configedits/commits. OriginalbackboneSHAa6f400bcf9bd722230d16ea7c3424b0d7658730126df604f67b4cccf42e25c1f.
## Open Questions And Risks
- Geometryrow-orderdependenceobserved4fixedscenes,notprovedharmfulorinnovative. Alltaskmaskreadoutcausality/noise/efficacy/populationuncertaintyUNKNOWNduestrictcontrolfailure;sourceatomicsriskNOTprovedexactcause. Defaultscience/10G/pareto/bansremain.
- BOTHprimaryblockedonnumericalcontrol,notexternalGPU/humanpermission. Resumeonlywithnewcausalsource/nativeevidenceandconcretepreregisteredboundedmeasurementrepairpreservingoriginal1e-6andallfailures. No specificjustifiedrepairdefined;timersarenotPASS/rerun/revisionauthorization. Retry/cooldownactualtimesinledger.
- design_cycleno_information_gain appliesFURTHERunchangedreplaysof2independentinterventionssharingonefailedmeasurementprerequisite,NOTnonewobservations/nativeprogressorindependentfalsification/globalrouteexhaustion/deadlineexpiry. No activeexecutablecandidateleftundertheunchangedfrozenprotocols.
- Fourauxpriorityholdsremainunchanged;onlyactuallydueitemsgetscopecheckbycurrentclosinghelper. GPU0availability/GPU1authorizationdoesnotpromoteoldsupervisionorM201. No repeatconsentquestion.
- Alloldcontrollershardcodeexpiredtokens;currenta1b2controllerexpiresafterfinish. Neverreexecuteoldops/study/closinghelpers;onlyfrozenprotocol/sourcecanbereusedwithfreshguard/lease/resources/assets.
## Last Tick
- tick_a1b2de4f actual4nativeGPUprocesses:1resolutionprefixguardfailure,1geometry4scene12levelcontrolrun,2relabelmaskpairs;0backward/models/admission/training. AlsoactualM204earlystop+twoCPUcheckpointmetadatareadslocatingtrueoutput,1CPUinstalledsourcebinding,andfinalGPU0releasecheck. Actualquery/expressioncountsinstoredanalysis,notinventedindependentdenominators.
- Preserveeveryfailure/rawreadout,originalearlystopinput/output,sourceprotocolandresourceadaptationhashes. Originalresolution3pairsunrun;notcountedasattempts. Scientificstatusinconclusiveexceptspecificnativegeometryproperty;0faketuningorvariantfillers.
- Reportnotes/full6sectionreport/finish/FINALIZEDreceiptandownedlease+pendingabsenceverificationSTILLREQUIREDatthisprefinishsave. Usagepartialbegin20:09:18Z->receiptlocalwindowonly,cacheincludedinput/reasoningincludedoutput,notbill;no postreleaseprojectwrites.
'''
assert len(memory.splitlines())<120
guard()
(ROOT/'pipeline/codex_memory.md').write_text(memory,encoding='utf-8')

index=ROOT/'pipeline/decisions/_index.md'
before=index.read_bytes()
env=os.environ.copy()
env['TZ']='CST-8'
decision=subprocess.run(['C:/Program Files (x86)/Git/bin/bash.exe',str(SKILL/'log_decision.sh'),'cluster_project','other',
    'M204 natural earlystop; native tests expose numerical control block.',
    'Preserve strict gates and measured hierarchy sensitivity; cool unchanged numerical replays,not GPUs.',
    'M204原生28轮patience10早停，真实续训best为0.49925217@18；GPU0释放后执行原分辨率pair0、4场景原生重标号及2组固定query掩码测试。分组12/12层变化且身份控制通过，但3个前向测试重聚合误差均1.907e-6超原1e-6。保留全部失败与原始读数，不推断收益/伤害，不放宽门槛，不伪称资源阻塞或重启训练。',str(analysis)],capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=20)
assert decision.returncode==0,decision.stderr
assert index.read_bytes().startswith(before)
save('decision_record_receipt.json',{'observed_at':now(),'returncode':decision.returncode,'stdout':decision.stdout,
    'stderr':decision.stderr,'existing_index_bytes_preserved':True,'timezone':'Asia/Shanghai'})
notes=save('report_notes.json',{'actions':[
    '本轮2026-10-20 04:09:18上海design快照；真实归属/前台模式/旧调度Disabled及当前目标授权已核对，仅一次begin。快照登记M204运行但进程未见(deathwatch1/3)，不将登记当作训练。历史最佳M95为0.5020、目标0.5100、差0.0080，仍未达标。',
    '04:12:24严格身份/UUID和实时三锁核实：M204原PID已消失，原生日志04:06:30结束并明确第28/50轮patience10早停。GPU0为41MiB/0%、无计算上下文且三锁可用；GPU1另有一项外部计算，9673MiB/77%；04:12:33 server3密钥SSH255超时，其GPU1占用未知。未抢卡、reset、迁移、恢复M201/M204或改队列消失计数。',
    '最先读取的20261019_093003/best及last仍是保留的第5轮恢复输入，已留证但不作本次最终指标。随后沿原生日志真实保存标记定位20261019_162904：best为第18轮，原生标量记录0.49925217；last为第27轮/未提升9次，原生第28轮break在保存之前。真实best未超M95；不把自然早停或本次核验当新训练/准入。队列终态仍待规范后续监控归档，未强制改记录。',
    '两项到期主线先恢复原稳定ID验证：预先冻结纯GPU0资源映射，仅改卡号/UUID/锁路径及清单位置；反向替换能恢复原运行器，原模型/config/checkpoint/样本/seed1999/协议与1e-6阈值均不变。每项执行前仍检查实际空闲、资产哈希、当前执行租约和三锁独占。',
    '原分辨率pair0实际原生前向：4表达支持667、4表达支持255，原细层为255token。point/features/mask/score/identity控制均0，重新聚合误差1.9073486328125e-6超过原1e-6，原断言在干预前停止。mask干预完成0对，余下原3对未运行，不算失败/完成，也不据此否定分辨率耦合假设。',
    '原生FPS/组合层级重标号几何测试真实完成4固定TRAIN场景，12/12层身份重放通过、12/12层物理共成员改变；当前二进制首物理种子0在逆序后对应666/709/2328/405。它证明这组样本的几何行序敏感性，不证明有害缺陷、新颖性、修复收益或源码与二进制全对应。',
    '在结果之后、执行之前预注册同ID的固定query mask扩展：2对/4场景/16表达，保留原生prefix/query/targets，只以原FPS重算重编号层级。两对都完成；其余五项原生重放控制为0，但重聚合均1.907e-6，仍不通过原1e-6。原始点message最大变化1.5078/1.58795，mask最大变化9.5246/11.1023仅为受限原始读数，任务因果收益/伤害未定；实际匹配query行数、表达覆盖和逐场景均值见analysis.json，不把相关行当独立样本。',
    '仅CPU绑定核验当前模型确用scatter_mean；实际安装源码说明GPU原子归约非确定性，与误差相容但未隔离成因。未重复内核试到PASS、改精度、换seed、放宽阈值或改原模型。四个诊断进程均退出后释放；最终GPU0无计算上下文且三锁可用，有独立释放证据。因此当前主线改记真实numerical_control_failure，而非继续谎报资源或授权阻塞。',
    '实际产出为4个原生GPU诊断进程(1分辨率控制失败、1几何4场景、2固定query mask对)，2次只读checkpoint元信息核验、1次安装源码绑定及释放检查；0新候选/模型/backward/准入/队列项/训练。原有CPU562场景普查和旧数值失败全部复用保留。辅助监督只在实际到期时作范围复查，不新增优先级或反复索要授权。',
    '用量只覆盖本轮begin(2026-10-19T20:09:18Z)至finish收据前可见本地记录，排除此前读取、晚到记录和最终回复；此处具体用量未知，以收据为准。缓存已在输入、reasoning已在输出，不重复相加、不视为账单。完整六段复用快照事实表，后续变化在本节注明；保存时finish尚未执行。'
], 'decisions':[
    '本轮科学结论分开：M204该次训练未超过历史最佳；4场景原生几何行序敏感性已观察到；重标号对mask的收益/伤害仍因严格数值控制失败而未定。后者不是模型有效或假设被科学证伪，不改成PASS，不自动开启训练。',
    '两项不同干预的有限原生测试共享一项真实失败的测量前提，源码审计尚未建立具体可证明修复；对继续相同重放设置有证据的短期no_information_gain冷却。该名称仅指进一步不变重放无新增诊断力，不抹去本轮新观察、不称全局路线穷尽/独立科学否定/资源不足或截止已到。原3个未运行分辨率对仍保持未执行。',
    '恢复条件为同稳定ID下出现具体、预注册且能守住原1e-6控制的测量实现证据；当前无已证明的修复，不靠计时器授权复跑/改阈值或制造变体。GPU0空闲不等于候选准入；保留M204全部输入/输出及native早停状态，后续由规范监控归档，不重启/迁移。'
]})
print(json.dumps({'analysis':evidence(analysis),'notes':evidence(notes),'raw_conditional_summary':raw_summary,
    'stop_reason':'no_information_gain','primary_retry_after':retry,'cooldown_not_after':earliest.isoformat(),
    'aux_scope_checks':len(aux_due),'final_gpu0_release':evidence(release_path),'finish_still_required':True},ensure_ascii=False,indent=2))
