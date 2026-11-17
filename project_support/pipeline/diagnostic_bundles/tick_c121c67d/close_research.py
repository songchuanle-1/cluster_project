"""Persist actual diagnostic cause evidence and honestly separate it from designs."""
from datetime import datetime,timedelta,timezone
import json
import os
import shutil
import subprocess
from ops import ROOT,OUT,SKILL,TOKEN,GOAL,IDS,guard,tick,save,evidence,now

owner,_=guard(180)
results={kind:tick.load(OUT/(kind+'_result.json')) for kind in ('resolution','relabel')}
for kind,result in results.items():
    execution=tick.load(OUT/(kind+'_execution.json'))
    assert execution['returncode']==0 and execution['data']['child_returncode']==0
    assert result['execution_completed'] and len(result['records'])==3
    assert result['fixed_repetitions_per_mode']==3
    assert result['input_clone_identical'] and result['token_mutation_errors']==[0,0,0]
    assert all(row['source_unchanged_since_capture'] and row['ids_unchanged_since_capture']
        and row['original_output_mutation_error']==0 and row['zero_input_output_max']==0 for row in result['records'])
    assert result['fixed_input_native_variation_observed']
    assert not result['source_pointer_reuse_preserves_strict_control']
    assert not result['clone_branch_preserves_strict_control'] and not result['admissible_measurement_repair_proved']
    assert not execution['data']['after']['contexts'] and all(execution['data']['after']['locks_available'].values())

terminal=tick.load(ROOT/'pipeline/experiments/M204-CPA.json')
assert terminal['status']=='done_earlystop' and terminal['final_best']=='0.4993' and terminal['epochs_final']=='28/50'
terminal_snapshot=save('M204_terminal_snapshot.json',terminal)
fle=ROOT/'Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1/fine_exchange.py'
assert tick.digest(fle)=='cd700b675ce765786c7babca339ba9dc75eabffb85f63b71a91701be495da676'
distinction=save('route_distinction_check.json',{'observed_at':now(),'source':evidence(fle),
    'tentative_idea':'Recipient-specific point-to-point content attention inside native fine geometric leaves.',
    'actual_existing_implementation':'FineLeafExchange uses cKDTree bounded within-leaf neighbors and headwise content scores for recipient-specific point exchange.',
    'decision':'Do not label this idea as a new structural design or create a renamed successor;it is already the M203/FLE information-interaction family. No new scientific test or global mainline rejection is implied.',
    'new_structural_designs':0,'new_candidates':0,'native_training':0})

work=tick.load(ROOT/'pipeline/research_work.json')
clock=datetime.now(timezone.utc)
aux_ids=['m95-native-relation-other-sign-conflict','m95-native-main-role-weight-precedence',
    'm95-native-secondary-positive-mass','m95-native-between-pair-support']
due_aux=[row for row in work['candidates'] if row['id'] in aux_ids and datetime.fromisoformat(row['retry_after'])<=clock]
if due_aux:
    scope=save('auxiliary_scope_recheck.json',{'observed_at':now(),'goal_sha256':GOAL,'checked_ids':[row['id'] for row in due_aux],
        'decision':'Pointfeaturemainline remains primary;no new human instruction promotes old supervision or recoversM201. Latest user asks whether new experiments exist;that question does not authorize reopening/retuning or altering gates.',
        'scope_changed':False,'new_scientific_tests':0})
    for row in due_aux:
        row['last_scope_check_at']=now()
        row['retry_after']=(clock+timedelta(hours=4)).isoformat()
        row['evidence'].append(evidence(scope))
retry=(clock+timedelta(hours=2)).isoformat()
cycle_retry=min([datetime.fromisoformat(retry)]+[datetime.fromisoformat(row['retry_after']) for row in work['candidates'] if row['id'] in aux_ids]).isoformat()
summary={}
for kind,result in results.items():
    summary[kind]={'scene_ids':result['scene_ids'],'input_clone_identical':result['input_clone_identical'],
        'token_mutation_errors':result['token_mutation_errors'],
        'per_level_native_source_variation':[row['source_within_repeat_max'] for row in result['records']],
        'per_level_source_errors':[row['source_errors'] for row in result['records']],
        'per_level_clone_errors':[row['clone_errors'] for row in result['records']],
        'cascade_source_errors':result['cascade_source_errors'],'cascade_clone_errors':result['cascade_clone_errors'],
        'source_pointer_fix_supported':False,'fixture':result['fixture']}
