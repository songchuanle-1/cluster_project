"""Read-only PSBR syntax/source checks; --write saves evidence under current tick guard.

No model module is imported and no synthetic/native forward is executed.
"""

import argparse
import ast
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


BUNDLE = Path(__file__).resolve().parent
PROJECT = BUNDLE.parents[3]
REPO = PROJECT / 'Cluster'
BASE_NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
BASE = REPO / 'framework/model/Quard_model' / BASE_NAME
NEW = BASE.with_name(BASE_NAME + '_psbr')
BASE_CONFIG = REPO / 'configs/Quard/ctf_hcg_csort' / (BASE_NAME + '.yaml')
NEW_CONFIG = REPO / 'configs/Quard/ctf_hcg_csort_psbr' / (BASE_NAME + '_psbr.yaml')
TOKEN = '8fafa3d4ebcb48e7ba3436e084f6ee9f'
THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
PROPOSAL_SHA = '7a82845976c83accb74f730fef4500046c6f7e004c5dff84b2ea02c2f0c79650'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(node):
    return ast.dump(node, include_attributes=False)


def named(nodes, name):
    return next(n for n in nodes if getattr(n, 'name', None) == name)


def write_guard():
    owner = json.loads((PROJECT / 'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf-8'))
    assert owner['token'] == TOKEN and owner['thread_id'] == THREAD
    assert owner['generated_at'] == '2026-10-22T02:12:05.347438+00:00'
    assert owner['deadline_at'] == '2026-10-22T03:12:05.347438+00:00'
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    for relative, key in [('pipeline/headless/.tick_context.json', 'context_sha256'),
                          ('pipeline/headless/.tick_context_state.next.json', 'pending_sha256')]:
        assert sha(PROJECT / relative) == owner[key]
    mode = json.loads((PROJECT / 'pipeline/execution_mode.json').read_text(encoding='utf-8'))
    assert mode['mode'] == 'foreground' and mode['target_thread_id'] == THREAD
    assert sha(PROJECT / 'pipeline/goal.json') == '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'


