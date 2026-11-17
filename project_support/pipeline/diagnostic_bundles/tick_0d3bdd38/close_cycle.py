"""Bind honest remaining work to the actual near deadline;never wait or extend."""
from datetime import datetime,timezone
import json
from ops import guard,save,evidence,ROOT,OUT
import foreground_tick as tick
owner=guard();now=datetime.now(timezone.utc);remaining=(datetime.fromisoformat(owner['deadline_at'])-now).total_seconds()
assert 0<remaining<=180,remaining
work=tick.load(ROOT/'pipeline/research_work.json')
work['design_cycle']={'stop_reason':'tick_deadline_near','attempted_ids':tick.load(OUT/'progress_summary.json')['attempted_ids'],
    'evidence':[evidence(OUT/'progress_summary.json'),evidence(OUT/'final_analysis.json')],
    'resume_condition':'Resume SAME terminal diagnosis ID with separately frozen native Q/Fcross-factor capture on same unique best13/cohort32/helperrevision2;first require native mask reconstruction<=1e-6,current owning lease,liveidle authorizedGPU and3flocks. No training restart/VALselection/numericalrevision3. Auxiliary holds retain original conditions.',
    'observed_at':now.isoformat(),'deadline_at':owner['deadline_at'],'remaining_seconds':remaining}
guard();tick.save(ROOT/'pipeline/research_work.json',work)
save('closure_clock.json',{'observed_at':now.isoformat(),'deadline_at':owner['deadline_at'],'remaining_seconds':remaining,'stop':'tick_deadline_near','resources_not_falsely_blocked':True})
print(json.dumps({'deadline_really_near':True,'remaining_seconds':remaining}))
