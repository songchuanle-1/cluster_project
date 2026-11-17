"""Small CRE native-observer contract checks, never Torch/model/native/remote."""
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
import ast
import copy
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/project/cluster_project')
REFERENCE = ROOT / 'pipeline/diagnostic_bundles/tick_05f6addd/aef_native_prepare'


def main():
    checks = []
    def need(name, value):
        assert value, name
        checks.append({'name': name, 'passed': True})
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    worker = ast.parse((HERE / 'worker.py').read_bytes())
    runtime = ast.parse((HERE / 'native_runtime.py').read_bytes())
    old_worker = ast.parse((REFERENCE / 'worker.py').read_bytes())
    old_runtime = ast.parse((REFERENCE / 'native_runtime.py').read_bytes())
    function = lambda tree, name: next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    nested = lambda name: next(n for n in ast.walk(worker) if isinstance(n, ast.FunctionDef) and n.name == name)
    dump = lambda node: ast.dump(node, include_attributes=False)
    for path in [HERE / 'worker.py', HERE / 'native_runtime.py', *sorted((HERE / 'candidate_model').glob('*.py'))]:
        compile(path.read_bytes(), str(path), 'exec')
        need('AST+compile ' + path.name, True)
    need('whole original resources AST unchanged', dump(function(worker, 'resources')) == dump(function(old_worker, 'resources')))
    for name in ['sha', 'verify_source_version', 'verify', 'observe', 'acquire', 'release', 'fingerprint', 'save']:
        need('generic runtime exact AST ' + name, dump(function(runtime, name)) == dump(function(old_runtime, name)))
    normalized = ast.parse((HERE / 'native_runtime.py').read_text('utf8').replace('CRE', 'AEF'))
    need('version guard only diagnostic label renamed', dump(function(normalized, 'require_promoted_version')) == dump(function(old_runtime, 'require_promoted_version')))
    manifest = json.loads((HERE / 'manifest_template.json').read_text('utf8'))
    binding = json.loads((HERE / 'source_version_binding.json').read_text('utf8'))
    active = ['current_token', 'stage', 'tick_generated_at', 'deadline_at', 'physical_gpu', 'gpu_uuid', 'allowed_gpus', 'context_sha256', 'pending_sha256', 'runtime_code_commit']
    need('ten active fields null/no execution files', all(manifest[k] is None for k in active) and not any((HERE / name).exists() for name in ['native_manifest.json', 'execution_binding.json', 'execution_lease.json']))
    need('version-bound7ed parent/runtime026c capability', manifest['draft_execution_disabled'] is False and manifest['code_commit'] == '7ed9373db335d44c884133da3eced3fca03ad29a' and manifest['source_parent_commit'] == manifest['runtime_expected_commit'] == '026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563')
    need('twelve stage payload hashes exact', len(manifest['diagnostic_files']) == 12 and all(sha(HERE / n) == h for n, h in manifest['diagnostic_files'].items()))
    need('actual source proof/peer refs exact', all(sha(ROOT / binding[k]['path']) == binding[k]['sha256'] for k in ['isolated_source_version', 'isolated_source_version_independent_review']))
    source = json.loads((ROOT / 'pipeline/diagnostic_bundles/tick_65785aaf/new_candidate_prepare/source_manifest.json').read_text('utf8'))
    need('all original c760 nine source/YAML bytes', binding['source_files'] == source['source_files'] and sha(HERE / 'candidate.yaml') == source['native_YAML_sha256'] and all(sha(HERE / 'candidate_model' / n) == h for n, h in binding['candidate_source_hashes'].items()))
    # Execute only actual pure metadata observer functions, with four small
    # production plans. This is not a rerun of the prior source46 suite.
    helper = ast.parse((HERE / 'candidate_model/root_exchange.py').read_bytes())
    namespace = {'copy': copy}
    nodes = [function(helper, 'build_root_exchange_plan'), function(worker, 'cre_plan_observation'), function(worker, 'cre_coverage_preflight')]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'actual_CRE_observer_metadata', 'exec'), namespace)
    cases = [([], [], [], [0, 0, 0]), ([0], [0], [2], [2, 2, 4]), ([0, 2], [0, 1, 2], [0, 1, 2], [4, 4, 4]), ([0, 1, 2], [0, 1, 2], [0, 1, 2], [4, 4, 4])]
    for i, args in enumerate(cases):
        plan = namespace['build_root_exchange_plan'](*args); before = copy.deepcopy(plan)
        observed = namespace['cre_plan_observation'](plan)
        coverage = namespace['cre_coverage_preflight']([tuple(args[:3])])
        need('actual plan observer nonmutating/core coverage case' + str(i), plan == before == observed and coverage['real_cross_root_path_possible'] is (len(plan['coarse_roots']) >= 2))
    coverage = namespace['cre_coverage_preflight']([([0], [0], [2]), ([0, 1], [0, 1], [0, 1])])
    need('singleton scene legal if batch contains another cross-root scene', coverage['real_cross_root_path_possible'] is True and coverage['potential_real_directed_edges'] == 2)
    bad = namespace['build_root_exchange_plan'](*cases[2]); bad['work_rows'][0] = (0, 0)
    try: namespace['cre_plan_observation'](bad)
    except AssertionError: need('malformed actual observer edge identity refused', True)
    else: raise AssertionError('Self-edge passed observer')
    # Actual mean wrapper control flow with opaque stdlib values. The stub
    # original returns an object; no numerical mean/Tensor operation is executed.
    class Value:
        device = 'stdlib'
        def __init__(self, tag, shape): self.tag, self.shape = tag, shape
        def detach(self): return self
        def clone(self): return Value(self.tag, self.shape)
        def new_zeros(self, shape): return Value('zero', shape)
        def index_copy(self, dim, index, value):
            assert dim == 0
            return Value('copied:' + value.tag, self.shape)
    messages = Value('actual-U-GELU', (2, 1)); output = Value('actual-mean', (2, 1)); groups = [[0], [1]]
    context = {'phase': 'await_mean', 'mean_count': 0, 'U_activation_ref': messages, 'groups': groups, 'record': {'mean_calls': []}, 'normalized': [None, None, Value('coarse', (1, 4, 1))], 'root_ids': [0, 2]}
    calls = []
    def original_mean(value, actual_groups):
        calls.append((value, actual_groups)); return output
    fake = SimpleNamespace(long='long', tensor=lambda values, **kwargs: list(values))
    ns = {'state': {'cre_context': context, 'forward_index': 1}, 'torch': fake, 'copy': copy, 'original_mean': original_mean, 'summary': lambda value: {'finite': True}, 'fingerprint': lambda torch, value: value.tag, 'watch': lambda *args: None}
    exec(compile(ast.Module(body=[nested('observed_mean')], type_ignores=[]), 'actual_mean_wrapper', 'exec'), ns)
    returned = ns['observed_mean'](messages, groups)
    need('actual mean wrapper invokes original once and preserves return identity', returned is output and len(calls) == 1 and calls[0][0] is messages and calls[0][1] is groups and context['mean_count'] == 1 and context['phase'] == 'fine_decode')
    try: ns['observed_mean'](messages, groups)
    except AssertionError: need('wrong phase refuses before another mean call', len(calls) == 1)
    else: raise AssertionError('Mean wrapper replayed')
    weights = [object(), object(), object()]
    owner = SimpleNamespace(root_exchange=SimpleNamespace(d_model=4, **{name: SimpleNamespace(weight=w) for name, w in zip(['coarse_edge', 'fine_decode', 'middle_decode'], weights)}))
    ns = {'candidate': True, 'att': owner}
    exec(compile(ast.Module(body=[nested('parameter_blocks')], type_ignores=[]), 'actual_six_blocks', 'exec'), ns)
    blocks = ns['parameter_blocks']()
    need('actual six block schema covers three weights own/context halves', len(blocks) == 6 and all(blocks[name + '_own'] == (w, 0, 4, 0, 4) and blocks[name + '_context'] == (w, 0, 4, 4, 8) for name, w in zip(['coarse_edge', 'fine_decode', 'middle_decode'], weights)))
    # Applying only actual top metadata assertions to an unbound template must
    # refuse runtime_code_commit before any manifest import/NVML/lock/Torch call.
    ns = {'MANIFEST': manifest, 'CANDIDATE_COMMIT': binding['code_commit'], 'RUNTIME_EXPECTED_COMMIT': binding['runtime_expected_commit']}
    try: exec(compile(ast.Module(body=[n for n in runtime.body if isinstance(n, ast.Assert)][:5], type_ignores=[]), 'unbound_metadata_refusal', 'exec'), ns)
    except AssertionError: need('actual top assertion rejects unbound runtime identity', True)
    else: raise AssertionError('Unbound template accepted')
    text = (HERE / 'worker.py').read_text('utf8')
    need('exact dynamic common exclusions retain allLN', "excluded = ('dec.cluster_att.cluster_ffn.0.', 'dec.cluster_att.cluster_ffn.1.', 'dec.cluster_att.cluster_ffn.2.', 'dec.cluster_att.root_exchange.')" in text)
    need('no inherited MST/flux/old candidate FFN path', all(t not in text for t in ['MST', 'mst_plan', 'middle_flux', 'actual_real_mst_edges']) and 'ffn_levels = () if candidate else (0,1,2)' in text)
    need('mean/maps restored and no auxiliary autograd', "global_replacements.append((cre_module,'equal_root_message_means',original_mean))" in text and 'for owner,name,original in reversed(global_replacements):setattr(owner,name,original)' in text and 'torch.autograd.grad(' not in text and 'torch.autograd.backward(' not in text)
    result = {'status': 'STDLIB_CRE_OBSERVER_SOFTWARE_CHECKS_PASSED_NOT_NATIVE_PASS', 'recorded_at': datetime.now(timezone.utc).isoformat(), 'checks': checks, 'check_count': len(checks), 'worker_sha256': sha(HERE / 'worker.py'), 'runtime_sha256': sha(HERE / 'native_runtime.py'), 'manifest_template_sha256': sha(HERE / 'manifest_template.json'), 'resources_function_AST_sha256': hashlib.sha256(dump(function(worker, 'resources')).encode()).hexdigest(), 'Torch_native_GPU_SSH_Git_shared_actions': False, 'old_source46_or61_98_suites_rerun': False, 'software_scope': 'Four metadata plans/core-boundary cases, actual opaque mean-wrapper once/return control, six weight-block schema, hashes/AST only. No Tensor math/GELU/gradients/native/resource result.'}
    with (HERE / 'static_validation.json').open('x', encoding='utf8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({'checks': len(checks), 'sha256': sha(HERE / 'static_validation.json')}))


if __name__ == '__main__': main()
