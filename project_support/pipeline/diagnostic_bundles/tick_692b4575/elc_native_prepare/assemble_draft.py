"""Private ELC packet assembly only. Does not import or execute model/runtime entries."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,io,json,shutil,tokenize
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_928313fd/sfc_native_prepare'
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_87f03f29/new_candidate_prepare'
PARENT='c9be548699cd66bf68badff9ae6198a03eafa142'
CID='hierarchy-undirected-edge-state-line-graph-composition'
EXP='M225-ELC'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):(HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert not (HERE/'worker.py').exists(),'Do not overwrite an existing draft'
assert sha(SOURCE/'preparation.json')=='c77746ae35e4f3bfbc1c58e62aff629798946bb91dd0befbd08f247ca5dd7dd8'
source=json.loads((SOURCE/'preparation.json').read_text(encoding='utf-8'))
for name,h in source['prepared_file_hashes'].items():assert sha(SOURCE/name)==h,name
for rel,h in source['source_files'].items():
    p=SOURCE/'staged_repository'/rel;assert sha(p)==h
    target=HERE/'candidate.yaml' if p.suffix=='.yaml' else HERE/'candidate_model'/p.name
    target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
worker=(ORIGIN/'worker.py').read_text(encoding='utf-8')
helpers='''def elc_plan_observation(plan,members):
    points,fm,mc=members;fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
    keys=[(l,i) for l,rows in enumerate((fine,middle,coarse)) for i in rows];positions={key:i for i,key in enumerate(keys)}
    edges=[(positions[(0,i)],positions[(1,fm[i])]) for i in fine]+[(positions[(1,j)],positions[(2,mc[j])]) for j in middle]
    incident=[[] for _ in keys]
    for e,(a,b) in enumerate(edges):incident[a].append(e);incident[b].append(e)
    components=[]
    for root in coarse:
        mids=[j for j in middle if mc[j]==root];fs=[i for i in fine if mc[fm[i]]==root]
        nodes=sorted([positions[(0,i)] for i in fs]+[positions[(1,j)] for j in mids]+[positions[(2,root)]])
        tree_D=2 if len(mids)==1 else 4
        components.append({'root_id':root,'nodes':nodes,'edges':sorted({e for node in nodes for e in incident[node]}),'tree_diameter':tree_D,'line_diameter':tree_D-1})
    expected={'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'node_keys':keys,'edges':edges,'incident':incident,'components':components,'point_count':len(points)}
    assert plan==expected;return copy.deepcopy(plan)


def elc_rounds_observation(plans,rounds):
    components=[];offset=0
    for plan in plans:
        components.extend((offset,c,plan) for c in plan['components']);offset+=len(plan['edges'])
    expected=[]
    for r in range(max((c['line_diameter'] for _,c,_ in components),default=0)):
        receivers=[];counts=[];groups=[]
        for offset,c,plan in components:
            if r>=c['line_diameter']:continue
            for e in c['edges']:
                endpoints=set(plan['edges'][e]);others=[f for f in c['edges'] if f!=e and endpoints.intersection(plan['edges'][f])]
                receivers.append(offset+e);counts.append(len(others))
            groups.extend([offset+e for e in plan['incident'][node]] for node in c['nodes'])
        rows={e:i for i,e in enumerate(receivers)};buckets={}
        for group in groups:
            bucket=buckets.setdefault(len(group),{'degree':len(group),'edges':[],'receiver_rows':[]})
            bucket['edges'].extend(group);bucket['receiver_rows'].extend(rows[e] for e in group)
        expected.append({'receivers':receivers,'counts':counts,'endpoint_buckets':[buckets[k] for k in sorted(buckets)]})
    assert rounds==expected;return True


def elc_coverage_preflight(members):
    scenes=[]
    for batch,(points,fm,mc) in enumerate(members):
        fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
        scenes.append({'batch':batch,'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'actual_path_count':len(fine)})
    return {'scenes':scenes,'true_supported_core_possible':any(p['actual_path_count'] for p in scenes),'total_true_paths':sum(p['actual_path_count'] for p in scenes)}


'''
a=worker.index('def sfc_plan_observation(');b=worker.index('def setup(',a)
worker=worker[:a]+helpers+worker[b:]
a=worker.index('    if candidate:\n        sfc_module=');b=worker.index('    original_csort=',a)
worker=worker[:a]+(HERE/'observer_block.py.txt').read_text(encoding='utf-8')+'\n'+worker[b:]
names={'sfc_coverage_preflight':'elc_coverage_preflight','SFC_synchronous_forest_observations':'ELC_edge_line_graph_observations'}
tokens=[]
for token in tokenize.generate_tokens(io.StringIO(worker).readline):
    text=token.string
    if token.type==tokenize.NAME:text=names.get(text,text.replace('synchronous_forest','edge_line_graph') if text=='synchronous_forest' else text)
    elif token.type==tokenize.STRING:
        text=text.replace('SFC','ELC').replace('synchronous_forest','edge_line_graph').replace('sfc_delta_snapshots','elc_delta_snapshots').replace('sfc-native','elc-native')
    tokens.append(token._replace(string=text))
worker=tokenize.untokenize(tokens)
worker=worker.replace('==131328','==262656').replace('new_operator_parameters=131328','new_operator_parameters=262656')
begin=worker.index('    def parameter_blocks():');end=worker.index('    def before_step(',begin)
worker=worker[:begin]+'''    def parameter_blocks():
        if not candidate:return {}
        c=att.edge_line_graph.channels
        return {name+'_'+role:(module.weight,0,c,col*c,(col+1)*c)
            for name,module in (('initialize',att.edge_line_graph.initialize),('cell',att.edge_line_graph.cell))
            for col,role in enumerate(('child_columns','parent_columns') if name=='initialize' else ('own_columns','other_edge_mean_columns'))}
'''+worker[end:]
old="record['actual_nodes']>0 and record['actual_rounds']==record['actual_neighbor_mean_calls']==record['actual_cell_calls']==record['actual_GELU_calls']==record['actual_state_index_copy_calls']"
new="record['actual_true_edges']>0 and record['actual_initialize_calls']==record['actual_incident_mean_calls']==1 and record['actual_rounds']==record['actual_neighbor_mean_calls']==record['actual_cell_calls']==record['actual_state_index_copy_calls'] and record['actual_GELU_calls']==record['actual_rounds']+1"
assert worker.count(old)==1;worker=worker.replace(old,new)
old="v['actual_nodes']>0 and v['actual_rounds']==v['actual_neighbor_mean_calls']==v['actual_cell_calls']==v['actual_GELU_calls']==v['actual_state_index_copy_calls']"
new="v['actual_true_edges']>0 and v['actual_initialize_calls']==v['actual_incident_mean_calls']==1 and v['actual_rounds']==v['actual_neighbor_mean_calls']==v['actual_cell_calls']==v['actual_state_index_copy_calls'] and v['actual_GELU_calls']==v['actual_rounds']+1"
assert worker.count(old)==1;worker=worker.replace(old,new)
worker=worker.replace('Two cell-input-column blocks descriptive; zeros legal.','Four initialize/cell input-column blocks descriptive; zeros legal.')
worker=worker.replace('Two cell-column blocks descriptive only; no per-round/node/row/column positivity gate.','All initialize/cell input-column blocks descriptive only; no per-map/edge/round/node/row/column positivity gate or forced line-D3 case.')
worker=worker.replace('Original TRAIN2 with actual ELC hooks','Original TRAIN2 with actual ELC hooks')
compile(worker,'private ELC worker','exec');(HERE/'worker.py').write_text(worker,encoding='utf-8',newline='\n')
runtime=(ORIGIN/'native_runtime.py').read_text(encoding='utf-8')
runtime=runtime.replace('SFC','ELC').replace('hierarchy-synchronous-full-neighbor-composition',CID).replace('M224-ELC',EXP)
runtime=runtime.replace('ctf_hcg_csort_sfc','ctf_hcg_csort_elc').replace("'_sfc.yaml'","'_elc.yaml'").replace("'_sfc'","'_elc'").replace("'sfc_'","'elc_'")
runtime=runtime.replace("CANDIDATE_COMMIT = 'c9be548699cd66bf68badff9ae6198a03eafa142'","CANDIDATE_COMMIT = None")
runtime=runtime.replace("SOURCE_PARENT_COMMIT = 'd4d062ef075abfe7cde93d4b4347ce146572762f'","SOURCE_PARENT_COMMIT = None")
runtime=runtime.replace("SOURCE_PREPARATION_SHA256 = '963dc214f10be23eae5852388bf67cef869330d996bec784c01916766314dcf0'","SOURCE_PREPARATION_SHA256 = '"+sha(SOURCE/'preparation.json')+"'")
runtime=runtime.replace("RUNTIME_EXPECTED_COMMIT = 'd4d062ef075abfe7cde93d4b4347ce146572762f'","RUNTIME_EXPECTED_COMMIT = '"+PARENT+"'")
runtime=runtime.replace('DRAFT_EXECUTION_DISABLED = False','DRAFT_EXECUTION_DISABLED = True')
compile(runtime,'private ELC runtime','exec');(HERE/'native_runtime.py').write_text(runtime,encoding='utf-8',newline='\n')
scope={'candidate_id':CID,'experiment_id':EXP,'draft_execution_disabled':True,'code_commit':None,'source_parent_commit':None,'runtime_expected_commit':PARENT,
       'native':'NOT_RUN','resources':'NOT_RUN','source_preparation_sha256':sha(SOURCE/'preparation.json'),'reference_native_preparation_sha256':sha(ORIGIN/'preparation.json'),
       'scope':'WIP only; no actual source version bound. Current main0314/GPU0 AOC occupied; no native/remote/entry or shared operation.'}
save('draft_scope.json',scope)
wip=HERE/'unversioned_disabled_wip';wip.mkdir(exist_ok=False)
for name in ('worker.py','native_runtime.py','draft_scope.json'):shutil.copyfile(HERE/name,wip/name)
print(json.dumps({'worker_sha256':sha(HERE/'worker.py'),'runtime_sha256':sha(HERE/'native_runtime.py'),'source_files':len(source['source_files'])}))
