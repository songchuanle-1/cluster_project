"""Actual JSON-only BFC result audit. No model/source imports or actions."""
from pathlib import Path
from datetime import datetime,timezone
import copy
import hashlib
import json
import math
import statistics

PROJECT=Path('D:/project/cluster_project')
TICK=Path(__file__).resolve().parent.parent
EXECUTION=TICK/'bfc_execution'
CID='hierarchy-parent-butterfly-token-composition'
COMMIT='48fc302c3c02ffef0b241be3593c386b6b65a72e'
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
PAIRS=[('smoke','champion'),('smoke','candidate'),('resources','champion'),('resources','candidate')]
BLOCKS=('left_output_from_left_input','left_output_from_right_input','right_output_from_left_input','right_output_from_right_input')
HANDLERS={'flop_count':'b5a02604a883bcda75deb918d68639d207c433938cf27e7034dd6de26a2956ba','jit_analysis':'110f30463ba9f20a86dc1f7a447bed29fe6d55dfedff4a30e05e955e47cacb31','jit_handles':'ef3a1d20ccad504bfdab7d2a127bce9483de1125d170d915d22f4addbc36c129'}
count=0
def need(value,message):
    global count
    count+=1
    if not value:raise ValueError(message)
def read(path):
    def reject(value):raise ValueError('Nonstandard JSON number '+value)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),parse_constant=reject)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path):return {'path':Path(path).relative_to(PROJECT).as_posix(),'sha256':sha(path)}
def linux_sha(value):return hashlib.sha256(json.dumps(value,indent=2,allow_nan=False).encode('utf-8')).hexdigest()
def finite(x):return type(x) in (int,float) and math.isfinite(x)
def tensor(v,nonzero=False,shape=None):
    need(v['finite'] is True and v['nonfinite_count']==0 and finite(v['abs_max']) and v['abs_max']>=0,'Malformed/nonfinite actual tensor summary')
    if nonzero:need(v['abs_max']>0,'Required aggregate original-loss path is zero')
    if shape is not None:need(v['shape']==shape,'Actual tensor shape differs')
def gradients(record,key,nonzero=False):
    need(record.get(key) and isinstance(record[key],list),'Missing native loss-gradient hook '+key)
    for value in record[key]:tensor(value,nonzero)

