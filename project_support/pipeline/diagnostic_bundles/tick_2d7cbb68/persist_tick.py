"""Persist the tested structure and an honest actionable validation state."""
from datetime import datetime,timezone
import shutil
from ops import *
owner=guard()
now=datetime.now(timezone.utc)
fresh=tick.load(OUT/'fresh_native/fresh_native_result.json')
resource=tick.load(OUT/'resource_comparison.json')
assert fresh['execution_completed'] and resource['passed_measured_budget']
controls=[OUT/'native_coarse/native_coarse_result.json',OUT/'raw_key_revision1/native_raw_key_result.json']
controls += [OUT/('eight_scene_'+str(i))/'native_raw_key_result.json' for i in range(4)]
controls += [OUT/('attribution_'+str(i))/'native_attribution_result.json' for i in range(4)]
values=[tick.load(p) for p in controls]
assert all(v['execution_completed'] and v['controls_passed'] for v in values)
package_paths=[OUT/'independent_package/native_package_champion_result.json',OUT/'package_isolated/native_package_candidate_isolated_result.json']
packages=[tick.load(p) for p in package_paths]
total_native=sum(v['native_forwards'] for v in values)+sum(v['native_train_forwards'] for v in packages)+fresh['native_forwards']
total_backward=sum(v['native_backwards'] for v in values)+sum(v['native_train_backwards'] for v in packages)+fresh['native_backwards']
semantic=[]
for i in range(4):
    v=tick.load(OUT/('eight_scene_'+str(i))/'native_raw_key_result.json')
    items={c['condition']:c for c in v['coarse_conditions']}
    semantic.append({'pair':i,'scenes':v['scene_ids'],'candidate_vs_original_loss':items['coarse_attention']['native_loss_delta'],
      'candidate_minus_uniform_loss':items['coarse_attention']['native_loss']-items['uniform_coarse_mean']['native_loss'],
      'candidate_minus_mismatch_loss':items['coarse_attention']['native_loss']-items['cyclic_key_value_mismatch']['native_loss'],
      'all_matching_identical':all(c['matching_identical'] for c in items.values())})
deferred={'recorded_at':now.isoformat(),'candidate_id':CID,'scope':'Same native error_readout.py protocol;all8scene error-localization readouts remain UNRUN',
 'actual_refusal':'guard(400) rejected with366.735992seconds remaining,before protocol/test staging or any CUDA execution',
 'budget_refusal_is_not_resource_block':True,'new_native_forwards':0,'native_failure':False,
 'groups':'Original native matched-positive mask error-point union versus valid correct-point complement;diagnostic GT only,frozen before interventions',
 'readouts':'Per-group denominator,original message loss-gradient dot unchanged candidate/uniform/mismatch delta(first-order surrogate only),actual mask-logit change;no training efficacy claim',
 'next_action':'Execute first2fixedTRAINscenes via error_readout.py under a new valid lease,then SAMEreadout on remaining6frozenTRAINscenes;no redoing passed backward/resources or old audits',
 'thresholds':'Native reconstruction/matching1e-6 unchanged;no tiny-sample efficacy cutoff or tuning'}
save('deferred_error_protocol.json',deferred)
save('analysis_summary.json',{'created_at':now.isoformat(),'candidate_id':CID,'scientific_stage':'validation',
 'new_stable_candidates':1,'structural_connection_revisions':1,'new_independent_package':True,'package_files':8,
 'native_forwards':total_native,'native_backwards':total_backward,'native_resource_predict_calls':sum(v['native_predict_calls'] for v in packages),
 'source_interface_calls':sum(v['source_interface_forwards'] for v in values),'suffix_calls':sum(v['suffix_replays'] for v in values),'criterion_calls':sum(v['criterion_replays'] for v in values),
 'suffix_gradient_probes':sum(v.get('suffix_gradient_probes',0) for v in values),
 'unique_fixed_TRAIN_scenes':8,'correlated_expressions_in_task_cohort':32,'resource_native_scene_count':4,
 'semantic_controls':semantic,'coarse_attention_is_not_a_proven_bottleneck_solution':True,
 'diagnosis_gate':False,'semantic_controls_gate':False,'reason':'Correct semantic key-value binding is not consistently better than uniform/mismatched controls;pretrained-loss signs are not trained harm or benefit. Neither whole-network missing information nor independent efficacy is established.',
 'native_backward_measured':True,'resources_measured':True,'cold_initialization_measured':True,
 'new_training':0,'admissions':0,'optimizer_steps':0,'scheduler_steps':0,'VAL_accuracy_selection':False,
 'original_failed_fixture_calls_retained':2,'candidate_import_failure_retained':'DuplicateCriterion from dual-model diagnostic loader;fixed only by fresh process,not force registry',
 'material_novelty':'UNKNOWN;ordinary cross-attention is existing prior art','full_optimizer_memory':'UNKNOWN',
 'deferred_error_localization':deferred,'whole_tick_status':'Pending postflight;not a scientific PASS or new training result',
 'deadline_at':owner['deadline_at'],'remaining_seconds_at_record':(datetime.fromisoformat(owner['deadline_at'])-now).total_seconds()})
