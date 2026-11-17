"""PSBR worker preparation checks without importing worker/runtime/torch.

Default is read-only. --write requires the current parent-owned tick guard.
"""

import argparse
import ast
import copy
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


BUNDLE = Path(__file__).resolve().parent
PROJECT = BUNDLE.parents[3]
REPO = PROJECT / 'Cluster'
REFERENCE = PROJECT / 'pipeline/diagnostic_bundles/tick_86e41faa/hrc_native_prepare'
SOURCE_PREP = BUNDLE.parent / 'psbr_prepare'
COMMIT = '74fcd21df0af9a971792038ffe251af1ffea2604'
CID = 'hierarchy-parent-segmented-bidirectional-token-state'
NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(node):
    return ast.dump(node, include_attributes=False)


def function(tree, name):
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def guard():
    owner = json.loads((PROJECT / 'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf-8'))
    assert owner['token'] == '8fafa3d4ebcb48e7ba3436e084f6ee9f'
    assert owner['thread_id'] == '01a159c5-29ab-7a22-ba7f-e79174757253'
    assert owner['generated_at'] == '2026-10-22T02:12:05.347438+00:00'
    assert owner['deadline_at'] == '2026-10-22T03:12:05.347438+00:00'
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    for relative, key in [('pipeline/headless/.tick_context.json','context_sha256'),
                          ('pipeline/headless/.tick_context_state.next.json','pending_sha256')]:
        assert sha(PROJECT / relative) == owner[key]
    mode = json.loads((PROJECT / 'pipeline/execution_mode.json').read_text(encoding='utf-8'))
    assert mode['mode'] == 'foreground' and mode['target_thread_id'] == owner['thread_id']
    assert sha(PROJECT / 'pipeline/goal.json') == GOAL


