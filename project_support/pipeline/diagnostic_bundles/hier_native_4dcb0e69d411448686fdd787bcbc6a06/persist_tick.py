"""Bind actual results to the same primary ID without promoting admission."""
from datetime import datetime, timezone
from pathlib import Path
import json
from run import BUNDLE, ROOT, TOKEN, GOAL_SHA, guard, tick

owner=guard()
now=datetime.now(timezone.utc)
remaining=(datetime.fromisoformat(owner['deadline_at'])-now).total_seconds()
def ref(path):
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
work=tick.load(ROOT/'pipeline/research_work.json')
before=tick.load(BUNDLE/'work_before.json')
primary='m95-hierarchical-mask-feature-path-audit'
other=lambda value:[c for c in value['candidates'] if c['id']!=primary]
assert other(work)==other(before) and len(work['candidates'])==100
candidate=next(c for c in work['candidates'] if c['id']==primary)
assert len(candidate['revision_history'])==1
assert candidate['revision_history'][0]['result']=='pending'
tests=tick.load(BUNDLE/'canonical_tests_result.json')
assert tests['check_count']==tests['passed']==91 and not tests['failures']
baseline=tick.load(BUNDLE/'memory_baseline_result.json')
canonical=tick.load(BUNDLE/'memory_canonical_result.json')
for result in (baseline,canonical):
    assert not result['outcome']['full_forward_completed']
    assert not result['outcome']['full_backward_completed']
    assert result['allocator_fraction']==.25 and result['optimizer_steps']==0
independent=tick.load(BUNDLE/'independent_adapter_result.json')
assert independent['static_checks_passed'] and independent['adapter']['cpu_smoke_passed']
release=tick.load(BUNDLE/'release_verification.json')
assert release['returncode']==0 and release['result']['flocks_acquired_released']==3
artifacts=[p for p in sorted(BUNDLE.iterdir()) if p.is_file() and p.suffix in ('.json','.md','.py')
    and p.name not in ('work_before.json','memory_before.md','notes.json','tick_result_summary.json')]
evidence=[ref(p) for p in artifacts]
candidate['evidence'].extend(item for item in evidence if item not in candidate['evidence'])
candidate['stage']='validation'
candidate['failure_scope']='inconclusive'
candidate['next_action']='On server3 physical GPU1 only, preregister matched module-boundary allocation traces for baseline and canonical with unchanged .25 cap and the same first-pair TRAIN data. Localize their common pre-forward OOM before a bounded evidence-backed memory revision. Then validate the independent package native full forward/backward, full frozen cohort controls and matched whole-model resources. Never infer physical24GB insufficiency or foreign occupation; no optimizer/admission before all gates.'
revision=candidate['revision_history'][0]
revision['result']='passed'
revision['result_scope']='Only preregistered canonical-axis numerical correctness:91/91 under unchanged tolerances on original fixtures and16native inputs. Not whole-model backward, native independent package, resources, trained efficacy, or admission.'
revision['evidence'].extend([ref(BUNDLE/'canonical_tests_result.json'),ref(BUNDLE/'independent_adapter_result.json')])
statuses={
 'diagnosis':'Matched frozen-prefix interventions change native final masks/loss; repeats and native/M95 identity exact0. This establishes point-path task influence, not a causal deficit or trained benefit.',
 'controls':'Revision1 canonical-axis correctness91/91 including16native expressions; original12prototype and4compacted-native strictFAILs retained. Full independent native task controls still pending.',
 'native_backward':'One frozen-prefix SUFFIX backward passed with24existing tensors; independent full-model backward remains unverified. Canonical suffix attempt lacks a terminal result; both matched fresh-process runs OOM before full forward at unchanged25%cap.',
 'resources':'Both unchanged baseline and canonical hit25%allocator cap on matched TRAIN pair0/60; no physical24GB insufficiency or foreign-block conclusion. Full paired FLOPs/latency/memory remain pending. GPU1 contexts empty and3flocks released afterward.',
 'independence':'New physical8file package and byte-identical YAML exist; static/constructed CPU adapter smoke passed. No commit, native independent validation, admission receipt, safe sync or deployment yet.',
 'constraints':'Newest explicit future server3 physicalGPU1-only allocation appended as constraint22; all prior constraints and11bans preserved. No training admission requested.'}
