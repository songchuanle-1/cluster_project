"""Persist one independent primary-feature diagnosis before its test."""
import json
from ops import guard,save,advance,evidence,tick,ROOT,OUT,CID
guard(400)
RID='hierarchical-nonlocal-channel-rank-audit'
comparison=tick.load(OUT/'native_stride_comparison.json')
assert comparison['passed'] and tick.load(OUT/'mask_storage_control.json')['coordinate_canonical_masks_equal']
review=ROOT/'pipeline/reviews/motivation_review_20261018_ed0d2b32_rank.md'
design=ROOT/'pipeline/designs/exp_design_20261018_ed0d2b32_rank.md'
goal=tick.load(ROOT/'pipeline/goal.json')
text='# Motivation Review - cluster_project\n\n## 1. Goal\n```json\n'+json.dumps(goal,ensure_ascii=False,indent=2)+'\n```\nTarget.5100,historicalbest.5020,gap.0080.\n\n'
text+='## 2. Story Status\n| 假设 | 状态 | 证据 | 缺口 |\n|---|---|---|---|\n| 原生数值逐位重复 | 有限反例保留，诊断已收束 | 两轮冻结原生/索引/行序控制 | 具体唯一内核原因未知但非主线前置门槛 |\n| 层级更新有丰富跨区域通道交互 | 条件低秩待测 | 精确CTF/HCG源码 | 实际原生cotangent与子空间关系 |\n\n'
text+='## 3. Experiment Assessment\n| Experiment | mIoU | 与动机的关系 | 对故事线贡献 |\n|---|---|---|---|\n| 缓存M95 | .5020 | 既有对照 | 不等于新注意力成立 |\n| 缓存FLE | .4885315597 | 局部叶内交换的训练负面结果 | 不重启不换名 |\n| 本轮原生重复性 | 未训练 | 严格配对前提 | 保留精确前缀与参数标志 |\n\n'
text+='## 4. Gap Analysis\n原生CTF逐簇FFN、HCG按自身ID回写；其他粗簇的通道仅能通过3尺度权重间接影响此点。条件模块秩上界不等于完整网络瓶颈；需测任务梯度而非据公式宣称收益。\n\n'
text+='## 5. Design Rationale\n本项是独立的消息通信能力诊断，不是gate新变体、层数调参、图重分区或旧FLE重开。先固定24个读出并测原生VJP，之后才能考虑新结构。\n\n## 6. Next Batch\n见exp_design_20261018_ed0d2b32_rank.md；未准入任何训练。\n'
with review.open('x',encoding='utf-8') as f:f.write(text)
text='# Experiment Design - Conditioned Nonlocal Channel Diagnosis\n\n## 1. Motivation\n'+goal['description']+'\n\n'
text+='## 2. Current Best Results\nM95historical.5020,FLEcached.4885315597,target.5100. No newtrainedresult.\n\n## 3. Analysis & Direction\n将有限数值排查收束，回到原生层级点更新的跨区域通道。公式、控制和否定条件见nonlocal_rank_prereg.md。\n\n'
text+='## 4. Experiment Plan\n| ID | Hypothesis | Matched control | Pending actual test |\n|---|---|---|---|\n| hierarchical-nonlocal-channel-rank-audit | 条件模块均值上下文Jacobian秩至多2 | owncoarse活跃/remote精确0,fullshape原生重建1e-6 | 1nativebackward,24tokenVJPs,48CPUJacobians |\n\n'
text+='## 5. GPU Allocation Plan\n仅server4physicalGPU0，原生固定权重/数据/seed1999/batch2，活体检查与三锁；CPU双精度只作远端数学参照。\n\n## 6. Implementation Checklist\n- [x] 先审查再设计并预注册固定读出、完整源码和对照。\n- [ ] 执行原生重建/VJP/CPUJacobian，保留全部失败和未知。\n- [ ] 如需新结构，先做匹配任务干预和独立六门准入。\n未新建训练model/config、未commit/deploy/queue/launch。\n\n'
text+='## 7. Risk Assessment\n2scenes/8expressions不足以推断总体；秩至多2源于既有三尺度门控，不证明主线失败或新颖性。原始论文新颖性核对未进行，不宣称创新。外部encoder/decoder路径及参数可提供其他信息；低投影仅为风险，不是训练收益/伤害。\n\nStatus: DIAGNOSIS ONLY,NOT ADMITTED.\n'
with design.open('x',encoding='utf-8') as f:f.write(text)
advance([OUT/'native_stride_comparison.json',OUT/'mask_storage_control.json'],stage='complete',failure_scope='inconclusive',
    gate_result='Finite reproducibility audit COMPLETE with actualnative descriptor/incidence/maskstorage controls. Currentpair aligned0;earlierdifferences retained;unique kernelcause UNKNOWN,not efficacy.',
    next_action='Use exact savedprefix/nativeparameterflags in downstream causal featuretests;do not reopen this finiteaudit for an optional unique-kernel explanation or loosen controls.')
work=tick.load(ROOT/'pipeline/research_work.json')
assert not any(c['id']==RID for c in work['candidates'])
work['candidates'].append({'id':RID,'stage':'diagnosis','hypothesis_id':'conditioned_cluster_message_nonlocal_rank',
    'hypothesis':'Conditioned on native prefix/assignments, outside-coarsest-cluster feature communication in M95pointmessage has atmost2channel directions;quantify taskgradient reachability,not whole-network harm.',
    'matched_control':'Same original weights/prefix/flags/query;fullshape replay1e-6;native owncoarseVJP versus remote0;float64 meancontext versus owncoarseJacobians,first/middle/lastreadouts fixed.',
    'failure_scope':'inconclusive','gate_result':'NOT_RUN;source-derived conditionalrank prediction only,not taskdeficit or admission.',
    'next_action':'One original nativeM95 loss/backward/capture plus24tokenVJP controls,then48CPUJacobians andnativecotangent projections;no newarchitecture or training.',
    'evidence':[evidence(p) for p in (OUT/'nonlocal_rank_prereg.md',OUT/'information_path_and_mask_contract.json',review,design)]})
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
save('rank_preparation.json',{'candidate_id':RID,'stage':'diagnosis','review':evidence(review),'design':evidence(design),'new_training':0,'scientific_status':'pending actualnative test,not efficacy/novelty'})
print(json.dumps({'created':RID,'previous_finite_audit':'complete','training_admitted':False}))
