"""Freeze the one shared-prefix change before observing its results."""
from datetime import datetime,timezone
from run import BUNDLE,ROOT,TOKEN,guard,tick

guard()
work=tick.load(ROOT/'pipeline/research_work.json')
before=tick.load(BUNDLE/'work_before.json')
primary='m95-hierarchical-mask-feature-path-audit'
assert [c for c in work['candidates'] if c['id']!=primary]==[c for c in before['candidates'] if c['id']!=primary]
candidate=next(c for c in work['candidates'] if c['id']==primary)
assert len(candidate['revision_history'])==1 and candidate['revision_history'][0]['result']=='passed'
def ref(name):
    path=BUNDLE/name
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
failure=[ref('trace_baseline_result.json'),ref('trace_canonical_result.json')]
prereg=[ref('revision2_prereg.md'),ref('rematerialization.py'),ref('checkpoint_api.json')]
candidate['revision_history'].append({'revision':2,'failure_scope':'implementation',
    'reason':'Both branches reach point readout with about5.81GB retained; canonical fails at output projection, original M95 fails after readout under SAME25%cap. Shared pure-prefix activation retention is a bounded memory-lifetime defect, not foreign occupation or hypothesis falsification.',
    'change':'Non-reentrant RNG-preserving rematerialization of every original use_cluster=False encoder and paired decoder; structurally first5pairs. Last cluster encoder/final decoder/bank/CSORT are NOT checkpointed. Identical adaptation for matched baseline/canonical diagnostics; no parameter/arithmetic/data/dtype/batch/cap change.',
    'prediction':'All20native captured pure-prefix module output/input-gradient/parameter-gradient comparisons meet originalfloat32<=1e-6; matched baseline/canonical full native loss/backward can finish under original25%cap and own-NVML guard, with cluster executed once.',
    'preregistered_at':datetime.now(timezone.utc).isoformat(),'failure_evidence':failure,
    'preregistration_evidence':prereg,'result':'pending','evidence':[]})
candidate['stage']='implementation'
candidate['next_action']='Execute revision2 frozen20native prefix-module equivalence tests, then matched fresh-process actual full native loss/backward with unchanged25%cap, no optimizer. Preserve all oldFAILs and all six unpassed admission gates.'
candidate['evidence'].extend([e for e in failure+prereg if e not in candidate['evidence']])
tick.save(ROOT/'pipeline/research_work.json',work)
tick.save(BUNDLE/'revision2_registration.json',{'token':TOKEN,'revision':2,'result':'pending',
    'registered_at':candidate['revision_history'][-1]['preregistered_at'],
    'other99unchanged':True,'new_training':0,'failure_evidence':failure,'preregistration_evidence':prereg})
print('Revision2 preregistered under SAME ID; original results and other99records retained.')
