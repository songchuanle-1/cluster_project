"""Independent stdlib CTS/BEC review helper: no Torch/module import or native claim."""
from pathlib import Path
import argparse, ast, copy, hashlib, json
from datetime import datetime, timezone
from types import SimpleNamespace

ROOT = Path(r'D:/project/cluster_project')
HERE = ROOT / 'pipeline/diagnostic_bundles/tick_6bdbcf77'
PREP = HERE / 'new_candidate_prepare/preparation.json'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

class ListRows:
    """Plain Python lists for production mean indexing only, not a Tensor."""
    device = 'metadata-only'
    def __init__(self, rows, channels):
        self.rows = copy.deepcopy(rows)
        self.channels = channels
        assert all(len(row) == channels for row in rows)
    def new_zeros(self, shape):
        assert len(shape) == 2 and shape[1] == self.channels
        return ListRows([[0.0] * shape[1] for _ in range(shape[0])], shape[1])
    def index_select(self, dim, ids):
        assert dim == 0
        return ListRows([self.rows[i] for i in ids], self.channels)
    def mean(self, dim):
        assert dim == 0 and self.rows
        return [sum(row[c] for row in self.rows) / len(self.rows)
                for c in range(self.channels)]
    def index_copy(self, dim, ids, values):
        assert dim == 0 and len(ids) == len(values.rows)
        out = ListRows(self.rows, self.channels)
        for i, row in zip(ids, values.rows):
            out.rows[i] = list(row)
        return out

