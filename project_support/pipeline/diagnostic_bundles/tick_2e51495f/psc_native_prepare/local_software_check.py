"""Actual CPU-only PSC observer wiring checks; symbolic tensors are not Torch."""
from pathlib import Path
import ast
import copy
import datetime
import hashlib
import json
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/project/cluster_project')
NATIVE = HERE / 'native'
HVD = ROOT / 'pipeline/diagnostic_bundles/tick_c7451cf1/hvd_native_prepare/native'
MIC = ROOT / 'pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_prepare/native'
checks = []


def check(name, value):
    assert value, name
    checks.append({'name': name, 'passed': True})


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def function(text, name):
    return next(ast.get_source_segment(text, node) for node in ast.parse(text).body
                if isinstance(node, ast.FunctionDef) and node.name == name)


class SymbolicTensor:
    """Shape/reference protocol only; never claims numerical or gradient validity."""
    def __init__(self, shape, data=None, dtype='native'):
        self.shape = tuple(shape)
        self.data = data
        self.dtype = dtype
        self.requires_grad = False
    def __getitem__(self, key):
        if type(key) is int:
            return SymbolicTensor(self.shape[1:], self.data[key] if self.data is not None else None, self.dtype)
        assert isinstance(key, SymbolicTensor)
        return SymbolicTensor((sum(key.data), *self.shape[1:]), dtype=self.dtype)
    def __invert__(self):
        return SymbolicTensor(self.shape, [not v for v in self.data], 'bool')
    def to(self, *args, **kwargs):
        return SymbolicTensor(self.shape, self.data, kwargs.get('dtype', self.dtype))
    def detach(self):
        return self
    def cpu(self):
        return self
    def tolist(self):
        return self.data
    def new_zeros(self, shape):
        return SymbolicTensor(shape, dtype=self.dtype)
    def new_ones(self, shape):
        return SymbolicTensor(shape, dtype=self.dtype)
    def index_add(self, dim, labels, values):
        assert dim == 0 and len(labels.shape) == 1
        return SymbolicTensor(self.shape, dtype=self.dtype)
    def index_select(self, dim, labels):
        assert dim == 0
        return SymbolicTensor((labels.shape[0], *self.shape[1:]), dtype=self.dtype)
    def clamp_min(self, value):
        return self
    def __truediv__(self, other):
        return SymbolicTensor(self.shape, dtype=self.dtype)
    def __sub__(self, other):
        assert self.shape == other.shape
        return SymbolicTensor(self.shape, dtype=self.dtype)
    def unsqueeze(self, dim):
        dim = dim if dim >= 0 else len(self.shape) + dim + 1
        return SymbolicTensor((*self.shape[:dim], 1, *self.shape[dim:]), dtype=self.dtype)
    def __mul__(self, other):
        assert len(self.shape) == len(other.shape)
        shape = []
        for x, y in zip(self.shape, other.shape):
            assert x == y or x == 1 or y == 1
            shape.append(max(x, y))
        return SymbolicTensor(shape, dtype=self.dtype)
    def flatten(self, start_dim=0):
        width = 1
        for value in self.shape[start_dim:]:
            width *= value
        return SymbolicTensor((*self.shape[:start_dim], width), dtype=self.dtype)
    def __add__(self, other):
        assert self.shape == other.shape
        return SymbolicTensor(self.shape, dtype=self.dtype)


def original_cat(values, dim=0):
    dim = dim if dim >= 0 else len(values[0].shape) + dim
    shape = list(values[0].shape)
    assert all(all(v.shape[i] == shape[i] for i in range(len(shape)) if i != dim) for v in values)
    shape[dim] = sum(v.shape[dim] for v in values)
    return SymbolicTensor(shape)


ORIGINAL_METHODS = {name: getattr(SymbolicTensor, name) for name in
                    ('__getitem__', '__invert__', 'to', '__add__', 'index_select')}


