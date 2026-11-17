"""Private source-bound LFT native draft assembly; no native code is imported."""
from pathlib import Path
import ast, hashlib, json
import author_guard as ag

ag.check()
ROOT=ag.ROOT;HERE=ag.HERE
BASE=ROOT/'pipeline/diagnostic_bundles/tick_34f4e385/wfc_native_prepare'
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_34f4e385/lft_candidate_prepare'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
ref=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
assert sha(BASE/'preparation.json')=='af6d4dd62858baaad4fb773909e2219f9e39c5c2752ebf626f20feae56790e20'
assert sha(BASE/'worker.py')=='2a58906fc56408df78d66e479e0a846f34d0154348e478a04ce378ef14bce3e6'
assert sha(SOURCE/'preparation.json')=='1210502d2454513983554dacf80293f7cd85fbdb55949b39f34e50b8fd01be92'
prep=read(SOURCE/'preparation.json');code='5931d403a8bfc9f4d3fe6115a194bbeb55a9e8b1';parent='18e64b8d95ed0ba5c1053ead114c0f91a4b0c324'
proof=HERE.parent/'lft_version_prepare/isolated_source_version.json'
assert sha(proof)=='920307fd465821f61b9b83a2cbe1c4072a7695769ee1eac7f4456885aa784057'
version=read(proof);assert version['code_commit']==code and version['parent_commit']==parent and version['diff_exact9A'] is True
assert version['frozen_source_files']==version['committed_blob_sha256']==prep['source_files']
CID=prep['candidate_id'];EXP=prep['experiment_id'];NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_lft'
for name,value in prep['source_files'].items():
    source=SOURCE/'staged_repository'/name;assert sha(source)==value
    target=HERE/('candidate_model/'+Path(name).name if name.endswith('.py') else 'candidate.yaml')
    ag.write_bytes(target,source.read_bytes())
