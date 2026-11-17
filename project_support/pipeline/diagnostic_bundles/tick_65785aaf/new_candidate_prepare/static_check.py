"""Small actual-production metadata/forward software checks, never Torch/native."""
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
import ast
import hashlib
import itertools
import json
import math

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/project/cluster_project')
NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cre'
MODEL = HERE / 'staged_repository/framework/model/Quard_model' / NAME
BASE = ROOT / 'Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
CONFIG = 'configs/Quard/ctf_hcg_csort_cre/' + NAME + '.yaml'


class Value:
    """Generic scalar-list tensor stand-in, not PyTorch or GELU/gradient proof."""
    device = 'stdlib'; dtype = 'float'
    def __init__(self, data, shape):
        self.data, self.shape = list(data), tuple(shape)
        assert len(self.data) == math.prod(self.shape)
    @property
    def ndim(self): return len(self.shape)
    def detach(self): return self
    def cpu(self): return self
    def tolist(self):
        if self.ndim == 1: return list(self.data)
        width = math.prod(self.shape[1:])
        return [Value(self.data[i * width:(i + 1) * width], self.shape[1:]).tolist() for i in range(self.shape[0])]
    def reshape(self, *shape):
        if len(shape) == 1 and isinstance(shape[0], tuple): shape = shape[0]
        return Value(self.data, shape)
    def new_zeros(self, shape): return Value([0] * math.prod(shape), shape)
    def index_select(self, dim, index):
        assert dim == 0
        width = math.prod(self.shape[1:])
        return Value([x for i in index.data for x in self.data[i * width:(i + 1) * width]], (len(index.data), *self.shape[1:]))
    def index_copy(self, dim, index, source):
        assert dim == 0
        width = math.prod(self.shape[1:]); out = list(self.data)
        assert source.shape == (len(index.data), *self.shape[1:])
        for row, i in enumerate(index.data): out[i * width:(i + 1) * width] = source.data[row * width:(row + 1) * width]
        return Value(out, self.shape)
    def mean(self, dim):
        assert dim == 0 and self.ndim == 2 and self.shape[0]
        rows = self.tolist()
        return Value([sum(row[c] for row in rows) / len(rows) for c in range(self.shape[1])], (self.shape[1],))


class ListTorch:
    long = 'int'
    @staticmethod
    def tensor(values, **kwargs): return Value(values, (len(values),))
    @staticmethod
    def cat(values, dim):
        assert dim == -1 and all(v.ndim == 2 and v.shape[0] == values[0].shape[0] for v in values)
        rows = [v.tolist() for v in values]
        return Value([x for r in range(values[0].shape[0]) for field in rows for x in field[r]], (values[0].shape[0], sum(v.shape[1] for v in values)))
    @staticmethod
    def stack(values, dim):
        assert dim == 0 and values and all(v.shape == values[0].shape for v in values)
        return Value([x for v in values for x in v.data], (len(values), *values[0].shape))