work=tick.load(ROOT/'pipeline/research_work.json')
candidate=next(c for c in work['candidates'] if c['id']==CID)
revision=candidate['revision_history'][0]
revision.update(result='inconclusive',evidence=revision['evidence']+[evidence(OUT/'eight_scene_execution_summary.json'),evidence(OUT/'replacement_attribution_summary.json')])
gates={'diagnosis':{'passed':False,'reason':'No stable task-relevant semantic use deficit established beyond path activity;error-point localization pending'},
 'controls':{'passed':False,'reason':'Native identity/matching and operator contracts pass,but semantic correct-vs-uniform/mismatch direction is inconsistent;do not collapse these into a PASS'},
 'native_backward':{'passed':True,'evidence':[evidence(package_paths[1]),evidence(OUT/'fresh_native/fresh_native_result.json')]},
 'resources':{'passed':True,'evidence':[evidence(OUT/'resource_comparison.json')]},
 'independence':{'passed':True,'evidence':[evidence(OUT/'independent_package.json')]},
 'constraints':{'passed':False,'reason':'Structure and all fixed settings/bans reviewed,not a complete scientific admission;no receipt,commit or deployment'}}
advance([OUT/'analysis_summary.json',OUT/'deferred_error_protocol.json',OUT/'replacement_attribution_summary.json'],
 stage='validation',failure_scope='inconclusive',revision_history=[revision],gates=gates,
 next_action=deferred['next_action'],gate_result='Full native/cold initialization/resources/independent implementation measured;task diagnosis+semantic controls unpassed;no admission or training')
work=tick.load(ROOT/'pipeline/research_work.json')
work['design_cycle']={'status':'actionable_candidate_validation_pending','attempted_ids':[CID],
 'evidence':[evidence(OUT/'analysis_summary.json')],'resume_condition':deferred['next_action'],
 'note':'No global exhaustion,resource block,goal hold or elapsed deadline asserted. An active validation candidate remains;finish only accepts actual near-deadline disposition.'}
