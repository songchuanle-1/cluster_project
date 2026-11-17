"""Source-bound diagnostic reference; never edits production source."""
import ast
import copy
import hashlib
from pathlib import Path

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8388608), b''): h.update(b)
    return h.hexdigest()

def build(source, expected, torch):
    assert sha(source) == expected
    tree = ast.parse(Path(source).read_text())
    original = next(f for c in tree.body if isinstance(c, ast.ClassDef) and c.name == 'C2F_ClusterAttn_CTF_HCG'
                    for f in c.body if isinstance(f, ast.FunctionDef) and f.name == '_cluster_to_points')
    changed = copy.deepcopy(original)
    indices = [i for i, s in enumerate(changed.body) if isinstance(s, ast.Assign) and
               any(isinstance(t, ast.Name) and t.id == 'global_mean' for t in s.targets)]
    assert len(indices) == 1
    index = indices[0]
    assert ast.unparse(changed.body[index]) == 'global_mean = point_feats.mean(dim=1, keepdim=True).expand_as(point_feats)'
    replacement = ast.parse('''
_valid_count = (~point_mask).sum(dim=1, keepdim=True).unsqueeze(-1)
_masked_mean = point_feats.masked_fill(point_mask.unsqueeze(-1), 0).sum(dim=1, keepdim=True) / _valid_count.clamp_min(1)
global_mean = torch.where(_valid_count == point_feats.shape[1], point_feats.mean(dim=1, keepdim=True), _masked_mean).expand_as(point_feats)
''').body
    changed.body[index:index+1] = replacement
    assert ast.dump(ast.Module(body=original.body[:index], type_ignores=[])) == ast.dump(ast.Module(body=changed.body[:index], type_ignores=[]))
    assert ast.dump(ast.Module(body=original.body[index+1:], type_ignores=[])) == ast.dump(ast.Module(body=changed.body[index+3:], type_ignores=[]))
    def compile_one(f):
        scope = {'torch': torch}
        module = ast.fix_missing_locations(ast.Module(body=[f], type_ignores=[]))
        exec(compile(module, str(source), 'exec'), scope)
        return scope['_cluster_to_points']
    return compile_one(original), compile_one(changed), {
        'source_sha256': expected, 'diagnostic_reference_revision': 1,
        'original_ast_sha256': hashlib.sha256(ast.dump(original).encode()).hexdigest(),
        'reference_ast_sha256': hashlib.sha256(ast.dump(changed).encode()).hexdigest(),
        'only_global_mean_assignment_changed': True, 'production_modified': False}
