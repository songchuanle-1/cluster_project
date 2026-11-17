"""Offline refusal fixtures only; synthetic values are never native evidence."""
import copy
import unittest
import review_results as v


def tensor(nonzero=True):
    return {'shape': [2, 3, 256], 'dtype': 'torch.float32', 'finite': True,
            'nonfinite_count': 0, 'abs_max': 1.0 if nonzero else 0.0}


def hashes(letter):
    return {str(k): letter * 64 for k in range(3)}


def fixture():
    """Explicit synthetic semantic fixture, no filesystem/native result files."""
    manifest = {'candidate_id': v.CID, 'code_commit': v.COMMIT, 'goal_sha256': v.GOAL,
                'config': v.CONFIG, 'tolerance': 1e-6, 'candidate_config_sha256': 'a'*64,
                'stage': '/synthetic/not-executed', 'candidate_source_hashes': {'refined_composition.py': 'c'*64},
                'assets': {'source_hashes': {'network.py': 'd'*64}, 'config_path': '/synthetic/original.yaml',
                           'pretrain': '/synthetic/pretrain.pth', 'pretrain_sha256': 'b'*64,
                           'native_train_source_sha256': 'e'*64}}
    raws = {}
    for mode, target in v.PAIRS:
        candidate = target == 'candidate'
        raw = {'execution_completed': True, 'mode': mode, 'target': target, 'candidate_id': v.CID,
               'code_commit': v.COMMIT, 'goal_sha256': v.GOAL, 'new_training': 0,
               'model_package': 'framework.model.Quard_model.' + v.NAME + ('_hrc' if candidate else ''),
               'source_hashes': manifest['candidate_source_hashes'] if candidate else manifest['assets']['source_hashes'],
               'native_model_and_yaml_unchanged': True, 'config_sha256': 'a'*64, 'original_config_sha256': 'a'*64,
               'runtime_config_sha256': 'f'*64, 'native_train_source_sha256': 'e'*64,
               'initialization': {'kind': 'native_train_pretrain', 'seed': 1999, 'trained_m95_checkpoint_loaded': False,
                                  'path': '/synthetic/pretrain.pth', 'sha256': 'b'*64,
                                  'loader': 'gorilla.load_checkpoint(strict=False,map_location=cpu)'},
               'config_source': manifest['stage']+'/candidate.yaml' if candidate else manifest['assets']['config_path'],
               'runtime_config_path': manifest['stage']+'/runtime_config_'+mode+'_'+target+'/'+v.NAME+('_hrc' if candidate else '')+'.yaml',
               'configuration_adaptations': {'work_dir': {'from': '/synthetic/work', 'to': manifest['stage']+'/native_'+mode+'_'+target},
                                            'dist': 'False, native single-GPU CLI default'},
               'data_source': {'train': {'training': True, 'prefix': 'train', 'data_root': '/synthetic/data'}}}
        if mode == 'resources':
            raw.update(batch_size=1, lang_num_max=1, warmup=20, repeat=100, optimizer_steps=0,
                       native_loss_forwards=0, native_criterion_backwards=0, native_predict_calls=121,
                       measurements_ms=list(range(1, 101)), median_ms=50.5, p90_ms=90.1,
                       input_sha256='1'*64, scan_ids=['synthetic'], ann_ids=[1], parameter_flags_preserved=True,
                       source_body_executed_without_replacement=True, validation_accuracy_evaluated_for_selection=False,
                       parameters=1000, peak_allocated_bytes=900, peak_reserved_bytes=1000,
                       profile={'profiler_file_sha256': v.HANDLERS.copy(), 'flops': 9e9, 'flops_g': 9.0,
                                'within10G': True, 'unsupported_ops': {'aten::index_add_': 2}, 'by_operator': {}, 'fvcore_version': 'fixture'},
                       full_optimizer_training_peak='UNKNOWN; synthetic fixture')
        else:
            raw.update({k: True for k in ('native_data_loaded', 'native_train_function_executed', 'backward_finite',
                                          'native_ffn_each_level_updated', 'observer_readout_complete', 'native_smoke_checks_passed',
                                          'wrappers_and_hooks_restored', 'native_smoke_training')})
            raw.update(intended_path_observed=candidate, training_checkpoint_saved=False, optimizer_steps=2,
                       native_loss_forwards=2, native_criterion_backwards=2, losses=[1.0, 2.0],
                       actual_train_command='tools.train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)',
                       native_dataloader_config={'batch_size': 2, 'num_workers': 4, 'persistent_workers': True},
                       batches=[{'sha256': str(i)*64, 'scan_ids': ['synthetic'], 'ann_ids': [i], 'scenes_len': [1]} for i in (1, 2)],
                       native_ffn_initial_hash_by_level=hashes('1'), native_ffn_after_hash_by_level=hashes('2'),
                       steps=[], ffn_calls=[], raw_bank_observations=[], csort_raw_input_observations=[], hcg_readbacks=[],
                       refined_parent_mean_calls=[], coarse_dependency_probes=[], new_operator_parameters=0 if candidate else None,
                       smoke_peak_allocated_bytes=7000, smoke_peak_reserved_bytes=8000, smoke_memory_scope='Synthetic observer fixture',
                       pure_training_peak_memory='UNKNOWN; synthetic fixture')
            for forward in (1, 2):
                raw['steps'].append({'all_observed_gradients_finite': True, 'nonfinite_parameter_names': [], 'gradient_tensor_count': 3,
                                     'optimizer_step_completed': True, 'ffn_by_level': {str(k): {'weight': tensor()} for k in range(3)},
                                     'ffn_before_step_hash': hashes('1'), 'ffn_after_step_hash': hashes('2')})
                for level in range(3):
                    raw['ffn_calls'].append({'forward': forward, 'level': level, 'input': tensor(), 'output': tensor(),
                                             'native_input_gradients': [tensor()], 'native_output_gradients': [tensor()]})
                raw['raw_bank_observations'].append({'unchanged_after_full_forward': True, 'ids_unchanged_after_full_forward': True,
                                                     'maps_unchanged_after_full_forward': True, 'levels': [tensor()]*3,
                                                     'raw_sha256': '3'*64, 'id_sha256': '4'*64, 'map_sha256': '5'*64})
                raw['csort_raw_input_observations'].extend([{'forward': forward, 'pair': k, 'original_raw_objects': True,
                                                            'original_calls': 1, 'output': tensor()} for k in (0, 1)])
                raw['hcg_readbacks'].append({'fine_original_residual_abs_max': 0.0, 'levels': [tensor()]*3,
                                             'output': tensor(), 'native_point_message_gradients': [tensor()]})
                if candidate:
                    raw['refined_parent_mean_calls'].extend([{'forward': forward, 'level': k, 'original_call_count': 1,
                        'reference_tolerance': 1e-6, 'reference_abs_max': 0.0, 'child': tensor(), 'output': tensor(),
                        'native_child_gradients': [tensor()], 'native_output_gradients': [tensor()],
                        'batches': [{'empty_parent_zero_before_ffn': True, 'parent_padding_zero_before_ffn': True,
                                     'child_prefix': 3, 'child_padded_width': 3,
                                     'empty_child_id_slots_from_adjacent_ids': 0, 'child_slots_without_real_point_support': 0,
                                     'empty_parent_id_slots': 0, 'parent_real_width': 2, 'parent_padded_width': 2}]} for k in (1, 2)])
                probe = {k: True for k in ('parameter_grad_state_unchanged', 'optimizer_state_unchanged', 'scheduler_state_unchanged',
                                           'cpu_rng_unchanged', 'cuda_rng_unchanged', 'autograd_grad_only', 'retain_graph')}
                probe.update(probe_backward_or_step_called=False, parameter_grad_sha256_before='6'*64,
                             parameter_grad_sha256_after='6'*64, support=[{'coarse_ids_reached_by_real_points': [0]}],
                             fine_ffn_first_weight_gradient=tensor() if candidate else None,
                             middle_ffn_first_weight_gradient=tensor() if candidate else None)
                raw['coarse_dependency_probes'].append(probe)
        raws[mode+'_'+target] = raw
    return raws, manifest


