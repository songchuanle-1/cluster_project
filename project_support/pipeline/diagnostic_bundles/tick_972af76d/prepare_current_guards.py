"""Reuse existing reviewed guard implementations; preserve original tool packets."""
from pathlib import Path
import ast
from anchor import ROOT, guard
HERE=Path(__file__).resolve().parent
OLD=ROOT/'pipeline/diagnostic_bundles/tick_f395f943'
guard()
for name in ['cre','hpc']:
    source=(OLD/('check_'+name+'_current_guard.py')).read_text('utf8')
    source=source.replace('cre_f395_original_adapter','cre_972a_original_adapter').replace('hpc_f395_reviewed_adapter','hpc_972a_reviewed_adapter')
    if name=='hpc':
        source=source.replace("OP=HERE/'hpc_operational_prepare'", "OP=ROOT/'pipeline/diagnostic_bundles/tick_f395f943/hpc_operational_prepare'")
    ast.parse(source)
    guard()
    with (HERE/('check_'+name+'_current_guard.py')).open('x',encoding='utf8') as f: f.write(source)
