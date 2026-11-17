"""BEC native packet static/software checks only; no Torch/native/Git/network."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,ast,builtins,hashlib,json,re,runpy,sys,traceback
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_4694ba96/cts_native_prepare'
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_6bdbcf77/new_candidate_prepare'
CHECKS=[]
def check(name,value):
 CHECKS.append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def funcs(tree):return {n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
def dump(node):return ast.dump(node,include_attributes=False)
def run():
 worker=(HERE/'worker.py').read_text();runtime=(HERE/'native_runtime.py').read_text();wt=ast.parse(worker);rt=ast.parse(runtime);wf=funcs(wt);rf=funcs(rt)
 previous_worker=(ORIGIN/'worker.py').read_text();pwf=funcs(ast.parse(previous_worker));prf=funcs(ast.parse((ORIGIN/'native_runtime.py').read_text()))
 paths=sorted(HERE.rglob('*.py'))
 for p in paths:compile(p.read_text(),str(p),'exec')
 check('all_actual_Python_files_syntax_compile',len(paths)>=13)
 check('whole_original_resources_AST_unchanged',dump(wf['resources'])==dump(pwf['resources']))
 resource_sha=hashlib.sha256(dump(wf['resources']).encode()).hexdigest()
 check('historical_resource_AST_SHA28185',resource_sha=='28185afffac5b63f5d71ac9cdb1d1481b73e1aceace1a07ae78944499ed552e0')
 oldsetup=ast.get_source_segment(previous_worker,pwf['setup']).replace('CTS','BEC').replace('cts-','bec-')
 oldsetup=oldsetup.replace("excluded = ('dec.cluster_att.cluster_ffn.1.', 'dec.cluster_att.middle_triad.')","excluded = ('dec.cluster_att.cluster_ffn.0.', 'dec.cluster_att.cluster_ffn.1.', 'dec.cluster_att.bipartite_edges.')")
 oldsetup=oldsetup.replace('exclude exact replaced-middle and new-triadic prefixes on both targets; retain middle LayerNorm','exclude exact replaced fine/middle FFN and new bipartite_edges prefixes on both targets; retain all three original LayerNorms and coarse FFN; derive actual names/counts, no fixed843')
 check('native_setup_only_identity_and_precise_common_scope_change',dump(wf['setup'])==dump(funcs(ast.parse(oldsetup))['setup']))
 check('native_main_original_acquire_train_resources_finally_AST',dump(wf['main'])==dump(funcs(ast.parse(ast.get_source_segment(previous_worker,pwf['main']).replace('CTS','BEC')))['main']))
 for name in ('sha','verify','observe','acquire','release','fingerprint','save'):
  check('original_runtime_guard_'+name+'_AST',dump(rf[name])==dump(prf[name]))
 check('original_null_version_guard_AST_with_identity_message_only',dump(rf['require_promoted_version'])==dump(funcs(ast.parse(ast.get_source_segment((ORIGIN/'native_runtime.py').read_text(),prf['require_promoted_version']).replace('CTS','BEC')))['require_promoted_version']))
 m=json.loads((HERE/'manifest_template.json').read_text());v=json.loads((HERE/'source_version_binding.json').read_text());source=json.loads((SOURCE/'preparation.json').read_text())
 check('frozen_BEC_source_preparation2d06',sha(SOURCE/'preparation.json')=='2d0606030583fd29719a39a114e11c1c31f44b63ca0fa2cff849baf40e7ca14d')
 for name,h in m['candidate_source_hashes'].items():check('exact_frozen_model_copy_'+name,sha(HERE/'candidate_model'/name)==h==sha(SOURCE/'staged_repository/framework/model/Quard_model'/source['model_name']/name))
 check('exact_eight_independent_source_files',len(m['candidate_source_hashes'])==8 and 'bipartite_edges.py' in m['candidate_source_hashes'])
 check('original_native_YAML_exact_bytes',sha(HERE/'candidate.yaml')==m['candidate_config_sha256']=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a')
 check('frozen_BEC_protocol6555_exact',sha(HERE/'native_protocol.md')==sha(SOURCE/'native_protocol.md')=='655591ddcdb017461884381fb27d006e9ba3062f530b9bb6f44dc7dc85466a10')
 check('exact_null_commit_parent_future_version',all(m[k] is None for k in ('code_commit','source_version_commit','source_parent_commit','future_version_parent')) and all(v[k] is None for k in ('code_commit','parent_commit','future_version_parent','isolated_source_version')))
 active=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')
 check('ten_execution_fields_all_null',all(m[k] is None for k in active))
 check('runtime_draft_true_and_null_candidate_parent_constants','DRAFT_EXECUTION_DISABLED = True' in runtime and 'CANDIDATE_COMMIT = None' in runtime and 'SOURCE_PARENT_COMMIT = None' in runtime)
 check('base_reference48fc_not_a_chosen_version_parent',m['base_reference_commit']=='48fc302c3c02ffef0b241be3593c386b6b65a72e' and m['future_version_parent'] is None)
 check('source_path_hash_dictionary_exact9',v['source_files']=={x['path']:x['sha256'] for x in source['source_files']} and len(v['source_files'])==9)
 check('twelve_diagnostic_hashes_exact',len(m['diagnostic_files'])==12 and all(sha(HERE/n)==h for n,h in m['diagnostic_files'].items()))
 check('source_version_binding_hash_exact',sha(HERE/'source_version_binding.json')==m['source_version_binding_sha256'])
 check('BEC_runtime_identity_stage_namespace',"'M215-BEC'" in runtime and "'bec_'" in runtime and "'_bec'" in runtime and 'hierarchy-cross-level-bipartite-edge-composition' in runtime)
 check('no_old_CTS_mechanism_or_BFC_gate_in_worker',all(x not in worker for x in ('middle_triad','triadic_calls','actual_three_distinct','nonpower2','native_output_half','BFC')))
 smoke=wf['smoke'];nested={n.name:n for n in ast.walk(smoke) if isinstance(n,ast.FunctionDef)}
 previous_nested={n.name:n for n in ast.walk(pwf['smoke']) if isinstance(n,ast.FunctionDef)}
 for name in ('observed_csort','last_encoder_pre','attention_post','ila_pre','last_encoder_post','decoder_post'):
  check('original_raw_CSORT_inst_path_'+name+'_AST',dump(nested[name])==dump(previous_nested[name]))
 check('original_TwoNativeBatches_AST',dump(next(n for n in ast.walk(smoke) if isinstance(n,ast.ClassDef) and n.name=='TwoNativeBatches'))==dump(next(n for n in ast.walk(pwf['smoke']) if isinstance(n,ast.ClassDef) and n.name=='TwoNativeBatches')))
 check('original_train_loop_exhaustion_not_exception_stop','train.train(1,model,TwoNativeBatches(loader),optimizer,scheduler,cfg,logger,writer)' in worker and 'raise Stop' not in worker)
 check('mean_original_called_once_and_returned_unchanged',sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='original_mean' for n in ast.walk(nested['observed_mean']))==1 and ast.unparse(nested['observed_mean']).rstrip().endswith('return output'))
 check('observer_does_not_recompute_numerical_means',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='mean' for n in ast.walk(nested['observed_mean'])))
 check('no_aux_autograd_or_backward','autograd.grad(' not in worker and '.backward(' not in worker)
 rawsource=ast.get_source_segment(worker,nested['observed_build']);presource=ast.get_source_segment(worker,nested['bec_pre'])
 check('raw_build_core_preflight_before_original_FFN_watch','bec_core_preflight' in rawsource and 'INCONCLUSIVE_ORIGINAL_BATCH_LACKS_BEC_CORE_EDGES' in rawsource)
 check('bec_pre_inconclusive_before_context_or_watch',presource.index('if not coverage')<presource.index("state['bec_context']")<presource.index('watch(value'))
 check('one_child_and_degree_boundary_not_extra_hard_gate','core_path_possible' in dump(wf['bec_core_preflight']) and 'degree>=2/singleton/empty/padding is NOT_EXERCISED' in dump(wf['bec_core_preflight']))
 check('aggregate12_param_blocks_and_actual_update','assert len(result_blocks) == 12' in ast.unparse(nested['parameter_blocks']) and 'native_parameter_block_gradients' in dump(nested['before_step']) and 'parameter_block_after_step_hash' in dump(nested['after_step']))
 check('FFN_individual_call_zero_legal',"for key in ('native_input_gradients','native_output_gradients'):assert record.get(key) and all(g['finite'] for g in record[key])" in worker)
 check('operator_individual_call_zero_legal',"all(g['finite'] for g in call[key])" in worker and "g['abs_max']>0 for g in call[key]" not in worker)
 check('U_V_split_gradient_readouts_recorded_and_finite','native_split_output_gradients' in dump(nested['activation_post']) and "x['retained']['finite'] and x['upward']['finite']" in worker)
 check('original_three_skip_helper_to_HCG_checks','BEC_original_three_skip_HCG_inputs' in worker and 'BEC_helper_coarse_object_exact' in worker)
 check('method_global_hook_finally_restoration','for owner,name,original in reversed(global_replacements)' in worker and 'for owner,name in reversed(replacements)' in worker and 'for hook in hooks:hook.remove()' in worker)
 check('smoke_peak_limits_and_pairing_unknown','not pure TRAIN memory' in worker and 'UNKNOWN; no separate no-observer native TRAIN process pair' in worker and 'NOT_VALIDATED_BY_SINGLE_TARGET_WORKER' in worker)
 fixture=json.loads((HERE/'observer_fixture_run1.json').read_text())
 check('actual36_software_observer_fixture_proof_matches_current_worker',fixture['status']=='SOFTWARE_OBSERVER_FIXTURES_PASSED_NATIVE_NOT_RUN' and fixture['check_count']==36 and fixture['worker_sha256']==sha(HERE/'worker.py'))
 check('software_fixture_reports_no_native_gradients',fixture['observations']['gradient_callbacks_and_optimizer_steps']=='NOT_EXECUTED' and len(fixture['observations']['runs'])==4)
 # Actual version-guard function is exercised only in isolated in-memory globals.
 module=ast.Module(body=[rf['require_promoted_version']],type_ignores=[]);scope={'re':re,'SOURCE_PREPARATION_SHA256':m['source_preparation_sha256']}
 exec(compile(module,'<actual-null-version-guard>','exec'),scope)
 for draft,commit,parent in ((True,None,None),(False,None,None),(False,'a'*40,None),(False,None,'b'*40)):
  scope.update(DRAFT_EXECUTION_DISABLED=draft,CANDIDATE_COMMIT=commit,SOURCE_PARENT_COMMIT=parent)
  try:scope['require_promoted_version']()
  except RuntimeError:pass
  else:raise AssertionError('Unbound version accepted')
 check('four_actual_in_memory_disabled_missing_version_refusals',True)
 # Real local module entry attempts, before fcntl/manifest/Torch. No subprocess.
 events=[];original_import=builtins.__import__
 def guarded_import(name,*args,**kwargs):
  if name.split('.')[0] in ('torch','fcntl','pynvml','gorilla','numpy','yaml'):
   events.append({'forbidden_import':name});raise AssertionError(name)
  return original_import(name,*args,**kwargs)
 def audit(event,args):
  if event in ('subprocess.Popen','socket.connect','socket.bind'):
   events.append({'forbidden_event':event});raise AssertionError(event)
  if event=='open' and ('native_manifest.json' in str(args[0]) or 'execution_lease' in str(args[0])):
   events.append({'forbidden_execution_file':str(args[0])});raise AssertionError(str(args[0]))
 sys.addaudithook(audit);builtins.__import__=guarded_import;sys.path.insert(0,str(HERE));entries=[]
 try:
  for name in ('native_runtime.py','worker.py'):
   try:runpy.run_path(str(HERE/name),run_name='__main__')
   except RuntimeError as exc:message=str(exc)
   else:raise AssertionError('Disabled entry accepted')
   assert message=='BEC native preparation is execution-disabled; a fresh reviewed operational bundle and lease are required'
   entries.append({'entry':name,'refused_before_manifest_fcntl_Torch':True,'message':message})
 finally:builtins.__import__=original_import;sys.path.remove(str(HERE))
 check('two_actual_local_disabled_entries_before_execution_files_or_native_imports',len(entries)==2 and events==[])
 check('no_Torch_import_or_actual_execution_materials','torch' not in sys.modules and all(not (HERE/n).exists() for n in ('native_manifest.json','execution_binding.json','execution_lease.json','adapter_release.json')))
 return {'compiled_python_files':[p.relative_to(HERE).as_posix() for p in paths],'resource_AST_sha256':resource_sha,'local_disabled_entry_refusals':entries,
  'forbidden_events':events,'in_memory_invalid_version_cases':4,'observer_software_fixture':{'path':'observer_fixture_run1.json','sha256':sha(HERE/'observer_fixture_run1.json')},'native_gradient_or_optimizer_execution':'NOT_RUN'}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',default='static_validation.json');args=parser.parse_args();p=HERE/args.output;assert p.parent==HERE and not p.exists(),'Preserve previous proof'
 result={'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':'hierarchy-cross-level-bipartite-edge-composition','experiment_id':'M215-BEC',
  'status':'PENDING','checks':CHECKS,'worker_sha256':sha(HERE/'worker.py'),'runtime_sha256':sha(HERE/'native_runtime.py'),'static_check_sha256':sha(Path(__file__)),
  'code_commit':None,'source_parent_commit':None,'native':'NOT_RUN','resources':'NOT_RUN','transport':'NOT_RUN','Torch':'NOT_IMPORTED'}
 try:result['observations']=run();result['status']='STATIC_SOFTWARE_NATIVE_PREPARATION_CHECKS_PASSED_NATIVE_NOT_RUN'
 except Exception as exc:result.update(status='STATIC_PREPARATION_CHECK_FAILED_NOT_NATIVE',error=str(exc),traceback=traceback.format_exc())
 result['check_count']=len(CHECKS);result['failed_checks']=[c for c in CHECKS if not c['passed']]
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({'status':result['status'],'checks':len(CHECKS),'sha256':sha(p)}));return int(result['status']=='STATIC_PREPARATION_CHECK_FAILED_NOT_NATIVE')
if __name__=='__main__':raise SystemExit(main())
