"""Software schema fixtures only. No native data/results/Torch execution."""
from pathlib import Path
from datetime import datetime,timezone
import ast
import argparse
import builtins
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
FROZEN=PROJECT/'pipeline/diagnostic_bundles/tick_6bdbcf77/cts_operational_prepare/native'
actions=[];checks=[];refusals=[]


def audit(event,args):
    if event=='subprocess.Popen' or event.startswith('socket.'):
        actions.append(event);raise AssertionError('Real process/network forbidden')


sys.addaudithook(audit)
original_import=builtins.__import__
def guarded_import(name,*args,**kwargs):
    assert not name.startswith(('torch','framework','gorilla')),'Native import forbidden'
    return original_import(name,*args,**kwargs)
builtins.__import__=guarded_import
spec=importlib.util.spec_from_file_location('cts_schema_reviewer',HERE/'review_cts.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.FROZEN=FROZEN.relative_to(PROJECT).as_posix()
build,describe,preflight=r.topology_functions()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
T=lambda shape,v=1.:dict(shape=list(shape),dtype='torch.float32',finite=True,nonfinite_count=0,abs_max=v)


def passed(name):checks.append(name)
def refuse(name,fn,inconclusive=False):
    try:fn()
    except (ValueError,KeyError,TypeError,OSError,StopIteration,AttributeError,IndexError) as e:
        if inconclusive:assert 'INCONCLUSIVE' in str(e),str(e)
        refusals.append({'case':name,'error_type':type(e).__name__,'reason':str(e)[:220]})
    else:raise AssertionError('Invalid fixture accepted: '+name)


def fixture_record(n=6,forward=1,optional=True):
    # Actual production metadata function is exercised; all tensor summaries below
    # are explicitly synthetic schema values and never saved as a raw result.
    if optional:
        counts=[1,1,0,2,1,1,1,0,1];parents=[0]*8+[1];width=10
    else:counts=[1]*n;parents=[0]*n;width=n
    centers=[[float(i//2),0.,0.] for i in range(len(counts))]
    groups,seq=describe(build(centers,parents,[x>0 for x in counts],64))
    for g in groups:g['batch']=0
    for c in seq:c['batch']=0
    groups=json.loads(json.dumps(groups));seq=json.loads(json.dumps(seq));calls=[]
    for i,entry in enumerate(seq):
        round_=entry['kind']=='round';rows=len(entry['own_ids']) if round_ else len(entry['original_ids'])
        negzero=not round_ or all(x is None for x in entry['negative_ids'])
        call={**entry,'forward':forward,'call_index':i,'actual_all_inputs_from_same_old_state':True,
            'no_fake_padded_triplet_participant':True,'cross_receiver_donor_reuse_is_legal':True,
            'duplicate_real_source_within_receiver':False,'activation_original_calls':1,
            'input':T([rows,768]),'linear_output':T([rows,256]),'output':T([rows,256]),
            'own_input':T([rows,256]),'positive_input':T([rows,256],1. if round_ else 0.),'negative_input':T([rows,256],0. if negzero else 1.),
            'native_input_gradients':[T([rows,768],1. if i==0 else 0.)],
            'native_linear_output_gradients':[T([rows,256],1. if i==0 else 0.)],
            'native_output_gradients':[T([rows,256],1. if i==0 else 0.)]}
        call.update({k:'a'*64 for k in ('input_sha256','linear_output_sha256','output_sha256','old_state_sha256','writeback_reference_sha256')})
        if round_:call.update(unpaired_carry_reference_exact=True,aliased_negative_slots_private_zero_observed=True)
        else:call['singleton_private_zero_neighbors']=True
        calls.append(call)
    rounds=[x for x in calls if x['kind']=='round']
    return {'fixture_scope':'SYNTHETIC_COMPONENT_SCHEMA_ONLY_NOT_NATIVE','forward':forward,
        'input':T([1,width,256]),'output':T([1,width,256]),'original_middle_norm_calls':1,'original_triadic_forward_calls':1,
        'returned_original_bank_shape':True,'original_ID_inverse_scatter_observed':True,
        'unsupported_and_batch_padding_update_zero':True,'final_writeback_from_actual_outputs_reference_exact':True,
        'actual_output_requires_grad':True,'self_exclusive_claim':False,
        'native_input_gradients':[T([1,width,256])],'native_output_gradients':[T([1,width,256])],
        'batches':[{'batch':0,'real_point_counts':counts,'middle_prefix':len(counts),'padded_width':width,'centers':centers,'parent_ids':parents,
            'true_supported_original_ids':[i for i,x in enumerate(counts) if x>0],
            'unsupported_internal_ids':[i for i,x in enumerate(counts) if not x],'batch_padding_rows':width-len(counts),
            'support_formula':'bincount(ids1[ids0],minlength=ids2.numel())>0'}],
        'groups':groups,'actual_builder_calls':1,'mix_calls':calls,
        'actual_three_distinct_real_input_rows':sum(c['three_distinct_real_input_rows'] for c in rounds),
        'actual_multiround_supported_parent_groups':sum(g['multiround'] for g in groups),
        'actual_dilated_round_calls':sum(c['round_index']>=1 for c in rounds),
        'actual_round_mix_calls':len(rounds),'actual_singleton_mix_calls':sum(c['kind']=='singleton' for c in calls),
        'actual_aliased_negative_zero_rows':sum(c['aliased_negative_zero_rows'] for c in rounds),
        'actual_supported_singleton_groups':sum(g['n']==1 for g in groups),
        'actual_unsupported_internal_rows':sum(x==0 for x in counts),'actual_padding_rows':width-len(counts),
        'offdiagonal_dependency_probe':'NOT_IMPLEMENTED_NOT_MEASURED'}


record=fixture_record();r.triadic_record(record);passed('synthetic_n6_alias_singleton_holes_padding_and_individual_zero_call_gradients_accepted')
r.triadic_record(fixture_record(4,optional=False));passed('synthetic_power2_n4_without_alias_singleton_padding_accepted_no_new_nonpower_or_optional_gate')
for n in (0,1,2,3):refuse('missing_actual_core_coverage_n'+str(n),lambda n=n:r.triadic_record(fixture_record(n,optional=False)),inconclusive=True)
mutations={
 'old_state_false':lambda x:x['mix_calls'][0].update(actual_all_inputs_from_same_old_state=False),
 'fake_pad_participant':lambda x:x['mix_calls'][0].update(no_fake_padded_triplet_participant=False),
 'source_alias_not_deduplicated':lambda x:x['mix_calls'][0].update(duplicate_real_source_within_receiver=True),
 'cross_receiver_reuse_wrongly_forbidden':lambda x:x['mix_calls'][0].update(cross_receiver_donor_reuse_is_legal=False),
 'activation_replay':lambda x:x['mix_calls'][0].update(activation_original_calls=2),
 'wrong_row_source_ID':lambda x:x['mix_calls'][0]['positive_ids'].reverse(),
 'wrong_round_offset':lambda x:x['mix_calls'][0].update(offset=9),
 'wrong_input_width':lambda x:x['mix_calls'][0]['input'].update(shape=[6,512]),
 'wrong_output_width':lambda x:x['mix_calls'][0]['output'].update(shape=[6,512]),
 'missing_call_gradient':lambda x:x['mix_calls'][0].update(native_output_gradients=[]),
 'nonfinite_call_gradient':lambda x:x['mix_calls'][0]['native_output_gradients'][0].update(finite=False,nonfinite_count=1),
 'private_alias_not_observed':lambda x:x['mix_calls'][1].update(aliased_negative_slots_private_zero_observed=False),
 'carry_not_exact':lambda x:x['mix_calls'][0].update(unpaired_carry_reference_exact=False),
 'singleton_nonzero_private_neighbor':lambda x:x['mix_calls'][-1]['positive_input'].update(abs_max=1.),
 'fake_self_exclusive':lambda x:x.update(self_exclusive_claim=True),
 'original_ID_not_restored':lambda x:x.update(original_ID_inverse_scatter_observed=False),
 'final_output_ref_not_exact':lambda x:x.update(final_writeback_from_actual_outputs_reference_exact=False),
 'requires_grad_lost':lambda x:x.update(actual_output_requires_grad=False),
 'coverage_count_fabricated':lambda x:x.update(actual_three_distinct_real_input_rows=999),
 'support_row_fabricated':lambda x:x['batches'][0].update(true_supported_original_ids=[0]),
 'wrong_geometry_group_order':lambda x:x['groups'][0]['order'].reverse(),
 'builder_call_missing':lambda x:x.update(actual_builder_calls=0),
 'middle_norm_replayed':lambda x:x.update(original_middle_norm_calls=2),
}
for label,mutation in mutations.items():
    x=copy.deepcopy(record);mutation(x);refuse(label,lambda x=x:r.triadic_record(x))

BLOCKS=['own_input','positive_input','negative_input']
def step(forward=1,tracked=('ffn_0','ffn_2','triadic_mix'),candidate=True):
    blocks=BLOCKS if candidate else [];before='a' if forward==1 else 'b';after='b' if forward==1 else 'c'
    return {'forward':forward,'gradient_tensor_count':2,'nonfinite_parameter_names':[],'all_observed_gradients_finite':True,'optimizer_step_completed':True,
        'tracked_module_gradients':{n:{'weight':T([1]),'bias':T([1],0.)} for n in tracked},
        **{key:{n:letter*64 for n in tracked} for key,letter in [('module_before_step_hash',before),('weight_before_step_hash',before),('module_after_step_hash',after),('weight_after_step_hash',after)]},
        'native_parameter_block_gradients':{n:T([256,256]) for n in blocks},
        'parameter_block_before_step_hash':{n:before*64 for n in blocks},'parameter_block_after_step_hash':{n:after*64 for n in blocks}}
r.required_weight_blocks({'steps':[step()]},True);passed('synthetic_three_aggregate_input_block_gradient_and_slice_update_schema_accepted')
for name in BLOCKS:
    x=step();x['native_parameter_block_gradients'][name]['abs_max']=0.;refuse('zero_aggregate_'+name,lambda x=x:r.required_weight_blocks({'steps':[x]},True))
    x=step();x['parameter_block_after_step_hash'][name]=x['parameter_block_before_step_hash'][name];refuse('no_actual_slice_update_'+name,lambda x=x:r.required_weight_blocks({'steps':[x]},True))
x=step();x['native_parameter_block_gradients'].pop('negative_input');refuse('missing_negative_aggregate_block',lambda:r.required_weight_blocks({'steps':[x]},True))

manifest=r.read(FROZEN/'manifest_template.json')
manifest.update(stage='/data/songcl/Project/Cluster_project/pipeline/cts_aaaaaaaa_gpu0',current_token='a'*32,
 tick_generated_at='2026-10-25T20:00:00+00:00',deadline_at='2026-10-25T21:00:00+00:00',physical_gpu=0,
 gpu_uuid=r.UUIDS[0],allowed_gpus=[0,1],context_sha256='b'*64,pending_sha256='c'*64,runtime_code_commit=r.RUNTIME_EXPECTED)
INITIAL={'kind':'native_train_pretrain','seed':1999,'trained_m95_checkpoint_loaded':False,'path':manifest['assets']['pretrain'],'sha256':manifest['assets']['pretrain_sha256'],'loader':'gorilla.load_checkpoint(strict=False,map_location=cpu)'}
DATA={'train':{'prefix':'train','training':True,'data_root':'synthetic-only','type':'SyntheticSchemaFixture'}}
def base(mode,target):
    candidate=target=='candidate';selected=r.NAME+('_cts' if candidate else '')
    return {'fixture_scope':'SYNTHETIC_SCHEMA_ONLY_NOT_ACTUAL_NATIVE_RESULT','execution_completed':True,'mode':mode,'target':target,'candidate_id':r.CID,'code_commit':r.COMMIT,'goal_sha256':r.GOAL,
        'model_package':'framework.model.Quard_model.'+selected,'source_hashes':manifest['candidate_source_hashes'] if candidate else manifest['assets']['source_hashes'],
        'native_model_and_yaml_unchanged':True,'config_sha256':r.YAML_SHA,'original_config_sha256':r.YAML_SHA,'runtime_config_sha256':'d'*64,
        'initialization':copy.deepcopy(INITIAL),'native_train_source_sha256':manifest['assets']['native_train_source_sha256'],
        'config_source':manifest['stage']+'/candidate.yaml' if candidate else manifest['assets']['config_path'],
        'runtime_config_path':manifest['stage']+'/runtime_config_'+mode+'_'+target+'/'+selected+'.yaml',
        'configuration_adaptations':{'dist':'False, native single-GPU CLI default','work_dir':{'from':'synthetic-production-workdir','to':manifest['stage']+'/native_'+mode+'_'+target}},
        'new_training':0,'data_source':copy.deepcopy(DATA),'experiment_id':r.EID,'config':r.CONFIG,'stage':manifest['stage'],'physical_gpu':0,'gpu_uuid':r.UUIDS[0],
        'diagnostic_worker_sha256':r.WORKER_SHA,'runtime_sha256':manifest['diagnostic_files']['native_runtime.py'],'source_preparation_sha256':r.SOURCE_PREP_SHA,
        **{k:manifest[k] for k in ('current_token','tick_generated_at','deadline_at','context_sha256','pending_sha256')}}

def smoke(target):
    candidate=target=='candidate';x=base('smoke',target);levels=[0,2] if candidate else [0,1,2];tracked=['ffn_'+str(i) for i in levels]+(['triadic_mix'] if candidate else [])
    x.update(optimizer_steps=2,native_loss_forwards=2,native_criterion_backwards=2,native_predict_calls=0,
        **{k:True for k in ('native_data_loaded','backward_finite','intended_path_observed','native_train_function_executed','native_smoke_checks_passed','observer_readout_complete','wrappers_and_hooks_restored','native_tracked_each_module_updated')},
        auxiliary_autograd_grad_or_backward_used=False,training_checkpoint_saved=False,native_failure_is_not_whole_mechanism_rejection=True,
        actual_train_command='SYNTHETIC_SCHEMA_FIXTURE',native_train_cli_reference=['SYNTHETIC_ONLY'],losses=[1.,2.],loss_tensor_observations=[T([]),T([])],loss_component_observations=[{'loss':T([])},{'loss':T([])}],
        steps=[step(i,tracked,candidate) for i in (1,2)],batches=[{'sha256':str(i)*64,'scan_ids':['synthetic-only-'+str(i)],'ann_ids':[i],'scenes_len':[1]} for i in (1,2)],native_backward_records=[{'forward':i,'count':1,'gradient':T([])} for i in (1,2)],
        ffn_calls=[{'forward':i,'level':level,'input':T([1,10,256]),'output':T([1,10,256]),'native_input_gradients':[T([1,10,256])],'native_output_gradients':[T([1,10,256])]} for i in (1,2) for level in levels],
        raw_bank_observations=[{'forward':i,'unchanged_after_full_forward':True,'ids_unchanged_after_full_forward':True,'maps_unchanged_after_full_forward':True,'raw_sha256':('a' if candidate else 'b')*64,'id_sha256':'a'*64,'map_sha256':'a'*64} for i in (1,2)],
        csort_raw_input_observations=[{'original_raw_objects':True,'original_childmap_object':True,'original_calls':1,'output':T([])} for _ in range(4)],
        hcg_readbacks=[{'output':T([1,11,256]),'native_point_message_gradients':[T([1,11,256])],'original_residual_levels':{str(i):True for i in levels},'CTS_middle_original_skip_and_exact_HCG_input':True} for _ in (1,2)],
        inst_to_mask_path_observations=[{'single_native_inst_update_exact':True,'new_extra_injection':False,'gate':T([]),**{k:[T([1,11,256])] for k in ('native_post_cluster_inst_gradients','native_post_ILA_inst_gradients','native_final_mask_gradients')}} for _ in (1,2)],
        native_tracked_initial_hash={n:'a'*64 for n in tracked},native_tracked_after_hash={n:'c'*64 for n in tracked},
        dynamic_parameter_inventory={'original_FFN_parameters_by_level':{'0':525568,'1':0 if candidate else 525568,'2':525568},'new_declared_parameters':196864 if candidate else 0,'geometry_registered_buffer_names':[],'actual_full_model_parameters':157155386 if candidate else 157484090},
        CTS_triadic_observations=[fixture_record(forward=i) for i in (1,2)] if candidate else [],native_dataloader_config={'SYNTHETIC_ONLY':True},
        common_initialized_parameters={'names':['dec.cluster_att.cluster_ffn_norm.1.weight','SYNTHETIC_COMMON'],'tensor_count':2,'parameter_count':2,'sha256':'a'*64,'excluded_name_prefixes':['dec.cluster_att.cluster_ffn.1.','dec.cluster_att.middle_triad.'],'scope':'SYNTHETIC_SCHEMA_ONLY'},
        offdiagonal_dependency_probe='NOT_IMPLEMENTED_NOT_MEASURED',pure_training_peak_memory='UNKNOWN; synthetic software fixture',smoke_memory_scope='SYNTHETIC_ONLY',smoke_peak_allocated_bytes=1024,smoke_peak_reserved_bytes=2048)
    if candidate:x['native_coverage_preflight_observations']=[preflight([(b['parent_ids'],[n>0 for n in b['real_point_counts']]) for b in v['batches']]) for v in x['CTS_triadic_observations']]
    return x

def resource(target):
    x=base('resources',target);candidate=target=='candidate'
    x.update(batch_size=1,lang_num_max=1,warmup=20,repeat=100,optimizer_steps=0,native_loss_forwards=0,native_criterion_backwards=0,native_predict_calls=121,
        measurements_ms=[2. if candidate else 1.]*100,median_ms=2. if candidate else 1.,p90_ms=2. if candidate else 1.,input_sha256='a'*64,scan_ids=['synthetic-only'],ann_ids=[1],
        parameter_flags_preserved=True,source_body_executed_without_replacement=True,validation_accuracy_evaluated_for_selection=False,
        parameters=157155386 if candidate else 157484090,peak_allocated_bytes=1024,peak_reserved_bytes=2048,
        profile={'profiler_file_sha256':r.HANDLERS,'flops':5e9,'flops_g':5.,'within10G':True,'unsupported_ops':{'synthetic_unsupported':3 if candidate else 1},'by_operator':{},'fvcore_version':'SYNTHETIC_SCHEMA_ONLY'},full_optimizer_training_peak='UNKNOWN; synthetic only')
    return x

raws={mode+'_'+target:smoke(target) if mode=='smoke' else resource(target) for mode,target in r.PAIRS}
facts=r.review_payloads(raws,manifest)
assert facts['resource_observations']['delta_p90_pct']==100. and facts['resource_observations']['unsupported_ops_candidate']=={'synthetic_unsupported':3}
assert facts['first_raw_bank_digest_comparison']['raw_sha256'] is False
passed('synthetic_complete_payload_schema_accepted_with_slower_latency_nonzero_unsupported_and_different_rawbank_no_new_gates')
for label,mutation in {
 'completed_string_only_not_semantics':lambda x:x['smoke_candidate'].update(losses=[]),
 'loss_nonfinite':lambda x:x['smoke_candidate'].update(losses=[float('nan'),1.]),
 'loss_bool':lambda x:x['smoke_candidate'].update(losses=[True,1.]),
 'one_optimizer_step':lambda x:x['smoke_candidate'].update(optimizer_steps=1),
 'extra_backward':lambda x:x['smoke_candidate'].update(native_criterion_backwards=3),
 'missing_loss_hook':lambda x:x['smoke_candidate']['native_backward_records'][0].update(count=0),
 'native_data_false':lambda x:x['smoke_candidate'].update(native_data_loaded=False),
 'native_flag_missing':lambda x:x['smoke_candidate'].pop('backward_finite'),
 'missing_input_pair':lambda x:x['smoke_candidate']['batches'][0].update(sha256='f'*64),
 'common_init_mismatch':lambda x:x['smoke_candidate']['common_initialized_parameters'].update(sha256='b'*64),
 'middleLN_omitted':lambda x:x['smoke_candidate']['common_initialized_parameters'].update(names=['x','y']),
 'old_seed':lambda x:x['smoke_candidate']['initialization'].update(seed=2000),
 'fullmodel_checkpoint':lambda x:x['smoke_candidate']['initialization'].update(trained_m95_checkpoint_loaded=True),
 'preflight_missing':lambda x:x['smoke_candidate'].pop('native_coverage_preflight_observations'),
 'extra_injection':lambda x:x['smoke_candidate']['inst_to_mask_path_observations'][0].update(new_extra_injection=True),
 'HCG_skip_false':lambda x:x['smoke_candidate']['hcg_readbacks'][0].update(CTS_middle_original_skip_and_exact_HCG_input=False),
 'allobserved_nonfinite':lambda x:x['smoke_candidate']['steps'][0].update(all_observed_gradients_finite=False),
 'required_own_W_zero':lambda x:x['smoke_candidate']['steps'][0]['native_parameter_block_gradients']['own_input'].update(abs_max=0.),
 'required_negative_slice_not_updated':lambda x:x['smoke_candidate']['steps'][0]['parameter_block_after_step_hash'].update(negative_input='a'*64),
 'wrong_new_param_inventory':lambda x:x['smoke_candidate']['dynamic_parameter_inventory'].update(new_declared_parameters=262656),
 'wrong_resource_sample':lambda x:x['resources_candidate'].update(input_sha256='f'*64),
 'changed_handler':lambda x:x['resources_candidate']['profile']['profiler_file_sha256'].update(flop_count='f'*64),
 'over_original10G':lambda x:x['resources_candidate']['profile'].update(flops=11e9,flops_g=11.,within10G=False),
 'unsupported_hidden':lambda x:x['resources_candidate']['profile'].pop('unsupported_ops'),
 'fewer_resource_samples':lambda x:x['resources_candidate'].update(measurements_ms=[1.]*99),
 'training_in_resource':lambda x:x['resources_candidate'].update(optimizer_steps=1),
 'fake_pureTRAIN':lambda x:x['resources_candidate'].update(full_optimizer_training_peak='MEASURED'),
}.items():
    x=copy.deepcopy(raws);mutation(x);refuse(label,lambda x=x:r.review_payloads(x,manifest))
for label,x in [('null_all',None),('empty_all',{}),('one_arm_only',{'smoke_candidate':raws['smoke_candidate']}),('null_arm',{**raws,'smoke_candidate':None})]:
    refuse(label,lambda x=x:r.review_payloads(x,manifest))
for value in (None,{},False,'execution_completed=true'):
    refuse('raw_object_'+repr(value),lambda value=value:r.common(value,manifest,'smoke','candidate'))
wrong=copy.deepcopy(manifest);wrong['runtime_code_commit']=r.COMMIT;refuse('candidate_commit_falsely_used_as_runtime',lambda:r.review_payloads(raws,wrong))
wrong=copy.deepcopy(manifest);wrong['physical_gpu']=True;refuse('bool_GPU',lambda:r.review_payloads(raws,wrong))
x=copy.deepcopy(raws);x['smoke_candidate'].update(execution_completed=False,coverage_status='INCONCLUSIVE_ORIGINAL_BATCH_LACKS_CORE_TRIADIC_PATH')
refuse('actual_failure_coverage_classified_inconclusive',lambda:r.review_payloads(x,manifest),inconclusive=True)

# Exercise the unchanged four-request/envelope/hash shell entirely in memory.
# These objects never become execution files or a real validated review artifact.
r.configure_current_anchors(PROJECT)
virtual=(HERE/'SYNTHETIC_IN_MEMORY_CHAIN_ONLY').resolve()
vm={};wire=lambda v:json.dumps(v,indent=2,allow_nan=False).encode()
owner={'token':'a'*32,'thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':manifest['tick_generated_at'],'deadline_at':manifest['deadline_at'],'context_sha256':manifest['context_sha256'],'pending_sha256':manifest['pending_sha256']}
manifest_hash=hashlib.sha256(wire(manifest)).hexdigest()
lease={'project':'cluster_project','thread_id':owner['thread_id'],'native_manifest_sha256':manifest_hash,'token':owner['token'],'generated_at':owner['generated_at'],'deadline_at':owner['deadline_at'],'server_id':'server-4','physical_gpu':0,'gpu_uuid':r.UUIDS[0],'allowed_gpus':[0,1],'goal_sha256':r.GOAL,'context_sha256':owner['context_sha256'],'pending_sha256':owner['pending_sha256']}
binding={'project':'cluster_project','candidate_id':r.CID,'code_commit':r.COMMIT,'goal_sha256':r.GOAL,'owner':owner,'frozen_preparation_sha256':r.PREP_SHA,'frozen_template_sha256':r.TEMPLATE_SHA,'adapter_release_sha256':r.RELEASE_SHA,'native_manifest_sha256':manifest_hash,'execution_lease_sha256':hashlib.sha256(wire(lease)).hexdigest(),'stage':manifest['stage'],'runtime_code_commit':r.RUNTIME_EXPECTED,'physical_gpu':0,'gpu_uuid':r.UUIDS[0],'server_binding':{'allowed_gpus':[0,1]}}
vm.update({'execution_binding.json':binding,'native_manifest.json':manifest,'execution_lease.json':lease})
for i,(mode,target) in enumerate(r.PAIRS,1):
    name=mode+'_'+target;raw=copy.deepcopy(raws[name]);raw['native_manifest_sha256']=manifest_hash
    identity={'project':'cluster_project','candidate_id':r.CID,'code_commit':r.COMMIT,'stage':manifest['stage'],'token':owner['token'],'request_id':str(i)*32,'operation':'run','physical_gpu':0,'gpu_uuid':r.UUIDS[0],'native_manifest_sha256':manifest_hash}
    command=['/synthetic/python','-B',manifest['stage']+'/worker.py','--lease',manifest['stage']+'/execution_lease.json','--mode',mode,'--target',target]
    vm[name+'_request.json']={**identity,'mode':mode,'target':target}
    vm[name+'_execution.json']={'identity':identity,'certainty':'terminal','returncode':0,'command':command,'pid':100+i,'original_process_identity':{'pid':100+i,'start_ticks':'123','argv':command},'result':raw,'result_sha256':hashlib.sha256(wire(raw)).hexdigest(),'stdout_sha256':'a'*64,'stderr_sha256':'b'*64}
read_original,digest_original=r.read,r.digest
def chain_check(objects):
    def fake_read(path):
        p=Path(path).resolve()
        return copy.deepcopy(objects[p.name]) if p.parent==virtual else read_original(path)
    def fake_digest(path):
        p=Path(path).resolve()
        return hashlib.sha256(wire(objects[p.name])).hexdigest() if p.parent==virtual else digest_original(path)
    with patch.object(r,'read',side_effect=fake_read),patch.object(r,'digest',side_effect=fake_digest):
        return r._review_directory_bound(PROJECT,virtual)
assert chain_check(vm)['review_status']=='RAW_SEMANTICS_VALIDATED_NOT_ADMISSION'
passed('synthetic_in_memory_four_original_request_envelope_hash_chain_schema_accepted_no_files_emitted')
for label,mutation in {
    'uncertain_envelope':lambda x:x['smoke_candidate_execution.json'].update(certainty='uncertain'),
    'bool_returncode':lambda x:x['smoke_candidate_execution.json'].update(returncode=False),
    'failed_process':lambda x:x['smoke_candidate_execution.json'].update(returncode=1),
    'missing_raw_result':lambda x:x['smoke_candidate_execution.json'].update(result=None),
    'wrong_remote_result_SHA':lambda x:x['smoke_candidate_execution.json'].update(result_sha256='f'*64),
    'wrong_request_target':lambda x:x['smoke_champion_request.json'].update(target='candidate'),
    'wrong_envelope_identity':lambda x:x['resources_candidate_execution.json']['identity'].update(request_id='f'*32),
    'wrong_original_argv':lambda x:x['smoke_candidate_execution.json']['original_process_identity'].update(argv=['foreign']),
    'wrong_constructed_command':lambda x:x['smoke_candidate_execution.json']['command'].__setitem__(2,'/foreign/worker.py'),
    'trim_owner_context':lambda x:x['execution_binding.json']['owner'].pop('context_sha256'),
    'wrong_physical_UUID':lambda x:x['execution_binding.json'].update(gpu_uuid=r.UUIDS[1]),
    'candidate_as_runtime':lambda x:x['execution_binding.json'].update(runtime_code_commit=r.COMMIT),
}.items():
    x=copy.deepcopy(vm);mutation(x);refuse(label,lambda x=x:chain_check(x))

# Actual entry receives no actual raw directory and must return2 with no report.
saved=sys.argv;sys.argv=['review_cts.py','--project',str(PROJECT),'--execution-dir',str(HERE/'MISSING_ACTUAL_RESULTS')]
stdout=io.StringIO()
try:
    with contextlib.redirect_stdout(stdout):rc=r.main()
finally:sys.argv=saved
cli=json.loads(stdout.getvalue());assert rc==2 and cli['review_status']=='REFUSED_MISSING_OR_INVALID_ACTUAL_EVIDENCE' and cli['standard_PASS_receipt_queue_written'] is False
passed('actual_checker_CLI_missing_real_directory_refuses_no_standard_or_actual_success_report')

source=HERE/'review_cts.py';old=PROJECT/'pipeline/diagnostic_bundles/tick_336ca5d7/bfc_execution_review_prepare/review_bfc.py'
fn=lambda p,n:next(x for x in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(x,ast.FunctionDef) and x.name==n)
assert ast.dump(fn(source,'resources'),include_attributes=False)==ast.dump(fn(old,'resources'),include_attributes=False)
passed('resource_validator_full_AST_unchanged_from_reviewed_BFC_shell')
assert 'nonpower' not in source.read_text(encoding='utf-8') and 'left_output_from_left_input' not in source.read_text(encoding='utf-8') and 'native_output_half_gradients' not in source.read_text(encoding='utf-8')
passed('no_inherited_BFC_nonpower_halves_fourquadrant_gate')
assert actions==[] and 'torch' not in sys.modules
result={'schema_version':1,'checked_at':datetime.now(timezone.utc).isoformat(),'result_kind':'ACTUAL_LOCAL_SOFTWARE_FIXTURE_CHECKS_ONLY_NOT_NATIVE','candidate_id':r.CID,'code_commit':r.COMMIT,
    'checker_sha256':sha(source),'test_source_sha256':sha(Path(__file__)),'logical_checks':checks,'logical_check_count':len(checks),'negative_refusal_cases':refusals,'negative_refusal_count':len(refusals),
    'synthetic_fixture_scope':'All populated raw/tensor values are in-memory software schema fixtures explicitly marked SYNTHETIC; none are saved as actual native results or four-result review evidence.',
    'actual_missing_result_CLI':cli,'real_process_network_events':actions,'torch_imported':False,'native_resources_TRAIN2':'NOT_RUN','actual_four_result_review':'NOT_RUN_NO_ACTUAL_RAW','standard_PASS_receipt_queue_written':False}
parser=argparse.ArgumentParser();parser.add_argument('--output',default='software_validation_final.json');args=parser.parse_args()
path=HERE/args.output
assert path.resolve().parent==HERE.resolve() and not path.exists()
with path.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
print(json.dumps({'logical_check_count':len(checks),'negative_refusal_count':len(refusals),'proof_sha256':sha(path),'actual_native':'NOT_RUN'}))
