"""Private FCB draft assembly; numerical resources/runtime functions stay original."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,shutil
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_2ef53d6b/aoc_native_prepare'
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_f8d84d12/new_candidate_prepare'
EXPECTED_PARENT='0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name,value):(HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert sha(SOURCE/'preparation.json')=='44c63ca146496f9052f3823f1ab299bf3fa8e044bab0df014abc33c2ff9343a2'
source=json.loads((SOURCE/'preparation.json').read_text(encoding='utf-8'))
for rel,expected in source['prepared_file_hashes'].items():assert sha(SOURCE/rel)==expected,rel
assert len(source['source_files'])==9 and all(sha(SOURCE/'staged_repository'/rel)==expected for rel,expected in source['source_files'].items())
for rel in source['source_files']:
    path=SOURCE/'staged_repository'/rel
    target=HERE/'candidate.yaml' if path.suffix=='.yaml' else HERE/'candidate_model'/path.name
    target.parent.mkdir(exist_ok=True);shutil.copyfile(path,target)
worker=(ORIGIN/'worker.py').read_text(encoding='utf-8')
start=worker.index('def aoc_plan_observation(');end=worker.index('def setup(',start)
helpers='''def fcb_plan_observation(plan,members):
    points,fm,mc=members;fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
    parents=[middle.index(fm[i]) for i in fine]
    fp=[f for f in range(len(fine)) for _ in coarse];cp=[c for _ in fine for c in range(len(coarse))]
    expected={'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'fine_parent_positions':parents,
        'middle_fine_counts':[parents.count(j) for j in range(len(middle))],'pair_fine_positions':fp,'pair_coarse_positions':cp,
        'fine_pair_counts':[len(coarse)]*len(fine),'coarse_pair_counts':[len(fine)]*len(coarse),
        'pair_count':len(fp),'point_count':len(points)}
    assert plan==expected
    record=copy.deepcopy(plan);record['observed_nonancestor_pairs']=sum(coarse[c]!=mc[fm[fine[f]]] for f,c in zip(fp,cp))
    return record


def fcb_coverage_preflight(members):
    scenes=[]
    for batch,(points,fm,mc) in enumerate(members):
        fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
        scenes.append({'batch':batch,'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,
            'actual_path_count':len(fine),'actual_pair_count':len(fine)*len(coarse)})
    return {'scenes':scenes,'true_fine_coarse_pair_possible':any(x['actual_pair_count'] for x in scenes),
        'total_true_paths':sum(x['actual_path_count'] for x in scenes),'total_true_pairs':sum(x['actual_pair_count'] for x in scenes)}


'''
worker=worker[:start]+helpers+worker[end:]
for old,new in [('AOC','FCB'),('aoc-native-smoke','fcb-native-smoke'),('ancestral_commutator','fine_coarse_bipartite'),
    ('aoc_context','fcb_context'),('aoc_delta_snapshots','fcb_delta_snapshots'),('aoc_coverage_preflight','fcb_coverage_preflight'),
    ('true_ancestral_order_path_possible','true_fine_coarse_pair_possible')]:worker=worker.replace(old,new)
begin=worker.index('    if candidate:\n        aoc_module=');end=worker.index('    original_csort=',begin)
worker=worker[:begin]+(HERE/'observer_block.py.txt').read_text(encoding='utf-8')+'\n'+worker[end:]
worker=worker.replace("==131328","==262656").replace('new_operator_parameters=131328','new_operator_parameters=262656')
old="""        c=att.fine_coarse_bipartite.channels;weight=att.fine_coarse_bipartite.cell.weight
        return {'first_argument_columns':(weight,0,c,0,c),'second_argument_columns':(weight,0,c,c,2*c)}"""
new="""        c=att.fine_coarse_bipartite.channels
        return {name+'_'+side+'_columns':(module.weight,0,c,start,start+c)
            for name,module in [('pair',att.fine_coarse_bipartite.pair_map),('middle',att.fine_coarse_bipartite.middle_map)]
            for side,start in [('first',0),('second',c)]}"""
assert worker.count(old)==1;worker=worker.replace(old,new)
worker=worker.replace('FCB_ancestral_order_observations','FCB_fine_coarse_bipartite_observations')
worker=worker.replace("record['actual_cell_calls']==record['actual_GELU_calls']==2 and record['actual_private_mean_calls']==2", "record['actual_pair_map_calls']==record['actual_middle_map_calls']==1 and record['actual_GELU_calls']==2 and record['actual_private_mean_calls']==3")
worker=worker.replace("v['actual_cell_calls']==v['actual_GELU_calls']==2 and v['actual_private_mean_calls']==2", "v['actual_pair_map_calls']==v['actual_middle_map_calls']==1 and v['actual_GELU_calls']==2 and v['actual_private_mean_calls']==3")
worker=worker.replace('INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_ANCESTRY_PATH','INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_FINE_COARSE_PAIR')
worker=worker.replace('Two input-column blocks descriptive; zeros legal. Whole cell aggregate weight is the nonzero gate.','Four map-input-column blocks descriptive; zeros legal. Whole two-map core aggregate weight is the nonzero gate.')
worker=worker.replace('Two column blocks descriptive only; no per-call/branch/row/column positivity gate.','Four map-column blocks descriptive only; no per-map/pair/row/column positivity gate.')
worker=worker.replace('Whole cell original-loss gradient/update controls trainability.','Whole two-map core original-loss gradient/update controls trainability.')
worker=worker.replace('true supported fine ancestral-order path','true scene-local fine-coarse pair')
worker=worker.replace("if candidate and not exchange_calls[-1]['actual_true_fine_paths']:","if candidate and not exchange_calls[-1]['actual_true_pairs']:")
worker=worker.replace("record['actual_true_fine_paths']>0 and record['actual_pair_map_calls']","record['actual_true_pairs']>0 and record['actual_pair_map_calls']")
worker=worker.replace("v['actual_true_fine_paths']>0 and v['actual_pair_map_calls']","v['actual_true_pairs']>0 and v['actual_pair_map_calls']")
assert 'actual_cell_calls' not in worker and 'ancestral_commutator' not in worker
compile(worker,'FCB_worker_draft','exec');(HERE/'worker.py').write_text(worker,encoding='utf-8',newline='\n')
runtime=(ORIGIN/'native_runtime.py').read_text(encoding='utf-8')
for old,new in [('AOC','FCB'),('hierarchy-ancestral-order-commutator-composition','hierarchy-fine-coarse-complete-bipartite-composition'),
    ('M222-FCB','M223-FCB'),('_aoc','_fcb'),("'aoc_'","'fcb_'"),
    ('f7b85c78198a538985661e04714b8eb48de7e2173547f93f1a3ba7fede53f9dd','44c63ca146496f9052f3823f1ab299bf3fa8e044bab0df014abc33c2ff9343a2')]:runtime=runtime.replace(old,new)
runtime=runtime.replace('DRAFT_EXECUTION_DISABLED = False','DRAFT_EXECUTION_DISABLED = True')
runtime=runtime.replace("CANDIDATE_COMMIT = '0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'",'CANDIDATE_COMMIT = None')
runtime=runtime.replace("SOURCE_PARENT_COMMIT = '9c42fdc4e9168acec18980d782ee9c163e043bb7'",'SOURCE_PARENT_COMMIT = None')
runtime=runtime.replace("RUNTIME_EXPECTED_COMMIT = '9c42fdc4e9168acec18980d782ee9c163e043bb7'",f'RUNTIME_EXPECTED_COMMIT = {EXPECTED_PARENT!r}')
compile(runtime,'FCB_runtime_draft','exec');(HERE/'native_runtime.py').write_text(runtime,encoding='utf-8',newline='\n')
def fn(text,name):return ast.dump(next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
assert fn(worker,'resources')==fn((ORIGIN/'worker.py').read_text(encoding='utf-8'),'resources')
save('draft_scope.json',{'status':'UNFROZEN_UNVERSIONED_FCB_NATIVE_DRAFT_NOT_NATIVE_PASS','recorded_at':datetime.now(timezone.utc).isoformat(),
    'candidate_id':source['candidate_id'],'experiment_id':'M223-FCB','code_commit':None,'source_commit':None,'source_parent_commit':None,
    'expected_future_source_parent':EXPECTED_PARENT,'runtime_expected_commit':EXPECTED_PARENT,'draft_execution_disabled':True,
    'source_preparation_sha256':sha(SOURCE/'preparation.json'),'native_protocol_sha256':sha(SOURCE/'native_protocol.md'),
    'all_original18_prototype_hashes_and9source_match':True,'worker_sha256':sha(HERE/'worker.py'),'native_runtime_sha256':sha(HERE/'native_runtime.py'),
    'manifest_execution_fields':{key:None for key in ('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')},
    'resources_whole_AST_unchanged':True,'native':'NOT_RUN','resources':'NOT_RUN','source_binding_pending_actual_root_proof':True,
    'formal_preparation_created':False,'no_Git_SSH_GPU_Torch_or_shared_operation':True})
print(json.dumps({'worker':sha(HERE/'worker.py'),'runtime':sha(HERE/'native_runtime.py'),'source_exact9_unchanged':True,'DRAFT':True}))
