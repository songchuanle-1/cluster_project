"""Private stdlib source assembly only; does not import generated worker/runtime."""
from pathlib import Path
import ast

HERE=Path(__file__).resolve().parent
OLD=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_7e492595/cre_native_prepare/worker.py')
text=OLD.read_text('utf-8');tree=ast.parse(text)
def function(name):
    return ast.get_source_segment(text,next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name))
def change(value,old,new):
    assert value.count(old)==1,(old[:120],value.count(old))
    return value.replace(old,new)

metadata='''def hpc_coverage_preflight(members):
    scenes=[]
    for batch,(ids0,ids1,ids2) in enumerate(members):
        fine=sorted(set(ids0));middle=sorted({ids1[i] for i in fine});coarse=sorted({ids2[j] for j in middle})
        counts={k:0 for k in coarse}
        for i in fine:counts[ids2[ids1[i]]]+=1
        scenes.append({'batch':batch,'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,
            'component_fine_descendant_counts':counts,'real_cross_level_path':bool(fine and middle and coarse),
            'two_fine_component':any(n>=2 for n in counts.values())})
    return {'scenes':scenes,'real_cross_level_component_possible':any(x['real_cross_level_path'] and x['two_fine_component'] for x in scenes)}


def hpc_plan_observation(plan,point_ids,fine_to_middle,middle_to_coarse,widths):
    result=copy.deepcopy(plan);fine=result['fine_ids'];middle=result['middle_ids'];coarse=result['coarse_ids']
    assert fine==sorted(set(point_ids)) and middle==sorted({fine_to_middle[i] for i in fine})
    assert coarse==sorted({middle_to_coarse[j] for j in middle})
    assert result['fine_parent_positions']==[middle.index(fine_to_middle[i]) for i in fine]
    assert result['middle_parent_positions']==[coarse.index(middle_to_coarse[j]) for j in middle]
    fc=[result['fine_parent_positions'].count(j) for j in range(len(middle))]
    mc=[result['middle_parent_positions'].count(k) for k in range(len(coarse))]
    assert result['fine_child_counts']==fc and result['middle_child_counts']==mc
    a1=[2.0+n/2.0 for n in fc];a2=[1.0+n for n in mc]
    for j,k in enumerate(result['middle_parent_positions']):a2[k]-=1.0/a1[j]
    assert result['middle_diagonal']==a1 and result['coarse_diagonal']==a2
    assert result['edge_count']==len(fine)+len(middle) and result['active_node_count']==len(fine)+len(middle)+len(coarse)
    assert result['point_count']==len(point_ids)
    prefixes=[max(ids,default=-1)+1 for ids in (point_ids,fine_to_middle,middle_to_coarse)]
    result['optional_boundary_counts']={'unsupported_internal_rows':[prefixes[l]-len(ids) for l,ids in enumerate((fine,middle,coarse))],
        'batch_padding_rows':[widths[l]-prefixes[l] for l in range(3)],'empty_supported_forest':not bool(fine),
        'singleton_fine_components':sum(n==1 for n in hpc_coverage_preflight([(point_ids,fine_to_middle,middle_to_coarse)])['scenes'][0]['component_fine_descendant_counts'].values())}
    result['numerical_scope']='Exact original Python metadata/Schur coefficients, not a native direct-solve or FP32 residual test'
    return result
'''

setup=function('setup')
setup=setup.replace("'CRE requires only the original final hierarchy injection'","'HPC requires only the original final hierarchy injection'")
start=setup.index('    if mode == \'smoke\':\n        excluded =')
end=setup.index('    return torch, gorilla',start)
setup=setup[:start]+'''    if mode == 'smoke':
        common={name:p.detach() for name,p in model.named_parameters()}
        observation={'scope':'Actual entire named-parameter initialization after native backbone pretrain before loader; HPC retains all original parameters/constructors, no exclusions or fixed inferred count',
            'excluded_name_prefixes':[], 'names':list(common), 'shapes':{n:list(p.shape) for n,p in common.items()},
            'tensor_count':len(common),'parameter_count':sum(p.numel() for p in common.values()),
            'sha256':fingerprint(torch,common),'paired_equality':'NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; compare both actual complete named sets and fingerprints, buffers/RNG not claimed'}
        result['common_initialized_parameters']=observation
        result['full_named_parameter_initialization']=observation
'''+setup[end:]

