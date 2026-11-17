"""Disabled candidate-limited CTS actual-results -> standards/receipt/FIFO waiting draft.
No operation on import. Root must materialize/review exact actual independent refs first.
"""
import argparse
import copy
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import promotion_common as common

ROOT=common.ROOT
TICK=common.TICK
EXP=common.EXP
CID=common.CID
COMMIT=common.TESTED
CONFIG=common.CONFIG
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')

def save(path,value):
    common.owner_guard()
    with Path(path).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-root',action='store_true')
    args=parser.parse_args()
    if not args.execute_root:
        print('DRAFT_DISABLED: no standard/decision/receipt/queue/shared operation invoked')
        return
    common.execution_enabled(args.execute_root)
    common.owner_guard()
    sys.path.insert(0,str(SKILL))
    import closure
    import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));common.require(lock is not None,'Canonical pipeline lock busy')
    try:
        owner=common.owner_guard();manifest,raw_hashes,reviews=common.reviewed_four_raw()
        common.require(common.git('rev-parse','HEAD')==COMMIT,'Actual testedCTS4e8 must already be primaryHEAD; do not pre-sign')
        paths=common.source_paths(manifest)
        common.require(common.git('show','-s','--format=%P',COMMIT)==common.BASE,'CTS source is not exact single child48fc')
        common.require(set(common.git('diff-tree','--no-commit-id','--name-status','-r',COMMIT).splitlines())=={'A\t'+p for p in paths},'Actual source is not only exact nine additions')
        for p,h in paths.items():
            common.require(common.sha(common.CODE/p)==h and __import__('hashlib').sha256(common.git_bytes('show',COMMIT+':'+p)).hexdigest()==h,'Actual tested source/YAML differs from main/Git blob')
        common.protected()
        queue=monitor.load_queue(str(ROOT));work=common.read(ROOT/'pipeline/research_work.json')
        common.require(not any(t.get('id')==EXP for ts in queue['gpu_queues'].values() for t in ts),'Duplicate CTS queue task')
        common.require(monitor.load_experiment(str(ROOT),EXP) is None,'Existing experiment requires read-only reconciliation')
        candidate=next(c for c in work['candidates'] if c['id']==CID)
        policy=common.read(ROOT/'pipeline/closure_policy.json');auth=policy['experiment_first']['authorization']
        common.require(candidate['stage']=='validation' and candidate['code_commit']==COMMIT and candidate['authorization']==auth,'Current candidate identity/stage/authorization differs')
        common.require(not candidate.get('revision_history') and not candidate.get('implementation_revision_sha256'),'Revisions require separately reviewed binding')
        common.require(not any(candidate.get(k) for k in ('human_hold','scope_hold','numerical_hold','dispatch_hold','hold','paused','requires_human','requires_confirmation','needs_confirmation')),'Candidate hold cannot be bypassed')
        protected_before=common.protected_lifecycle(queue)
        execution=common.TEST_TICK/'cts_execution';binding=common.read(execution/'execution_binding.json')
        gpu=binding['physical_gpu'];common.require(gpu==0 and type(gpu) is int,'This root CTS promotion is only its actual selectedGPU0')
        raws={mode+'_'+target:common.read(execution/(mode+'_'+target+'_execution.json'))['result'] for mode,target in common.PAIRS}
        local=common.read(ROOT/common.SEMANTIC_REVIEW_PATH);observation=local['observations'];smoke=raws['smoke_candidate'];now=datetime.now(timezone.utc).isoformat()
        common.require(observation['existing_memory_condition_needs_separate_retention_decision'] is False,'Existing memory-retention condition needs a separate real decision')
        identity={'id':EXP,'candidate_id':CID,'config':CONFIG,'code_commit':COMMIT,'goal_sha256':common.GOAL}
        evidence=[common.ref(execution/(m+'_'+t+'_execution.json')) for m,t in common.PAIRS]
        evidence.extend(common.ref(execution/n) for n in ('execution_binding.json','native_manifest.json','execution_lease.json'))
        evidence.extend(reviews)
        evidence.append(dict(common.CURRENT_RESOURCE_AUTHORIZATION))
        evidence.extend([common.ref(common.CHECKER_PATH),common.ref(Path(__file__)),common.ref(common.TEST_TICK/'exact_terminal_archive_result.json'),common.ref(common.TEST_TICK/'exact_terminal_archive_review.json')])
        standard_smoke={**identity,'steps':smoke['optimizer_steps'],'losses':smoke['losses'],
          'native_data_loaded':smoke['native_data_loaded'],'backward_finite':smoke['backward_finite'],'intended_path_observed':smoke['intended_path_observed'],
          'split':'train','command':smoke['actual_train_command'],'data_source':smoke['data_source']['train'],
          'native_train_cli_reference':smoke['native_train_cli_reference'],'paired_TRAIN_batches':smoke['batches'],
          'common_initialized_parameter_observations':observation['common_initialized_parameter_observations'],
          'actual_three_distinct_real_input_row_counts':observation['actual_three_distinct_real_input_row_counts'],
          'actual_multiround_supported_parent_group_counts':observation['actual_multiround_supported_parent_group_counts'],
          'actual_dilated_round_call_counts':observation['actual_dilated_round_call_counts'],
          'actual_aliased_negative_zero_rows':observation['actual_aliased_negative_zero_rows'],
          'actual_map_call_counts':observation['actual_map_call_counts'],'actual_required_weight_blocks':observation['actual_required_weight_blocks'],
          'native_test_owner':common.TEST_OWNER,'current_promotion_owner':common.CURRENT_OWNER,'current_resource_authorization':common.CURRENT_RESOURCE_AUTHORIZATION,'effective_stop_at':common.EFFECTIVE_STOP_AT,'evidence':evidence,'recorded_at':now,
          'limitations':{'efficacy':'UNKNOWN','full_buffer_values':'NOT_RECORDED','offdiagonal_probe':observation['offdiagonal_dependency_probe'],
            'empty_padding_singleton_coverage':{k:observation[k] for k in ('actual_unsupported_internal_rows','actual_padding_rows','actual_supported_singleton_groups')},
            'raw_cross_target_digest_scope':observation['raw_bank_digest_scope'],'pure_TRAIN_memory':smoke['pure_training_peak_memory']}}
        resources={**identity,'passed_existing_resource_requirements':True,'recorded_at':now,
          'protocol':{'batch_size':1,'lang_num_max':1,'warmup':20,'repeat':100,'counted_flops_limit':10e9},
          'observations':observation['resource_observations'],'evidence':evidence,
          'limitations':'Original handlers/unsupported dictionaries retained; Python/CPU work not wholly counted. Smoke peak includes observers, pure TRAIN memory and efficacy UNKNOWN. No new latency threshold.'}
        constraints={**identity,'passed':True,'recorded_at':now,'checks':{
          'current_main_HEAD_equals_actual_tested4e8':True,'nine_source_YAML_equal_actual_manifest_Git_and_main':True,
          'all28_protected_status_bytes_unchanged_index_empty':True,'original_YAML_seed_schedule_data_optimizer':True,
          'actual_two_TRAIN_batches_common_named_initialization_paired':True,'original_FPS_rawbanks_CSORT_HCG_single_inst_and_skip':True,
          'three_aggregate_W_columns_original_loss_grad_and_actual_updates_observed':True,
          'actual_three_distinct_input_multiround_consumed_dilation_observed':True},
          'structural_change':'Only middle FFN delta replaced by same-parent deterministic cyclic triadic synchronous old-state composition, shared3C-toC Linear plus original GELU, minimal ceil(log3 n) rounds, duplicate negative alias privatezero. Original LN/cfskip/fine/coarse/FPS/IDs/rawCSORT/HCG/singleinst retained. Per-call/row zero legal. Actual technical checks are not novelty/benefit/accuracy proof.',
          'source_hashes':manifest['candidate_source_hashes'],'config_sha256':manifest['candidate_config_sha256'],
          'frozen_native_preparation':common.ref(ROOT/candidate['worker_preparation']['preparation']['path']),
          'evidence':evidence,'resource_scope':'Actual selectedserver4GPU0/max1/currentgrant only; no fallback. Canonical BFC crashed/BCR earlystop/M206 pause and original source/receipt/archive remain unchanged. BEC9b67 failed resource arm is preserved separately, not CTS scientific gate or relabeled code4e8.'}
        outputs={'smoke':TICK/'cts_native_smoke.json','resources':TICK/'cts_resource_comparison.json','constraints':TICK/'cts_constraints_independence.json'}
        receipt_path=ROOT/'pipeline/admissions/M214-CTS.json'
        common.require(not receipt_path.exists() and not any(p.exists() for p in outputs.values()),'Existing standard/receipt cannot be overwritten or phase replayed')
        task={'id':EXP,'label':'CTS parent cyclic triadic state composition','config':CONFIG,'code_commit':COMMIT,
          'admission_receipt':'pipeline/admissions/M214-CTS.json','status':'waiting','gpu':'0','server':'server-4','profile':'experiment_first','added_at':now,
          'note':'Original seed1999/epochs50/maxiters70/native YAML unchanged; actual pairedTRAIN2/resources independently reviewed. Source4e8 only. Technical admission is not efficacy; BFC crash/BCR earlystop/M206pause preserved.'}
        common.begin_phase('admit_queue',{'actual_raw_hashes':raw_hashes,'actual_review_refs':reviews,'protected_lifecycle':protected_before,'target_task':task})
        for k in outputs:save(outputs[k],{'smoke':standard_smoke,'resources':resources,'constraints':constraints}[k])
        args_log=['C:/Program Files (x86)/Git/bin/bash.exe',str(SKILL/'log_decision.sh'),'cluster_project','queue_push',
          'Admit exact testedCTS4e8 after actual twoTRAIN steps and paired original resources?',
          'Create actual experiment-first receipt and FIFO waiting CTS only on its actual selectedGPU0; no launch by this helper.',
          'CTS original-loss three aggregate W-column gradients/updates and true3distinct/multiround/dilation verified; per-call zeros legal. Original inputs/common initialization/resources reviewed. Canonical archives and M206 pause protected; efficacy UNKNOWN.',
          '; '.join(x['path']+' SHA'+x['sha256'] for x in [common.ref(p) for p in outputs.values()]+reviews)]
        common.owner_guard();run=subprocess.run(args_log,capture_output=True,text=True,encoding='utf-8',timeout=30,env=os.environ.copy())
        common.require(run.returncode==0,'Decision logger failed; preserve durable partialphase, no rerun: '+run.stderr)
        decision=Path(run.stdout.strip().split('-> ',1)[1].strip());decision_ref=common.ref(decision)
        receipt={**identity,'profile':'experiment_first','authorization':auth,'native_smoke':common.ref(outputs['smoke']),
          'decision':decision_ref,'created_at':now,'native_test_owner':common.TEST_OWNER,'promotion_owner':common.CURRENT_OWNER,'current_resource_authorization':common.CURRENT_RESOURCE_AUTHORIZATION,'effective_stop_at':common.EFFECTIVE_STOP_AT,'independent_review':common.ref(ROOT/common.INDEPENDENT_REVIEW_PATH),
          'gates':{name:{'passed':True,'evidence':[common.ref(outputs[kind]),common.ref(ROOT/common.INDEPENDENT_REVIEW_PATH)]} for name,kind in [('native_backward','smoke'),('resources','resources'),('independence','constraints'),('constraints','constraints')]},'efficacy':'UNKNOWN; technical admission is not training success or accuracy gain.'}
        save(receipt_path,receipt)
        closure.admission(ROOT,task)
        prospective=copy.deepcopy(queue);prospective['gpu_queues']['server-4'].append(task)
        closure.validate_foreground_dispatch_budget(ROOT,prospective,task)
        candidate.setdefault('execution_preparation_history',[]).append({'recorded_at':now,'reason':'Preserve original reviewed static catalog before actual four-arm admission','worker_preparation':copy.deepcopy(candidate['worker_preparation']),'execution_adapter':copy.deepcopy(candidate['execution_adapter'])})
        candidate.update(stage='deployment',training_status='waiting',experiment_first_admission=True,admission_receipt=common.ref(receipt_path),
          native_status='ACTUAL_TRAIN2_BACKWARD_THREE_W_COLUMNS_OBSERVED',resource_status='ACTUAL_ORIGINAL_PAIRED_RESOURCE_PROTOCOL_PASSED',
          native_execution=common.ref(ROOT/common.SEMANTIC_REVIEW_PATH),native_execution_code_commit=COMMIT,
          native_smoke_status='ACTUAL_TRAIN2_PASSED',resource_profile_status='ACTUAL_PAIRED_RESOURCES_PASSED',admission_status='ADMITTED_WAITING',
          implementation_status='ACTUAL_NATIVE_TRAIN2_AND_RESOURCE_PAIR_VERIFIED',source_status='TESTED4E8_PRESENT_MAIN',
          next_action='Canonical one-shot FIFO selectedGPU0 dispatch must recheck exact source/runtime/assets/idle/3locks/native progress. Preserve canonical BFC crashed, BCR earlystop, M206 user pause and BEC original9b67 results. No blind replay or sibling ff.')
        for k in ('blocker_kind','blocker','blocked_at','retry_after','unblock_condition'):candidate.pop(k,None)
        candidate['worker_preparation'].update(status='ACTUAL_NATIVE_TRAIN2_AND_RESOURCES_COMPLETED_PASSED',native_backward_executed=True,resource_profile_executed=True,native_backward_passed=True,resources_passed=True,active_native_manifest_or_execution_lease_created=True)
        candidate['execution_adapter'].update(status='ACTUAL_FRESH_BINDING_FOUR_ARMS_TERMINAL_REVIEWED',native_execution_tested=True,native_execution_code_commit=COMMIT,remote_adapter_execution_tested=True,active_binding_manifest_lease_created=True,standard_summaries_created=True,
          active_binding=common.ref(execution/'execution_binding.json'),native_manifest=common.ref(execution/'native_manifest.json'),execution_lease=common.ref(execution/'execution_lease.json'),actual_four_result_review=common.ref(ROOT/common.SEMANTIC_REVIEW_PATH),execution_results={m+'_'+t:common.ref(execution/(m+'_'+t+'_execution.json')) for m,t in common.PAIRS})
        for p in [*outputs.values(),receipt_path,decision,ROOT/common.SEMANTIC_REVIEW_PATH,ROOT/common.INDEPENDENT_REVIEW_PATH,Path(__file__)]:
            item=common.ref(p)
            if item not in candidate.setdefault('evidence',[]):candidate['evidence'].append(item)
        work['updated_at']=now
        common.owner_guard()
        require_before=common.protected_lifecycle(monitor.load_queue(str(ROOT)));common.require(require_before==protected_before,'Protected lifecycle changed before queue write')
        # Once intent already exists. Any partial write requires read-only reconciliation, never rerun.
        destination=ROOT/'pipeline/research_work.json';temporary=destination.with_name(destination.name+'.'+common.TOKEN+'.cts_admission.tmp')
        with temporary.open('x',encoding='utf-8') as stream:
            json.dump(work,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        common.owner_guard();os.replace(temporary,destination)
        monitor.save_queue(str(ROOT),prospective)
        experiment=copy.deepcopy(task);experiment['history']=[{'ts':now,'status':'waiting','action':'actual_experiment_first_admission_queued','receipt':common.ref(receipt_path)}]
        monitor.save_experiment(str(ROOT),experiment)
        common.require(common.protected_lifecycle(monitor.load_queue(str(ROOT)))==protected_before,'Protected canonical terminal/M206/nontarget state changed')
        common.protected();common.owner_guard()
        result={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':common.EXPECTED_OWNER,'task':task,'receipt':common.ref(receipt_path),'decision':decision_ref,
          'standard_artifacts':{k:common.ref(v) for k,v in outputs.items()},'canonical_admission_validated':True,'canonical_tick_budget_validated':True,
          'protected_archived_BFC_BCR_M206_and_other_rows_unchanged':True,'training_launched':False,'source_synced':False}
        save(TICK/'cts_admission_queue_result.json',result);common.phase_result('admit_queue',result)
        print(json.dumps({'id':EXP,'status':'waiting','receipt':common.ref(receipt_path),'training_launched':False,'source_synced':False},ensure_ascii=False))
    finally:lock.close()

if __name__=='__main__':main()