analysis=save('analysis.json',{'observed_at':now(),'token':TOKEN,'snapshot_at':'2026-10-20T00:10:39.387707+00:00',
    'latest_human_question':'没有新设计的实验吗',
    'direct_answer':'No new independent structural design/implementation/admission/training has been produced this tick. These are numerical-cause diagnostics,not new architecture experiments. Currentdesigngap is acknowledged,not disguised by diagnosticcounts.',
    'canonical_terminal':{'M204_status':'done_earlystop','epochs':'28/50','canonical_rounded_best':'0.4993',
        'cached_native_checkpoint_repr':'0.49925217@18 from04:30Shanghai prior probe,not reread this tick',
        'archived_at_local':'2026-10-20T08:10:38.352403','source':evidence(terminal_snapshot),
        'outcome':'ThisrealizationbelowhistoricalM95.5020;not entireCPAmechanismfalsification,scientificadmissionorautomaticrestart.'},
    'native_discrimination':summary,
    'interpretation':'Bothnativecontexts preserve exactinputs/IDs/strides and input/outputversions;tokenmutation0 and zero-inputcontrols0. Exactsame-source-pointer calls stillvary up to1.9073486328125e-6,so inputcopying/aliasmutation alone cannot explain the failed1e-6native replay. Nativefixedinput floatingreductionvariation is directlyobserved;no specificatomic schedulingcauseproof or controlpreservingrepair is asserted.',
    'scientific_limits':'Original1e-6controls and oldfailuresremainFAILED. No retestinguntilPASS,precision/operator/seed/thresholdchange,new backward or trainable structure. Geometricrowordersensitivity remains the prior4sceneobservation;taskharm/benefit/noveltyUNKNOWN. Numericaldiagnostic hold is candidate-specific,not a global freeze on independent structure design.',
    'distinctness_check':evidence(distinction),
    'denominators':{'native_lossforward_contexts':2,'observations_of_expressions':16,'distinct_scene_ids':3,
        'overlap':'scene0000_00 and its first4expressions occur in bothcontexts;neitherexpressions nor3kernelrepetitions are independentpopulation samples.',
        'capture_levels_per_context':3,'fixed_repetitions_per_source_or_clone':3,'population_CI':None},
    'this_tick_outputs':{'new_structural_designs':0,'new_structural_models':0,'new_candidates':0,'admissions':0,'new_training':0,
        'native_cause_processes':2,'native_lossforwards':2,'native_backwards':0,'new_remote_native_fixtures':2,
        'canonical_terminal_candidate_reconciliation':1,'source_duplicate_idea_checks':1,'aux_scope_rechecks':len(due_aux)},
    'operational_fault':'FirstlocalobserverassumedterminalM204stillinactivequeue andassertedafterread-onlyresourceprobe. Correctedtoofficialpipeline/experiments/M204-CPA.json;failure retained in observationartifact. Not remotehostfailure or GPUscientifictest.',
    'resources':'Bothserver4authorizedcardsidleat08:19:14with3locksavailable;onlyGPU0usedfordiagnostics,eachreturnedcontextsnone/3locksavailable. GPU1notused;lateroccupancyUNKNOWN. server3unreachableinthispreflight,occupationUNKNOWN.',
    'stop_reason':'no_information_gain','stop_scope':'No furtherUNCHANGED source/clone/mutation replay is justified after fixeddiscrimination shows both attemptedcapture-onlyexplanations inadequate. Newnativevariationevidenceis real;this is not globalrouteexhaustion or lackofnewobservations. No concrete controlpreservingmeasurementrepair or independent evidenced admissiblenewstructuredefined;do not fabricatefiller.',
    'retry_after':retry,'cooldown_not_after':cycle_retry,
    'evidence':[evidence(OUT/name) for name in ('aggregation_cause_protocol.json','resolution_execution.json','resolution_result.json',
        'relabel_execution.json','relabel_result.json','current_resources_and_terminal.json')],
    'execution_status':'Report/finish/receipt and locallease-releaseverification still required.'})

