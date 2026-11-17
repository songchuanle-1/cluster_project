"""Metadata-only port of the exact original-process end observer."""
from pathlib import Path
import ast
from anchor import ROOT,guard
HERE=Path(__file__).resolve().parent
guard();s=(ROOT/'pipeline/diagnostic_bundles/tick_2b832a02/observe_cre_end_and_slot.py').read_text('utf8')
changes=[('CRE','HPC'),('cre','hpc'),('M217-HPC','M218-HPC'),('118189','187081'),
         ('d58576b396cfb54577652be972f3ffaffda508c9','6282263d805c1741234f97afc981a05aca2ad6e3'),
         ('tick_01b53a4e/hpc_root_ff_result.json','tick_2b832a02/hpc_root_ff_result.json'),
         ('tick_ab79f632/hpc_training_progress_observation.json','tick_2b832a02/hpc_training_progress_observation_final.json')]
for a,b in changes:
    assert a in s,a;s=s.replace(a,b)
ast.parse(s);p=HERE/'observe_hpc_end_and_slot.py';assert not p.exists()
with p.open('x',encoding='utf8') as f:f.write(s)
print('EXACT_ORIGINAL_HPC_END_OBSERVER_PREPARED_NO_REMOTE_ACTION_YET')