class ListMetadata:
    long = 'metadata-int'
    @staticmethod
    def tensor(ids, dtype, device):
        assert dtype == 'metadata-int' and device == 'metadata-only'
        return list(ids)
    @staticmethod
    def stack(rows, dim):
        assert dim == 0 and rows
        return ListRows(rows, len(rows[0]))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-preparation-sha', required=True)
    args = parser.parse_args()
    assert sha(PREP) == args.expected_preparation_sha
    preparation = json.loads(PREP.read_text(encoding='utf-8'))
    files = preparation['source_files']
    source = next(x for x in files if x['path'].endswith('/bipartite_edges.py'))
    path = PREP.parent / source['prepared_path']
    text = path.read_text(encoding='utf-8')
    tree = ast.parse(text)
    plan_node = next(n for n in tree.body
                     if isinstance(n, ast.FunctionDef) and n.name == 'build_bipartite_plan')
    cls = next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == 'CrossLevelBipartiteEdgeComposition')
    mean_node = next(n for n in cls.body
                     if isinstance(n, ast.FunctionDef) and n.name == '_mean_messages')
    module = ast.Module(body=[copy.deepcopy(plan_node), copy.deepcopy(mean_node)],
                        type_ignores=[])
    ast.fix_missing_locations(module)
    environment = {'torch': ListMetadata}
    exec(compile(module, 'actual_BEC_plan_and_mean_AST_only', 'exec'), environment)
    build = environment['build_bipartite_plan']
    mean = environment['_mean_messages']
    self = SimpleNamespace(channels=3)
    cases = []
    assertions = 0
    def check(value):
        nonlocal assertions
        assert value
        assertions += 1
    def one(label, points, fine_parent, middle_parent, widths):
        p = build(points, fine_parent, middle_parent, widths)
        fs = sorted(set(points))
        ms = sorted({fine_parent[i] for i in fs})
        cs = sorted({middle_parent[i] for i in ms})
        check(p['fine_ids'] == tuple(fs))
        check(p['middle_ids'] == tuple(ms))
        check(p['coarse_ids'] == tuple(cs))
        check(p['fine_edges'] == tuple((i, fine_parent[i]) for i in fs))
        check(p['middle_edges'] == tuple((i, middle_parent[i]) for i in ms))
        check(p['fine_parent_ids'] == tuple(fine_parent[i] for i in fs))
        check(p['middle_parent_ids'] == tuple(middle_parent[i] for i in ms))
        check(p['widths'] == tuple(widths))
        # Arbitrary captured upward message rows indexed by original child ID.
        # Nonuniform point counts must NOT weight these child-token means.
        upward = {i: [float(100 * i + 7 * c + 1) for c in range(3)] for i in fs}
        rows0 = ListRows([upward[i] for i in fs], 3)
        untouched0 = copy.deepcopy(rows0.rows)
        actual1 = mean(self, rows0, p['fine_mean_groups'], widths[1])
        oracle1 = [[0.0] * 3 for _ in range(widths[1])]
        for parent in ms:
            children = [i for i in fs if fine_parent[i] == parent]
            oracle1[parent] = [sum(upward[i][c] for i in children) / len(children)
                               for c in range(3)]
        check(actual1.rows == oracle1)
        check(rows0.rows == untouched0)
        # Second-level message values depend on the actual first mean, but the
        # oracle groups by original middle IDs, never message-row positions.
        upward1 = {i: [3 * oracle1[i][c] + middle_parent[i] * 11 + c
                       for c in range(3)] for i in ms}
        rows1 = ListRows([upward1[i] for i in ms], 3)
        untouched1 = copy.deepcopy(rows1.rows)
        actual2 = mean(self, rows1, p['middle_mean_groups'], widths[2])
        oracle2 = [[0.0] * 3 for _ in range(widths[2])]
        for parent in cs:
            children = [i for i in ms if middle_parent[i] == parent]
            oracle2[parent] = [sum(upward1[i][c] for i in children) / len(children)
                               for c in range(3)]
        check(actual2.rows == oracle2)
        check(rows1.rows == untouched1)
        check(all(actual1.rows[i] == [0.0] * 3
                  for i in range(widths[1]) if i not in ms))
        check(all(actual2.rows[i] == [0.0] * 3
                  for i in range(widths[2]) if i not in cs))
        repeated = [i for i in fs for _ in range(1 + (i % 5))]
        check(build(repeated, fine_parent, middle_parent, widths) == p)
        cases.append({'label': label, 'true_fine': len(fs), 'true_middle': len(ms),
                      'true_coarse': len(cs), 'widths': widths})
    for n in range(129):
        k1 = (n + 3) // 4 if n else 0
        k2 = (k1 + 2) // 3 if k1 else 0
        f = [(i * 7 + 3) % k1 for i in range(n)] if k1 else []
        m = [(i * 5 + 1) % k2 for i in range(k1)] if k2 else []
        pts = [i for i in range(n) for _ in range(1 + i % 3)]
        one('all_supported_n' + str(n), pts, f, m, [n + 2, k1 + 2, k2 + 2])
    specials = [
        ('zero_widths', [], [], [], [0, 0, 0]),
        ('all_empty_padded', [], [2, 1, 0, 2], [1, 0, 1], [6, 5, 4]),
        ('holes_and_repeated_points', [7, 1, 7, 4, 1, 7], [3, 2, 3, 1, 0, 2, 3, 1],
         [2, 0, 2, 1], [10, 6, 5]),
        ('high_originalIDs', [11, 11, 9], [5] * 12, [3, 0, 3, 1, 0, 2], [14, 8, 6]),
        ('singleton_both_levels', [0, 0, 0], [0], [0], [3, 2, 2]),
        ('multiple_children_equal_mean_not_pointweighted',
         [0] * 9 + [1] + [2] * 3, [0, 0, 0], [1], [5, 3, 4]),
        ('different_parent_childdegrees', [0, 1, 2, 3, 4, 5],
         [0, 0, 0, 2, 3, 3], [2, 1, 2, 0], [8, 6, 5]),
    ]
    for values in specials:
        one(*values)
    invalid = [
        ([], [], [], [1, 2]), ([], [], [], [1, -1, 1]),
        ([], [], [], [True, 1, 1]), ([], [], [], [1.0, 1, 1]),
        (None, [], [], [1, 1, 1]), ([True], [0], [0], [1, 1, 1]),
        ([-1], [0], [0], [1, 1, 1]), ([0.0], [0], [0], [1, 1, 1]),
        ([0], [], [], [1, 1, 1]), ([1], [0], [0], [2, 1, 1]),
        ([0], [1], [0], [1, 1, 1]), ([0], [0], [1], [1, 1, 1]),
        ([], [0, 0], [0], [1, 1, 1]), ([], [0], [0, 0], [1, 1, 1]),
        ([0], [False], [0], [1, 1, 1]),
        ([0], [0], [-1], [1, 1, 1])
    ]
    for values in invalid:
        try:
            build(*values)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid metadata accepted: ' + repr(values))
    output = {
        'status': 'ACTUAL_PRODUCTION_BEC_PLAN_AND_TWO_MEANS_STDLIB_VALIDATED_NOT_NATIVE',
        'recorded_at': datetime.now(timezone.utc).isoformat(),
        'source_preparation': {'path': PREP.relative_to(ROOT).as_posix(),
                               'sha256': args.expected_preparation_sha},
        'helper': {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)},
        'executed_production_functions': ['build_bipartite_plan', '_mean_messages'],
        'valid_cases': len(cases), 'all_n_0_through_128_included': True,
        'special_cases': len(specials), 'invalid_metadata_cases_rejected': len(invalid),
        'assertions': assertions, 'cases': cases,
        'no_Torch_import': True, 'full_Tensor_forward_executed': False,
        'full_linear_GELU_autograd_FP32_resources': 'NOT_RUN',
        'scope': 'Actual production metadata plan and mean-row functions were extracted via AST. '
                 'Plain Python lists test original-ID/row grouping, two-level child-equal means, '
                 'repeated-point invariance, empty/unsupported/padded rows. '
                 'No Tensor, full model, data, train, backward, profiler or native claim.'
    }
    out = HERE / 'independent_review/bec_production_validation.json'
    assert not out.exists()
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'path': str(out), 'sha256': sha(out),
                      'valid_cases': len(cases), 'invalid_cases': len(invalid),
                      'assertions': assertions, 'native': 'NOT_RUN'}))

if __name__ == '__main__':
    main()