smoke=function('smoke').replace('CRE','HPC').replace('cre-native-smoke','hpc-native-smoke')
a=smoke.index('    ffn_levels =');b=smoke.index('    tracked =',a)
smoke=smoke[:a]+'''    ffn_levels=(0,1,2)
    tracked_modules={'ffn_'+str(i):att.cluster_ffn[i] for i in ffn_levels}
'''+smoke[b:]
smoke=smoke.replace('exchange_calls','resolvent_calls')
a=smoke.index('    if candidate:\n        cre_module=');b=smoke.index('    original_csort=',a)
smoke=smoke[:a]+(HERE/'hpc_observer_block.txt').read_text('utf-8')+'\n'+smoke[b:]
smoke=change(smoke,"coverage=cre_coverage_preflight(members)","coverage=hpc_coverage_preflight(members)")
smoke=change(smoke,"if not coverage['real_cross_root_path_possible']:","if not coverage['real_cross_level_component_possible']:")
smoke=smoke.replace('INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_REAL_CROSS_ROOT_PATH','INCONCLUSIVE_FIXED_BATCH_NO_SUPPORTED_TWO_FINE_COMPONENT')
smoke=change(smoke,"INCONCLUSIVE_COVERAGE: original fixed TRAIN batch lacks any scene with >=2 true coarse roots before grad watches; no resampling/seed change or mechanism rejection","INCONCLUSIVE_COVERAGE: original fixed TRAIN batch lacks a supported fine-middle-coarse component with >=2 fine descendants before grad watches; no redraw or mechanism rejection")
smoke=change(smoke,"calls.append(record);state['ffn_snapshots'][level]=output.detach().clone()",'''calls.append(record);state['ffn_snapshots'][level]=output.detach().clone()
            state['ffn_counts'][level]+=1;state['ffn_outputs'][level]=output
            if candidate:assert values[0] is state['analyzed_outputs'][level]''')
smoke=smoke.replace('cre_delta_snapshots','hpc_delta_snapshots')
smoke=change(smoke,"        for level in ffn_levels:\n            exact=fingerprint(torch,refined[level])==fingerprint(torch,raw[level].detach()+state['ffn_snapshots'][level])", "        for level in (ffn_levels if not candidate else ()):\n            exact=fingerprint(torch,refined[level])==fingerprint(torch,raw[level].detach()+state['ffn_snapshots'][level])")
smoke=change(smoke,"record['HPC_original_three_skips_and_exact_HCG_inputs']=exact;assert all(exact)",'''record['HPC_original_three_skips_and_exact_HCG_inputs']=exact;assert all(exact)
            context=state['hpc_context'];assert context['solver_count']==2 and state['norm_counts']==[1,1,1] and state['ffn_counts']==[1,1,1]
            context['record'].update(actual_three_LN_calls=list(state['norm_counts']),actual_three_FFN_calls=list(state['ffn_counts']),
                original_two_solver_calls=context['solver_count'],actual_cross_level_component_exercised=True,
                original_three_skips_and_HCG_inputs=exact,graph_reachability_scope='Actual original plan/ordered gather-Schur-add-parent-read-writeback graph and native finite loss gradients; no pairwise Jacobian or auxiliary intervention')
            resolvent_calls.append(context['record'])''')
smoke=change(smoke,"state['forward_index']+=1;state['ffn_snapshots']={};state['norm_counts']=[0,0,0];state['norm_outputs']={}","state['forward_index']+=1;state['ffn_snapshots']={};state['ffn_counts']=[0,0,0];state['ffn_outputs']={};state['norm_counts']=[0,0,0];state['norm_outputs']={}")
smoke=smoke.replace("'hpc_delta_snapshots','norm_outputs'","'hpc_delta_snapshots','norm_outputs','ffn_outputs','hpc_context','analyzed_outputs'")
a=smoke.index('    def parameter_blocks():');b=smoke.index('    def before_step(',a)
smoke=smoke[:a]+smoke[b:]
a=smoke.index("        if candidate and not resolvent_calls[-1]['actual_real_directed_root_edges']:");b=smoke.index('        observed={',a)
smoke=smoke[:a]+'''        if candidate:assert resolvent_calls[-1]['original_two_solver_calls']==2 and resolvent_calls[-1]['actual_cross_level_component_exercised']
'''+smoke[b:]
smoke=change(smoke,"assert gradients and all(g is not None and g['finite'] for g in gradients.values())\n            assert all(g['abs_max']>0 for n,g in gradients.items() if n.endswith('weight')),'Native tracked weight gradient is zero; local path control failed, not whole-mechanism rejection; no seed/readout change'",'''weights=[g for n,g in gradients.items() if n.endswith('weight')]
            assert weights and all(g is not None and g['finite'] for g in weights)
            assert all(g is None or g['finite'] for g in gradients.values())
            assert any(g['abs_max']>0 for g in weights),'Native original FFN group aggregate weight gradient is zero; local path control, no resampling or whole-mechanism rejection'
            record.setdefault('tracked_group_aggregate_weight_nonzero',{})[name]=True''')