for row in work['candidates']:
    if row['id'] in IDS:
        row.update(stage='blocked',updated_at=now(),failure_scope='implementation',
            failure_scope_detail='Native diagnostic measurement/replay implementation only;underlying structure/taskeffect remains inconclusive,not corehypothesisfalsified.',
            blocker_kind='numerical_control_failure',
            blocker='Twoinstrumentednativecontexts prove exactinputs/IDs/stridesandtokensunchanged,but exactsame-pointerfloat32native reductions vary up to1.9073486328125e-6 > frozen1e-6. Pointerreuseandclone-alias-onlyrepairsnot supported. No concretegate-preservingmeasurementrepairproved. GPUauthorization/availabilitynotthisblock.',
            retry_after=retry,unblock_condition='New concretecausalmeasurementrepair preregisteredunderSAMEstableID and testedagainstoriginal1e-6nativecontrols,allfailedresultsretained. Timer doesnotauthorizeunchangedmodel/kernelreplay,favorabletrialselection,newprecision/operator/gatewaiver ortraining.',
            next_action='Use the saved true-nativeinputfixtures to formulate a genuinelydiscriminating control-preserving measurementstep BEFORE anotherrun;do not re-loadfullprefix torepeatidenticalsource/clonekernelprobes. No justifiedrepairyet. Keep numericalholdcandidate-specific;do notcallitnewarchitectureorfreezeindependentstructuredesign.',
            scientific_admission=False,gate_result='Nativeinput/outputmutationcontrols0;bothsourcepointerandclonebranches fail unchanged1e-6 in2contexts. Nativefixedinputvariationobserved;measurementrepairunproved. Originalmaskcausalinterpretation/structuraladmissionremainUNPASSED.')
        row['evidence'].extend([evidence(analysis),evidence(distinction)])
    elif row['id']=='coarse-semantic-point-cross-attention':
        assert row['stage']=='training'
        row.update(stage='complete',updated_at=now(),scientific_admission=False,
            next_action='Preserve canonicalM204naturalearlystop28/50 andbestapprox.4993;do not restart/migrate or countasnewexperiment. FullmatchedVALuncertaintyunknown;no global mechanismfalsificationornewscientificPASS.',
            terminal_observation={'experiment_id':'M204-CPA','state':'done_earlystop','best_miou_rounded':'0.4993','epochs':'28/50','restarted':False,'evidence':evidence(terminal_snapshot)})
        row['evidence'].append(evidence(terminal_snapshot))
