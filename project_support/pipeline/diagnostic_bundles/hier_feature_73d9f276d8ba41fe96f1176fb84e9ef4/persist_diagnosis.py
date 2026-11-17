"""Persist actual diagnostic evidence and the authorized auxiliary scope hold."""
import copy
import csv
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path
from audit_feature_path import BUNDLE,ROOT,TOKEN,GOAL_SHA,guard,tick

PRIMARY='m95-hierarchical-mask-feature-path-audit'
OLD=('m95-native-relation-other-sign-conflict','m95-native-main-role-weight-precedence','m95-native-secondary-positive-mass','m95-native-between-pair-support')
guard()
source=tick.load(BUNDLE/'source_audit_same_shape.json')
controls=tick.load(BUNDLE/'cpu_controls_same_shape.json')
native=tick.load(BUNDLE/'native_input_incidence.json')
prep=tick.load(BUNDLE/'native_preparation.json')
assert len(source['tests'])==12 and all(source['tests'].values())
assert controls['overall_control_status']=='FAILED_STRICT_CROSS_SHAPE_CONTROL_RETAINED'
assert not controls['checks']['masked_mean_control_padding_invariant']
assert all(controls['same_shape_checks'].values()) and not controls['cuda_initialized']
assert native['group_count']==4 and native['expression_count']==16 and native['repeat_exact']
assert native['checkpoint']['matches_expected_frozen'] and native['network_forwards']==0
assert prep['strict_state_load'] and not prep['cuda_initialized'] and prep['native_network_forwards']==0
resource=controls['resource']
gpu=next(csv.reader([resource['gpu']],skipinitialspace=True))
assert gpu[1]=='GPU-7f82edb9-f620-8045-caea-a75232265cd1'
assert int(gpu[4])<30000 and resource['compute'] and resource['locks']['/tmp/cluster_project_gpu0_m201_migration.lock']=='held'
now=datetime.now(timezone.utc)
assert (now-datetime.fromisoformat(resource['observed_at'])).total_seconds()<3600
work_path=ROOT/'pipeline/research_work.json'
work=tick.load(work_path)
original_hash=tick.digest(work_path)
memory_path=ROOT/'pipeline/codex_memory.md'
old_memory=memory_path.read_bytes()
for name,data in [('goal_snapshot.json',(ROOT/'pipeline/goal.json').read_bytes()),('memory_before.md',old_memory),('work_before_scope_hold.json',work_path.read_bytes())]:
    path=BUNDLE/name
    assert not path.exists()
    path.write_bytes(data)
def ref(path):return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
snapshot=ref(BUNDLE/'goal_snapshot.json')
assert snapshot['sha256']==GOAL_SHA
review=ROOT/'pipeline/reviews/motivation_review_hier_feature_20261015_73d9.md'
evidence=[ref(BUNDLE/name) for name in ('audit_feature_path.py','audit_feature_path_v2.py','source_audit_same_shape.json','cpu_attempt.json','cpu_attempt_v2.json','cpu_control_revision_v2.md','same_shape_prereg.md','cpu_controls_same_shape.json','probe_native_assets.py','native_asset_probe.json','native_input_incidence.py','native_input_incidence.json','prepare_native.py','native_preparation.json','native_capture_prereg.md','native_feature_capture.py')]+[ref(review),snapshot]
primary=next(c for c in work['candidates'] if c['id']==PRIMARY)
assert primary['stage']=='diagnosis'
primary['evidence']=[e for e in primary['evidence'] if e['path']!='pipeline/goal.json']+evidence
primary.update(stage='blocked',failure_scope='inconclusive',blocker_kind='gpu_context_or_lock_not_released',
    blocker='Actual '+resource['observed_at']+': GPU0 free11994MiB, NVML2634704 uses20016MiB, original training flock held. Native inputs and exact CPU checkpoint/model load prepared; no authorized exclusive GPU capture can run. Synthetic CPU controls do not establish native task harm.',
    retry_after=(now+timedelta(hours=1)).isoformat(),
    unblock_condition='Fresh pinned server-4 GPU0 has no other NVML context and >=30000MiB idle-equivalent memory; all original training/diagnostic flocks acquired; exact M95 checkpoint/source/config and fixed groups reverified under new current foreground lease.',
    next_action='Under a new verified foreground lease, run prepared native_feature_capture.py only after fresh original resource/flock guards. Capture unchanged M95 checkpoint fe5e4a5f... on fixed TRAIN groups0,60,101,124; retain strict CPU cross-shape FAIL and distinguish real features from inferred padding incidence. Then test frozen same-shape interventions and level-message redundancy; no normalization-only training variant.',
    wake_paths=['pipeline/goal.json','SERVERS.yaml'],
    findings={'source_assertions_passed':12,'cpu_same_shape_checks_passed':4,'cpu_cross_shape_strict_control':'FAIL retained at1.1920928955078125e-6','native_input_unique_groups':4,'native_input_unique_expressions':16,'native_input_repeats':2,'native_network_forwards':0,'cpu_state_load':'strict;847parameter tensors','training_started':False})
