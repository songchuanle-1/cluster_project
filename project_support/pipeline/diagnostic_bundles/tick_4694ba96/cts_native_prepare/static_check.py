"""CTS native preparation: actual stdlib/AST/refusal checks, not native execution."""
from pathlib import Path
import argparse,ast,hashlib,json,math,subprocess,sys,traceback
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REFERENCE=ROOT/'pipeline/diagnostic_bundles/tick_ab7e46d4/bfc_native_prepare'
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_3824d9c9/new_candidate_prepare'
checks=[]
def check(name,condition):
    checks.append({'name':name,'passed':bool(condition)})
    if not condition:raise AssertionError(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def functions(tree):return {n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def dump(node):return ast.dump(node,include_attributes=False)
def extract(nodes,names,namespace=None):
    scope={} if namespace is None else namespace
    module=ast.Module(body=[nodes[n] for n in names],type_ignores=[])
    exec(compile(ast.fix_missing_locations(module),'<actual-extracted-production-functions>','exec'),scope)
    return scope

def run():
    worker=(HERE/'worker.py').read_text();runtime=(HERE/'native_runtime.py').read_text()
    wt=ast.parse(worker);rt=ast.parse(runtime);wf=functions(wt);rf=functions(rt)
    baseworker=(REFERENCE/'worker.py').read_text();basert=ast.parse((REFERENCE/'native_runtime.py').read_text());brf=functions(basert)
    compiled=[]
    for p in sorted(HERE.rglob('*.py')):
        compile(p.read_text(),str(p),'exec');compiled.append(str(p.relative_to(HERE)))
    check('all_actual_python_sources_compile_without_import',len(compiled)>=13)
    check('original_resources_whole_AST_unchanged',dump(wf['resources'])==dump(functions(ast.parse(baseworker))['resources']))
    resource_ast_sha=hashlib.sha256(dump(wf['resources']).encode()).hexdigest()
    check('resources_AST_original_historical_SHA',resource_ast_sha=='28185afffac5b63f5d71ac9cdb1d1481b73e1aceace1a07ae78944499ed552e0')
    renamed=baseworker.replace('middle_butterfly','middle_triad').replace('butterfly','triadic').replace('BFC','CTS').replace('_bfc','_cts')
    check('native_setup_namespace_only_AST',dump(wf['setup'])==dump(functions(ast.parse(renamed))['setup']))
    for name in ('sha','verify','observe','acquire','release','fingerprint','save'):
        check('runtime_original_guard_'+name+'_AST_unchanged',dump(rf[name])==dump(brf[name]))
    source=json.loads((SOURCE/'preparation.json').read_text())
    m=json.loads((HERE/'manifest_template.json').read_text());v=json.loads((HERE/'source_version_binding.json').read_text())
    check('frozen_source_preparation_exact',sha(SOURCE/'preparation.json')=='bfab01a31a0fc7a0d679156d5e0e6fcfa987e56e5f3bb1bdf6bded9e2208f76e')
    for name,h in m['candidate_source_hashes'].items():
        check('source_byte_copy_'+name,sha(HERE/'candidate_model'/name)==h==sha(SOURCE/'staged_repository/framework/model/Quard_model'/source['model_name']/name))
    check('eight_independent_CTS_source_files',len(m['candidate_source_hashes'])==8 and 'middle_triad.py' in m['candidate_source_hashes'])
    check('original_native_YAML_exact',sha(HERE/'candidate.yaml')==m['candidate_config_sha256']=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a')
    for k in ('code_commit','source_version_commit','source_parent_commit','future_version_parent'):check('manifest_unbound_'+k,m[k] is None)
    active=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')
    check('all_ten_execution_fields_null',all(m[k] is None for k in active))
    check('source_version_parent_and_commit_null',v['code_commit'] is None and v['parent_commit'] is None and v['future_version_parent'] is None and v['isolated_source_version'] is None)
    check('source_version_nine_path_hash_dictionary',isinstance(v['source_files'],dict) and v['source_files']=={row['path']:row['sha256'] for row in source['source_files']})
    check('source_version_binding_manifest_hash_chain',sha(HERE/'source_version_binding.json')==m['source_version_binding_sha256'])
    check('no_BFC_version_substitution','48fc302c' not in runtime and '48fc302c' not in json.dumps(m)+json.dumps(v))
    check('base_reference_not_future_parent',m['base_reference_commit']=='11a811618179ab1ddc0cee299194667413b7fdb9' and v['future_version_parent'] is None)
    check('template_disabled',m['draft_execution_disabled'] is True)
    check('all_twelve_diagnostic_hashes',len(m['diagnostic_files'])==12 and all(sha(HERE/n)==h for n,h in m['diagnostic_files'].items()))
    scope=extract(rf,['require_promoted_version'],{'re':__import__('re'),'DRAFT_EXECUTION_DISABLED':True,'CANDIDATE_COMMIT':None,'SOURCE_PARENT_COMMIT':None,'SOURCE_PREPARATION_SHA256':m['source_preparation_sha256']})
    variants=[(True,None,None),(False,None,None),(False,'a'*40,None),(False,None,'b'*40)]
    for i,(draft,commit,parent) in enumerate(variants):
        scope.update(DRAFT_EXECUTION_DISABLED=draft,CANDIDATE_COMMIT=commit,SOURCE_PARENT_COMMIT=parent)
        try:scope['require_promoted_version']()
        except RuntimeError:pass
        else:raise AssertionError('Invalid unbound runtime accepted')
    check('draft_and_null_commit_parent_refuse_in_memory',len(variants)==4)
    initial_call=next(n.lineno for n in rt.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='require_promoted_version')
    fcntl_line=next(n.lineno for n in rt.body if isinstance(n,ast.Import) and n.names[0].name=='fcntl')
    manifest_line=next(n.lineno for n in rt.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MANIFEST' for t in n.targets))
    check('initial_refusal_precedes_fcntl_and_manifest',initial_call<fcntl_line<manifest_line)
    plans=extract(functions(ast.parse((HERE/'candidate_model/middle_triad.py').read_text())),['build_triadic_plan'],{'math':math})
    observers=extract(wf,['triadic_plan_observation','triadic_coverage_preflight'])
    build=plans['build_triadic_plan'];describe=observers['triadic_plan_observation'];preflight=observers['triadic_coverage_preflight']
    observed_cases=[]
    for n in range(129):
        plan=build([(float(i),0.,0.) for i in range(n)],[7]*n,[True]*n,n)
        groups,stages=describe(plan)
        round_stages=[s for s in stages if s['kind']=='round'];rows=sum(len(s['own_ids']) for s in round_stages)
        expected_rounds=0;p=1
        while p<n:expected_rounds+=1;p*=3
        assert len(round_stages)==expected_rounds and rows==n*expected_rounds
        assert len([s for s in stages if s['kind']=='singleton'])==int(n==1)
        core=preflight([([7]*n,[True]*n)])
        assert core['three_distinct_real_sources_possible']==(n>=3) and core['multiround_possible']==(n>=4) and core['dilation_r_ge1_possible']==(n>=4)
        assert sum(s['three_distinct_real_input_rows'] for s in round_stages)>0 if n>=3 else sum(s['three_distinct_real_input_rows'] for s in round_stages)==0
        observed_cases.append({'n':n,'rounds':expected_rounds,'rows':rows})
    check('actual_production_plan_to_new_observer_n0_to128',len(observed_cases)==129)
    special=[([],[],[]),([(0.,0.,0.)]*6,[0]*6,[True]*6),([(0.,0.,0.)]*9,[3,3,4,3,4,7,3,4,7],[True,False,True,True,True,False,True,False,True])]
    for coords,parents,support in special:
        p=build(coords,parents,support,len(parents));groups,stages=describe(p)
        assert {x for g in groups for x in g['order']}=={i for i,v in enumerate(support) if v}
        for s in stages:
            if s['kind']=='round':
                assert len(s['own_ids'])==len(set(s['own_ids']))
                assert all(len([x for x in row[2:] if x is not None])==len(set(x for x in row[2:] if x is not None)) for row in s['rows'])
    six=describe(build([(float(i),0.,0.) for i in range(6)],[0]*6,[True]*6,6))[1]
    check('n6_later_alias_legal_separate_from_three_distinct',six[0]['three_distinct_real_input_rows']==6 and six[1]['three_distinct_real_input_rows']==0 and six[1]['aliased_negative_zero_rows']==6)
    check('hole_ties_empty_parent_observer_mapping',len(special)==3)
    all_empty=preflight([([0,0],[False,False]),([],[])])
    check('all_empty_preflight_inconclusive',all_empty['true_supported_tokens']==0 and not any(all_empty[k] for k in ('three_distinct_real_sources_possible','multiround_possible','dilation_r_ge1_possible')))
    nested={n.name:n for n in ast.walk(wf['smoke']) if isinstance(n,ast.FunctionDef)}
    obuild=dump(nested['observed_build']);pre=dump(nested['triadic_pre']);post=dump(nested['triadic_post'])
    check('raw_build_preflight_before_original_FFN_hooks','triadic_coverage_preflight' in obuild and 'INCONCLUSIVE_ORIGINAL_BATCH' in obuild)
    check('triadic_pre_coverage_before_input_watch',pre.index('triadic_coverage_preflight')<pre.index("id='watch'"))
    check('output_coverage_before_requires_grad_watch',post.index('INCONCLUSIVE_COVERAGE')<post.index("id='watch'"))
    check('exact_three_W_column_blocks',"'own_input': (weight, 0, c, 0, c)" in ast.unparse(nested['parameter_blocks']) and "'positive_input': (weight, 0, c, c, 2 * c)" in ast.unparse(nested['parameter_blocks']) and "'negative_input': (weight, 0, c, 2 * c, 3 * c)" in ast.unparse(nested['parameter_blocks']))
    check('block_gradients_original_optimizer_pre_hook','native_parameter_block_gradients' in dump(nested['before_step']) and 'parameter_block_after_step_hash' in dump(nested['after_step']))
    check('no_BFC_nonpower_half_quadrant_gate',all(word not in worker.lower() for word in ('nonpower','quadrant','output_half','both_halves','butterfly')))
    check('no_auxiliary_autograd_backward_probe','autograd.grad(' not in worker and 'probe.backward(' not in worker)
    check('native_train_call_and_normal_two_batch_exhaustion','yield from itertools.islice(iter(self.native),2)' in worker and 'train.train(1,model,TwoNativeBatches(loader),optimizer,scheduler,cfg,logger,writer)' in worker)
    check('smoke_memory_and_single_target_limits_honest','not pure TRAIN memory' in worker and 'NOT_VALIDATED_BY_SINGLE_TARGET_WORKER' in worker)
    entries=[]
    for name in ('native_runtime.py','worker.py'):
        completed=subprocess.run([sys.executable,'-B','-X','utf8',str(HERE/'refusal_probe.py'),name],capture_output=True,text=True,encoding='utf-8',timeout=20)
        assert completed.returncode==0,(name,completed.stdout,completed.stderr)
        value=json.loads(completed.stdout);assert value['refused'] and value['forbidden_events']==[] and value['torch_imported'] is False;entries.append(value)
    check('two_actual_local_disabled_entry_refusals_before_native_imports',len(entries)==2)
    check('no_actual_execution_materials',all(not (HERE/name).exists() for name in ('native_manifest.json','execution_binding.json','execution_lease.json','adapter_release.json')))
    check('checker_never_imported_torch','torch' not in sys.modules)
    return {'compiled_python_files':compiled,'production_observer_cases':observed_cases,'special_observer_cases':len(special),
      'local_disabled_entry_observations':entries,'resources_AST_SHA256':resource_ast_sha,'runtime_invalid_guard_variants':len(variants)}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='static_validation.json');args=parser.parse_args()
    out=HERE/args.output
    assert out.parent==HERE and not out.exists(),'Preserve prior proof; choose a new output filename'
    value={'schema_version':1,'candidate_id':'hierarchy-parent-cyclic-triadic-state-composition','experiment_id':'M214-CTS',
      'checked_at':datetime.now(timezone.utc).isoformat(),'scope':'STDLIB_STATIC_OBSERVER_AND_DISABLED_ENTRY_ONLY',
      'native':'NOT_RUN','resources':'NOT_RUN','Torch':'NOT_IMPORTED','transport':'NOT_RUN','code_commit':None,'source_parent_commit':None,
      'worker_sha256':sha(HERE/'worker.py'),'runtime_sha256':sha(HERE/'native_runtime.py'),'static_check_sha256':sha(Path(__file__)),'checks':checks}
    try:value['observations']=run();value['status']='STATIC_CHECKS_PASSED_NATIVE_NOT_RUN'
    except Exception as exc:value.update(status='STATIC_CHECK_FAILED_NOT_NATIVE',error=str(exc),traceback=traceback.format_exc())
    value['check_count']=len(checks);value['failed_checks']=[v for v in checks if not v['passed']]
    with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps({'status':value['status'],'checks':len(checks),'result':str(out),'sha256':sha(out)}))
    return 0 if value['status']=='STATIC_CHECKS_PASSED_NATIVE_NOT_RUN' else 1
if __name__=='__main__':raise SystemExit(main())
