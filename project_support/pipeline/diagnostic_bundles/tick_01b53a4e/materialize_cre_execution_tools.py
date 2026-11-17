"""Root-reviewed operational copy; preserve disabled author templates and all raw evidence."""
from pathlib import Path
from datetime import datetime,timezone
import ast,json
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent;SOURCE=HERE/'cre_admission_prepare';DEST=HERE/'cre_admission_execute'
FILES={'cre_evidence.py':'ae8a6ab7a0b759d0c046cdea827365c363289d2ac658486bf41b61a230eba9de','summarize_cre_actual.py':'7a9213ac3d62ad168e2d4d3493922256e0930346535169f1eb04e79038a0a833','fast_forward_tested_cre.py':'8414a61e8c88c816eb42db9641fa3ff95daee4f79602d20e31562d5823fd141e','evidence_bindings.json':'d17b2bc09590a2fe4b91a091f023a411757c3b4e495700367bfc067143ab7b76'}
guard();assert not DEST.exists()
assert sha(HERE/'cre_actual_independent_review.json')=='83b616377b904036b00f8be9afa16a773f1e59204b3c0cfd62067afd68f0842d'
for n,h in FILES.items():assert sha(SOURCE/n)==h,n
DEST.mkdir()
for n in FILES:
    data=(SOURCE/n).read_bytes()
    if n=='cre_evidence.py':
        assert data.count(b'DRAFT_EXECUTION_DISABLED=True')==1
        data=data.replace(b'DRAFT_EXECUTION_DISABLED=True',b'DRAFT_EXECUTION_DISABLED=False')
    if n.endswith('.py'):ast.parse(data)
    guard()
    with (DEST/n).open('xb') as f:f.write(data)
record={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'author_disabled_source_files':FILES,'materialized_files':{n:sha(DEST/n) for n in FILES},'only_enabled_difference':'cre_evidence DRAFT_EXECUTION_DISABLED True→False in this root operational copy only; all evidence/owner/source/resource/negative-preservation checks kept','actual_independent_review':{'path':(HERE/'cre_actual_independent_review.json').relative_to(ROOT).as_posix(),'sha256':sha(HERE/'cre_actual_independent_review.json')},'scope':'Root has reviewed these concrete four-result-bound helpers under existing project authorization. No gate/source/model change or operation executed by materialization.'}
guard()
with (DEST/'root_activation.json').open('x',encoding='utf8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
print('Reviewed operational copy materialized; author disabled templates unchanged.')