for name,gate in primary['gates'].items():
    assert not gate['passed']
primary['gates']['diagnosis']['status']='Source path and native-input trigger measured; actual learned feature/task deficit unknown.'
primary['gates']['controls']['status']='12source assertions and4same-shape CPU controls pass; original strict cross-shape1e-6 control FAIL retained; native mechanism controls unrun.'
primary['gates']['resources']['status']='Real NVML context+training flock prevent original exclusive GPU guard; no new-model efficiency measured.'
scope_evidence=[snapshot,ref(ROOT/'pipeline/decisions/20261015-152750_route_change.md')]
for cid in OLD:
    c=next(c for c in work['candidates'] if c['id']==cid)
    assert c['stage']=='blocked'
    c['pre_user_mainline_hold']={k:copy.deepcopy(c.get(k)) for k in ('blocker_kind','blocker','retry_after','unblock_condition','next_action')}
    c.update(research_role='auxiliary_scope_hold',blocker_kind='human_authorization',
        blocker='Latest USER-MAINLINE20261015 supersedes supervision as primary; this stable ID is auxiliary only. This is a scope hold, not scientific falsification and not a claim that prior GPU/resource conditions cleared.',
        retry_after=(now+timedelta(hours=4)).isoformat(),
        unblock_condition='Explicit user authorization to restore this priority, or a separately justified mechanism-matched auxiliary test required by the current point-feature mainline; still verify all original native/resource/goal guards. A due timer or GPU opening alone never permits resume.',
        next_action='Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first.',
        wake_paths=['pipeline/goal.json','docs/research_mainline_correction_20261015.md'],
        historical_gates_scope='Preserved records only; no current-goal admission or trained efficacy asserted.')
    for item in scope_evidence:
        if item not in c['evidence']:c['evidence'].append(item)
work['mainline_alignment']={'at':now.isoformat(),'goal':snapshot,'primary_candidate_id':PRIMARY,'auxiliary_ids':list(OLD),'scientific_rejections_added':0}
work['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':[PRIMARY,*OLD],
    'evidence':[ref(BUNDLE/'cpu_controls_same_shape.json'),ref(BUNDLE/'native_input_incidence.json'),ref(BUNDLE/'native_preparation.json'),ref(review)],
    'resume_condition':primary['unblock_condition'],'retry_after':primary['retry_after'],
    'scope':'Primary next native capture is blocked by actual NVML context and original training flock, not a queue-full claim or route exhaustion. Non-GPU source/module/input/checkpoint/model preparation executed. Auxiliary scope holds preserve history and do not reopen on resource availability.'}
