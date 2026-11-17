"""Persist real gate progress and the resource/revision-limit hold honestly."""
from datetime import datetime,timezone,timedelta
import json
from run import BUNDLE,ROOT,TOKEN,GOAL_SHA,guard,tick
from independent_native import inspect_source

owner=guard()
inspect_source()
now=datetime.now(timezone.utc)
remaining=(datetime.fromisoformat(owner['deadline_at'])-now).total_seconds()
before=tick.load(BUNDLE/'work_before.json')
work=tick.load(ROOT/'pipeline/research_work.json')
primary='m95-hierarchical-mask-feature-path-audit'
others=lambda value:[c for c in value['candidates'] if c['id']!=primary]
assert others(work)==others(before)
candidate=next(c for c in work['candidates'] if c['id']==primary)
old=next(c for c in before['candidates'] if c['id']==primary)
assert candidate['revision_history'][0]==old['revision_history'][0]
assert len(candidate['revision_history'])==2 and candidate['revision_history'][-1]['result']=='pending'
analysis=tick.load(BUNDLE/'resource_analysis.json')
controls=tick.load(BUNDLE/'revision2_controls_result.json')
mechanism=tick.load(BUNDLE/'mechanism_controls_result.json')
first=tick.load(BUNDLE/'independent_native_result.json')
second=tick.load(BUNDLE/'native_second_independent_result.json')
release=tick.load(BUNDLE/'release_verification.json')
assert controls['passed']==controls['check_count']==20 and not controls['failures']
assert first['outcome']['passed_this_diagnostic'] and second['outcome']['passed_this_diagnostic']
assert not analysis['resource_gate_passed'] and release['returncode']==0
assert all(row['loss_delta']==row['mask_max_delta']==0 for row in mechanism['repeats'])
def ref(path):
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
def here(name):return ref(BUNDLE/name)
decision=ROOT/'pipeline/decisions/20261016-103728_question.md'
assert decision.exists()
files=[path for path in sorted(BUNDLE.iterdir()) if path.is_file() and path.suffix in ('.py','.md','.json')
    and path.name not in ('work_before.json','memory_before.md','goal_snapshot.json','notes.json','tick_result_summary.json')]
evidence=[ref(path) for path in files]+[ref(decision)]
candidate['evidence'].extend(item for item in evidence if item not in candidate['evidence'])
revision=candidate['revision_history'][-1]
revision['result']='passed'
revision['evidence']=[here(name) for name in ('revision2_controls_result.json','revision2_baseline_result.json',
    'revision2_canonical_result.json','independent_native_result.json','native_second_independent_result.json')]
candidate['stage']='blocked'
candidate['failure_scope']='implementation'
candidate['blocker_kind']='human_authorization'
candidate['blocker']='Current independent realization exceeds SAME historical full-model counted FLOPs limit:10.034588748G>10G (M95 baseline9.762532428G). GPU/memory/native backward are available/passed. Effective two-implementation-revision limit is exhausted, so a third resource-only local change needs explicit human authorization. This is NOT foreign GPU occupation, physical24GB insufficiency, mechanism falsification or a request to loosen10G.'
candidate['retry_after']=(now+timedelta(hours=4)).isoformat()
candidate['unblock_condition']='Explicit human authorization for ONE additional preregistered same-ID resource implementation refinement with original10G/strict1e-6/native/resource/validation gates unchanged, or an externally supplied verified compliant implementation. Do not raise goal limits or begin revision3 automatically.'
candidate['next_action']='Preserve the four passed scientific/native/independence gates and both failed strict resource histories. Wait for hash-addressed explicit authorization before any revision3; then investigate reduced masked VALUE aggregation while retaining canonical QK/softmax axes, retest original fixtures/native full backward and SAME full-model counted resources. No admission/queue/training until10G and all gates pass; use server3 physicalGPU1 only.'
candidate['wake_paths']=list(dict.fromkeys(candidate.get('wake_paths',[])+['pipeline/authorizations/hds_resource_revision3.json']))
def gate(passed,status,names):return {'passed':passed,'status':status,'evidence':[here(name) for name in names]}
candidate['gates']={
 'diagnosis':gate(True,'Actual branch-scoped information gap measured on4scenes/16expressions: original ancestor value supports miss mean86.576%valid leaves and multiply cover2.035%; disjoint cut covers exactly once. Not proof that all-model context is absent or redundancy is harmful.', ['mechanism_controls_result.json','resource_analysis.json']),
 'controls':gate(True,'Current independent canonical versus uniform/ancestor native same-prefix controls separate final masks; paired repeats exactly0. Original91operator controls retained and20new native prefix-module output/input/parameter-gradient errors exactly0 at original1e-6. Signed untrained loss risks retained, no trained gain claim.', ['mechanism_controls_result.json','revision2_controls_result.json']),
 'native_backward':gate(True,'Physical independent package actual full native loss and backward complete on BOTH frozen pairs,4scenes/16expressions;24existing point-path tensors finite/nonzero each, core once, zero new trainable tensors/optimizer steps. Earlier suffix-only/failed attempts stay unpromoted.', ['independent_native_result.json','native_second_independent_result.json']),
 'resources':gate(False,'SAME full-model FVCore counted10.034588748G exceeds unchanged10G, baseline9.762532428G; not rounded down.20/100bs1 latency83.1302->83.6800ms, inference peak equal928491008bytes; matched TRAIN peak+4.7966%. Memory/native execution pass but resources overall FAIL.', ['profile_counted_baseline_result.json','profile_counted_independent_result.json','resource_analysis.json']),
 'independence':gate(True,'Nine physical independent Python files, unique byte-identical config, no cross-variant imports; hashed diagnostic-only remote package actually executed full native backward. No code commit/production safe sync/admission/launch occurred.', ['independent_upload.json','independent_native_result.json','native_second_independent_result.json']),
 'constraints':gate(False,'Mainline/data/seed/schedule/precision/batch11bans and permanent server3GPU1 preserved. Current resource10G constraint fails; two local revisions used. No unilateral revision3, target/gate change, old-route recovery or training.', ['resource_analysis.json','revision2_registration.json'])}
