"""Bind the conditional design, real tests and resource block to one stable ID."""
from datetime import datetime, timedelta, timezone
import copy
import json
import re
from run_cpu import BUNDLE, ROOT, TOKEN, guard, tick

guard()
PRIMARY = 'm95-hierarchical-mask-feature-path-audit'
result = tick.load(BUNDLE/'result.json')
calibration = tick.load(BUNDLE/'calibration_result.json')
assert result['status']=='FAIL_CONSTRUCTED_OPERATOR_CONTROL'
assert result['check_count']==39 and len(result['failures'])==12
assert all(calibration['checks'].values()) and not calibration['original_strict_control_reclassified']
assert not result['cuda_initialized'] and not calibration['cuda_initialized']
assert result['native_network_forwards']==result['optimizer_steps']==0
resource_bundle = ROOT/'pipeline/diagnostic_bundles'/('resource_recheck_'+TOKEN)
resource = tick.load(resource_bundle/'resource_result.json')
assert resource['token']==TOKEN and not resource['ready_for_original_capture_guards'] and resource['probe_flocks_released']
before = tick.load(BUNDLE/'work_before.json')
work_path = ROOT/'pipeline/research_work.json'
assert tick.load(work_path)==before
work_hash = tick.digest(work_path)
work = copy.deepcopy(before)
candidate = next(c for c in work['candidates'] if c['id']==PRIMARY)
assert candidate['stage']=='blocked' and all(not gate['passed'] for gate in candidate['gates'].values())
review = ROOT/'pipeline/reviews/motivation_review_20261016_hier_support.md'
design = ROOT/'pipeline/designs/exp_design_20261016_hier_support.md'


def ref(path):
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}


sources = {
    'checked_at':datetime.now(timezone.utc).isoformat(),
    'scope':'Primary paper abstracts and version-matched API documentation; not comprehensive novelty proof.',
    'sources':[
        {'title':'Stratified Transformer for 3D Point Cloud Segmentation','arxiv':'2203.14508','url':'https://arxiv.org/abs/2203.14508','official_code':'https://github.com/dvlab-research/Stratified-Transformer','boundary':'Dense-near/sparse-far keys and variable-length memory pre-exist.'},
        {'title':'Point Transformer V2: Grouped Vector Attention and Partition-based Pooling','arxiv':'2210.05666','url':'https://arxiv.org/abs/2210.05666','boundary':'Grouped vector attention and partition-based pooling pre-exist.'},
        {'title':'PyTorch checkpoint documentation','url':'https://docs.pytorch.org/docs/2.8/checkpoint.html','boundary':'Recomputation trades compute for saved activations; exact target runtime2.8.0+cu128 tested separately.'},
        {'title':'PyTorch SDPA documentation','url':'https://docs.pytorch.org/docs/2.8/generated/torch.nn.functional.scaled_dot_product_attention.html','boundary':'SDPA backend and numeric equivalence cannot be presumed; strict float32 FAIL retained.'}]}
tick.save(BUNDLE/'prior_work.json',sources)
files = [review, design] + [BUNDLE/name for name in (
    'goal_snapshot.json','prereg.md','hier_support.py','test_cpu.py','run_cpu.py','frozen_sources.json',
    'attempt.json','result.json','calibration_prereg.md','calibration.py','run_calibration.py',
    'calibration_attempt.json','calibration_result.json','prior_work.json')]
files += [resource_bundle/name for name in ('remote_probe.py','attempt.json','resource_result.json')]
evidence = [ref(path) for path in files]
candidate['evidence'].extend(evidence)
candidate['proposed_mechanism'] = {
    'name':'hierarchical-disjoint-support-point-readout', 'status':'conditional_prototype_not_admitted',
    'design':ref(design),'review':ref(review), 'user_clarification':'Memory is one reference, not the only research axis.',
    'new_stable_candidates':0,'trained_variants':0,'standalone_native_model_config':False,
    'novelty_proven':False,'historical_rejected_ids_reopened':[]}
candidate['findings']['support_prototype'] = {
    'observed_at':result['recorded_at'],'constructed_checks':39,'passed':27,'strict_float32_failed':12,
    'result':ref(BUNDLE/'result.json'),'same_shape_checkpoint_exact':True,
    'calibration':ref(BUNDLE/'calibration_result.json'),
    'scope':'CPU constructed operator and frozen original-module path distinction only; no native task or whole-model memory efficacy.'}
