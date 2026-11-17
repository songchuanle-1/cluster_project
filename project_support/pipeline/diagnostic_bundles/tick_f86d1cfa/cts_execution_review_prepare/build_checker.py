"""Build a local CTS JSON reviewer from the reviewed BFC envelope/resource shell."""
from pathlib import Path
import ast
import hashlib

HERE=Path(__file__).resolve().parent
SOURCE=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_336ca5d7/bfc_execution_review_prepare/review_bfc.py')
text=SOURCE.read_text(encoding='utf-8')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='cb245895a3f4b8619f4e1fad183a5654d0ac11fc68bf96a202bce66a1550ecb8'
for before,after in [
    ('hierarchy-parent-butterfly-token-composition','hierarchy-parent-cyclic-triadic-state-composition'),
    ('M213-BFC','M214-CTS'),('_bfc','_cts'),('BFC_butterfly_observations','CTS_triadic_observations'),
    ('middle_butterfly','middle_triad'),('butterfly_mix','triadic_mix'),('butterfly_record','triadic_record'),
    ('BFC','CTS'),('bfc_','cts_'),('butterflies','triadics'),('butterfly','triadic'),
    ("COMMIT='48fc302c3c02ffef0b241be3593c386b6b65a72e'", "COMMIT='4e80006047d5cb3dcdfb9c1102e02c33f354a07d'\nRUNTIME_EXPECTED='48fc302c3c02ffef0b241be3593c386b6b65a72e'"),
    ("ORIGIN='pipeline/diagnostic_bundles/tick_ab7e46d4/bfc_native_prepare'", "ORIGIN='pipeline/diagnostic_bundles/tick_4694ba96/cts_native_prepare'"),
    ('727b89a23dedd97f152a557755133c73ce338c311689a716cc32c336e39259f4','ff7fb7a65999369f277744828598822883a222a10ce1ef02732aafeb561fb2cf'),
    ('8839251920577921493b0b663df123c330b850b08779c9841d1d98bbe26e813e','03329ec50fba63d67330342052ec34262f772aee6cc16d3d8d2978d58628c27c'),
    ('8512a69de3d5fcdd32523bbf966833485f3e17329235881de7aa0bd5adbe4501','bfab01a31a0fc7a0d679156d5e0e6fcfa987e56e5f3bb1bdf6bded9e2208f76e'),
    ('262656','196864'),
]:
    text=text.replace(before,after)
# The namespace transform precedes this literal because the old path contains bfc.
text=text.replace("ORIGIN='pipeline/diagnostic_bundles/tick_ab7e46d4/cts_native_prepare'", "ORIGIN='pipeline/diagnostic_bundles/tick_4694ba96/cts_native_prepare'")
text=text.replace('CTS actual pair-stage/mix/GELU/scatter/quadrant checks follow unchanged worker883925 observations. No actual results exist at preparation.', 'CTS old-state own/positive/negative mix/GELU/scatter/three-column checks follow unchanged worker03329 observations. Actual results are absent at preparation.')


def replace_function(name,source):
    global text
    node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=text.splitlines(keepends=True)
    text=''.join(lines[:node.lineno-1])+source.rstrip()+'\n'+''.join(lines[node.end_lineno:])


