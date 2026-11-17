"""Record current evidence with the existing owner; never change goal or snapshot."""
from datetime import datetime, timezone
import json
from ops import guard, save, evidence, ROOT, OUT, CID, TOKEN
import foreground_tick as tick

owner=guard()
assert tick.load(OUT/'independent_analysis_audit.json')['passed']
assert tick.load(OUT/'production_source_postcheck.json')['unchanged']
result=tick.load(OUT/'fullval/paired_analysis_result.json')
work=tick.load(ROOT/'pipeline/research_work.json')
by={c['id']:c for c in work['candidates']}
now=datetime.now(timezone.utc).isoformat()
def add(c,names):
    known={(x['path'],x['sha256']) for x in c['evidence']}
    for name in names:
        item=evidence(OUT/name)
        if (item['path'],item['sha256']) not in known:c['evidence'].append(item)
def resolve_old_resource_hold(c):
    keys=('blocker_kind','required_server','blocker','retry_after','unblock_condition','last_rechecked_at')
    prior={key:c.pop(key) for key in keys if key in c}
    if prior:c.setdefault('resolved_resource_holds',[]).append({'resolved_at':now,'prior':prior,'evidence':[evidence(OUT/'native_preexecution_metric.json')]})

c=by[CID];c.update(stage='complete',failure_scope='inconclusive',updated_at=now,
    gate_result='Finite exact-run disposition audit complete:normal earlystop23,bestepoch13,23native validations,no error markers;not a mechanism efficacy PASS.',
    next_action='Retain original logs and checkpoints;no restart or replacement. Use the now-completed unique-best fullVAL result for scientific disposition.')
add(c,['exit_result.json','terminal_reconciliation.json','M203_native_terminal.log'])
c=by['fle-fixed-membership-metric-geometry-audit'];resolve_old_resource_hold(c)
c.update(stage='complete',failure_scope='inconclusive',updated_at=now,
    gate_result='Finite native fixed-membership question complete:8TRAINgeometries,24FPS/64fine-kernel calls,56comparisons,alloutputerror0/fallbackflips0;features synthetic,not trainedmask or wholehierarchy proof.',
    next_action='Preserve original artificial lattice failure and this finite native negative reproduction;no epsilon/source repair. Any whole-hierarchy or trained-mask robustness claim needs its own task-relevant preregistered test.')
c['gates'].update(native_FPS_membership='EXECUTED_8_GEOMETRIES',native_fixed_membership_transform='PASS_56_FINITE_COMPARISONS',trained_mask_effect='UNKNOWN')
add(c,['native_metric_result.json','native_execution_metric.json'])
c=by['fle-self-neighbor-content-separation'];resolve_old_resource_hold(c)
c.update(stage='implementation',failure_scope='implementation',updated_at=now,
    gate_result='INVALID_MATCHED_NORM_CONTROL:original and diagnosticrepair1 fail unchanged1e-6;cohort incomplete,neighborcontent usefulness inconclusive.',
    next_action='Before another native run,derive deterministic norm-preserving transplant accounting for float32 reductions on saved captured inputs;preregister bounded diagnosticrevision2 with specific defect/change/prediction and unchanged1e-6controls. If no valid repair,close this diagnostic implementation as inconclusive rather than relax gates;no model change/restart or VAL selection.')
c['gates'].update(native_same_prefix_diagnostic='FAILED_STRICT_NORM_CONTROL_INCOMPLETE_COHORT',diagnostic_revision1='FAILED_SAME_NATIVE_CONTROL',trained_efficacy='M203_REALIZATION_NEGATIVE_SEPARATE_FROM_CAUSAL_DIAGNOSTIC')
c['diagnostic_instrumentation_history'][-1].update(result='failed_control_captured',evidence=[evidence(OUT/'norm_capture/native_diagnostic_result.json'),evidence(OUT/'norm_capture/failed_norm_input.npz'),evidence(OUT/'norm_forensics_result.json')])
c['diagnostic_revision_history'][-1].update(result='failed',evidence=[evidence(OUT/'precision_cpu_result.json'),evidence(OUT/'norm_repair/native_diagnostic_result.json'),evidence(OUT/'native_execution_repair.json')],interpretation='True norm error improved;legacyCPU3of4fail,native scene2fails. AggregateCPUflag is not an all-control PASS;not a production modelrevision.')
add(c,['native_diagnostic_result.json','native_execution_self.json','native_execution_capture.json','norm_capture/native_diagnostic_result.json','norm_capture/failed_norm_input.npz','norm_forensics_result.json','precision_cpu_result.json','norm_precision_prereg.md','norm_repair/native_diagnostic_result.json','native_execution_repair.json'])
c=by['fine-leaf-local-point-exchange']
c.update(stage='rejected',failure_scope='implementation',updated_at=now,
    gate_result='TRAINED_REALIZATION_NO_GAIN:normal earlystop23/bestepoch13;fullVAL .4885315597 belowbaseline.4894/M95.5020/target.5100;pairedavailableM95delta-.0139291520. Does not falsify every point-exchange mechanism.',
    rejection_reason='This frozen trained FLE realization failed efficacy and original converged branch-stop;not a pretraining magnitude veto or universal family rejection.',
    next_action='Do not restart,scan or reopen this rejected realization automatically. Preserve matched diagnostics and mainline;future genuinely distinct structural work needs task-relevant diagnosis and unchanged gates. Self/nonself control repair stays on its existing diagnostic ID.',
    unmeasured_gates=['material novelty','full-training peak','original no-cluster resource delta','independent-repeat noise floor'])
add(c,['fullval/candidate_fle_epoch13.json','fullval/paired_candidate_capture_index.json','fullval/paired_analysis.py','fullval/paired_analysis_result.json','independent_analysis_audit.json','production_source_postcheck.json'])
work.pop('design_cycle',None)
guard();tick.save(ROOT/'pipeline/research_work.json',work)
files=['exit_result.json','terminal_reconciliation.json','native_metric_result.json','native_diagnostic_result.json','norm_capture/native_diagnostic_result.json','norm_forensics_result.json','precision_cpu_result.json','norm_repair/native_diagnostic_result.json','fullval/candidate_fle_epoch13.json','fullval/paired_analysis_result.json','independent_analysis_audit.json','server4_final_resources.json','server3_final_resources.json','production_source_postcheck.json']
save('progress_summary.json',{'observed_at':now,'token':TOKEN,'attempted_ids':[CID,'fine-leaf-local-point-exchange','fle-fixed-membership-metric-geometry-audit','fle-self-neighbor-content-separation'],
    'native_neural_forwards':368,'native_fps_layer_calls':24,'fine_kernel_calls_geometry':64,'geometry_transform_comparisons':56,'suffix_replays':6,
    'CPU_feature_gradient_executions':1,'native_backwards':0,'optimizer_steps':0,'new_production_model_revisions':0,'diagnostic_arithmetic_revisions':1,'new_admissions':0,'new_train_launches':0,
    'fullval_expressions':9508,'fullval_scenes':141,'fullval_native_forwards':363,'candidate_miou':result['candidate_native_miou'],'paired_result':result['groups']['all'],
    'evidence':[evidence(OUT/name) for name in files],
    'postflight':'PENDING_NOT_PRECLAIMED','scope':'Only this tick real executions;not cumulative successes or billable usage'})
print(json.dumps({'persisted':True,'active_implementation':'fle-self-neighbor-content-separation','finish':'NOT_YET_CALLED'}))