binding=read(EXECUTION/'execution_binding.json');manifest=read(EXECUTION/'native_manifest.json');lease=read(EXECUTION/'execution_lease.json')
need(binding['candidate_id']==CID and binding['code_commit']==COMMIT and binding['goal_sha256']==GOAL,'Binding identity differs')
need(type(binding['physical_gpu']) is int and binding['physical_gpu']==0 and binding['gpu_uuid']=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c','Wrong original selected GPU')
need(binding['stage']=='/data/songcl/Project/Cluster_project/pipeline/bfc_'+binding['owner']['token'][:8]+'_gpu0','Wrong actual stage')
need(sha(EXECUTION/'native_manifest.json')==binding['native_manifest_sha256'] and sha(EXECUTION/'execution_lease.json')==binding['execution_lease_sha256'],'Original manifest/lease hash drift')
need(set(binding['owner'])=={'token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256'},'Original owner field inventory differs')
need(binding['runtime_code_commit']=='11a811618179ab1ddc0cee299194667413b7fdb9','Runtime/source distinction differs')
frozen=PROJECT/'pipeline/diagnostic_bundles/tick_64ac844e/bfc_operational_prepare/native'
need(sha(frozen/'preparation.json')==binding['frozen_preparation_sha256']=='0c50b957129c44367d63ade6984d997fa1e0a22c59469a2355542095d0f25cf5','Frozen native preparation differs')
need(sha(frozen/'manifest_template.json')==binding['frozen_template_sha256']=='4d9caaab1e857fda73e9c2ef863ec815c2a81f26f128d614cb1368826e21ddb5','Frozen template differs')
expected_manifest=read(frozen/'manifest_template.json');o=binding['owner']
expected_manifest.update(current_token=o['token'],stage=binding['stage'],tick_generated_at=o['generated_at'],deadline_at=o['deadline_at'],physical_gpu=0,gpu_uuid=binding['gpu_uuid'],allowed_gpus=binding['server_binding']['allowed_gpus'],context_sha256=o['context_sha256'],pending_sha256=o['pending_sha256'],runtime_code_commit=binding['runtime_code_commit'])
need(expected_manifest==manifest,'Actual manifest is not exact original template/binding')
need(lease=={'project':'cluster_project','thread_id':o['thread_id'],'native_manifest_sha256':binding['native_manifest_sha256'],'token':o['token'],'generated_at':o['generated_at'],'deadline_at':o['deadline_at'],'server_id':'server-4','physical_gpu':0,'gpu_uuid':binding['gpu_uuid'],'allowed_gpus':binding['server_binding']['allowed_gpus'],'goal_sha256':GOAL,'context_sha256':o['context_sha256'],'pending_sha256':o['pending_sha256']},'Lease differs from original immutable owner/binding')
raws={};envelopes={};requests={};raw_refs=[];early_identity=[]
for mode,target in PAIRS:
    arm=mode+'_'+target;path=EXECUTION/(arm+'_execution.json');env=read(path);req=read(EXECUTION/(arm+'_request.json'));raw=env['result']
    identity={'project':'cluster_project','candidate_id':CID,'code_commit':COMMIT,'stage':binding['stage'],'token':o['token'],'request_id':req['request_id'],'operation':'run','physical_gpu':0,'gpu_uuid':binding['gpu_uuid'],'native_manifest_sha256':binding['native_manifest_sha256']}
    need(req==dict(identity,mode=mode,target=target) and env['identity']==identity,'Original request identity differs')
    need(env['certainty']=='terminal' and type(env['returncode']) is int and env['returncode']==0 and raw['execution_completed'] is True,'Arm not terminal rc0/completed')
    need(linux_sha(raw)==env['result_sha256'],'Original Linux result serialization SHA differs')
    need((raw['mode'],raw['target'],raw['candidate_id'],raw['code_commit'],raw['goal_sha256'])==(mode,target,CID,COMMIT,GOAL),'Actual raw identity differs')
    need(raw['native_manifest_sha256']==binding['native_manifest_sha256'] and all(raw[k]==manifest[k] for k in ('stage','physical_gpu','gpu_uuid','current_token','tick_generated_at','deadline_at','context_sha256','pending_sha256')),'Actual raw original binding differs')
    need(raw['diagnostic_worker_sha256']==manifest['diagnostic_files']['worker.py']=='8839251920577921493b0b663df123c330b850b08779c9841d1d98bbe26e813e' and raw['runtime_sha256']==manifest['diagnostic_files']['native_runtime.py'],'Actual worker/runtime hashes differ')
    need(raw['source_hashes']==(manifest['candidate_source_hashes'] if target=='candidate' else manifest['assets']['source_hashes']),'Raw source inventory/hash differs')
    need(raw['config_sha256']==raw['original_config_sha256']==manifest['candidate_config_sha256']=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a','Original YAML differs')
    need(raw['native_train_source_sha256']==manifest['assets']['native_train_source_sha256'] and raw['native_model_and_yaml_unchanged'] is True,'Native train/source contract differs')
    init=raw['initialization'];need(init['kind']=='native_train_pretrain' and init['seed']==1999 and init['trained_m95_checkpoint_loaded'] is False and init['sha256']==manifest['assets']['pretrain_sha256'] and init['path']==manifest['assets']['pretrain'],'Original native pretrain/seed differs')
    package='framework.model.Quard_model.'+manifest['name']+('_bfc' if target=='candidate' else '')
    need(raw['model_package']==package and raw['experiment_id']=='M213-BFC' and raw['config']==manifest['config'],'Wrong actual model resolver')
    tail=['-B',binding['stage']+'/worker.py','--lease',binding['stage']+'/execution_lease.json','--mode',mode,'--target',target]
    proc=env['original_process_identity'];need(env['command'][1:]==tail and proc['argv'] in (env['command'],[]) and proc['pid']==env['pid'] and str(proc['start_ticks']).isdigit(),'Original command/PID identity record differs')
    early_identity.append({'arm':arm,'pid':env['pid'],'start_ticks':proc['start_ticks'],'early_proc_argv_observed_equal':proc['argv']==env['command'],'limitation':'Empty early /proc argv is unobserved, not proof for a future signal. Direct immutable command/terminal wait/result and saved read-only reconciliation are separately checked.'})
    raw_refs.append({'mode':mode,'target':target,'execution_path':path.relative_to(PROJECT).as_posix(),'execution_sha256':sha(path),'result_sha256':env['result_sha256'],'request_id':identity['request_id']})
    raws[arm]=raw;envelopes[arm]=env;requests[arm]=req

def expected_scalar_metadata(record):
    """Independent block-pair oracle from actual JSON, never production code."""
    allgroups=[];sequence=[]
    for batch in record['batches']:
        centers,parents,counts=batch['centers'],batch['parent_ids'],batch['real_point_counts'];k=batch['middle_prefix'];width=batch['padded_width']
        need(len(centers)==len(parents)==len(counts)==k<=width,'Native geometry/support prefix differs')
        support=[i for i,n in enumerate(counts) if n>0]
        need(batch['true_supported_original_ids']==support and batch['unsupported_internal_ids']==[i for i,n in enumerate(counts) if n==0] and batch['batch_padding_rows']==width-k,'Actual original support/padding count differs')
        groups=[]
        for parent in sorted(set(parents[i] for i in support)):
            order=sorted([i for i in support if parents[i]==parent],key=lambda i:tuple(centers[i])+ (i,));n=len(order);m=(n-1).bit_length();bits=list(range(m))+list(range(m-2,-1,-1))
            groups.append({'parent':parent,'order':order,'n':n,'bits':bits,'nonpower_of_two':n>1 and bool(n&(n-1)),'multistage':len(bits)>1,'batch':batch['batch']})
        active=set(support)
        for r in range(max([len(g['bits']) for g in groups]+[0])):
            pairs=[]
            for g in groups:
                if r>=len(g['bits']):continue
                bit=g['bits'][r];stride=2**bit;n=g['n'];order=g['order']
                # Pair lower/upper halves of each block, truncating actual n.
                for start in range(0,n,2*stride):
                    for left in range(start,min(start+stride,n)):
                        right=left+stride
                        if right<n:pairs.append([g['parent'],bit,order[left],order[right]])
            used=[i for pair in pairs for i in pair[2:]];need(len(used)==len(set(used)),'Scalar oracle matching overlaps')
            sequence.append({'kind':'round','round_index':r,'pairs':pairs,'left_ids':[p[2] for p in pairs],'right_ids':[p[3] for p in pairs],'participant_ids':sorted(used),'unpaired_active_ids':sorted(active-set(used)),'batch':batch['batch']})
        single=[g['order'][0] for g in groups if g['n']==1]
        if single:sequence.append({'kind':'singleton','original_ids':single,'batch':batch['batch']})
        allgroups.extend(groups)
    return allgroups,sequence

native_summary={};topology_summary=[];half_zero_counts={'left':0,'right':0,'events':0}
for target in ('champion','candidate'):
    raw=raws['smoke_'+target];candidate=target=='candidate'
    need(type(raw['optimizer_steps']) is int and raw['optimizer_steps']==raw['native_loss_forwards']==raw['native_criterion_backwards']==2 and raw['native_predict_calls']==0,'Original TRAIN2 counts differ')
    need(len(raw['losses'])==2 and all(finite(v) for v in raw['losses']) and raw['data_source']['train']['prefix']=='train' and raw['data_source']['train']['training'] is True,'Actual finite TRAIN losses/data missing')
    for key in ('native_data_loaded','backward_finite','intended_path_observed','native_train_function_executed','native_smoke_checks_passed','observer_readout_complete','wrappers_and_hooks_restored','native_tracked_each_module_updated'):need(raw[key] is True,'Actual native flag absent '+key)
    need(raw['auxiliary_autograd_grad_or_backward_used'] is False and raw['training_checkpoint_saved'] is False,'Extra backward/checkpoint altered diagnostic')
    for key in ('steps','batches','native_backward_records','raw_bank_observations','hcg_readbacks','inst_to_mask_path_observations'):need(len(raw[key])==2,'Missing two-forward records '+key)
    need(len(raw['ffn_calls'])==(4 if candidate else 6) and len(raw['csort_raw_input_observations'])==4 and len(raw['BFC_butterfly_observations'])==(2 if candidate else 0),'Original/new branch counts differ')
    tracked={'ffn_0','ffn_2','butterfly_mix'} if candidate else {'ffn_0','ffn_1','ffn_2'}
    need(set(raw['native_tracked_initial_hash'])==set(raw['native_tracked_after_hash'])==tracked,'Tracked module inventory differs')
    for index,step in enumerate(raw['steps']):
        need(step['optimizer_step_completed'] is True and step['all_observed_gradients_finite'] is True and step['nonfinite_parameter_names']==[] and step['gradient_tensor_count']>0,'Native optimizer/finite evidence incomplete')
        need(set(step['tracked_module_gradients'])==tracked,'Actual original FFN/mix gradient inventory differs')
        for name,grads in step['tracked_module_gradients'].items():
            for parameter,value in grads.items():need(value is not None,'Tracked grad absent');tensor(value,parameter.endswith('weight'))
            need(step['module_before_step_hash'][name]!=step['module_after_step_hash'][name] and step['weight_before_step_hash'][name]!=step['weight_after_step_hash'][name],'Tracked actual weight update absent')
            need(step['module_before_step_hash'][name]==(raw['native_tracked_initial_hash'][name] if index==0 else raw['steps'][index-1]['module_after_step_hash'][name]),'Native module continuity differs')
        need(set(step['native_parameter_block_gradients'])==(set(BLOCKS) if candidate else set()),'Actual four W quadrant evidence differs')
        for name,value in step['native_parameter_block_gradients'].items():
            tensor(value,True,[256,256]);need(step['parameter_block_before_step_hash'][name]!=step['parameter_block_after_step_hash'][name],'Actual quadrant slice did not update')
            if index:need(step['parameter_block_before_step_hash'][name]==raw['steps'][index-1]['parameter_block_after_step_hash'][name],'Quadrant update continuity differs')
    for record in raw['native_backward_records']:need(record['count']==1,'Extra original criterion backward');tensor(record['gradient'])
    for values in raw['loss_component_observations']:
        need(values,'Missing actual criterion components')
        for value in values.values():tensor(value)
    levels=[0,2] if candidate else [0,1,2]
    for forward in (1,2):need([x['level'] for x in raw['ffn_calls'] if x['forward']==forward]==levels,'Remaining original FFN sequence differs')
    for record in raw['ffn_calls']:
        tensor(record['input']);tensor(record['output']);gradients(record,'native_input_gradients',True);gradients(record,'native_output_gradients',True)
    for record in raw['raw_bank_observations']:need(all(record[k] is True for k in ('unchanged_after_full_forward','ids_unchanged_after_full_forward','maps_unchanged_after_full_forward')),'Original bank/IDs/maps changed')
    for record in raw['csort_raw_input_observations']:need(record['original_raw_objects'] is True and record['original_childmap_object'] is True and record['original_calls']==1,'CSORT original source changed');tensor(record['output'])
    for record in raw['hcg_readbacks']:
        need(record['original_residual_levels']=={str(i):True for i in levels},'Original remaining skips changed');tensor(record['output']);gradients(record,'native_point_message_gradients',True)
        if candidate:need(record['BFC_middle_original_skip_and_exact_HCG_input'] is True,'Actual middle cf+delta/HCG path absent')
    for record in raw['inst_to_mask_path_observations']:
        need(record['single_native_inst_update_exact'] is True and record['new_extra_injection'] is False,'Original inst update changed')
        for key in ('native_post_cluster_inst_gradients','native_post_ILA_inst_gradients','native_final_mask_gradients'):gradients(record,key,True)
    for record in raw['BFC_butterfly_observations']:
        groups,sequence=expected_scalar_metadata(record)
        need(record['groups']==groups and record['actual_builder_calls']==len(record['batches'])==record['input']['shape'][0],'Actual geometry groups/builder count differs')
        need(len(sequence)==len(record['mix_calls']),'Actual consumed call count differs')
        for key,predicate in (('actual_n_ge3_supported_parent_groups',lambda g:g['n']>=3),('actual_nonpower2_supported_parent_groups',lambda g:g['nonpower_of_two']),('actual_multistage_supported_parent_groups',lambda g:g['multistage'])):need(record[key]==sum(predicate(g) for g in groups)>0,'Actual preregistered BFC core coverage missing')
        previous={}
        for index,(call,expected) in enumerate(zip(record['mix_calls'],sequence)):
            need(all(call[k]==v for k,v in expected.items()) and call['call_index']==index and call['forward']==record['forward'],'Actual pair/batch/order/round differs from independent scalar oracle')
            rows=len(call['left_ids']) if call['kind']=='round' else len(call['original_ids'])
            for key in ('input','linear_output','output'):tensor(call[key],False,[rows,512])
            for key in ('left_input','right_input','left_output','right_output'):tensor(call[key],False,[rows,256])
            need(call['actual_both_inputs_from_same_old_state'] is True and call['no_fake_padded_pair_participant'] is True and call['activation_original_calls']==1,'Native actual input/activation control absent')
            for key in ('native_input_gradients','native_linear_output_gradients','native_output_gradients'):gradients(call,key)
            need(call['native_output_half_gradients'],'Missing actual pair-half loss observations')
            for halves in call['native_output_half_gradients']:
                for side in ('left','right'):
                    tensor(halves[side],False,[rows,256]);half_zero_counts[side]+=int(halves[side]['abs_max']==0)
                half_zero_counts['events']+=1
            if call['batch'] in previous:need(call['old_state_sha256']==previous[call['batch']],'Observed actual old-state/writeback hash chain differs')
            previous[call['batch']]=call['writeback_reference_sha256']
            if call['kind']=='round':need(call['unpaired_carry_reference_exact'] is True,'Actual unpaired state carry failed')
            else:need(call['singleton_private_zero_right_input'] is True and call['right_input']['abs_max']==0,'Actual private singleton boundary failed')
        need(all(record[k] is True for k in ('original_ID_inverse_scatter_observed','returned_original_bank_shape','unsupported_and_batch_padding_update_zero','final_writeback_from_actual_outputs_reference_exact','actual_output_requires_grad')),'Actual original-ID/output control absent')
        gradients(record,'native_input_gradients',True);gradients(record,'native_output_gradients',True)
        need(record['self_exclusive_claim'] is False and record['offdiagonal_dependency_probe']=='NOT_IMPLEMENTED_NOT_MEASURED','Unimplemented/incorrect graph claim')
        topology_summary.append({key:record[key] for key in ('forward','actual_builder_calls','actual_n_ge3_supported_parent_groups','actual_nonpower2_supported_parent_groups','actual_multistage_supported_parent_groups','actual_round_mix_calls','actual_singleton_mix_calls','actual_supported_singleton_groups','actual_unsupported_internal_rows','actual_padding_rows')})
    native_summary[target]={'losses':raw['losses'],'optimizer_steps':raw['optimizer_steps'],'finite_parameter_gradient_counts':[s['gradient_tensor_count'] for s in raw['steps']],'parameter_inventory':{k:v for k,v in raw['dynamic_parameter_inventory'].items() if k!='state_dict_keys'},'observer_smoke_peak_allocated_bytes':raw['smoke_peak_allocated_bytes'],'observer_smoke_peak_reserved_bytes':raw['smoke_peak_reserved_bytes']}

s,c=raws['smoke_candidate'],raws['smoke_champion']
need(s['batches']==c['batches'] and s['initialization']==c['initialization'] and s['native_dataloader_config']==c['native_dataloader_config'] and s['data_source']==c['data_source'],'Actual native input/init/loader pair differs')
ci,bi=s['common_initialized_parameters'],c['common_initialized_parameters']
need(all(ci[k]==bi[k] for k in ('names','tensor_count','parameter_count','sha256','excluded_name_prefixes')),'Actual common named initialization differs')
need(ci['tensor_count']==len(ci['names'])==843 and ci['parameter_count']==156958522 and ci['sha256']=='04231c23641ec4d1fd7b9a31292b1b117ee84c5c22385379f641ddba2063b07a','Actual measured common inventory differs')
need(ci['excluded_name_prefixes']==['dec.cluster_att.cluster_ffn.1.','dec.cluster_att.middle_butterfly.'] and not any(n.startswith(tuple(ci['excluded_name_prefixes'])) for n in ci['names']) and any(n.startswith('dec.cluster_att.cluster_ffn_norm.1.') for n in ci['names']),'Common exclusion/middle-LN scope differs')

for target in ('champion','candidate'):
    raw=raws['resources_'+target];v=raw['measurements_ms'];ordered=sorted(v)
    need((raw['batch_size'],raw['lang_num_max'],raw['warmup'],raw['repeat'])==(1,1,20,100) and len(v)==100 and all(finite(x) and x>0 for x in v),'Original resource protocol/timing samples differ')
    need(raw['optimizer_steps']==raw['native_loss_forwards']==raw['native_criterion_backwards']==0 and raw['native_predict_calls']==121,'Resources ran training or wrong predict count')
    need(math.isclose(raw['median_ms'],statistics.median(v),rel_tol=1e-12,abs_tol=1e-12) and math.isclose(raw['p90_ms'],ordered[89]+.1*(ordered[90]-ordered[89]),rel_tol=1e-12,abs_tol=1e-12),'Actual timing statistics inconsistent')
    profile=raw['profile'];need(profile['profiler_file_sha256']==HANDLERS and profile['within10G'] is (profile['flops']<=1e10) and profile['flops_g']==profile['flops']/1e9,'Original handlers/FLOPs flag differs')
    need(math.isclose(sum(profile['by_operator'].values()),profile['flops'],rel_tol=1e-12) and all(type(n) is int and n>=0 for n in profile['unsupported_ops'].values()),'Actual operator/unsupported disclosure malformed')
    need(raw['parameter_flags_preserved'] is True and raw['source_body_executed_without_replacement'] is True and raw['validation_accuracy_evaluated_for_selection'] is False and raw['full_optimizer_training_peak'].startswith('UNKNOWN'),'Resource observer/accuracy/scope changed')
a,b=raws['resources_candidate'],raws['resources_champion']
need(all(a[k]==b[k] for k in ('input_sha256','scan_ids','ann_ids','initialization','data_source')) and a['profile']['fvcore_version']==b['profile']['fvcore_version'],'Actual resource input/init/profiler pair differs')
need(a['parameters']==s['dynamic_parameter_inventory']['actual_full_model_parameters'] and b['parameters']==c['dynamic_parameter_inventory']['actual_full_model_parameters'] and a['parameters']-b['parameters']==262656-525568,'Actual model inventory/replacement delta differs')
need(a['profile']['flops']<=1e10,'Candidate exceeds original counted10G budget')
memory_triggered=a['peak_allocated_bytes']>1.15*b['peak_allocated_bytes'] or s['smoke_peak_allocated_bytes']>1.15*c['smoke_peak_allocated_bytes']
need(not memory_triggered,'Existing memory retention condition requires a separate real retention decision')
delta=lambda x,y:100*(x/y-1)
resources={'candidate':{k:a[k] for k in ('parameters','median_ms','p90_ms','peak_allocated_bytes','peak_reserved_bytes')},'champion':{k:b[k] for k in ('parameters','median_ms','p90_ms','peak_allocated_bytes','peak_reserved_bytes')},'candidate_counted_flops':a['profile']['flops'],'champion_counted_flops':b['profile']['flops'],'delta_flops':a['profile']['flops']-b['profile']['flops'],'delta_parameters':a['parameters']-b['parameters'],'delta_median_percent':delta(a['median_ms'],b['median_ms']),'delta_P90_percent':delta(a['p90_ms'],b['p90_ms']),'delta_predict_allocated_percent':delta(a['peak_allocated_bytes'],b['peak_allocated_bytes']),'delta_predict_reserved_percent':delta(a['peak_reserved_bytes'],b['peak_reserved_bytes']),'delta_observer_smoke_allocated_percent':delta(s['smoke_peak_allocated_bytes'],c['smoke_peak_allocated_bytes']),'delta_observer_smoke_reserved_percent':delta(s['smoke_peak_reserved_bytes'],c['smoke_peak_reserved_bytes']),'existing15percent_memory_retention_condition_triggered':memory_triggered,'same_actual_resource_input_sha256':a['input_sha256'],'original_handlers':HANDLERS,'candidate_full_unsupported_ops':a['profile']['unsupported_ops'],'champion_full_unsupported_ops':b['profile']['unsupported_ops'],'candidate_by_operator':a['profile']['by_operator'],'champion_by_operator':b['profile']['by_operator']}

# Recheck actual remote saved objects, not only the derived history flags.
status=read(TICK/'bfc_status_after_four.json');history=read(TICK/'bfc_native_operation_history.json')
need(status['binding']==binding and status['binding_is_current'] is True and status['current_owner_token']==o['token'],'Saved actual status binding differs')
remote=status['remote'];need(remote['workers']==[] and not remote['compute_contexts'].strip() and remote['gpu_identity_matches'] is True and remote['read_only'] is True,'Actual selected stage/context is not empty')
need([v.strip() for v in remote['gpu_inventory'].strip().split(',')][:2]==['0',binding['gpu_uuid']],'Saved actual selected inventory differs')
run_items=[item for item in remote['requests'] if item['request']['operation']=='run'];need(len(run_items)==4,'Unexpected extra/missing run requests')
for mode,target in PAIRS:
    arm=mode+'_'+target;env=envelopes[arm];req=requests[arm]
    matches=[x for x in run_items if x['request']['request_id']==req['request_id']];need(len(matches)==1,'Status missing/ambiguous original request')
    recon=read(TICK/('reconcile_'+arm+'_console.json'));selected=[x for x in recon['requests'] if x['request']['request_id']==req['request_id']]
    need(len(selected)==len(recon['requests'])==1 and recon['workers']==[] and not recon['compute_contexts'].strip(),'Actual filtered original reconciliation differs or remains active')
    for item in (matches[0],selected[0]):
        need(item['request']==req and item['request_sha256']==linux_sha(req),'Remote/local original request full object/SHA differs')
        need(all(item[flag] is True for flag in ('identity_matches','started_identity_matches','started_command_matches','completed_identity_matches','completed_command_matches','completed_result_identity_matches','result_identity_matches')),'Remote identity/command/result observation failed')
        need(item['completed']==env and item['completed_sha256']==linux_sha(env) and item['result']==env['result'] and item['result_sha256']==linux_sha(env['result'])==env['result_sha256'],'Remote/local entire terminal/result objects or Linux SHA differ')
        need(item['started']['identity']==env['identity'] and item['started']['command']==env['command'] and item['started']['process_identity']==env['original_process_identity'] and item['original_pid_still_same'] is False,'Actual original start/proc/termination link differs')
    record=next(x for x in history['same_original_requests_reconciled_read_only'] if x['mode']==mode and x['target']==target)
    need(record['local_execution']==ref(EXECUTION/(arm+'_execution.json')) and record['actual_reconcile_evidence']==ref(TICK/('reconcile_'+arm+'_console.json')) and record['request_id']==req['request_id'] and record['remote_result_sha256']==env['result_sha256'],'Derived history immutable original refs differ')
need(history['workers_after']==history['selected_gpu_contexts_after']==[] and history['physical_gpu']==0 and history['code_commit']==COMMIT and history['status_evidence']==ref(TICK/'bfc_status_after_four.json') and (TICK/'bfc_status_after_four.json').read_bytes()==(TICK/'status_after_four_console.json').read_bytes(),'History/status bytecopy or selected identity differs')
local_path=TICK/'bfc_execution_review_prepare/actual_four_result_review.json';local=read(local_path)
need(sha(local_path)=='b8fa916c6c746e86d03fc3aa4fc3325382e11266c6662de85ece09a35934ae4b','Root actual checker report changed')
need(local['review_status']=='RAW_SEMANTICS_VALIDATED_NOT_ADMISSION' and local['candidate_id']==CID and local['code_commit']==COMMIT and local['goal_sha256']==GOAL and local['standard_PASS_receipt_queue_written'] is False and local['observations']['native_semantics_and_pairing_checked'] is True and local['observations']['resource_protocol_checked'] is True,'Root actual checker report identity/semantics boundary differs')
need(local['observations']['candidate_losses']==s['losses'] and local['observations']['native_optimizer_steps']==2 and local['observations']['paired_TRAIN_batches']==s['batches'] and local['observations']['existing_memory_condition_needs_separate_retention_decision']==memory_triggered,'Actual checker report facts differ from this independent recomputation')
cross=TICK/'bfc_actual_result_cross_review.json';need(sha(cross)=='419fd14b3043fe0b2f27918e598eb10a62877a586906380b02e01d05b8b10a8a' and read(cross)['material_concerns']==[],'External cross-review differs')
result={'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'FOUR_ACTUAL_BFC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED','candidate_id':CID,'experiment_id':'M213-BFC','code_commit':COMMIT,'goal_sha256':GOAL,'material_concerns':[],'raw_results':raw_refs,'anchors':{'local_review':ref(local_path),'execution_binding':ref(EXECUTION/'execution_binding.json'),'native_manifest':ref(EXECUTION/'native_manifest.json'),'execution_lease':ref(EXECUTION/'execution_lease.json'),'actual_operation_history':ref(TICK/'bfc_native_operation_history.json'),'actual_status':ref(TICK/'bfc_status_after_four.json'),'external_cross_review':ref(cross),'review_script':ref(Path(__file__))},'actual_data_assertions':count,'native_checks_passed':True,'resource_checks_passed':True,'native_review':native_summary,'actual_geometry_scalar_oracle':{'method':'Independent block lower/upper-half matching from actual JSON geometry, never importing or executing production/model source','native_bank_instances':sum(x['actual_builder_calls'] for x in topology_summary),'original_unique_TRAIN_scenes':sorted({scene for batch in s['batches'] for scene in batch['scan_ids']}),'per_forward':topology_summary,'old_state_writeback_hash_chain_checked':True,'individual_half_gradient_observations':half_zero_counts,'individual_call_or_half_zero_is_legal':True},'pairing_review':{'actual_two_batches':s['batches'],'common_named_initialized_parameters':{k:ci[k] for k in ('tensor_count','parameter_count','sha256','excluded_name_prefixes')},'common_names_exactly_equal':True,'original_fine_coarse_initial_hashes_equal':all(s['native_tracked_initial_hash'][key]==c['native_tracked_initial_hash'][key] for key in ('ffn_0','ffn_2')),'full_buffers_RNG_common_state':'NOT_RECORDED_NOT_CLAIMED','first_cross_target_raw_digest_equal':{key:s['raw_bank_observations'][0][key]==c['raw_bank_observations'][0][key] for key in ('raw_sha256','id_sha256','map_sha256')},'cross_target_intermediate_digest_is_not_a_new_exact_equality_gate':True},'resources_review':resources,'identity_chain':{'runtime_checkout_commit_from_original_binding':binding['runtime_code_commit'],'staged_candidate_source_commit':COMMIT,'original_owner':o,'physical_gpu':0,'gpu_uuid':binding['gpu_uuid'],'remote_complete_request_result_objects_and_Linux_serialization_checked':True,'all_four_original_workers_no_longer_same_process_from_saved_reconcile':True,'saved_selected_contexts_empty':True,'early_process_observations':early_identity},'reviewer_authorship_disclosure':'This reviewer agent previously authored the frozen BFC diagnostic observer and draft checker. This audit recomputes actual JSON/geometry/resource/identity facts without executing that checker or production source, and is independent of root execution/report generation; it is not a second experiment or a claim of author-blind review. A separate MDC cross-review is externally anchored.','limitations':['Actual technical original TRAIN2 success is not trained model accuracy gain or whole-mechanism novelty. Only two original TRAIN batches/four scene IDs were used; bank-instance counts are not independent scenes/experiments.','Original source-value equality and real tensor paths are the frozen native hook observations/assertions, not a new Tensor/model replay by this reviewer. No source/Git/SSH/GPU/Torch or native compute was performed here.','Actual singleton/unsupported internal/padding counts are0 in both candidate forwards: those optional native boundaries remain NOT_EXERCISED. Symbolic tests/source cover separate scope.','Offdiagonal dependency/identity-Q/mean/conservation controls are not implemented by BFC and are not new admission gates. No self-exclusive or conservation claim.','Unsupported operators are fully retained; counted FLOPs omit some CPU/Python/index/GELU work. Candidate measured P90 is slower. No new latency gate or universal latency gain is claimed.','Smoke memory contains observer snapshots/topology overhead and is not pure TRAIN memory. The existing15% allocated-memory condition did not trigger; pure TRAIN and unmeasured no-cluster baseline remain UNKNOWN.','Saved actual selectedGPU0 emptiness is a timestamped result, not a future resource lease or guarantee. Empty early argv observations are not independently verified signal identities.','This report does not create standard summaries, decision, receipt, queue, source promotion or formal training; root must separately validate current source/constraints/owner/budget/admission.'],'scientific_admission_created':False,'standard_PASS_receipt_queue_written':False,'efficacy':'UNKNOWN'}
out=TICK/'bfc_native_resource_independent_review.json'
with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
print(json.dumps({'path':str(out),'sha256':sha(out),'status':result['status'],'checks':count,'material_concerns':[],'anchors_local_review':result['anchors']['local_review'],'resources':{k:resources[k] for k in ('candidate_counted_flops','champion_counted_flops','delta_median_percent','delta_P90_percent','delta_predict_allocated_percent','delta_observer_smoke_allocated_percent','existing15percent_memory_retention_condition_triggered')}}))
