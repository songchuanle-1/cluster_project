"""Recheck scopeholds only if actually due;no restoration or auxiliary test."""
from datetime import datetime,timezone,timedelta
import json
from ops import guard,save,add,ROOT,OUT
import foreground_tick as tick

o=guard()
now=datetime.now(timezone.utc)
w=tick.load(ROOT/'pipeline/research_work.json')
due=[c for c in w['candidates'] if c['stage']=='blocked' and c.get('blocker_kind')=='human_authorization'
     and datetime.fromisoformat(c['retry_after'])<=now]
if due:
    paths=sorted({p for c in due for p in c['wake_paths']})
    observations=[]
    for p in paths:
        target=(ROOT/p).resolve()
        assert ROOT.resolve() in target.parents
        observations.append({'path':p,'exists':target.exists(),'sha256':tick.digest(target) if target.is_file() else None})
    save('scope_hold_recheck.json',{'observed_at':now.isoformat(),'actually_due_ids':[c['id'] for c in due],
        'watched_files':observations,'goal_unchanged':True,'new_explicit_priority_restore_authorization':False,
        'current_native_point_diagnostics_require_auxiliary_tests':False,'auxiliary_native_tests':0,
        'outcome':'Originalscopeblockers/unblockconditionspreserved;timers/GPUidle do not grant restoration'})
    for c in due:
        c.update(last_rechecked_at=now.isoformat(),retry_after=(now+timedelta(hours=4)).isoformat())
        add(c,[OUT/'scope_hold_recheck.json'])
    guard()
    tick.save(ROOT/'pipeline/research_work.json',w)
    notes=tick.load(OUT/'report_notes.json')
    notes['actions'].append('本轮中途实际到期的'+str(len(due))+'个人审/辅助范围冻结项仅复查当前goal与监测文件哈希；无新的恢复授权，原阻塞和解除条件不变，按4小时有界重查，辅助原生测试0。非放行、非GPU资源阻塞。')
    tick.save(OUT/'report_notes.json',notes)
remaining=(datetime.fromisoformat(o['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
if remaining<=180:
    w=tick.load(ROOT/'pipeline/research_work.json')
    active=next(c for c in w['candidates'] if c['id']=='native-train-prefix-repeatability-audit')
    w['design_cycle']={'stop_reason':'tick_deadline_near','attempted_ids':['hierarchical-padding-context-invariance-audit',active['id']],
        'evidence':[{'path':(OUT/'final_progress.json').relative_to(ROOT).as_posix(),'sha256':tick.digest(OUT/'final_progress.json')}],
        'resume_condition':active['next_action'],'observed_remaining_seconds':remaining}
    guard()
    tick.save(ROOT/'pipeline/research_work.json',w)
print(json.dumps({'actually_due_holds':len(due),'remaining_seconds':remaining,'deadline_at':o['deadline_at']}))