candidate['findings'].update(revision2_controls=here('revision2_controls_result.json'),
    revision2_result_scope='PASSED only pure-prefix numerical equivalence and original25%native memory feasibility; current canonical dense arithmetic remains resource-ineligible at10.034588748G.',
    independent_native_first=here('independent_native_result.json'),independent_native_second=here('native_second_independent_result.json'),
    current_mechanism_controls=here('mechanism_controls_result.json'),matched_full_resources=here('resource_analysis.json'),
    training_started=False,latest_release_verification=here('release_verification.json'))
candidate['proposed_mechanism']['status']='independent_native_passed_resource_ineligible_authorization_hold'
old_cycle=work.pop('design_cycle',None)
if remaining<=180:
    work['design_cycle']={'stop_reason':'tick_deadline_near','attempted_ids':[primary],
        'recorded_at':now.isoformat(),'evidence':[here('resource_analysis.json'),here('release_verification.json')],
        'resume_condition':candidate['unblock_condition']}
assert others(work)==others(before)
tick.save(ROOT/'pipeline/research_work.json',work)
summary={'token':TOKEN,'recorded_at':now.isoformat(),'snapshot_at':'2026-10-16T01:43:30.123361+00:00',
    'deadline_at':owner['deadline_at'],'seconds_remaining_at_persist':remaining,'candidate_id':primary,
    'stage':'blocked','blocker_kind':'human_authorization','failure_scope':'implementation',
    'passed_gates':[key for key,value in candidate['gates'].items() if value['passed']],
    'resource_gate_passed':False,'revision2_result':'passed_memory_lifetime_only','other99unchanged':True,
    'new_candidates':0,'new_admissions':0,'new_training':0,'optimizer_steps':0,'evidence':evidence,
    'goal_sha256':GOAL_SHA,'servers_unchanged':tick.digest(ROOT/'SERVERS.yaml')==tick.digest(BUNDLE/'servers_snapshot.yaml'),
    'prior_design_cycle_archived':old_cycle,'execution_status':'POSTFLIGHT_PENDING',
    'scientific_status':'Four gates pass; current implementation resource-ineligible, hypothesis not falsified; further revision needs explicit authorization.'}