for name,status in statuses.items():
    candidate['gates'][name]={'passed':False,'status':status}
candidate['findings']['native_same_prefix_suffix']=ref(BUNDLE/'native_suffix_probe_result.json')
candidate['findings']['canonical_revision1_correctness']=ref(BUNDLE/'canonical_tests_result.json')
candidate['findings']['matched_memory_baseline']=ref(BUNDLE/'memory_baseline_result.json')
candidate['findings']['matched_memory_canonical']=ref(BUNDLE/'memory_canonical_result.json')
candidate['findings']['independent_static_cpu_adapter']=ref(BUNDLE/'independent_adapter_result.json')
candidate['findings']['latest_resource_guard']={'observed_at':release['result']['observed_at'],
    'evidence':ref(BUNDLE/'release_verification.json'),'server':'server-3','physical_gpu':1,
    'ready_for_reference_capture':True,'ready_for_new_core_training':False,
    'scope':'Fresh empty NVML contexts and3flocks released; not whole-model resource admission.'}
candidate['findings']['training_started']=False
candidate['proposed_mechanism']['standalone_native_model_config']=True
candidate['proposed_mechanism']['status']='independent_draft_numerical_controls_passed_not_admitted'
if remaining<=180:
    work['design_cycle']={'stop_reason':'tick_deadline_near','attempted_ids':[primary],
        'evidence':[ref(BUNDLE/'canonical_tests_result.json'),ref(BUNDLE/'memory_baseline_result.json'),
            ref(BUNDLE/'memory_canonical_result.json'),ref(BUNDLE/'independent_adapter_result.json')],
        'resume_condition':candidate['next_action'],'recorded_at':now.isoformat()}
assert other(work)==other(before)
tick.save(ROOT/'pipeline/research_work.json',work)
summary={'token':TOKEN,'recorded_at':now.isoformat(),'snapshot_at':'2026-10-16T00:42:18.186501+00:00',
    'deadline_at':owner['deadline_at'],'seconds_remaining_at_persist':remaining,
    'candidate_id':primary,'stage':'validation','revision1_result':'passed_correctness_only',
    'gates_passed':0,'other99unchanged':True,'new_candidates':0,'new_admissions':0,
    'new_training':0,'optimizer_steps':0,'goal_sha256':GOAL_SHA,
    'servers_sha256':tick.digest(ROOT/'SERVERS.yaml'),'resource_confirmation':ref(BUNDLE/'resource_confirmation_record.json'),
    'evidence':evidence,'independent_source_files':independent['files'],
    'baseline_outcome':baseline['outcome'],'canonical_outcome':canonical['outcome'],
    'release_verification':ref(BUNDLE/'release_verification.json'),
    'scientific_status':'validation, not admitted; no trained gain; full native/resources pending',
    'execution_status':'POSTFLIGHT_PENDING'}