base_worker=(BASE/'worker.py').read_text(encoding='utf-8');tree=ast.parse(base_worker)
def function(name):
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    return ast.get_source_segment(base_worker,node)+'\n'
head=base_worker[:base_worker.index('def wfc_plan_observation')].replace('WFC native','LFT native')
helpers='''def lft_plan_observation(plan,members):
    points,fm,mc=members;fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
    mid_position={j:p for p,j in enumerate(middle)};coarse_position={j:p for p,j in enumerate(coarse)}
    fp=[mid_position[fm[i]] for i in fine];mp=[coarse_position[mc[j]] for j in middle]
    expected={'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'fine_parent_positions':fp,'middle_parent_positions':mp,
        'middle_fine_counts':[sum(1 for i in fine if fm[i]==j) for j in middle],
        'coarse_middle_counts':[sum(1 for j in middle if mc[j]==k) for k in coarse],'point_count':len(points)}
    assert plan==expected;return copy.deepcopy(plan)


def lft_coverage_preflight(members):
    scenes=[]
    for batch,(points,fm,mc) in enumerate(members):
        fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
        scenes.append({'batch':batch,'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'actual_path_count':len(fine)})
    return {'scenes':scenes,'true_supported_core_possible':any(p['actual_path_count'] for p in scenes),'total_true_paths':sum(p['actual_path_count'] for p in scenes)}


'''
setup=function('setup')
old="excluded = ('dec.cluster_att.cluster_ffn.0.', 'dec.cluster_att.cluster_ffn.1.', 'dec.cluster_att.cluster_ffn.2.', 'dec.cluster_att.wedge_factor.')"
assert old in setup;setup=setup.replace(old,"excluded = ('dec.cluster_att.nonlinear_lifting.',)")
setup=setup.replace('WFC requires only','LFT requires only').replace('exclude all three removed FFN prefixes and new-wedge_factor subtree on both targets; retain all three LayerNorms','exclude ONLY new nonlinear_lifting subtree on both targets; retain all original FFNs and three LayerNorms')
smoke=function('smoke');start=smoke.index('    if candidate:\n        wfc_module=');end=smoke.index('    original_csort=',start)
smoke=smoke[:start]+(HERE/'candidate_observer.txt').read_text(encoding='utf-8')+'\n'+smoke[end:]
smoke=smoke.replace('actual WFC hooks','actual LFT hooks').replace('wfc_coverage_preflight','lft_coverage_preflight').replace('wfc_delta_snapshots','lft_delta_snapshots').replace('wfc-native-smoke','lft-native-smoke')
smoke=smoke.replace('wedge_factor','nonlinear_lifting').replace('WFC_original','LFT_original').replace('WFC_nonlinear_lifting_observations','LFT_nonlinear_lifting_observations').replace('131328','263168')
smoke=smoke.replace('ffn_levels = () if candidate else (0,1,2)','ffn_levels = (0,1,2)')
old="        assert all(sum(p.numel() for p in att.cluster_ffn[level].parameters())==0 for level in range(3))\n"
assert old in smoke;smoke=smoke.replace(old,'')
old="        for level in ffn_levels:\n            exact=fingerprint(torch,refined[level])"
assert old in smoke;smoke=smoke.replace(old,"        for level in (() if candidate else ffn_levels):\n            exact=fingerprint(torch,refined[level])")
start=smoke.index('    def parameter_blocks():');end=smoke.index('    def before_step(',start)
smoke=smoke[:start]+'''    def parameter_blocks():
        if not candidate:return {}
        c=att.nonlinear_lifting.channels
        return {name:(getattr(att.nonlinear_lifting,name).weight,0,c,0,c)
            for name in ('predict_fine','update_middle','predict_middle','update_coarse')}
'''+smoke[end:]
smoke=smoke.replace("if candidate and not exchange_calls[-1]['actual_nodes']:","if candidate and not exchange_calls[-1]['actual_true_fine_paths']:")
smoke=smoke.replace('no true wedge-factor path','no true lifting path')
smoke=smoke.replace("            if candidate:\n                assert any(","            if candidate and name=='nonlinear_lifting':\n                assert any(")
smoke=smoke.replace("            if candidate:\n                weights=[g", "            if candidate and name=='nonlinear_lifting':\n                weights=[g")
smoke=smoke.replace('Candidate whole nonlinear_lifting aggregate only; individual maps/weights/rows/bias may be zero or unexercised, descriptive only','New nonlinear_lifting core aggregate only; original FFNs retain their original weight gates. Individual new maps/rows/bias may be zero or unexercised.')
smoke=smoke.replace('Two factor_map input-column blocks descriptive','Four new P/U whole weight blocks descriptive')
smoke=smoke.replace('Both factor-map columns descriptive only; no per-wedge/node/row/column positivity or optional role/degree gate.','All four new P/U maps descriptive only; no per-map/row/column/bias positivity or optional degree/inverse gate.')
smoke=smoke.replace('assert len(calls)==(0 if candidate else 6)','assert len(calls)==6')
old="assert record['actual_wedges']>0 and record['actual_factor_map_calls']==record['actual_GELU_calls']==record['actual_private_incidence_mean_calls']==1 and record['actual_final_index_copy_calls']==3"
new="assert record['actual_true_fine_paths']>0 and record['actual_map_calls']==record['actual_GELU_calls']==8 and record['actual_private_mean_calls']==4 and record['actual_original_FFN_calls']==[1,1,1] and record['actual_final_index_copy_calls']==3"
assert old in smoke;smoke=smoke.replace(old,new)
old="len(exchange_calls)==2 and all(v['actual_wedges']>0 and v['actual_factor_map_calls']==v['actual_GELU_calls']==v['actual_private_incidence_mean_calls']==1 and v['actual_final_index_copy_calls']==3 for v in exchange_calls)"
new="len(exchange_calls)==2 and all(v['actual_true_fine_paths']>0 and v['actual_map_calls']==v['actual_GELU_calls']==8 and v['actual_private_mean_calls']==4 and v['actual_original_FFN_calls']==[1,1,1] and v['actual_final_index_copy_calls']==3 for v in exchange_calls)"
assert old in smoke;smoke=smoke.replace(old,new)
worker=head+helpers+setup+'\n\n'+smoke+'\n\n'+function('resources')+'\n\n'+function('json_safe')+'\n\n'+function('main').replace('Exact native WFC or original M95','Exact native LFT or original M95')+"\nif __name__=='__main__':\n    main()\n"
assert 'wedge_factor' not in worker and 'actual_wedges' not in worker and 'WFC' not in worker and 'wfc_' not in worker
compile(worker,str(HERE/'worker.py'),'exec');ag.write_text(HERE/'worker.py',worker)
runtime=(BASE/'native_runtime.py').read_text(encoding='utf-8')
replacements={"CANDIDATE_COMMIT = '94c4fe61b38f46f321a7ee84236fea70ade04d9b'":"CANDIDATE_COMMIT = '"+code+"'",
    "SOURCE_PREPARATION_SHA256 = '659528feeee9f8a08f2b5e5aad22af9f21f8cc5994940e8fd04854b1976316c6'":"SOURCE_PREPARATION_SHA256 = '"+sha(SOURCE/'preparation.json')+"'",
    'Reusable WFC':'Reusable LFT','WFC native preparation':'LFT native preparation',
    'hierarchy-wedge-factor-incidence-composition':CID,"'M226-WFC'":"'M227-LFT'",'ctf_hcg_csort_wfc/':'ctf_hcg_csort_lft/',"'_wfc.yaml'":"'_lft.yaml'","'_wfc'":"'_lft'","'wfc_'":"'lft_'"}
