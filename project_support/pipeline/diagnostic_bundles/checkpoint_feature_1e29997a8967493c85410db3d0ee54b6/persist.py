"""Append the checkpoint-source control without changing any existing hold."""
from datetime import datetime,timezone
import json
from run_checkpoint_controls import BUNDLE,ROOT,TOKEN,guard,tick

PRIMARY='m95-hierarchical-mask-feature-path-audit'
guard()
result=tick.load(BUNDLE/'result.json')
assert result['overall_control_status']=='PASS_CURRENT_FIXTURE_ONLY'
assert all(result['checks'].values()) and all(result['same_shape_checks'].values())
assert result['checkpoint_sha256']=='fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
assert result['module_state_count']==30 and result['fixture_rng_unchanged']
assert not result['cuda_initialized'] and result['gpu_tests']==result['optimizer_steps']==0
assert not result['resource']['fresh_this_tick']
work_path=ROOT/'pipeline/research_work.json'
work=tick.load(work_path)
work_hash=tick.digest(work_path)
candidate=next(c for c in work['candidates'] if c['id']==PRIMARY)
assert candidate['stage']=='blocked' and candidate['blocker_kind']=='gpu_context_or_lock_not_released'
assert datetime.fromisoformat(candidate['retry_after'])>datetime.now(timezone.utc),'Do not silently miss an elapsed retry'
protected={k:candidate[k] for k in ('blocker_kind','blocker','retry_after','unblock_condition','next_action')}
memory_path=ROOT/'pipeline/codex_memory.md'
memory=memory_path.read_text(encoding='utf-8')
for name,data in (('work_before.json',work_path.read_bytes()),('memory_before.md',memory_path.read_bytes())):
    path=BUNDLE/name
    assert not path.exists()
    path.write_bytes(data)
def ref(path):return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
evidence=[ref(BUNDLE/name) for name in ('prereg.md','run_checkpoint_controls.py','remote_checkpoint_fixture.py','attempt.json','result.json')]
candidate['evidence'].extend(evidence)
candidate['findings']['checkpoint_source_control']={
    'observed_at':result['recorded_at'],'module_state_count':30,'fixture_rng_unchanged':True,
    'padding_valid_feature_delta':result['metrics']['padding_valid_feature_delta'],
    'padding_fixed_query_logit_delta':result['metrics']['padding_fixed_query_logit_delta'],
    'cross_shape_control_delta':result['metrics']['masked_mean_padding_control_delta'],
    'same_shape_path_block_delta':result['same_shape_metrics']['blocked_global_mean_path_delta'],
    'scope':'Original frozen checkpoint module weights but still constructed point/token inputs, not native TRAIN network features. Both previous random-weight strict FAILs preserved.'}
candidate['gates']['controls']['status']='Checkpoint-weighted constructed CPU fixture current controls pass; both prior random-weight strict cross-shape1e-6 FAILs retained. Native feature mechanism controls unrun; admission false.'
assert all(not gate['passed'] for gate in candidate['gates'].values())
assert all(candidate[k]==v for k,v in protected.items())
old_resource=ROOT/'pipeline/diagnostic_bundles/hier_feature_73d9f276d8ba41fe96f1176fb84e9ef4/cpu_controls_same_shape.json'
work['design_cycle']={
    'stop_reason':'external_resource_blocked','attempted_ids':[PRIMARY],
    'evidence':evidence+[ref(old_resource)],
    'resume_condition':candidate['unblock_condition'],'retry_after':candidate['retry_after'],
    'scope':'One new non-GPU checkpoint-weight source control executed. Primary resource block/retry/guards remain unchanged and are not due; GPU occupation was NOT rechecked this tick, historical16:24:50+08 evidence is not a fresh observation. The four due auxiliary scope-hold signals are acknowledged without executing or changing those candidates. No route exhaustion/queue-full/new idle claim.'}
