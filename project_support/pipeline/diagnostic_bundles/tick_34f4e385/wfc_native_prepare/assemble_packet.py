"""Private WFC native draft assembly. Does not import or execute native code."""
from pathlib import Path
import ast, hashlib, json

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
BASE=ROOT/'pipeline/diagnostic_bundles/tick_692b4575/elc_native_prepare'
SOURCE=HERE.parent/'new_candidate_prepare'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,value):
    assert not p.exists(),p
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
assert sha(BASE/'worker.py')=='614ae48a90e5f4c0e8e83b8a34d0c1b2922f1617ec3d74eb868287bb22d66beb'
assert sha(BASE/'native_runtime.py')=='f9f5e6f04edb0ce996c2299062291ac3944a049862e0936f6d57020cd53c88b9'
prep=read(SOURCE/'preparation.json');assert sha(SOURCE/'preparation.json')=='659528feeee9f8a08f2b5e5aad22af9f21f8cc5994940e8fd04854b1976316c6'
code='94c4fe61b38f46f321a7ee84236fea70ade04d9b';parent='18e64b8d95ed0ba5c1053ead114c0f91a4b0c324'
CID=prep['candidate_id'];EXP=prep['experiment_id'];NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_wfc'
proof=HERE.parent/'wfc_version_prepare/isolated_source_version.json'
assert sha(proof)=='76994bbc02a017317488fe305b0c0a835ef29d5ceb1d275779c2eee10b3462e8'
version=read(proof);assert version['code_commit']==code and version['parent_commit']==parent and version['diff_exact9A'] is True
assert version['frozen_source_files']==version['committed_blob_sha256']==prep['source_files']
source_hashes={Path(name).name:value for name,value in prep['source_files'].items() if name.endswith('.py')}
for name,value in prep['source_files'].items():
    source=SOURCE/'staged_repository'/name;assert sha(source)==value
    target=HERE/('candidate_model/'+Path(name).name if name.endswith('.py') else 'candidate.yaml')
    assert not target.exists();target.parent.mkdir(exist_ok=True);target.write_bytes(source.read_bytes())
base_worker=(BASE/'worker.py').read_text(encoding='utf-8');tree=ast.parse(base_worker)
def function(name):
    item=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    return ast.get_source_segment(base_worker,item)+'\n'
