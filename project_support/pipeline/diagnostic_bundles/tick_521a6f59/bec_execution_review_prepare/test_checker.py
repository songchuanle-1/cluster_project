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
FROZEN=PROJECT/'pipeline/diagnostic_bundles/tick_521a6f59/bec_operational_prepare/native'
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
spec=importlib.util.spec_from_file_location('bec_schema_reviewer',HERE/'review_bec.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.FROZEN=FROZEN.relative_to(PROJECT).as_posix()
# Extract only original pure-stdlib metadata functions, never import native modules.
tree=ast.parse((FROZEN/'candidate_model/bipartite_edges.py').read_text(encoding='utf8'))
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_bipartite_plan')
env={};exec(compile(ast.Module(body=[node],type_ignores=[]),'<production-pure-plan>','exec'),env)
build=env['build_bipartite_plan']
worker=ast.parse((FROZEN/'worker.py').read_text(encoding='utf8'))
nodes=[n for n in worker.body if isinstance(n,ast.FunctionDef) and n.name in ('bec_membership_observation','bec_core_preflight')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<original-pure-support>','exec'),env)
preflight=env['bec_core_preflight']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
T=lambda shape,v=1.:dict(shape=list(shape),dtype='torch.float32',finite=True,nonfinite_count=0,abs_max=v)


def passed(name):checks.append(name)
def refuse(name,fn,inconclusive=False):
    try:fn()
    except (ValueError,KeyError,TypeError,OSError,StopIteration,AttributeError,IndexError) as e:
        if inconclusive:assert 'INCONCLUSIVE' in str(e),str(e)
        refusals.append({'case':name,'error_type':type(e).__name__,'reason':str(e)[:220]})
    else:raise AssertionError('Invalid fixture accepted: '+name)


def fixture_record(forward=1,optional=True,empty=False):
    # Raw/tensor values below are explicitly synthetic and remain in memory.
    widths=[7,5,4]
    members=[([0,0,2,3,4],[0,0,1,1,3,3],[0,0,2,2])]
    if not optional:members=[([0],[0],[0])]
    if empty:members=[([],[0],[0])]
    if optional:members.append(([],[0,1],[0,1])) # exercise empty means legally
    metas=json.loads(json.dumps(preflight(members)));batches=[];up=[];down=[];means=[]
    def op(b,name,rows):
        out=512 if name.startswith('up_') else 256
        call={'forward':forward,'batch':b,'operator':name,'input':T([rows,512]),'field_shapes':[[rows,256],[rows,256]],'field_sha256':['a'*64,'b'*64],
          'actual_original_branch_inputs_match':True,'actual_real_edges':rows,'linear_output':T([rows,out]),'output':T([rows,out]),'original_GELU_calls':1,
          **{k:'a'*64 for k in ('input_sha256','linear_output_sha256','output_sha256')},
          **{k:[T([rows,512 if k=='native_input_gradients' else out],0.)] for k in ('native_input_gradients','native_linear_output_gradients','native_output_gradients')}}
        if name.startswith('up_'):call.update(actual_split_views={'retained_sha256':'a'*64,'upward_sha256':'b'*64},native_split_output_gradients=[{'retained':T([rows,256],0.),'upward':T([rows,256],0.)}])
        return call
    for b,ids in enumerate(members):
        plan=json.loads(json.dumps(build(*ids,widths)));meta=metas['batches'][b]
        batches.append({'batch':b,'original_plan':plan,'true_support':meta,'fine_prefix':len(ids[1]),'middle_prefix':len(ids[2]),'coarse_prefix':plan['prefixes'][2],
          **{key:sorted(set(range(plan['prefixes'][i]))-set(plan[idskey])) for i,(key,idskey) in enumerate(zip(('unsupported_internal_fine_ids','unsupported_internal_middle_ids','unsupported_internal_coarse_ids'),('fine_ids','middle_ids','coarse_ids')))},
          'padding_rows':[w-k for w,k in zip(widths,plan['prefixes'])]})
        if meta['fine_edges']:up.append(op(b,'up_fine',meta['fine_edges']))
        if meta['middle_edges']:up.append(op(b,'up_middle',meta['middle_edges']))
        if meta['middle_edges']:down.append(op(b,'down_middle',meta['middle_edges']))
        if meta['fine_edges']:down.append(op(b,'down_fine',meta['fine_edges']))
        for level in (0,1):
            rows=meta['fine_edges' if level==0 else 'middle_edges'];groups=plan['fine_mean_groups' if level==0 else 'middle_mean_groups'];width=widths[level+1]
            mean={'forward':forward,'batch':b,'level':level,'groups':groups,'width':width,'input':T([rows,256]),'input_sha256':'b'*64,'output':T([width,256]),'output_sha256':'a'*64,
              'actual_supported_rows':rows,'original_mean_calls':1,'equal_child_row_counts':[len(v) for _,v in groups],'means_recomputed_by_observer':False}
            if rows:mean.update(native_mean_input_gradients=[T([rows,256],0.)],native_mean_output_gradients=[T([width,256],0.)])
            else:mean['empty_boundary_status']='NOT_EXERCISED_GRADIENT_PATH; legal zero private mean'
            means.append(mean)
    B=len(members)
    return {'fixture_scope':'SYNTHETIC_SCHEMA_ONLY_NOT_NATIVE','forward':forward,'fine_input':T([B,7,256]),'middle_input':T([B,5,256]),'coarse_raw_input':T([B,4,256]),
       'native_coverage_preflight':metas,'batches':batches,'operator_calls':up+down,'private_mean_calls':means,
       'actual_fine_edges':metas['fine_edges'],'actual_middle_edges':metas['middle_edges'],'core_path_observed':True,'actual_builder_calls':B,
       **{k:True for k in ('actual_two_up_split_private_mean_two_down_path','actual_original_coarse_skip_masked_and_consumed','original_ID_restoration_and_unsupported_padding_delta0_exact','actual_a2_enters_original_LN2','unsupported_coarse_bias_masked_in_reference')},
       'coarse_original_LN_FFN_calls':1,'original_LN_calls':{'0':1,'1':1,'2':1},'outputs':[T([B,w,256]) for w in widths],'output_sha256':['a'*64]*3,
       **{k:[T([B,7 if 'fine' in k or 'level0' in k else 5 if 'middle' in k or 'level1' in k else 4,256],0.)] for k in ('native_helper_level0_output_gradients','native_helper_level1_output_gradients','native_helper_level2_output_gradients','native_fine_norm_input_gradients','native_middle_norm_input_gradients','native_coarse_raw_input_gradients','native_collected_coarse_input_gradients')},
       **{k:'a'*64 for k in ('coarse_collected_input_sha256','coarse_actual_FFN_output_sha256','coarse_supported_mask_sha256','coarse_masked_delta_sha256')},'offdiagonal_dependency_probe':'NOT_IMPLEMENTED_NOT_MEASURED'}

record=fixture_record();r.bec_record(record);passed('synthetic_two_level_up_split_private_mean_coarse_once_down_schema_with_optional_holes_pad_empty_and_zero_callbacks')
r.bec_record(fixture_record(optional=False));passed('synthetic_single_child_core_accepted_no_degree2_or_optional_coverage_gate')
refuse('empty_core_inconclusive',lambda:r.bec_record(fixture_record(empty=True,optional=False)),True)
mutations={
 'up_input_not_original':lambda x:x['operator_calls'][0].update(actual_original_branch_inputs_match=False),
 'GELU_replayed':lambda x:x['operator_calls'][0].update(original_GELU_calls=2),
 'wrong_map_width':lambda x:x['operator_calls'][0]['linear_output'].update(shape=[4,256]),
 'wrong_edge_count':lambda x:x['operator_calls'][0].update(actual_real_edges=999),
 'missing_up_split':lambda x:x['operator_calls'][0].pop('actual_split_views'),
 'wrong_retained_down_source':lambda x:x['operator_calls'][-1]['field_sha256'].__setitem__(0,'f'*64),
 'wrong_upward_mean_source':lambda x:x['private_mean_calls'][0].update(input_sha256='f'*64),
 'mean_recomputed':lambda x:x['private_mean_calls'][0].update(means_recomputed_by_observer=True),
 'unequal_mean_groups':lambda x:x['private_mean_calls'][0].update(equal_child_row_counts=[999]),
 'coarse_FFN_twice':lambda x:x.update(coarse_original_LN_FFN_calls=2),
 'original_LN_missing':lambda x:x['original_LN_calls'].update({'1':0}),
 'coarse_mask_absent':lambda x:x.update(unsupported_coarse_bias_masked_in_reference=False),
 'skip_mask_not_consumed':lambda x:x.update(actual_original_coarse_skip_masked_and_consumed=False),
 'IDs_not_restored':lambda x:x.update(original_ID_restoration_and_unsupported_padding_delta0_exact=False),
 'faked_true_support':lambda x:x['batches'][0]['true_support'].update(fine_ids=[0]),
 'wrong_parent_map_length':lambda x:x['batches'][0]['original_plan']['fine_parent_ids'].append(0),
 'wrong_private_mean_rowgroup':lambda x:x['batches'][0]['original_plan']['fine_mean_groups'][0][1].append(99),
 'incomplete_beforewatch_preflight':lambda x:x['native_coverage_preflight'].update(fine_edges=999),
 'nonfinite_callback':lambda x:x['operator_calls'][0]['native_output_gradients'][0].update(finite=False,nonfinite_count=1),
 'missing_callback':lambda x:x['operator_calls'][0].update(native_output_gradients=[]),
 'unimplemented_probe_claimed':lambda x:x.update(offdiagonal_dependency_probe='MEASURED')}
for label,mutate in mutations.items():
    x=copy.deepcopy(record);mutate(x);refuse(label,lambda x=x:r.bec_record(x))

BLOCKS=[n+'_'+o+'_'+f for n in ('up_fine','up_middle') for o in ('retained','upward') for f in ('child','parent')]+[n+'_'+f for n in ('down_middle','down_fine') for f in ('retained','context')]
def step(forward=1,tracked=('ffn_2','up_fine','up_middle','down_middle','down_fine'),candidate=True):
    blocks=BLOCKS if candidate else [];before='a' if forward==1 else 'b';after='b' if forward==1 else 'c'
    return {'forward':forward,'gradient_tensor_count':2,'nonfinite_parameter_names':[],'all_observed_gradients_finite':True,'optimizer_step_completed':True,
        'tracked_module_gradients':{n:{'weight':T([1]),'bias':T([1],0.)} for n in tracked},
        **{key:{n:letter*64 for n in tracked} for key,letter in [('module_before_step_hash',before),('weight_before_step_hash',before),('module_after_step_hash',after),('weight_after_step_hash',after)]},
        'native_parameter_block_gradients':{n:T([256,256]) for n in blocks},
        'parameter_block_before_step_hash':{n:before*64 for n in blocks},'parameter_block_after_step_hash':{n:after*64 for n in blocks}}
r.required_weight_blocks({'steps':[step()]},True);passed('synthetic_twelve_aggregate_block_gradient_and_actual_slice_update_schema_accepted')
for name in BLOCKS:
    x=step();x['native_parameter_block_gradients'][name]['abs_max']=0.;refuse('zero_aggregate_'+name,lambda x=x:r.required_weight_blocks({'steps':[x]},True))
    x=step();x['parameter_block_after_step_hash'][name]=x['parameter_block_before_step_hash'][name];refuse('no_actual_slice_update_'+name,lambda x=x:r.required_weight_blocks({'steps':[x]},True))
x=step();x['native_parameter_block_gradients'].pop(BLOCKS[-1]);refuse('missing_twelfth_aggregate_block',lambda:r.required_weight_blocks({'steps':[x]},True))

manifest=r.read(FROZEN/'manifest_template.json')
manifest.update(stage='/data/songcl/Project/Cluster_project/pipeline/bec_aaaaaaaa_gpu0',current_token='a'*32,
 tick_generated_at='2026-10-25T20:00:00+00:00',deadline_at='2026-10-25T21:00:00+00:00',physical_gpu=0,
 gpu_uuid=r.UUIDS[0],allowed_gpus=[0,1],context_sha256='b'*64,pending_sha256='c'*64,runtime_code_commit=r.RUNTIME_EXPECTED)
INITIAL={'kind':'native_train_pretrain','seed':1999,'trained_m95_checkpoint_loaded':False,'path':manifest['assets']['pretrain'],'sha256':manifest['assets']['pretrain_sha256'],'loader':'gorilla.load_checkpoint(strict=False,map_location=cpu)'}
DATA={'train':{'prefix':'train','training':True,'data_root':'synthetic-only','type':'SyntheticSchemaFixture'}}
def base(mode,target):
    candidate=target=='candidate';selected=r.NAME+('_bec' if candidate else '')
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
    candidate=target=='candidate';x=base('smoke',target);levels=[2] if candidate else [0,1,2];tracked=['ffn_'+str(i) for i in levels]+(['up_fine','up_middle','down_middle','down_fine'] if candidate else [])
    x.update(optimizer_steps=2,native_loss_forwards=2,native_criterion_backwards=2,native_predict_calls=0,
        **{k:True for k in ('native_data_loaded','backward_finite','intended_path_observed','native_train_function_executed','native_smoke_checks_passed','observer_readout_complete','wrappers_and_hooks_restored','native_tracked_each_module_updated')},
        auxiliary_autograd_grad_or_backward_used=False,training_checkpoint_saved=False,native_failure_is_not_whole_mechanism_rejection=True,
        actual_train_command='SYNTHETIC_SCHEMA_FIXTURE',native_train_cli_reference=['SYNTHETIC_ONLY'],losses=[1.,2.],loss_tensor_observations=[T([]),T([])],loss_component_observations=[{'loss':T([])},{'loss':T([])}],
        steps=[step(i,tracked,candidate) for i in (1,2)],batches=[{'sha256':str(i)*64,'scan_ids':['synthetic-only-'+str(i)],'ann_ids':[i],'scenes_len':[1]} for i in (1,2)],native_backward_records=[{'forward':i,'count':1,'gradient':T([])} for i in (1,2)],
        ffn_calls=[{'forward':i,'level':level,'input':T([1,10,256]),'output':T([1,10,256]),'native_input_gradients':[T([1,10,256])],'native_output_gradients':[T([1,10,256])]} for i in (1,2) for level in levels],
        raw_bank_observations=[{'forward':i,'unchanged_after_full_forward':True,'ids_unchanged_after_full_forward':True,'maps_unchanged_after_full_forward':True,'raw_sha256':('a' if candidate else 'b')*64,'id_sha256':'a'*64,'map_sha256':'a'*64} for i in (1,2)],
        csort_raw_input_observations=[{'original_raw_objects':True,'original_childmap_object':True,'original_calls':1,'output':T([])} for _ in range(4)],
        hcg_readbacks=[{'output':T([1,11,256]),'native_point_message_gradients':[T([1,11,256])],'original_residual_levels':{} if candidate else {str(i):True for i in levels},'BEC_original_three_skip_HCG_inputs':[True]*3,'BEC_helper_coarse_object_exact':True} for _ in (1,2)],
        inst_to_mask_path_observations=[{'single_native_inst_update_exact':True,'new_extra_injection':False,'gate':T([]),**{k:[T([1,11,256])] for k in ('native_post_cluster_inst_gradients','native_post_ILA_inst_gradients','native_final_mask_gradients')}} for _ in (1,2)],
        native_tracked_initial_hash={n:'a'*64 for n in tracked},native_tracked_after_hash={n:'c'*64 for n in tracked},
        dynamic_parameter_inventory={'original_FFN_parameters_by_level':{'0':0 if candidate else 525568,'1':0 if candidate else 525568,'2':525568},'new_declared_parameters':787968 if candidate else 0,'new_registered_buffer_names':[],'actual_full_model_parameters':157220922 if candidate else 157484090},
        BEC_edge_observations=[fixture_record(forward=i) for i in (1,2)] if candidate else [],native_dataloader_config={'SYNTHETIC_ONLY':True},
        common_initialized_parameters={'names':['dec.cluster_att.cluster_ffn_norm.'+str(i)+'.weight' for i in range(3)]+['dec.cluster_att.cluster_ffn.2.weight'],'tensor_count':4,'parameter_count':4,'sha256':'a'*64,'excluded_name_prefixes':['dec.cluster_att.cluster_ffn.0.','dec.cluster_att.cluster_ffn.1.','dec.cluster_att.bipartite_edges.'],'scope':'SYNTHETIC_SCHEMA_ONLY'},
        offdiagonal_dependency_probe='NOT_IMPLEMENTED_NOT_MEASURED',pure_training_peak_memory='UNKNOWN; synthetic software fixture',smoke_memory_scope='SYNTHETIC_ONLY',smoke_peak_allocated_bytes=1024,smoke_peak_reserved_bytes=2048)
    if candidate:x['native_coverage_preflight_observations']=[v['native_coverage_preflight'] for v in x['BEC_edge_observations']]
    return x

def resource(target):
    x=base('resources',target);candidate=target=='candidate'
    x.update(batch_size=1,lang_num_max=1,warmup=20,repeat=100,optimizer_steps=0,native_loss_forwards=0,native_criterion_backwards=0,native_predict_calls=121,
        measurements_ms=[2. if candidate else 1.]*100,median_ms=2. if candidate else 1.,p90_ms=2. if candidate else 1.,input_sha256='a'*64,scan_ids=['synthetic-only'],ann_ids=[1],
        parameter_flags_preserved=True,source_body_executed_without_replacement=True,validation_accuracy_evaluated_for_selection=False,
        parameters=157220922 if candidate else 157484090,peak_allocated_bytes=1024,peak_reserved_bytes=2048,
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
 'HCG_skip_false':lambda x:x['smoke_candidate']['hcg_readbacks'][0].update(BEC_original_three_skip_HCG_inputs=[True,False,True]),
 'allobserved_nonfinite':lambda x:x['smoke_candidate']['steps'][0].update(all_observed_gradients_finite=False),
 'required_own_W_zero':lambda x:x['smoke_candidate']['steps'][0]['native_parameter_block_gradients'][BLOCKS[0]].update(abs_max=0.),
 'required_negative_slice_not_updated':lambda x:x['smoke_candidate']['steps'][0]['parameter_block_after_step_hash'].update({BLOCKS[-1]:'a'*64}),
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
x=copy.deepcopy(raws);x['smoke_candidate'].update(execution_completed=False,coverage_status='INCONCLUSIVE_ORIGINAL_BATCH_LACKS_BEC_CORE_EDGES')
refuse('actual_failure_coverage_classified_inconclusive',lambda:r.review_payloads(x,manifest),inconclusive=True)

# Exercise the unchanged four-request/envelope/hash shell entirely in memory.
# These objects never become execution files or a real validated review artifact.
# No live release/current candidate anchor is fabricated. In-memory directory-shell
# fixtures explicitly bypass only external-anchor configuration; production CLI
# below exercises the real configuration and must refuse missing actual anchors.
contract=r.read(HERE/'external_packet_contract.json')
r.FROZEN=Path(contract['native_preparation']['path']).parent.as_posix();r.PREP_SHA=contract['native_preparation']['sha256']
r.TEMPLATE_SHA=contract['manifest_template_sha256'];r.RELEASE=contract['static_release']['path'];r.RELEASE_SHA=contract['static_release']['sha256']
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
        return copy.deepcopy(objects[p.name]) if p.parent==virtual else read_original(FROZEN.parent/'release_template.json' if p==PROJECT/r.RELEASE else path)
    def fake_digest(path):
        p=Path(path).resolve()
        return hashlib.sha256(wire(objects[p.name])).hexdigest() if p.parent==virtual else digest_original(FROZEN.parent/'release_template.json' if p==PROJECT/r.RELEASE else path)
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
    'foreign_original_thread':lambda x:x['execution_binding.json']['owner'].update(thread_id='foreign-root'),
    'wrong_physical_UUID':lambda x:x['execution_binding.json'].update(gpu_uuid=r.UUIDS[1]),
    'candidate_as_runtime':lambda x:x['execution_binding.json'].update(runtime_code_commit=r.COMMIT),
}.items():
    x=copy.deepcopy(vm);mutation(x);refuse(label,lambda x=x:chain_check(x))

# Actual entry receives no actual raw directory and must return2 with no report.
saved=sys.argv;sys.argv=['review_bec.py','--project',str(PROJECT),'--execution-dir',str(HERE/'MISSING_ACTUAL_RESULTS')]
stdout=io.StringIO()
try:
    with contextlib.redirect_stdout(stdout):rc=r.main()
finally:sys.argv=saved
cli=json.loads(stdout.getvalue());assert rc==2 and cli['review_status']=='REFUSED_MISSING_OR_INVALID_ACTUAL_EVIDENCE' and cli['standard_PASS_receipt_queue_written'] is False
passed('actual_checker_CLI_missing_real_directory_refuses_no_standard_or_actual_success_report')

source=HERE/'review_bec.py';old=PROJECT/'pipeline/diagnostic_bundles/tick_f86d1cfa/cts_execution_review_prepare/review_cts.py'
fn=lambda p,n:next(x for x in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(x,ast.FunctionDef) and x.name==n)
assert ast.dump(fn(source,'resources'),include_attributes=False)==ast.dump(fn(old,'resources'),include_attributes=False)
passed('resource_validator_full_AST_unchanged_from_reviewed_BFC_shell')
assert all(k not in source.read_text(encoding='utf8') for k in ('actual_three_distinct_real_input_rows','actual_multiround_supported_parent_groups','native_output_half_gradients','left_output_from_left_input'))
passed('no_inherited_CTS_three_sources_rounds_or_BFC_halves_quadrants_gate')
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