guard()
assert tick.digest(work_path)==work_hash
tick.save(work_path,work)
new_line='- Checkpoint-source CPU control '+TOKEN+': exact M95 module30state entries loaded; same constructed fixture/RNG unchanged. Featurepaddingdelta.176026702/fixedQlogitdelta.047073841; same-shape block/replay0; current cross-shape control9.536743e-7 within original1e-6. NOT native TRAIN features or new efficacy; both old random-weight strictFAILs retained.\n'
memory=memory.replace('## Active Hypotheses\n','## Active Hypotheses\n'+new_line,1)
memory=memory.replace('- Current73d9f276d8ba41fe96f1176fb84e9ef4,','- Prior73d9f276d8ba41fe96f1176fb84e9ef4,',1)
memory=memory.replace('## Last Tick\n','## Last Tick\n- Current'+TOKEN+' design snapshot2026-10-15T09:09:38.640203Z/deadline10:09:38.640203Z immutable. Due4auxiliary IDs remain user-scope-held and unchanged; primary not due until17:46:54+08. New checkpoint-weight CPU control evidence appended only to SAME primary;0candidate/variant/admission/GPUtest/networkforward/training/optimizer. No resource recheck or retry extension.\n',1)
memory=memory.replace('- This memory is written before postflight; actual completion/release authoritative in helper receipt and task.','- Current memory is pre-postflight; actual helper receipt/task governs completion. Prior73d9 tick actualPASS/FINALIZED/lease+pending absent verified2026-10-15T16:51:23+08.',1)
assert len(memory.splitlines())<120 and memory.count('## ')==7
memory_path.write_text(memory,encoding='utf-8')
notes={'actions':[
    '快照2026-10-15T09:09:38.640203Z，design；4个辅助监督候选因范围/工件变化被列为due，但最新用户主线禁止仅因due而恢复。已确认其范围暂停，未执行或改写这4个候选。主线资源候选尚未到原17:46:54+08复查时间。',
    '同一主线候选新增一次权重来源对照：原fixture/seed1999/输入生成顺序/1e-6不变，严格装载M95冻结checkpoint中的30项cluster模块状态，RNG状态未改变。所有执行均在server-4 CPU，CUDA未初始化。',
    '冻结权重构造fixture的padding有效特征delta0.176026702、固定Qlogitdelta0.047073841；原logits重放/路径阻断delta0；本次跨形状控制9.536743e-7通过原1e-6。旧随机权重两次FAIL不覆盖；该结果不是实际TRAIN学习特征、任务伤害、泛化收益或新的科学准入。',
    '本轮不提前重复GPU资源探针、不推断释放，沿用上轮16:24:50+08历史阻塞证据并明确其非本轮实时观测；原blocker/retry/unblock/next_action、资源门槛和4个辅助范围暂停保持。',
    '新增候选/变体/准入/GPU测试/原生网络forward/训练/优化器步数均0。执行状态待finish核验，科学状态blocked/inconclusive，六项准入仍为false。用量仅begin至收据的可见本地窗口；缺失未知，缓存包含于输入、不重复相加，不是账单。'],
    'decisions':[
    '新CPU结果仅排查随机权重来源解释，继续同一主线诊断；原生M95特征捕获仍须到期后以新鲜资源/锁/文件核验和当前前台租约执行。',
    '尊重用户主线及现有资源冷却，旧监督候选不因due自动恢复；保留所有旧FAIL、历史门槛和科学未知，不新增独立核心、不为填槽训练，也不宣称本轮实时显存足够。']}
tick.save(BUNDLE/'notes.json',notes)
tick.save(BUNDLE/'persistence.json',{'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),'new_candidates':0,'changed_candidate_ids':[PRIMARY],'old_auxiliary_candidates_unchanged':True,'resource_hold_fields_unchanged':True,'primary_retry_unchanged':candidate['retry_after'],'memory_lines':len(memory.splitlines())})
print(json.dumps({'candidate':PRIMARY,'stage':candidate['stage'],'new_candidates':0,'six_gates_passed':0,'old_auxiliary_holds_unchanged':True,'resource_retry_unchanged':candidate['retry_after'],'memory_lines':len(memory.splitlines())},indent=2))