head=base_worker[:base_worker.index('def elc_plan_observation')]
helpers='''def wfc_plan_observation(plan,members):
    points,fm,mc=members;fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
    keys=[(l,i) for l,rows in enumerate((fine,middle,coarse)) for i in rows];positions={key:i for i,key in enumerate(keys)}
    edges=[(positions[(0,i)],positions[(1,fm[i])]) for i in fine]+[(positions[(1,j)],positions[(2,mc[j])]) for j in middle]
    neighbors=[[] for _ in keys]
    for a,b in edges:neighbors[a].append(b);neighbors[b].append(a)
    for row in neighbors:row.sort()
    wedges=[(a,m,z) for m,row in enumerate(neighbors) for a,z in itertools.combinations(row,2)]
    incidence=[[i for i,wedge in enumerate(wedges) if node in wedge] for node in range(len(keys))]
    expected={'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'node_keys':keys,'neighbors':neighbors,'edges':edges,'wedges':wedges,'incidence':incidence,'factor_count':len(wedges),'point_count':len(points)}
    assert plan==expected;return copy.deepcopy(plan)


def wfc_coverage_preflight(members):
    scenes=[]
    for batch,(points,fm,mc) in enumerate(members):
        fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
        scenes.append({'batch':batch,'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'actual_path_count':len(fine)})
    return {'scenes':scenes,'true_supported_core_possible':any(p['actual_path_count'] for p in scenes),'total_true_paths':sum(p['actual_path_count'] for p in scenes)}


'''
setup=function('setup').replace("'ELC requires only", "'WFC requires only").replace('dec.cluster_att.edge_line_graph.','dec.cluster_att.wedge_factor.').replace('new-edge_line_graph','new-wedge_factor')
smoke=function('smoke')
start=smoke.index('    if candidate:\n        elc_module=');end=smoke.index('    original_csort=',start)
smoke=smoke[:start]+(HERE/'candidate_observer.txt').read_text(encoding='utf-8')+'\n'+smoke[end:]
smoke=smoke.replace('elc_coverage_preflight','wfc_coverage_preflight').replace('elc_delta_snapshots','wfc_delta_snapshots').replace('elc-native-smoke','wfc-native-smoke')
smoke=smoke.replace('edge_line_graph','wedge_factor').replace('ELC_original','WFC_original').replace('ELC_wedge_factor_observations','WFC_wedge_factor_observations').replace('actual ELC hooks','actual WFC hooks').replace('262656','131328')
start=smoke.index('    def parameter_blocks():');end=smoke.index('    def before_step(',start)
smoke=smoke[:start]+'''    def parameter_blocks():
        if not candidate:return {}
        c=att.wedge_factor.channels
        return {role:(att.wedge_factor.factor_map.weight,0,c,col*c,(col+1)*c)
            for col,role in enumerate(('center_columns','endpoint_sum_columns'))}
'''+smoke[end:]
old="assert record['actual_true_edges']>0 and record['actual_initialize_calls']==record['actual_incident_mean_calls']==1 and record['actual_rounds']==record['actual_neighbor_mean_calls']==record['actual_cell_calls']==record['actual_state_index_copy_calls'] and record['actual_GELU_calls']==record['actual_rounds']+1"
new="assert record['actual_wedges']>0 and record['actual_factor_map_calls']==record['actual_GELU_calls']==record['actual_private_incidence_mean_calls']==1 and record['actual_final_index_copy_calls']==3"
assert old in smoke;smoke=smoke.replace(old,new)
old="len(exchange_calls)==2 and all(v['actual_true_edges']>0 and v['actual_initialize_calls']==v['actual_incident_mean_calls']==1 and v['actual_rounds']==v['actual_neighbor_mean_calls']==v['actual_cell_calls']==v['actual_state_index_copy_calls'] and v['actual_GELU_calls']==v['actual_rounds']+1 for v in exchange_calls)"
new="len(exchange_calls)==2 and all(v['actual_wedges']>0 and v['actual_factor_map_calls']==v['actual_GELU_calls']==v['actual_private_incidence_mean_calls']==1 and v['actual_final_index_copy_calls']==3 for v in exchange_calls)"
assert old in smoke;smoke=smoke.replace(old,new)
smoke=smoke.replace('Four initialize/cell input-column blocks descriptive','Two factor_map input-column blocks descriptive').replace('All initialize/cell input-column blocks descriptive only; no per-map/edge/round/node/row/column positivity gate or forced line-D3 case.','Both factor-map columns descriptive only; no per-wedge/node/row/column positivity or optional role/degree gate.')
smoke=smoke.replace('actual E-state initialize/cell', 'actual WFC factor_map').replace('no true wedge_factor path','no true wedge-factor path')
tail=function('resources')+'\n\n'+function('json_safe')+'\n\n'+function('main').replace('Exact native ELC or original M95','Exact native WFC or original M95')+"\nif __name__=='__main__':\n    main()\n"
worker=head.replace('ELC native','WFC native')+helpers+setup+'\n\n'+smoke+'\n\n'+tail
assert 'edge_line_graph' not in worker and 'elc_' not in worker and 'actual_rounds' not in worker
compile(worker,str(HERE/'worker.py'),'exec');(HERE/'worker.py').write_text(worker,encoding='utf-8')
runtime=(BASE/'native_runtime.py').read_text(encoding='utf-8')
replacements={
    "DRAFT_EXECUTION_DISABLED = False":"DRAFT_EXECUTION_DISABLED = True",
    "CANDIDATE_COMMIT = '18e64b8d95ed0ba5c1053ead114c0f91a4b0c324'":"CANDIDATE_COMMIT = '"+code+"'",
    "SOURCE_PARENT_COMMIT = 'c9be548699cd66bf68badff9ae6198a03eafa142'":"SOURCE_PARENT_COMMIT = '"+parent+"'",
    "SOURCE_PREPARATION_SHA256 = 'c77746ae35e4f3bfbc1c58e62aff629798946bb91dd0befbd08f247ca5dd7dd8'":"SOURCE_PREPARATION_SHA256 = '"+sha(SOURCE/'preparation.json')+"'",
    "RUNTIME_EXPECTED_COMMIT = 'c9be548699cd66bf68badff9ae6198a03eafa142'":"RUNTIME_EXPECTED_COMMIT = '"+parent+"'",
    'Reusable ELC':'Reusable WFC','ELC native preparation':'WFC native preparation',
    'hierarchy-undirected-edge-state-line-graph-composition':CID,"'M225-ELC'":"'M226-WFC'",
    'ctf_hcg_csort_elc/':'ctf_hcg_csort_wfc/',"'_elc.yaml'":"'_wfc.yaml'","'_elc'":"'_wfc'","'elc_'":"'wfc_'"}
