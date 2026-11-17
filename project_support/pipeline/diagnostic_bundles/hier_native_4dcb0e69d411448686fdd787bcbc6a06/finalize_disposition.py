"""Record the actual deadline boundary, never an invented resource block."""
from datetime import datetime,timezone
import json
from run import BUNDLE,ROOT,TOKEN,guard,tick
owner=guard()
now=datetime.now(timezone.utc)
remaining=(datetime.fromisoformat(owner['deadline_at'])-now).total_seconds()
assert 0<remaining<=180
work=tick.load(ROOT/'pipeline/research_work.json')
before=tick.load(BUNDLE/'work_before.json')
primary='m95-hierarchical-mask-feature-path-audit'
assert [c for c in work['candidates'] if c['id']!=primary]==[c for c in before['candidates'] if c['id']!=primary]
candidate=next(c for c in work['candidates'] if c['id']==primary)
def ref(name):
    path=BUNDLE/name
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
work['design_cycle']={'stop_reason':'tick_deadline_near','attempted_ids':[primary],
    'recorded_at':now.isoformat(),'seconds_remaining':remaining,
    'evidence':[ref(name) for name in ('canonical_tests_result.json','memory_baseline_result.json','memory_canonical_result.json','independent_adapter_result.json','release_verification.json')],
    'resume_condition':candidate['next_action']}
tick.save(ROOT/'pipeline/research_work.json',work)
tick.save(BUNDLE/'deadline_disposition.json',{'token':TOKEN,**work['design_cycle']})
print(json.dumps({'recorded_at':now.isoformat(),'seconds_remaining':remaining,'stop_reason':'tick_deadline_near','other99unchanged':True}))
