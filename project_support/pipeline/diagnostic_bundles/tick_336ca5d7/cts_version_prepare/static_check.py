"""Pure stdlib checks of the disabled CTS source-save draft; no Git or writes outside proof."""
from pathlib import Path
import argparse,ast,contextlib,hashlib,io,json,re,runpy,sys
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
checks=[];events=[]
def check(name,value):
    checks.append({'name':name,'passed':bool(value)})
    if not value:raise AssertionError(name)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def audit(event,args):
    if event in ('subprocess.Popen','socket.connect','socket.bind'):
        events.append(event);raise AssertionError('No actual Git/process/network allowed')
sys.addaudithook(audit)
def run():
    p=HERE/'prepare_isolated_cts_version.py';text=p.read_text();tree=ast.parse(text);compile(text,str(p),'exec')
    check('actual_helper_syntax_compile',True)
    scope=runpy.run_path(str(p),run_name='cts_disabled_static_only')
    check('disabled_default_constant',scope['DRAFT_EXECUTION_ENABLED'] is False)
    sentinel=[]
    def forbidden(*args,**kwargs):sentinel.append((args,kwargs));raise AssertionError('Actual operation reached')
    scope['execute']=forbidden
    # Functions retain runpy globals, so patch the actual main globals explicitly.
    main=scope['main'];g=main.__globals__;original_execute=g['execute'];g['execute']=forbidden
    stdout=io.StringIO()
    with contextlib.redirect_stdout(stdout):value=main([])
    check('actual_main_default_no_Git_no_writes',value==0 and stdout.getvalue().strip()=='DRAFT_DISABLED_NO_GIT_WORKTREE_OR_SOURCE_WRITE' and not sentinel)
    try:main(['--execute-root'])
    except RuntimeError as exc:message=str(exc)
    else:raise AssertionError('Disabled root entry accepted')
    check('actual_main_execute_flag_still_disabled',message.startswith('Draft is execution-disabled') and not sentinel)
    variants=[None,'','a'*63,'g'*64,'../outside','a'*65]
    g['DRAFT_EXECUTION_ENABLED']=True
    for value in variants:
        args=['--execute-root']+([] if value is None else ['--bfc-admission-sha',value])
        try:main(args)
        except RuntimeError as exc:assert 'Actual formal BFC admission SHA required' in str(exc)
        else:raise AssertionError('Invalid SHA accepted')
    g['DRAFT_EXECUTION_ENABLED']=False;g['execute']=original_execute
    check('six_actual_invalid_admission_parameter_refusals',len(variants)==6 and not sentinel)
    funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    dump=lambda n:ast.dump(n,include_attributes=False)
    check('fixed_actual_parent48fc_not_reference11a',scope['BASE']==scope['PRIMARY']=='48fc302c3c02ffef0b241be3593c386b6b65a72e' and scope['SOURCE_REFERENCE']=='11a811618179ab1ddc0cee299194667413b7fdb9')
    expected_keys={'token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256'}
    check('exact_current_owner_six_fields',set(scope['EXPECTED_OWNER'])==expected_keys and scope['EXPECTED_OWNER']['token']=='336ca5d7348b4018b7fd8b9e41f6eee3')
    own=dump(funcs['owner_guard'])
    check('actual_thread_mode_original_deadline_context_pending_guard',all(t in own for t in ('CODEX_THREAD_ID','foreground','.tick_context.json','.tick_context_state.next.json','deadline_at')))
    snapshot=dump(funcs['primary_snapshot'])
    check('baseline28_status_bytes_empty_index_and_indexfile_SHA',all(t in snapshot for t in ('protected_existing_worktree','status_hex','index_sha256','protected_files','--cached','--name-only')))
    gate=funcs['bfc_tested_primary_gate'];gd=dump(gate)
    check('actual_current_tick_canonical_admission_and_four_review_gate',all(t in gd for t in ('admission','independent_review','raw_results','CURRENT_TICK','execution_sha256','created_at')))
    check('actual_primary_exact_commit_parent_and_BFC9blob_gate',all(t in gd for t in ('rev-parse','rev-list','diff-tree','show','BASE','SOURCE_REFERENCE')))
    body=funcs['execute'];calls=[n for n in ast.walk(body) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='git']
    commands=[n.args[1].value for n in calls if len(n.args)>1 and isinstance(n.args[1],ast.Constant)]
    check('only_worktree_add_add_commit_mutation_commands',commands.count('worktree')==1 and commands.count('add')==1 and commands.count('commit')==1 and not set(commands)&{'reset','clean','stash','checkout','switch','merge','push','fetch','pull'})
    lines=text.splitlines()
    for literal in ("git(REPO,'worktree','add'","git(DEST,'add'","git(DEST,'commit'"):
        line=next(s for s in lines if literal in s)
        check('immediate_current_protection_guard_before_'+literal.split(',')[1].replace("'",''),'mutation_guard();' in line.split(literal)[0])
    check('source_exact9_prepared_map_and_CTS_namespace_guard',all(t in dump(funcs['source_details']) for t in ('middle_triad.py','source_file_count','prepared_file_hashes','source_commit','future_version_parent')))
    hook_pattern=next(n.value for n in ast.walk(funcs['git_hooks_filters_guard']) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.startswith('^(core'))
    check('hooks_filters_no_network_smudge_command_options','GIT_LFS_SKIP_SMUDGE' in dump(funcs['git']) and 'core.fsmonitor=false' in dump(funcs['git']) and 'core.autocrlf=false' in dump(funcs['git']) and 'core.eol=lf' in dump(funcs['git']) and re.fullmatch(hook_pattern,'core.hooksPath') is not None and re.fullmatch(hook_pattern,'filter.custom.clean') is not None)
    check('thirteen_pipeline_ledger_bytes_frozen',len(scope['PROTECTED_LEDGER_NAMES'])==13 and 'running.json' in scope['PROTECTED_LEDGER_NAMES'] and 'experiments/M206-CGCA.json' in scope['PROTECTED_LEDGER_NAMES'] and 'experiments/M212-BCR.json' in scope['PROTECTED_LEDGER_NAMES'])
    check('no_existing_worktree_or_intent_replay','Previous attempt needs exact reconciliation; do not replay' in text and 'Worktree exists/escapes project' in text)
    check('ordinary_commit_exact_single_child_and_clean_worktree_checks',all(t in dump(body) for t in ('rev-list','diff-tree','committed_blob_sha256','--porcelain=v1')))
    check('source_prep_protocol_and_reviews_actual_frozen_hashes',scope['SOURCE_PREP_SHA']=='bfab01a31a0fc7a0d679156d5e0e6fcfa987e56e5f3bb1bdf6bded9e2208f76e' and scope['NATIVE_PROTOCOL_SHA']=='70363d43bdac998d346cf06c817389267cb69682242430dca8819dd29b0fefdc' and len(scope['REVIEWS'])==2)
    check('no_Torch_or_actual_process_network','torch' not in sys.modules and events==[])
    check('no_actual_version_operation_outputs',all(not (HERE/name).exists() for name in ('isolated_version_before.json','isolated_version_operation_intent.json','isolated_source_version.json')))
    return {'default_stdout':stdout.getvalue(),'disabled_execute_message':message,'invalid_SHA_cases':len(variants),'Git_or_process_network_events':events,
      'actual_operation_branch_calls':sentinel,'helper_sha256':sha(p),'actual_mutation_commands_run':0}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='static_validation_final.json');args=parser.parse_args()
    result={'schema_version':1,'checked_at':datetime.now(timezone.utc).isoformat(),'scope':'STDLIB_AST_DISABLED_AND_INVALID_PARAMETER_REFUSAL_ONLY',
      'candidate_id':'hierarchy-parent-cyclic-triadic-state-composition','experiment_id':'M214-CTS','checks':checks,'Git':'NOT_RUN','SSH':'NOT_RUN','GPU':'NOT_RUN','native':'NOT_RUN','source_commit':None,'helper_sha256':sha(HERE/'prepare_isolated_cts_version.py'),'checker_sha256':sha(Path(__file__))}
    try:result['observations']=run();result['status']='DISABLED_SOURCE_SAVE_DRAFT_CHECKS_PASSED_NO_GIT'
    except Exception as exc:
        import traceback
        result.update(status='DRAFT_STATIC_CHECK_FAILED',error=str(exc),traceback=traceback.format_exc())
    result['check_count']=len(checks);result['failed_checks']=[c for c in checks if not c['passed']]
    p=HERE/args.output
    assert p.parent==HERE and not p.exists(),'Preserve prior report; use a fresh output name'
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'status':result['status'],'checks':len(checks),'sha256':sha(p)}));return int(result['status']=='DRAFT_STATIC_CHECK_FAILED')
if __name__=='__main__':raise SystemExit(main())
