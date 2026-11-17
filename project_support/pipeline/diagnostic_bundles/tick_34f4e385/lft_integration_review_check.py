"""Independent narrow LFT integration audit; never imports a model or runs its tests."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json

ROOT = Path('D:/project/cluster_project')
HERE = ROOT / 'pipeline/diagnostic_bundles/tick_34f4e385'
PACK = HERE / 'lft_candidate_prepare'
PREP_SHA = '1210502d2454513983554dacf80293f7cd85fbdb55949b39f34e50b8fd01be92'
BASE = ROOT / 'pipeline/diagnostic_bundles/tick_87f03f29/new_candidate_prepare'
CID = 'hierarchy-nonlinear-lifting-analysis-synthesis'
NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_lft'
MODEL = PACK / 'staged_repository/framework/model/Quard_model' / NAME
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
dump = lambda node: ast.dump(node, include_attributes=False)
checks = []


def check(name, value):
    checks.append({'check': name, 'passed': bool(value)})
    assert value, name


def methods(tree):
    return {(cls.name, item.name): item for cls in tree.body if isinstance(cls, ast.ClassDef)
            for item in cls.body if isinstance(item, ast.FunctionDef)}


def ref(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


prep = json.loads((PACK / 'preparation.json').read_text(encoding='utf-8'))
check('frozen_preparation_SHA', sha(PACK / 'preparation.json') == PREP_SHA)
check('candidate_and_counts', prep['candidate_id'] == CID and prep['experiment_id'] == 'M227-LFT'
      and prep['source_file_count'] == 9 and prep['model_file_count'] == 8)
check('prototype_NULL_reference18e', all(prep[key] is None for key in ('code_commit', 'source_commit', 'source_parent_commit'))
      and prep['base_reference_commit'] == '18e64b8d95ed0ba5c1053ead114c0f91a4b0c324')
for name, value in prep['prepared_file_hashes'].items():
    check('frozen_map:' + name, sha(PACK / name) == value)
baseprep = json.loads((BASE / 'preparation.json').read_text(encoding='utf-8'))
for name in ('__init__.py', 'backbone.py', 'dec.py', 'loss.py', 'network.py', 'sample_model.py'):
    expected = next(value for path, value in baseprep['source_files'].items() if path.endswith('/' + name))
    check('original_M95_bytes:' + name, sha(MODEL / name) == expected)
config = PACK / 'staged_repository' / prep['config']
check('native_YAML_original_a18_bytes', sha(config) == 'a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a')
original = PACK / 'original_m95_hier_postprocess.py.txt'
check('restored_original_M95_hier_pin', sha(original) == '7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f')
old = methods(ast.parse(original.read_text(encoding='utf-8')))
new = methods(ast.parse((MODEL / 'hier_postprocess.py').read_text(encoding='utf-8')))
check('same25hierarchy_method_names', old.keys() == new.keys() and len(old) == 25)
allowed = {('C2F_ClusterAttn_CTF', '__init__'), ('C2F_ClusterAttn_CTF', 'forward')}
check('other23_methods_rawbank_FPS_HCG_CSORT_unchanged', all(dump(old[key]) == dump(new[key]) for key in old if key not in allowed))
ctor_old, ctor_new = old['C2F_ClusterAttn_CTF', '__init__'], new['C2F_ClusterAttn_CTF', '__init__']
check('original_constructor_prefix_FFN_LN_order_preserved', len(ctor_new.body) == len(ctor_old.body) + 2
      and all(dump(a) == dump(b) for a, b in zip(ctor_old.body, ctor_new.body)))
extension = ast.unparse(ast.Module(body=ctor_new.body[len(ctor_old.body):], type_ignores=[]))
check('new_maps_under_CPU_fork_only', 'torch.random.fork_rng(devices=[])' in extension
      and 'self.nonlinear_lifting = NonlinearLiftingComposition(d_model)' in extension)
check('original_FFNs_registered_not_replaced', 'nn.Identity' not in ast.unparse(ctor_new))
forward = new['C2F_ClusterAttn_CTF', 'forward']
text = ast.unparse(forward)
check('three_original_LN_once_before_core', 'normalized = [self.cluster_ffn_norm[lvl](cluster_feats_list[lvl]) for lvl in range(self.num_scales)]' in text)
check('pass_original_FFNs_to_core_without_alias_registration', 'self.nonlinear_lifting(normalized, cluster_ids_list, self.cluster_ffn)' in text)
check('three_original_raw_skips_only', 'refined_cluster_feats = [cf + change for cf, change in zip(cluster_feats_list, delta)]' in text)
def suffix(node):
    for index, statement in enumerate(node.body):
        if isinstance(statement, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'point_message' for t in statement.targets):
            return [dump(item) for item in node.body[index:]]
    raise AssertionError('point-message suffix absent')
check('original_HCG_message_norm_mask_return_suffix', suffix(forward) == suffix(old['C2F_ClusterAttn_CTF', 'forward']))
helper_tree = ast.parse((MODEL / 'nonlinear_lifting.py').read_text(encoding='utf-8'))
helper = next(item for item in helper_tree.body if isinstance(item, ast.ClassDef) and item.name == 'NonlinearLiftingComposition')
helper_ctor = next(item for item in helper.body if isinstance(item, ast.FunctionDef) and item.name == '__init__')
maps = [node for node in ast.walk(helper_ctor) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'Linear']
check('four_default_C_to_C_new_maps', len(maps) == 4 and all([dump(arg) for arg in node.args] == [dump(ast.Name(id='channels', ctx=ast.Load()))] * 2 for node in maps))
check('core_does_not_register_caller_FFN', 'ffns' not in ast.unparse(helper_ctor) and 'cluster_ffn' not in ast.unparse(helper_ctor))
helper_forward = next(item for item in helper.body if isinstance(item, ast.FunctionDef) and item.name == 'forward')
calls = [node for node in ast.walk(helper_forward) if isinstance(node, ast.Call) and isinstance(node.func, ast.Subscript)
         and isinstance(node.func.value, ast.Name) and node.func.value.id == 'ffns']
check('each_original_FFN_called_once_on_supported_packed_rows', sorted(node.func.slice.value for node in calls) == [0, 1, 2])
check('no_feature_detach_in_lifting_forward', not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'detach' for node in ast.walk(helper_forward)))
protocol = (PACK / 'native_protocol.md').read_text(encoding='utf-8')
check('protocol_full_original_FFN_common_and_zero_legal', 'include all original FFN and three LayerNorm parameters' in protocol
      and 'exclude ONLY new dec.cluster_att.nonlinear_lifting' in protocol and 'Individual map/row/column/bias/call zeros are legal' in protocol)
check('package_not_modified_during_review', sha(PACK / 'preparation.json') == PREP_SHA
      and all(sha(PACK / name) == value for name, value in prep['prepared_file_hashes'].items()))
out = HERE / 'lft_integration_independent_review.json'
assert not out.exists()
report = {'schema_version': 1, 'recorded_at': datetime.now(timezone.utc).isoformat(),
    'status': 'STATIC_LFT_ORIGINAL_M95_INTEGRATION_REVIEWED_NOT_NATIVE_PASS', 'candidate_id': CID,
    'experiment_id': 'M227-LFT', 'code_commit': None, 'material_concerns': [],
    'anchors': {'preparation': ref(PACK / 'preparation.json'), 'source_manifest': ref(PACK / 'source_manifest.json'),
                'native_protocol': ref(PACK / 'native_protocol.md'), 'auditor': ref(Path(__file__))},
    'source_files_exact9': prep['source_files'], 'check_count': len(checks), 'checks': checks,
    'scope': 'Narrow frozen SHA/AST/byte integration audit only. MDC separately reviews lifting topology and software oracle. Original FFNs are called once each on packed true-supported rows, not on full padded 3D banks.',
    'not_run': ['author72_suite', 'production_forward', 'Torch', 'FP32', 'autograd', 'native', 'resources', 'Git', 'SSH', 'GPU', 'shared_write'],
    'actual_common_initialization_and_native_gradient': 'NOT_RUN', 'efficacy': 'UNKNOWN', 'novelty': 'UNKNOWN'}
out.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
print(json.dumps({'review': ref(out), 'check_count': len(checks), 'material_concerns': []}))
