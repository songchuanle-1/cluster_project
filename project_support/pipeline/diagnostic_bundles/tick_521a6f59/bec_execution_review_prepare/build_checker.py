"""Local BEC checker port; never invokes native code or transport."""
from pathlib import Path
import ast
import hashlib

HERE=Path(__file__).resolve().parent
REFERENCE=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_f86d1cfa/cts_execution_review_prepare/review_cts.py')
assert hashlib.sha256(REFERENCE.read_bytes()).hexdigest()=='101d66e4dd2a81753ba240122cce8100987c5057c3b18f322fdb03c25f559b28'
text=REFERENCE.read_text(encoding='utf-8')
for a,b in [('hierarchy-parent-cyclic-triadic-state-composition','hierarchy-cross-level-bipartite-edge-composition'),('M214-CTS','M215-BEC'),
 ('CTS_triadic_observations','BEC_edge_observations'),('triadic_record','bec_record'),('middle_triad','bipartite_edges'),
 ('CTS','BEC'),('_cts','_bec'),('/cts_','/bec_'),
 ('4e80006047d5cb3dcdfb9c1102e02c33f354a07d','9b6782f44ca7f2c8ac35baea01dfd070314b5701'),
 ('bfab01a31a0fc7a0d679156d5e0e6fcfa987e56e5f3bb1bdf6bded9e2208f76e','2d0606030583fd29719a39a114e11c1c31f44b63ca0fa2cff849baf40e7ca14d'),
 ('ff7fb7a65999369f277744828598822883a222a10ce1ef02732aafeb561fb2cf','322c8ce812ffccda6cfa3d6d2d6e1dd8f73859ab5d3a9835d0c1110328c3e3ff'),
 ('03329ec50fba63d67330342052ec34262f772aee6cc16d3d8d2978d58628c27c','7e5d0f5b109e85d0d2f0bb7f2f806dd9db73fb7885add5abc372ce244ee753e3'),
 ("ORIGIN='pipeline/diagnostic_bundles/tick_4694ba96/bec_native_prepare'","ORIGIN='pipeline/diagnostic_bundles/tick_f86d1cfa/bec_native_prepare'")]:text=text.replace(a,b)
text=text.replace('BEC old-state own/positive/negative mix/GELU/scatter/three-column checks follow unchanged worker03329 observations. Actual results are absent at preparation.',
 'BEC actual up split/private mean/coarse-once/down/HCG and twelve aggregate blocks follow unchanged worker7e5 observations. No actual results exist at preparation.')
text=text.replace("YAML_SHA='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'", "YAML_SHA='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'\nCONTRACT_SHA=None")


def replace(name,value):
 global text
 node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
 lines=text.splitlines(keepends=True);text=''.join(lines[:node.lineno-1])+value.rstrip()+'\n'+''.join(lines[node.end_lineno:])