tick.save(ROOT/'pipeline/research_work.json',work)
final=ssh('''import json,subprocess,fcntl
from datetime import datetime,timezone
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],universal_newlines=True).strip()
assert [x.strip() for x in gpu.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],universal_newlines=True).strip()
locks={}
for kind in ('training','diagnostic','exclusive'):
    with open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b') as f:
        try:
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]='available_then_released'
        except BlockingIOError:locks[kind]='held_by_existing_writer'
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':gpu,'contexts':contexts,'locks':locks}))
''')
save('final_environment.json',final)
shutil.copyfile(ROOT/'pipeline/codex_memory.md',OUT/'memory_before.md')
shutil.copyfile(ROOT/'pipeline/diagnostic_bundles/tick_a89c20ef/goal_frozen.json',OUT/'goal_frozen.json')
goal=(OUT/'goal_frozen.json').read_text(encoding='utf-8')
review='''# Motivation Review - cluster_project
## 1. Goal
Unchanged current goal24constraints/11bans,hash42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec:
```json
'''+goal+'''
```
Target.5100,historicalM95.5020,baseline.4894,gap.0080;caches,not newly measured.
## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Coarse semantics can update points beyond own-cell gather | Active path,not efficacy | CPU/native/matching controls | Actual task deficit |
| Raw-key/refined-value connection improves semantic use | Inconclusive | Fixed8TRAINscenes | Correct-vs-mismatch direction inconsistent |
| Full graph is trainable and lightweight | Measured | Independent package/backward/cold init/resource pair | Whole optimizer peak unknown |
## 3. Experiment Assessment
M95 historical.5020 is comparator;available epoch16 is not verified historical champion weights.
M203-FLE cached.4885315597 is stopped,not restarted. No VAL-selection or new accuracy claim.
New package changes only coarse semantic readback;fine/middle CTF/own-ID paths and loss remain.
## 4. Gap Analysis
Eight physical TRAINscenes/32correlatedexpressions,not independent attention conditions.
Coarse replacement loss direction and correct-vs-mean/mismatch advantages vary;not trained harm.
Own-removal/remote-addition counterfactual does not uniquely explain risk;not a deployable residual design.
## 5. Design Rationale
Preserve the same stableID/revision1. Next isolate original native error points versus correct points
before admitting any structure. Do not repeat old rank/mean/padding/CSORT audits or passed resource tests.
## 6. Next Batch
Same candidate validation via deferred_error_protocol.json;no new queued training or historical reopen.
'''
design='''# Experiment Design - cluster_project
## 1. Motivation
Literal goal:hierarchical information interaction must genuinely update point/superpoint inst_feats
used with query for masks. This candidate tests coarse-global semantics while retaining fine/middle paths.
## 2. Current Best Results
| ID | State | Best mIoU | Role |
|---|---|---|---|
| M95 | Historical cached | .5020 | Comparator;availableepoch16provenance caveat |
| M203-FLE | Stopped cached | .4885315597 | No restart |
## 3. Analysis & Direction
Variables:x_i are current point features;C are raw8coarse means;V=C+FFN(LN(C)).
For each existing head,A=softmax(xC^T/sqrt(d_head));new coarse message=AV.
Fine and middle messages,existing scale fusion/output projection/message norm/outer encoder path stay unchanged.
Revision1 moves ONLY keys from V to C,no temperature/heads/scale/gate/QKV tuning.
Gradient:remote values receive A-weighted task gradient;native actual A gradient and all coarseFFN/norm gradients
are finite/nonzero both fromM95checkpoint and newNetwork+originalbackbone. No new trainable parameters.
Degeneracies:identical keys or zero queries give mean values;coarse nonempty bank required.
Complexity:O(B*N*Kcoarse*C),Kcoarse8,notN2;attention bufferO(B*heads*N*8).
## 4. Experiment Plan
| StableID | Current phase | Actual result | Next |
|---|---|---|---|
| coarse-semantic-point-cross-attention | validation | Computational path/resources pass;semantic diagnosis unpassed | Frozen error-point readout |
Original prototype,raw-key repair,uniform and cyclic mismatch all retained. Query/criterion inputs/matching
are fixed within each capture;different process prefixes are NOT claimed exactly paired.
## 5. GPU Allocation Plan
Only server4physicalGPU0 used with pinned hostname/UUID and3lifetimeflocks.
server3physicalGPU1 foreign-busy at06:13Shanghai,laterUNKNOWN. server4GPU1 NOTauthorized.
## 6. Implementation Checklist
- Independent8sourcefile package+same-numerical-config:done,no foreign variant imports.
- Full original criterion backward,workers0/4,cold backbone initialization:done.
- Same-handler resources bs1warmup20repeat100,matched input hashes:done.
- Task deficit and semantic controls:NOTpassed;new error-point readout unrun due guarded budget.
- Commit/safeFFsync/admission/queue/launch:NOTperformed;no trainingoptimizer/schedulersteps.
## 7. Risk Assessment
Near-uniform attention and inconsistent semantic controls remain material risks.
Do not infer benefit/harm from small pretrained loss changes or use residual diagnostic as successor.
Resource9.769168428G versusM959.762532428G;median35.9614vs35.3617ms;
inference memory+1.2878%,matched train activation peaks+0.3289%to+0.7063%.
Full optimizer peak and original no-cluster resource delta UNKNOWN;all default budgets unchanged.
## 8. Smell Check And Prior Art
New coarse-point information edges,not numeric-only tuning;no new learned gate/scalar/projection.
Attnpool/qcond/agg/multi,TrueRoute,FLE,relation2Dtransport checked at implementation level.
Ordinary cross-attention and latent output-query reading are prior art(PerceiverIO,arXiv2107.14795).
Material novelty UNKNOWN;this is an unadmitted structural hypothesis,not a novel attention primitive.
## 9. Post-Training Plan
Only after real admission:unchangedScanReferVAL mIoU,baseline/champion comparators,seed1999/
epochs50/max_iters70 and lightweightPareto;scene clustering,predefined relation/same-class groups.
Evaluation noise floor unquantified;no test/VALmechanism selection,no extra datasets/seeds.
Status:VALIDATION,notAPPROVEDfortraining.
'''
for path,text in ((ROOT/'pipeline/reviews/motivation_review_20261019_2d7cbb68_cpa.md',review),(ROOT/'pipeline/designs/exp_design_20261019_2d7cbb68_cpa.md',design)):
    with path.open('x',encoding='utf-8') as f:f.write(text)