def main(write=False):
    checks = {}

    def check(name, condition):
        checks[name] = bool(condition)
        assert condition, name

    reference_hashes = {
        'worker.py':'37782c1ae1ea9cb2f7bb77d59c7b8aff926438fbac827106f94d8c8fa396ef01',
        'native_runtime.py':'4737e6f08ebb202cec073819ba95bcb94f78fc93ed1b4d5e214ef69d1f9ef0e4',
        'manifest_template.json':'ea756a6b95861ac65e3a535e9cfa5743151d965d8aed4876599bdab36b414509',
        'preparation.json':'4754db1a1c550c869596e0ca57cee99834239e8ed78e87ec65f68142f48c812a',
    }
    check('frozen_reference_files_unchanged', all(sha(REFERENCE / name) == value for name,value in reference_hashes.items()))
    check('frozen_source_preparation_unchanged', sha(SOURCE_PREP / 'preparation.json') == 'f1973052931bb76bb8a4087e1d1aff5d6e5051f2859227d4fbc74a7827020128')
    prepared_sources = json.loads((SOURCE_PREP / 'preparation.json').read_text(encoding='utf-8'))['source_hashes']
    manifest = json.loads((BUNDLE / 'manifest_template.json').read_text(encoding='utf-8'))
    check('exact_psbr_identity_and_commit', manifest['candidate_id'] == CID and manifest['experiment_id'] == 'M209-PSBR' and manifest['code_commit'] == COMMIT and manifest['candidate_name'] == NAME + '_psbr' and manifest['goal_sha256'] == GOAL)
    check('frozen_source_preparation_link', manifest['source_preparation_sha256'] == sha(SOURCE_PREP / 'preparation.json'))
    check('execution_fields_unbound', all(manifest[key] is None for key in ['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']))
    check('no_live_manifest_lease_binding_or_results', not any((BUNDLE / name).exists() for name in ['native_manifest.json','execution_lease.json','execution_binding.json']) and not list(BUNDLE.glob('*_result.json')))
    check('all_eleven_staged_diagnostic_hashes_match', len(manifest['diagnostic_files']) == 11 and all(sha(BUNDLE / name) == value for name,value in manifest['diagnostic_files'].items()))
    check('exact_eight_candidate_sources', len(manifest['candidate_source_hashes']) == 8 and len(list((BUNDLE / 'candidate_model').glob('*.py'))) == 8)
    for relative, expected in prepared_sources.items():
        local = REPO / relative
        staged = BUNDLE / 'candidate_model' / local.name if local.suffix == '.py' else BUNDLE / 'candidate.yaml'
        check('committed_copy_' + local.name, sha(local) == expected and sha(staged) == expected and hashlib.sha256(subprocess.check_output(['git','show',COMMIT + ':' + relative],cwd=REPO)).hexdigest() == expected)
    native = yaml.safe_load((BUNDLE / 'candidate.yaml').read_text(encoding='utf-8'))
    check('native_yaml_phase1_unchanged', native['train']['seed'] == 1999 and native['train']['epochs'] == 50 and native['lr_scheduler']['max_iters'] == 70 and native['model']['dec']['cluster_att_num_layers'] == 1 and native['model']['dec']['cluster_mode'] == 'ctf_hcg_csort')
    check('native_yaml_matches_m95_bytes', (BUNDLE / 'candidate.yaml').read_bytes() == (REPO / 'configs/Quard/ctf_hcg_csort' / (NAME + '.yaml')).read_bytes())
    paths = [BUNDLE/'worker.py',BUNDLE/'native_runtime.py',BUNDLE/'validate_static.py'] + sorted((BUNDLE/'candidate_model').glob('*.py'))
    for path in paths:
        source = path.read_text(encoding='utf-8')
        ast.parse(source, filename=str(path))
        compile(source,str(path),'exec')
    check('all_eleven_python_files_ast_compile_without_execution', len(paths) == 11)

    worker = ast.parse((BUNDLE / 'worker.py').read_text(encoding='utf-8'))
    old_worker = ast.parse((REFERENCE / 'worker.py').read_text(encoding='utf-8'))
    runtime = ast.parse((BUNDLE / 'native_runtime.py').read_text(encoding='utf-8'))
    old_runtime = ast.parse((REFERENCE / 'native_runtime.py').read_text(encoding='utf-8'))
    resource = function(worker,'resources')
    check('resources_complete_ast_identical', dump(resource) == dump(function(old_worker,'resources')))
    for name in ['sha','verify','observe','acquire','release','fingerprint','save']:
        check('runtime_guard_function_identical_' + name, dump(function(runtime,name)) == dump(function(old_runtime,name)))
    check('runtime_has_no_model_setup_or_torch_import', not any(isinstance(n,ast.FunctionDef) and n.name == 'setup' for n in runtime.body) and not any(isinstance(n,(ast.Import,ast.ImportFrom)) and any(a.name == 'torch' or a.name.startswith('torch.') for a in n.names) for n in ast.walk(runtime)))
    runtime_text=(BUNDLE/'native_runtime.py').read_text(encoding='utf-8')
    check('runtime_exact_psbr_staging_and_identity', "STAGE.name == 'psbr_' + MANIFEST['current_token'][:8]" in runtime_text and "MANIFEST['experiment_id'] == 'M209-PSBR'" in runtime_text and "CANDIDATE_COMMIT = '" + COMMIT + "'" in runtime_text)
    check('runtime_exact_physical_uuid_map', "0: 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'" in runtime_text and "1: 'GPU-7f82edb9-f620-8045-caea-a75232265cd1'" in runtime_text)
    old_setup = function(old_worker,'setup')
    setup = copy.deepcopy(function(worker,'setup'))
    common = setup.body[-2]
    check('common_parameter_readout_smoke_only', isinstance(common,ast.If) and ast.unparse(common.test) == "mode == 'smoke'" and "'cluster_ffn.1.' not in name and 'middle_recurrence.' not in name" in ast.unparse(common))
    del setup.body[-2]
    for node in ast.walk(setup):
        if isinstance(node,ast.Constant) and isinstance(node.value,str):
            node.value=node.value.replace('PSBR requires only the original final hierarchy injection','Dependency control requires only the original final hierarchy injection')
    check('setup_native_body_unchanged_except_common_parameter_readout', dump(setup) == dump(old_setup))
    main_node = function(worker,'main')
    acquire_line = min(n.lineno for n in ast.walk(main_node) if isinstance(n,ast.Call) and ast.unparse(n.func)=='acquire')
    setup_line = min(n.lineno for n in ast.walk(main_node) if isinstance(n,ast.Call) and ast.unparse(n.func)=='setup')
    check('main_acquire_before_setup_torch', acquire_line < setup_line)
    smoke = function(worker,'smoke')
    calls = [ast.unparse(n.func) for n in ast.walk(smoke) if isinstance(n,ast.Call)]
    check('one_original_train_train_call', calls.count('train.train') == 1)
    check('no_auxiliary_backward_autograd_grad_step_or_rng_call', not any(name.endswith(('.backward','.grad','.step','.zero_grad','.manual_seed','.set_rng_state')) for name in calls))
    smoke_text = ast.unparse(smoke)
    check('two_native_batches_normal_exhaustion', 'itertools.islice(iter(self.native), 2)' in smoke_text and 'train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)' in smoke_text)
    check('native_loss_tensor_backward_hook', 'loss.register_hook(loss_backward)' in smoke_text and "result['native_criterion_backwards'] += 1" in smoke_text)
    check('native_optimizer_pre_post_hooks', 'optimizer.register_step_pre_hook(before_step)' in smoke_text and 'optimizer.register_step_post_hook(after_step)' in smoke_text)
    check('real_support_non_singleton_and_reset_observers', 'ids1[ids0]' in smoke_text and "record['nonsingleton_supported_parent_groups'] >= 1" in smoke_text and "group['zero_boundary_' + direction] = True" in smoke_text)
    check('actual_inverse_write_observation', "context['inverse'][group['batch']].index_copy_" in smoke_text and "fingerprint(torch, output) == fingerprint(torch, context['inverse'])" in smoke_text)
    check('real_WxWhWo_weight_gradients_and_updates_required', "('Wx', 'Wh', 'Wo')" in smoke_text and "g['abs_max'] > 0" in smoke_text and "record['weight_before_step_hash'][name] != record['weight_after_step_hash'][name]" in smoke_text)
    check('raw_csort_hcg_and_inst_mask_observers_present', all(value in smoke_text for value in ['original_raw_objects','PSBR_middle_exact_HCG_input','single_native_inst_update_exact','native_final_mask_gradients','maps_unchanged_after_full_forward']))
    check('no_HRC_specific_mean_or_probe_relabel', not any(value in (BUNDLE/'worker.py').read_text(encoding='utf-8') for value in ['refined_parent_mean','coarse_dependency_probe','fine_ffn_first_weight_gradient']))
    check('offdiagonal_not_implemented_and_pairing_unknown_are_explicit', 'NOT_IMPLEMENTED_NOT_MEASURED' in smoke_text and 'NOT_VALIDATED_BY_SINGLE_TARGET_WORKER' in smoke_text)
    check('observer_memory_not_pure_training', 'not pure TRAIN memory' in smoke_text and 'UNKNOWN; no separate no-observer native TRAIN process pair' in smoke_text)
    check('finally_restores_wrappers_and_hooks', any(isinstance(n,ast.Try) and any(isinstance(t,ast.For) and 'delattr(owner, name)' in ast.unparse(t) for t in n.finalbody) and 'hook.remove()' in ast.unparse(n.finalbody) for n in ast.walk(smoke)))
    check('no_torch_worker_runtime_imported_during_checks', 'torch' not in sys.modules and 'native_runtime' not in sys.modules and 'worker' not in sys.modules)
    result = {'schema_version':1,'status':'STATIC_PREPARATION_CHECKS_PASS_NATIVE_NOT_RUN',
        'candidate_id':CID,'experiment_id':'M209-PSBR','source_commit':COMMIT,
        'checked_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,
        'worker_sha256':sha(BUNDLE/'worker.py'),'runtime_sha256':sha(BUNDLE/'native_runtime.py'),
        'manifest_template_sha256':sha(BUNDLE/'manifest_template.json'),
        'resource_ast_sha256':hashlib.sha256(dump(resource).encode()).hexdigest(),
        'source_preparation_sha256':sha(SOURCE_PREP/'preparation.json'),
        'validate_static_sha256':sha(Path(__file__)),
        'actual_execution':{'torch':False,'native':False,'ssh':False,'gpu':False,'stage':False,'lease':False},
        'native_smoke':'NOT_RUN','standard_resources':'NOT_RUN','actual_pairing':'NOT_RUN',
        'offdiagonal_probe':'NOT_IMPLEMENTED','scientific_admission':False,
        'execution_adapter':'NOT_PREPARED; current owner must separately bind and stage',
        'claims_scope':'Syntax/source/manifest checks only; no raw native results, PASS receipt or queue entry generated'}
    if write:
        guard()
        (BUNDLE/'static_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    main(parser.parse_args().write)