replace('configure_current_anchors', '''def configure_current_anchors(project):
    global FROZEN,PREP_SHA,TEMPLATE_SHA,RELEASE,RELEASE_SHA
    project=Path(project).resolve()
    need(hash_string(CONTRACT_SHA),'Real frozen external packet contract is unbound; no placeholder/None authorization')
    contract_path=Path(__file__).resolve().with_name('external_packet_contract.json')
    need(digest(contract_path)==CONTRACT_SHA,'Exact BEC external contract changed');contract=read(contract_path)
    c=next(x for x in read(project/'pipeline/research_work.json')['candidates'] if x['id']==CID)
    need(c['code_commit']==COMMIT and c['goal_sha256']==GOAL,'Current BEC candidate identity changed')
    native=c['worker_preparation']['preparation'];outer=c['execution_adapter']['preparation'];release=c['execution_adapter']['release']
    for item,key in [(native,'native_preparation'),(outer,'operational_preparation'),(release,'static_release')]:
        need(item==contract[key],'Current BEC packet is not the exact independently reviewable frozen version')
        path=(project/item['path']).resolve();need(path.is_relative_to(project) and digest(path)==item['sha256'],'External BEC package anchor mismatch')
    FROZEN=Path(native['path']).parent.as_posix();PREP_SHA=native['sha256'];RELEASE=release['path'];RELEASE_SHA=release['sha256']
    prep=read(project/native['path']);TEMPLATE_SHA=prep['prepared_file_hashes']['manifest_template.json']
    need(TEMPLATE_SHA==contract['manifest_template_sha256'],'BEC template differs from frozen contract')
    need(prep['code_commit']==prep['source_commit']==COMMIT and prep['source_parent_commit']==prep['runtime_expected_commit']==RUNTIME_EXPECTED and prep['draft_execution_disabled'] is False,'Actual source9b67/parent48fc operational copy required')
    need(digest(project/ORIGIN/'preparation.json')==ORIGIN_PREP_SHA and digest(project/FROZEN/'worker.py')==WORKER_SHA,'Original disabled322c or exact7e5 observer changed')
    need(digest(project/FROZEN/'native_runtime.py')==contract['runtime_sha256'],'Exact reviewed BEC runtime changed')
    proof=read(project/FROZEN/'source_version_binding.json')
    need(proof['code_commit']==COMMIT and proof['parent_commit']==proof['runtime_expected_commit']==RUNTIME_EXPECTED and proof['original_source_preparation_sha256']==SOURCE_PREP_SHA and len(proof['source_files'])==9,'Actual BEC9b67/48fc source binding differs')
    for item,key in [(proof['isolated_source_version'],'source_version'),(proof['isolated_source_version_independent_review'],'source_version_independent_review')]:
        path=(project/item['path']).resolve();need(item==contract[key] and path.is_relative_to(project) and digest(path)==item['sha256'],'Actual BEC source version proof changed')
    package=read(project/outer['path']);need(package['candidate_id']==CID and package['code_commit']==COMMIT,'Outer BEC identity differs')
    for name,h in package['prepared_file_hashes'].items():
        path=(project/Path(outer['path']).parent/name).resolve();need(path.is_relative_to((project/Path(outer['path']).parent).resolve()) and digest(path)==h,'Externally anchored BEC package changed: '+name)
    grant=project/'pipeline/authorizations/server4_gpu1_20261025.json';need(digest(grant)=='90f8820a60ef4d4e277904815b025658f7b8b457b0711a4d0ef5f7395fdd23f8','Explicit resource grant changed')
    return [dict(native),dict(outer),dict(release),{'path':grant.relative_to(project).as_posix(),'sha256':digest(grant)},{'path':ORIGIN+'/preparation.json','sha256':ORIGIN_PREP_SHA}]
''')
replace('topology_functions', '''def plan_metadata(plan):
    """Validate recorded active original-ID metadata without inventing missing point lists.

    No feature mean/GELU/Linear/FFN is recomputed. Original full point membership
    arrays are not separately persisted; frozen7e5 validates their actual objects.
    """
    need(isinstance(plan,dict),'Missing actual BEC production plan')
    widths=plan['widths'];prefix=plan['prefixes']
    need(len(widths)==len(prefix)==3 and all(type(x) is int and x>=0 for x in widths+prefix) and all(k<=w for k,w in zip(prefix,widths)),'Malformed original bank widths/prefixes')
    ids=[plan[k] for k in ('fine_ids','middle_ids','coarse_ids')]
    for values,k in zip(ids,prefix):need(isinstance(values,list) and values==sorted(set(values)) and all(type(i) is int and 0<=i<k for i in values),'Invalid true-supported original IDs')
    fine,middle,coarse=ids;fe=plan['fine_edges'];me=plan['middle_edges']
    need(len(plan['fine_parent_ids'])==len(fine) and len(plan['middle_parent_ids'])==len(middle),'BEC parent-source list length differs')
    need(fe==[[i,p] for i,p in zip(fine,plan['fine_parent_ids'])] and len(fe)==len(fine),'Fine edge/source ID order differs')
    need(me==[[i,p] for i,p in zip(middle,plan['middle_parent_ids'])] and len(me)==len(middle),'Middle edge/source ID order differs')
    need(all(type(p) is int and 0<=p<prefix[1] for _,p in fe) and sorted({p for _,p in fe})==middle,'Fine parent support differs')
    need(all(type(p) is int and 0<=p<prefix[2] for _,p in me) and sorted({p for _,p in me})==coarse,'Middle parent support differs')
    fg=[[p,[i for i,(_,parent) in enumerate(fe) if parent==p]] for p in middle]
    mg=[[p,[i for i,(_,parent) in enumerate(me) if parent==p]] for p in coarse]
    need(plan['fine_mean_groups']==fg and plan['middle_mean_groups']==mg,'Private means are not equal one-row-per-supported-child groups')
    fd={str(p):len(rows) for p,rows in fg};md={str(p):len(rows) for p,rows in mg}
    return {'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'fine_edges':len(fe),'middle_edges':len(me),
        'fine_parent_supported_child_degrees':fd,'middle_parent_supported_child_degrees':md,
        'singleton_fine_parent_groups':sum(x==1 for x in fd.values()),'singleton_middle_parent_groups':sum(x==1 for x in md.values()),
        'degree_ge2_fine_parent_groups':sum(x>=2 for x in fd.values()),'degree_ge2_middle_parent_groups':sum(x>=2 for x in md.values())}
''')
replace('actual_coverage','')
replace('bec_record', '''def bec_record(record):
    need(isinstance(record,dict) and isinstance(record['batches'],list),'Missing actual BEC branch record')
    support=[];up=[];down=[];means=[];by_batch={};widths=None
    for batch in record['batches']:
        b=batch['batch'];need(type(b) is int and b==len(by_batch),'BEC batch order differs')
        plan=batch['original_plan'];meta=plan_metadata(plan);support.append(meta);by_batch[b]=plan
        if widths is None:widths=plan['widths']
        need(plan['widths']==widths and batch['true_support']==meta,'Actual true support/source metadata differs')
        need([batch['fine_prefix'],batch['middle_prefix'],batch['coarse_prefix']]==plan['prefixes'],'Original BEC prefix differs')
        for level,key in enumerate(('unsupported_internal_fine_ids','unsupported_internal_middle_ids','unsupported_internal_coarse_ids')):
            need(batch[key]==sorted(set(range(plan['prefixes'][level]))-set(plan[('fine_ids','middle_ids','coarse_ids')[level]])),'Unsupported BEC IDs differ')
        need(batch['padding_rows']==[w-k for w,k in zip(widths,plan['prefixes'])],'BEC batch padding differs')
        if meta['fine_edges']:up.append((b,'up_fine',meta['fine_edges']));down.append((b,'down_fine',meta['fine_edges']))
        if meta['middle_edges']:up.append((b,'up_middle',meta['middle_edges']));down.insert(len(down)-int(bool(meta['fine_edges'])),(b,'down_middle',meta['middle_edges']))
        means.extend([(b,0,meta['fine_edges'],plan['fine_mean_groups'],widths[1]),(b,1,meta['middle_edges'],plan['middle_mean_groups'],widths[2])])
    expected_pre={'batches':support,'fine_edges':sum(x['fine_edges'] for x in support),'middle_edges':sum(x['middle_edges'] for x in support),
        'core_path_possible':any(x['fine_edges']>0 and x['middle_edges']>0 for x in support),
        'degree_boundary_scope':'Record only; absent degree>=2/singleton/empty/padding is NOT_EXERCISED, not another hard gate'}
    need(expected_pre['core_path_possible'],'INCONCLUSIVE: original fixed TRAIN batch lacks BEC real edges at both levels; no sample replacement')
    need(record['native_coverage_preflight']==expected_pre and record['actual_fine_edges']==expected_pre['fine_edges'] and record['actual_middle_edges']==expected_pre['middle_edges'],'Actual BEC preflight/edge counts differ')
    need(record['core_path_observed'] is True and record['actual_builder_calls']==len(support),'Missing actual BEC core/builder path')
    for key in ('actual_two_up_split_private_mean_two_down_path','actual_original_coarse_skip_masked_and_consumed','original_ID_restoration_and_unsupported_padding_delta0_exact','actual_a2_enters_original_LN2','unsupported_coarse_bias_masked_in_reference'):
        need(record[key] is True,'Missing original BEC path control: '+key)
    need(record['coarse_original_LN_FFN_calls']==1 and record['original_LN_calls']=={'0':1,'1':1,'2':1},'Original coarse transform/three LN calls changed')
    B=len(support)
    for level,key in enumerate(('fine_input','middle_input','coarse_raw_input')):
        tensor(record[key]);need(record[key]['shape']==[B,widths[level],256],'Original BEC bank shape differs')
    need(len(record['outputs'])==len(record['output_sha256'])==3,'BEC helper must return three banks')
    for level,value in enumerate(record['outputs']):
        tensor(value);need(value['shape']==[B,widths[level],256],'BEC output bank shape differs');need(hash_string(record['output_sha256'][level]),'BEC output fingerprint missing')
        gradients(record,'native_helper_level'+str(level)+'_output_gradients')
    for key in ('native_fine_norm_input_gradients','native_middle_norm_input_gradients','native_coarse_raw_input_gradients','native_collected_coarse_input_gradients'):gradients(record,key)
    for key in ('coarse_collected_input_sha256','coarse_actual_FFN_output_sha256','coarse_supported_mask_sha256','coarse_masked_delta_sha256'):need(hash_string(record[key]),'Original collected-coarse/mask fingerprint missing')
    operators=record['operator_calls'];need(len(operators)==len(up)+len(down),'Wrong actual BEC operator count')
    by_op={}
    for call,(b,name,rows) in zip(operators,up+down):
        need(call['batch']==b and call['operator']==name and call['forward']==record['forward'] and call['actual_real_edges']==rows,'BEC up/coarse/down source order/count differs')
        need(call['actual_original_branch_inputs_match'] is True and call['original_GELU_calls']==1,'Actual captured branch/activation control missing')
        for key in ('input','linear_output','output'):tensor(call[key])
        columns=512 if name.startswith('up_') else 256
        need(call['input']['shape']==[rows,512] and call['linear_output']['shape']==call['output']['shape']==[rows,columns] and call['field_shapes']==[[rows,256],[rows,256]],'BEC new map dimensions changed')
        need(len(call['field_sha256'])==2 and all(hash_string(h) for h in call['field_sha256']),'BEC captured input-field fingerprints missing')
        for key in ('input_sha256','linear_output_sha256','output_sha256'):need(hash_string(call[key]),'BEC captured actual map fingerprint missing')
        for key in ('native_input_gradients','native_linear_output_gradients','native_output_gradients'):gradients(call,key) # legal per-call zero
        if name.startswith('up_'):
            views=call['actual_split_views'];need(set(views)=={'retained_sha256','upward_sha256'} and all(hash_string(h) for h in views.values()),'Missing actual U/V split')
            need(call['native_split_output_gradients'],'Missing original-loss U/V split readout')
            for pair in call['native_split_output_gradients']:
                tensor(pair['retained']);tensor(pair['upward']);need(pair['retained']['shape']==pair['upward']['shape']==[rows,256],'BEC U/V split gradient shape differs')
        else:
            retained=by_op[(b,'up_middle' if name=='down_middle' else 'up_fine')]['actual_split_views']['retained_sha256']
            need(call['field_sha256'][0]==retained,'Actual retained U branch did not enter corresponding down map')
        by_op[(b,name)]=call
    private=record['private_mean_calls'];need(len(private)==len(means),'Actual private mean call count differs')
    for call,(b,level,rows,groups,width) in zip(private,means):
        need(call['forward']==record['forward'] and call['batch']==b and call['level']==level and call['groups']==groups and call['width']==width and call['actual_supported_rows']==rows,'Private mean original child groups/count/order differs')
        need(call['original_mean_calls']==1 and call['means_recomputed_by_observer'] is False and call['equal_child_row_counts']==[len(v) for _,v in groups],'Private mean must consume original outputs once with equal child rows')
        tensor(call['input']);tensor(call['output']);need(call['input']['shape']==[rows,256] and call['output']['shape']==[width,256],'Private mean shape differs')
        need(hash_string(call['input_sha256']) and hash_string(call['output_sha256']),'Private actual mean fingerprints absent')
        if rows:
            name='up_fine' if level==0 else 'up_middle';need(call['input_sha256']==by_op[(b,name)]['actual_split_views']['upward_sha256'],'Actual upward V split did not enter private mean')
            gradients(call,'native_mean_input_gradients');gradients(call,'native_mean_output_gradients')
        else:need(call['empty_boundary_status'].startswith('NOT_EXERCISED'),'Empty private mean boundary overclaimed')
    need(record['offdiagonal_dependency_probe']=='NOT_IMPLEMENTED_NOT_MEASURED','Unimplemented BEC probe overclaimed')
    return expected_pre
''')
replace('required_weight_blocks', '''def required_weight_blocks(raw,candidate):
    expected={name+'_'+out+'_'+field for name in ('up_fine','up_middle') for out in ('retained','upward') for field in ('child','parent')}
    expected|={name+'_'+field for name in ('down_middle','down_fine') for field in ('retained','context')}
    if not candidate:expected=set()
    for step in raw['steps']:
        need(set(step['native_parameter_block_gradients'])==set(step['parameter_block_before_step_hash'])==set(step['parameter_block_after_step_hash'])==expected,'Missing actual BEC12 aggregate weight slices')
        for name,value in step['native_parameter_block_gradients'].items():
            tensor(value,True);need(value['shape']==[256,256],'BEC aggregate slice shape differs')
            before=step['parameter_block_before_step_hash'][name];after=step['parameter_block_after_step_hash'][name]
            need(hash_string(before) and hash_string(after) and before!=after,'BEC aggregate slice update absent; weight decay alone is insufficient')
''')

