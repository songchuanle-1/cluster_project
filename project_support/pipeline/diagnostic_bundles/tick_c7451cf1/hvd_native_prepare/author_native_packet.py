"""Author HVD diagnostic worker from frozen FINAL MIC worker bytes only."""
from pathlib import Path
import ast,copy,json
import author_guard as ag
ag.author_guard()
ROOT=ag.ROOT;HERE=ag.HERE
PRODUCER=ROOT/'pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_prepare/native'
MOTHER=ROOT/'pipeline/diagnostic_bundles/tick_265517f1/new_candidate_prepare'
NATIVE=HERE/'native'
assert ag.sha(PRODUCER/'worker.py')=='5bdaa5532dd9b794b8e215caac81e1bef1e3ba1c2b654f7dd68fe33106c60348'
source=(PRODUCER/'worker.py').read_text(encoding='utf8')
start=source.index('    if candidate:\n        core=att.mobius_interaction;graph=')
end=source.index('    original_csort=att._cross_scale_orth_loss',start)
source=source[:start]+(HERE/'hvd_observer_block.py.txt').read_text(encoding='utf8')+'\n'+source[end:]
source=source.replace('mobius_interaction','variance_decomposition').replace('MIC','HVD').replace('Mobius','HVD').replace('mic_','hvd_').replace('mic-native','hvd-native')
start=source.index('def hvd_plan_observation(');end=source.index('\n\ndef setup(',start)
source=source[:start]+"""def hvd_plan_observation(plan,members,valid_count,widths):
    points,fm,mc=members;fine=sorted(set(points));middle=sorted({fm[index] for index in fine});coarse=sorted({mc[index] for index in middle})
    assert plan['nodes']==[fine,middle,coarse] and len(points)==valid_count
    expected={'nodes':[fine,middle,coarse],
        'point_to_fine':[fine.index(index) for index in points],
        'fine_to_middle':[middle.index(fm[index]) for index in fine],
        'middle_to_coarse':[coarse.index(mc[index]) for index in middle]}
    assert plan==expected
    output=copy.deepcopy(plan);output.update(point_count=valid_count,true_supported_nodes_by_scale=[len(nodes) for nodes in plan['nodes']],
        unsupported_or_padding_nodes_by_scale=[widths[level]-len(nodes) for level,nodes in enumerate(plan['nodes'])])
    return output
"""+source[end:]
source=source.replace("        assert sum(p.numel() for p in att.variance_decomposition.parameters())==65792\n",'')
start=source.index('    def parameter_blocks():');end=source.index('    def before_step(',start)
source=source[:start]+"    def parameter_blocks():\n        return {}  # HVD trainability is assessed across the whole new core.\n"+source[end:]
source=source.replace("'The shared cell weight block is descriptive; subset/row/column/bias zeros legal. Whole variance_decomposition aggregate weight is the nonzero gate.'", "'Any optional parameter-block report is descriptive; whole variance_decomposition aggregate weight is the only new nonzero gate.'")
source=source.replace("'norm_outputs','encoder_inst_before'", "'norm_outputs','hvd_input_points_ref','hvd_point_mask_ref','encoder_inst_before'")
source=source.replace("        assert ids_list is bank.cluster_ids_list\n", "        assert ids_list is bank.cluster_ids_list\n        if candidate:assert point_feats is state['hvd_input_points_ref'] and point_mask is state['hvd_point_mask_ref']\n")
source=source.replace("new_operator_parameters=65792 if candidate else None", "new_operator_parameters=sum(p.numel() for p in att.variance_decomposition.parameters()) if candidate else None")
source=source.replace("record['actual_true_fine_paths']>0 and record['actual_cell_calls']==record['actual_GELU_calls']==1 and record['actual_subset_slices']==8 and record['actual_contrast_operations']==7 and record['actual_private_mean_calls']==2 and record['actual_final_index_copy_calls']==3", "record['actual_true_fine_paths']>0 and record['actual_supported_scene_count']>0 and record['actual_stats_calls']==record['actual_pack_calls']==record['actual_factor_calls']==record['actual_GELU_calls']==record['actual_supported_scene_count'] and record['actual_group_mean_calls']==8*record['actual_supported_scene_count'] and record['actual_linear_calls']==2*record['actual_supported_scene_count'] and record['actual_final_index_copy_calls']==3*record['actual_supported_scene_count']")
source=source.replace("all(v['actual_true_fine_paths']>0 and v['actual_cell_calls']==v['actual_GELU_calls']==1 and v['actual_subset_slices']==8 and v['actual_private_mean_calls']==2 and v['actual_final_index_copy_calls']==3 for v in exchange_calls)", "all(v['actual_true_fine_paths']>0 and v['actual_stats_calls']==v['actual_pack_calls']==v['actual_factor_calls']==v['actual_GELU_calls']==v['actual_supported_scene_count'] and v['actual_group_mean_calls']==8*v['actual_supported_scene_count'] and v['actual_final_index_copy_calls']==3*v['actual_supported_scene_count'] for v in exchange_calls)")
source=source.replace("Eight subsets/individual rows/columns/biases descriptive only; no per-subset positivity, FP32 cancellation/Jacobian or optional coverage gate.", "Individual statistic components/maps/rows/columns/biases descriptive only; no component positivity, FP32, minimum-effect/Jacobian or optional coverage gate.")
source=source.replace("Whole shared-core original-loss gradient/update", "Whole HVD-core original-loss gradient/update")
ast.parse(source)
def func(text,name):return next(ast.get_source_segment(text,node) for node in ast.parse(text).body if isinstance(node,ast.FunctionDef) and node.name==name)
assert func(source,'resources')==func((PRODUCER/'worker.py').read_text(encoding='utf8'),'resources')
assert '65792' not in source and 'mobius' not in source.lower() and 'actual_subset_slices' not in source
ag.write_text(NATIVE/'worker.py',source)
runtime=(PRODUCER/'native_runtime.py').read_text(encoding='utf8')
runtime=runtime.replace('MIC','HVD').replace('mic_','hvd_').replace('_mic','_hvd').replace('M229-HVD','M230-HVD').replace('M229-MIC','M230-HVD')
runtime=runtime.replace('hierarchy-ancestry-mobius-interaction-composition','hierarchy-native-variance-decomposition-composition')
runtime=runtime.replace('07ef534a6e44f22bd7b2d083550ebd7823d1d3d3','e38d92db60f43dde00ae0e537493dc3f3dfc82db')
runtime=runtime.replace('346af0bbd95ad4e0de616a580c9b0417c53ce2898ba2336d7933122711d60e8d','ae8baa7a0d6dd0524e2e8fb6bba05ba97dd2410f8fa8c686b1c020c2a77b8dfb')
assert 'DRAFT_EXECUTION_DISABLED = True' in runtime;ast.parse(runtime)
ag.write_text(NATIVE/'native_runtime.py',runtime)
manifest=json.loads((MOTHER/'source_manifest.json').read_text(encoding='utf8'))
for path,digest in manifest['source_files_exact9'].items():
    original=MOTHER/'staged_repository'/path;assert ag.sha(original)==digest
    ag.write_bytes(NATIVE/('candidate.yaml' if path.endswith('.yaml') else 'candidate_model/'+Path(path).name),original.read_bytes())
print(json.dumps({'worker_sha256':ag.sha(NATIVE/'worker.py'),'runtime_sha256':ag.sha(NATIVE/'native_runtime.py'),'model_files':len(list((NATIVE/'candidate_model').glob('*.py'))),'resources_body_byte_exact':True}))