replace_function('configure_current_anchors', '''def configure_current_anchors(project):
    global FROZEN,PREP_SHA,TEMPLATE_SHA,RELEASE,RELEASE_SHA
    project=Path(project).resolve()
    c=next(x for x in read(project/'pipeline/research_work.json')['candidates'] if x['id']==CID)
    need(c['code_commit']==COMMIT and c['goal_sha256']==GOAL,'Current CTS external candidate identity changed')
    grant=project/'pipeline/authorizations/server4_gpu1_20261025.json'
    need(digest(grant)=='90f8820a60ef4d4e277904815b025658f7b8b457b0711a4d0ef5f7395fdd23f8','Exact explicit GPU resource grant missing/changed')
    native=c['worker_preparation']['preparation'];outer=c['execution_adapter']['preparation'];release=c['execution_adapter']['release']
    expected=[('pipeline/diagnostic_bundles/tick_6bdbcf77/cts_operational_prepare/native/preparation.json','aab40a87e8fcdff7b92cdd95ceb07340d81f8e9acb71ec101e100d9ac42edfc4'),
              ('pipeline/diagnostic_bundles/tick_6bdbcf77/cts_operational_prepare/preparation.json','51cbc658fcf5877a0b46776e361adb99d36d4551841aacdf7559ac6d46c937d6'),
              ('pipeline/diagnostic_bundles/tick_6bdbcf77/cts_operational_prepare/adapter_release.json','eaa3e84f0b07ccb4c5dc7cdd732995894d7c00d079562847611b57bdb118fa99')]
    for item,(name,h) in zip((native,outer,release),expected):
        need(item=={'path':name,'sha256':h},'Current external CTS packet is not the reviewed exact version')
        path=(project/item['path']).resolve();need(path.is_relative_to(project) and digest(path)==item['sha256'],'Current external package anchor mismatch')
    FROZEN=Path(native['path']).parent.as_posix();PREP_SHA=native['sha256'];RELEASE=release['path'];RELEASE_SHA=release['sha256']
    prep=read(project/native['path']);TEMPLATE_SHA=prep['prepared_file_hashes']['manifest_template.json']
    need(prep['code_commit']==prep['source_commit']==COMMIT and prep['source_parent_commit']==prep['runtime_expected_commit']==RUNTIME_EXPECTED and prep['draft_execution_disabled'] is False,'Reviewed version-bound CTS operational packet required')
    need(TEMPLATE_SHA=='9d6125187ccec3378d372c3952705cc8190cd855e5beb223d1300c82a6b9ef5d','Exact CTS template changed')
    need(digest(project/ORIGIN/'preparation.json')==ORIGIN_PREP_SHA and digest(project/FROZEN/'worker.py')==WORKER_SHA,'Reviewed disabled origin or CTS worker changed')
    need(digest(project/ORIGIN/'native_runtime.py')=='5e8959c61d6554d836d9b0736a874d8dca4861b0c91c64716abb666de46abf27','Original disabled/unversioned runtime changed')
    need(digest(project/FROZEN/'native_runtime.py')=='ca74d300e84fccc87bf4d21ee49c335e4f18606f0213a1a5589c5700e17ecce3','Exact reviewed CTS version/runtime48fc guard changed')
    proof=read(project/FROZEN/'source_version_binding.json')
    need(proof['code_commit']==COMMIT and proof['parent_commit']==proof['runtime_expected_commit']==RUNTIME_EXPECTED and proof['original_source_preparation_sha256']==SOURCE_PREP_SHA and len(proof['source_files'])==9,'Actual source4e8/parent48fc binding differs')
    for item,h in [(proof['isolated_source_version'],'6b666a8c8e9d0f5bed8422fa02e6e2ea17192b1114c6eda5ecf28affb409c2d0'),(proof['isolated_source_version_independent_review'],'5f3eb45ef1672730a18cf1d211837e1bc06e47f5c0010dd550f55227ac59de87')]:
        path=(project/item['path']).resolve();need(path.is_relative_to(project) and item['sha256']==h and digest(path)==h,'Actual CTS source version proof changed')
    package=read(project/outer['path'])
    need(package['candidate_id']==CID and package['code_commit']==COMMIT,'Outer CTS identity differs')
    for name,h in package['prepared_file_hashes'].items():
        path=(project/Path(outer['path']).parent/name).resolve();need(path.is_relative_to((project/Path(outer['path']).parent).resolve()) and digest(path)==h,'Externally anchored outer package changed: '+name)
    return [dict(native),dict(outer),dict(release),{'path':grant.relative_to(project).as_posix(),'sha256':digest(grant)},{'path':ORIGIN+'/preparation.json','sha256':ORIGIN_PREP_SHA}]
''')

