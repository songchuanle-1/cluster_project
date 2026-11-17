"""Persist one local implementation revision before seeing its test outputs."""
from datetime import datetime,timezone
import json
from run import BUNDLE,ROOT,TOKEN,guard,tick
guard()
path=ROOT/'pipeline/research_work.json'
work=tick.load(path)
before=tick.load(BUNDLE/'work_before.json')
assert work==before
candidate=next(c for c in work['candidates'] if c['id']=='m95-hierarchical-mask-feature-path-audit')
assert not candidate.get('revision_history')
def ref(file):return {'path':file.relative_to(ROOT).as_posix(),'sha256':tick.digest(file)}
failure=[ref(ROOT/'pipeline/diagnostic_bundles/hier_support_5df76ddd906e4741b57970488d4b33bd/result.json'),
    ref(BUNDLE/'native_support_probe_result.json'),ref(BUNDLE/'runtime_probe_result.json')]
candidate['revision_history']=[{'revision':1,'failure_scope':'implementation',
    'reason':'Compacted key axes differ from canonical dense arithmetic; original12strictfloat32FAILs plus4native-input strict discrepancies retained. Target torch1.12 lacks SDPA.',
    'change':'Keep full bounded per-scale bank axis; vectorized static support masks before plain matmul/softmax. No dtype/backend/threshold/seed/parameter change; grouped/chunk/checkpoint optimization claims withdrawn for this realization.',
    'prediction':'Original frozen fixtures and all16native expressions match unchanged dense reference output/readout/input gradients within original1e-6 float32 and1e-10 float64; original failures never reclassified.',
    'preregistered_at':datetime.now(timezone.utc).isoformat(),'failure_evidence':failure,
    'result':'pending','evidence':[ref(BUNDLE/'revision1_prereg.md'),ref(BUNDLE/'canonical_readout.py')]}]
candidate['stage']='implementation'
candidate['next_action']='Run preregistered revision1 canonical-bank-axis operator against UNCHANGED dense reference, frozen fixtures and native inputs under original tolerances; then same-prefix native suffix and matched resources. Retain all oldFAILs and no training admission.'
candidate['evidence'].extend([ref(BUNDLE/'revision1_prereg.md'),ref(BUNDLE/'canonical_readout.py')])
assert all(not gate['passed'] for gate in candidate['gates'].values())
tick.save(path,work)
tick.save(BUNDLE/'revision_prereg_record.json',{'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'candidate_id':candidate['id'],'revision':1,'result':'pending','failure_evidence':failure,
    'prereg_sha256':tick.digest(BUNDLE/'revision1_prereg.md'),'core_sha256':tick.digest(BUNDLE/'canonical_readout.py'),
    'other99unchanged':True,'new_candidates':0,'new_training':0})
print('Revision1 preregistered; same ID, original failures and all six gates retained.')
