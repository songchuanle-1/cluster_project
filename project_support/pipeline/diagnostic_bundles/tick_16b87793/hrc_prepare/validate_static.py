"""Read-only HRC static checks. Run with python -B; never imports torch."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import yaml

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
REPO = ROOT / 'Cluster'
prep = json.loads((OUT / 'preparation.json').read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for relative, expected in {**prep['original_control_hashes'], **prep['source_hashes']}.items():
    path = REPO / relative
    assert path.resolve().is_relative_to(REPO.resolve()) and sha(path) == expected, relative
control = REPO / 'framework/model/Quard_model' / prep['control_package']
variant = REPO / 'framework/model/Quard_model' / prep['new_package']
assert len(list(variant.glob('*.py'))) == 8
for path in variant.glob('*.py'):
    ast.parse(path.read_bytes(), filename=str(path))
    compile(path.read_bytes(), str(path), 'exec')
    if path.name not in ['hier_postprocess.py', 'refined_composition.py']:
        assert path.read_bytes() == (control / path.name).read_bytes()
old = ast.parse((control/'hier_postprocess.py').read_bytes())
new = ast.parse((variant/'hier_postprocess.py').read_bytes())
classes = lambda tree: {n.name:n for n in tree.body if isinstance(n,ast.ClassDef)}
a, b = classes(old), classes(new)
for cls in ['PointCloudPartitioner','SharedClusterBank','C2F_ClusterAttn_CTF_HCG','C2F_ClusterAttn_CTF_HCG_CSORT']:
    assert ast.dump(a[cls]) == ast.dump(b[cls]), cls
constructor = lambda cls: next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
assert ast.dump(constructor(a['C2F_ClusterAttn_CTF'])) == ast.dump(constructor(b['C2F_ClusterAttn_CTF']))
control_yaml = REPO / ('configs/Quard/ctf_hcg_csort/' + prep['control_package'] + '.yaml')
variant_yaml = REPO / ('configs/Quard/ctf_hcg_csort_hrc/' + prep['new_package'] + '.yaml')
assert control_yaml.read_bytes() == variant_yaml.read_bytes()
assert yaml.safe_load(control_yaml.read_text(encoding='utf-8')) == yaml.safe_load(variant_yaml.read_text(encoding='utf-8'))
assert 'torch' not in sys.modules
print(json.dumps({'static_checks':'PASS','sources':8,'native_smoke':'NOT_RUN','resources':'NOT_RUN','efficacy':'UNKNOWN'}))
