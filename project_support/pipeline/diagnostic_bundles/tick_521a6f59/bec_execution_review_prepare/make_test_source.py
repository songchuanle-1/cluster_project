"""Local authoring utility; emits only software fixtures, never actual results."""
from pathlib import Path

here=Path(__file__).resolve().parent
old=here.parents[3]/'pipeline/diagnostic_bundles/tick_f86d1cfa/cts_execution_review_prepare/test_checker.py'
s=old.read_text(encoding='utf8')
s=s.replace('tick_6bdbcf77/cts_operational_prepare','tick_521a6f59/bec_operational_prepare').replace('cts_schema_reviewer','bec_schema_reviewer').replace('review_cts.py','review_bec.py').replace('_cts','_bec').replace('/cts_','/bec_')
s=s.replace('build,describe,preflight=r.topology_functions()', '''# Extract only original pure-stdlib metadata functions, never import native modules.
tree=ast.parse((FROZEN/'candidate_model/bipartite_edges.py').read_text(encoding='utf8'))
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_bipartite_plan')
env={};exec(compile(ast.Module(body=[node],type_ignores=[]),'<production-pure-plan>','exec'),env)
build=env['build_bipartite_plan']
worker=ast.parse((FROZEN/'worker.py').read_text(encoding='utf8'))
nodes=[n for n in worker.body if isinstance(n,ast.FunctionDef) and n.name in ('bec_membership_observation','bec_core_preflight')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<original-pure-support>','exec'),env)
preflight=env['bec_core_preflight']''')
a=s.index('def fixture_record(');b=s.index('BLOCKS=',a)
s=s[:a]+'''def fixture_record(forward=1,optional=True,empty=False):
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

''' +s[b:]
s=s.replace("BLOCKS=['own_input','positive_input','negative_input']", "BLOCKS=[n+'_'+o+'_'+f for n in ('up_fine','up_middle') for o in ('retained','upward') for f in ('child','parent')]+[n+'_'+f for n in ('down_middle','down_fine') for f in ('retained','context')]")
s=s.replace("tracked=('ffn_0','ffn_2','triadic_mix')", "tracked=('ffn_2','up_fine','up_middle','down_middle','down_fine')")
s=s.replace('synthetic_three_aggregate_input_block_gradient_and_slice_update_schema_accepted','synthetic_twelve_aggregate_block_gradient_and_actual_slice_update_schema_accepted').replace("pop('negative_input')","pop(BLOCKS[-1])").replace('missing_negative_aggregate_block','missing_twelfth_aggregate_block')
s=s.replace("levels=[0,2] if candidate else [0,1,2];tracked=['ffn_'+str(i) for i in levels]+(['triadic_mix'] if candidate else [])", "levels=[2] if candidate else [0,1,2];tracked=['ffn_'+str(i) for i in levels]+(['up_fine','up_middle','down_middle','down_fine'] if candidate else [])")
s=s.replace("'CTS_middle_original_skip_and_exact_HCG_input':True", "'BEC_original_three_skip_HCG_inputs':[True]*3,'BEC_helper_coarse_object_exact':True")
s=s.replace("'original_residual_levels':{str(i):True for i in levels}", "'original_residual_levels':{} if candidate else {str(i):True for i in levels}")
s=s.replace("{'0':525568,'1':0 if candidate else 525568,'2':525568}","{'0':0 if candidate else 525568,'1':0 if candidate else 525568,'2':525568}")
s=s.replace('196864 if candidate else 0','787968 if candidate else 0').replace("'geometry_registered_buffer_names'","'new_registered_buffer_names'").replace('157155386','157220922')
s=s.replace('CTS_triadic_observations','BEC_edge_observations')
s=s.replace("['dec.cluster_att.cluster_ffn_norm.1.weight','SYNTHETIC_COMMON']","['dec.cluster_att.cluster_ffn_norm.'+str(i)+'.weight' for i in range(3)]+['dec.cluster_att.cluster_ffn.2.weight']").replace("'tensor_count':2,'parameter_count':2","'tensor_count':4,'parameter_count':4")
s=s.replace("['dec.cluster_att.cluster_ffn.1.','dec.cluster_att.middle_triad.']","['dec.cluster_att.cluster_ffn.0.','dec.cluster_att.cluster_ffn.1.','dec.cluster_att.bipartite_edges.']")
s=s.replace("preflight([(b['parent_ids'],[n>0 for n in b['real_point_counts']]) for b in v['batches']])","v['native_coverage_preflight']")
s=s.replace("update(CTS_middle_original_skip_and_exact_HCG_input=False)","update(BEC_original_three_skip_HCG_inputs=[True,False,True])")
s=s.replace("['own_input'].update(abs_max=0.)","[BLOCKS[0]].update(abs_max=0.)").replace("update(negative_input='a'*64)","update({BLOCKS[-1]:'a'*64})")
s=s.replace("'INCONCLUSIVE_ORIGINAL_BATCH_LACKS_CORE_TRIADIC_PATH'","'INCONCLUSIVE_ORIGINAL_BATCH_LACKS_BEC_CORE_EDGES'")
s=s.replace('r.configure_current_anchors(PROJECT)', '''# No live release/current candidate anchor is fabricated. In-memory directory-shell
# fixtures explicitly bypass only external-anchor configuration; production CLI
# below exercises the real configuration and must refuse missing actual anchors.
contract=r.read(HERE/'external_packet_contract.json')
r.FROZEN=Path(contract['native_preparation']['path']).parent.as_posix();r.PREP_SHA=contract['native_preparation']['sha256']
r.TEMPLATE_SHA=contract['manifest_template_sha256'];r.RELEASE=contract['static_release']['path'];r.RELEASE_SHA=contract['static_release']['sha256']''')
s=s.replace("return copy.deepcopy(objects[p.name]) if p.parent==virtual else read_original(path)","return copy.deepcopy(objects[p.name]) if p.parent==virtual else read_original(FROZEN.parent/'release_template.json' if p==PROJECT/r.RELEASE else path)")
s=s.replace("return hashlib.sha256(wire(objects[p.name])).hexdigest() if p.parent==virtual else digest_original(path)","return hashlib.sha256(wire(objects[p.name])).hexdigest() if p.parent==virtual else digest_original(FROZEN.parent/'release_template.json' if p==PROJECT/r.RELEASE else path)")
s=s.replace("'wrong_physical_UUID':", "'foreign_original_thread':lambda x:x['execution_binding.json']['owner'].update(thread_id='foreign-root'),\n    'wrong_physical_UUID':")
s=s.replace("old=PROJECT/'pipeline/diagnostic_bundles/tick_336ca5d7/bfc_execution_review_prepare/review_bfc.py'", "old=PROJECT/'pipeline/diagnostic_bundles/tick_f86d1cfa/cts_execution_review_prepare/review_cts.py'")
s=s.replace("assert 'nonpower' not in source.read_text(encoding='utf-8') and 'left_output_from_left_input' not in source.read_text(encoding='utf-8') and 'native_output_half_gradients' not in source.read_text(encoding='utf-8')", "assert all(k not in source.read_text(encoding='utf8') for k in ('actual_three_distinct_real_input_rows','actual_multiround_supported_parent_groups','native_output_half_gradients','left_output_from_left_input'))")
s=s.replace('no_inherited_BFC_nonpower_halves_fourquadrant_gate','no_inherited_CTS_three_sources_rounds_or_BFC_halves_quadrants_gate')
(here/'test_checker.py').write_text(s,encoding='utf8')