a=smoke.index("        record['native_parameter_block_gradients']={}");b=smoke.index('    def after_step(',a)
smoke=smoke[:a]+smoke[b:]
a=smoke.index("        record['parameter_block_after_step_hash']");b=smoke.index("        result['optimizer_steps']+=1",a)
smoke=smoke[:a]+smoke[b:]
smoke=change(smoke,'HPC_root_exchange_observations=resolvent_calls','HPC_resolvent_observations=resolvent_calls')
smoke=change(smoke,"coverage_gate_scope='Each original fixed TRAIN forward needs at least one >=2-real-root scene; a singleton scene is legal. Optional boundaries/call/row/bias zeros legal; no resampling.'", "coverage_gate_scope='Each original fixed TRAIN forward needs a true fine-middle-coarse component with at least two supported fine descendants. Optional boundaries/per-call/row/bias zeros legal; no resampling or numerical residual gate.'")
smoke=change(smoke,"'new_declared_parameters':sum(p.numel() for p in att.root_exchange.parameters()) if candidate else 0", "'new_declared_parameters':0")
smoke=change(smoke,"assert len(calls)==(0 if candidate else 6) and len(resolvent_calls)==(2 if candidate else 0)","assert len(calls)==6 and len(resolvent_calls)==(2 if candidate else 0)")
a=smoke.index('    for record in resolvent_calls:');b=smoke.index('    for record in readbacks:',a)
smoke=smoke[:a]+'''    for record in resolvent_calls:
        assert record['original_prepare_calls']==1 and record['original_two_solver_calls']==2 and record['actual_three_LN_calls']==record['actual_three_FFN_calls']==[1,1,1]
        assert [call['phase'] for call in record['solver_calls']]==['analysis','synthesis']
        for call in record['solver_calls']:
            for level in range(3):
                for key in ('native_input_level'+str(level)+'_gradients','native_output_level'+str(level)+'_gradients'):
                    assert call.get(key) and all(g['finite'] for g in call[key])
            for operation in call['operations']:
                if operation['kind']=='new_tensor':continue
                for key in ('native_input_gradients','native_output_gradients'):
                    assert operation.get(key) and all(g['finite'] for g in operation[key])
                if operation['kind'] in ('index_add','index_copy'):
                    assert operation.get('native_source_gradients') and all(g['finite'] for g in operation['native_source_gradients'])
        # Each row/call may be zero. Only three original FFN groups have an aggregate nonzero/update gate.
'''+smoke[b:]
smoke=change(smoke,"intended_path_observed=(len(resolvent_calls)==2 and all(v['actual_real_directed_root_edges']>0 and v['actual_private_mean_calls']==1 for v in resolvent_calls)) if candidate else len(calls)==6", "intended_path_observed=(len(resolvent_calls)==2 and all(v['original_two_solver_calls']==2 and v['actual_cross_level_component_exercised'] for v in resolvent_calls)) if candidate else len(calls)==6")
smoke=change(smoke,'new_operator_parameters=393984 if candidate else None','new_operator_parameters=0')
header=text[:text.index('def cre_plan_observation')].replace('CRE native','HPC native')
main=function('main').replace('Exact native CRE or original M95','Exact native HPC or original M95')
worker=header+metadata+'\n\n'+setup+'\n\n'+smoke+'\n\n'+function('resources')+'\n\n'+function('json_safe')+'\n\n'+main+"\n\nif __name__=='__main__':\n    main()\n"
assert 'root_exchange' not in worker and 'cre_' not in worker and 'parameter_blocks' not in worker
compile(worker,'worker.py','exec')
with (HERE/'worker.py').open('x',encoding='utf-8',newline='\n') as f:f.write(worker)
print('HPC_WORKER_WRITTEN_SOURCE_ONLY',len(worker.splitlines()))