def observer_case(mutation=None):
    for name, original in ORIGINAL_METHODS.items():
        setattr(SymbolicTensor, name, original)
    fake_torch = types.SimpleNamespace(Tensor=SymbolicTensor, cat=original_cat,
        zeros_like=lambda value, *args, **kwargs: SymbolicTensor(value.shape))
    source = (NATIVE / 'candidate_model/position_scatter.py').read_text()
    tree = ast.parse(source)
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name in ('_group_mean', '_centered_cross', 'cross_scatter_components', 'pack_cross_rows')]
    production = {'torch': fake_torch}
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<immutable-PSC-functions-symbolic-protocol-only>', 'exec'), production)
    if mutation == 'omit_within_between_add':
        segment = function(source, 'cross_scatter_components').replace('total1 = w1 + b1', 'total1 = w1')
        exec(compile(segment, '<negative-law-mutation>', 'exec'), production)
    elif mutation == 'wrong_coarse_position_center':
        segment = function(source, 'cross_scatter_components').replace(
            '_centered_cross(x1, f1, x2, f2, p2, n2)',
            '_centered_cross(x1, f1, f2, f2, p2, n2)')
        exec(compile(segment, '<negative-center-mutation>', 'exec'), production)
    elif mutation == 'wrong_pack_component':
        segment = function(source, 'pack_cross_rows').replace(
            '(normalized[0], j0, b1.index_select', '(normalized[0], normalized[0], b1.index_select')
        exec(compile(segment, '<negative-pack-mutation>', 'exec'), production)
    state = {'forward_index': 1, 'norm_counts': [1, 1, 1]}
    core = types.SimpleNamespace(channels=2)
    ids = [[SymbolicTensor((3,), [0, 0, 1])],
           [SymbolicTensor((2,), [0, 0])], [SymbolicTensor((1,), [0])]]
    points = SymbolicTensor((1, 4, 2))
    positions = SymbolicTensor((1, 4, 3), dtype='coordinate_native')
    mask = SymbolicTensor((1, 4), [[False, False, False, True]], 'bool')
    normalized = [SymbolicTensor((1, n, 2)) for n in (3, 2, 2)]
    state.update(psc_encoder_features_ref=points, psc_encoder_positions_ref=positions,
        psc_padded_positions_ref=positions, psc_encoder_mask_ref=mask,
        norm_outputs=dict(enumerate(normalized)))
    env = {
        'state': state, 'core': core, 'bank': types.SimpleNamespace(cluster_ids_list=ids),
        'summary': lambda x: {'shape': list(x.shape), 'dtype': x.dtype, 'finite': True},
        'fingerprint': lambda torch, value: str(id(value)), 'torch': fake_torch,
        'watch': lambda *args: None, 'lite_watch': lambda *args: None,
        'original_group_mean': production['_group_mean'],
        'original_cross': production['_centered_cross'],
        'original_components': production['cross_scatter_components'],
        'original_pack': production['pack_cross_rows'],
        'original_cat': original_cat, 'original_zeros_like': fake_torch.zeros_like,
        'original_getitem': ORIGINAL_METHODS['__getitem__'],
        'original_invert': ORIGINAL_METHODS['__invert__'],
        'original_to': ORIGINAL_METHODS['to'],
        'original_add': ORIGINAL_METHODS['__add__'],
        'original_select': ORIGINAL_METHODS['index_select'],
    }
    worker_tree = ast.parse((NATIVE / 'worker.py').read_text())
    nodes = {node.name: node for node in ast.walk(worker_tree) if isinstance(node, ast.FunctionDef)}
    names = ['exchange_pre', 'observed_getitem', 'observed_invert', 'observed_to',
        'observed_group_mean', 'observed_cross', 'observed_add', 'observed_components',
        'observed_select', 'observed_zeros_like', 'observed_pack', 'observed_cat']
    exec(compile(ast.Module(body=[nodes[name] for name in names], type_ignores=[]),
                 '<actual-new-PSC-observers-symbolic-protocol-only>', 'exec'), env)
    for name, replacement in {
        '__getitem__': 'observed_getitem', '__invert__': 'observed_invert',
        'to': 'observed_to', '__add__': 'observed_add',
        'index_select': 'observed_select',
    }.items():
        setattr(SymbolicTensor, name, env[replacement])
    production.update(_group_mean=env['observed_group_mean'], _centered_cross=env['observed_cross'])
    fake_torch.cat = env['observed_cat']; fake_torch.zeros_like = env['observed_zeros_like']
    try:
        sent_positions = SymbolicTensor(positions.shape) if mutation == 'wrong_native_coordinate_reference' else positions
        env['exchange_pre'](core, (points, sent_positions, mask, normalized, ids))
        valid = points[0][~mask[0]]
        coords = positions[0][~mask[0]].to(dtype=valid.dtype)
        c = state['psc_context']
        record = {key: 0 for key in ('actual_group_mean_calls', 'actual_centered_cross_calls',
            'actual_within_between_add_calls', 'actual_stats_calls', 'actual_pack_calls', 'actual_factor_concat_calls')}
        record.update(point_count=3, group_mean_observations=[], centered_cross_observations=[],
            stats_observations=[], pack_observations=[])
        plan = {'nodes': [[0, 1], [0], [0]], 'point_to_fine': [0, 0, 1],
                'fine_to_middle': [0, 0], 'middle_to_coarse': [0]}
        scene = dict(record=record, plan=plan, batch=0, counts=[2, 1, 1],
            stats_active=False, pack_active=False, factor_active=False,
            mean_refs=[], pack_select_refs=[], pack_cat_refs=[], selected_normalized_refs={})
        c['current_scene'] = scene
        mappings = tuple(SymbolicTensor((len(plan[key]),), plan[key]) for key in
                         ('point_to_fine', 'fine_to_middle', 'middle_to_coarse'))
        stats = env['observed_components'](valid, coords, *mappings, 2, 1, 1)
        rows = [normalized[level][0].index_select(0, SymbolicTensor((len(nodes),), nodes))
                for level, nodes in enumerate(plan['nodes'])]
        packed = env['observed_pack'](rows, stats, mappings[1], mappings[2])
        assert [row.shape for row in packed] == [(2, 20), (1, 20), (1, 20)]
        assert record['actual_group_mean_calls'] == 11
        assert record['actual_centered_cross_calls'] == 3
        assert record['actual_within_between_add_calls'] == 1
        assert all(info['original_calls'] == 1 for info in record['group_mean_observations'])
        return record
    finally:
        for name, original in ORIGINAL_METHODS.items():
            setattr(SymbolicTensor, name, original)


