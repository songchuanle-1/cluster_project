"""Retain scientific states; refresh only actual due scope/resource evidence."""
from tick_ops import *
import hashlib
guard(180)
slots=tick.load(OUT/'authorized_slots_current.json')
assert slots['server-4']['idle'] is False
assert slots['server-3']['idle'] is None and slots['server-3']['gpu_query']['returncode']==255
assert len(slots['server-4']['M204']['latest_distinct_native_steps'])>=2
integrity=tick.load(OUT/'frozen_bundle_integrity.json');assert len(integrity['bundles'])==2
scope=tick.load(OUT/'scope_recheck.json');assert scope['goal_sha256']==GOAL and not scope['new_scope_authorization_in_this_turn']
now=datetime.now(timezone.utc);resource_retry=(now+timedelta(minutes=58)).isoformat();human_retry=(now+timedelta(hours=4)).isoformat()
work=tick.load(ROOT/'pipeline/research_work.json')
def scientific_state(c):
 value={k:c.get(k) for k in ('hypothesis','hypothesis_id','gates','failure_scope','revision_history')}
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
before={c['id']:scientific_state(c) for c in work['candidates'] if c['id'] in PRIMARY+AUX}
def append(c,paths):
 known={(e['path'],e['sha256']) for e in c['evidence']}
 for path in paths:
  entry=evidence(path)
  if (entry['path'],entry['sha256']) not in known:c['evidence'].append(entry)
for cid in PRIMARY:
 c=next(c for c in work['candidates'] if c['id']==cid)
 assert c['stage']=='blocked' and c['non_gpu_preparation_complete'] is True
 c.update(last_checked_at=now.isoformat(),blocker_kind='external_resource',retry_after=resource_retry,
  blocker='Duefreshcheck20:19Shanghai:server4authorizedGPU0isheldbyliveM204andall3locks;server3GPU1queryandcomputecontextsreturn255devicehandleUnknownError,socurrentGPU1UUID/memory/occupationUNKNOWN. NoauthorizedverifiedidleexclusiveCUDAavailable. Frozenlocalnativebundle/protocolunchanged;nonGPUpreparationalreadycomplete.',
  unblock_condition='Actualserver4GPU0openingORserver3GPU1queryrecovery;thenfreshpinnedhostname/UUID/liveidleness/all3exclusiveflocks/nativeassets/currentforegroundleaseandoriginal1e-6taskcontrolsverify. Timeraloneisnotavailability. Retainallpriorstrictfailures;noM204restart/newtraininginferred.')
 append(c,[OUT/'authorized_slots_current.json',OUT/'frozen_bundle_integrity.json',OUT/'recheck_result.md',OUT/'recheck_due.py'])
for cid in AUX:
 c=next(c for c in work['candidates'] if c['id']==cid)
 assert c['stage']=='blocked' and c['blocker_kind']=='human_authorization'
 c.update(last_checked_at=now.isoformat(),retry_after=human_retry)
 append(c,[OUT/'scope_recheck.json',OUT/'recheck_result.md'])
for c in work['candidates']:
 if c['id'] in before:assert scientific_state(c)==before[c['id']],'Do not rewrite scientific states while checking holds'
save('due_check_disposition.json',{'observed_at':now.isoformat(),'ids_rechecked':PRIMARY+AUX,'resource_retry_after':resource_retry,'human_scope_retry_after':human_retry,'scientific_state_sha256_unchanged':before,'new_candidates':0,'new_scientific_passes':0,'native_task_mask_executions':0,'new_training':0,'meaning':'Actualduedependencyevidenceonly,not6newexperiments;no repeated unchangedCPUfixtures or gatewaivers.'})
work['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':PRIMARY+AUX,
 'evidence':[evidence(OUT/name) for name in ('authorized_slots_current.json','frozen_bundle_integrity.json','scope_recheck.json','due_check_disposition.json','recheck_result.md')],
 'resume_condition':'Resumeoriginal2preparedprimarynativeTASKSafteractualauthorizedresourceavailabilityandfreshstrictguards;4auxiliaryscopeholdsuntilactualscope/mainlineevidencechanges. NoautomaticM204restart/tuning/duplicatecandidate.',
 'retry_after':resource_retry,'scope':'Due6stableIDsreviewedfirst. Remainingreservebudget2notdenied;nomandatorybootstrapwithdueIDs,nonewindependenterror evidenceandnoduplicate/placeholdervariant. Notglobalindependentrouteexhaustion.',
 'new_candidates':0,'new_training':0,'new_scientific_passes':0}
guard();tick.save(ROOT/'pipeline/research_work.json',work)
notes={'actions':[
 '本轮快照20:11:53上海；begin仅执行一次，按分页读取6个到期稳定ID，优先续做原有候选而非新建同义变体。实际储备0/2、准备预算2、总待续6/8；未把停放项当可用储备，也未伪称预算为0或路线耗尽。',
 '20:19:01实测server4授权GPU0身份/UUID正确，M204及三锁占用；Train[13/50]3651→3656/4686，日志mtime新鲜。server3SSH/hostname正常但GPU1及contexts查询继续return255，报设备句柄UnknownError，UUID/显存/占用仍未知，故无可安全使用且已核实空闲的授权独占卡。未重置、驱逐、重启或使用未授权卡。',
 '两主线原native_manifest绑定的runner/runtime/metrics及protocol哈希均未改变，原1e-6及旧float32/缓存GPU失败保留；先前可执行非GPU准备已完成，本轮不重跑无变化的CPU数值、移植或统计fixture。真实原生任务mask仍未执行，不能当科学对照通过。',
 '四个到期辅助方向按ID核对scope与原门槛；最新goal仍以分层点特征为primary，未出现恢复监督优先级的新授权。保留全部历史科学状态，包括BPS旧已过门槛；不重跑旧监督测试、不恢复M201、不重复索取已执行的CPA恢复授权。',
 '本轮begin监控best约0.4944、13/50；历史champion0.5020、baseline0.4894、target0.5100不变。实际产出为6个到期证据复查、2份入口完整性核验和1组两授权卡资源记录，非6个新实验；新候选/科学PASS/准入/原生mask实测/新训练均0。收据用量窗口为begin到receipt的本地部分日志，完整收据当前待生成；未知不记0，不把cache/input和reasoning/output重复相加或当账单。'],
 'decisions':[
 '资源状态与上一轮相同：现有M204继续，两个已准备主线仍等原生CUDA对照；server3故障持续而不是新故障。当前没有新科学结论，不把早期best当完整训练提升或新champion。',
 '两资源候选在1小时内或实际资源/队列证据变化后按原稳定ID复查；四辅助scope hold在4小时内或真实scope/主线证据变化后复查。到期或查询恢复都不是空闲/优先级恢复/新训练许可，仍须新鲜身份、占用、锁、资产及原1e-6控制。',
 '不制造候选填预算、不宣称所有独立路线穷尽、不重复无变化研究或索权；保留固定query、原native目标/配对与所有既有失败。本轮只做有意义的到期依赖检查，完整六段留档。',
 '本报告保存时finish待验证；仅在finish明确通过并核实上下文提交及租约/待提交文件释放后称本轮检查完成。无变化健康推进默认静默，不改变自动化通知或调度。']}
save('report_notes.json',notes)
print(json.dumps({'updated_due_ids':6,'resource_retry_after':resource_retry,'auxiliary_scope_retry_after':human_retry,'scientific_states_unchanged':True,'new_training':0,'notes':str(OUT/'report_notes.json')},ensure_ascii=True,indent=2))
