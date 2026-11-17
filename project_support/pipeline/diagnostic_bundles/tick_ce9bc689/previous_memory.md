# Codex Research Memory
## Goal And Phase
- Currenttick4eca1157b1244438ac81677bebd28862,2026-10-18Shanghai,cluster_projectonly. GoalSHA42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec unchanged;24constraints/11bans;Phase1notuning;target.5100.
- Mainline:scale-specific hierarchical point/superpoint inst_feats updates used with queries for masks. Efficiency is a constraint,not sole contribution. No otherproject/scheduler/background/newchat/nestedCodex.
- Authorizedonlyserver4physicalGPU0/dl04-MS-7E06/.115/UUIDGPU-958e741a-e5cf-127e-ffe8-9b984e1f404c andserver3physicalGPU1/sysu311-MS-7C59/.120/UUIDGPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0,onetask/card. server4GPU1 NOTauthorized. Keysused,passwordreferenceunread;noeviction/reset/lockdeletion.
- Seed1999,batch2/workers4,epochs50/max_iters70,optimizer/loss/data/earlystop unchanged. Default10G,HDSexactexceptionnottransferred. No M201recovery/HDSrevision3/normhelperrevision3.
## Champion And Baseline
- CACHEDhistoricalM95.5020,baseline.4894,target.5100,gap.0080. AvailableM95epoch16=.5024607181549072 is NOT verifiedhistoricalchampionweights.
- CACHEDM203FLEnormalearlystop23/50,bestepoch13=.48853155970573425,branchstopped/notrestarted. BestSHA b380d9ec67b3efbec1efbbdbfaab5df96903e93770c17b9ec1293ebcb26ff0dd. Last.pth expectedepoch22/noimprove9(break-before-save),notcorruption.
- CACHEDfullVAL9508/141 pairedavailableM95delta-.0139291520,sceneCI[-.0223369116,-.0054631474]. Notrerun/countedtick. M202HDSstopped29,best.4946560264@19.
- AvailableM95frozenSHAfe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e usedforpairedcorrectness only,notchampionverification.
## Active Hypotheses
- hierarchical-padding-context-invariance-audit now COMPLETE finitecorrectnessdiagnosis. Prior nativeFLE/M95same-shape masked-value tests provedunmaskedglobalmean affectsvalidpointmessages/masks;this issharedlegacyissue,not newattentioncontribution.
- THIStick diagnosticreference1 changesONLYglobal_mean AST:masked_fill(mask,0).sum/count.clamp_min(1),nativeoriginalmean on no-paddingrows. No productionfile,parameter,precision,seed or optimizerchange.
- CPU exactsource/actualtrainedgateweights:4cases/model,10syntheticbackwards;no-paddingoutput/gradidentity0,masked-gradient0,allmasked/zero-scale nulls0,appendinvariance0,finite-differenceerrors<2e-13. Notnativeadmission.
- InitialnativeM95/FLEinterfacesFAILEDsuffix1e-6controls(1.90735e-5/2.67029e-5);allgather/gradient/nulls0. Failuresimmutable. Onepreregisteredflagprobe demonstrated allrequires_gradFalsecausesdifference;initial/restorednativeflags produceALLoriginalreconstruction/controlerrors0. Notrandomretry/loosentolerance/arithmeticrepair.
- Nativeoriginalflagreferenceinterfacespass;maskedgrad0,validgradnonzero,allidentity/nulls0. M95originalmaskedgathergrad1.7798e-5,FLE1.0810e-6. Allparameterflags preserved,no parameter.grad accumulation ininput-onlyautograd.
- Fourfresh native.train processes M95/FLE x original/reference each nativeforward/loss.backward/originalclip.1PASS,nooptimizer/schedulersteps. Targetlevel_gate/point_out_projgradientsfinite/nonzero. Fixedbatch2 wholepointmaskedgradoriginal1.5439e-8/8.3486e-9,reference0both. Nativeprefixhashesdifferdespiteidenticalbatch:doNOTattributeinstantlossdifferences tofix.
- ResourcegatherONLYbs1/warmup20/repeat100: M95median.146976->.200016ms(+.05304,+36.09%);FLE.135920->.193968ms(+.05805,+42.71%). Allocatedmodulepeak+1536bytesboth. Notfullmodellatency/resourcePASS.
- Singlefixedbatch nativeforward/backward peaks M953.592365->3.592395GiB(+31744bytes),FLE3.818330->3.818331GiB(+1024bytes). Optimizerstatesnotloaded;not alltrainingpeak. Warmup/resourcecoldstep scopes separate;noefficacyclaim.
- Configreadconfirms trainbatch2/workers4,valbatch1/workers2,testbatch1/workers1,seed1999/epochs50/maxiters70/clip.1. Onno-paddingrowsreferenceexactlyoriginal;no newVALor promisedcheckpointmIoUboost.
- NEWstable native-train-prefix-repeatability-audit VALIDATION:2fresh ORIGINAL processes/model,first2TRAINgroups/samecheckpoint/batch/seed/RNG/native.train/backward/clip,nooptimizer. RawprefixarraysandRNGhasheskeptremotely inrepeat_model_i stages.
- RepeatinputsandCPUtorch/CUDAtorch/numpy/PythonRNGstatesallidentical,geometry/otherarraydifferences inrepeat_analysis_result.json. PointprefixmaxabsM953.3881515e-6,FLE3.3378601e-6;lossdiff2.9802322e-8/0. Notbitwiserepeatable;concretebackendcauseunlocalized. Onepair/model isNOTtrainingseedvarianceorCI;do notrelax1e-6gates.
- NEXT same repeatID:localizeearliestdivergentnative tensor acrossbackbone/encoder withfrozeninput/RNG/exactsavedprefixcontrols,freshlease/liveidleGPU/3locks. No seedscan,blindretryuntilmatching,productionpatch ortraining. Corestructuralmechanism/efficacy stillneeded.
## Closed Or Failed Directions
- PriorfiniteQFdiagnosis COMPLETE,inconclusive trainedbenefit. Lasttickfirst9nativeforwardsfailednormrevision2,onevalid32TRAINreplication reconstructed0. PointonlyPioudelta+.0075331,CI[-.0001237,.0218365]cross0;queryonly+.0002626,indexflips0. Initialfailurepreserved,no normrepair3.
- fine-leaf-local-point-exchange COMPLETEnegative trainedrealization,branchstopped;no restart/tuningpermission orwholemainlinefalsification. HistoricalrejectedIDs/all11bans/HDSfailures/geometrylatticefailure retained.
- Fourauxiliaryhuman/scopeholds remain;recheckonlywhenactuallydue,keeporiginalauthorizationconditions. Nativepointcorrectness/repeatability tests do not require oldsupervisiontests. Timers/freeGPUsdo notrestorethem.
- Originalm95-hierarchical-mask-feature-path-audit alreadycovers scalecomplementarity;notrenamed/reopened as anewcandidate. Singlemaskedmeanrepair isNOTnewPhase1coreinnovation/admission.
- CACHEDFLE9.627987020G/M959.762532428G;fullmodel43.732vs36.821ms,FLE~18.77%slower,sampledmemory+3.48to7.92%. Notremeasuredwholemodelthis tick;alltrainingpeak/originalbaselineincrementUNKNOWN.
## Running And Queue
- Immutable snapshot2026-10-18T10:12:30.890299Z/design,deadline11:12:30.890299Z(Shanghai19:12:30),active0/target2/budget2,due1,reservebudget0. Actualowner/envthread01a04987-fdbe-7301-b2f0-f9b6ab60f74c verified. Pipeline-cluster_project Disabled/notchanged.
- No active/waitingtraining ornewcommit/deployment/admission/VAL. Onlyserver4GPU0used;server3GPU1notused. Finalfreshprobe19:07:17Shanghai:GPU0 41MiB/0%,nocontexts,training/diagnostic/exclusive3locksreleased. No commandrunning.
- Nativeproduction7M95+9FLEsourcefiles/configs/checkpointshashesunchangedaftertests. DirtyPDC/untrackedBCCA preserved. No repeatbegin/preflight/deadlineedit. Prior6a3484ad COMPLETE/FINALIZED/contextcommitted/lock+pendingabsentverified;priorceb5e6c1INCOMPLETEunchanged.
## Open Questions And Risks
- Nativefinitepaddingcorrectness nowconfirmedincludingrealbackward,NOTestablishedcauseofM203vsM95trainedgap. Uniformrollout/retraining,structuralinnovation,generalization andmaterialnovelty remainunverified;noautomaticstoppedbranchrestart.
- Repeatsidentify6missinggradtensors:unuseddec.cluster_att.query_linear/k_linear/v_linearweights+bias,bothmodels;allotherexistinggradientsfinite,actualpointfusionweightgradnonzero. Thisagreeslegacyunusedrouting,notnewdiscoveryornewinnovation.
- Parameterfreezingcanchangeevalnumericalpath;preserveactualflagsandcalibratecontext,notabsolutetolerance. Matchedrawprefixcontrolsneededbeforetinyinstantlossinterpretation. Onepairnot independenttrainingnoise.
## Last Tick
- Bundlepipeline/diagnostic_bundles/tick_4eca1157;analysis_summary/repeat_analysis_result/final_progress/rawnativefailuresandpassresults;reviews/designs4eca1157(+repeat);decision20261018-190717_other.md.
- ActualTHIS tick12nativeforwards/20nativebackwards(interface12/fulltrainmode8)/14suffix;CPU10syntheticbackwards;400module-timingsamples. Optimizer/scheduler/newtrainingloop/newVAL/admission/productionmodels0;newdiagnosticID1. Cachednotaddedagain.
- Memorybackedup incurrentbundle/previous_memory.md. Currentfinish/receiptstatusPENDINGuntilcanonicalconfirmation;onlyrealremaining<=180permitsdeadline-near. No waits/padding/fakeblocks/rejections.
- VerifyclosurePASS/COMPLETE/FINALIZED/context_committed andabsentownedlease/pending;otherwiseexactfailure+abort/release. No writesafterrelease. Receiptusagebegin-to-receiptonly,cacheinputsubset/reasoningoutputsubset,notbilling;numericusageUNKNOWNuntilreceipt.