def main():
    worker = (NATIVE / 'worker.py').read_text()
    runtime = (NATIVE / 'native_runtime.py').read_text()
    hvd = (HVD / 'worker.py').read_text()
    mic = (MIC / 'worker.py').read_text()
    for path in [*NATIVE.glob('*.py'), *(NATIVE / 'candidate_model').glob('*.py'), Path(__file__)]:
        compile(path.read_bytes(), str(path), 'exec')
        check('compile_without_import:' + path.name, True)
    check('resources_complete_function_exact_HVD', function(worker, 'resources') == function(hvd, 'resources'))
    check('resources_complete_function_exact_MIC', function(worker, 'resources') == function(mic, 'resources'))
    check('unchanged_native_TRAIN2_call', 'train.train(1,model,TwoNativeBatches(loader),optimizer,scheduler,cfg,logger,writer)' in worker)
    check('unchanged_common_init_scope', "'dec.cluster_att.position_feature_scatter.'" in worker and 'retain three original LayerNorms' in worker)
    check('whole_core_gradient_gate', "if candidate and name=='position_feature_scatter'" in worker and 'whole_position_feature_scatter_weight_gradient' in worker)
    check('whole_core_weight_and_module_update', 'whole_position_feature_scatter_weight_updated' in worker and 'whole_position_feature_scatter_module_updated' in worker)
    check('no_extra_autograd_grad', 'autograd.grad(' not in worker)
    check('DRAFT_true', 'DRAFT_EXECUTION_DISABLED = True' in runtime)
    proc = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(NATIVE / 'native_runtime.py')],
        capture_output=True, text=True, timeout=10)
    check('actual_runtime_import_refuses_before_manifest_or_Torch', proc.returncode != 0 and
          'PSC native preparation is execution-disabled' in proc.stderr and 'ModuleNotFoundError' not in proc.stderr)
    template = json.loads((NATIVE / 'manifest_template.json').read_text())
    ten = ('current_token', 'stage', 'tick_generated_at', 'deadline_at', 'physical_gpu',
           'gpu_uuid', 'allowed_gpus', 'context_sha256', 'pending_sha256', 'runtime_code_commit')
    check('ten_execution_fields_NULL', all(template[k] is None for k in ten))
    check('source_0ccc_parent_runtime_d20', template['code_commit'] == '0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d'
          and template['source_parent_commit'] == template['runtime_expected_commit'] == 'd20eb221eff6584b67d4e9b5673559d0e1cb735b')
    check('runtime_current_root', template['root'].endswith('Cluster_hvd_20261106'))
    check('GPU0_overlay_20000_max1_three_locks', template['resource_memory_policy'] ==
          {'allow_external_overlay': True, 'minimum_free_mib_before_launch': 20000,
           'max_project_tasks_per_gpu': 1, 'cooperative_lock_kinds': ['training', 'diagnostic', 'exclusive'],
           'external_contexts': 'record_preserve_no_signals', 'measurement_scope': 'authorized_overlay_potentially_contended_not_exclusive'})
    check('runtime_has_only_GPU0_UUID', 'GPU-7f82edb9' not in runtime)
    for name, digest in template['diagnostic_files'].items():
        check('diagnostic_hash:' + name, sha(NATIVE / name) == digest)
    check('no_active_materials', not any((NATIVE / name).exists() for name in
        ('native_manifest.json', 'execution_lease.json', 'execution_binding.json', 'request.json', 'release.json')))
    record = observer_case()
    check('actual_symbolic_observer_positive_original_coordinate_mask_cast_chain', True)
    check('actual_symbolic_observer_11_original_means_3_cross_1_law_add', record['actual_group_mean_calls'] == 11 and record['actual_centered_cross_calls'] == 3 and record['actual_within_between_add_calls'] == 1)
    check('actual_symbolic_observer_10C_pack_actual_references', record['pack_observations'][0]['packing_blocks_C_3C_3C_3C'])
    for mutation in ('wrong_native_coordinate_reference', 'omit_within_between_add',
                     'wrong_coarse_position_center', 'wrong_pack_component'):
        caught = False
        try:
            observer_case(mutation)
        except AssertionError:
            caught = True
        check('actual_symbolic_negative_control:' + mutation, caught)
    result = {
        'schema_version': 1, 'recorded_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'passed': True, 'actual_check_count': len(checks), 'checks': checks,
        'worker_sha256': sha(NATIVE / 'worker.py'), 'runtime_sha256': sha(NATIVE / 'native_runtime.py'),
        'scope': 'Actual new CPU compile/AST/hash/default-refusal and symbolic tensor/reference wiring checks with four deliberate negative controls only. Symbolic protocol has no numeric tensor arithmetic or autograd; not Torch, native data/TRAIN/full-forward, resources, efficacy or novelty. Original54 source tests not rerun.',
        'native': 'NOT_RUN', 'resources': 'NOT_RUN', 'Torch_autograd': 'NOT_RUN',
        'original_source_54_checks_repeated': False,
        'runtime_refusal': {'returncode': proc.returncode, 'stderr': proc.stderr},
    }
    output = HERE / 'software_validation.json'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'passed': True, 'checks': len(checks), 'result': str(output), 'sha256': sha(output)}))


if __name__ == '__main__':
    main()
