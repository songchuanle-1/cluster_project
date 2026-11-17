"""Private SFC observer assembly; never imports model/Torch or executes any entry."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,shutil
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_89d05b33/fcb_native_prepare'
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_9169196d/new_candidate_prepare'
PARENT='d4d062ef075abfe7cde93d4b4347ce146572762f'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):(HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert sha(SOURCE/'preparation.json')=='963dc214f10be23eae5852388bf67cef869330d996bec784c01916766314dcf0'
source=json.loads((SOURCE/'preparation.json').read_text(encoding='utf-8'))
for name,h in source['prepared_file_hashes'].items():assert sha(SOURCE/name)==h,name
for rel,h in source['source_files'].items():
    p=SOURCE/'staged_repository'/rel;assert sha(p)==h
    target=HERE/'candidate.yaml' if p.suffix=='.yaml' else HERE/'candidate_model'/p.name
    target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
worker=(ORIGIN/'worker.py').read_text(encoding='utf-8');begin=worker.index('def fcb_plan_observation(');end=worker.index('def setup(',begin)
helpers='''def sfc_plan_observation(plan,members):
    points,fm,mc=members;fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
    keys=[(l,i) for l,rows in enumerate((fine,middle,coarse)) for i in rows];positions={key:i for i,key in enumerate(keys)}
    neighbors=[[] for _ in keys]
    for child,parent in ([(positions[(0,i)],positions[(1,fm[i])]) for i in fine]+[(positions[(1,j)],positions[(2,mc[j])]) for j in middle]):
        neighbors[child].append(parent);neighbors[parent].append(child)
    for row in neighbors:row.sort()
    components=[]
    for root in coarse:
        mids=[j for j in middle if mc[j]==root];fs=[i for i in fine if mc[fm[i]]==root]
        nodes=sorted([positions[(0,i)] for i in fs]+[positions[(1,j)] for j in mids]+[positions[(2,root)]])
        components.append({'root_id':root,'nodes':nodes,'diameter':2 if len(mids)==1 else 4,'edge_count':len(fs)+len(mids)})
    expected={'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'node_keys':keys,'neighbors':neighbors,
        'components':components,'edge_count':len(fine)+len(middle),'point_count':len(points)}
    assert plan==expected;return copy.deepcopy(plan)


def sfc_rounds_observation(plans,rounds):
    components=[];offset=0
    for plan in plans:
        components.extend((offset,c,plan['neighbors']) for c in plan['components']);offset+=len(plan['node_keys'])
    expected=[]
    for r in range(max((c['diameter'] for _,c,_ in components),default=0)):
        receivers=[];sources=[];source_receivers=[];counts=[]
        for offset,c,neighbors in components:
            if r>=c['diameter']:continue
            for node in c['nodes']:
                row=len(receivers);receivers.append(offset+node);counts.append(len(neighbors[node]))
                sources.extend(offset+n for n in neighbors[node]);source_receivers.extend([row]*len(neighbors[node]))
        expected.append({'receivers':receivers,'sources':sources,'source_receivers':source_receivers,'counts':counts})
    assert rounds==expected;return True


def sfc_coverage_preflight(members):
    scenes=[]
    for batch,(points,fm,mc) in enumerate(members):
        fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
        scenes.append({'batch':batch,'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'actual_path_count':len(fine)})
    return {'scenes':scenes,'true_supported_core_possible':any(p['actual_path_count'] for p in scenes),'total_true_paths':sum(p['actual_path_count'] for p in scenes)}


'''
worker=worker[:begin]+helpers+worker[end:]
for old,new in [('FCB','SFC'),('fcb-native-smoke','sfc-native-smoke'),('fine_coarse_bipartite','synchronous_forest'),
    ('fcb_context','sfc_context'),('fcb_delta_snapshots','sfc_delta_snapshots'),('fcb_coverage_preflight','sfc_coverage_preflight'),('true_fine_coarse_pair_possible','true_supported_core_possible')]:worker=worker.replace(old,new)
begin=worker.index('    if candidate:\n        fcb_module=');end=worker.index('    original_csort=',begin)
worker=worker[:begin]+(HERE/'observer_block.py.txt').read_text(encoding='utf-8')+'\n'+worker[end:]
worker=worker.replace('hooks, replacements, global_replacements = [], [], []','hooks, replacements, global_replacements = [], [], []\n    installations = []')
worker=worker.replace('==262656','==131328').replace('new_operator_parameters=262656','new_operator_parameters=131328')
begin=worker.index('    def parameter_blocks():');end=worker.index('    def before_step(',begin)
worker=worker[:begin]+'''    def parameter_blocks():
        if not candidate:return {}
        c=att.synchronous_forest.channels;weight=att.synchronous_forest.cell.weight
        return {'own_columns':(weight,0,c,0,c),'neighbor_mean_columns':(weight,0,c,c,2*c)}
'''+worker[end:]
worker=worker.replace("exchange_calls[-1]['actual_true_pairs']","exchange_calls[-1]['actual_nodes']")
worker=worker.replace('SFC_synchronous_forest_observations','SFC_synchronous_forest_observations')
worker=worker.replace("record['actual_true_pairs']>0 and record['actual_pair_map_calls']==record['actual_middle_map_calls']==1 and record['actual_GELU_calls']==2 and record['actual_private_mean_calls']==3", "record['actual_nodes']>0 and record['actual_rounds']==record['actual_neighbor_mean_calls']==record['actual_cell_calls']==record['actual_GELU_calls']==record['actual_state_index_copy_calls']")
worker=worker.replace("v['actual_true_pairs']>0 and v['actual_pair_map_calls']==v['actual_middle_map_calls']==1 and v['actual_GELU_calls']==2 and v['actual_private_mean_calls']==3", "v['actual_nodes']>0 and v['actual_rounds']==v['actual_neighbor_mean_calls']==v['actual_cell_calls']==v['actual_GELU_calls']==v['actual_state_index_copy_calls']")
worker=worker.replace('Four map-input-column blocks descriptive; zeros legal. Whole two-map core aggregate weight is the nonzero gate.','Two cell-input-column blocks descriptive; zeros legal. Whole shared-core aggregate weight is the nonzero gate.')
worker=worker.replace('Four map-column blocks descriptive only; no per-map/pair/row/column positivity gate.','Two cell-column blocks descriptive only; no per-round/node/row/column positivity gate.')
worker=worker.replace('Whole two-map core original-loss gradient/update controls trainability.','Whole shared-core original-loss gradient/update controls trainability.')
worker=worker.replace('true scene-local fine-coarse pair','true supported forest core').replace('INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_FINE_COARSE_PAIR','INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_FOREST')
worker=worker.replace('    try:\n        train.train(', '    try:\n        for owner,name,replacement in installations:setattr(owner,name,replacement)\n        train.train(')
assert 'actual_pair_map_calls' not in worker and 'actual_true_pairs' not in worker and 'fine_coarse_bipartite' not in worker
compile(worker,'SFC_worker_draft','exec');(HERE/'worker.py').write_text(worker,encoding='utf-8',newline='\n')
runtime=(ORIGIN/'native_runtime.py').read_text(encoding='utf-8')
for old,new in [('FCB','SFC'),('hierarchy-fine-coarse-complete-bipartite-composition','hierarchy-synchronous-full-neighbor-composition'),('M223-SFC','M224-SFC'),('_fcb','_sfc'),("'fcb_'","'sfc_'"),
    ('44c63ca146496f9052f3823f1ab299bf3fa8e044bab0df014abc33c2ff9343a2','963dc214f10be23eae5852388bf67cef869330d996bec784c01916766314dcf0')]:runtime=runtime.replace(old,new)
runtime=runtime.replace('DRAFT_EXECUTION_DISABLED = False','DRAFT_EXECUTION_DISABLED = True')
runtime=runtime.replace("CANDIDATE_COMMIT = 'd4d062ef075abfe7cde93d4b4347ce146572762f'",'CANDIDATE_COMMIT = None')
runtime=runtime.replace("SOURCE_PARENT_COMMIT = '0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'",'SOURCE_PARENT_COMMIT = None')
runtime=runtime.replace("RUNTIME_EXPECTED_COMMIT = '0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'",f'RUNTIME_EXPECTED_COMMIT = {PARENT!r}')
compile(runtime,'SFC_runtime_draft','exec');(HERE/'native_runtime.py').write_text(runtime,encoding='utf-8',newline='\n')
def fn(text,name):return ast.dump(next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
assert fn(worker,'resources')==fn((ORIGIN/'worker.py').read_text(encoding='utf-8'),'resources')
save('draft_scope.json',{'status':'UNVERSIONED_DISABLED_SFC_NATIVE_DRAFT_NOT_NATIVE_PASS','recorded_at':datetime.now(timezone.utc).isoformat(),
    'candidate_id':source['candidate_id'],'experiment_id':'M224-SFC','code_commit':None,'source_commit':None,'source_parent_commit':None,
    'expected_future_source_parent':PARENT,'runtime_expected_commit':PARENT,'draft_execution_disabled':True,'original21map9source_unchanged':True,
    'worker_sha256':sha(HERE/'worker.py'),'native_runtime_sha256':sha(HERE/'native_runtime.py'),'resources_complete_AST_unchanged':True,
    'manifest_execution_fields':{key:None for key in ('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')},
    'native':'NOT_RUN','resources':'NOT_RUN','formal_source_binding_pending_real_root_proof':True,'no_Git_SSH_GPU_Torch_or_shared_operation':True})
print(json.dumps({'worker':sha(HERE/'worker.py'),'runtime':sha(HERE/'native_runtime.py'),'DRAFT':True,'source_exact9_unchanged':True}))
