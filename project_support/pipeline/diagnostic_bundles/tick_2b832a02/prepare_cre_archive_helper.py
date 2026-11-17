"""Prepare one exact original CRE normal-terminal canonical archive helper."""
from pathlib import Path
import ast,json
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
guard();obs=HERE/'cre_end_and_slot_observation.json';v=json.loads(obs.read_text('utf8'))
assert v['owner']==EXPECTED and v['observation']['process']=={'pid':118189,'exists':False}
assert v['observation']['explicit_early_stop_lines']==['Early stopping at epoch 30: no improvement for 10 epochs (best=0.4961)']
assert v['reviewed_CRE_readonly_probe']['idle'] is True
source=ROOT/'pipeline/diagnostic_bundles/tick_0f02aaa2/archive_aef_normal_terminal.py'
s=source.read_text('utf8')
changes=[
    ('AEF','CRE'),('aef','cre'),('M216-CRE','M217-CRE'),
    ('0f02aaa25b1a4f6e9d27cf8da33b8ca1',EXPECTED['token']),
    ('56b2a96dc48cc8a88f0f7105527ef448113b1060','d58576b396cfb54577652be972f3ffaffda508c9'),
    ('759301','118189'),('20261027_124036','20261028_024115'),
    ('041074985258a51cf2a5629dcbf19f55fceb42c5255c78251c1fb9cc680ae9a9','0ab8d1bd7e518322c25ae36bb80344fb62f90c150e5ca09bd856cb53d0a6320b'),
    ('01ff5497bd7413d238c2e45f002aa5cccfda988eae11d7ac4c6267f3b26fe2ea',sha(obs)),
    ('epoch 23','epoch 30'),('23/50','30/50'),('23of50','30of50'),('0.4956','0.4961')]
for old,new in changes:
    assert old in s,old;s=s.replace(old,new)
ast.parse(s);target=HERE/'archive_cre_normal_terminal.py';assert not target.exists()
with target.open('x',encoding='utf8') as f:f.write(s)
record={'owner':EXPECTED,'source_helper':{'path':source.relative_to(ROOT).as_posix(),'sha256':sha(source)},
        'prepared_helper':{'path':target.relative_to(ROOT).as_posix(),'sha256':sha(target)},
        'actual_terminal_observation':{'path':obs.relative_to(ROOT).as_posix(),'sha256':sha(obs)},
        'changes':'Only exact original M217 identifiers/source/receipt/log/time and actual normal earlystop30/.4961 metadata. Canonical API and once/x-only/full-log/PID-match behavior unchanged.',
        'scope':'Prepared helper only, root execution NOT_RUN; no queue or lifecycle mutation.'}
with (HERE/'cre_archive_preparation.json').open('x',encoding='utf8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(record['prepared_helper']))
