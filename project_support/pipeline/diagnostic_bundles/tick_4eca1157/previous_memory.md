# Codex Research Memory
## Goal And Phase
- Currenttick6a3484ad478847ebb8200eee80781f84,2026-10-18Shanghai,cluster_projectonly. GoalSHA42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec unchanged;24constraints/11bans;Phase1no tuning;target.5100.
- Mainline:scale-specific hierarchical point/superpoint inst_feats updates used with queries for masks. Efficiency is a constraint,not sole contribution. No otherproject/scheduler/background/newchat/nestedCodex.
- Only server4physicalGPU0/dl04-MS-7E06/192.168.1.115/UUIDGPU-958e741a-e5cf-127e-ffe8-9b984e1f404c and server3physicalGPU1/sysu311-MS-7C59/192.168.1.120/UUIDGPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0,onetask/card. server4GPU1 NOT authorized. Keysused,passwordreferenceunread;noeviction/reset/lockdeletion.
- Originalseed1999,batch2/workers4,epochs50/max_iters70,optimizer/loss/data/earlystop unchanged. Default10G,HDSexactsourceexceptionnottransferred;noM201recovery/HDSrevision3/normhelperrevision3.
## Champion And Baseline
- CACHED historicalM95.5020,baseline.4894,target.5100,gap.0080. AvailableM95epoch16=.5024607181549072 is NOT verified historicalchampionweights.
- CACHED M203normalearlystop23/50,bestepoch13=.48853155970573425,branchstopped/notrestarted. BestSHA b380d9ec67b3efbec1efbbdbfaab5df96903e93770c17b9ec1293ebcb26ff0dd. Last.pth expectedepoch22/noimprove9 because break-before-save,notcorruption.
- CACHED fullVAL9508/141 pairedavailableM95delta-.0139291520,sceneCI[-.0223369116,-.0054631474]. Notrerun/countedtick. M202HDSstopped29,best.4946560264@19.
- AvailableM95frozencheckpointSHA fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e usedTHIS tickfornativecounterpart,notchampionverification.
## Active Hypotheses
- fle-native-nonself-target-mixing-audit now COMPLETE finiteQFdiagnosis,scientificinconclusive. CACHED prior32TRAINtargetalignment-.0105940,CI[-.0160851,-.0065348],119eligible/128,9supportempty,unknownlabels0;notcausalbenefit.
- THIS tickQFattempt1 FAILED unchanged revision2 normsolver atscene9:9nativeforwards/8completedscenes/24suffix. Preserve native_qf result;no arithmeticrepair/tolerancechange.
- ONE preregistered exactsource replicationpassed32TRAINscenes/128expressions/32forwards/96suffix. Actual out_norm(query)/mask_feats capture:allnative/identity/source/suffixreconstruction errors0,logitadditivity0. Firstfailure remains;strictnormcontrollerNOTrobustlyreproducible.
- L00Piou.6272896715,L01pointchanged.6197565587,L10querychanged.6270270730,L11both.6197565587. Pointonlydifference+.0075331128,CI[-.0001237072,.0218364935]cross0;queryonly+.0002625985. Queryfeatureschange32/32butindexflips0. NotadditiveIoU/percentageattribution/traininggain.
- All32inputSHA equalcachedterminal/attention,normalPiouexact,nativelossmaxdiff4.7684e-7. Nottrainingseednoise. Exploratoryalignment-PiouPearson.07179CIcross0;BCErankassociationnegative,notpositivecausalproof/novelty.
- NEW hierarchical-padding-context-invariance-audit remains VALIDATION. Sourceglobal_mean=point_feats.mean includesmaskedpositions. TwofixedTRAINscene interface:all6paddingcases affectvalidmessages/masks;identity/zero-scalecontrols0.
- Naturalbatch2:729vs1185validpoints;4expressionrows have456maskedpositions(38.48%),maskedfeaturesabsupto8.1644. Croppedgatherchanges.0571to.1256;nonpaddedroundoff1.24e-5explicitlyretained.
- SameBNC/validpoints/tokens/IDs control removesGEMMshapeconfound. FLEzero-masked masklogitchange4.6985588;maskedvalidmeanfill.5251312. Identity/zero-scale/nonpaddedrownullsALL0. Productionoperatorunchanged.
- ExactavailableM95samebatch2 also dependent:zero-maskedlogitchange1.1126709;validmeanfill.2718506;ALLcontrols0. Sharedunmaskedmeansource;effectdifferenceNOTarchitectureestimate(differentweights).
- CPUexactsourcefloat64fixtures4syntheticbackwards:maskedgradientM95.000159833/FLE.000167646,zero-scalenulls0. NOT nativebackward/resource/efficacyadmission;noCUDA.
- NEXT SAMEpaddingID:uniform_padding_followup_protocol.md. Freeze a uniformvalidpointcontract for BOTHmodels;nextCPUdegeneratecases/nativebackward/resources underfreshlease/liveGPU/3locks. No unilateralbaselinehandicap,single-opPhase1variant,automaticfix/training/VAL.
## Closed Or Failed Directions
- CACHED earlyepoch2/8TRAINnormmatchedPiou-.0079658 andterminal32+.0075331 bothCIcross0;earlycannotbereplacedbyterminalbest. Normrevision1/repairfailuresandTHIStickrevision2failure retained;no3rdrepair.
- fine-leaf-local-point-exchange COMPLETEnegative trainedrealization,branchstopped;notrestartpermission orwholemechanismfalsification. HistoricalrejectedIDs,all11bans,HDSfailures,geometrylatticefailure retained.
- Fourauxiliaryhuman/scopeholds nextretry19:09Shanghai;notdue/notrecheckedthis tick. FreeGPUs do not reopen them.
- CACHED FLE9.627987020G/M959.762532428G;43.732vs36.821ms(~18.77%slower),sampledmemory+3.48to7.92%. Notnewmeasured/speedup. Fulltrainingallocatorpeak/originalbaselineincrementUNKNOWN.
## Running And Queue
- Immutable snapshot2026-10-18T08:09:01.130869Z/design,deadline09:09:01.130869Z(Shanghai17:09:01),active0/target2/budget2,due1,reservebudget0. Actualowner/envthread01a04987-fdbe-7301-b2f0-f9b6ab60f74c verified. LegacyPipeline-cluster_project Disabled/notchanged.
- No training/waiting/commit/deployment/admission/newVAL. Onlyserver4GPU0usedthis tick;server3GPU1notused. Finalfreshprobe17:02:06Shanghai:GPU0 41MiB/0%,nocontexts,all3lifetimeflocks released. No nativecommandsremain.
- No repeatbegin/preflight/deadlineedit. Prior0d3bdd38 COMPLETE/FINALIZED andpriorceb5e6c1 INCOMPLETEreceiptsunchanged. DirtyPDC/untrackedBCCA preserved. Older memory backedup in currentbundle/previous_memory.md.
## Open Questions And Risks
- Sharedpaddingdependence confirmedonactualnativebatch2interfaces,NOT establishedcauseofM203vsM95gap. Uniformrepairbenefit,trainingnoise,generalization,fulltrainingmemory andmaterialnoveltyUNKNOWN.
- Singlemasked-meanfix isnotnewPhase1coreinnovation. Keep bothbaselines,gradient/degenerate/complexity/resource/admissiongates;no newseed/data/schedule/VALselection. Do not claimtrainingharm fromCPUgradient or robustnessfromonevalidnormreplicate.
## Last Tick
- Bundlepipeline/diagnostic_bundles/tick_6a3484ad;immutableprogress_summary,qf_analysis,source_postcheck,allresults;review/designsuffix6a3484ad;decision20261018-170206_other.md.
- ActualTHIS tick46nativeforwards/138suffix;nativebackwards/optimizer/newtraining/VAL/admission0;CPU4syntheticbackwards+3statisticalcontractcases. One newdiagnosticID,0productionmodels,0arithmeticrevision3. Cachednotaddedagain.
- Finish/receiptstatus PENDING untilcanonicalconfirmation. Onlyrealremaining<=180seconds permits deadline-near;neverwait/pad/fakeblocks/rejections. VerifyclosurePASS/COMPLETE/FINALIZED/context_committed andabsentownedlease/pending;otherwiseexactfailure+abort/release.
- No writesafterrelease. Receiptusagebegin-to-receiptonly,cacheinputsubset/reasoningoutputsubset,notbilling;numericusageUNKNOWNuntilreceipt.
