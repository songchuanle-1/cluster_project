"""Disabled candidate-limited BEC R1 actual-results -> standards/receipt/FIFO waiting draft.
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

def atomic_work(work):
    common.owner_guard();path=ROOT/'pipeline/research_work.json';tmp=path.with_name(path.name+'.'+common.TOKEN+'.bec_r1_pending_admission.tmp')
    with tmp.open('x',encoding='utf8') as stream:
        json.dump(work,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    common.owner_guard();os.replace(tmp,path)

def decision_path(stdout):
    raw=stdout.strip().splitlines()[-1].split('-> ',1)[1].strip()
    if len(raw)>3 and raw[0]=='/' and raw[2]=='/':raw=raw[1].upper()+':'+raw[2:]
    path=Path(raw).resolve();common.require(path.is_relative_to(ROOT/'pipeline/decisions') and path.is_file(),'Actual decision logger path missing/outside decisions; preserve partial phase')
    return path

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
        common.require(common.git('rev-parse','HEAD')==COMMIT,'Actual testedBEC026c R1 must already be primaryHEAD; do not pre-sign')
        paths=common.source_paths(manifest)
        common.require(common.git('show','-s','--format=%P',COMMIT)==common.BASE,'BEC R1 source is not exact single child4e8')
        common.require(set(common.git('diff-tree','--no-commit-id','--name-status','-r',COMMIT).splitlines())=={'A\t'+p for p in paths},'Actual source is not only exact nine additions')
        for p,h in paths.items():
            common.require(common.sha(common.CODE/p)==h and __import__('hashlib').sha256(common.git_bytes('show',COMMIT+':'+p)).hexdigest()==h,'Actual tested source/YAML differs from main/Git blob')
        common.protected()
        queue=monitor.load_queue(str(ROOT));work=common.read(ROOT/'pipeline/research_work.json')
        common.require(not any(t.get('id')==EXP for ts in queue['gpu_queues'].values() for t in ts),'Duplicate BEC R1 queue task')
        common.require(monitor.load_experiment(str(ROOT),EXP) is None,'Existing experiment requires read-only reconciliation')
        candidate=next(c for c in work['candidates'] if c['id']==CID)
        policy=common.read(ROOT/'pipeline/closure_policy.json');auth=policy['experiment_first']['authorization']
        common.require(candidate['stage']=='validation' and candidate['code_commit']==COMMIT and candidate['authorization']==auth,'Current candidate identity/stage/authorization differs')
        history=candidate.get('revision_history',[])
        common.require(len(history)==1 and history[0].get('revision')==1 and history[0].get('result')=='pending' and not candidate.get('implementation_revision_sha256'),'Only sole pending registered R1 may be admitted')
        prereg_path=ROOT/'pipeline/diagnostic_bundles/tick_45eb3b04/bec_revision1_preregistration.json'
        common.require(common.sha(prereg_path)=='3fa782b8970de909a219cc090e2188983e1afeab1ac99cac43df07b4f1e5b527','Immutable R1 preregistration changed')
        original_revision=common.read(prereg_path)['preregistration'];mutable={'result','evidence','result_evidence'}
        common.require({k:v for k,v in history[0].items() if k not in mutable}=={k:v for k,v in original_revision.items() if k not in mutable},'R1 immutable protocol differs')
        common.require(not any(candidate.get(k) for k in ('human_hold','scope_hold','numerical_hold','dispatch_hold','hold','paused','requires_human','requires_confirmation','needs_confirmation')),'Candidate hold cannot be bypassed')
        protected_before=common.protected_lifecycle(queue)
        execution=common.TEST_TICK/'bec_r1_execution';binding=common.read(execution/'execution_binding.json')
        gpu=binding['physical_gpu'];common.require(gpu==0 and type(gpu) is int,'This root BEC R1 promotion is only its actual selectedGPU0')
        raws={mode+'_'+target:common.read(execution/(mode+'_'+target+'_execution.json'))['result'] for mode,target in common.PAIRS}
        local=common.read(ROOT/common.SEMANTIC_REVIEW_PATH);observation=local['observations'];smoke=raws['smoke_candidate'];now=datetime.now(timezone.utc).isoformat()
        common.require(observation['existing_memory_condition_needs_separate_retention_decision'] is False,'Existing memory-retention condition needs a separate real decision')
        identity={'id':EXP,'candidate_id':CID,'config':CONFIG,'code_commit':COMMIT,'goal_sha256':common.GOAL}
        evidence=[common.ref(execution/(m+'_'+t+'_execution.json')) for m,t in common.PAIRS]
        evidence.extend(common.ref(execution/n) for n in ('execution_binding.json','native_manifest.json','execution_lease.json'))
        evidence.extend(reviews)
        evidence.append(dict(common.CURRENT_RESOURCE_AUTHORIZATION))
        evidence.extend([common.ref(common.CHECKER_PATH),common.ref(Path(__file__)),common.ref(prereg_path)])
        passed=copy.deepcopy(candidate);revision=passed['revision_history'][0]
        actual_result_evidence=[common.ref(execution/(m+'_'+t+'_execution.json')) for m,t in common.PAIRS]+reviews
        for entry in actual_result_evidence:
            if entry not in revision.setdefault('evidence',[]):revision['evidence'].append(entry)
            if entry not in revision.setdefault('result_evidence',[]):revision['result_evidence'].append(entry)
        revision['result']='passed'
        closure.validate_revisions(ROOT,passed,candidate)
        revision_sha=closure.revision_digest(revision)
        passed['implementation_revision_sha256']=revision_sha
        identity['implementation_revision_sha256']=revision_sha
        standard_smoke={**identity,'steps':smoke['optimizer_steps'],'losses':smoke['losses'],
          'native_data_loaded':smoke['native_data_loaded'],'backward_finite':smoke['backward_finite'],'intended_path_observed':smoke['intended_path_observed'],
          'split':'train','command':smoke['actual_train_command'],'data_source':smoke['data_source']['train'],
          'native_train_cli_reference':smoke['native_train_cli_reference'],'paired_TRAIN_batches':smoke['batches'],
          'common_initialized_parameter_observations':observation['common_initialized_parameter_observations'],
          'actual_fine_edge_counts':observation['actual_fine_edge_counts'],'actual_middle_edge_counts':observation['actual_middle_edge_counts'],
          'actual_new_operator_call_counts':observation['actual_new_operator_call_counts'],'actual_private_mean_call_counts':observation['actual_private_mean_call_counts'],
          'actual_required_weight_blocks':observation['actual_required_weight_blocks'],
          'native_test_owner':common.TEST_OWNER,'current_promotion_owner':common.CURRENT_OWNER,'current_resource_authorization':common.CURRENT_RESOURCE_AUTHORIZATION,'effective_stop_at':common.EFFECTIVE_STOP_AT,'evidence':evidence,'recorded_at':now,
          'limitations':{'efficacy':'UNKNOWN','full_buffer_values':'NOT_RECORDED','offdiagonal_probe':observation['offdiagonal_dependency_probe'],
            'optional_degree_empty_padding_coverage':observation['actual_optional_boundary_counts'],
            'raw_cross_target_digest_scope':observation['raw_bank_digest_scope'],'pure_TRAIN_memory':smoke['pure_training_peak_memory']}}
        resources={**identity,'passed_existing_resource_requirements':True,'recorded_at':now,
          'protocol':{'batch_size':1,'lang_num_max':1,'warmup':20,'repeat':100,'counted_flops_limit':10e9},
          'observations':observation['resource_observations'],'evidence':evidence,
          'limitations':'Original handlers/unsupported dictionaries retained; Python/CPU work not wholly counted. Smoke peak includes observers, pure TRAIN memory and efficacy UNKNOWN. No new latency threshold.'}
        constraints={**identity,'passed':True,'recorded_at':now,'checks':{
          'current_main_HEAD_equals_actual_tested026c':True,'nine_source_YAML_equal_actual_manifest_Git_and_main':True,
          'all28_protected_status_bytes_unchanged_index_empty':True,'original_YAML_seed_schedule_data_optimizer':True,
          'actual_two_TRAIN_batches_common_named_initialization_paired':True,'original_FPS_rawbanks_CSORT_HCG_single_inst_and_skip':True,
          'five_modules_and_twelve_aggregate_W_blocks_original_loss_grad_and_actual_slice_updates_observed':True,
          'actual_two_up_splits_equal_child_private_means_original_coarse_once_two_down_and_three_skips_observed':True,
          'registered_R1_true_to_one_scalar_exact_CPU_compatibility_and_immutable_protocol_preserved':True},
          'structural_change':'Same registered BEC graph: supported fine/middle bipartite upward retained/upward splits, equal supported-child private means, original coarse LN/FFN once with unsupported delta masked, two downward maps and three original skips/HCG/singleinst. R1 only changes bool-mask index_fill scalar True to integer1 for original JIT compatibility. Individual call/row zero legal; no new threshold or graph. Actual technical pass is not efficacy or novelty.',
          'source_hashes':manifest['candidate_source_hashes'],'config_sha256':manifest['candidate_config_sha256'],
          'frozen_native_preparation':common.ref(ROOT/candidate['worker_preparation']['preparation']['path']),
          'evidence':evidence,'resource_scope':'Actual selectedserver4GPU0/max1/currentgrant only; no fallback. Canonical CTS stopped_unknown, BFC crashed, BCR earlystop and M206 pause/source/receipt/archive remain unchanged. Original9b smoke and failed JIT resource arm are history, never026c R1 results.'}
        outputs={'smoke':TICK/'bec_r1_native_smoke.json','resources':TICK/'bec_r1_resource_comparison.json','constraints':TICK/'bec_r1_constraints_independence.json'}
        receipt_path=ROOT/'pipeline/admissions/M215-BEC.json'
        common.require(not receipt_path.exists() and not any(p.exists() for p in outputs.values()),'Existing standard/receipt cannot be overwritten or phase replayed')
        task={'id':EXP,'label':'BEC cross-level bipartite edge composition R1','config':CONFIG,'code_commit':COMMIT,
          'admission_receipt':'pipeline/admissions/M215-BEC.json','status':'waiting','gpu':'0','server':'server-4','profile':'experiment_first','added_at':now,
          'note':'Original seed1999/epochs50/maxiters70/native YAML unchanged; actual pairedTRAIN2/resources independently reviewed. Source026c/R1 only. Technical admission is not efficacy; CTS stopped_unknown/BFC crash/BCR earlystop/M206pause preserved.'}
        common.begin_phase('admit_queue',{'actual_raw_hashes':raw_hashes,'actual_review_refs':reviews,'protected_lifecycle':protected_before,'target_task':task})
        for k in outputs:save(outputs[k],{'smoke':standard_smoke,'resources':resources,'constraints':constraints}[k])
        args_log=['C:/Program Files (x86)/Git/bin/bash.exe',str(SKILL/'log_decision.sh'),'cluster_project','queue_push',
          'Admit exact testedBEC026c R1 after actual twoTRAIN steps and paired original resources?',
          'Create actual experiment-first receipt and FIFO waiting BEC R1 only on its actual selectedGPU0; no launch by this helper.',
          'BEC R1 actual original-loss five-module/twelve aggregate-block gradients+updates and two-up/private-mean/coarse-once/two-down/three-skip path verified; per-call zeros legal. Original pairedTRAIN/common/resources reviewed. Canonical archives and M206 pause protected; efficacy UNKNOWN.',
          '; '.join(x['path']+' SHA'+x['sha256'] for x in [common.ref(p) for p in outputs.values()]+reviews)]
        common.owner_guard();run=subprocess.run(args_log,capture_output=True,text=True,encoding='utf-8',timeout=30,env=os.environ.copy())
        common.require(run.returncode==0,'Decision logger failed; preserve durable partialphase, no rerun: '+run.stderr)
        decision=decision_path(run.stdout);decision_ref=common.ref(decision)
        receipt={**identity,'profile':'experiment_first','authorization':auth,'native_smoke':common.ref(outputs['smoke']),
          'decision':decision_ref,'created_at':now,'native_test_owner':common.TEST_OWNER,'promotion_owner':common.CURRENT_OWNER,'current_resource_authorization':common.CURRENT_RESOURCE_AUTHORIZATION,'effective_stop_at':common.EFFECTIVE_STOP_AT,'independent_review':common.ref(ROOT/common.INDEPENDENT_REVIEW_PATH),
          'gates':{name:{'passed':True,'evidence':[common.ref(outputs[kind]),common.ref(ROOT/common.INDEPENDENT_REVIEW_PATH)]} for name,kind in [('native_backward','smoke'),('resources','resources'),('independence','constraints'),('constraints','constraints')]},'efficacy':'UNKNOWN; technical admission is not training success or accuracy gain.'}
        save(receipt_path,receipt)
        # closure.admission reads canonical current R1 status. Persist the
        # actually passed revision while it still remains validation/nonqueued,
        # then run exact admission/budget checks before any queue mutation.
        passed.update(stage='validation',admission_status='PASSED_R1_NOT_YET_QUEUED',native_execution_code_commit=COMMIT)
        work['candidates'][work['candidates'].index(candidate)]=passed;candidate=passed
        work['updated_at']=now
        atomic_work(work)
        closure.admission(ROOT,task)
        prospective=copy.deepcopy(queue);prospective['gpu_queues']['server-4'].append(task)
        closure.validate_foreground_dispatch_budget(ROOT,prospective,task)
        candidate.setdefault('execution_preparation_history',[]).append({'recorded_at':now,'reason':'Preserve original reviewed static catalog before actual four-arm admission','worker_preparation':copy.deepcopy(candidate['worker_preparation']),'execution_adapter':copy.deepcopy(candidate['execution_adapter'])})
        candidate.update(stage='deployment',training_status='waiting',experiment_first_admission=True,admission_receipt=common.ref(receipt_path),
          native_status='ACTUAL_TRAIN2_BACKWARD_FIVE_MODULES_TWELVE_BLOCKS_OBSERVED',resource_status='ACTUAL_ORIGINAL_PAIRED_RESOURCE_PROTOCOL_PASSED',
          native_execution=common.ref(ROOT/common.SEMANTIC_REVIEW_PATH),native_execution_code_commit=COMMIT,
          native_smoke_status='ACTUAL_TRAIN2_PASSED',resource_profile_status='ACTUAL_PAIRED_RESOURCES_PASSED',admission_status='ADMITTED_WAITING',
          implementation_status='ACTUAL_NATIVE_TRAIN2_AND_RESOURCE_PAIR_VERIFIED',source_status='TESTED026C_R1_PRESENT_MAIN',
          next_action='Canonical one-shot FIFO selectedGPU0 dispatch must recheck exact source/runtime/assets/idle/3locks/native progress. Preserve CTS stopped_unknown, BFC crashed, BCR earlystop, M206 user pause and original9b results. No blind replay or sibling ff.')
        for k in ('blocker_kind','blocker','blocked_at','retry_after','unblock_condition'):candidate.pop(k,None)
        candidate['worker_preparation'].update(status='ACTUAL_NATIVE_TRAIN2_AND_RESOURCES_COMPLETED_PASSED',native_backward_executed=True,resource_profile_executed=True,native_backward_passed=True,resources_passed=True,active_native_manifest_or_execution_lease_created=True)
        candidate['execution_adapter'].update(status='ACTUAL_FRESH_BINDING_FOUR_ARMS_TERMINAL_REVIEWED',native_execution_tested=True,native_execution_code_commit=COMMIT,remote_adapter_execution_tested=True,active_binding_manifest_lease_created=True,standard_summaries_created=True,
          active_binding=common.ref(execution/'execution_binding.json'),native_manifest=common.ref(execution/'native_manifest.json'),execution_lease=common.ref(execution/'execution_lease.json'),actual_four_result_review=common.ref(ROOT/common.SEMANTIC_REVIEW_PATH),execution_results={m+'_'+t:common.ref(execution/(m+'_'+t+'_execution.json')) for m,t in common.PAIRS})
        for item in evidence:
            if item not in candidate.setdefault('evidence',[]):candidate['evidence'].append(item)
        for p in [*outputs.values(),receipt_path,decision,ROOT/common.SEMANTIC_REVIEW_PATH,ROOT/common.INDEPENDENT_REVIEW_PATH,Path(__file__)]:
            item=common.ref(p)
            if item not in candidate.setdefault('evidence',[]):candidate['evidence'].append(item)
        work['updated_at']=now
        common.owner_guard()
        require_before=common.protected_lifecycle(monitor.load_queue(str(ROOT)));common.require(require_before==protected_before,'Protected lifecycle changed before queue write')
        # Once intent already exists. Any partial write requires read-only reconciliation, never rerun.
        destination=ROOT/'pipeline/research_work.json';temporary=destination.with_name(destination.name+'.'+common.TOKEN+'.bec_admission.tmp')
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
        save(TICK/'bec_admission_queue_result.json',result);common.phase_result('admit_queue',result)
        print(json.dumps({'id':EXP,'status':'waiting','receipt':common.ref(receipt_path),'training_launched':False,'source_synced':False},ensure_ascii=False))
    finally:lock.close()

if __name__=='__main__':main()
