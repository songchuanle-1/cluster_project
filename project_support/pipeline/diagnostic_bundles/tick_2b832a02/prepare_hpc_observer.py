"""Bind the existing read-only original-training observer to actual canonical HPC."""
from pathlib import Path
import ast,json
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
guard();dispatch=HERE/'hpc_dispatch_result.json'
assert sha(dispatch)=='d91f87399ae7486222032ddc5da41fb8c233de2c99d46449deb135aa1c2770c1'
exp=json.loads((ROOT/'pipeline/experiments/M218-HPC.json').read_text('utf8'))
assert exp['status']=='running' and exp['pid']==187081 and exp['code_commit']=='6282263d805c1741234f97afc981a05aca2ad6e3'
assert exp['launch_verified'] is True and exp['launch_verification']=='training_progress'
s=(ROOT/'pipeline/diagnostic_bundles/tick_240fb040/observe_cre.py').read_text('utf8')
changes=[('Exact original CRE','Exact original HPC'),('M217-CRE','M218-HPC'),('PID=118189','PID=187081'),
         ("COMMIT='d58576b396cfb54577652be972f3ffaffda508c9'","COMMIT='6282263d805c1741234f97afc981a05aca2ad6e3'"),
         ('tick_01b53a4e/cre_root_ff_result.json','tick_2b832a02/hpc_root_ff_result.json'),
         ('cre_training_progress_observation.json','hpc_training_progress_observation.json')]
for before,after in changes:
    assert before in s,before;s=s.replace(before,after)
ast.parse(s);target=HERE/'observe_hpc.py';assert not target.exists()
with target.open('x',encoding='utf8') as f:f.write(s)
print('EXACT_EXISTING_OBSERVER_BOUND_TO_VERIFIED_ORIGINAL_HPC187081')
