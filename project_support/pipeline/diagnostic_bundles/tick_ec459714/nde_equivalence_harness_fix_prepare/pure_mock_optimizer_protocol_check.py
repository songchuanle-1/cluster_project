"""Stdlib-only native optimizer-selection protocol proof; never import Torch."""
import ast
import copy
import json
from pathlib import Path
import sys
import types

HERE = Path(__file__).resolve().parent
TICK = HERE.parent

def prove():
    assert 'torch' not in sys.modules and 'gorilla' not in sys.modules
    collection = json.loads((TICK / 'eq_harness_failure_evidence/collection.json').read_bytes())
    config = collection['optimizer']
    class Parameter:
        def __init__(self, name, requires_grad=True):
            self.name, self.requires_grad = name, requires_grad
    class Module:
        def __init__(self):
            self.children = {}
            self.own = []
        def add_module(self, name, value):
            self.children[name] = value
            setattr(self, name, value)
        def parameters(self):
            yield from self.own
            for child in self.children.values():
                yield from child.parameters()
    core = Module()
    core.own = [Parameter('analysis.weight'), Parameter('analysis.bias'),
                Parameter('synthesis.weight'), Parameter('synthesis.bias'),
                Parameter('frozen_example', False)]
    original_parameters = list(core.parameters())
    selected = [p for p in original_parameters if p.requires_grad]
    def downstream_capture(value):
        result = {k: v for k, v in value.items() if k != 'params'}
        result['params'] = [{**{k: v for k, v in group.items() if k != 'params'},
                             'params': list(group['params'])}
                            for group in value['params']]
        return result
    native_tree = ast.parse((TICK / 'eq_harness_failure_evidence/installed_gorilla_solver_build.py').read_bytes())
    native_functions = [copy.deepcopy(n) for n in native_tree.body
                        if isinstance(n, ast.FunctionDef)
                        and n.name in ('build_optimizer', 'build_single_optimizer')]
    for n in native_functions:
        n.returns = None
        for arg in n.args.args:
            arg.annotation = None
    ns = {'_build_optimizer': downstream_capture, 'OPTIM': {'type': 'Adam', 'lr': .001}}
    exec(compile(ast.fix_missing_locations(ast.Module(body=native_functions, type_ignores=[])), '<exact installed selection functions; annotations removed only>', 'exec'), ns)
    try:
        ns['build_optimizer'](core, copy.deepcopy(config))
    except AttributeError as error:
        reproduced = 'text_encoder' in str(error)
    else:
        reproduced = False
    assert reproduced
    helper_tree = ast.parse((HERE / 'equivalence_diagnostic.py').read_bytes())
    helper = next(n for n in helper_tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == 'optimizer_carrier_for_core')
    helper_ns = {}
    exec(compile(ast.Module(body=[helper], type_ignores=[]), '<exact new carrier helper>', 'exec'), helper_ns)
    fake_torch = types.SimpleNamespace(nn=types.SimpleNamespace(Module=Module))
    carrier = helper_ns['optimizer_carrier_for_core'](fake_torch, core)
    assert list(carrier.children) == list(config['paramwise_cfg'])
    assert carrier.dec is core
    assert all(not list(getattr(carrier, name).parameters())
               for name in list(config['paramwise_cfg'])[:-1])
    assert list(core.parameters()) == original_parameters
    original_config = copy.deepcopy(config)
    fixed = ns['build_optimizer'](carrier, copy.deepcopy(config))
    assert config == original_config
    full_native = Module()
    for name in list(config['paramwise_cfg'])[:-1]:
        module = Module()
        module.own = [Parameter(name + '.unrelated')]
        full_native.add_module(name, module)
    native_dec = Module()
    native_dec.own = [Parameter('dec.unrelated')]
    native_dec.add_module('existing_core', core)
    full_native.add_module('dec', native_dec)
    native = ns['build_optimizer'](full_native, copy.deepcopy(config))
    core_ids = {id(p) for p in original_parameters}
    for native_group, fixed_group in zip(native['params'], fixed['params']):
        native_selected = [p for p in native_group['params'] if id(p) in core_ids]
        assert len(native_selected) == len(fixed_group['params'])
        assert all(a is b for a, b in zip(native_selected, fixed_group['params']))
        assert {k: v for k, v in native_group.items() if k != 'params'} == {k: v for k, v in fixed_group.items() if k != 'params'}
    assert len(fixed['params']) == 5
    assert all(not group['params'] for group in fixed['params'][:4])
    assert all(a is b for a, b in zip(fixed['params'][4]['params'], selected))
    assert len(fixed['params'][4]['params']) == len(selected)
    assert {k: v for k, v in fixed.items() if k != 'params'} == {k: v for k, v in native.items() if k != 'params'}
    assert fixed['type'] == 'AdamW' and fixed['lr'] == .0001 and fixed['weight_decay'] == .0005
    assert [g['lr_mult'] for g in fixed['params']] == [.001, .01, .01, .01, 1.0]
    assert 'torch' not in sys.modules and 'gorilla' not in sys.modules
    return {'passed': True, 'original_missing_text_encoder_reproduced': reproduced,
            'exact_native_selection_functions_executed_with_annotations_removed_only': True,
            'same_five_YAML_groups': [g['type'] for g in fixed['params']],
            'group_parameter_counts': [len(g['params']) for g in fixed['params']],
            'native_fullmodel_restricted_core_group_identity_order_and_options_exact': True,
            'same_core_objects_registration_order_requires_grad_filter_and_config': True,
            'no_model_state_or_RNG_operation': True,
            'actual_AdamW_or_tensor_numerics_executed': False,
            'Torch_or_gorilla_imported': False}

if __name__ == '__main__':
    print(json.dumps(prove(), allow_nan=False))