tick.save(BUNDLE/'tick_result_summary.json',summary)
memory='''# Codex Research Memory
## Goal And Phase
- USER20261015 primary: hierarchical interaction updates point/superpoint inst_feats for query-mask prediction. Memory is one reference, not the contribution or sole objective. Phase1 no-tuning,target.5100,11bans unchanged.
- ALL future training/GPU diagnostics: server-3 physicalGPU1 only, one slot, even if server4 frees. Hostsysu311-MS-7C59/currentIP192.168.1.120/UUID340de111-e7e4-ed2d-15c9-8ab6a253e4a0. server4/server6 new dispatch disabled; no scheduler change.
- Goal22constraints SHA3b96e04fae2945649ce42ce65674ff5dbf6c7ce24e19123093ecdebc71d4c102 unchanged. Full old memory/work in current memory_trace_cc39552e325049f5b8ac15dd3e055b06 bundle.
## Champion And Baseline
- Historical M95.5020/baseline.4894/target.5100/gap.0080; NO new trained mIoU or efficacy. Same frozen weights fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e.
- Matched resource M95 first VAL expression scene0011_00/ann0:9.762532428G counted FLOPs,157484090params,83.1302ms median,102.4548msP90,928491008byte inference peak.
## Active Hypotheses
- SAME m95-hierarchical-mask-feature-path-audit now blocked/human_authorization/failure_scope implementation. Four gates PASS: diagnosis,controls,native_backward,independence; resources/constraints FAIL at unchanged10G. Other99records and BPS historical6passes unchanged; no M201 recovery.
- Revision1 numerical correctness91/91 preserved; all original12prototype/4native compacted strictFAILs preserved. Revision2 preregistered pure-prefix rematerialization (use_cluster=False first5encoder+paireddecoder, nonreentrant/RNG preserved). Last cluster encoder/final decoder/CSORT untouched; no arithmetic/parameter/config/batch/dtype/cap change.
- Revision2 PASSED its scope:20native module output/input/parameter-gradient comparisons exactly0, originalfloat32<=1e-6; actual full native loss/backward passes for paired baseline/canonical and physical independent package on TRAIN0,60 and101,124/4scenes/16expressions.24existing point-path tensors finite/nonzero per batch; core once; optimizer0.
- Physical independent9Pythonfiles+unique original-byte YAML: model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1. Diagnostic-only hashed copy in /sdc1/songcl/Project/Cluster_project/pipeline/revision2_cc39552e; no commit/production sync/queue/training.
- Current same-prefix canonical/uniform/ancestor controls:2native captures/12suffix forwards; all paired repeats exactly0. Controls change final masks/loss; selectedquery changes0. Ancestor loss deltas vs canonical -.00215745/-5.722e-6; uniform+.00336754/-.00011909. Retain signs as untrained fixed-weight risk, not improvement or trained harm.
- Native branch value support misses mean86.576%valid fine tokens/multiply covers2.035%under old ancestors; disjoint covers once16/16. Denominator branch valid fine tokens, point-weighted per expression; NOT all-model context absence, semantic objects, information redundancy harm or population efficacy.
## Closed Or Failed Directions
- Current independent realization FAILS matched standard counted FLOPs:10.034588748G>10G, excess34588748. No rounding/gate/calculation shortcut. Current realization ineligible; mechanism NOT scientifically rejected.
- Added272056320counted operations=2*N1620*C256*K328. Canonical full-axis arithmetic solved strict controls but computes masked edges. Source-only future idea: retain QK/softmax axes and reduce masked VALUE work; UNTESTED, not a PASS or authorized revision3.
- Both allowed implementation revisions consumed. Do not reset/rename/reclassify history or change goal defaults to authorize a third. Explicit human permission required for one additional bounded resource-only realization under SAME10G/strict controls.
- Preserve prior91rejected/4complete, four auxiliary scope holds, original numerical failures and all old attempts. Original full-forward OOMs at25%cap and unfinalized suffix-backward attempt remain failures, not retroactively promoted.
## Running And Queue
- Immutable preflight2026-10-16T01:43:30.123361Z/design:running0/claiming0/waiting0/capacity1/budget1/reservebudget0. New candidates/admissions/training/optimizersteps all0.
- Matched TRAIN peak allocated baseline4293406720bytes/candidate4499342848bytes(+4.7966%); same25%allocator+NVML guards PASS. Full backprop is feasible for fixed cohort, not a claim about every scene/optimizer/training schedule.
- Inference samebs1/warmup20/repeat100:first VAL expression only, candidate83.6800ms median/99.0421msP90(+.6614%median), same928491008byte peak/157484090params. Unsupported-operator lists retained for BOTH.
- fvcore initially missing; failure retained. Pinned profiler deps installed ONLY under diagnostic/profiler_dependencies, no-deps, torch1.12+cu113/transformers4.31/numpy1.24.4 base unchanged. No new GPU/runtime upgrade.
- Release2026-10-16T02:36:36.031566Z:GPU1 total24268/free24267MiB/util0/no contexts;3flocks acquired/released; no GPU0 or foreign job operations.
## Open Questions And Risks
- Wait for explicit hash-addressed authorization for ONE additional same-ID resource realization or externally supplied compliant code; do not unilaterally change10G/default2revision limit. Candidate wake_path pipeline/authorizations/hds_resource_revision3.json. Retry bounded4hours; timer grants no authorization.
- If authorized: preregister reduced masked VALUE aggregation while canonical QK/softmax remain; original constructed/native1e-6 controls, full native backwards and SAME standard full resources required. No dtype/batch/head/scale/schedule tuning or banned routes.
- Actual effect/novelty/generalization remain unproved. Keep full trained comparison and scene-level subgroup/noise limits in exp_design_20261016_hier_support.md; no VALIDATION mechanism selection or test-set use.
- User-dirty scripts/validate_pdc_20261009.py SHA00d58e60d96a61272d4c8719fbca85fab449252ea84311ee3af09be015b26c26 preserved; unrelated BCCA files untouched. No Git commit or reset.
## Last Tick
- cc39552e325049f5b8ac15dd3e055b06; snapshot01:43:30.123361Z/deadline02:43:30.123361Z unchanged. Bundle tick_result_summary.json binds actual evidence; decision20261016-103728_question.md records authorization question.
- Execution POSTFLIGHT_PENDING; only actual finish/abort output and absent lease determine completion. Do not invent external GPU blocks/elapsed deadline or run busywork to obtain PASS. If honest early authorization hold cannot pass checker, preserve evidence and abort.
- Usage is partial local begin-to-receipt window, cachedinput already in input/reasoning already in output, not billing. No post-release project writes.
'''
assert len(memory.splitlines())<120
(ROOT/'pipeline/codex_memory.md').write_text(memory,encoding='utf-8')
notes={'actions':[
 '本轮快照2026-10-16 09:43:30北京时间，mode=design；只续做同一主线候选，预算1/储备预算0，不重复preflight、不跨项目或改调度。所有GPU诊断都在server3物理GPU1，永久用卡授权不变。',
 '在原25%额度下定位共同前缀保留激活；预注册第二次局部修复，仅重算未启用cluster的前五组编码/解码层，保留RNG，最后cluster/CSORT不重算。20组原生模块对照全部通过，输出/输入梯度/参数梯度最大差均0，原1e-6不变。',
 '独立9文件模型及原样配置完成两批TRAIN完整损失前反向，4场景16表达，每批24个点路径张量梯度有限非零，core仅一次。原生后缀同前缀canonical/均匀/祖先对照重复差0且改变最终mask；固定旧权重下有正有负loss方向，不能当训练收益。',
 '历史统一完整模型口径：M95 FLOPs9.762532428G，候选10.034588748G>10G，超出34588748，资源门槛失败。bs1/warmup20/repeat100中位83.1302→83.6800ms，推理峰值均928491008bytes，参数相同157484090；配对训练峰值+4.7966%。显存与完整反向通过不等于计算量准入。',
 'fvcore缺失首次测量保留为未知；固定版本分析器仅补在项目隔离目录，原torch/transformers/numpy环境未改，两分支使用同分析器和同VAL首表达，仅作资源测量。另保存本地包装器AST匹配故障及GitBash路径故障事实，均未改变模型或准入。',
 '科学状态blocked：诊断/机制控制/原生反向/独立性四项有证据通过；资源与约束未通过。第二次修复只通过其数值/内存生命周期范围，当前实现仍不具训练资格；默认两次修订已用尽，第三次需明确授权，不自行改goal或门槛。其余99记录逐条不变，全部旧FAIL/辅助冻结保留。',
 '10:36:36实查GPU1空闲24267/24268MiB、利用率0%、无计算进程，三个资源锁已释放；新候选0/准入0/训练0/优化器0。执行状态POSTFLIGHT_PENDING，以随后finish/abort和锁核验为准；收据用量待取，缺失为未知，缓存不叠加，用量非账单。'],
 'decisions':[
 '不为只超0.034588748G就放宽或四舍五入10G，不以显存成功代替资源门槛，不将固定权重loss或梯度叫作精度提升。',
 '保留当前层级机制与已通过项，不把实现资源失败记为整个假设证伪。若获明确授权，下一次只针对masked VALUE计算量做有界实现修复，保持canonical QK/softmax和原严格控制；当前不执行第三次修改或增加变体。',
 '不捏造GPU阻塞、路线耗尽、阶段冻结或已到截止。按真实时间/收尾检查处理；验收不能接受诚实的提前授权等待时，保存证据并abort，核实释放。']}
tick.save(BUNDLE/'notes.json',notes)
tick.save(BUNDLE/'local_helper_faults.json',{'token':TOKEN,'recorded_at':now.isoformat(),
    'faults':[{'name':'profile_wrapper_AST_prefix','observed_time':'unknown','stage':'before_GPU_execution','error':'AssertionError because interpolated prefix was BinOp rather than Constant','repair':'Append parsed prefix after initial assignment; frozen protocol unchanged'},
              {'name':'GitBash_path','observed_time':'unknown','stage':'before_log_script_execution','error':'C:/Program Files/Git/bin/bash.exe absent','repair':'Get-Command verified C:/Program Files (x86)/Git/bin/bash.exe; standard log succeeded'}]})
print(json.dumps({'token':TOKEN,'stage':'blocked','passed_gates':summary['passed_gates'],
    'resources_passed':False,'other99unchanged':True,'seconds_remaining':remaining,
    'design_cycle':work.get('design_cycle',{}).get('stop_reason'),'memory_lines':len(memory.splitlines())}))
