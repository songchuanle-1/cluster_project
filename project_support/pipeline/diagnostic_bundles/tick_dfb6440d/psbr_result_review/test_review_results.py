"""Offline read-only raw fixtures; mutate copies in memory, never native evidence."""
import copy
import json
from pathlib import Path
import unittest
import review_results as v
BASE=Path(__file__).resolve().parent.parent

def actual(name, family='psbr'):
    return json.loads((BASE/(family+'_execution')/(name+'_execution.json')).read_text(encoding='utf-8-sig'))['result']

class SchemaRefusalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=actual('smoke_candidate');cls.b=actual('smoke_champion');cls.r=actual('resources_candidate','hrc')
    def ccopy(self): return copy.deepcopy(self.c)
    def refuse(self, raw):
        with self.assertRaises((v.Refused,KeyError,TypeError,ValueError,IndexError)):v.smoke(raw,True)
    def test_real_smoke_schema_success(self):v.smoke(self.c,True);v.smoke(self.b,False)
    def test_native_loss_must_be_finite(self):
        x=self.ccopy();x['losses'][0]=float('nan');self.refuse(x)
    def test_native_backward_required(self):
        x=self.ccopy();x['native_criterion_backwards']=1;self.refuse(x)
    def test_Wh_weight_must_have_native_nonzero_gradient(self):
        x=self.ccopy();x['steps'][0]['tracked_module_gradients']['Wh']['weight']['abs_max']=0;self.refuse(x)
    def test_Wo_native_weight_update_required(self):
        x=self.ccopy();x['steps'][0]['weight_after_step_hash']['Wo']=x['steps'][0]['weight_before_step_hash']['Wo'];self.refuse(x)
    def test_actual_nonsingleton_required(self):
        x=self.ccopy();x['PSBR_recurrence_observations'][0]['nonsingleton_supported_parent_groups']=0;self.refuse(x)
    def test_boundary_reset_required(self):
        x=self.ccopy();x['PSBR_recurrence_observations'][0]['groups'][0]['wh_calls'][0]['input_state_is_zero']=False;self.refuse(x)
    def test_inverse_scatter_required(self):
        x=self.ccopy();x['PSBR_recurrence_observations'][0]['inverse_write_to_original_ids_exact']=False;self.refuse(x)
    def test_supported_domain_not_padding(self):
        x=self.ccopy();x['PSBR_recurrence_observations'][0]['groups'][0]['order'][0]=99999;self.refuse(x)
    def test_raw_csort_not_refined_substitution(self):
        x=self.ccopy();x['csort_raw_input_observations'][0]['original_raw_objects']=False;self.refuse(x)
    def test_HCG_must_receive_PSBR(self):
        x=self.ccopy();x['hcg_readbacks'][0]['PSBR_middle_exact_HCG_input']=False;self.refuse(x)
    def test_no_extra_inst_injection(self):
        x=self.ccopy();x['inst_to_mask_path_observations'][0]['new_extra_injection']=True;self.refuse(x)
    def test_common_hash_is_not_a_new_equality_gate(self):
        x=self.ccopy();x['common_initialized_parameters']['sha256']='0'*64;v.smoke(x,True)
    def test_resource_original_protocol_success(self):v.resources(self.r)
    def test_resource_handler_change_refused(self):
        x=copy.deepcopy(self.r);x['profile']['profiler_file_sha256']['jit_handles']='0'*64
        with self.assertRaises(v.Refused):v.resources(x)
    def test_resource_measurement_summary_recomputed(self):
        x=copy.deepcopy(self.r);x['median_ms']+=1
        with self.assertRaises(v.Refused):v.resources(x)
    def test_resource_no_training(self):
        x=copy.deepcopy(self.r);x['optimizer_steps']=1
        with self.assertRaises(v.Refused):v.resources(x)
    def test_resource_all_100_real_timings(self):
        x=copy.deepcopy(self.r);x['measurements_ms'].pop()
        with self.assertRaises(v.Refused):v.resources(x)

if __name__=='__main__':unittest.main()
