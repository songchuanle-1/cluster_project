"""Reuse the established exact process/log/source observer for the new original CRE run."""
from pathlib import Path
import ast
from anchor import ROOT,guard
HERE=Path(__file__).resolve().parent
guard();s=(ROOT/'pipeline/diagnostic_bundles/tick_0f02aaa2/observe_aef.py').read_text('utf8')
changes=[('AEF','CRE'),('PID=759301','PID=118189'),("COMMIT='56b2a96dc48cc8a88f0f7105527ef448113b1060'","COMMIT='d58576b396cfb54577652be972f3ffaffda508c9'"),('M216-AEF','M217-CRE'),('pipeline/diagnostic_bundles/tick_458bf62f/aef_root_ff_result.json','pipeline/diagnostic_bundles/tick_01b53a4e/cre_root_ff_result.json'),('aef_training_progress_observation.json','cre_training_progress_observation.json')]
# The first uppercase substitution already renamed the experiment suffix.
for old,new in changes:
    if old=='M216-AEF':old='M216-CRE'
    assert old in s,old
    s=s.replace(old,new)
old="values,best,missed=mon.parse_native_lineage(lines,resumed=False)"
assert old in s;s=s.replace(old,old+"\n  if not values:best=None;missed=None")
ast.parse(s);guard()
with (HERE/'observe_cre.py').open('x',encoding='utf8') as f:f.write(s)