guard()
assert tick.digest(work_path)==original_hash
tick.save(work_path,work)
archive=ref(BUNDLE/'memory_before.md')
memory=f'''# Codex Research Memory
## Goal And Phase
- USER20261015 PRIMARY: hierarchical attention/information interaction actually updates point/superpoint inst_feats for query-mask prediction. Supervision/relations AUXILIARY only. Goal20constraints/11bans unchanged SHA{GOAL_SHA}; Phase1 target.5100 unmet.
- Owner01a04987-fdbe-7301-b2f0-f9b6ab60f74c; foreground only. Server-4GPU0RTX5090 one slot, pinned dl04-MS-7E06/UUID7f82edb9; server6no dispatch. Pipeline-cluster_project Disabled; no scheduler change.
- Prior complete119-line scientific memory archived verbatim: {archive['path']} SHA{archive['sha256']}. All old sourcefacts/failures/receipts/limitations retained there and in unchanged historical candidate records.
## Champion And Baseline
- Historical M95-CTF-HCG-CSORT .5020; baseline .4894; gap .0080. No new metric/efficacy from this tick.
- Frozen M95 checkpoint fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e verified at current server4 configured model folder20260815_101011/best.pth; meta epoch16. Frozen diagnostic state, not a new champion claim.
## Active Hypotheses
- PRIMARY {PRIMARY}: blocked on actual context+training flock. Exact native inputs and CPU full-model load prepared. Next run native_feature_capture.py under fresh owned lease/resource/flock/checkpoint guards; no synthetic-to-native inference.
- CTF independent per-scale FFN, HCG composed gather+point/global-mean scale fusion; actual cluster branch query-blind GIVEN bank/inputs, not whole-model query/language independence. Message updates inst_feats and mask readout uses inst_feats.
- 12AST assertions passed. Constructed CPU6validpoint fixture: query swap0, repeat0, token permutation3.703001976, padding featuredelta.093810439/fixedQlogitdelta.043136418. NOT real TRAIN features or learned efficacy.
- Same-shape4controls passed, gate-logit replay/path-block delta0; raw mean includes padded rows. Actual task/scale complementarity unknown. All six admission gates remain false.
- Four OLD supervision IDs are auxiliary_scope_hold with human_authorization blocker, not scientifically rejected; all evidence/gates preserved. Do not execute old next_action or recover M201 on due timers/resource openings.
## Closed Or Failed Directions
- Entire prior91rejected/4complete records and scope-specific failures unchanged; full details in memory archive and research_work.json. No rejected route reopened, relabeled or tuned.
- This tick CPU control V1 andV2 strict cross-shape1e-6 FAIL at1.1920928955078125e-6 retained in cpu_attempt.json/cpu_attempt_v2.json. Same-shape pass does not replace either FAIL.
- Pure masked-mean/normalization repair is NOT an independently admitted hierarchy-attention core. Banned gate/routing/residual/repeated injection/noN2 and Phase1 tuning bans remain.
- PDC .4977434278, BEI .4741974175, TMR .4952795208 native screens remain below M95; historical BPS interruption is not an efficacy rejection.
## Running And Queue
- Preflight2026-10-15T08:10:12.609019Z: design/running0/claiming0/waiting0/capacity1/budget1; no new training. GPU facts unknown in deterministic preflight table.
- Actual resource {resource['observed_at']}: GPU0free11994/used20107/total32607MiB/util0; NVML2634704 uses20016MiB; original training flock held, two diagnostic flocks available. NOT idle/authorized to allocate; no signals/reset/deletion/foreign scan.
- Native dataset4TRAIN groups0/60/101/124,4scenes/16uniqueexpressions, two repeats exact;8getitem/32expression appearances NOT32unique. Pair lengths667/2329 and406/1441 infer padding valid fractions.286389/.281749; no network feature capture.
- CPU full M95 constructed and state loaded STRICT,847parameter tensors/two serialized buffers verified, CUDAfalse/native network forwards0/optimizer0. Prepared adapter GPU branch not executed.
## Open Questions And Risks
- Learned feature redundancy, padding-induced real task harm, novelty, full native backward and new mechanism efficiency unknown. Input-incidence/source arithmetic is not a native feature/benefit certificate.
- Preserve original1e-6 controls and all prior full-forward FAILs; do not tune precision/tolerance/seed/sample/config to create PASS.
- No GPU native launch until live no-other-NVML context, >=30000MiB idle-equivalent headroom and actual originalflocks acquired. Preserve original.25allocator cap and current one-slot authorization.
- M201 remains interrupted/no automatic restore under latest mainline. Full checkpoint/642optimizer/scheduler/patience state and false-monitor interruption evidence remain in archive; no cold restart/trajectory claim.
- New core must follow actual fixed-TRAIN diagnosis; no normalization-only/new-loss-only successor or history renaming. Literature not re-reviewed this tick; no independent novelty asserted.
## Last Tick
- Current{TOKEN}, design snapshot08:10:12.609019Z/deadline09:10:12.609019Z immutable. New1primary diagnostic,4old scope-held;0new rejection/admission/training/GPUtests/optimizer. Source/model/inputs CPU evidence only; scienceblocked/inconclusive.
- Full review pipeline/reviews/motivation_review_hier_feature_20261015_73d9.md; bundle {BUNDLE.relative_to(ROOT).as_posix()}; exact hashes in candidate evidence. CPU full-model preparation/native inputs complete; next test is real native feature capture on released GPU.
- This memory is written before postflight; actual completion/release authoritative in helper receipt and task. Prior manual2860ad0928504b40a4e36908928e3a83 finishedPASS/FINALIZED with lease+pending absent verified15:30:07+08.
'''
assert len(memory.splitlines())<120
guard()
memory_path.write_text(memory,encoding='utf-8')
notes={'actions':[
    'cluster_project；快照2026-10-15T08:10:12.609019Z，design。依最新用户主线先登记稳定候选并完成12项源码断言；CTF为分尺度FFN、HCG为层级广播/融合，不把已有骨架说成新层间注意力。',
    '原模块构造CPU样本：padding有效特征delta0.093810439、固定query logits delta0.043136418。两次严格跨形状控制FAIL保留；后续同形状4项路径控制通过，不能替代旧FAIL或当作真实TRAIN特征伤害。',
    '实际原生CPU取样4群组/4场景/16表达式，两次重复一致；8次getitem/32表达式出现不是32独立样本。预注册两对超点长度667/2329和406/1441支持padding触发条件，未捕获学习特征。',
    '16:36+08核验M95冻结checkpoint fe5e4a5f...与配置a18f2c6f...；原生适配器CPU构造和严格装载847参数tensor、两项序列化缓冲区通过，CUDA未初始化，网络forward/backward均未执行。',
    '后快照资源16:24:50+08：server-4 GPU0 free11994MiB，NVML2634704占20016MiB，原训练flock held；另两诊断锁可得。未达既有30000MiB/无其他NVML/原flock守卫，未分配GPU。',
    '4个旧监督候选仅转辅助范围暂停，保留原状态、证据、失败和历史门槛，不因到期/空槽恢复M201。新主线候选六门槛均未通过；新增候选1，准入/训练/科学否决/GPU测试/优化器步数均0。',
    '执行状态待finish/收据核验；科学状态blocked/inconclusive。用量仅begin到收据可见本地窗口，不含先前读取、延迟记录和最终回复；缺失未知，缓存含于输入而非重复相加，不是账单。'],
    'decisions':[
    '按已授权主线继续同一m95-hierarchical-mask-feature-path-audit；原生捕获协议和CPU准备已完成，下一步在新租约下重新核实资源后捕获真实M95特征，再决定结构机制。',
    '以真实资源证据作external_resource_blocked收尾，不宣称路线穷尽；主要候选一小时后可重查，旧监督范围暂停仅在新授权或主线匹配对照需求下解除。未改目标/调度/队列/训练代码或准入标准。']}
tick.save(BUNDLE/'notes.json',notes)
tick.save(BUNDLE/'persistence.json',{'token':TOKEN,'recorded_at':now.isoformat(),'primary_stage':primary['stage'],'scope_held_ids':list(OLD),'memory_lines':len(memory.splitlines()),'archive':archive,'new_candidates':1,'admissions':0,'training':0,'scientific_rejections':0})
print(json.dumps({'token':TOKEN,'primary':'blocked','auxiliary_scope_holds':4,'memory_lines':len(memory.splitlines()),'next_primary_retry':primary['retry_after'],'six_gates_passed':0},indent=2))