# Keep the original native loop validation; replace only BEC-specific inventories,
# callback nonzero gates (7e5 per-call finite-only), and three original HCG skips.
text=text.replace("len(raw['ffn_calls'])==(4 if candidate else 6)","len(raw['ffn_calls'])==(2 if candidate else 6)")
text=text.replace("tracked=('ffn_0','ffn_2','triadic_mix') if candidate", "tracked=('ffn_2','up_fine','up_middle','down_middle','down_fine') if candidate")
text=text.replace("levels=[0,2] if candidate", "levels=[2] if candidate")
text=text.replace("tensor(record['input']);tensor(record['output']);gradients(record,'native_input_gradients',True);gradients(record,'native_output_gradients',True)","tensor(record['input']);tensor(record['output']);gradients(record,'native_input_gradients');gradients(record,'native_output_gradients')")
text=text.replace("        need(record['original_residual_levels']=={str(i):True for i in levels},'Remaining fine/coarse/original skip path changed')\n        if candidate:need(record['BEC_middle_original_skip_and_exact_HCG_input'] is True,'Original middle cf skip/triadic output did not reach HCG')", "        if candidate:\n            need(record['original_residual_levels']=={} and record['BEC_original_three_skip_HCG_inputs']==[True,True,True] and record['BEC_helper_coarse_object_exact'] is True,'Original BEC three skips/coarse object did not reach HCG')\n        else:need(record['original_residual_levels']=={str(i):True for i in levels},'Original M95 skip path changed')")
text=text.replace("expected={'0':525568,'1':0 if candidate else 525568,'2':525568}","expected={'0':0 if candidate else 525568,'1':0 if candidate else 525568,'2':525568}")
text=text.replace("inv['new_declared_parameters']==(196864 if candidate else 0) and inv['geometry_registered_buffer_names']==[]", "inv['new_declared_parameters']==(787968 if candidate else 0) and inv['new_registered_buffer_names']==[]")
text=text.replace("triadics=raw['BEC_edge_observations']","edges=raw['BEC_edge_observations']").replace('len(triadics)','len(edges)').replace('enumerate(triadics)','enumerate(edges)')
text=text.replace("exclusions=['dec.cluster_att.cluster_ffn.1.','dec.cluster_att.bipartite_edges.']", "exclusions=['dec.cluster_att.cluster_ffn.0.','dec.cluster_att.cluster_ffn.1.','dec.cluster_att.bipartite_edges.']")
text=text.replace("and any(n.startswith('dec.cluster_att.cluster_ffn_norm.1.') for n in ci['names'])", "and all(any(n.startswith('dec.cluster_att.cluster_ffn_norm.'+str(i)+'.') for n in ci['names']) for i in range(3)) and any(n.startswith('dec.cluster_att.cluster_ffn.2.') for n in ci['names'])")
text=text.replace("a['parameters']-b['parameters']==196864-525568", "a['parameters']-b['parameters']==787968-2*525568")
start=text.index("      'actual_three_distinct_real_input_row_counts':")
end=text.index("      'first_raw_bank_digest_comparison':",start)
text=text[:start]+'''      'actual_fine_edge_counts':[v['actual_fine_edges'] for v in records],
      'actual_middle_edge_counts':[v['actual_middle_edges'] for v in records],
      'actual_new_operator_call_counts':[{n:sum(c['operator']==n for c in v['operator_calls']) for n in ('up_fine','up_middle','down_middle','down_fine')} for v in records],
      'actual_private_mean_call_counts':[len(v['private_mean_calls']) for v in records],
      'actual_required_weight_blocks':sorted(s['steps'][0]['native_parameter_block_gradients']),
      'actual_optional_boundary_counts':[[{'singleton_fine':b['true_support']['singleton_fine_parent_groups'],'singleton_middle':b['true_support']['singleton_middle_parent_groups'],'degree_ge2_fine':b['true_support']['degree_ge2_fine_parent_groups'],'degree_ge2_middle':b['true_support']['degree_ge2_middle_parent_groups'],'unsupported':[len(b[k]) for k in ('unsupported_internal_fine_ids','unsupported_internal_middle_ids','unsupported_internal_coarse_ids')],'padding':b['padding_rows']} for b in v['batches']] for v in records],
'''+text[end:]
text=text.replace('candidate package is staged hash-bound4e8','candidate package is staged hash-bound9b67').replace('M215-BEC/config/4e8/goal','M215-BEC/config/9b67/goal')
text=text.replace('Candidate4e8 and actual runtime48fc','Candidate9b67 and actual runtime48fc')
compile(text,str(HERE/'review_bec.py'),'exec')
with (HERE/'review_bec.py').open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
print('checker_sha256='+hashlib.sha256((HERE/'review_bec.py').read_bytes()).hexdigest())
