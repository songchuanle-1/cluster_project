"""Bounded authorization/scope rechecks only;never resume auxiliary tests."""
from datetime import datetime,timezone,timedelta
import json
from ops import guard,save,add,evidence,ROOT,OUT
import foreground_tick as tick
owner=guard();now=datetime.now(timezone.utc)
work=tick.load(ROOT/'pipeline/research_work.json')
due=[c for c in work['candidates'] if c['stage']=='blocked' and c.get('blocker_kind')=='human_authorization' and datetime.fromisoformat(c['retry_after'])<=now]
assert len(due)==4
paths=sorted({p for c in due for p in c['wake_paths']})
observations=[{'path':p,'exists':(ROOT/p).exists(),'sha256':tick.digest(ROOT/p) if (ROOT/p).is_file() else None} for p in paths]
goal=tick.load(ROOT/'pipeline/goal.json')
assert goal['research_mainline']['primary_axis']=='hierarchical_attention_point_feature_update'
save('scope_hold_recheck.json',{'observed_at':now.isoformat(),'actually_due_ids':[c['id'] for c in due],
    'watched_file_observations':observations,'goal_unchanged':True,'new_explicit_priority_restore_authorization':False,
    'mainline_requires_these_auxiliary_tests':False,'basis':'Current native point-content/QFdiagnosis does not require old relation/supervision-axis tests;unchanged goal keeps original priorityhold. Timers and freeGPU do not authorize restoration.',
    'auxiliary_native_tests_executed':0,'outcome':'All4originalblockers/unblockconditionspreserved;bounded4hourretryonly'})
for c in due:
    c['last_rechecked_at']=now.isoformat();c['retry_after']=(now+timedelta(hours=4)).isoformat()
    add(c,[OUT/'scope_hold_recheck.json'])
guard();tick.save(ROOT/'pipeline/research_work.json',work)
notes=tick.load(OUT/'report_notes.json')
notes['actions'].append('临近收尾核对4个人审/范围冻结项已在本轮中途实际到期：记录当前goal及主线路线文件哈希，未见新的优先级恢复授权，当前点特征/QF诊断不依赖这些旧辅助测试；保留原阻塞/解除条件，仅按契约延后4小时重查，辅助原生测试0。不是放行、不是新科学实验，也不是GPU资源阻塞。')
guard();tick.save(OUT/'report_notes.json',notes)
print(json.dumps({'actually_due_holds_rechecked':len(due),'scope_restored':False,'auxiliary_tests':0,'retry_after':(now+timedelta(hours=4)).isoformat()}))
