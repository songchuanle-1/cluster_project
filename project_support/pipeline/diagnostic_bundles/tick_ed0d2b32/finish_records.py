"""Persist real partial science, verify resources, then render six-section report."""
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
from ops import guard,save,ssh,run,advance,evidence,tick,ROOT,OUT,MODELS,TOKEN,CID
RID='hierarchical-nonlocal-channel-rank-audit'
owner=guard(15)
native_paths=[OUT/'native_m95_1/native_trace_result.json',OUT/'native_m95_2/native_trace_result.json',OUT/'rank_m95/native_trace_result.json']
native=[tick.load(p) for p in native_paths]
assert all(r['passed'] for r in native)
capture=tick.load(OUT/'rank_m95/native_rank_capture_result.json')
math=tick.load(OUT/'rank_math_result.json')
failed=tick.load(OUT/'channel_null/native_channel_null_result.json')
assert capture['passed'] and math['passed'] and not failed['passed']
assert not (OUT/'channel_failure').exists(),'Do not claim follow-up unstarted if stage exists'
counts={'native_forwards':sum(r['native_forwards'] for r in native),'native_backwards':sum(r['native_backwards'] for r in native),
    'native_token_vjps':capture['native_token_vjps'],'source_interface_forwards':capture['full_shape_replays']+failed['source_interface_forwards'],
    'cpu_jacobians':math['cpu_jacobian_count'],'new_training':0,'new_VAL':0,'new_models':0,'new_admissions':0,'optimizer_steps':0,'scheduler_steps':0,'failure_followup_gpu_calls':0}
save('final_progress.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'counts':counts,
    'native_results':[evidence(p) for p in native_paths],'null_failure':evidence(OUT/'channel_null/native_channel_null_result.json'),
    'failure_magnitude':'UNKNOWN:originalrunner asserted before persisting partialreadout magnitudes',
    'failure_followup':'NOT_RUN:currenttick remaining safe GPU launch window insufficient;guard failed before stage creation',
    'cached_counts_included':False})
assets=tick.load(MODELS)['m95']
program='''from pathlib import Path
import hashlib,json,subprocess,fcntl,datetime
m='''+repr({'root':assets['root'],'name':assets['name'],'assets':assets['assets']})+'''
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
root=Path(m['root']);a=m['assets']
for name,digest in a['source_hashes'].items():assert sha(root/'framework/model/Quard_model'/m['name']/name)==digest
for name,path in [('checkpoint',a['checkpoint']),('config',a['config_path']),('annotation',a['annotation_path'])]:assert sha(path)==a[name+'_sha256']
assert sha(root/'framework/dataset/scannetv2.py')==a['dataset_source_sha256']
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert row.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
assert not contexts
locks={}
for name in ('training','diagnostic','exclusive'):
    with open('/tmp/cluster_project_gpu0_'+name+'.lock','a+b') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[name]='released'
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'gpu':row,'contexts':contexts,'locks':locks,'m95_frozen_source_config_checkpoint_annotation_dataset_unchanged':True}))
'''
environment=ssh(program,timeout=60)
save('final_environment.json',environment)
summary={'observed_at':datetime.now(timezone.utc).isoformat(),'counts':counts,'frozen_assets_unchanged':True,
    'finite_repeatability_audit':'COMPLETE;actual pair incidence/decodedmask/alignedoutput identical;pastcounterexamples retained;unique kernelcause UNKNOWN,not a mainline prerequisite',
    'conditional_mean_context_ranks':math['mean_context_ranks'],'own_coarse_token_ranks':math['own_coarse_ranks'],
    'native_gradient_projection_median':math['mean_accessible_squared_fraction_median'],
    'rank_matched_DCT_projection_median':math['rank_matched_fixed_DCT_squared_fraction_median'],
    'own_coarse_projection_median':math['own_coarse_accessible_squared_fraction_median'],
    'denominator':{'scenes':2,'expressions':8,'readouts':24},'native_fullprefix_reconstruction':capture['native_replay_max_absolute'],
    'native_null_control':'FAILED original1e-6 gate after10sourceforwards;exactmagnitude UNKNOWN;followup NOT_RUN due safetywindow',
    'trained_efficacy':'UNKNOWN','whole_network_rank_claim':False,'novelty':'UNESTABLISHED','execution_status':'PENDING canonical finish/abort'}
