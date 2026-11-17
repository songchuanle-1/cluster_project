"""Author-local source port; no model import, transport or scientific outputs."""
from pathlib import Path
import ast

HERE=Path(__file__).resolve().parent
ORIGIN=HERE.parents[1]/'manual_gpu1_20261025/bcr_execution_review_prepare'
old=(ORIGIN/'review_bcr_v2.py').read_text(encoding='utf-8')
old=old.replace('BCR','BFC').replace('bcr','bfc').replace('M212','M213').replace('11a811618179ab1ddc0cee299194667413b7fdb9','48fc302c3c02ffef0b241be3593c386b6b65a72e').replace('hierarchy-parent-bidirectional-complement-recurrence','hierarchy-parent-butterfly-token-composition')


def substitute(name,text):
    global old
    tree=ast.parse(old);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=old.splitlines(keepends=True);old=''.join(lines[:node.lineno-1])+text.strip()+'\n'+''.join(lines[node.end_lineno:])


substitute('topology_functions', '''
def topology_functions():
    """Execute only externally hash-verified pure stdlib production/observer functions."""
    directory=Path('D:/project/cluster_project')/FROZEN
    environment={'math':math}
    for filename,name in [('candidate_model/middle_butterfly.py','build_butterfly_plan'),('worker.py','butterfly_plan_observation')]:
        tree=ast.parse((directory/filename).read_text(encoding='utf-8'))
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        exec(compile(ast.Module(body=[function],type_ignores=[]),str(directory/filename),'exec'),environment)
    return environment['build_butterfly_plan'],environment['butterfly_plan_observation']
''')
substitute('required_prior_state', '''
def actual_coverage(record,groups):
    for field,predicate in (
        ('actual_n_ge3_supported_parent_groups',lambda g:g['n']>=3),
        ('actual_nonpower2_supported_parent_groups',lambda g:g['nonpower_of_two']),
        ('actual_multistage_supported_parent_groups',lambda g:g['multistage'])):
        count=sum(predicate(g) for g in groups)
        need(record[field]==count and count>0,'INCONCLUSIVE: original fixed TRAIN batch lacks actual n3/nonpower2/multistage coverage; no replacement sample')
''')
substitute('complement_record', '''
def butterfly_record(record):
    tensor(record['input']);tensor(record['output'])
    need(record['input']['shape']==record['output']['shape'],'Butterfly output escaped original middle bank')
    need(record['input']['shape'][-1]==256,'Original middle width changed')
    need(record['original_middle_norm_calls']==record['original_butterfly_forward_calls']==1,'Original middle norm/operator call count changed')
    for key in ('returned_original_bank_shape','original_ID_inverse_scatter_observed','unsupported_and_batch_padding_update_zero','final_writeback_from_actual_outputs_reference_exact','actual_output_requires_grad'):
        need(record[key] is True,'Original middle support/scatter/autograd control missing: '+key)
    need(record['self_exclusive_claim'] is False,'BFC includes own state; self-exclusive claim is invalid')
    gradients(record,'native_input_gradients',True);gradients(record,'native_output_gradients',True)
    build,describe=topology_functions();groups=[];sequence=[]
    for batch in record['batches']:
        counts=batch['real_point_counts'];k=batch['middle_prefix'];width=batch['padded_width']
        need(type(k) is int and type(width) is int and len(counts)==k<=width and all(type(n) is int and n>=0 for n in counts),'Malformed real support/prefix')
        need(batch['true_supported_original_ids']==[i for i,n in enumerate(counts) if n>0] and batch['unsupported_internal_ids']==[i for i,n in enumerate(counts) if n==0] and batch['batch_padding_rows']==width-k,'Actual point support/padding differs')
        need(batch['support_formula']=='bincount(ids1[ids0],minlength=ids2.numel())>0','True support source changed')
        # The helper cap is the frozen configured64, not the batch padding width.
        plan=build(batch['centers'],batch['parent_ids'],[n>0 for n in counts],64);g,seq=describe(plan)
        for x in g:x['batch']=batch['batch']
        for x in seq:x['batch']=batch['batch']
        groups.extend(g);sequence.extend(seq)
    groups=json.loads(json.dumps(groups));sequence=json.loads(json.dumps(sequence))
    need(record['groups']==groups and record['actual_builder_calls']==len(record['batches'])==record['input']['shape'][0],'Actual production plan/group/builder mismatch')
    actual_coverage(record,groups)
    calls=record['mix_calls'];need(len(calls)==len(sequence),'Actual shared pair/singleton call count differs')
    for index,(call,expected) in enumerate(zip(calls,sequence)):
        need(all(call[k]==v for k,v in expected.items()) and call['call_index']==index and call['forward']==record['forward'],'Actual original-ID pair/stage/call order differs')
        need(call['actual_both_inputs_from_same_old_state'] is True and call['no_fake_padded_pair_participant'] is True and call['activation_original_calls']==1,'Actual old-stage input or original activation control missing')
        for key in ('input','linear_output','output','left_input','right_input','left_output','right_output'):tensor(call[key])
        for key in ('native_input_gradients','native_linear_output_gradients','native_output_gradients'):gradients(call,key)
        rows=len(expected['left_ids']) if call['kind']=='round' else len(expected['original_ids'])
        need(call['input']['shape']==call['linear_output']['shape']==call['output']['shape']==[rows,512],'Original batched 2C pair map dimensions changed')
        need(all(call[k]['shape']==[rows,256] for k in ('left_input','right_input','left_output','right_output')),'Original pair half dimensions changed')
        for key in ('input_sha256','linear_output_sha256','output_sha256','old_state_sha256','writeback_reference_sha256'):need(hash_string(call[key]),'Actual pair fingerprint absent: '+key)
        halves=call['native_output_half_gradients'];need(isinstance(halves,list) and halves,'Actual pair output-half loss observations missing')
        for pair in halves:
            # Each individual call/row/half may be zero. Four aggregate W blocks are separate gates.
            tensor(pair['left']);tensor(pair['right'])
            need(pair['left']['shape']==pair['right']['shape']==[rows,256],'Half-gradient shape differs')
        if call['kind']=='round':need(call['unpaired_carry_reference_exact'] is True,'Unpaired actual old state was not retained')
        else:need(call['singleton_private_zero_right_input'] is True and call['right_input']['abs_max']==0,'Singleton private zero boundary differs')
    need(record['actual_round_mix_calls']==sum(c['kind']=='round' for c in calls) and record['actual_singleton_mix_calls']==sum(c['kind']=='singleton' for c in calls),'Actual batched round/singleton counts differ')
    need(record['actual_supported_singleton_groups']==sum(g['n']==1 for g in groups) and record['actual_unsupported_internal_rows']==sum(len(b['unsupported_internal_ids']) for b in record['batches']) and record['actual_padding_rows']==sum(b['batch_padding_rows'] for b in record['batches']),'Actual singleton/unsupported/padding coverage differs')
    need(record['offdiagonal_dependency_probe']=='NOT_IMPLEMENTED_NOT_MEASURED','Unimplemented probe overclaimed')
''')
substitute('required_weight_blocks', '''
def required_weight_blocks(raw,candidate):
    expected_blocks={'left_output_from_left_input','left_output_from_right_input','right_output_from_left_input','right_output_from_right_input'}
    for step in raw['steps']:
        need(set(step['native_parameter_block_gradients'])==(expected_blocks if candidate else set()),'Missing actual four W quadrant gradients')
        for name,value in step['native_parameter_block_gradients'].items():
            tensor(value,True);need(value['shape']==[256,256],'Required actual W quadrant dimensions changed')
            before=step['parameter_block_before_step_hash'][name];after=step['parameter_block_after_step_hash'][name]
            need(hash_string(before) and hash_string(after) and before!=after,'Actual W quadrant update absent; weight decay alone is insufficient')
''')
# Keep the original native TRAIN/backward/optimizer path validator; change only new-map schema.
old=old.replace("('ffn_0','ffn_2','complement_scan','complement_readout')", "('ffn_0','ffn_2','butterfly_mix')")
old=old.replace("BFC_middle_original_skip_and_exact_HCG_input", "BFC_middle_original_skip_and_exact_HCG_input")
old=old.replace("(328192 if candidate else 0)","(262656 if candidate else 0)")
old=old.replace("complements=raw['BFC_complement_observations'];need(len(complements)==(2 if candidate else 0),'Unexpected actual BFC branch count')\n    for record in complements:complement_record(record)","butterflies=raw['BFC_butterfly_observations'];need(len(butterflies)==(2 if candidate else 0),'Unexpected actual BFC branch count')\n    for record in butterflies:butterfly_record(record)")
old=old.replace("'dec.cluster_att.middle_complement.'", "'dec.cluster_att.middle_butterfly.'")
old=old.replace("need(manifest['native_port_scope']['selected_physical_gpu']==1 and manifest['native_port_scope']['selected_gpu_uuid']=='GPU-7f82edb9-f620-8045-caea-a75232265cd1' and manifest['native_port_scope']['logical_cuda_device']==0,'GPU1 native port identity mismatch')", "need(type(manifest['physical_gpu']) is int and manifest['physical_gpu'] in UUIDS and manifest['gpu_uuid']==UUIDS[manifest['physical_gpu']],'Selected authorized physical GPU/UUID mismatch')")
old=old.replace("==328192-525568", "==262656-525568")
old=old.replace("records=s['BFC_complement_observations']", "records=s['BFC_butterfly_observations']")
start=old.index("      'actual_depth_ge2_scan_call_counts':")
end=old.index("      'actual_unsupported_internal_rows':",start)
old=old[:start]+"      'actual_nonpower2_supported_parent_group_counts':[v['actual_nonpower2_supported_parent_groups'] for v in records],\n      'actual_multistage_supported_parent_group_counts':[v['actual_multistage_supported_parent_groups'] for v in records],\n      'actual_map_call_counts':[{k:sum(c['kind']==k for c in v['mix_calls']) for k in ('round','singleton')} for v in records],\n      'actual_required_weight_blocks':['left_output_from_left_input','left_output_from_right_input','right_output_from_left_input','right_output_from_right_input'],\n"+old[end:]
old=old.replace("v['actual_singleton_supported_parent_groups']", "v['actual_supported_singleton_groups']")
# Generalize exact physical binding; never auto-switch or infer current idleness.
old=old.replace("manifest['physical_gpu'] == 1", "manifest['physical_gpu'] == binding['physical_gpu'] and type(binding['physical_gpu']) is int and binding['physical_gpu'] in UUIDS")
old=old.replace("binding['stage'] == '/data/songcl/Project/Cluster_project/pipeline/bfc_gpu1_' + binding['owner']['token'][:8] and\n         binding['gpu_uuid'] == 'GPU-7f82edb9-f620-8045-caea-a75232265cd1'", "binding['stage'] == '/data/songcl/Project/Cluster_project/pipeline/bfc_' + binding['owner']['token'][:8] + '_gpu' + str(binding['physical_gpu']) and\n         binding['gpu_uuid'] == UUIDS[binding['physical_gpu']]")
old=old.replace('physical_gpu=1, gpu_uuid=',"physical_gpu=binding['physical_gpu'], gpu_uuid=")
old=old.replace("'physical_gpu': 1, 'gpu_uuid':", "'physical_gpu': binding['physical_gpu'], 'gpu_uuid':")
old=old.replace("'Actual promoted GPU1 native package required'", "'Actual separately promoted and externally anchored native package required'")
old=old.replace("'Actual promoted GPU1 native package required'", "'Actual promoted selected-GPU native package required'")
old=old.replace("'Stage/token/authorized physicalGPU1 binding mismatch'", "'Stage/token/selected physical GPU binding mismatch'")
old=old.replace('Original BFC external candidate identity changed','Current BFC external candidate identity changed')
old=old.replace('BFC exclusive scan/readout/native checks are specific to actual unchanged worker a3b1 observations.', 'BFC actual pair-stage/mix/GELU/scatter/quadrant checks follow unchanged worker883925 observations. No actual results exist at preparation.')
old=old.replace('stage hash-bound11a','stage hash-bound48fc').replace('staged hash-bound11a','staged hash-bound48fc').replace('M213-BFC/config/11a/goal','M213-BFC/config/48fc/goal')
old=old.replace("FROZEN=PREP_SHA=TEMPLATE_SHA=RELEASE=RELEASE_SHA=None", "FROZEN=PREP_SHA=TEMPLATE_SHA=RELEASE=RELEASE_SHA=None\nUUIDS={0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',1:'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}")
old=old.replace("need(prep['code_commit']==COMMIT and prep['source_commit']==COMMIT and prep['draft_execution_disabled'] is False,'Actual promoted GPU1 native package required')", "need(prep['code_commit']==COMMIT and prep['source_commit']==COMMIT and prep['draft_execution_disabled'] is False,'Actual promoted selected-GPU native package required')")
old=old.replace("'actual_supported_singleton_groups':[v['actual_singleton_supported_parent_groups']", "'actual_supported_singleton_groups':[v['actual_supported_singleton_groups']")
# Never substitute absent results with defaults or preparation flags.
with (HERE/'review_bfc.py').open('x',encoding='utf-8',newline='\n') as stream:stream.write(old)
ast.parse(old)
print('Local BFC reviewer draft source written; no actual results or standard artifacts processed')
