"""Private AOC observer draft assembly; no model imports, Git or remote activity."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,shutil
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_9db8f3be/pes_native_prepare'
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_e666cac0/new_candidate_prepare'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):(HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert sha(SOURCE/'preparation.json')=='f7b85c78198a538985661e04714b8eb48de7e2173547f93f1a3ba7fede53f9dd'
prep=json.loads((SOURCE/'preparation.json').read_text())
checks={p:sha(SOURCE/'staged_repository'/p)==expected for p,expected in prep['source_files'].items()}
assert len(checks)==9 and all(checks.values())
for p,expected in prep['prepared_file_hashes'].items():assert sha(SOURCE/p)==expected,p
save('prototype_integrity_check.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':prep['candidate_id'],'source_preparation':{'path':str((SOURCE/'preparation.json').relative_to(ROOT)).replace('\\','/'),'sha256':sha(SOURCE/'preparation.json')},'exact9_source_bytes_match':checks,'all18_prepared_hashes_match':True,'prototype_code_source_parent_null':all(prep[k] is None for k in ('code_commit','source_commit','source_parent_commit')),'old_prototype_written':False})
for p in (SOURCE/'staged_repository').rglob('*'):
    if not p.is_file():continue
    if p.suffix=='.yaml':shutil.copyfile(p,HERE/'candidate.yaml')
    else:
        target=HERE/'candidate_model'/p.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
text=(ORIGIN/'worker.py').read_text(encoding='utf-8')
start=text.index('def pes_plan_observation(')
end=text.index('def setup(',start)
helpers='''def aoc_plan_observation(plan,members):
    points,fm,mc=members;fine=sorted(set(points))
    middle_for_paths=[fm[i] for i in fine];coarse_for_paths=[mc[j] for j in middle_for_paths]
    middle=sorted(set(middle_for_paths));coarse=sorted(set(coarse_for_paths))
    mp=[middle.index(j) for j in middle_for_paths];cp=[coarse.index(k) for k in coarse_for_paths]
    expected={'fine_ids':fine,'middle_for_paths':middle_for_paths,'coarse_for_paths':coarse_for_paths,
        'middle_ids':middle,'coarse_ids':coarse,'middle_parent_positions':mp,'coarse_parent_positions':cp,
        'middle_path_counts':[mp.count(j) for j in range(len(middle))],
        'coarse_path_counts':[cp.count(k) for k in range(len(coarse))],
        'path_count':len(fine),'point_count':len(points)}
    assert plan==expected
    return copy.deepcopy(plan)


def aoc_coverage_preflight(members):
    scenes=[]
    for batch,(ids0,ids1,ids2) in enumerate(members):
        fine=sorted(set(ids0));middle=sorted({ids1[i] for i in fine});coarse=sorted({ids2[j] for j in middle})
        scenes.append({'batch':batch,'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'actual_path_count':len(fine)})
    return {'scenes':scenes,'true_ancestral_order_path_possible':any(x['actual_path_count'] for x in scenes),
        'total_true_paths':sum(x['actual_path_count'] for x in scenes)}


'''
text=text[:start]+helpers+text[end:]
# Literal identity/namespace substitutions, before replacing the dedicated observer block.
for old,new in [('PES','AOC'),('pes-native-smoke','aoc-native-smoke'),('euler_state','ancestral_commutator'),('pes_context','aoc_context'),('pes_delta_snapshots','aoc_delta_snapshots'),('pes_coverage_preflight','aoc_coverage_preflight'),('true_euler_state_path_possible','true_ancestral_order_path_possible')]:text=text.replace(old,new)
# The broad module literal changes the coverage key as well; canonicalize the one key.
text=text.replace('true_ancestral_commutator_path_possible','true_ancestral_order_path_possible')
begin=text.index('    if candidate:\n        pes_module=')
end=text.index('    original_csort=',begin)
observer=(HERE/'observer_block.py.txt').read_text(encoding='utf-8')
text=text[:begin]+observer+'\n'+text[end:]
text=text.replace("'receiver_columns':(weight,0,c,0,c),'sender_columns':(weight,0,c,c,2*c)","'first_argument_columns':(weight,0,c,0,c),'second_argument_columns':(weight,0,c,c,2*c)")
text=text.replace('per-event','per-call/branch').replace('true supported fine ancestral_commutator path','true supported fine ancestral-order path')
text=text.replace("AOC_ancestral_commutator_observations=exchange_calls","AOC_ancestral_order_observations=exchange_calls")
text=text.replace("assert record['actual_true_edges']>0 and record['actual_total_events']==4*record['actual_true_edges'] and record['actual_cell_calls']==record['actual_GELU_calls']>0", "assert record['actual_true_fine_paths']>0 and record['actual_cell_calls']==record['actual_GELU_calls']==2 and record['actual_private_mean_calls']==2")
text=text.replace("all(v['actual_true_edges']>0 and v['actual_total_events']==4*v['actual_true_edges'] for v in exchange_calls)","all(v['actual_true_fine_paths']>0 and v['actual_cell_calls']==v['actual_GELU_calls']==2 and v['actual_private_mean_calls']==2 for v in exchange_calls)")
text=text.replace("INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_CAVITY","INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_ANCESTRY_PATH")
assert 'actual_true_edges' not in text and 'actual_total_events' not in text and 'euler_state' not in text
compile(text,'AOC_worker_draft','exec')
(HERE/'worker.py').write_text(text,encoding='utf-8',newline='\n')
runtime=(ORIGIN/'native_runtime.py').read_text(encoding='utf-8')
for old,new in [('PES','AOC'),('hierarchy-palindromic-euler-state-composition','hierarchy-ancestral-order-commutator-composition'),('M221-PES','M222-AOC'),('_pes','_aoc'),("'pes_'","'aoc_'"),('0c3e5cb396049b52b5eba8e04367be98a8973da883af8dde7631a23163cb21e0','f7b85c78198a538985661e04714b8eb48de7e2173547f93f1a3ba7fede53f9dd')]:runtime=runtime.replace(old,new)
runtime=runtime.replace("'M221-AOC'", "'M222-AOC'")
runtime=runtime.replace('DRAFT_EXECUTION_DISABLED = False','DRAFT_EXECUTION_DISABLED = True')
runtime=runtime.replace("CANDIDATE_COMMIT = '9c42fdc4e9168acec18980d782ee9c163e043bb7'",'CANDIDATE_COMMIT = None')
runtime=runtime.replace("SOURCE_PARENT_COMMIT = '5c0c211c8ecc9479ecb34dbb8118a95f4b20e391'",'SOURCE_PARENT_COMMIT = None')
runtime=runtime.replace("RUNTIME_EXPECTED_COMMIT = '5c0c211c8ecc9479ecb34dbb8118a95f4b20e391'","RUNTIME_EXPECTED_COMMIT = '9c42fdc4e9168acec18980d782ee9c163e043bb7'")
compile(runtime,'AOC_runtime_draft','exec')
(HERE/'native_runtime.py').write_text(runtime,encoding='utf-8',newline='\n')
def function(t,name):return ast.dump(next(n for n in ast.parse(t).body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
assert function(text,'resources')==function((ORIGIN/'worker.py').read_text(encoding='utf-8'),'resources')
save('draft_scope.json',{'status':'UNFROZEN_UNVERSIONED_AOC_NATIVE_DRAFT_NOT_NATIVE_PASS','candidate_id':prep['candidate_id'],'experiment_id':'M222-AOC','code_commit':None,'source_commit':None,'source_parent_commit':None,'expected_future_source_parent':'9c42fdc4e9168acec18980d782ee9c163e043bb7','runtime_expected_commit':'9c42fdc4e9168acec18980d782ee9c163e043bb7','source_preparation_sha256':sha(SOURCE/'preparation.json'),'native_protocol_sha256':sha(SOURCE/'native_protocol.md'),'draft_execution_disabled':True,'source_commit_binding_pending':True,'manifest_execution_fields':{k:None for k in ('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')},'native':'NOT_RUN','resources':'NOT_RUN','worker_sha256':sha(HERE/'worker.py'),'native_runtime_sha256':sha(HERE/'native_runtime.py'),'resource_function_AST_unchanged':True,'no_formal_preparation_until_actual_source_proof':True})
print(json.dumps({'worker_sha256':sha(HERE/'worker.py'),'runtime_sha256':sha(HERE/'native_runtime.py'),'prototype_exact9_unchanged':True,'draft_execution_disabled':True}))
