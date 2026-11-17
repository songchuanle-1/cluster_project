"""Persist actual CPU results and the evidenced exclusive-resource blocker."""
from datetime import datetime,timedelta,timezone
import json
from ops import guard,save,evidence,ROOT,OUT,CID

guard()
operator=json.loads((OUT/'cpu_contracts_result.json').read_text())
prepared=json.loads((OUT/'cpu_prepare_result.json').read_text())
busy_guard=json.loads((OUT/'occupied_guard_precheck.json').read_text())
four=json.loads((OUT/'server4_live_final.json').read_text())
three=json.loads((OUT/'server3_live_final.json').read_text())
assert operator['passed'] and prepared['passed'] and busy_guard['expected_refusal']
assert not operator['cuda_initialized'] and not prepared['cuda_initialized']
assert four['occupied'] and three['occupied']
assert four['training_pid_alive'] and all(pids==[1995443] for pids in four['lock_owner_pids'].values())
now=datetime.now(timezone.utc)
for observation in (four,three):assert (now-datetime.fromisoformat(observation['observed_at'])).total_seconds()<900
assert len(operator['checks'])==8 and len(prepared['batches'])==8
files=['diagnostic_prereg.md','implementation_notes.md','cpu_contracts_result.json','frozen_assets.json','asset_metadata_result.json',
    'native_manifest.json','cpu_prepare_result.json','occupied_guard_precheck.json','server4_live_final.json','server3_live_final.json',
    'preparation_precheck_failure.json','orchestration_quote_failure.json','native_cpu_preparation_execution.json']
entries=[evidence(OUT/name) for name in files]
entries+=[evidence(ROOT/'pipeline/reviews/motivation_review_20261018_dbeca5d6.md'),evidence(ROOT/'pipeline/designs/exp_design_20261018_dbeca5d6.md')]
summary={'observed_at':now.isoformat(),'scientific_status':'inconclusive_native_pending_resource',
    'operator_cpu_case_groups':8,'strict_weight_loads':1,'cpu_collated_batches':8,'train_scenes':8,'expressions':32,
    'checkpoint_epoch':prepared['checkpoint_meta']['epoch'],'checkpoint_selected_by':'first stable closed last observed,not best score',
    'new_native_forwards':0,'new_native_backwards':0,'diagnostic_optimizer_steps':0,'cuda_initialized':False,
    'new_models':0,'admissions':0,'launches':0,'training_source_changed':False,
    'live_m203_validation':four['native_validation_miou'],'live_m203_epoch_step':four['last_native_epoch_step'],
    'both_authorized_slots_occupied':True,'busy_guard_refused_before_torch_and_locks':True,
    'limitations':['CPU tests and data preparation are not native trained diagnostic execution','early training is not final efficacy','material novelty unestablished','full-run allocated-memory peak unknown'],
    'next_action':'Continue unchanged M203;execute frozen same-prefix self/nonself diagnostic only after an authorized physical card is idle and a fresh owning foreground lease plus lifetime GPU locks are verified',
    'evidence':entries}
save('progress_summary.json',summary)
entries.append(evidence(OUT/'progress_summary.json'))
work=json.loads((ROOT/'pipeline/research_work.json').read_text())
candidate=next(c for c in work['candidates'] if c['id']==CID)
assert candidate['stage']=='diagnosis'
candidate.update(stage='blocked',blocker_kind='exclusive_gpu_slot',required_server='server-4',
    blocker='Non-GPU preparation completed:8 CPU operator case groups,strict trained-checkpoint CPU load and8 native CPU-collated TRAIN groups. Both authorized physical slots occupied at00:49:42Shanghai;server4GPU0 training1995443 owns all3locks;server3GPU1 foreign1453 preserved. No CUDA diagnostic run.',
    retry_after=(now+timedelta(hours=1)).isoformat(),
    unblock_condition='Fresh live check finds server4physicalGPU0 idle (<1024MiB,util<10,no compute contexts),correct hostname/UUID and all training/diagnostic/exclusive flocks can be acquired under a fresh owning tick lease. Server3GPU1 fallback requires target asset/runtime validation before any execution.',
    next_action='Use frozen native_manifest.json/checkpoint epoch2/cohort8TRAINscenes32expressions and native_diagnostic.py --lease <fresh_current_tick_lease>;recheck source/config/data/checkpoint hashes,physical idle slot and lifetime locks before CUDA;run strict same-prefix normal/identity/nonself-content controls and preserve all results without changing1e-6tolerance. Do not edit M203,admit another model or resume training from diagnostic snapshot.',
    failure_scope='inconclusive',evidence=entries,
    gates={'operator_cpu':'PASS8casegroups','trained_checkpoint_strict_cpu_load':'PASS','native_train_cpu_collation':'PASS8scenes32expressions',
        'occupied_guard':'PASSrefusedwithouttorchorlocks','native_same_prefix_diagnostic':'NOT_RUN_RESOURCE_BLOCKED','trained_efficacy':'UNKNOWN','material_novelty':'UNESTABLISHED'},
    attempted_alternatives=['All analytic decomposition/norm/identity/permutation/tie/padding/gradient controls executed onCPU',
        'Strict time-selected trained-weight CPU load and original eight TRAIN scene collation executed withoutCUDA',
        'Checked authorized server4GPU0 and server3GPU1 live:both occupied;preserved training/foreign jobs',
        'Read-only busy-card guard refusal tested with0locks and noTorch import;no sharing/reset/eviction'],
    updated_at=now.isoformat())
work['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':[CID],
    'evidence':entries,'resume_condition':candidate['unblock_condition'],
    'scope':'This tick only:new trained-point-path diagnostic advanced from diagnosis after real CPU tests. Not route exhaustion,scientific rejection or a new admission.',
    'retry_after':candidate['retry_after']}
guard()
import foreground_tick
foreground_tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'candidate':CID,'stage':'blocked','reason':'exclusive_gpu_slot','cpu_tests_passed':True,'native_tests':'not_run','retry_after':candidate['retry_after'],'new_models':0,'admissions':0}))