observed = datetime.fromisoformat(resource['observed_at'])
retry = observed + timedelta(hours=1)
candidate['retry_after'] = retry.isoformat()
candidate['blocker'] = ('Fresh2026-10-16T00:30:57+08 pinned server4 GPU0 free1551MiB/util71; '
    'NVML2634704uses20016MiB and4093981uses10436MiB; original training flock held; all original '
    'guardsfalse. Constructed conditional-support prototype executed, but strict float32 readout '
    'equivalence remains inconclusive; original FAIL retained. Native learned-feature capture/controls '
    'and full-model gates not executed. Do not launch on free1551MiB or interpret CPU storage as GPU peak.')
candidate['findings']['latest_resource_guard'] = {
    'observed_at':resource['observed_at'],'evidence':ref(resource_bundle/'resource_result.json'),
    'ready':False,'native_network_forwards_this_tick':0,
    'scope':'Live occupation and original flock evidence; no allocation.'}
candidate['gates']['controls']['status'] = (
    'New conditional-support prototype39controls:27pass/12strictfloat32FAIL retained; float64/reference '
    'and same-shape checkpoint diagnostics not substitute. Prior CPU random-weight FAILs retained; '
    'native learned-feature mechanism controls unrun; no admission.')
candidate['next_action'] = (
    'Do not repeat resource-only ticks as the entire design. Conditional support design and prototype '
    'are saved; maintain original thresholds and user clarification(memory is a constraint/reference). '
    'Under fresh original identity/NVML/30000MiB/three-flock guards capture unchanged M95 TRAIN '
    'groups0,60,101,124. Establish actual learned-feature deficit before selecting this core; execute '
    'same-capture ancestor/uniform/support controls and resolve strict float32 readout uncertainty. '
    'No independent model/config, backward/resource/novelty or training admission currently certified.')
assert all(not gate['passed'] for gate in candidate['gates'].values())
old = {c['id']:c for c in before['candidates']}
assert all(c==old[c['id']] for c in work['candidates'] if c['id']!=PRIMARY)
work['design_cycle'] = {
    'stop_reason':'external_resource_blocked','attempted_ids':[PRIMARY], 'evidence':evidence,
    'resume_condition':candidate['unblock_condition'],'retry_after':retry.isoformat(),
    'scope':'Manual mechanism design and two substantive CPU tests completed under same diagnostic ID, '
            'not a new reserve/queue candidate. Native learned-feature diagnosis and full integration '
            'still require occupied GPU and original guards. Prototype strict float32 FAIL remains; '
            'not route exhaustion, trained gain, guard relaxation or novelty PASS.'}
memory_path = ROOT/'pipeline/codex_memory.md'
memory = memory_path.read_text(encoding='utf-8')
assert memory == (BUNDLE/'memory_before.md').read_text(encoding='utf-8')
memory = re.sub(r'(?m)^- Current(?=[0-9a-f]{32} )','- Prior',memory)
memory = memory.replace('## Active Hypotheses\n','## Active Hypotheses\n- USER20261016 clarification: VRAM is a reference/constraint, NOT the sole direction. Same primary ID now has conditional disjoint-support point-readout design/prototype; fine own-middle / middle other-same-coarse / coarse outside-coarse supports cover leaves once. Not M39 token-self-attention or query-topk routing; full historical-family/novelty audit still incomplete.\n- New prototype39constructed CPU controls:27pass/12float32 strict1e-6FAIL; original results retained. Same-shape repeat/checkpoint outputs+gradients+fixedQ exact0, independentfloat64 controls pass, but none reclassifies strictFAIL. Native feature/task/whole-model memory benefits unknown.\n',1)
lines = memory.splitlines()
for index,line in enumerate(lines):
    if line.startswith('- Current preflight'):
        lines[index]='- Current preflight2026-10-15T16:28:02.884904Z: manual design/running0/claiming0/waiting0/capacity1/budget1; reserve5/target2/budget0. One conditional prototype under SAME ID,0newcandidate/admission/training.'
    elif line.startswith('- Fresh pinned server4 resource'):
        lines[index]='- Fresh pinned server4 resource2026-10-16T00:30:57.912471+08:00: total32607/used30551/free1551MiB/util71; NVML2634704uses20016MiB,4093981uses10436MiB; trainingflock held, diagnosticflocks acquired/released. Originalguardsfalse; CPU tests only.'
    elif line.startswith('- Primary retry'):
        lines[index]='- Primary retry2026-10-16T01:30:57.912471+08:00 or resource/goal/authorization evidence change; four auxiliary holds and retries unchanged. Timers grant no GPU/science permission. Save design work rather than another resource-only review; next substantive test native feature capture.'