def main(write=False):
    checks = {}

    def check(name, condition):
        checks[name] = bool(condition)
        assert condition, name

    inventory = json.loads((BUNDLE / 'source_inventory.json').read_text(encoding='utf-8'))
    sources = sorted(NEW.glob('*.py'))
    check('exact_eight_independent_sources', len(sources) == 8)
    check('frozen_proposal_unchanged', sha(BUNDLE.parent / 'variant_proposal.json') == PROPOSAL_SHA)
    for path in sources:
        source = path.read_text(encoding='utf-8')
        ast.parse(source, filename=str(path))
        compile(source, str(path), 'exec')
    check('all_eight_ast_and_compile_without_import', True)
    check('inventory_all_nine_hashes_match', all(sha(REPO / rel) == value for rel, value in inventory['new_files'].items()) and len(inventory['new_files']) == 9)
    check('all_original_baseline_hashes_unchanged', all(sha(REPO / rel) == value for rel, value in inventory['baseline_sources'].items()))
    check('all_28_preexisting_dirty_files_unchanged', len(inventory['protected_before']) == 28 and all(sha(REPO / rel) == value for rel, value in inventory['protected_before'].items()))
    check('five_unmodified_copies_byte_identical', all((BASE / name).read_bytes() == (NEW / name).read_bytes() for name in ['__init__.py', 'backbone.py', 'loss.py', 'network.py', 'sample_model.py']))
    check('native_yaml_byte_identical', BASE_CONFIG.read_bytes() == NEW_CONFIG.read_bytes())
    config = yaml.safe_load(NEW_CONFIG.read_text(encoding='utf-8'))
    check('native_yaml_all_fields_equal', config == yaml.safe_load(BASE_CONFIG.read_text(encoding='utf-8')))
    check('frozen_phase1_yaml_values', config['train']['seed'] == 1999 and config['train']['epochs'] == 50 and config['lr_scheduler']['max_iters'] == 70 and config['model']['dec']['cluster_att_num_layers'] == 1 and config['model']['dec']['cluster_mode'] == 'ctf_hcg_csort' and config['model']['dec']['activation_fn'] == 'gelu')

    original = ast.parse((BASE / 'hier_postprocess.py').read_text(encoding='utf-8'))
    candidate = ast.parse((NEW / 'hier_postprocess.py').read_text(encoding='utf-8'))
    changed_classes = {'PointCloudPartitioner', 'SharedClusterBank', 'C2F_ClusterAttn_CTF'}
    for node in original.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name not in changed_classes:
            check('unchanged_ast_' + node.name, dump(node) == dump(named(candidate.body, node.name)))
    for class_name, methods in [('PointCloudPartitioner', ['partition_points', 'cluster_layer']),
                                ('SharedClusterBank', ['__init__', 'build_cluster_feats'])]:
        old_class = named(original.body, class_name)
        new_class = named(candidate.body, class_name)
        for method in methods:
            check('unchanged_ast_' + class_name + '_' + method, dump(named(old_class.body, method)) == dump(named(new_class.body, method)))
    old_ctf = named(original.body, 'C2F_ClusterAttn_CTF')
    new_ctf = named(candidate.body, 'C2F_ClusterAttn_CTF')
    old_init = named(old_ctf.body, '__init__')
    new_init = named(new_ctf.body, '__init__')
    check('original_ctf_constructor_prefix_unchanged', dump(old_init.args) == dump(new_init.args) and [dump(s) for s in old_init.body] == [dump(s) for s in new_init.body[:len(old_init.body)]])
    init_text = ast.unparse(new_init)
    check('middle_ffn_removed_from_registration', 'self.cluster_ffn[1] = nn.Identity()' in init_text)
    forks = [n for n in ast.walk(new_init) if isinstance(n, ast.With)]
    check('only_new_module_constructor_forked_cpu_rng', len(forks) == 1 and ast.unparse(forks[0].items[0].context_expr) == 'torch.random.fork_rng(devices=[])' and len(forks[0].body) == 1 and ast.unparse(forks[0].body[0]) == 'self.middle_recurrence = ParentSegmentedBidirectionalRecurrence(d_model)')
    new_forward = named(new_ctf.body, 'forward')
    old_forward = named(old_ctf.body, 'forward')
    check('cluster_attention_forward_api_unchanged', dump(old_forward.args) == dump(new_forward.args))
    middle_branch = next(n for n in ast.walk(new_forward) if isinstance(n, ast.If) and ast.unparse(n.test) == 'lvl == 1')
    expected_middle = 'refined = self.middle_recurrence(self.cluster_ffn_norm[1](cf), self.middle_positions, cluster_ids_list[2], self.middle_valid)'
    check('middle_exact_replacement_without_residual', len(middle_branch.body) == 1 and ast.unparse(middle_branch.body[0]) == expected_middle)
    old_refined = next(n for n in ast.walk(old_forward) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'refined' for t in n.targets))
    check('fine_coarse_exact_native_residual_ffn', len(middle_branch.orelse) == 1 and dump(middle_branch.orelse[0]) == dump(old_refined))
    # The unmodified HCG and CSORT classes above cover their full method bodies,
    # including raw input references, weights, accumulation, composition and gates.
    htext = (NEW / 'hier_postprocess.py').read_text(encoding='utf-8')
    check('current_original_centroid_cache', 'middle_positions = [coords.detach() for coords in per_layer_coords[2]]' in htext)
    check('support_from_actual_composed_point_ids', 'point_to_mid = ids1[ids0]' in htext and 'torch.bincount(point_to_mid, minlength=Kmid) > 0' in htext)
    check('cache_bound_to_exact_current_parent_ids', 'self.middle_parent_ids is not cluster_ids_list[2]' in htext and 'self.partitioner.middle_parent_ids is not self.cluster_ids_list[2]' in htext)

    old_dec = ast.parse((BASE / 'dec.py').read_text(encoding='utf-8'))
    new_dec = ast.parse((NEW / 'dec.py').read_text(encoding='utf-8'))
    for node in old_dec.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name != 'Encoder_layer':
            check('unchanged_dec_ast_' + node.name, dump(node) == dump(named(new_dec.body, node.name)))
    old_encoder = named(old_dec.body, 'Encoder_layer')
    new_encoder = named(new_dec.body, 'Encoder_layer')
    check('encoder_constructor_unchanged', dump(named(old_encoder.body, '__init__')) == dump(named(new_encoder.body, '__init__')))
    old_ef = named(old_encoder.body, 'forward')
    new_ef = named(new_encoder.body, 'forward')
    original_forward_dump = dump(old_ef)
    selected_if = next(n for n in ast.walk(new_ef) if isinstance(n, ast.If) and ast.unparse(n.test) == 'self.use_cluster and batch_offsets is not None')
    start = next(i for i, n in enumerate(selected_if.body) if isinstance(n, ast.If) and ast.unparse(n.test) == 'self.cluster_bank.middle_parent_ids is not self.cluster_bank.cluster_ids_list[2]')
    extras = selected_if.body[start:start + 4]
    check('encoder_only_adds_cache_assert_and_three_assignments', len(extras) == 4 and isinstance(extras[0], ast.If) and all(isinstance(n, ast.Assign) for n in extras[1:]))
    del selected_if.body[start:start + 4]
    check('encoder_remaining_native_forward_unchanged', dump(new_ef) == original_forward_dump)

    recurrence = ast.parse((NEW / 'middle_recurrence.py').read_text(encoding='utf-8'))
    recurrent_class = named(recurrence.body, 'ParentSegmentedBidirectionalRecurrence')
    recurrent_init = named(recurrent_class.body, '__init__')
    check('exact_three_shared_linear_registrations', [ast.unparse(n) for n in recurrent_init.body[2:]] == ['self.Wx = nn.Linear(d_model, d_model, bias=True)', 'self.Wh = nn.Linear(d_model, d_model, bias=False)', 'self.Wo = nn.Linear(2 * d_model, d_model, bias=True)'])
    recurrent_forward = named(recurrent_class.body, 'forward')
    call_names = [ast.unparse(n.func) for n in ast.walk(recurrent_forward) if isinstance(n, ast.Call)]
    check('one_Wx_two_shared_Wh_one_Wo_call_sites', call_names.count('self.Wx') == 1 and call_names.count('self.Wh') == 2 and call_names.count('self.Wo') == 1 and call_names.count('torch.tanh') == 2)
    check('no_added_gate_attention_qkv_or_seed_call', not any(name.endswith(('.sigmoid', '.softmax', '.manual_seed', '.backward', '.step')) for name in call_names))
    check('unsupported_and_padding_zero_then_original_id_inverse_write', 'output = middle.new_zeros((padded_K, C))' in ast.unparse(recurrent_forward) and 'output = output.index_copy(0, original_ids, self.Wo(paired))' in ast.unparse(recurrent_forward))
    check('independent_two_direction_zero_state_boundaries', sum(isinstance(n, ast.Assign) and ast.unparse(n) == 'state = projected.new_zeros((C,))' for n in ast.walk(recurrent_forward)) == 2)
    check('no_torch_model_imported_by_static_check', 'torch' not in sys.modules)

    result = {
        'schema_version': 1,
        'status': 'STATIC_CHECKS_PASS_NATIVE_NOT_RUN',
        'candidate_id': 'hierarchy-parent-segmented-bidirectional-token-state',
        'experiment_id': 'M209-PSBR',
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'check_count': len(checks),
        'checks': checks,
        'source_hashes': {str(p.relative_to(REPO)).replace('\\', '/'): sha(p) for p in sources + [NEW_CONFIG]},
        'static_check_sha256': sha(Path(__file__)),
        'estimated_middle_parameters': {'new': 262656, 'replaced_old': 525568, 'delta': -262912, 'status': 'STATIC_ARITHMETIC_NOT_RUNTIME_INVENTORY'},
        'executed': {'torch_import': False, 'synthetic_forward': False, 'native': False, 'gpu': False, 'ssh': False, 'stage': False, 'git_mutation': False},
        'native_smoke': 'NOT_RUN',
        'standard_resources': 'NOT_RUN',
        'actual_loader_pairing': 'UNKNOWN_NOT_RUN',
        'efficacy': 'UNKNOWN_UNTRAINED',
        'admission_ready': False,
    }
    if write:
        write_guard()
        (BUNDLE / 'static_validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    main(parser.parse_args().write)