class RefusalFixtures(unittest.TestCase):
    def check_rejected(self, mutate):
        raws, manifest = fixture(); mutate(raws, manifest)
        with self.assertRaises((v.Refused, KeyError)):
            v.review_payloads(raws, manifest)

    def test_complete_synthetic_schema_only_no_native_evidence(self):
        raws, manifest = fixture(); result = v.review_payloads(raws, manifest)
        self.assertFalse(result['admission_authorized_by_this_report'])
        self.assertEqual(result['resource_observations']['unsupported_ops_candidate'], {'aten::index_add_': 2})

    def test_missing_raw_cannot_default_to_success(self):
        self.check_rejected(lambda r,m: r.pop('smoke_candidate'))

    def test_incomplete_execution_refused(self):
        self.check_rejected(lambda r,m: r['smoke_candidate'].update(execution_completed=False))

    def test_nonfinite_loss_refused(self):
        self.check_rejected(lambda r,m: r['smoke_candidate'].update(losses=[float('nan'), 2]))

    def test_no_backward_count_refused(self):
        self.check_rejected(lambda r,m: r['smoke_candidate'].update(native_criterion_backwards=0))

    def test_frozen_mean_tolerance_boundary(self):
        raws, manifest = fixture(); raws['smoke_candidate']['refined_parent_mean_calls'][0]['reference_abs_max'] = 1e-6
        v.review_payloads(raws, manifest)
        self.check_rejected(lambda r,m: r['smoke_candidate']['refined_parent_mean_calls'][0].update(reference_abs_max=1.000001e-6))

    def test_wrong_batches_refused(self):
        self.check_rejected(lambda r,m: r['smoke_candidate']['batches'][1].update(sha256='7'*64))

    def test_wrong_initial_weights_refused(self):
        self.check_rejected(lambda r,m: r['smoke_candidate']['native_ffn_initial_hash_by_level'].update({'0': '8'*64}))

    def test_probe_contamination_refused(self):
        self.check_rejected(lambda r,m: r['smoke_candidate']['coarse_dependency_probes'][0].update(scheduler_state_unchanged=False))

    def test_control_coarse_path_must_be_unused(self):
        self.check_rejected(lambda r,m: r['smoke_champion']['coarse_dependency_probes'][0].update(fine_ffn_first_weight_gradient=tensor()))

    def test_handler_change_refused(self):
        self.check_rejected(lambda r,m: r['resources_candidate']['profile'].update(profiler_file_sha256={}))

    def test_resource_count_and_flops_refused(self):
        self.check_rejected(lambda r,m: r['resources_candidate'].update(measurements_ms=[1.0]*99))
        self.check_rejected(lambda r,m: r['resources_candidate']['profile'].update(flops=10.1e9, flops_g=10.1, within10G=False))

    def test_memory_condition_reported_not_invented_pure_train(self):
        raws, manifest = fixture(); raws['resources_candidate']['peak_allocated_bytes'] = 1100
        result = v.review_payloads(raws, manifest)
        self.assertTrue(result['existing_memory_condition_needs_separate_retention_decision'])
        self.assertIn('UNKNOWN', result['resource_observations']['pure_training_peak'])

    def test_raw_output_digest_difference_is_disclosure_not_new_gate(self):
        raws, manifest = fixture(); raws['smoke_candidate']['raw_bank_observations'][0]['raw_sha256'] = '9'*64
        result = v.review_payloads(raws, manifest)
        self.assertFalse(result['first_raw_bank_digest_comparison']['raw_sha256'])


if __name__ == '__main__':
    unittest.main()