memory='\n'.join(lines)+'\n'
memory=memory.replace('## Last Tick\n','## Last Tick\n- Current'+TOKEN+' snapshot16:28:02.884904Z/deadline17:28:02.884904Z unchanged. Manual request and clarification honored: 6-section review/7-section design, isolated prototype39controls and calibration executed on server4CPU; strict12FAIL retained, priorFAILs preserved.0newstablecandidate/admission/nativeforward/training/optimizer; other99records and4auxholds unchanged. Actual finish pending.\n',1)
assert memory.count('## ')==7 and len(memory.splitlines())<120
notes={'actions':[
    '本次手动设计快照2026-10-15T16:28:02.884904Z（北京时间2026-10-16 00:28:02），design；用户随后明确显存只是参考，不是唯一思路。主线保持分层信息交互真实更新inst_feats；目标20约束/11禁令、seed/schedule/数据/损失、唯一server4GPU0及后台Disabled均未改。',
    '完成六段动机审查和七段具体设计：自身中簇内fine、同coarse下其他middle、其余coarse三组互斥支持，点特征分别做attention后接原写回。保留原FFN/scale/loss/注入路径，不新增大QKV、query路由、gate或residual机制。与M39/TrueRoute有源码路径区别；文献初核已知层级/近密远疏并非新颖，独立新颖性未证。',
    '在server4CPU完成两棵固定构造树39项控制：27通过，12项float32严格控制FAIL保留（固定query读出约3.81e-6/6.20e-6，超过1e-6）。覆盖、支持内/排除路径、padding/空树等通过不代替严格失败；没有原生TRAIN特征、完整backward或新指标。',
    '追加冻结数值定位：原样重复及同形状checkpoint前后向/query差0；double条件读出仍约2.21e-6/4.22e-6，未声称唯一原因已解决。原M95训练权重模块的自身coarse干预路径与原型排除路径不同；这只是同构造输入下的路径区别，不是任务收益。',
    'CPU保存storage对照1553845 vs1075940字节，仅相对本算子稠密参考，不能称为GPU峰值或优于M95。原始资源00:30:57+08:free1551MiB/util71，两个NVML上下文和训练锁仍在，三项原守卫均false；未GPU分配/干预进程/reset/删锁。',
    '同一候选新增条件式原型/设计证据，科学状态blocked/inconclusive、六项准入仍false；其余99记录及4辅助范围暂停保持。新增稳定候选/准入/原生网络forward/训练/优化器步数均0。执行状态待finish核验；收据仅begin到receipt本地部分窗口，缓存包含于input/推理包含于output，不重复相加、不作账单。'
], 'decisions':[
    '继续研究任务特征分工，显存仅与延迟/FLOPs共同构成约束；不再把所有设计工作停在显存轮询。候选图已具体化并测试，但不以构造通过项、CPU storage或通用分层概念声称新颖/有效。',
    '按真实external_resource_blocked保留原生缺口；严格控制FAIL不抹除、不改容差或精度凑PASS，不重开旧失败/恢复M201。下一实质测试为原M95固定TRAIN捕获和条件诊断，原资源/锁全部通过后才能执行；新模型完整准入仍未完成。候选资源fallback为2026-10-16T01:30:57.912471+08:00，准确自动化触发时间未知。'
]}
guard()
assert tick.digest(work_path)==work_hash
tick.save(work_path,work)
memory_path.write_text(memory,encoding='utf-8')
tick.save(BUNDLE/'notes.json',notes)
tick.save(BUNDLE/'persistence.json',{'token':TOKEN,'changed_candidate_ids':[PRIMARY],
    'other99_unchanged':True,'new_candidates':0,'prototype_operators':1,'controls_passed':27,'strict_controls_failed':12,
    'original_gate_pass_booleans_unchanged':True,'new_training':0,'memory_lines':len(memory.splitlines()),
    'evidence_references_added':len(evidence)})
print(json.dumps({'candidate':PRIMARY,'new_candidates':0,'prototype_operators':1,
    'constructed_controls_passed':27,'constructed_strict_failed':12,'six_gates_passed':0,
    'other99_unchanged':True,'evidence_added':len(evidence),'memory_lines':len(memory.splitlines())},indent=2))