work['design_cycle']={'updated_at':now(),'stop_reason':'no_information_gain','attempted_ids':list(IDS),
    'no_gain_reason':'Preregistereddiscrimination actuallytests two distinctcapture-onlycausalexplanations:source/input/outputmutation and clone-pointer-onlymismatch. Both are contradicted on exactnativefixedinputs:mutation0 andsame-pointervariation>1e-6. No furtherunchangedreplaywouldrepairthesecontrols. DistinctprimaryquestionsareNOTfalsified;commonreductionvariationdoesnotprovebenefit/harm orglobaldesignexhaustion.',
    'resume_condition':'A concrete new gate-preservingmeasurementrevision/independentlyevidenced structuraldiagnosis;retainoriginalfailures anddo not duplicateFLE/rerununchangedkernels. New authorizationnotneededforalready-scopedoperations,but alloriginalgates/resourceleasesremain.',
    'retry_after':cycle_retry,'evidence':[evidence(analysis),evidence(distinction)],
    'attempt_results':[
        {'candidate_id':IDS[0],'hypothesis_id':'captured-input-or-output-mutation-causes-reaggregation-mismatch',
         'test':'Originalresolution667/255context:actual3levelsource/IDversions,bitwiseclones,pre/postclusteroutputs and3fixednativecallspermode.',
         'result':'Inputs/IDs/stridesunchanged,token/outputmutation0 andzero-inputcontrol0;unchangedsame-pointerreductionsstillvary1.907e-6. Capturemutation-onlyexplanationnot supported;originalstrictgateFAILED,nocorecouplingfalsification.',
         'evidence':[evidence(OUT/'resolution_result.json')]},
        {'candidate_id':IDS[1],'hypothesis_id':'clone-pointer-or-layout-alone-causes-reaggregation-mismatch',
         'test':'Originalrelabel667/710context:source-pointerversusbitwiseclone withfixed3repetitions,fullcascade andmutationcontrols.',
         'result':'Sourceandcloneinputsbitwiseidentical,stridesunchanged;sourcepointerreuseitselfstillFAILS1e-6andshowsnativevariation. Clone-onlyrepairnot supported;maskharm/benefitandadmissionunproved.',
         'evidence':[evidence(OUT/'relabel_result.json')]}]}
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
shutil.copyfile(ROOT/'pipeline/codex_memory.md',OUT/'memory_before.md')
memory='''# Codex Research Memory
## Goal And Phase
- Currentc121c67d871245c9b846e2cf447e91f3,begin2026-10-20T00:10:39.387707Z/deadline01:10:39.387707Z(08:10/09:10Shanghai),DESIGN. Owner01a04987-fdbe-7301-b2f0-f9b6ab60f74c/PipelineDisabled verified;onebegin,no repeatedpreflight.
- Prior56d2046bf3044817b70f465f0541e947STEADYautofinalized/PASS/lease+pendingabsent06:11:40;priora1b2FINALIZED/PASS/released04:40:13. Neverreuseoldtokensorbelieveoldprefinishmemorywording.
- GoalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85,25constraints/11bans,target.5100. Primaryhierarchicalpoint/inst_featsupdate;4supervisionauxpriorityholds,not scientificrejection. Seed1999/epochs50/max_iters70/gatesunchanged.
- Latestdirecthumanquestion:没有新设计的实验吗. Answerhonestly:0newindependentstructuraldesign/model/admission/training;currentworkisdiagnosis. DoNOTcallnativeprobeexecutionsnewarchitectureexperimentsorcreateweakfillerstosatisfyquestion. Userquestiondoesnotgrantreopening/gate/commit/schedulerchanges.
- Authorizedserver4GPU0/1andserver3GPU1,1task/card,capacity3. ExistingGPU1consentvalid,no repeatquestion. No server3GPU0/server6newdispatch/reset/eviction/restart/migration. Strictknownhost/keySSH,passwordreferenceunread.
## Champion And Baseline
- HistoricalM95.5020,baseline.4894,target.5100,gap.0080;M95frozenepoch16=.5024607181549072NOTverifiedhistoricalchampionweights.
- CURRENTcanonicalM204archive08:10:38Shanghai:done_earlystop28/50,finalroundedbest.4993,removedfromqueue. Actualnativeearlystop04:06:30previouslyverifiedpatience10;exactcheckpointscalarrepr.49925217@18isCACHED04:30probe,notnewread.
- CACHEDactualresumedoutputs20261019_162904:bestepoch18;last27/noimprove9becausenativebreakbeforecheckpointsave. Original20261019_093003epoch5/.43399662arepreservedresumeINPUTS. Noautomaticrestart/migration;single-runbelowM95notwholeCPAmechanismfalsification.
- CACHEDM203FLE.4885315597@epoch13,earlystop23/50,priorVALdelta-.0139291520/sceneCI[-.0223369116,-.0054631474];notreopened.
## Active Hypotheses
- coarse-semantic-point-cross-attention/M204CPA-R1 nowCOMPLETEincandidateledger,reconciledfromcanonicalterminalM204snapshot. ScientificadmissionFALSE;manualtrainingexceptionnotPASS. Qpoint/Krawcoarse/Vrefinedcoarse,1connectionrevision/0newparams,no revision2/automaticrestart. Prior9.769168428GvsM959.762532428G,fulloptimizerpeakUNKNOWN.
- hierarchy-native-batch-minimum-resolution BLOCKEDnumerical_control_failure,measurementimplementationonly;coreclamp/taskinterpretationinconclusive. Prior562/562TRAINcensus28support<256,min131,0missing/unknown;notrerun. Oldnativepair0supports667x4/255x4,finetokens255,baselinefivecontrols0/reaggregation1.907e-6FAIL1e-6beforeintervention;0completedmaskpairs,oldpairs1-3UNRUN.
- hierarchy-native-superpoint-relabeling-audit BLOCKEDsameoldstrictmeasurementgate. Priornative4scenegeometry12/12identityPASSand12/12physicalmembershipchanges;firstphysicalseed0->666/709/2328/405measured,sourcebinaryfullcorrespondenceunproved. Prior2fixedquerymaskpairs4scenes16expr/76correlatedqueryrowscompletedbutbothreaggregation1.907e-6FAIL;rawmaskmax9.5246/11.1023NOTcausalharm/benefit;scene-balancedrawerror-3.808396365036106e-5,taskinterpretationinconclusive.
- CURRENTtwoNEWinstrumentednativecontexts:resolution0000/0029andrelabel0000/0001,8expressionobservationseach,3distinctsceneswith0000overlap. Actualsource/IDversionsandbitwiseinputs/stridesunchanged;pre/postclustertokenandcapturedoutputmutationerrors0;zero-inputmeans0.
- CURRENTfixed3source+3clonecalls/level:exactSAMEsourcepointerstillvariesupto1.9073486328125e-6inBOTHcontexts. BothsourcepointerfullcascadeandclonebranchesFAILoriginal1e-6. Thisdirectlydemonstratesnativefixedinputfloatingreductionvariationandrulesoutclone/inputmutationasSOLEcause;notproofspecificatomicschedulingorvalidrepair/taskharm. No favorabletrialselection/precision/operator/seed/gatechange.
- TwoTRUE-NATIVEcapturedinputfixturesnowremote:.../pipeline/cause_c121c67d_resolution/native_aggregation_fixture.pt SHA09c72c1423d5b9113ffe3e15ac9d7050e18256450b389227de88906d021c4929,9122249bytes;.../cause_c121c67d_relabel/... SHAa436f38811edaa72c5d14d48d4058f7cfd713001fa29b183ff702844cc6ebaec,11016969bytes. Exactpaths/metadata/localresultsinbundle. Usefixturesforgenuinelynewmeasurements;doNOTrerunfullprefixforunchangedkernels.
- Existingtorch_scatter2.1.2/torch2.8.0+cu128sourceatomicnondeterminismdocumentationretained;newempiricalvariationisstrongerthansourcewitness,butnospecificgatepreservingmeasurementrepairproved. OldCPUFPSunsupported/fixedanchor/censusprobesnotrepeated.
## Closed Or Failed Directions
- Allrank/meanmoment/ancestry/padding/prefix/QF/HDS/FLEdiagnoses/rejections/bansanddirtyPDC/untrackedBCCA preserved. No renamedrouting/gate/residual/largeQKV/N2attention/tuning/canonicalseed singleoprepair/HDSrevision3/FLErestart/M201recovery.
- CURRENTsource-distinctioncheck:recipient-specificpointcontentattentioninsidefineleavesisALREADYFineLeafExchange/M203(k32,cKDTreeboundedneighbors,headwiseattention). DoNOTrenameit/newlinearizedkerneltomakea'newstructuraldesign'. Thisisduplicateideasourcecheck,notnewnativeexperiment/globalmainlinefalsification.
- Prior8scene/32exprstudiesCOMPLETE,nottrainable:expressiondonorerror+.004466350020434506,7positive/1negative,295correlatedqueryrows;scaleboundaryinteraction-.006994256213229087,2positive/6negative,30/32expr. No unchangedreruns/efficacyclaim.
- Originalexpressionboolfailure+revision1preserved;scaleFULLSOURCEpermutation2.86102294921875e-6FAILED1e-6all4;fixedfusion0NOTfullsourcePASS. PriorCPUfloat32identity3.814697265625e-6/algebra2.4318695068359375e-5andcachedGPUreconstruction7.48e-6FAILuresunchanged. No optionalkernelretry/precisionwaiver/reopenedhistoricalfamilies.
## Running And Queue
- CURRENT08:10snapshotactive0/target3,waiting0,candidatebudget3,actionablereserve2/2,prepbudget0,pending6/8. 2oldnumericalroutes+4auxpriorityholds. M204terminalreconciledtocandidatecomplete;0newstructuraldesigns/models/candidates/admissions/queueentries/training. Cumulativecountsnotprogress/successrate.
- CURRENT08:19:14server4GPU0IDLE41MiB/0%,GPU1IDLE15MiB/0%,bothcontextsnone/3locksavailable. GPU0usedonlyfor2nativecausediagnostics;eachchildreturn0thencontextsnone/3locksavailable. GPU1notused;lateroccupationunknown. Cannotblamelackofcards/permissionfornewdesigngap.
- server3preflightunreachable,GPU1occupationUNKNOWN/notidleoroccupied;noseparateconnectionretry. No foreignjobs/reset/drivers/schedulerchanges. Pinnedserver4.115/dl04-MS-7E06 GPU0UUID958e741a-e5cf-127e-ffe8-9b984e1f404c,GPU1UUID7f82edb9-f620-8045-caea-a75232265cd1;server3.120/sysu311-MS-7C59 GPU1UUID340de111-e7e4-ed2d-15c9-8ab6a253e4a0.
- Recordedproductioncommitc31f45994f8d68b78dfe8bb4fef3f9aaefabe86e(prior);no model/configedits/commits. OriginalbackboneSHAa6f400bcf9bd722230d16ea7c3424b0d7658730126df604f67b4cccf42e25c1f. Nativeoriginalsources/assetsverifybeforeeachdiagnostic;runtimeGPU0copyunchanged.
## Open Questions And Risks
- Oldmaskharm/benefit/populationuncertainty/noveltyUNKNOWN. Numericalprerequisitefailsonbaselinefixedinputs;thisisnotcandidate-mechanismfailureorGLOBALstructuredesignfreeze. A genuinelyindependentpointfeatureinteractiondesignhasNOTbeenproducedthisTick;acknowledgethescientificdesigngap.
- TwooldIDsmeasurementfailure_scopeimplementation;no newmodelimplementationrevisionclaimed. Newcausalfixturebasedmeasurementmustbepreregisteredandpreserveoriginal1e-6andallfailuresbeforeanotherGPUrun. No currentlyprovedrepair;timerisnotpermissiontorerununchangedkernelorrelaxgates.
- design_cycleno_information_gainlimitedtofurtherUNCHANGEDsource/clone/mutationreplayafter2capture-onlyhypothesesdiscriminated. Notnonewobservations/globalindependentroutesexhausted/resourcesblocked/deadlineexpired. No fakefillerortrainingwithunpassedgates.
- Fourauxpriorityholdsunchanged;onlyactuallydueitemsrecheckedatclosure. Theirtimer/GPUavailability/directstatusquestiondoesnotpromotethemorM201. No repeatedhumanconfirmationneeded.
- Alloldcontrollershaveexpiredtokens;currentc121controlleralsoexpiresafterfinish. Neverrunoldops/study/closehelpersunchanged. Usecurrentleaseplusfrozenfixture/source/protocol/UUID/context/lockschecks.
## Last Tick
- tick_c121c67d:2instrumentednativeoriginal-lossforwards/2savedtrue-nativefixtures;fixedsource/clone/mutationdiscrimination,0newbackward or architecture/model/admission/training. 1canonicalM204terminalreconciliation and1duplicatefineleaf-ideasourcecheck. Nativeexpressions16observations/3scenes,notindependentpopulationsamples.
- InitiallocalobserverassumedM204stillinactivequeueandasserted;correctedtoofficialexperimentarchive. Failurepreservedinobservation;no remote/GPUscientificfailureinferred. Allnativechildrenfinishedwithcontextsnoneandthreefreelocks. Artifacts pipeline/diagnostic_bundles/tick_c121c67d/.
- Atthisprefinishsave,fullsixsectionreport/finish/FINALIZEDreceiptandownedlease+pendingabsenceverificationSTILLREQUIRED. Usagepartialbegin00:10:39Z->receiptlocalwindowonly,cacheincludedinput/reasoningincludedoutput,notbill;no postreleaseprojectwrites.
'''
assert len(memory.splitlines())<120
guard()
(ROOT/'pipeline/codex_memory.md').write_text(memory,encoding='utf-8')
index=ROOT/'pipeline/decisions/_index.md'
before=index.read_bytes()
env=os.environ.copy()
env['TZ']='CST-8'
decision=subprocess.run(['C:/Program Files (x86)/Git/bin/bash.exe',str(SKILL/'log_decision.sh'),'cluster_project','other',
    'Native replay variation localized; no new structural design.',
    'Preserve strict failures; distinguish diagnostics from architecture experiments.',
    '用户询问有无新设计：明确本轮0新结构方案/模型/准入/训练。两原生上下文输入/索引/token均未突变，但同一指针重复原生mean仍波动至1.907e-6，排除仅复制或别名解释；原1e-6门槛仍未过。已有FLE覆盖细叶内点间注意力，不改名冒充新结构。M204规范归档，保留全部失败及原生夹具，不把数值问题或资源空槽当全局研究冻结/启动许可。',str(analysis)],capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=20)