save('analysis_summary.json',summary)
memory={
 'Goal And Phase':['Tick ed0d2b32aa804291bbf7f5a23828a4a6,2026-10-18Shanghai,cluster_project only. GoalSHA42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec unchanged;24constraints/11bans;target.5100.',
 'Mainline:scale-specific hierarchical point/superpoint inst_feats updates used withquery for masks;memoryonlyconstraint. No tuning,N2attention,largeQKV,bannedrenaming,HDSrevision3,normrevision3,M201recovery/FLErestart.',
 'Onlyserver4physicalGPU0/.115/dl04-MS-7E06/UUIDGPU-958e741a-e5cf-127e-ffe8-9b984e1f404c andserver3physicalGPU1/.120/sysu311-MS-7C59/UUIDGPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0. server4GPU1 NOTauthorized. Keysused,passwordreferenceunread. Seed1999/batch2/workers4/epochs50/maxiters70 unchanged.'],
 'Champion And Baseline':['CACHED historicalM95.5020,baseline.4894,target.5100,gap.0080. AvailableM95epoch16=.5024607181549072 NOT verifiedhistoricalchampionweights.',
 'CACHED M203FLEnormalearlystop23/50,bestepoch13=.48853155970573425,NOTrestarted. FullVAL9508/141 pairedavailableM95delta-.0139291520,sceneCI[-.0223369116,-.0054631474];notrerun.'],
 'Active Hypotheses':['NEW hierarchical-nonlocal-channel-rank-audit VALIDATION,failure_scope=inconclusive;diagnosis only,NOT a gate/model/newattention proposal or admission.',
 'Sourcecondition:CTF independentclusterFFN,HCGgathers ownscaleIDs;outsidecoarsestcluster channels enter conditioned pointmessage only via globalmean->3softmaxscaleweights,Jacobianrank<=2. NOTwhole-network rank/bottleneck:upstreamencoder/decoder/weights offerotherpaths.',
 'ActualnativeM95capture PASS,fullshapeprefixreconstruction0,nativeflags preserved,24owncoarseVJPnonzero/remoteexact0,originalparametergradsnotaccumulated. Fixed2TRAINscenes/8expressions/first-middle-last24readouts;no populationCI.',
 '48CPUfloat64Jacobians:meancontext rank2 all24,owncoarse rank255. Nativegradient squaredprojection median.02924659679,owncoarse.99998850419,fixedrankmatchedDCT.003474533423. These are geometric projections,NOT taskloss gain/harm or modelquality.',
 'Nativechannel-null sourcefollowup FAILED original1e-6 at3rdreadout(expr0,lastvalid) after10sourceforwards;baseline0. Exactfailednull magnitude UNKNOWN because runnerasserted before partialrecords persisted. Keeporiginalsource/result/manifest/failure. No tolerancechange.',
 'Prespecified one-failing-readout followup PREPARED BUT NOTRUN:guard380 failed before any stage/GPUcall. Files channel_failure_prereg.md/native_channel_failure.py/run_channel_failure.py available;needs NEWtoken/deadline beforeuse.',
 'NEXT sameID:single fixedfailure readout,save exactnull/row/owncoarse changes and float32cast/mean-rounding residuals;preserve strict1e-6/1e-12 and sourceflags. No retryuntilpassing;taskcausalintervention and originalpaperreview stillrequired before structuralcandidate/admission.'],
 'Closed Or Failed Directions':['native-train-prefix-repeatability-audit finite COMPLETE this tick:2actualnativeM95 captures selectedsameSimt/TF32False;input/weights/RNGsame,alignedoutput0 andcanonicalfwd/bwd0. Maskstorage initiallynaivelyreindexed,then8bitsemantic reconstruction undoargsort provescanonicalmasksequal;originalmisreadretained. Float64referencefirst256coordinatespair0,vsnative2.87946e-6 reported/notnewgate. Unique kernelcause remains UNKNOWN;do not reopen indefinitekernelwork.',
 'Previousfinitepaddingaudit COMPLETE:uniformmaskedmean reference+actualweightCPU/nativecontrols,maskedgrad0;initialrequires_gradFalsefailures retained;restoringnativeflags givesexact0. Singleopfix NOTcoreinnovation/admission.',
 'PriorQF finite COMPLETE,inconclusivebenefit;pointonlyPiou+.0075331 CIcross0;no normrevision3. HDS/FLEnegative trainedrealizations retained,notwholemainlinefalsification;no restart.',
 'Targetedduplicatechecks foundsuperpoint-oracle-ceiling andcentroid-graph/BCCA routes alreadyclosed;DIDNOTreopen/rename them. m95-hierarchical-mask-feature-path-audit alreadycoversscalecomplementarity.',
 'Fourauxiliaryhuman/scopeholds unchanged/notdue at22:09snapshot;prioractualrecheck~19:10/retry~23:10. Do not automaticallyprioritize auxiliaryholds or derivevariants on timer/idleGPU;originalauthorization conditionsremain.'],
 'Running And Queue':['Snapshot2026-10-18T14:09:37.742682Z/design,deadline15:09:37.742682Z(Shanghai23:09:37);active0/target2/admissionbudget2/reservebudget0. Actualenvthread01a04987-fdbe-7301-b2f0-f9b6ab60f74c verified;Pipeline-cluster_projectDisabled unchanged.',
 'Onlyserver4GPU0used,oneprocessatatime/lifetime3locks;no trainingloop/VAL/admission/optimizer/scheduler/queuewrites. Finalenvironment.json recordsfreshnoGPUcontexts/3locksreleased/sourceconfcheckpointshashesunchanged. server3utilization UNKNOWN.',
 'DirtyPDC/untrackedBCCA andforeignjobs preserved;noreset/eviction/lockdeletion/repeatedpreflight/deadlineedit/background/newtask/nestedCodex.'],
 'Open Questions And Risks':['Conditionedmodule rankbound is real but not traineddeficit/generalization/novelty. Crucialnative nullgate FAILED;do not treat CPUmath/sourceVJP as scientificPASS or automatically add globalattention/gate.',
 'Readoutprojection lowdimensioncanbegeneric;onefixedDCTcontrol isnot a randomspace distribution. Only2scenes/no populationCI. Localgdotmessagechange inattemptednulltest isnot measurednewnativeloss.',
 'CachedfullmodelFLE9.627987020G/M959.762532428G andlatency43.732vs36.821ms notremeasured. Currentdiagnostic peaks excludeoptimizerstate,NOTalltrainingresourcePASS. Default10G/HDSexactexception unchanged.'],
 'Last Tick':['Bundlepipeline/diagnostic_bundles/tick_ed0d2b32;final_progress/analysis_summary/final_environment/native_stride/mask_storage/rank_math/native_nullfailure andpreregistered followup. Previousmemory backedup.',
 'THIS tick3nativeforwards/3nativebackwards,24nativeinterface tokenVJPs,11sourceinterfaceforwardsincluding10failednullattempt forwards,48CPUJacobians. Preparedfailurefollowup GPUcalls0. Oldcachedcountsnotadded. Newdiagnosis1,finiteauditcompleted1;newtraining/VAL/models/admissions/optimizer/scheduler0.',
 'Reportsummary_ed0d2b32aa804291bbf7f5a23828a4a6.md hasfull6sections;receiptusage begin-to-receiptonly,cachedinput/reasoningoutput subsets,notbilling,numericusage UNKNOWNuntilreceipt.',
 'Execution PENDING atmemorywrite;canonical receipt/finish overridesstalePENDING. VerifyPASS/COMPLETE/FINALIZED/contextcommitted andownedlease/pendingabsent;otherwiseabort/release exactfailure. No postreleasewrites.']}