def main():
    checks = []; sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    def check(name, value):
        assert value, name
        checks.append({'name': name, 'passed': True})
    for p in sorted(MODEL.glob('*.py')):
        compile(p.read_bytes(), str(p), 'exec')
        check('AST+compile ' + p.name, True)
    helper = ast.parse((MODEL / 'root_exchange.py').read_bytes())
    cls = next(n for n in helper.body if isinstance(n, ast.ClassDef))
    namespace = {'torch': ListTorch}
    nodes = [n for n in helper.body if isinstance(n, ast.FunctionDef)]
    forward = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'forward')
    exec(compile(ast.Module(body=nodes + [forward], type_ignores=[]), 'actual_CRE_production_functions', 'exec'), namespace)
    plan = namespace['build_root_exchange_plan']
    cases = [([], [], [], (0, 0, 0)), ([0], [0], [2], (3, 2, 4)),
             ([0, 2, 2], [0, 1, 2], [0, 1, 2], (4, 4, 4)),
             ([0, 1, 2], [0, 1, 2], [0, 1, 2], (4, 4, 4)),
             (list(range(8)), list(range(8)), list(range(8)), (8, 8, 8)),
             ([], [0, 1, 2], [0, 1, 2], (4, 4, 4))]
    for index, args in enumerate(cases):
        p = plan(*args); point, f2m, m2c, widths = args
        expected_roots = sorted({m2c[f2m[i]] for i in point})
        check('true composed support / topology case' + str(index), p['coarse_roots'] == expected_roots and p['fine_ids'] == sorted(set(point)))
        edges = [tuple(row) for row in p['work_rows'] if row[1] is not None]
        check('exact cross-root directed graph / case' + str(index), set(edges) == set(itertools.permutations(expected_roots, 2)) and len(edges) == p['real_directed_edge_count'])
        check('every fine/middle recipient original ancestor / case' + str(index), p['fine_rows'] == [(i, m2c[f2m[i]]) for i in sorted(set(point))] and all(parent in expected_roots for i, parent in p['middle_rows']))
    p = plan([0, 2, 2], [0, 1, 2], [0, 1, 2], (4, 4, 4))
    check('holes never inserted or renumbered', p['work_rows'] == [(0, 2), (2, 0)] and p['fine_rows'] == [(0, 0), (2, 2)])
    invalid = [([True], [0], [0], (1, 1, 1)), ([-1], [0], [0], (1, 1, 1)), ([1], [0], [0], (1, 1, 1)),
               ([0], [1], [0], (1, 1, 1)), ([0], [0], [1], (1, 1, 1)), ([], [0], [], (1, 0, 1)),
               ([], [], [], (1, 2)), ([], [], [], (True, 1, 1))]
    for i, args in enumerate(invalid):
        try: plan(*args)
        except ValueError: check('malformed metadata rejected' + str(i), True)
        else: raise AssertionError('Invalid metadata accepted')
    # Execute actual forward with opaque list-tensor mechanics and tagged affine
    # maps plus square stand-in. Fixed literal results check graph wiring; these
    # maps/activation are deliberately not the real Linear/GELU or native proof.
    class Map:
        def __init__(self, role): self.role, self.calls = role, []
        def __call__(self, value):
            self.calls.append(value.tolist()); a, b = {'U': (1, 2), 'D0': (1, 3), 'D1': (2, 1)}[self.role]
            return Value([a * row[0] + b * row[1] for row in value.tolist()], (value.shape[0], 1))
    def owner(): return SimpleNamespace(d_model=1, capacities=(8, 8, 8), coarse_edge=Map('U'), fine_decode=Map('D0'), middle_decode=Map('D1'), activation=lambda v: Value([x * x for x in v.data], v.shape))
    def ids(*levels): return [[Value(level, (len(level),))] for level in levels]
    features = [Value([2, 99, 7, 88], (1, 4, 1)), Value([4, 77, 6, 66], (1, 4, 1)), Value([1, 55, 3, 44], (1, 4, 1))]
    old = [list(v.data) for v in features]; o = owner()
    out = namespace['forward'](o, features, ids([0, 2, 2], [0, 1, 2], [0, 1, 2]))
    check('actual forward root orientation and direct unskipped-message synthesis', [v.data for v in out] == [[22201, 0, 6724, 0], [3249, 0, 1369, 0], [49, 0, 25, 0]])
    check('all inputs unchanged; U/D0/D1 each one batched call', [v.data for v in features] == old and [len(m.calls) for m in (o.coarse_edge, o.fine_decode, o.middle_decode)] == [1, 1, 1] and o.coarse_edge.calls[0] == [[1, 3], [3, 1]])
    o = owner(); features[2] = Value([99, 55, 3, 44], (1, 4, 1))
    out = namespace['forward'](o, features, ids([0], [0], [2]))
    check('actual singleton sender is privatezero not realID0', o.coarse_edge.calls == [[[3, 0]]] and [v.data for v in out] == [[841, 0, 0, 0], [289, 0, 0, 0], [0, 0, 9, 0]])
    o = owner(); features[2] = Value([1, 2, 4, 99], (1, 4, 1))
    out = namespace['forward'](o, features, ids([0, 1, 2], [0, 1, 2], [0, 1, 2]))
    check('actual fixed equal mean of post-nonlinearity edge outputs', out[2].data == [53, 58, 50, 0] and len(o.coarse_edge.calls[0]) == 6)
    o = owner(); out = namespace['forward'](o, features, ids([], [0, 1, 2], [0, 1, 2]))
    check('actual all-empty support has no map/bias work and zero deltas', all(v.data == [0] * 4 for v in out) and not any(m.calls for m in (o.coarse_edge, o.fine_decode, o.middle_decode)))
    base_tree = ast.parse((BASE / 'hier_postprocess.py').read_bytes()); new_tree = ast.parse((MODEL / 'hier_postprocess.py').read_bytes())
    def methods(t): return {c.name + '.' + f.name: f for c in t.body if isinstance(c, ast.ClassDef) for f in c.body if isinstance(f, ast.FunctionDef)}
    before, after = methods(base_tree), methods(new_tree); dump = lambda n: ast.dump(n, include_attributes=False)
    changed = {n for n in before if dump(before[n]) != dump(after[n])}
    check('only original CTF init/forward changed; all rawbank/FPS/CSORT/HCG methods preserved', set(before) == set(after) and changed == {'C2F_ClusterAttn_CTF.__init__', 'C2F_ClusterAttn_CTF.forward'})
    prefix = len(before['C2F_ClusterAttn_CTF.__init__'].body)
    check('original constructor sequence before newmodule preserved', all(dump(a) == dump(b) for a, b in zip(before['C2F_ClusterAttn_CTF.__init__'].body, after['C2F_ClusterAttn_CTF.__init__'].body[:prefix])))
    check('six original independent files byte-identical including full decoder', all((MODEL / n).read_bytes() == (BASE / n).read_bytes() for n in ['__init__.py', 'backbone.py', 'dec.py', 'loss.py', 'network.py', 'sample_model.py']))
    check('original native YAML byte-identical', sha(HERE / 'staged_repository' / CONFIG) == 'a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a')
    code = (MODEL / 'hier_postprocess.py').read_text('utf8')
    check('CPU fork only/no new seed; three original skips/LNs', 'torch.random.fork_rng(devices=[])' in code and 'manual_seed' not in code and 'cluster_feats_list[lvl] + deltas[lvl]' in code and 'self.cluster_ffn_norm[lvl](cluster_feats_list[lvl])' in code)
    c = 256
    check('source-only parameter arithmetic', 3 * (2 * c * c + c) == 393984 and 3 * (8 * c * c + 5 * c) == 1576704 and 1576704 - 393984 == 1182720)
    result = {'status': 'STDLIB_PRODUCTION_PATH_CHECKS_PASSED_NOT_TORCH_NATIVE_PASS', 'recorded_at': datetime.now(timezone.utc).isoformat(), 'checks': checks, 'check_count': len(checks), 'valid_metadata_cases': len(cases), 'invalid_metadata_cases': len(invalid), 'actual_forward_list_standin_cases': 4, 'source_helper_sha256': sha(MODEL / 'root_exchange.py'), 'source_hierarchy_sha256': sha(MODEL / 'hier_postprocess.py'), 'scope': 'Actual production plan/mean/forward AST executed with scalar list-tensor stand-ins and deliberately non-native tagged maps/square activation. Tests wiring, indices, zero boundaries and arithmetic only; no Torch/GELU/autograd/FP32/resource/accuracy or initialization-pairing claim.', 'Git_SSH_GPU_Torch_shared_writes': False}
    with (HERE / 'static_validation_final.json').open('x', encoding='utf8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({'checks': len(checks), 'sha256': sha(HERE / 'static_validation_final.json')}))


if __name__ == '__main__': main()
