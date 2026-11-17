"""BTC harness AST/topology/observer-stub checks only; no torch or native import."""
import ast
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

ROOT = Path('D:/project/cluster_project')
TICK = ROOT/'pipeline/diagnostic_bundles/tick_7dcc29e8'
NATIVE = TICK/'btc_operational_prepare/native'
OLD = ROOT/'pipeline/diagnostic_bundles/tick_42ce600b/psnc_operational_prepare/native'
MODEL = ROOT/'pipeline/diagnostic_bundles/tick_2c25f38f/new_candidate_prepare/staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc/middle_tree.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function(tree, name):
    return next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == name)


def extract(nodes, namespace):
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<actual-function-AST>', 'exec'), namespace)


def main():
    checks = {}
    worker_source = (NATIVE/'worker.py').read_text(encoding='utf-8')
    runtime_source = (NATIVE/'native_runtime.py').read_text(encoding='utf-8')
    compile(worker_source, str(NATIVE/'worker.py'), 'exec')
    compile(runtime_source, str(NATIVE/'native_runtime.py'), 'exec')
    checks['both_actual_sources_compile_without_import'] = True
    worker, runtime = ast.parse(worker_source), ast.parse(runtime_source)
    old_worker = ast.parse((OLD/'worker.py').read_text(encoding='utf-8'))
    old_runtime = ast.parse((OLD/'native_runtime.py').read_text(encoding='utf-8'))
    assert ast.dump(function(worker, 'resources')) == ast.dump(function(old_worker, 'resources'))
    checks['resources_full_function_AST_exact_original_PSNC'] = True
    for name in ('sha', 'verify', 'observe', 'acquire', 'release', 'fingerprint', 'save'):
        assert ast.dump(function(runtime, name)) == ast.dump(function(old_runtime, name))
    checks['seven_runtime_safety_utility_AST_exact_original'] = True
    assert "CANDIDATE_COMMIT = '00e2b18c6b8d568a64edb496e6979d766440883c'" in runtime_source
    assert "version['parent_commit'] == '43dce016c1a1713c2a5dab7061810dc2efde8954'" in runtime_source
    assert "version['original_source_preparation_sha256'] == MANIFEST['source_preparation_sha256']" in runtime_source
    assert "PHYSICAL_GPU == 0" in runtime_source and "'btc_' + MANIFEST['current_token'][:8]" in runtime_source
    checks['BTC_version_parent_preparation_stage_GPU0_literals'] = True
    main_node = function(worker, 'main')
    acquire_call = next(x for x in ast.walk(main_node) if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == 'acquire')
    setup_call = next(x for x in ast.walk(main_node) if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == 'setup')
    assert acquire_call.lineno < setup_call.lineno
    assert not any(isinstance(x, (ast.Import, ast.ImportFrom)) and 'torch' in ast.unparse(x) for x in worker.body)
    checks['acquire_precedes_native_torch_setup_no_module_torch_import'] = True
    prefixes = ('dec.cluster_att.cluster_ffn.1.', 'dec.cluster_att.middle_tree.')
    names = ['dec.cluster_att.cluster_ffn.1.0.weight', 'dec.cluster_att.middle_tree.inside.weight',
             'dec.cluster_att.cluster_ffn_norm.1.weight', 'dec.cluster_att.cluster_ffn.0.0.weight']
    assert [n for n in names if not n.startswith(prefixes)] == names[2:]
    assert all(p in ast.unparse(function(worker, 'setup')) for p in prefixes)
    checks['common_prefix_exclusion_retains_middle_LayerNorm'] = True
    model_tree = ast.parse(MODEL.read_text(encoding='utf-8'))
    namespace = {'math': math}
    extract([function(model_tree, 'build_parent_forest'), function(worker, 'forest_observation')], namespace)
    build, observe = namespace['build_parent_forest'], namespace['forest_observation']
    cases = [([], [], []), ([[0., 0., 0.]], [0], [True]),
             ([[0., 0., 0.], [1., 0., 0.]], [0, 0], [True, True]),
             ([[0., 0., 0.], [1., 0., 0.], [2., 0., 0.]], [0, 0, 0], [True]*3),
             ([[0., 0., 0.]]*5, [0]*5, [True]*5),
             ([[float(i), 2.*i, 0.] for i in range(8)], [4, 2, 4, 2, 4, 2, 4, 2], [True, True, False, True, True, False, True, True])]
    case_counts = []
    for centers, parents, supported in cases:
        groups, plan = observe(build(centers, parents, supported, 64))
        case_counts.append([g['n'] for g in groups])
        for group in groups:
            calls = [x for x in plan if x['parent'] == group['parent']]
            for kind in ('inside', 'outside', 'leaf'):
                assert sum(x['map'] == kind for x in calls) == group['expected_'+kind+'_calls']
            assert not any(x['map'] == 'inside' and x['node'] == group['root'] for x in calls)
            for x in calls:
                if x['map'] == 'leaf':
                    assert x['input_source_ids'][0] == [x['node']]
                    assert set(x['input_source_ids'][1]) == set(group['original_middle_ids'])-{x['node']}
    checks['actual_production_topology_to_observer_plan_n0_n1_n2_n3_ties_parentholes'] = True

    # Execute actual observer hook function AST on simple Python vector stubs.
    # This tests reference bookkeeping/GELU ordering, never torch tensor behavior.
    class BoolVector:
        def __init__(self, values): self.values = values
        def all(self): return all(self.values)
    class Vector:
        def __init__(self, values): self.values = tuple(values); self.shape = (len(values),); self.requires_grad = True
        def __getitem__(self, key): return Vector(self.values[key])
        def detach(self): return self
        def eq(self, value): return BoolVector([x == value for x in self.values])
    def fingerprint(_torch, value): return hashlib.sha256(repr(value.values).encode()).hexdigest()
    def summary(value): return {'finite': all(math.isfinite(x) for x in value.values), 'shape': list(value.shape)}
    def watch(value, record, key):
        assert value.requires_grad
        record.setdefault('registered_stub_watch_keys', []).append(key)
    forest = build([[0.,0.,0.],[1.,0.,0.],[2.,0.,0.]], [0,0,0], [True]*3, 64)
    groups, plan = observe(forest)
    for item in plan: item['batch'] = 0
    values = {(0, 0, 'inside', token): Vector([token+1., token+2.]) for token in range(3)}
    values[(0, 0, 'outside', groups[0]['root'])] = None
    context = {'pending': None, 'pending_activation': None, 'plan': plan, 'plan_index': 0,
               'values': values, 'record': {'map_calls': []}}
    state = {'tree_context': context, 'forward_index': 1}
    env = {'state': state, 'att': SimpleNamespace(middle_tree=SimpleNamespace(channels=2)),
           'torch': object(), 'fingerprint': fingerprint, 'summary': summary, 'watch': watch}
    smoke = function(worker, 'smoke')
    nodes = [next(n for n in ast.walk(smoke) if isinstance(n, ast.FunctionDef) and n.name == name)
             for name in ('map_pre', 'map_post', 'activation_post')]
    extract(nodes, env)
    for index, item in enumerate(plan):
        inputs = []
        for kind, node in item['input_refs']:
            value = context['values'][(0, item['parent'], kind, node)]
            inputs.extend([0., 0.] if value is None else value.values)
        value, linear_output = Vector(inputs), Vector([index+.3, index+.7])
        env['map_pre'](item['map'])(None, (value,))
        env['map_post'](item['map'])(None, (value,), linear_output)
        if item['map'] != 'leaf':
            key = (0, item['parent'], item['map'], item['node'])
            assert key not in context['values']
            activated_output = Vector([11.+index, 21.+index])
            env['activation_post'](None, (linear_output,), activated_output)
            assert fingerprint(None, context['values'][key]) == fingerprint(None, activated_output)
            assert fingerprint(None, context['values'][key]) != fingerprint(None, linear_output)
    assert context['plan_index'] == len(plan) and context['pending'] is context['pending_activation'] is None
    assert all(x['actual_input_sources_exact'] for x in context['record']['map_calls'])
    checks['actual_observer_hooks_store_original_activation_not_preactivation_without_replay'] = True
    assert 'INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_N_GE3_PARENT' in worker_source
    assert "for g in call[key])" in worker_source
    checks['coverage_inconclusive_and_per_call_finite_only_scope_preserved'] = True
    proof = json.loads((NATIVE/'source_version_binding.json').read_text(encoding='utf-8'))
    assert proof['code_commit'] == '00e2b18c6b8d568a64edb496e6979d766440883c'
    assert proof['parent_commit'] == '43dce016c1a1713c2a5dab7061810dc2efde8954'
    assert proof['original_source_preparation_sha256'] == 'c36b4d095ee3d48510a1064f699b2fe41be33569aaefb917d873a45c484d0814'
    checks['root_provided_version_binding_interface_matches_runtime'] = True
    result = {'schema_version': 1, 'status': 'STATIC_AST_TOPOLOGY_AND_OBSERVER_STUB_CHECKS_PASSED_NATIVE_NOT_RUN',
              'checks': checks, 'logical_check_count': len(checks), 'topology_cases_supported_group_sizes': case_counts,
              'source_hashes': {name: sha(NATIVE/name) for name in ['worker.py','native_runtime.py']},
              'source_version_binding_sha256': sha(NATIVE/'source_version_binding.json'),
              'scope': 'Actual function AST and Python scalar/vector stubs only; no torch/module/runtime import, no native forward/backward, no GPU/SSH/model/Git/shared mutation.',
              'native_execution': 'NOT_RUN', 'resources': 'NOT_RUN',
              'unknowns': ['real tensor shape/autograd/numeric behavior', 'real n>=3 TRAIN coverage', 'real common initialization and batch pairing', 'true empty/padding/singleton native coverage', 'actual latency/VRAM/FLOPs', 'efficacy']}
    path = Path(__file__).with_name('static_validation.json')
    with path.open('x', encoding='utf-8') as stream: json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({'report': str(path), 'sha256': sha(path), 'logical_check_count': len(checks), 'source_hashes': result['source_hashes']}))


if __name__ == '__main__':
    main()