replace_function('topology_functions', '''def topology_functions():
    """Only hash-bound pure stdlib metadata functions; no model/Torch import."""
    directory=Path('D:/project/cluster_project')/FROZEN
    environment={'math':math}
    entries=[('candidate_model/middle_triad.py','build_triadic_plan'),('worker.py','triadic_plan_observation'),('worker.py','triadic_coverage_preflight')]
    for filename,name in entries:
        tree=ast.parse((directory/filename).read_text(encoding='utf-8'))
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        exec(compile(ast.Module(body=[function],type_ignores=[]),str(directory/filename),'exec'),environment)
    return tuple(environment[name] for filename,name in entries)
''')

replace_function('actual_coverage', '''def actual_coverage(record,groups,calls):
    rounds=[c for c in calls if c['kind']=='round']
    expected={'actual_three_distinct_real_input_rows':sum(c['three_distinct_real_input_rows'] for c in rounds),
              'actual_multiround_supported_parent_groups':sum(g['multiround'] for g in groups),
              'actual_dilated_round_calls':sum(c['round_index']>=1 for c in rounds)}
    for field,count in expected.items():
        need(type(record[field]) is int and record[field]==count,'Actual CTS coverage count differs: '+field)
        need(count>0,'INCONCLUSIVE: original fixed TRAIN batch lacks3distinct/multiround/r>=1; no sample replacement')
    return expected
''')

replace_function('triadic_record', '''def triadic_record(record):
    tensor(record['input']);tensor(record['output'])
    need(record['input']['shape']==record['output']['shape'] and record['input']['shape'][-1]==256,'CTS output escaped original middle bank/width')
    need(record['original_middle_norm_calls']==record['original_triadic_forward_calls']==1,'Original middle norm/operator call count changed')
    for key in ('returned_original_bank_shape','original_ID_inverse_scatter_observed','unsupported_and_batch_padding_update_zero','final_writeback_from_actual_outputs_reference_exact','actual_output_requires_grad'):
        need(record[key] is True,'Original middle support/scatter/autograd control missing: '+key)
    need(record['self_exclusive_claim'] is False,'CTS includes own state and makes no self-exclusive claim')
    build,describe,preflight=topology_functions();groups=[];sequence=[]
    for batch in record['batches']:
        counts=batch['real_point_counts'];k=batch['middle_prefix'];width=batch['padded_width']
        need(type(k) is int and type(width) is int and len(counts)==k<=width and all(type(n) is int and n>=0 for n in counts),'Malformed real support/prefix')
        need(batch['true_supported_original_ids']==[i for i,n in enumerate(counts) if n>0] and batch['unsupported_internal_ids']==[i for i,n in enumerate(counts) if n==0] and batch['batch_padding_rows']==width-k,'Actual point support/padding differs')
        need(batch['support_formula']=='bincount(ids1[ids0],minlength=ids2.numel())>0','True support source changed')
        plan=build(batch['centers'],batch['parent_ids'],[n>0 for n in counts],64);g,seq=describe(plan)
        for x in g:x['batch']=batch['batch']
        for x in seq:x['batch']=batch['batch']
        groups.extend(g);sequence.extend(seq)
    groups=json.loads(json.dumps(groups));sequence=json.loads(json.dumps(sequence))
    need(record['groups']==groups and record['actual_builder_calls']==len(record['batches'])==record['input']['shape'][0],'Actual CTS production plan/group/builder mismatch')
    calls=record['mix_calls'];need(len(calls)==len(sequence),'Actual CTS shared round/singleton call count differs')
    actual_coverage(record,groups,sequence)
    gradients(record,'native_input_gradients',True);gradients(record,'native_output_gradients',True)
    for index,(call,expected) in enumerate(zip(calls,sequence)):
        need(all(call[k]==v for k,v in expected.items()) and call['call_index']==index and call['forward']==record['forward'],'Actual CTS original-ID source/round/call order differs')
        for key in ('actual_all_inputs_from_same_old_state','no_fake_padded_triplet_participant','cross_receiver_donor_reuse_is_legal'):
            need(call[key] is True,'Actual old-state/donor boundary control missing: '+key)
        need(call['duplicate_real_source_within_receiver'] is False and call['activation_original_calls']==1,'CTS source deduplication/original GELU differs')
        rows=len(expected['own_ids']) if call['kind']=='round' else len(expected['original_ids'])
        for key in ('input','linear_output','output','own_input','positive_input','negative_input'):tensor(call[key])
        need(call['input']['shape']==[rows,768] and call['linear_output']['shape']==call['output']['shape']==[rows,256],'Actual CTS3C-toC map dimensions changed')
        need(all(call[key]['shape']==[rows,256] for key in ('own_input','positive_input','negative_input')),'CTS three actual source dimensions changed')
        for key,shape in [('native_input_gradients',[rows,768]),('native_linear_output_gradients',[rows,256]),('native_output_gradients',[rows,256])]:
            gradients(call,key)  # Individual call/row zeros are legal; only aggregate W blocks require nonzero.
            need(all(g['shape']==shape for g in call[key]),'Actual CTS call gradient shape differs')
        for key in ('input_sha256','linear_output_sha256','output_sha256','old_state_sha256','writeback_reference_sha256'):need(hash_string(call[key]),'Actual CTS fingerprint absent: '+key)
        if call['kind']=='round':
            need(call['unpaired_carry_reference_exact'] is True and call['aliased_negative_slots_private_zero_observed'] is True,'Old-state carry/private aliased-negative boundary differs')
        else:need(call['singleton_private_zero_neighbors'] is True and call['positive_input']['abs_max']==call['negative_input']['abs_max']==0,'Singleton private-zero neighbors differ')
    rounds=[c for c in calls if c['kind']=='round']
    need(record['actual_round_mix_calls']==len(rounds) and record['actual_singleton_mix_calls']==sum(c['kind']=='singleton' for c in calls),'Actual CTS batched map counts differ')
    need(record['actual_aliased_negative_zero_rows']==sum(c['aliased_negative_zero_rows'] for c in rounds),'Actual CTS alias count differs')
    need(record['actual_supported_singleton_groups']==sum(g['n']==1 for g in groups) and record['actual_unsupported_internal_rows']==sum(len(b['unsupported_internal_ids']) for b in record['batches']) and record['actual_padding_rows']==sum(b['batch_padding_rows'] for b in record['batches']),'Actual optional CTS boundary coverage differs')
    need(record['offdiagonal_dependency_probe']=='NOT_IMPLEMENTED_NOT_MEASURED','Unimplemented probe overclaimed')
    return preflight([(b['parent_ids'],[n>0 for n in b['real_point_counts']]) for b in record['batches']])
''')