for old,new in replacements.items():assert old in runtime,old;runtime=runtime.replace(old,new)
compile(runtime,str(HERE/'native_runtime.py'),'exec');ag.write_text(HERE/'native_runtime.py',runtime)
source_hashes={Path(name).name:value for name,value in prep['source_files'].items() if name.endswith('.py')}
sourcepeer=ROOT/'pipeline/diagnostic_bundles/tick_34f4e385/lft_source_independent_review.json'
peer=read(sourcepeer);assert peer['candidate_id']==CID and peer['material_concerns']==[] and peer['source_files_exact9']==prep['source_files']
binding={'schema_version':1,'candidate_id':CID,'experiment_id':EXP,'code_commit':code,'parent_commit':parent,'runtime_expected_commit':parent,
    'candidate_source_hashes':source_hashes,'candidate_config_sha256':prep['source_files'][prep['config']],'source_files':prep['source_files'],
    'original_source_preparation_sha256':sha(SOURCE/'preparation.json'),'source_preparation':ref(SOURCE/'preparation.json'),
    'native_protocol':ref(SOURCE/'native_protocol.md'),'isolated_source_version':ref(proof),'independent_source_review':ref(sourcepeer),
    'scope':'Actual5931 exact-nine child18e source only. Prototype1210 NULL unchanged. Native DRAFTTrue and all10 execution fields NULL; no current operational readiness, native/FP32 result or main/runtime promotion.'}
ag.save(HERE/'source_version_binding.json',binding)
manifest=read(BASE/'manifest_template.json')
manifest.update(candidate_id=CID,experiment_id=EXP,candidate_name=NAME,config=prep['config'],code_commit=code,
    candidate_source_hashes=source_hashes,candidate_config_sha256=prep['source_files'][prep['config']],source_preparation_sha256=sha(SOURCE/'preparation.json'),
    source_version_commit=code,source_parent_commit=parent,future_version_parent=parent,runtime_expected_commit=parent,base_reference_commit=parent,
    source_version_binding_sha256=sha(HERE/'source_version_binding.json'),draft_execution_disabled=True,scientific_admission=False,
    protocol='Original60d07 LFT: native paired naturalTRAIN2, all original FFNs/LNs in dynamic common; actual triangular analysis P0/U0/P1/U1, original3 packed FFNs once each, reverse U1/P1/U0/P0 synthesis;8 maps/GELU,4 original means,3original-ID delta scatters/rawskip/HCG/singleinst. Whole NEW4map aggregate weight gradient/update only;individual new map/row/column/bias0 legal. Original resources fullAST. DRAFTTrue/10NULL/nativeNOT_RUN; separately frozen reviewed operational activation/freshowner/idlephysical0/three locks needed.')
diagnostics={'candidate_model/'+name:value for name,value in source_hashes.items()}
diagnostics.update({'candidate.yaml':sha(HERE/'candidate.yaml'),'worker.py':sha(HERE/'worker.py'),'native_runtime.py':sha(HERE/'native_runtime.py'),'source_version_binding.json':sha(HERE/'source_version_binding.json')})
manifest['diagnostic_files']=diagnostics;ag.save(HERE/'manifest_template.json',manifest)
ag.save(HERE/'launcher_plan.json',{'status':'PLAN_ONLY_EXECUTION_DISABLED_NO_RELEASE','candidate_id':CID,'code_commit':code,'runtime_expected_commit':parent,
    'native':'NOT_RUN','resources':'NOT_RUN','requires':'Independent observer review and separately frozen operational activation/release, currentroot-owner/deadline/resources, actual idle selected physicalGPU0 and3locks. Preserve both running original jobs.',
    'four_future_worker_commands':[['python','-B','worker.py','--lease','<fresh_exact_lease>','--mode',mode,'--target',target] for mode in ('smoke','resources') for target in ('champion','candidate')],
    'stage_formula':'lft_<fresh_owner_token8>_gpu0','local_execution_directory':'lft_execution','no_active_manifest_lease_request_result_release':True})
ag.save(HERE/'private_author_guard_record.json',ag.check())
print(json.dumps({'worker_sha256':sha(HERE/'worker.py'),'runtime_sha256':sha(HERE/'native_runtime.py'),'manifest_sha256':sha(HERE/'manifest_template.json')}))
