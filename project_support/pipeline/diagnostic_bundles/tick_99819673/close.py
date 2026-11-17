"""Honest current-source numerical hold, complete audit, then foreground validation."""
import copy
from datetime import datetime,timedelta,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import register
c=register.c
ROOT,OUT=register.ROOT,register.OUT
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr'


def main():
    c.guard(600)
    matched=c.tick.load(OUT/'committed_matched_controls_candidate_result.json')
    native=c.tick.load(OUT/'validation_committed_controls_candidate_result.json')
    resources=c.tick.load(OUT/'validation_committed_resources_candidate_result.json')
    parent=c.tick.load(OUT/'validation_h2_resources_champion_result.json')
    decomposition=c.tick.load(OUT/'numeric_decomposition2_decompose_candidate_result.json')
    assert all(x['execution_completed'] for x in (matched,native,resources,parent,decomposition))
    failures=[{'pair_index':b['pair_index'],'expression':x['expression'],'weighted_fine_mean_error':x['weighted_fine_mean_error']}
        for b in matched['batches'] for x in b['operator'] if x['weighted_fine_mean_error']>1e-6]
    assert len(failures)==1 and failures[0]['weighted_fine_mean_error']==1.0270338783868738e-6
    commit=c.tick.load(OUT/'local_commit_result.json')['code_commit']
    assert commit=='36b59daae6cdad2560024379eb5ed6acbcb20db2'
    package=ROOT/'Cluster/framework/model/Quard_model'/NAME
    expected=c.tick.load(OUT/'validation_committed/native_manifest.json')['candidate_source_hashes']
    binding=[]
    for path in sorted(package.glob('*.py')):
        relative=path.relative_to(ROOT/'Cluster').as_posix()
        blob=subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'show',commit+':'+relative])
        sha=hashlib.sha256(blob).hexdigest()
        assert sha==expected[path.name]==c.tick.digest(path)==c.tick.digest(OUT/'source_committed'/path.name)
        binding.append({'path':relative,'sha256':sha})
    source=c.save('committed_source_binding.json',{'observed_at':c.now(),'code_commit':commit,'files':binding,
        'actual_current_bytes_equal_committed_blobs_and_native_tested_source':True,'source_language_changed_after_commit':False,
        'line_ending_note':'Git LF normalization has identical normalized bytes/AST; this does not explain or excuse the fresh numerical failure.'})
    review=c.save('committed_gate_review.json',{'observed_at':c.now(),'candidate_id':c.CID,'code_commit':commit,
        'scientific_admission':False,'failure_scope':'implementation','blocker_kind':'numerical_control_failure',
        'failed_gate':'point-mass-weighted fine pre-fusion mean invariance <=1e-6','tolerance':1e-6,'failures':failures,
        'denominators':{'scenes':8,'expressions':32,'failed_expression_records':1},
        'passed_components':{'full_source_identity_row_inverse_disabled_parent_max':native['maximum_full_source_control_error'],
            'gradient_tensors_finite':native['gradient_tensor_count'],'transport_path_finite_nonzero':native['transport_path_gradients'],
            'native_matched_identity_max':max(v for b in matched['batches'] for v in b['controls'].values()),
            'strict_equal_mass_conjugacy_max':max(x['strict_equal_mass_conjugacy_error'] for b in matched['batches'] for x in b['operator'])},
        'preservation':'Earlier R2 tested-source PASS and completed revision_history remain immutable. Current committed-byte retest contradicts the original conservation gate, so no admission receipt, queue or training. No favorable-rerun selection.',
        'decomposition':{'summary':decomposition['summary'],'fixture':decomposition['fixture'],
            'limits':'This is a fresh capture, not the original failed P/T/Tprime. FP64 reference matmul has its own rounding; do not call exact real arithmetic. Only per-group maxima and maximum-coordinate components persisted; complete per-channel arrays/P32/Tprime32 were not retained, a narrower archive than preregistration. Fresh drift9.5367e-7 does not clear prior1.0270e-6 failure.'},
        'resources':{'parameters_added':0,'standard_flops_g':resources['profile']['flops_g'],'parent_standard_flops_g':parent['profile']['flops_g'],
            'median_ms':resources['median_ms'],'parent_median_ms':parent['median_ms'],'median_ratio':resources['median_ms']/parent['median_ms'],
            'p90_ms':resources['p90_ms'],'parent_p90_ms':parent['p90_ms'],'peak_allocated_bytes_each':resources['peak_allocated_bytes'],
            'full_optimizer_peak':'UNKNOWN','original_no_cluster_baseline_resource_delta':'UNKNOWN; original config absent, no fabricated substitute'},
        'task_readout':'Same8TRAINscenes/32expressions: content FG worse than matched no-transport7/8scene; better than strict mismatch6/8scene. Actual inst/mask path active, trained efficacy and global novelty unknown. No mechanism-family falsification.',
        'revision_boundary':'Default2implementation revisions consumed. No automatic R3 or precision/tolerance/FPS/seed/schedule change; numerical hold is not missing GPU permission or trained harm.',
        'evidence':[c.evidence(OUT/x) for x in ('committed_matched_controls_candidate_result.json','validation_committed_controls_candidate_result.json',
            'validation_committed_resources_candidate_result.json','numeric_decomposition2_decompose_candidate_result.json',
            'committed_bytes_retest_preregistration.json','local_commit_result.json','final_release_after_decomposition.json')]})
    # Log the concrete decision through the canonical helper, without editing the skill.
    script=c.SKILL/'log_decision.sh'
    shell=Path('C:/Program Files (x86)/Git/bin/bash.exe');assert shell.is_file()
    command=[str(shell),'-s','--','cluster_project','next_batch',
        'Can committed RSTR pass the frozen conservation control?',
        'Hold RSTR; preserve commit and all failed controls.',
        'One of32expressions exceeds1e-6. Two revisions consumed; no automaticR3. All8pending IDs are scoped/numerical holds, not a GPU shortage.',
        str(review)]
    result=subprocess.run(command,input=script.read_text(encoding='utf-8'),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
    assert result.returncode==0,result.stderr
    decision=Path(result.stdout.strip().split('-> ')[-1]);assert decision.is_file()
    helper=c.save('final_decision_helper.json',{'observed_at':c.now(),'canonical_script':str(script),'canonical_script_sha256':c.tick.digest(script),
        'execution':'Canonical content via Git bash stdin with normal LF shell line endings; no skill edits.','returncode':result.returncode,
        'stdout':result.stdout,'stderr':result.stderr,'decision':c.evidence(decision)})
    design=ROOT/'pipeline/designs/exp_design_20261021-0028_rstr_committed_hold.md'
    text=f'''# Experiment Design — RSTR 当前已提交、数值待解版本
更新于 {c.now()}；稳定ID `{c.CID}`；commit `{commit}`。

## 1. Motivation（为什么设计这批实验）
主线是层级交互真实更新inst_feats并参与query-mask生成；目标mIoU≥.5100，M95历史最佳.5020，差.0080。完整冻结goal见上游 `pipeline/reviews/motivation_review_20261020-2359_rstr.md`。本轮只设计一个新结构，默认8/8pending上限及全部25约束/11bans未变。

## 2. Current Best Results（基于什么数据做决策）
| 记录 | 结果 | 范围 |
|---|---|---|
| baseline / M95 | .4894 / .5020 | 历史训练结果；本轮无新mIoU |
| RSTR committed R2 | 未训练，scientific_admission=false | 8TRAINscene/32expr，same cohort重复诊断 |
| 最终源图控制 / backward | 最大0；642梯度有限，传输入/输出非零 | 完整实际pooling+active encoder，固定FPS membership；不是上游backbone/FPS重编号等变 |
| 融合前加权均值控制 | **1/32表达1.027033878e-6 >1e-6 FAIL** | 早先9.5367e-7通过仍保留，不能挑通过复测 |

## 3. Analysis & Direction（方向分析）
原CTF是per-token refinement后按ID读回；祖先mean仍含间接信息，新假设仅针对细叶之间缺少直接内容和值交换。目标常跨细叶，新的路径和内容对应确实改变mask；相对同R2排序/CSR的无传输参考，FG7/8scene变差，相对严格错配6/8更好。平滑是风险，不是收益证明。M39全尺度投影attention+residual/LN、PCE物理接触点图、FLE同叶点图、CPA point-to-coarse和HDS支持集的历史状态不重开。MH/Sinkformers是公开既有primitive，整体新颖性未知。

## 4. Experiment Plan（具体做什么）
同一中层parent内，T_i为CTF细token，n_i为有效超点行成员数，π_i=n_i/Σn；沿原8heads/d32。Q_ij=softmax_j(T_i·T_j/√32)，i≠j时P_ij=min(Q_ij,π_jQ_ji/π_i)，P_ii=1−Σ_j≠iP_ij，T'=PT。只替换fine bank，保留原中粗信息和所有已有模块。数学上πᵀP=πᵀ，浮点实测必须满足原1e-6；不声称融合/投影/LN/logit均值守恒。

匹配对照固定：无传输；任意fixed cycle affinity（π和值固定）；等n子集fixed cycle affinity，保持P_c=RPRᵀ。所有GT只读出，query由无传输native固定，生产及每个对照都恰好传输一次。不同坐标顺序同步排列features/mask/pos/ids[0]并逆恢复，GT不移位。

当前动作是**数值hold**，无可自动执行的第三修订。后续如合法恢复，仍须同一ID/原门槛/原失败证据，不能换名重开或改FP32/seed/FPS/温度过关。训练后评估计划保留早先设计§4：原ScanRefer split/seed1999/50epochs/max_iters70，主mIoU与M95/baseline对比，scene聚类配对不确定性、预定义多叶/单叶/混合父簇及FG/non-target子组，下降≥.002且95%区间上界<0记material harm；test不选机制，不额外seed扫参。

## 5. GPU Allocation Plan（GPU 分配计划）
本轮仅server4GPU0做原生诊断，末次00:27Shanghai已核验无compute context、三类flock可用；没有新训练。server4GPU0/1及server3GPU1权限保持，不能把授权名单当实时空闲。没有GPU忙的停止理由；所有研究ID当前被scope/numeric门阻挡且pending8/8。

## 6. Implementation Checklist（实施清单）
- 已完成：独立8源文件+1配置、AST/import/hash、原生loss反向、完整源图控制、最终提交字节复测、同口径资源、全部负面留档。
- 已获人类明确授权并完成：只涉及这9文件的本地commit `{commit[:8]}`；Git LF规整与旧AST等价，精确commit源重新测过。未把行尾当数值失败原因。
- 当前FAIL：融合前真实超点质量均值误差1.027e-6>原1e-6；没有准入receipt、推送、生产同步、入队、optimizer或训练。
- R1 failed、早先R2测试passed记录保持不可变；追加committed复测FAIL决定当前不准入。默认两次实现修订用完。
- 新误差分解：fresh capture2048groups/32calls，最差9.5367e-7，其中同坐标P32平稳性应用约−1.2614e-7、FP32乘法约−8.2754e-7，重构差0；不是原失败输入。只归档group最大值/最大坐标，未保留全channel误差/P/Tprime；不能说精确归因原FAIL或解除hold。

## 7. Risk Assessment（风险评估）
最终已提交字节同口径bs1,warmup20,repeat100：M95median{parent['median_ms']:.3f}ms、P90{parent['p90_ms']:.3f}ms；RSTRmedian{resources['median_ms']:.3f}ms、P90{resources['p90_ms']:.3f}ms，median+{(resources['median_ms']/parent['median_ms']-1)*100:.2f}%。计数9.762532428→9.763134540G，参数增量0，推理峰值各936763392bytes。FVCore不支持项仍列原结果；完整optimizer峰值/无cluster baseline资源差/总体噪声底/训练效果/整体新颖性未知。不宣称Pareto胜出。

按质量可逆凸组合，weighted variance预计收缩，本轮native约26.73%；可能损伤目标细节，FG负面结果不可用背景均值掩盖。canonical实现要求valid行连续前缀、无重合有效xyz；未覆盖不能补造。

## 8. Smell Check
零新增参数但新增直接跨细叶依赖和非平凡信息聚合，不是纯归一化/scaling小层；原8heads/d32不扫值。没有新learned gate、residual支路、大QKV、语言/query路由、point N²或重复层注入。R1/R2只修数值顺序，不冒充新机制。理论与技术路径成立不代替浮点门或效益。

当前状态：设计及本地提交完成；实现数值hold；核心假设未被科学证伪，训练收益未知。最新证据 `pipeline/diagnostic_bundles/tick_99819673/committed_gate_review.json`。
'''
    with design.open('x',encoding='utf-8') as stream:stream.write(text)
    work=c.tick.load(ROOT/'pipeline/research_work.json');candidate=next(x for x in work['candidates'] if x['id']==c.CID)
    existing={(x['path'],x['sha256']) for x in candidate['evidence']}
    evidence_paths=[source,review,design,decision,helper,Path(__file__),OUT/'committed_matched_controls_candidate_result.json',
        OUT/'validation_committed_controls_candidate_result.json',OUT/'validation_committed_resources_candidate_result.json',
        OUT/'numeric_decomposition2_decompose_candidate_result.json',OUT/'final_release_after_decomposition.json',OUT/'committed_bytes_retest_preregistration.json',
        OUT/'numeric_decomposition_timing.json']
    for path in evidence_paths:
        value=c.evidence(path)
        if (value['path'],value['sha256']) not in existing:candidate['evidence'].append(value)
    candidate.update(stage='blocked',blocker_kind='numerical_control_failure',failure_scope='implementation',
        blocker='Committed R2 weighted fine pre-fusion mean control exceeds frozen1e-6:1.0270338783868738e-6 in1/32expressions. Fullsource0 does not compensate. Default2implementation revisions consumed; no automaticR3.',
        retry_after=(datetime.now(timezone.utc)+timedelta(hours=4)).isoformat(),
        unblock_condition='New independently auditable evidence plus any required scoped extra-revision authorization for the SAME candidate under unchanged goal/gates. A timer/free GPU/favorable fresh capture alone does not unblock; changed implementation must retest all affected original gates.',
        next_action='Preserve committed9file bundle and allR0/R1/earlierR2/current-retest outcomes. Review numeric decomposition limits; no automatic third repair, precision/tolerance/FPS/seed change, push, receipt, queue or training. Resume only a legally authorized same-ID next step after real new evidence/scope.',
        scientific_admission=False,code_commit=commit,design=c.evidence(design),
        current_retest={'status':'failed','scope':'implementation','evidence':c.evidence(review)},
        wake_paths=['pipeline/goal.json','SERVERS.yaml','pipeline/authorizations/rstr_extra_revision_authorization.json'])
    pending=[x for x in work['candidates'] if x['stage'] not in ('training','complete','rejected','closed')]
    assert len(pending)==8 and all(x['stage']=='blocked' for x in pending)
    capacity=c.save('bounded_stop_capacity.json',{'observed_at':c.now(),'pending_count':8,'pending_limit':8,
        'records':[{'id':x['id'],'stage':x['stage'],'blocker_kind':x.get('blocker_kind'),'failure_scope':x.get('failure_scope')} for x in pending],
        'actual_reason':'New unfinished IDs prohibited by8/8research preparation limit. Every existing nonterminal ID is currently scoped or numerical hold; RSTR fixed decomposition completed and no authorized third realization exists. Full pending alone never forbids advancing an existing executable action.',
        'not_claimed':['GPU shortage','two independently exhausted causal routes','global route exhaustion','elapsed deadline','hypothesis falsification'],
        'resume_condition':'Resume actual newly authorized/evidenced existing action, or independent new diagnosis when legitimate pending headroom opens. Do not remove/complete holds to fabricate headroom.'})
    candidate['evidence'].append(c.evidence(capacity))
    if work.get('design_cycle'):work.setdefault('design_cycle_history',[]).append(copy.deepcopy(work['design_cycle']))
    work['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':[c.CID],
        'actual_reason':'Legacy operational stop label for bounded research capacity/scope holds: pending8/8 and all existing IDs blocked. RSTR itself remains numerical_control_failure, never a human/GPU permission diagnosis.',
        'evidence':[c.evidence(capacity),c.evidence(review),c.evidence(decision)],
        'resume_condition':'Existing holds must gain real new evidence/authorized next action, or pending headroom must legitimately open; no automaticR3, favorable-repeat clearing or stale permission request.'}
    c.tick.save(ROOT/'pipeline/research_work.json',work)
    memory=f'''# Codex Research Memory

## Goal And Phase
- Actual owner {c.THREAD} verified against environment/execution_mode; current tick {c.TOKEN}, DESIGN snapshot2026-10-20T23:47:29Shanghai,deadline2026-10-21T00:47:29Shanghai. Finish not yet claimed; receipt/release authoritative.
- GoalSHA{c.GOAL};target.5100,M95best.5020,gap.0080,baseline.4894. Mainline hierarchy→inst_feats→query/mask; auxiliary supervision held.25constraints/11bans unchanged;seed1999/epochs50/max_iters70/default10G unchanged. Old Windows scheduler remains Disabled, no automation change.
- Recovery owner chat01a159c5 retained original01a04987 history. Prior a3495e4b INCOMPLETE; e7cf135a FINALIZED; db8abb54 steady FINALIZED. Do not replayoldtokens.

## Champion And Baseline
- No new trained result,optimizer step,queue admission,push,production deployment ortraining. FrozenM95epoch16 diagnostic only,not guaranteed champion checkpoint.
- Latest committed-byte matched resources: M95median{parent['median_ms']:.6f}/P90{parent['p90_ms']:.6f}ms;RSTR{resources['median_ms']:.6f}/{resources['p90_ms']:.6f}ms,median+{(resources['median_ms']/parent['median_ms']-1)*100:.3f}%;9.762532428→9.763134540G;157484090params each,added0;inferenceallocated936763392/reserved1191182336each. Unsupportedops retained. Fulloptimizerpeak/originalno-clusterresource delta UNKNOWN;historicalconfigs/model_base1.yamlabsent, no fabricatedsubstitute.

## Active Hypotheses
- New stableID{c.CID} only; RSTR fixed parent-sibling fine token transport. π=n/sum(n)countsSUPERPOINTrows,8heads/d32,Q=softmax(TTᵀ/√32),offdiagPij=min(Qij,πjQji/πi),diagcompletion,T'=PT. Only fine pre-fusion massmean claim;notpostfusion/LN/logit.
- Independent8modelsource+1config created; actualsource9file localcommit{commit} under directhumanreply‘授权这9个文件的本地提交’. Authpipeline/authorizations/rstr_local_commit_20261021_99819673.json. Newreply grants onlylocalcommit; no otherconsent invented. No unrelatedfilescommitted.
- Gitautocrlf normalizedCRLF→LF;normalizedbytes/ASTsame;livefiles nowexactcommitLF andexactnative-testedsource. No LF-causes-numerical-failureclaim. OriginalarchivesR0/R1/R2preserved.
- Fullactualsourcepooling+activeencoder controlsR0max2.861e-6FAIL. R1fixedfeature-onlyCSR,geometry/FPSunchanged:identity+disabledparent0,row2.861e-6FAIL. R2actualactiveencoder canonicalSPordering/restoredids/output:fullsourceall0,642finitegradients,pathinput/outputfinite/nonzero. Default2revisionsconsumed.
- EarlierR28sceneweightedmeanmax9.536743e-7PASS preserved. FINALCOMMITTEDretest:1/32expression(pair1expr0,scene0002firstexpression)weightedfine-mean1.0270338783868738e-6>frozen1e-6FAIL;identity0,strictconjugacy2.384e-7. Overallscientific_admissionFALSE,stageblocked/numerical_control_failure/failure_scopeimplementation. Completedrevision2oldPASSimmutable;current_retestFAILoverridesadmissionreadiness.
- Samefixed8TRAINscenes/32expr32580supportpairs,550FGpairs repeatedlyused,notnewindependentcohorts. ContentFGworsevsR2no-transport7/8scenes,bettervsstrictmismatch6/8. Pathsactive,taskbenefit/noveltyUNKNOWN. No tinycohortgainthreshold,tuningorbenefitclaim.
- R2matcheddiagnosticdisablesinternal_sibling_fine,andapplieseachPRE-transportexternalarmexactlyonce. Canonicalfeatures/mask/pos/ids[0]aligned;GTusesrestoredoriginalIDs/masks. Queryfrommatchedno-transportnative,notexacthistoricalM95-sourcecounterpart. Independentreadonlyauditconfirmedalignment/source.
- Onefixednumericdecompositioncompleted2048groups/32calls: freshmax9.536743e-7,atthesamepeakcoordinateP32stationarityapplication−1.261365e-7+FP32matmulrounding−8.275378e-7,reconstruction0. FP64readoutonly,notnewoperatorprecision. FreshcaptureNOToriginalFAILP/T/output,neverclearsheldfailure. Per-groupmax/componentonlystored;fullperchannel/P/Tprimearraysnotarchived.
- Remote detachedfixture8.55MB livesapprovedstage sibling_99819673_numeric_decomposition2/numeric_fixture.pt,sha9c9ff0259a03fba8981ef2369b48b38ed62a682f78f7f57454bc084ccccbc53c,noGT;no localnativeGPU/dataexecution.

## Closed Or Failed Directions
- PreserveallPCE R1/R2/R3failures andscope. Real21:41PCEone-extrarevisiongrantalreadyconsumed;noautomaticR4. PCElastfullsource2.861e-6>1e-6,notmechanismfalsification. OldHDS/FLE/CPA/M201notreopened/restarted.
- Previous e7cf135a coarse-specificcontamination/exactconstant-only/finalILAsource-invariance explanationsrejectedonlyinscope. No unchangedreplay,newrouting/biascenteringordelete-layercandidate.
- RSTRM39-C2Cdenseprojectedallscaleattentionisclosesthistory,butnewfixedsiblings/pointmassreversibility/no projections arewhole-mechanism differences;notnovelprimitive(MH/Sinkformersknown). No newgate/residual/QKV/N²/tuning/repeatedinjection.
- Harness0invalidparentCSORTsuperbindingfixedwithverifiedCTFfeaturebody;h1spconvimporterror0forwardthenCPUrecheck+freshnativepassed;partialtracebool-outputerrorpreserved. Firstdecompositionstagingcorrectlyrefused1500sminimum;missing-stageattemptresult{{}}unrun;bounded2controlleractual4forwardcompleted. No failedrunrewrittenPASS.

## Running And Queue
- Preflightactive0/target3,waiting0,issuesempty;endnoqueueaddition/newexperimentID/training. Pending8/8,allblocked:old4human/scope+old3numeric+RSTRnumeric. NewIDcapreal;everyexistingIDcurrentlyhasnoauthorizedexecutableactionafterRSTRdiagnostic. No GPUshortage/exhaustionclaim.
- Latest2026-10-21T00:27:03Shanghai server4dl04-MS-7E06 GPU0UUID958e741a contextsabsent andtraining/diagnostic/exclusiveflocksavailable. Historicalobservationnotfutureidleness. AllGPUusesstrictpinnedknownhost+freshlease;server4GPU1/server3GPU1grantsretained,server3GPU0/server6newdispatchnotallowed. No passwords/sudo/reset/foreignjobchanges.

## Open Questions And Risks
- RSTRcurrentnumericalholdrequiresnewauditableevidenceandanyrequiredspecificextra-revisionauthorization beforechangedR3;timer/freeGPU/newlowdriftcaptureisnotunblock. Do not repeatlocalcommitpermissionquestion—itwasansweredandcommitcompleted.
- Scopeofexact0isfixedmembershippooling+activeencoder,notupstreambackbone/FPSrelabeling. ValidSPprefix/uniquegeometryassumptions;floatingweightedmeancloseboundary;smallnonrandomcohort;FGadversepattern. Efficacy/generalization/noisefloor/fulloptimizerpeak/overallnoveltyunknown.
- External_resource_blockeddesign_cycleislegacyoperationalcapacity/scopeholdlabel;RSTRitselfresearchnumericalhold,notmissingGPUpermission. PendingcapaloneonlyforbidsnewunfinishedIDs,notavailableexistingactions. No fakeindependent2route/globalexhaustion/deadlinestop.

## Last Tick
- Bundlepipeline/diagnostic_bundles/tick_99819673;currentdesignexp_design_20261021-0028_rstr_committed_hold.md;committed_gate_review.json/source_binding/local_commit_result/decisions retainallactualscope/evidence. Sixsectionreportnoteswillbewrittenbeforefinish. No sourcechangebeyondauthorized9files;otherdirtybcca/pce/validate_pdc preserved.
- RetryRSTRnumericalevidencein4hunlessrealnewscope/evidencewakesearlier. Monitorstillrunsnormally;no scheduler/cooldown-policychange. Currentfinishnotyetclaimed; requireactualpostflightPASS,FINALIZEDreceiptandabsentownedlease. No projectwritesafterrelease.
'''
    assert len(memory.splitlines())<120
    c.tick.save(ROOT/'pipeline/codex_memory.md',memory) if False else (ROOT/'pipeline/codex_memory.md').write_text(memory,encoding='utf-8')
    c.save('report_notes.json',{'actions':[
        '按用户继续设计试验指令登记1个RSTR稳定候选，冻结8TRAIN场景/32表达及无传输、内容传输、严格等质量错配对照；真实inst_feats和mask路径有响应，全部任务方向留档。',
        '完成独立8源文件+1配置、推导与原文/历史审查、实际native loss反向及同口径资源；两次有界局部修订后完整pooling+active encoder控制最大0，642梯度有限且传输路径非零。',
        f'用户明确授权9文件本地提交，完成{commit[:8]}；Git仅规整行尾，归档旧字节/AST等价并对精确提交字节重新原生验证。无推送/生产部署/入队/训练。',
        '最终提交字节复测1/32表达的融合前加权均值误差1.027033878e-6>冻结1e-6，当前实现数值hold。早先通过值和全部R0/R1/R2失败保留，未用有利复测清除失败。',
        f'最终已提交源同口径9.76313454G、推理峰值与M95相同、median{resources["median_ms"]:.3f}vs{parent["median_ms"]:.3f}ms(+{(resources["median_ms"]/parent["median_ms"]-1)*100:.2f}%)；FG较无传输7/8场景变差，较严格错配6/8更好，不宣布收益。',
        '定点数值分解完成，fresh捕获最差漂移9.5367e-7，同坐标矩阵平稳性应用和FP32乘法舍入可相加重构；不是原失败张量，归档范围限组级最大值，不能据此解除hold。末次GPU0无context且三类flock可用。'],
        'decisions':[
        'RSTR归类为numerical_control_failure/implementation，未否定核心假设；默认两次实现修订已用完，不自动R3，不改阈值/精度/FPS/seed/schedule，不签发准入或训练。',
        '研究pending8/8且每个现有ID当前均scope/numeric hold；本轮用容量/授权holds操作性收尾，RSTR不是GPU许可问题，不称GPU忙、两独立路线或全局穷尽。',
        '下一步仅在真实新证据及合法修订范围到位后续做同ID，或合法待处理容量打开后开展独立诊断；保留已完成的具体本地提交授权，不重复索要。']})
    print(json.dumps({'current_design':str(design),'decision':str(decision),'candidate_stage':'blocked','pending':8,'commit':commit,'postflight':'NOT_YET_RUN'},ensure_ascii=False))


if __name__=='__main__':main()