tick.save(BUNDLE/'tick_result_summary.json',summary)
memory='''# Codex Research Memory
## Goal And Phase
- USER20261015 primary: hierarchical attention/information exchange that updates point/superpoint inst_feats for query-mask prediction. Memory is one reference, not the only objective. Phase1 no-tuning, target.5100 and11bans unchanged.
- USER20261016 permanent allocation: ALL future cluster_project training/GPU diagnostics use server-3 physicalGPU1 only, one slot; even if server4 later frees. server4/server6 new dispatch disabled; preserve existing jobs/locks; no scheduler change.
- Verified hostname sysu311-MS-7C59, currentIP192.168.1.120, GPU UUID340de111-e7e4-ed2d-15c9-8ab6a253e4a0. OldIP192.168.1.194 is historical. Goal22constraints, SHA3b96e04fae2945649ce42ce65674ff5dbf6c7ce24e19123093ecdebc71d4c102.
- Full prior memory/work retained in this tick bundle memory_before.md/work_before.json. Owner01a04987-fdbe-7301-b2f0-f9b6ab60f74c; foreground only.
## Champion And Baseline
- Historical M95-CTF-HCG-CSORT.5020, baseline.4894, target.5100/gap.0080. No new trained metric or efficacy.
- Frozen reference weights fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e and checkoutf8457d3b657e66306a7fce1afb3d81d8ab874669 unchanged.
## Active Hypotheses
- SAME m95-hierarchical-mask-feature-path-audit now validation; four auxiliary supervision records stay scope-held, all other99records unchanged. All six NEW-core admission booleans remain false.
- Frozen native capture e4a7e63605bb60d9e9a543cd22ac2635a37627ee3db22d870122e1a254342e08: TRAINgroups0,60,101,124/4scenes/16unique expressions/2repeats. No new cohort or VAL selection.
- Native support coverage/excluded/included controls16/16; compacted operator4/16strictfloat32FAILs retained. Whole-model12forward intervention trial showed sampling uncertainty; not assigned a unique cause.
- Frozen SAME-prefix native suffix:2captures/12suffix forwards; all repeat and native/M95 identity masks/loss exact0. Uniform/content interventions change masks/loss;1SUFFIX-only backward has24finite/nonzero existing tensors. Not full-model admission or task improvement.
- Revision1 preregistered under SAME ID: retain canonical bounded bank axis and static disjoint support masks; original dtype8heads/thresholds/weights/seed unchanged.91/91correctness checks pass on original fixtures and16native inputs; equivalence output/fixed-query/input-gradient errors0. Revision result passed FOR CORRECTNESS ONLY.
- Independent draft model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1 has8physicalPythonfiles and byte-identical parent YAML. Only point readout changed; CTF/CSORT/loss/gate/projection unchanged. Static/constructed CPU adapter forward/grad/padding smoke passed; not native full-model independence admission.
- Mainline mechanism remains per-level disjoint context support into point features, then query-mask readout. Novelty/causal performance deficit/trained benefit remain unproved; no claims of grouped/chunk/checkpoint memory savings for canonical realization.
## Closed Or Failed Directions
- Preserve prior91rejected/4complete and four auxiliary scope holds with their original historical gate sets, including BPS sixpasses; no M201 recovery.
- Preserve original12strictfloat32 prototype FAILs,4native compacted FAILs, cross-shape numerical negatives and prior environment/analyzer failures. Revision correctness does not reclassify them.
- Canonical suffix full-backward attempt had6logged suffix forwards then NVML-own budget guard failure, no terminal result. Do not certify its full backward from partial logs.
- Fresh matched baseline/canonical first-pair TRAIN processes BOTH OOM before full forward under unchanged.25allocator cap; baseline5.71GiB/canonical5.76GiB allocated with~16.6GiB physically free. Both resource tests failed; not external occupation, physical24GB insufficiency or hypothesis rejection.
- Banned gate/routing/residual/repeated-injection routes remain closed; no tuning or renamed supervision variants.
## Running And Queue
- Immutable preflight2026-10-16T00:42:18.186501Z/mode design:running0/claiming0/waiting0/capacity1/budget1/reservebudget0. OldIP made GPU unknown then; later repair/diagnostics do not alter sections0-3.
- Existing isolated server3 checkout /sdc1/songcl/Project/Cluster_project/Cluster_hier_feature_abdff23d; Python3.8.13/torch1.12+cu113/3d-stmn unchanged. Native capture remains in pipeline/server3_fallback_abdff23d.
- Release verification2026-10-16T01:36:37.166224Z:GPU1 total24268/free24267MiB/util0/no compute contexts; all3mappedflocks acquired and released. No GPU0 use or foreign job operations.
- New candidates0/admissions0/training0/optimizersteps0. Independent draft not committed/synced/deployed or queued.
## Open Questions And Risks
- Next server3GPU1-only test: preregister matched module-boundary allocation traces with SAME25%cap/TRAINpair0,60; localize shared baseline/candidate forward OOM before any evidence-backed memory revision. Never loosen budget or infer foreign block to obtain PASS.
- Then complete independent full-model native forward/backward and full-cohort task controls, paired FLOPs<=10G/latency/relative memory and all scientific gates before admission/safe sync/training.
- Actual GPU idleness and exclusive leases must be reverified before every GPU use; no resets/eviction/stale-lock deletion/otherGPU use. Do not conflate suffix gradients with full-model feasibility or efficacy.
- User-dirty scripts/validate_pdc_20261009.py SHA00d58e60d96a61272d4c8719fbca85fab449252ea84311ee3af09be015b26c26 unchanged; unrelated BCCA directories untouched.
## Last Tick
- Token4dcb0e69d411448686fdd787bcbc6a06; snapshot2026-10-16T00:42:18.186501Z/deadline2026-10-16T01:42:18.186501Z unchanged. Resume same lease, never reacquire/repeat preflight.
- Bundle pipeline/diagnostic_bundles/hier_native_4dcb0e69d411448686fdd787bcbc6a06/tick_result_summary.json hashes actual evidence, resource confirmation, independent files, both failed memory tests and release verification.
- Report uses immutable preflight facts plus Chinese actions/decisions. Finish/abort and actual receipt/absent lease govern execution status; local usage is partial begin-to-receipt window, cached input included, not billing.
'''
assert len(memory.splitlines())<120
(ROOT/'pipeline/codex_memory.md').write_text(memory,encoding='utf-8')
notes={'actions':[
    '已实际使用server3物理GPU1。用户最新确认已追加为目标约束22：今后训练与GPU诊断始终仅用该卡，server4恢复空闲也不切回；单槽，server4/server6禁止新派发。核验主机sysu311-MS-7C59及UUID；地址从失效旧IP修正为192.168.1.120，未重复preflight。',
    '快照为2026-10-16 08:42:18北京时间；第0-3段是修复地址之前的不可变事实，GPU不可达/未知不是当前仍不可达。09:36:37实查GPU1总24268MiB/空闲24267MiB/利用率0%，无计算进程，三个资源锁全部可取得且已释放。',
    '沿用唯一主线候选m95-hierarchical-mask-feature-path-audit；完成原生支持控制、整网干预及冻结同前缀后缀测试。后缀重复与原生M95身份对照差值0；干预改变最终mask与原生loss。一次后缀反向24个既有张量梯度有限且非零，不算完整模型反向或训练收益。',
    '预注册修订1保留完整有界bank轴；原始夹具与16条原生输入共91/91数值控制通过，原float32/float64容差不变；原12条与新增4条压缩实现失败保留。独立8文件模型/原样YAML及CPU接口测试通过，但未提交、部署、入队或获准训练。',
    '基线与候选两次新进程配对显存测试都在完整前向前触发原25%分配额度，整网反向均未完成；不是他人占卡，不证明物理24GB不足，也不支持节省显存或机制被证伪。先前修订后缀尝试无终态收据，保留失败且不认证整网反向。',
    '科学状态validation，六项新候选准入均未通过；本轮新候选0/新准入0/训练0/优化器步0。其余99条记录逐条不变，四条旧监督路线继续范围冻结。执行状态POSTFLIGHT_PENDING，以随后finish/abort与锁核验结果为准；用量收据待正式收尾读取，缺失记未知，缓存不重复相加、用量不是账单。'],
    'decisions':[
    '永久采用server3物理GPU1，保留其他机器既有任务与证据，不碰其他项目、调度、冻结协议、数据验证边界或失败历史。',
    '修订1只证明算子数值一致性，不提升完整原生/资源/独立性准入。当前不启动正式训练，不用历史champion或局部梯度冒充提升。',
    '下一步预注册同25%额度、同TRAIN首批的模块边界显存追踪，定位基线与候选共同前向峰值；再做独立模型完整前反向、同口径效率与完整机制控制。剩余时间不足安全执行时按真实截止收尾，不捏造外部阻塞或放宽门槛。']}
tick.save(BUNDLE/'notes.json',notes)
print(json.dumps({'token':TOKEN,'primary_stage':candidate['stage'],'revision1':revision['result'],
    'remaining_seconds':remaining,'design_cycle':work.get('design_cycle',{}).get('stop_reason'),
    'evidence_added':len(evidence),'other99unchanged':True,'new_training':0,'memory_lines':len(memory.splitlines())}))
