"""Add the remaining reviewed root operations to the enabled sibling, no model change."""
from pathlib import Path
from datetime import datetime,timezone
import ast,json
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent;SOURCE=HERE/'cre_admission_prepare';DEST=HERE/'cre_admission_execute'
FILES={'admit_cre_queue.py':'6aa684477dd98f16d8c429afe4159894b20421d36bccca8c1ad0921c80c8e762','dispatch_cre_once.py':'cf6f95a6e1b3311370b5c13dbc0a3e7dfadecd21289b08a71ad8b13ba561140d'}
guard();assert (DEST/'root_activation.json').exists()
assert sha(HERE/'cre_actual_independent_review.json')=='83b616377b904036b00f8be9afa16a773f1e59204b3c0cfd62067afd68f0842d'
assert json.loads((HERE/'cre_root_ff_result.json').read_text('utf8'))['HEAD']=='d58576b396cfb54577652be972f3ffaffda508c9'
for n,h in FILES.items():
    assert sha(SOURCE/n)==h and not (DEST/n).exists();data=(SOURCE/n).read_bytes();ast.parse(data);guard()
    with (DEST/n).open('xb') as f:f.write(data)
guard()
with (DEST/'root_queue_tool_materialization.json').open('x',encoding='utf8') as f:json.dump({'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'frozen_author_files':FILES,'materialized_files':{n:sha(DEST/n) for n in FILES},'changes':'Exact copies; shared evidence module already reviewed/activated in root sibling. No evidence/gate/source/seed change.'},f,ensure_ascii=False,indent=2);f.write('\n')
print('Concrete queue and one-dispatch operations materialized, no operation executed yet.')