guard()
shutil.copyfile(ROOT/'pipeline/codex_memory.md',OUT/'previous_memory.md')
text='# Codex Research Memory\n'+''.join('## '+h+'\n'+''.join('- '+v+'\n' for v in values) for h,values in memory.items())
assert len(text.splitlines())<120
(ROOT/'pipeline/codex_memory.md').write_text(text,encoding='utf-8')
decision=run(['C:/Program Files (x86)/Git/bin/bash.exe','C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh','cluster_project','other',
 '条件跨粗簇通道秩是否足以支持新结构训练？','有限数值审计收束；主线条件秩诊断有实测，但原生null门槛失败，保留验证中。后续只复查固定失败读出，不调阈值不训练。','3次原生反向、24原生接口VJP、48CPUJacobian；null失败实际幅度未知，单案例复查因安全窗口未启动。','pipeline/diagnostic_bundles/tick_ed0d2b32/analysis_summary.json; final_progress.json; final_environment.json'],timeout=15)
save('decision_execution.json',{'returncode':decision.returncode,'stdout':decision.stdout,'stderr':decision.stderr})
assert decision.returncode==0,decision.stderr
decision_path=Path(decision.stdout.strip().rsplit('-> ',1)[1])
advance([OUT/'analysis_summary.json',OUT/'final_progress.json',OUT/'final_environment.json',OUT/'channel_failure_prereg.md',OUT/'native_channel_failure.py',OUT/'run_channel_failure.py',decision_path],candidate_id=RID,
    stage='validation',failure_scope='inconclusive',gate_result='Conditionalrank/VJP findings retained;nativechannelnull FAILED strict1e-6 after10sourceforwards;exactfailureamplitude UNKNOWN;followup NOTRUN due safe-window guard;NOT admissible.',
    next_action='In fresh owning tick run ONE prespecified expression0/lastvalid nullcontrol capture:record exactfailure magnitude, float32cast/mean-rounding residuals and unchangednativeflags/gates. Never retryuntilPASS,relax1e-6/1e-12 or infer trained benefit. Prepared runner needs fresh token/deadline.')
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
assert 0<remaining<=180,remaining
work=tick.load(ROOT/'pipeline/research_work.json')
work['design_cycle']={'stop_reason':'tick_deadline_near','attempted_ids':[CID,RID],
    'evidence':[evidence(OUT/'final_progress.json'),evidence(OUT/'analysis_summary.json')],
    'resume_condition':'New owning lease/liveidle authorizedGPU/triplelocks;singleprespecified failingreadout recording with unchanged1e-6/1e-12/nativeflags;science remains inconclusive.'}
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
notes={'actions':[
 '快照2026-10-18 22:09:37上海/design；begin预检仅一次，原owner核实。只用server4GPU0，未使用GPU1/server3，未改变目标/调度/训练协议。',
 '两次实际原生M95调用补全所选算法/索引：坐标对齐输出0，fwd/bwd连接相同。最初mask存储误读已保留；反解argsort并用8邻居位图语义控制证明mask实际一致。有限数值审计完成，不为唯一内核原因无限延期主线。',
 '新增主线条件通道秩诊断：2场景8表达24固定读出；原生前缀完整重建0，24自身粗簇VJP活跃/其他粗簇精确0；48CPUJacobian测均值上下文秩2、自身粗簇255。梯度平方投影中位数0.0292466，固定同秩DCT0.00347453；不是训练loss改善或整网表达力上限。',
 '关键负面结果：原生null对照在第三个固定读出超过既定1e-6门槛后停止，累计10接口前向；基线重建0。具体失败幅度因原脚本未先保存部分记录而未知，不能写0。保留原始源码、manifest和失败；一次固定失败读出复查已预注册，但安全窗口guard失败，实际未启动/GPU调用0。',
 '本轮实际3次原生整网前后向、24原生接口VJP、11接口前向含失败尝试、48CPUJacobian；新训练/VAL/model/准入/优化步骤0。final_environment核实冻结资产未变、GPU0无上下文、三锁释放。',
 '用量仅begin至收据可见窗口，具体值待helper收据；缺失未知，缓存属于输入/推理属于输出子集，不重复相加、不当账单。实际产出为本轮上述诊断和失败证据，不是token量。'],
 'decisions':['没有新mIoU提升：目标0.5100、历史最佳0.5020、差0.0080；缓存FLE早停23/50最佳0.48853156不重启。主线研究未改为单纯显存或数值修复。',
 '新候选保持validation/证据不确定，未完成科学准入，不新建训练变体。条件秩测量不证明整网瓶颈、效果或新颖性；原生null失败不能靠放宽阈值记PASS。四个辅助保留不自动重开。',
 '当前实际剩余'+str(round(remaining))+'秒，真实末180秒按tick_deadline_near保留同一失败读出的具体下一步；本轮执行状态仍待finish校验，失败则保留证据并abort核实释放。']}
save('notes_final.json',notes)
print(tick.report('cluster_project',TOKEN,str(OUT/'notes_final.json')))
print(json.dumps({'counts':counts,'remaining_seconds':remaining,'science':'inconclusive;native nullgate failed,not trainingadmission','execution':'ready for canonical finish'}))
