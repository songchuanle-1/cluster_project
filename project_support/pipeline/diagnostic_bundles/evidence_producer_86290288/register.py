"""Register the required stable diagnosis before any broad route review."""
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

os.environ['PROJECT_ROOT']='D:/project'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick

ROOT=Path('D:/project/cluster_project')
OUT=Path(__file__).resolve().parent
TOKEN='862902880d824f63be9f0113367d1207'
owner=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']
assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
work=tick.load(ROOT/'pipeline/research_work.json')
cid='m202-paired-native-evidence-producer'
assert not any(c['id']==cid for c in work['candidates'])
evidence=lambda path:{'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
work['candidates'].append({
    'id':cid,'stage':'diagnosis','candidate_type':'operational_diagnostic',
    'parent_candidate_id':'m95-hierarchical-mask-feature-path-audit',
    'parent_experiment_id':'M202-HDS','created_at':datetime.now(timezone.utc).isoformat(),
    'hypothesis':'A prediction-blind producer can export unique split/scene/object/annotation-aligned IoUs while exactly preserving native prediction values and their aggregate; malformed, duplicated, missing or mispaired identities must fail explicit controls.',
    'matched_control':'Unmodified native model.predict and tools/train.py prediction[piou] aggregation; same fixed TRAIN cohort/checkpoint/seed, no altered features, masks, selection or optimization.',
    'next_action':'Inspect actual native predict and dataset identity contracts, execute CPU alignment/aggregation negative controls, then perform fixed-TRAIN native equivalence capture on an idle authorized slot under exclusive locks.',
    'evidence':[evidence(OUT/'prereg.md'),evidence(ROOT/'Cluster/tools/train.py')],
    'scope':'Operational evidence producer for the existing frozen evaluation plan; not a new model/training admission or reopened scientific mechanism.'})
tick.save(ROOT/'pipeline/research_work.json',work)
print('REGISTERED_DIAGNOSIS='+cid)
