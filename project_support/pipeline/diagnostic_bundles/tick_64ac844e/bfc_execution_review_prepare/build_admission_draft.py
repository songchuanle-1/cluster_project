"""Local authoring port of the reviewed root-only BCR admission envelope."""
from pathlib import Path
import ast

HERE=Path(__file__).resolve().parent
ORIGIN=HERE.parents[1]/'manual_gpu1_20261025/bcr_execution_review_prepare'
old=(ORIGIN/'admit_bcr_with_history_draft.py').read_text(encoding='utf-8')
old=old.replace('BCR','BFC').replace('bcr','bfc').replace('M212','M213').replace('11a811618179ab1ddc0cee299194667413b7fdb9','48fc302c3c02ffef0b241be3593c386b6b65a72e').replace('hierarchy-parent-bidirectional-complement-recurrence','hierarchy-parent-butterfly-token-composition')
old=old.replace("tick_7526f819", "tick_64ac844e").replace("7526f819f16e4f688566119d347cd198", "64ac844e35434422a64b1eea3d01cfa8")
old=old.replace("EXECUTION = TICK/'bfc_gpu1_execution'", "EXECUTION = TICK/'bfc_execution'")
old=old.replace("REVIEW = HERE/'actual_four_result_review.json'", "REVIEW = None  # Must be supplied as a real actual-report path; no outcome is prepared.")
old=old.replace("TOKEN = '64ac844e35434422a64b1eea3d01cfa8'", "TOKEN = None  # Set from the actual current root owner after all evidence is supplied.")
old=old.replace("review_bfc_v2.py", "review_bfc.py")


def substitute(name,text):
    global old
    tree=ast.parse(old);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=old.splitlines(keepends=True);old=''.join(lines[:node.lineno-1])+text.strip()+'\n'+''.join(lines[node.end_lineno:])