replace_function('required_weight_blocks', '''def required_weight_blocks(raw,candidate):
    expected={'own_input','positive_input','negative_input'} if candidate else set()
    for step in raw['steps']:
        need(set(step['native_parameter_block_gradients'])==expected,'Missing actual three CTS W input-column gradients')
        need(set(step['parameter_block_before_step_hash'])==set(step['parameter_block_after_step_hash'])==expected,'Missing actual CTS slice update fingerprints')
        for name,value in step['native_parameter_block_gradients'].items():
            tensor(value,True);need(value['shape']==[256,256],'Required W input-column dimensions changed')
            before=step['parameter_block_before_step_hash'][name];after=step['parameter_block_after_step_hash'][name]
            need(hash_string(before) and hash_string(after) and before!=after,'Required W input-column actual update absent; weight decay alone is insufficient')
''')

# Shared native smoke checks are retained; only CTS observation inventory differs.
text=text.replace("    for record in triadics:triadic_record(record)", "    preflights=raw.get('native_coverage_preflight_observations',[])\n    need(len(preflights)==(2 if candidate else 0),'Missing/unexpected original-batch coverage preflight')\n    for index,record in enumerate(triadics):\n        need(preflights[index]==triadic_record(record),'Actual before-watch coverage preflight differs from source support')")
text=text.replace("    records=s['CTS_triadic_observations']", "    records=s['CTS_triadic_observations']")
text=text.replace("      'actual_n_ge3_supported_parent_group_counts':[v['actual_n_ge3_supported_parent_groups'] for v in records],\n      'actual_nonpower2_supported_parent_group_counts':[v['actual_nonpower2_supported_parent_groups'] for v in records],\n      'actual_multistage_supported_parent_group_counts':[v['actual_multistage_supported_parent_groups'] for v in records],", "      'actual_three_distinct_real_input_row_counts':[v['actual_three_distinct_real_input_rows'] for v in records],\n      'actual_multiround_supported_parent_group_counts':[v['actual_multiround_supported_parent_groups'] for v in records],\n      'actual_dilated_round_call_counts':[v['actual_dilated_round_calls'] for v in records],\n      'actual_aliased_negative_zero_rows':[v['actual_aliased_negative_zero_rows'] for v in records],")
text=text.replace("'actual_required_weight_blocks':['left_output_from_left_input','left_output_from_right_input','right_output_from_left_input','right_output_from_right_input']", "'actual_required_weight_blocks':['own_input','positive_input','negative_input']")
text=text.replace("    need(manifest['source_preparation_sha256']==SOURCE_PREP_SHA", "    need(manifest['runtime_code_commit']==manifest['runtime_expected_commit']==manifest['source_parent_commit']==RUNTIME_EXPECTED and manifest['source_version_commit']==COMMIT,'Candidate4e8 and actual runtime48fc must remain distinct exact identities')\n    need(manifest['source_preparation_sha256']==SOURCE_PREP_SHA")
text=text.replace("    need(binding['stage'] == manifest['stage']", "    need(binding['runtime_code_commit']==RUNTIME_EXPECTED,'Original CTS execution used an unexpected runtime checkout')\n    need(binding['stage'] == manifest['stage']")
text=text.replace('candidate package is staged hash-bound48fc','candidate package is staged hash-bound4e8; actual runtime remains48fc')
text=text.replace('M214-CTS/config/48fc/goal','M214-CTS/config/4e8/goal')
text=text.replace("    need(raw['execution_completed'] is True", "    need(not str(raw.get('coverage_status','')).startswith('INCONCLUSIVE') and 'INCONCLUSIVE_COVERAGE' not in str(raw.get('error','')),'INCONCLUSIVE: original fixed TRAIN batch did not exercise required CTS path; no replacement sample')\n    need(raw['execution_completed'] is True")
text=text.replace("def common(raw, manifest, mode, target):", "def common(raw, manifest, mode, target):\n    need(isinstance(raw,dict),'Actual raw result must be a JSON object')")
text=text.replace("def review_payloads(raws,manifest):", "def review_payloads(raws,manifest):\n    need(isinstance(raws,dict) and set(raws)=={mode+'_'+target for mode,target in PAIRS} and all(isinstance(v,dict) for v in raws.values()),'Exactly four actual raw JSON objects are required')\n    need(isinstance(manifest,dict),'Actual manifest must be a JSON object')")
text=text.replace('(Refused,KeyError,TypeError,ValueError,OSError,StopIteration)', '(Refused,KeyError,TypeError,ValueError,OSError,StopIteration,AttributeError,IndexError)')
text=text.replace("except (Refused,KeyError,TypeError,ValueError,OSError,StopIteration,AttributeError,IndexError) as error:result={'review_status':'REFUSED_MISSING_OR_INVALID_ACTUAL_EVIDENCE'", "except (Refused,KeyError,TypeError,ValueError,OSError,StopIteration,AttributeError,IndexError) as error:result={'review_status':('INCONCLUSIVE_ORIGINAL_BATCH_COVERAGE' if 'INCONCLUSIVE' in str(error) else 'REFUSED_MISSING_OR_INVALID_ACTUAL_EVIDENCE')")
# Descriptive strings must not carry stale BFC graph assumptions.
text=text.replace('four W quadrant','three W input-column').replace('Four aggregate W blocks','Three aggregate W input-column blocks')
compile(text,str(HERE/'review_cts.py'),'exec')
with (HERE/'review_cts.py').open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
print('checker_sha256='+hashlib.sha256((HERE/'review_cts.py').read_bytes()).hexdigest())