decision=run(['C:/Program Files (x86)/Git/bin/bash.exe','C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh','cluster_project','other',
 '粗层语义到点特征的独立结构是否达到科学准入？',
 '保留同一CPA候选validation及一次key连接修订；完整反向、冷初始化和资源已测，但语义诊断不一致，不准入训练。',
 '八固定TRAIN场景正确key对均值/错配没有稳定优势；风险归因不唯一。原生图和梯度有效、9.769G及显存增量通过实测，不等于任务收益。',
 'pipeline/diagnostic_bundles/tick_2d7cbb68/analysis_summary.json;pipeline/diagnostic_bundles/tick_2d7cbb68/deferred_error_protocol.json'])
save('decision_execution.json',{'returncode':decision.returncode,'stdout':decision.stdout,'stderr':decision.stderr})
assert decision.returncode==0,decision.stderr
memory=f'''# Codex Research Memory
## Goal And Phase
- Tick{TOKEN},cluster_project only. GoalSHA{GOAL};24constraints/11bans,target.5100. Same current thread verified,Pipeline-cluster_projectDisabled.
- Mainline:scale-specific hierarchical updates of actual point/superpoint inst_feats used for masks. No tuning,N2attention,largeQKV,newgates/residual/routing/HDSrevision3/normrevision3/M201recovery/FLErestart.
- Onlyserver4physicalGPU0/.115/dl04-MS-7E06/UUID958e741a-e5cf-127e-ffe8-9b984e1f404c andserver3physicalGPU1/.120/sysu311-MS-7C59/UUID340de111-e7e4-ed2d-15c9-8ab6a253e4a0. server4GPU1 NOTauthorized. Passwordreferenceunread.
## Champion And Baseline
- CACHED historicalM95.5020,baseline.4894,target.5100,gap.0080. AvailableM95epoch16=.5024607181549072 NOTverifiedhistoricalchampionweights. Nonewaccuracymeasured.
- CACHED M203FLEbest.4885315597@epoch13,earlystop23/50;priorfullVALdelta-.0139291520 vsavailableM95,sceneCI[-.0223369116,-.0054631474]. NOTrestarted/rerun.
## Active Hypotheses
- {CID},stagevalidation,failure_scopeinconclusive,1preregisteredconnectionrevision. ConcreteNEWindependentpackageM95suffix_cpa_r1,8files,noforeignvariantimports,newparameters0;configonlystructuralmodechanges,allnumericalsettingsfixed.
- Candidate:coarsepointattentionQ=pointcurrentfeature,K=rawcoarsebank,V=CTFrefinedcoarse. Fine/middleoriginalpaths/fusion/lossunchanged. Prototypeinitiallyusedrefinedkeys;revision1keysourceonly,nottemperaturetuning.
- CPU/source actualremote-control0vsprototype.3366122815;sourcegradient0vsnew.3724726743. GraphactivityNOTtaskdeficit. TwofixtureAttributeErrorsretained;onlyinterfacesfixed.
- Fullsame-prefixnativecriterion/mask/scoresandidentitycontrols<=1e-6;ALLchangedmasktarget/index/num_boxesfingerprintsidentical. OriginalM95forwardswithsuffixgradientsnotfullcandidatebackward;separatefullcandidateandcoldtestsbelow.
- EightfixedTRAINscenes/32expressions taskreplication:rawkeylossdeltas[.000116109848,.000743627548,.000042438507,-.000026822090];correct-vs-uniformdirection2/4better,correct-vs-mismatch1/4better. Not efficacy/harm/populationCI or stablediagnosis.
- Eight-sceneown-removal/remote-additionfactorialdoesnotuniquelyexplainrisk;diagnosticONLY,NOTresidual/gateproposal. Allnegativesretained,no2ndstructuralrevision.
- Independentcandidatefullnativebackward4batches/workers0and4;actualattentionlossgradfinite/nonzero,all6existingcoarseFFN/normparamgradsfinite/nonzero. SameM95paramstate/shapes157484090params.
- COLDinitnewNetworkseed1999+originalbackboneSHAa6f400bcf9bd722230d16ea7c3424b0d7658730126df604f67b4cccf42e25c1f;4scenes/16expressions/2batchesworkers4nativeforwardbackwardPASS;AdamW/PolyLRconstructed,0steps/stateentries,noM95headreuse.
- ResourcesSAMEinput/unchangedFVCorehandlers:CPA9.769168428G,M959.762532428G,delta.006636G;median35.96142349vs35.36171450ms(+1.6959%),P9037.93424vs37.36143ms. Inferpeak+1.2878%;matchedtrainpeaks+0.3289%to+0.7063%,all<15%. Fulloptimizerpeak/originalno-clusterresourcedeltaUNKNOWN.
- Newoperatorfloat64CPUjointkeyvalue/pointpermutation,paddingoutput/gradient/extension,identicalkeyuniformcontracts<=1e-6,finite-differencegradcheckPASS. This is NOToldfullmodelpaddingaudit.
- ScientificdiagnosisandsemanticcontrolgatesNOTpassed;nativebackward/resources/physicalindependencemeasured. No scientificreceipt,commit,sync,queueortraining. StandardcrossattentionpriorartPerceiverIOchecked,materialnoveltyUNKNOWN.
- NEXTEXACT:deferred_error_protocol.json/error_readout.py. Originalmatched-positive-maskerrorpointunionversusvalidcorrectpoints;per-groupdenominators,nativemessagegdotdelta(firstordersurrogate)andactualmasklogitchange. ALL8scenesUNRUNunderthisNEWreadout:first2thenremaining6,groundtruthdiagnosticsonly. guard400refusedwith366.735992sec;noCUDA/nativefailure/resourceblock. DoNOTrepeatpassedresources/backwardoroldaudits.
## Closed Or Failed Directions
- Priorfinite rank/meanmoment/ancestry/padding/prefix/QF/HDS/FLEauditsremainCOMPLETEwithoriginalstrictfailures. Rank2orpooledmomentblindnessNOTwhole-networktaskdeficit;do not reopen.
- m95-native-support-faithful-csort REJECTED:cached32scenecompleteparentmeanloss1,gradient~0. No map-onlyrepair/tuning/rename. Purity/identity/centroidgraph/BCCAclosed,dirtyPDC/untrackedBCCApreserved.
- DuplicateCriterion failurewasdiagnosticloaderimporting2modelpackages;0candidateforward/bwd. Fixedfreshprocessdirectcandidate,notforce/deleteregistry;originalfailureretained,notanewmodelrevision.
- FourauxiliaryscopeholdsNOTdue06:09snapshot,retryfromprior~08:42orrealwakechanges;unchanged,nopromotion/recheck. Notmainlineresourceblocks.
## Running And Queue
- Snapshot2026-10-18T22:09:38.510560Z/design,deadline23:09:38.510560Z(Shanghai07:09:38);active0/target2,admissionbudget2,reservebudget0.
- Live06:13server4GPU0idle41MiB/0%/nocontexts/3locksavailable;server3GPU1foreignbusy18354MiB/100%;laterserver3UNKNOWN. FinalGPU0postcheckfinal_environment.json. EveryCUDAjobfreshidentity/idleness/3lifetimeflocks.
- No training/optimizer/schedulerupdates. Freshoptimizerconstructedbutunstepped. No otherprojects,schedulerchanges,newthreads,nestedCodex,deletion/eviction/reset/foreignjobchanges.
## Open Questions And Risks
- Coretaskdeficitstillunproven;untrainedlossorgradientisNOTtrainedbenefit/harm. Semanticbindingdirectioninconsistent;do notadmitfromresourcesuccessorreadoutactivity.
- No globalrouteexhaustion/resourcehold/phasehold/deadlinefiction. Candidateisactionablevalidation,notfakeblocked. FinishrequiresACTUALremaining<=180ifcapacitygapstillopen;no waiting/padding/repeatedunchangedfinish.
- Usagebegin->receiptpartialwindowonly;cacheinput/reasoningoutputaresubsets,notbilling. Fulltrainingpeak/noisefloor/noveltyunknown.
## Last Tick
- Bundlepipeline/diagnostic_bundles/tick_2d7cbb68. ACTUAL{total_native}nativeforwards/{total_backward}backwards,242resourcepredictcalls,59source-interface/69suffix/69criterioncalls,39suffixgradientprobes,1candidate+1revision;8uniqueTRAINscenes,repeatedconditionsnotindependentexperiments. Training/admissions/VALselection/optimizersteps0.
- Full6sectionreportsummary_{TOKEN}.md,review/design/decisionandguardednextprotocolpersisted. CurrentexecutionPENDINGfinish;do notclaimCOMPLETEwithoutactualpostflight/contextcommit/release.
- Previousa89c20efactuallyaborted04:45:13,receiptINCOMPLETE/contextnotcommitted;lease/pendingabsent04:45:36. Oldprereleasememoryplannedstatussuperseded;neverreuseoldtoken.
'''
assert len(memory.splitlines())<120
(ROOT/'pipeline/codex_memory.md').write_text(memory,encoding='utf-8')
notes={'actions':[
 '快照上海时间2026-10-19 06:09:38，design；历史最佳0.5020、目标0.5100、差0.0080。预检无在训/等待；无新mIoU测量。',
 '本轮建立同一稳定候选CPA：仅粗层语义到点特征的新信息边，细/中层、原损失和所有数值配置不变。一次预注册key来源连接修订；8文件独立包，无新增投影/门控/可学习参数，不重开FLE/HDS/路由或CSORT。',
 '同前向原生mask/损失重建和身份对照通过1e-6；所有条件的实际监督mask/indices/num_boxes一致。八固定TRAIN场景中，正确key相对均值和错配的方向不稳定，诊断及语义准入未通过，不能称训练收益或整个主线失败。',
 '完成自身粗簇移除/远处信息加入的归因诊断，结果不能唯一解释风险。它仅为非部署反事实，不生成被禁残差变体。',
 '独立候选完整原生反向、0/4worker，以及仅原backbone的新Network冷初始化均通过；实际attention和粗层FFN/norm有有限非零loss梯度。冷初始化构建AdamW/PolyLR但均0步骤/optimizer状态0，未复用M95诊断头。',
 '同输入、原FVCore计数器、bs1/warmup20/repeat100：CPA9.769168428G vs M959.762532428G，增加0.006636G；延迟35.9614 vs35.3617ms(+1.696%)；推理峰值显存+1.288%，匹配原生反向峰值+0.329%至+0.706%。无fulloptimizer峰值及原无clusterbaseline资源数据，记未知；不改变10G或15%规则。',
 '新算子的排列等变/键值联合排列不变、padding输出/梯度/扩展、相同key均值退化及有限差分通过；不是重复旧整网padding/内核审计。原CPU夹具两次接口失败和候选装载注册冲突均保留；后者以独立进程直接加载修复，未覆盖注册表。',
 f'实际{total_native}次原生前向/{total_backward}反向，242次资源predict、59次source-interface、69次suffix/criterion、39次suffix梯度探针；只有1候选/1结构修订，8个物理TRAIN场景；计数不是独立模型或训练实验数。训练、准入、验证选型、optimizer/scheduler更新均0。',
 '错误点定位读数被guard400在剩余366.735992秒时拒绝，未启动CUDA；不是资源阻塞或科学失败。deferred_error_protocol.json已保存，仍在同一ID的validation阶段，先执行首2场景，再余6；不重做已通过的资源/反向或已完成旧审计。',
 '资源授权仅server4物理GPU0与server3物理GPU1；06:13后者为外部占用18354MiB/100%，之后未知。最终GPU0实际占用和三个锁释放可用性见final_environment.json。未使用server4GPU1或触碰其他项目/调度。',
 '本轮科学状态：有可执行待续候选，核心语义诊断未证实，不准入训练。执行状态等待实际finish；不宣称提前耗尽路线、资源阻塞或截止已过，不修改deadline或校验器。',
 '用量仅以最终收据begin至receipt的可见响应窗口为准，数值在收据前未知；不含更早阅读、迟到记录及最终回复，不是账单；缓存是输入子集、推理是输出子集，不能重复相加。'
 ],'decisions':[
 '保留粗层语义直达点特征候选及一次key连接修订，现有独立实现、原生反向/冷初始化和资源证据有效；正确语义匹配的任务作用未稳定证实，诊断与准入仍不通过。',
 '下一步仅续做已冻结错误点定位读数；八场景采样、原监督、seed1999/epochs50/max_iters70、预算和全部禁令不变。无优化器更新、无训练入队、无旧路线重开。',
 '按真实deadline与规范finish结果收尾；若校验不通过，保留实际错误并abort释放。未执行读数不记失败或PASS，不以资源测试通过冒充科学成功。'
 ]}
save('notes.json',notes)
print(json.dumps({'persisted':True,'native_forwards':total_native,'native_backwards':total_backward,'stage':'validation','admission':False,'remaining_seconds':(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds(),'final_environment':final},ensure_ascii=False))