assert decision.returncode==0,decision.stderr
assert index.read_bytes().startswith(before)
save('decision_record_receipt.json',{'observed_at':now(),'returncode':decision.returncode,'stdout':decision.stdout,'stderr':decision.stderr,'existing_index_bytes_preserved':True,'timezone':'Asia/Shanghai'})
notes=save('report_notes.json',{'actions':[
    '本轮2026-10-20 08:10:39上海design快照，真实任务归属、目标授权和旧调度Disabled已核对；仅一次begin。规范监控确认M204-CPA第28/50轮自然早停并归档，活动/排队均0，预算3；历史最佳M95为0.5020、目标0.5100、差0.0080。M204终态约0.4993未超历史最佳，04:30旧checkpoint探测的0.49925217@18只是缓存，不当本轮新效益。',
    '用户本轮直接询问“没有新设计的实验吗”。已明确回答：目前确实0新增独立结构设计、0新模型/准入/训练；上一轮4次及本轮2次均为诊断，不能当新结构实验。当前研究设计缺口如实记录，不能靠检查数量或把已有FLE改名掩盖。',
    '08:19:14严格身份/UUID核实server4GPU0为41MiB/0%、GPU1为15MiB/0%，均无计算上下文且三锁可用；本轮两卡确实可用，所以不把没有新训练归因于缺卡或授权。server3在本轮预检不可达，GPU1占用未知。首次本地观察器对已归档任务仍在活动队列的假设导致断言，已修正为官方单条实验归档并保留故障事实，未重复preflight或重启任务。',
    '在执行前预注册两个旧稳定ID的可区分成因对照：原分辨率667/255与原重标号667/710两个上下文，每个只运行一次带内部采集的原生loss前向，采集三个实际mean层的原输入/精确复制/分组索引、版本/布局及cluster前后token。每层原指针和复制分支各固定3次原生归约，并固定零输入/整级联对照；保留全部结果，不试到PASS。原模型/config/seed/精度/算子/1e-6门槛均不变。',
    '两上下文都完成，输入与复制逐位一致，输入和索引版本不变，token及原输出突变误差均0，零输入控制0；但完全相同输入及同一指针的原生float32归约仍波动至1.9073486328125e-6，两个整级联原指针/复制分支均未过原1e-6。因此复制/别名突变不是唯一原因，原生固定输入归约波动已被直接观察；未证明具体原子调度成因或可准入修复，更不能推断结构收益/伤害。',
    '保存两份带哈希的真实原生输入夹具在本项目远端诊断目录，后续可在夹具上提出有区分力的新测量，避免重复加载全模型。两个GPU子进程均正常退出，随后GPU0上下文为空、三锁可用。实际为2原生loss前向、16表达观察(重叠scene0000，共3个不同场景)、0backward、新架构、新准入或训练；相关行/核重复不当独立统计样本。',
    '定向核对已有FineLeafExchange源码，发现“细几何叶内点对点内容注意力”已属于M203/FLE的信息流，不能换名充当新设计。只完成一次来源去重审查，不记为新候选或新原生实验；旧所有数值失败、FLE/HDS/routing等禁令和验证边界保留。四个辅助监督ID仅在实际到期时作范围复查，未因空卡或当前问题恢复优先级。',
    '用量仅本轮begin(2026-10-20T00:10:39Z)至finish收据前可见本地记录，排除此前读取、晚到记录和最终回复；此处具体值未知，以收据为准。缓存在输入中、reasoning在输出中，不重复相加、不视为账单。完整六段复用快照事实表；报告保存时finish尚未执行。'
], 'decisions':[
    '两项旧诊断的阻塞限于测量实现：原生固定输入归约波动已观察，原1e-6失败仍失败。不能把该数值问题解释为新结构无效，也不能将旧候选的数值门槛扩展成所有独立新结构研究的全局冻结；本轮尚未形成独立且有证据的新结构方案，这是实际设计进度缺口。',
    '两个不同成因解释(输入/输出突变与仅复制指针/布局)经过预注册原生对照均不足以解释问题；继续相同重放无额外诊断力，按证据作短期no_information_gain冷却。它不是“本轮没有新信息”、全局路线穷尽、资源阻塞或截止已到，也不是两项原始结构假设被证伪。',
    '保留原生夹具和所有失败。恢复前先定义同稳定ID下具体、预注册且保持原门槛的测量步骤；不重复旧核直到偶然通过、不改精度/阈值/seed、不把已有FLE改名补位。M204已规范归档，不自动重启/迁移；本轮0新结构实验，不能写成新设计完成。'
]})
print(json.dumps({'analysis':evidence(analysis),'notes':evidence(notes),'primary_retry_after':retry,'cooldown_not_after':cycle_retry,
    'aux_scope_checks':len(due_aux),'new_structural_designs':0,'native_cause_processes':2,
    'M204_candidate_terminal_reconciled':True,'finish_still_required':True},ensure_ascii=False,indent=2))