for old,new in replacements.items():assert old in runtime,old;runtime=runtime.replace(old,new)
compile(runtime,str(HERE/'native_runtime.py'),'exec');(HERE/'native_runtime.py').write_text(runtime,encoding='utf-8')
binding={'schema_version':1,'candidate_id':CID,'experiment_id':EXP,'code_commit':code,'parent_commit':parent,
    'runtime_expected_commit':parent,'candidate_source_hashes':source_hashes,'candidate_config_sha256':prep['source_files'][prep['config']],
    'source_files':prep['source_files'],'original_source_preparation_sha256':sha(SOURCE/'preparation.json'),
    'source_preparation':ref(SOURCE/'preparation.json'),'native_protocol':ref(SOURCE/'native_protocol.md'),
    'isolated_source_version':ref(proof),'independent_source_review':ref(HERE.parent/'wfc_source_independent_review.json'),
    'scope':'Actual94c4 exact-nine child18e source only. Prototype6595 NULL unchanged. Native DRAFTTrue; future reviewed activation/new operational bundle required; no native, runtime ff or readiness claim.'}
save(HERE/'source_version_binding.json',binding)
manifest=read(BASE/'manifest_template.json')
manifest.update(candidate_id=CID,experiment_id=EXP,candidate_name=NAME,config=prep['config'],code_commit=code,
    candidate_source_hashes=source_hashes,candidate_config_sha256=prep['source_files'][prep['config']],
    source_preparation_sha256=sha(SOURCE/'preparation.json'),draft_execution_disabled=True,base_reference_commit=parent,
    source_version_commit=code,source_parent_commit=parent,future_version_parent=parent,runtime_expected_commit=parent,
    source_version_binding_sha256=sha(HERE/'source_version_binding.json'),scientific_admission=False,
    protocol='Frozen cc9 WFC protocol: original paired naturalTRAIN2 and original full resources. One actual shared factor_map/GELU over true unordered wedges, once original incidence mean,3 actual original-ID scatters/3LN/rawskip/HCG/singleinst. Wholecore aggregate original-loss weight finite/nonzero +aggregate weight/module update only; perwedge/row/column/bias0 legal. DRAFTTrue/10activeNULL/nativeNOT_RUN; future reviewed activation+freshowner/idlephysical0/three locks required.')
diagnostics={'candidate_model/'+name:value for name,value in source_hashes.items()}
diagnostics.update({'candidate.yaml':sha(HERE/'candidate.yaml'),'worker.py':sha(HERE/'worker.py'),'native_runtime.py':sha(HERE/'native_runtime.py'),'source_version_binding.json':sha(HERE/'source_version_binding.json')})
manifest['diagnostic_files']=diagnostics
save(HERE/'manifest_template.json',manifest)
save(HERE/'launcher_plan.json',{'status':'PLAN_ONLY_NOT_AN_EXECUTABLE_RELEASE','candidate_id':CID,'code_commit':code,
    'runtime_expected_commit':parent,'native_status':'NOT_RUN','resources_status':'NOT_RUN','requires':'Independent native observer review, separately frozen activation/operational release, current root owner/resources guard, actual idle selectedGPU0, fresh manifest+lease10fields, three physicalGPU locks; preserve both running jobs.',
    'four_future_worker_commands':[['python','-B','worker.py','--lease','<fresh_exact_lease>','--mode',mode,'--target',target] for mode in ('smoke','resources') for target in ('champion','candidate')],
    'stage_formula':'wfc_<fresh_owner_token8>_gpu0','local_execution_directory':'wfc_execution',
    'no_active_manifest_lease_request_result_or_release_created':True,'model_source_or_protocol_modified':False})
print(json.dumps({'worker_sha256':sha(HERE/'worker.py'),'runtime_sha256':sha(HERE/'native_runtime.py'),'manifest_template_sha256':sha(HERE/'manifest_template.json')}))