substitute('current_owner', '''
def current_owner():
    owner = read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    mode = read(ROOT/'pipeline/execution_mode.json')
    require(owner['thread_id'] == mode['target_thread_id'] == os.environ.get('CODEX_THREAD_ID') == THREAD,
            'Actual current root owner/environment/target mismatch; never override the thread')
    require(datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at']), 'Original deadline expired')
    require(sha(ROOT/'pipeline/headless/.tick_context.json') == owner['context_sha256'] and
            sha(ROOT/'pipeline/headless/.tick_context_state.next.json') == owner['pending_sha256'], 'Current context/pending changed')
    require(sha(ROOT/'pipeline/goal.json') == GOAL, 'Goal changed')
    return owner
''')
substitute('operation_history_checks', '''
def operation_history_checks():
    history_path=TICK/'bfc_native_operation_history.json';status_path=TICK/'bfc_status_after_four.json'
    history=read(history_path);status=read(status_path);binding=read(EXECUTION/'execution_binding.json')
    gpu=binding['physical_gpu'];require(type(gpu) is int and gpu in UUIDS and binding['gpu_uuid']==UUIDS[gpu],'Selected original GPU/UUID invalid')
    require(history['candidate_id']==CID and history['code_commit']==COMMIT and history['physical_gpu']==gpu and history['gpu_uuid']==UUIDS[gpu],'Actual operation history identity/GPU mismatch')
    require(history['token']==binding['owner']['token'] and history['workers_after']==[] and history['selected_gpu_contexts_after']==[],'Actual operation history is not terminal/empty')
    require(history['status_evidence']==ref(status_path) and status['binding']==binding,'Actual status source/hash/binding mismatch')
    spec=importlib.util.spec_from_file_location('actual_bfc_operation_history',HERE/'bfc_operation_history.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    console,bound,records,reconcile_refs=module.validate(TICK,EXECUTION)
    require(bound==binding and history['same_original_requests_reconciled_read_only']==records and history['original_status_console']==ref(console) and history['reconcile_console_evidence']==reconcile_refs,'Actual full original status/reconcile objects no longer match history')
    require(status_path.read_bytes()==Path(console).read_bytes(),'Saved status differs byte-for-byte from actual root console')
    return [ref(status_path),ref(history_path),ref(console),*reconcile_refs,ref(HERE/'bfc_operation_history.py')]
''')
substitute('actual_checks', '''
def actual_checks(independent_path, independent_sha):
    global TOKEN
    owner=current_owner();TOKEN=owner['token']
    require(isinstance(REVIEW_SHA,str) and len(REVIEW_SHA)==64 and isinstance(REVIEWER_SHA,str) and len(REVIEWER_SHA)==64 and REVIEW is not None,'Actual local report/checker SHA/path must be explicitly bound; draft cannot assume results')
    require(sha(ROOT/GPU1_GRANT['path'])==GPU1_GRANT['sha256'],'Exact explicit resource grant missing/changed')
    require(sha(REVIEW)==REVIEW_SHA and sha(HERE/'review_bfc.py')==REVIEWER_SHA,'Actual semantic review/checker changed')
    independent_path=Path(independent_path).resolve()
    require(independent_path.is_relative_to(ROOT) and sha(independent_path)==independent_sha,'Independent review path/SHA mismatch')
    independent=read(independent_path)
    require(independent['status']==EXPECTED_INDEPENDENT_STATUS and independent['material_concerns']==[],'Independent semantics/resource review did not pass')
    require((independent['candidate_id'],independent['code_commit'],independent['goal_sha256'])==(CID,COMMIT,GOAL),'Independent review identity mismatch')
    for mode,target in PAIRS:
        matches=[x for x in independent['raw_results'] if x['mode']==mode and x['target']==target];require(len(matches)==1,'Independent raw arm missing/ambiguous')
        item=matches[0];expected=EXECUTION/(mode+'_'+target+'_execution.json')
        require((ROOT/item['execution_path']).resolve()==expected.resolve() and sha(expected)==item['execution_sha256'],'Independent raw artifact drift')
        envelope=read(expected)
        require(item['result_sha256']==envelope['result_sha256'] and item['request_id']==envelope['identity']['request_id'],'Independent original request/result mismatch')
    spec=importlib.util.spec_from_file_location('actual_bfc_semantics',HERE/'review_bfc.py')
    reviewer=importlib.util.module_from_spec(spec);spec.loader.exec_module(reviewer)
    fresh=reviewer.review_directory(ROOT,EXECUTION);reviewed=read(REVIEW)
    require(fresh['review_status']==reviewed['review_status']=='RAW_SEMANTICS_VALIDATED_NOT_ADMISSION' and fresh['observations']==reviewed['observations'],'Current actual semantics differ from hash-bound report')
    require(reviewed['standard_PASS_receipt_queue_written'] is False and reviewed['candidate_id']==CID and reviewed['code_commit']==COMMIT,'Local report identity or no-write boundary differs')
    require(fresh['observations']['existing_memory_condition_needs_separate_retention_decision'] is False,'Original memory-retention condition needs a separate real decision')
    binding=read(EXECUTION/'execution_binding.json');manifest=read(EXECUTION/'native_manifest.json')
    keys={'token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256'}
    require(set(binding['owner'])==keys and binding['owner']=={k:owner[k] for k in keys},'Original six-field binding is not actual current owner; no historical lease replay')
    gpu=binding['physical_gpu'];require(type(gpu) is int and gpu in UUIDS and binding['gpu_uuid']==UUIDS[gpu],'Wrong selected original GPU')
    source_checks(manifest)
    policy=read(ROOT/'pipeline/closure_policy.json');auth=policy['experiment_first']['authorization']
    require(policy['enabled'] is True and policy['experiment_first']['enabled'] is True and auth==EXPECTED_AUTHORIZATION and sha(ROOT/auth['path'])==auth['sha256'],'Current experiment-first authorization changed')
    import yaml
    server=yaml.safe_load((ROOT/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']['server-4']
    require(gpu in server['allowed_gpus'] and server['max_tasks_per_gpu']==1 and server['dispatch_enabled'] is True and server['host']=='192.168.1.115' and server['expected_hostname']=='dl04-MS-7E06','Current selected-card eligibility changed')
    require(str(server['expected_gpu_uuids'].get(gpu,server['expected_gpu_uuids'].get(str(gpu))))==UUIDS[gpu],'Selected-card UUID changed')
    operation_history_checks()
    return owner,fresh,manifest,auth
''')
old=old.replace("global REVIEW_SHA, REVIEWER_SHA", "global REVIEW_SHA, REVIEWER_SHA, REVIEW, EXECUTION, TICK")
old=old.replace("parser.add_argument('--local-review-sha',required=True)", "parser.add_argument('--execution-dir',default=str(EXECUTION))\n    parser.add_argument('--local-review',required=True)\n    parser.add_argument('--local-review-sha',required=True)")
old=old.replace("REVIEW_SHA,REVIEWER_SHA=args.local_review_sha,args.reviewer_sha", "REVIEW_SHA,REVIEWER_SHA=args.local_review_sha,args.reviewer_sha\n    EXECUTION=Path(args.execution_dir).resolve();TICK=EXECUTION.parent;REVIEW=Path(args.local_review).resolve()\n    require(EXECUTION.name=='bfc_execution' and TICK.is_relative_to(ROOT/'pipeline/diagnostic_bundles') and REVIEW.is_relative_to(ROOT/'pipeline/diagnostic_bundles'),'Unexpected execution/report location')")
old=old.replace("candidate['code_commit'] == COMMIT and candidate['authorization'] == auth", "candidate['code_commit'] == COMMIT and candidate['authorization'] == auth")
start=old.index("        btc_before = copy.deepcopy(")
end=old.index("        raws = ",start)
old=old[:start]+"        protected_before=protected_snapshot(queue)\n        selected_gpu=read(EXECUTION/'execution_binding.json')['physical_gpu']\n"+old[end:]
old=old.replace("'actual_depth_ge2_scan_call_counts': observation['actual_depth_ge2_scan_call_counts'],", "'actual_nonpower2_supported_parent_group_counts': observation['actual_nonpower2_supported_parent_group_counts'],\n            'actual_multistage_supported_parent_group_counts': observation['actual_multistage_supported_parent_group_counts'],")
old=old.replace("'current_main_HEAD_equals_actual_tested11a'", "'current_main_HEAD_equals_actual_tested48fc'").replace("'eight_sources_and_YAML_equal_manifest_and_Git11a'", "'eight_sources_and_YAML_equal_manifest_and_Git48fc'")
old=old.replace("'only_replaced_middle_FFN_with_original_skip_shared_scan_readout_no_new_gate_language_route_QKV_or_residual_path'", "'only_replaced_middle_FFN_with_original_skip_shared_pair_composition_no_new_gate_language_route_QKV_or_residual_path'")
old=old.replace("Replace only original middle FFN delta with original-parent geometry-ordered exclusive prefix/suffix recurrence. One shared scan and one own/left/right readout have328192 parameters replacing525568, actual total delta-197376. Keep original cf skip/LayerNorm, fine/coarse FFNs, raw CSORT/FPS/IDs/HCG and single inst update. Native five weight-block gradients/updates and consumed depth2 nonzero prior-state loss path were actually reviewed.", "Replace only original middle FFN delta with original-parent geometry-ordered simultaneous butterfly pair composition. One shared2C-to2C Linear+GELU has262656 parameters replacing525568, actual delta-262912. Keep original cf skip/LayerNorm, fine/coarse FFNs, raw CSORT/FPS/IDs/HCG and single inst update. Actual same-old-state inputs, original two-output activation/scatter, n3/nonpower2/multistage and four aggregate weight-quadrant loss gradients/updates were reviewed; individual call/half zeros are legal. Own state is included, without a self-exclusive or conservation claim.")
old=old.replace("Only server4 physicalGPU1/max1 under exact grant90f. Existing GPU0 BTC is protected. M206 remains paused despite allowed GPU1. This creates waiting work, not launch or sync.", "Only actual selected server4 binding GPU0or1/max1 under current allowed resources; no auto-switch or availability claim. Both existing BTC0 and BCR1 task/experiment/receipt states are protected byte-for-byte; paused M206 is preserved. This creates waiting work, not launch, sync or a new resource grant.")
old=old.replace("Queue exact tested M213-BFC on authorized GPU1", "Queue exact tested M213-BFC on its actual selected authorized binding GPU")
old=old.replace("Actual original TRAIN2/native gradients/FFN0/2 and shared scan/readout and five weight-block updates/original-middle-skip-HCG-inst path and matched resource pair independently reviewed.", "Actual original TRAIN2/FFN0/2 and coupled pair-stage mix/GELU/scatter, four aggregate W quadrant original-loss gradients and updates, original-middle-skip-HCG-inst path and matched resource pair independently reviewed.")
old=old.replace("'label': 'BFC exclusive bidirectional complement recurrence'", "'label': 'BFC simultaneous two-output butterfly token composition'")
old=old.replace("'status': 'waiting', 'gpu': '1'", "'status': 'waiting', 'gpu': str(selected_gpu)")
old=old.replace('GPU1 only; BTC0 and M206 pause protected.', 'Actual selected binding GPU only; BTC0, BCR1 and M206 pause protected.')
old=old.replace("native_status='actual_TRAIN2_backward_exclusive_recurrence_five_weight_blocks_observed'", "native_status='actual_TRAIN2_backward_coupled_butterfly_four_W_quadrants_observed'")
old=old.replace('Exact original YAML is now verified in main Git11a', 'Exact original YAML is now verified in main Git48fc').replace('TESTED11A_', 'TESTED48FC_').replace('Exact tested BFC11a admitted waiting on only GPU1.', 'Exact tested BFC48fc admitted waiting on only its actual selected binding GPU.').replace('Do not touch GPU0 BTC, resume M206', 'Do not touch protected BTC0/BCR1, resume M206')
old=old.replace('fresh exact owner/assets/idleGPU1/three-lock binding. Four original M95/BFC GPU1 smoke/resource', 'fresh exact owner/assets/idle-selected-GPU/three-lock binding. Four original M95/BFC selected-GPU smoke/resource')
start=old.index("        require(next(t for t in monitor.load_queue(str(ROOT))['gpu_queues']['server-4'] if t['id'] == 'M206-CGCA')")
end=old.index("        result = ",start)
old=old[:start]+"        require(protected_snapshot(monitor.load_queue(str(ROOT)))==protected_before,'Protected BTC0/BCR1/M206/running registry changed')\n"+old[end:]
old=old.replace("'BTC0_queue_experiment_receipt_unchanged':True", "'BTC0_BCR1_M206_and_running_registry_unchanged':True")
old=old.replace('Main HEAD must actually equal tested11a', 'Main HEAD must actually equal tested48fc').replace('Native YAML Git11a blob differs', 'Native YAML Git48fc blob differs').replace('current validation11a','current validation48fc').replace('BFC11a','BFC48fc')
# Add exact protected state snapshots. A natural terminal task may already have been
# canonically archived; this helper must preserve whichever actual state exists.
marker='\ndef actual_checks('
idx=old.index(marker)
old=old[:idx]+'''
UUIDS={0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',1:'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}

def protected_snapshot(queue):
    result={'running_sha256':sha(ROOT/'pipeline/running.json')}
    expected={'M211-BTC':('00e2b18c6b8d568a64edb496e6979d766440883c','93756329046cf30357c258848d6b3287c25b4b0c96ef69b0ffd5f3b8710f2a36'),
              'M212-BCR':('11a811618179ab1ddc0cee299194667413b7fdb9','b8532405ba05101355898016aeeb45e1776217bc95a64a2ae449c1ff02ef60ac')}
    for eid,(commit,receipt_sha) in expected.items():
        rows=[t for tasks in queue['gpu_queues'].values() for t in tasks if t['id']==eid]
        require(len(rows)<=1,'Protected task duplicate before BFC admission')
        experiment_path=ROOT/'pipeline/experiments'/str(eid+'.json');experiment=read(experiment_path)
        require(experiment['id']==eid and experiment['code_commit']==commit,'Protected experiment identity differs')
        receipt_path=ROOT/'pipeline/admissions'/str(eid+'.json');require(sha(receipt_path)==receipt_sha,'Protected receipt changed')
        result[eid]={'queue_rows':copy.deepcopy(rows),'experiment_sha256':sha(experiment_path),'receipt_sha256':receipt_sha}
    rows=[t for tasks in queue['gpu_queues'].values() for t in tasks if t['id']=='M206-CGCA']
    require(len(rows)==1 and rows[0].get('dispatch_hold') and rows[0].get('resume_authorized') is False,'M206 user pause must remain exact; resource grant is not resume permission')
    result['M206-CGCA']={'queue_rows':copy.deepcopy(rows),'experiment_sha256':sha(ROOT/'pipeline/experiments/M206-CGCA.json')}
    return result

'''+old[idx:]
with (HERE/'admit_bfc_draft.py').open('x',encoding='utf-8',newline='\n') as stream:stream.write(old)
ast.parse(old)
print('Root-only BFC admission draft source written; no outcomes or standard/shared artifacts written')
