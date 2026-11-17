"""Create authentic HRC standard artifacts/receipt and canonical waiting task."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='dfb6440d1b69401da8e932239883e613'
COMMIT='74fcd21df0af9a971792038ffe251af1ffea2604'
CID='hierarchy-bottom-up-refined-token-composition'; EXP='M208-HRC'

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path):return {'path':Path(path).relative_to(ROOT).as_posix(),'sha256':sha(path)}
def save(path,data,exclusive=False):
    path=Path(path)
    if exclusive:
        with path.open('x',encoding='utf-8') as stream:json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n')
    else:
        tmp=path.with_name(path.name+'.'+TOKEN+'.tmp')
        with tmp.open('x',encoding='utf-8') as stream:
            json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,path)

def git(*args):return subprocess.check_output(['git','-C',str(ROOT/'Cluster'),*args],text=True,encoding='utf-8').strip()

def main():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    review_path=HERE/'hrc_result_review/actual_four_result_review_v2.json'
    independent_path=HERE/'hrc_native_resource_independent_review.json'
    assert sha(review_path)=='715e010daf41ac590cff719a5866f5a58fcaa92a1559977cd780a55955dd9b4d'
    assert sha(independent_path)=='42eb6f8abde465ca0ae55a26fcb39f08b87975a8e86ac137f22db77468520607'
    review=read(review_path);independent=read(independent_path)
    assert review['review_status']=='RAW_SEMANTICS_VALIDATED_NOT_ADMISSION'
    assert independent['status']=='FOUR_ACTUAL_HRC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED'
    execution=HERE/'hrc_execution'; binding=read(execution/'execution_binding.json');manifest=read(execution/'native_manifest.json')
    assert binding['owner']['token']==TOKEN and binding['code_commit']==COMMIT and binding['physical_gpu']==0
    results={name:read(execution/(name+'_execution.json'))['result'] for name in ['smoke_champion','smoke_candidate','resources_champion','resources_candidate']}
    for name,result in results.items():
        assert result['execution_completed'] is True and result['code_commit']==COMMIT and result['candidate_id']==CID
    smoke=results['smoke_candidate'];control=results['smoke_champion'];resource=results['resources_candidate']
    assert smoke['optimizer_steps']==2 and smoke['native_data_loaded'] and smoke['backward_finite'] and smoke['intended_path_observed']
    assert smoke['batches']==control['batches'] and smoke['native_ffn_initial_hash_by_level']==control['native_ffn_initial_hash_by_level']
    assert git('rev-parse','HEAD')==COMMIT and not git('diff','--cached','--name-only')
    # Verify the complete protected local worktree, never stash/reset or commit it.
    protected=read(ROOT/'pipeline/diagnostic_bundles/tick_16b87793/protected_worktree_before.json')['protected_existing_worktree']
    status_raw=subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'status','--porcelain','--untracked-files=all'],text=True,encoding='utf-8')
    actual_status={(line[:2],line[3:]) for line in status_raw.splitlines() if line}
    assert actual_status=={(row['status'],row['path']) for row in protected}
    for row in protected:assert sha(ROOT/'Cluster'/row['path'])==row['sha256']
    native_source=ROOT/'Cluster/framework/model/Quard_model'/manifest['candidate_name']
    for name,value in manifest['candidate_source_hashes'].items():
        assert sha(native_source/name)==value
        assert hashlib.sha256(subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'show',COMMIT+':'+(native_source/name).relative_to(ROOT/'Cluster').as_posix()])).hexdigest()==value
    config=manifest['config'];assert sha(ROOT/'Cluster'/config)==manifest['candidate_config_sha256']
    assert len(manifest['candidate_source_hashes'])==8 and '_hrc' in smoke['model_package']
    policy=read(ROOT/'pipeline/closure_policy.json');auth=policy['experiment_first']['authorization']
    assert sha(ROOT/auth['path'])==auth['sha256'] and policy['experiment_first']['enabled'] is True
    observation=review['observations'];resource_observations=observation['resource_observations']
    assert resource_observations['candidate_standard_flops']<=10e9
    assert observation['existing_memory_condition_needs_separate_retention_decision'] is False
    evidence=[ref(execution/(name+'_execution.json')) for name in results]+[ref(execution/'execution_binding.json'),ref(execution/'native_manifest.json'),ref(execution/'execution_lease.json'),ref(review_path),ref(independent_path)]
    now=datetime.now(timezone.utc).isoformat()
    standard_smoke={'id':EXP,'candidate_id':CID,'config':config,'code_commit':COMMIT,'goal_sha256':manifest['goal_sha256'],
                    'steps':smoke['optimizer_steps'],'losses':smoke['losses'],'native_data_loaded':smoke['native_data_loaded'],
                    'backward_finite':smoke['backward_finite'],'intended_path_observed':smoke['intended_path_observed'],
                    'split':'train','command':smoke['actual_train_command'],'data_source':smoke['data_source']['train'],
                    'native_train_cli_reference':smoke['native_train_cli_reference'],'evidence':evidence,'recorded_at':now,
                    'native_mean_control_max_abs':max(v['reference_abs_max'] for v in smoke['refined_parent_mean_calls']),
                    'mean_reference_tolerance':1e-6,'paired_initialization_scope':observation['initialization_fingerprint_scope'],
                    'paired_TRAIN_batches':smoke['batches'],'limitations':{
                      'full_common_model_initial_state_hash':'NOT_RECORDED',
                      'nontrivial_internal_empty_child_and_padding_cases':'NOT_OBSERVED_IN_THESE_TWO_BATCHES',
                      'raw_and_map_cross_target_digests':'Different; not a preregistered exact-output equality gate. No unmeasured cause claimed.',
                      'pure_TRAIN_peak_memory':'UNKNOWN; smoke includes unchanged diagnostic/probe overhead',
                      'training_efficacy':'UNKNOWN'}}
    resources={'id':EXP,'candidate_id':CID,'config':config,'code_commit':COMMIT,'goal_sha256':manifest['goal_sha256'],
               'passed_existing_resource_requirements':True,'recorded_at':now,'observations':resource_observations,
               'protocol':{'batch_size':1,'lang_num_max':1,'warmup':20,'repeat':100,'counted_flops_limit':10e9},
               'evidence':evidence,'limitations':'Original standard counting with all unsupported operators disclosed; equal counted FLOPs is not zero actual extra cost. Full TRAIN memory and efficacy UNKNOWN; no new gate added.'}
    constraints={'id':EXP,'candidate_id':CID,'code_commit':COMMIT,'config':config,'goal_sha256':manifest['goal_sha256'],'recorded_at':now,
                 'passed':True,'checks':{'current_local_HEAD_equals_tested_commit':True,'eight_candidate_sources_equal_manifest_and_git_blob':True,
                 'native_YAML_equal_tested_manifest':True,'independent_candidate_package_actually_loaded':True,
                 'original_seed_pretrain_schedule_data_optimizer_preserved':True,'original_TRAIN_split_used':True,
                 'structural_information_dependency_change_not_parameter_tuning':True,'no_new_gate_language_routing_large_QKV_or_banned_route':True,
                 'all28_protected_status_and_bytes_unchanged_index_empty':True,'current_scoped_project_authorization_hash':True},
                 'structural_change':'Original three FFNs each once; refined fine then middle features enter original fixed-child parent means before original next-level FFN. No new parameters. Raw banks, FPS/IDs, CSORT/HCG and final inst_feats readback retained.',
                 'configuration_adaptations':{name:r['configuration_adaptations'] for name,r in results.items()},
                 'source_hashes':manifest['candidate_source_hashes'],'config_sha256':manifest['candidate_config_sha256'],
                 'frozen_native_preparation':ref(ROOT/'pipeline/diagnostic_bundles/tick_37695e94/hrc_native_prepare_head74f/preparation.json'),
                 'evidence':evidence,'research_scope':'Experiment-first technical admission only; efficacy/whole-mechanism novelty not claimed. HAP earlystop does not reject HRC or whole hierarchy.',
                 'resources':'Only server4GPU0/max1; GPU1 released and M206 protected. This creates waiting work, not a launch or source sync.'}
    paths={'smoke':HERE/'hrc_native_smoke.json','resources':HERE/'hrc_resource_comparison.json','constraints':HERE/'hrc_constraints_independence.json'}
    for name,value in [('smoke',standard_smoke),('resources',resources),('constraints',constraints)]:save(paths[name],value,True)
    args=['C:/Program Files (x86)/Git/bin/bash.exe',str(SKILL/'log_decision.sh'),'cluster_project','queue_push',
          'Admit HRC after real native and resource checks','Queue tested HRC74f on authorized GPU0',
          '真实同批TRAIN2/有限loss与backward/逐级FFN更新/mean1e-6/依赖probe及原资源pair通过；独立复核通过。9.762532428G/0新增参数，预测显存相等、smoke增幅低15%。原seed1999/YAML/schedule/数据保持。全common初始state/真空槽边界/纯TRAIN峰值及效果未知；unsupported完整披露，不称零成本。仅GPU0，M206暂停/GPU1别人；不改旧失败或额外修订。',
          '; '.join(item['path']+' SHA'+item['sha256'] for item in [ref(paths['smoke']),ref(paths['resources']),ref(paths['constraints']),ref(independent_path)])]
    decision_run=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=30,env=os.environ.copy())
    assert decision_run.returncode==0,decision_run.stderr
    decision=Path(decision_run.stdout.strip().split('-> ',1)[1].strip())
    receipt={'id':EXP,'candidate_id':CID,'config':config,'code_commit':COMMIT,'goal_sha256':manifest['goal_sha256'],'profile':'experiment_first',
             'authorization':auth,'native_smoke':ref(paths['smoke']),'decision':ref(decision),'created_at':now,
             'gates':{name:{'passed':True,'evidence':[ref(paths[kind]),ref(independent_path)]} for name,kind in [('native_backward','smoke'),('resources','resources'),('independence','constraints'),('constraints','constraints')]},
             'independent_review':ref(independent_path),'efficacy':'UNKNOWN until original native formal training; admission is not a claim of validation gain.'}
    receipt_path=ROOT/'pipeline/admissions'/f'{EXP}.json';assert not receipt_path.exists()
    task={'id':EXP,'label':'HRC refined-token hierarchy','config':config,'code_commit':COMMIT,'admission_receipt':receipt_path.relative_to(ROOT).as_posix(),
          'status':'waiting','gpu':'0','server':'server-4','profile':'experiment_first','requires_exclusive_ownership':True,
          'added_at':now,'note':'Original YAML/seed1999/epochs50/maxiters70. Actual native and standard resource pair reviewed; GPU0 only. Native diagnostics are not formal training or efficacy.'}
    sys.path.insert(0,str(SKILL));import closure;import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        queue=monitor.load_queue(str(ROOT));work=read(ROOT/'pipeline/research_work.json')
        assert not any(t.get('id')==EXP for group in queue['gpu_queues'].values() for t in group)
        assert monitor.load_experiment(str(ROOT),EXP) is None
        m206_before=copy.deepcopy(next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M206-CGCA'))
        c=next(c for c in work['candidates'] if c['id']==CID)
        assert c['stage']=='validation' and c['code_commit']==COMMIT
        save(receipt_path,receipt,True)
        # Canonical validator checks actual saved artifacts and current candidate/policy.
        closure.admission(ROOT,task)
        prospective=copy.deepcopy(queue);prospective['gpu_queues']['server-4'].append(task)
        closure.validate_foreground_dispatch_budget(ROOT,prospective,task)
        c.update(stage='deployment',native_status='actual_native_TRAIN2_backward_path_mean_controls_passed',
                 resource_status='actual_original_protocol_pair_passed',experiment_first_admission=True,
                 admission_receipt=ref(receipt_path),training_status='waiting',
                 next_action='Tested HRC74f is admitted and waiting on only authorizedGPU0. After current sequential native diagnostic completes, canonical gated dispatch must recheck actual idle/UUID/exclusive ownership and source/assets then safe ff-only sync and original-YAML launch; verify increasing native training steps. No GPU1/M206 resume.')
        for name in ('blocker_kind','blocker','blocked_at','retry_after','unblock_condition'):c.pop(name,None)
        c['worker_preparation'].update(native_backward_executed=True,resource_profile_executed=True,active_native_manifest_or_execution_lease_created=True)
        c['execution_adapter'].update(native_execution_tested=True,remote_adapter_execution_tested=True,active_binding_manifest_lease_created=True,
                                      standard_summaries_created=True,standard_result_formatter=ref(Path(__file__)))
        for path in list(paths.values())+[receipt_path,decision,independent_path,review_path,HERE/'hrc_current_external_anchor_check.json']:
            item=ref(path)
            if item not in c['evidence']:c['evidence'].append(item)
        work['updated_at']=now;save(ROOT/'pipeline/research_work.json',work)
        monitor.save_queue(str(ROOT),prospective)
        experiment=copy.deepcopy(task);experiment['history']=[{'ts':now,'status':'waiting','action':'actual_experiment_first_admission_queued','receipt':ref(receipt_path)}]
        monitor.save_experiment(str(ROOT),experiment)
        assert next(t for t in monitor.load_queue(str(ROOT))['gpu_queues']['server-4'] if t['id']=='M206-CGCA')==m206_before
        result={'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'task':task,'receipt':ref(receipt_path),
                'decision':ref(decision),'standard_artifacts':{k:ref(v) for k,v in paths.items()},'canonical_admission_validated':True,
                'canonical_tick_budget_validated':True,'m206_queue_unchanged':True,'training_launched':False,'source_synced':False,
                'next_dispatch_boundary':'GPU0 currently used by sequential PSBR native diagnostic; canonical dispatch after it completes, within this same tick.'}
        save(HERE/'hrc_admission_queue_result.json',result,True)
        print(json.dumps({'id':EXP,'status':'waiting','receipt':ref(receipt_path),'source_synced':False,'training_launched':False},ensure_ascii=False))
    finally:lock.close()

if __name__=='__main__':main()
